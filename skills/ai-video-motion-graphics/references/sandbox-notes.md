# Sandbox & rendering notes

## Media I/O
- Extract frames with ffmpeg (`ffmpeg -i in.mp4 -vf "fps=24,scale=W:H" -q:v 2 dir/%04d.jpg`), then `cv2.imread`. `cv2.VideoCapture` seeking is fine for quick analysis but unreliable for exact frame work.
- Pre-scale extracted frames to the size they'll be displayed (card size) — faster renders, sharper downscale (INTER_AREA).
- Output: write JPG q96 frames, encode `libx264 -preset slow -crf 16/17 -pix_fmt yuv420p -movflags +faststart`, audio `aac 256k`, `-shortest`.
- `soundfile` may be missing — use `scipy.io.wavfile`. Extract audio with `ffmpeg -vn -ac 2 -ar 48000`.
- AI video clips often come at 1926×1076 / 24 fps; talking heads 1920×1080 / 30 fps. Map times explicitly (`src_frame = round(src_t*24)`), don't assume equal fps.

## Long renders
- Run in the background so tool calls don't time out:
  `setsid nohup python3 render.py A B > log.txt 2>&1 < /dev/null &` then poll `ls out | wc -l` with `sleep`.
- Memory: two workers each holding full-res mattes/arrays can get killed silently (no error in log, frame count stalls). If a worker dies, resume from the last frame with one worker.
- **Disk fills up**: each render folder of 1080p JPGs is 300 MB–1.2 GB. Check `df -h` before renders; delete frame folders of already-encoded versions. If `ls out | wc -l` is lower than the log says, suspect a full disk (cv2.imwrite fails silently).
- A crash mid-render prints a traceback in the log — fix and resume from that frame; don't re-render finished frames.
- Re-render only changed frame ranges when iterating; copy unchanged frames from the previous output folder.

## Network
- Package managers (pip/npm) usually work; model hosts are often blocked by default. **Word-level SRT via whisper.cpp works once the org allowlist has `huggingface.co` AND `*.hf.co`** (the model download redirects to us.aws.cdn.hf.co / cas-bridge.xethub.hf.co) - run `scripts/word_srt.sh input.mp4` (builds whisper.cpp, small.en q5_1, `-ml 1 -sow -dtw small.en`, strips empty entries; ~17 s for a 20 s clip on 2 CPUs). If blocked, ask the user to allowlist those domains or for an SRT export. A Hugging Face MCP connector does NOT unblock file downloads. Mattes: `scripts/person_matte.py` (GrabCut + guided filter).
- Files generated on external services (e.g. Artlist) may not be downloadable from the sandbox; ask the user to download and upload them.

## Fonts available (typical)
- `/usr/share/fonts/truetype/google-fonts/`: Poppins (Bold/Medium/Regular/Light), Lora Variable/Italic.
- DejaVu Sans / Serif / Sans Mono (use Mono for code panels). Some glyphs (✓ in Poppins) render as tofu — draw icons with shapes instead.

## Verification habits
- Always view contact sheets of test frames and zoomed crops before full renders, and a contact sheet of the final encode.
- You can't hear audio — say so, and give the user an SFX stem so they can rebalance.

## Files from the user's computer
- Stage media from the connected folder with the device bridge; commit deliverables back beside the sources with versioned names (`Intro_MotionGraphics_vN.mp4`, `Intro_SFX_stem_vN.wav`). A commit can fail with HTTP 503 - retry once, otherwise say which file stayed in the chat.
- User-dropped extras in the folder (e.g. `frame-53.png`, a new background PNG) are referenced by name in feedback - re-list the folder each round.

## Performance
- 660 frames (22 s) of 1080p with mattes + warped glass render in ~5 min with 2 background workers on 2 CPUs. For small fixes re-render only the affected frame range into the existing `out/` and re-encode.
- If the user interrupts a long render with new feedback, apply all of it and test a few frames before re-launching.
