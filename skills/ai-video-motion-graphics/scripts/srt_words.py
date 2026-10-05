"""Parse a word-level SRT -> [(start, end, word)].  CLI: python srt_words.py file.srt"""
import re, sys
def _s(x): h, m, r = x.split(':'); s, ms = r.split(','); return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000
def read_srt(path):
    t = open(path, encoding='utf-8').read()
    b = re.findall(r'\d+\s*\n(\d\d:\d\d:\d\d,\d\d\d) --> (\d\d:\d\d:\d\d,\d\d\d)\s*\n(.*?)(?:\n\s*\n|\Z)', t, re.S)
    return [(_s(a), _s(c), w.strip()) for a, c, w in b]
def find(words, token, after=0.0):
    """first start time of `token` (case-insensitive, punctuation stripped) at/after `after`"""
    tok = re.sub(r'\W', '', token.lower())
    for s, e, w in words:
        if s >= after and re.sub(r'\W', '', w.lower()) == tok: return s
    return None
if __name__ == '__main__':
    print(' '.join(f"[{s:.2f}]{w}" for s, e, w in read_srt(sys.argv[1])))
