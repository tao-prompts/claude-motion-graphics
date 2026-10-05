"""Recover which source shot + source time each frame of a draft/mock-up uses.
CLI: python match_frames.py draft.mp4 shot1.mp4 shot2.mp4 ...   -> prints every 6th frame and writes draft_map.json
Low error (<15) = full-frame use of that shot; high error = shot shown in a card/overlay or with effects."""
import sys, json, cv2, numpy as np
def thumbs(path):
    c = cv2.VideoCapture(path); out = []; fps = c.get(cv2.CAP_PROP_FPS) or 24
    while True:
        ok, f = c.read()
        if not ok: break
        out.append(cv2.resize(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY), (96, 54)).astype(np.float32))
    return np.array(out), fps
if __name__ == '__main__':
    D, dfps = thumbs(sys.argv[1]); S = {p: thumbs(p) for p in sys.argv[2:]}; res = []
    for i, g in enumerate(D):
        best = (1e9, None, None)
        for p, (A, fps) in S.items():
            e = np.abs(A - g[None]).mean((1, 2)); j = int(e.argmin())
            if e[j] < best[0]: best = (float(e[j]), p, j / fps)
        res.append({'t': i / dfps, 'err': best[0], 'shot': best[1], 'src_t': best[2]})
    for r in res[::6]: print(f"{r['t']:6.2f}s err {r['err']:6.1f}  {r['shot'].split('/')[-1]:28s} src {r['src_t']:5.2f}s")
    json.dump(res, open('draft_map.json', 'w'))
