#!/bin/bash
# Word-level SRT with whisper.cpp (one word per entry).  Usage: word_srt.sh input.(mp4|wav|mov) [out.srt]
# Needs huggingface.co AND *.hf.co (us.aws.cdn.hf.co, cdn-lfs.hf.co, cas-bridge.xethub.hf.co) on the org network allowlist.
set -e
W=/home/claude/whisper.cpp; M=$W/models/ggml-small.en-q5_1.bin
[ -d $W ] || git clone --depth 1 https://github.com/ggml-org/whisper.cpp $W
[ -x $W/build/bin/whisper-cli ] || (cd $W && cmake -B build -DCMAKE_BUILD_TYPE=Release >/dev/null && cmake --build build -j$(nproc) --config Release >/dev/null)
[ -f $M ] || curl -sSL -o $M https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.en-q5_1.bin
IN="$1"; OUT="${2:-${IN%.*}_words.srt}"; TMP=$(mktemp -d)
ffmpeg -loglevel error -y -i "$IN" -vn -ar 16000 -ac 1 -c:a pcm_s16le "$TMP/a.wav"
$W/build/bin/whisper-cli -m $M -f "$TMP/a.wav" -ml 1 -sow -dtw small.en -osrt -of "$TMP/raw" -np -t $(nproc) >/dev/null 2>&1
python3 - "$TMP/raw.srt" "$OUT" <<'PY'
import sys,re
b=re.split(r'\n\s*\n',open(sys.argv[1],encoding='utf-8').read().strip()); out=[]
for x in b:
    l=x.split('\n')
    if len(l)>=3 and ' '.join(l[2:]).strip(): out.append((l[1],' '.join(l[2:]).strip()))
open(sys.argv[2],'w',encoding='utf-8').write('\n\n'.join(f"{i}\n{ts}\n{t}" for i,(ts,t) in enumerate(out,1))+'\n')
print(len(out),'words ->',sys.argv[2])
PY
rm -rf "$TMP"
