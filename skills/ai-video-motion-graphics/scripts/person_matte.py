"""Person matte without ML: propagated GrabCut at half-res + guided-filter refine + temporal blend.

  python person_matte.py FRAMES_DIR OUT_DIR N --face X,Y --torso X0,Y0,X1,Y1 [--bg-rect X0,Y0,X1,Y1 ...]
                         [--static-fg "x,y x,y x,y ..."] [--orange-bg]

All coordinates are FULL-RES (1920x1080) frame pixels. Seeds only matter on frame 1; later frames propagate.
--static-fg: polygon always foreground (locked-off camera: desk/laptop in front of the UI panel).
--orange-bg: treat saturated bright orange pixels (lamps/lanterns) right of the face as background.
Check a few frames over a green plate before rendering: leaks into furniture below the text zone are harmless.
"""
import cv2, numpy as np, os, argparse
def guided(I, p, r, eps):
    mI = cv2.boxFilter(I, -1, (r, r)); mp = cv2.boxFilter(p, -1, (r, r))
    cIp = cv2.boxFilter(I * p, -1, (r, r)) - mI * mp; vI = cv2.boxFilter(I * I, -1, (r, r)) - mI * mI
    a = cIp / (vI + eps); b = mp - a * mI
    return cv2.boxFilter(a, -1, (r, r)) * I + cv2.boxFilter(b, -1, (r, r))
ap = argparse.ArgumentParser()
ap.add_argument('frames'); ap.add_argument('out'); ap.add_argument('n', type=int)
ap.add_argument('--face', required=True); ap.add_argument('--torso', required=True)
ap.add_argument('--bg-rect', action='append', default=[]); ap.add_argument('--static-fg', default=None)
ap.add_argument('--orange-bg', action='store_true')
A = ap.parse_args(); os.makedirs(A.out, exist_ok=True)
h2 = lambda v: [int(int(c) / 2) for c in v.split(',')]
fx, fy = h2(A.face); tx0, ty0, tx1, ty1 = h2(A.torso)
static = None
if A.static_fg:
    static = np.zeros((1080, 1920), np.float32)
    cv2.fillPoly(static, [np.int32([[int(c) for c in p.split(',')] for p in A.static_fg.split()])], 1.0)
    static = cv2.GaussianBlur(static, (0, 0), 1.5)
prev = None; pf = None
for i in range(1, A.n + 1):
    im = cv2.imread(f'{A.frames}/{i:04d}.jpg'); sm = cv2.resize(im, (960, 540), interpolation=cv2.INTER_AREA)
    mask = np.full((540, 960), cv2.GC_BGD if prev is None else cv2.GC_PR_BGD, np.uint8)
    if prev is None:
        mask[max(0, fy - 150):540, max(0, tx0 - 60):min(960, tx1 + 60)] = cv2.GC_PR_FGD
        cv2.ellipse(mask, (fx, fy), (60, 80), 0, 0, 360, cv2.GC_FGD, -1); mask[ty0:ty1, tx0:tx1] = cv2.GC_FGD
    else:
        k = np.ones((7, 7), np.uint8); fg = cv2.erode(prev, k, iterations=2); band = cv2.dilate(prev, k, iterations=3)
        mask[band > 0] = cv2.GC_PR_FGD; mask[band == 0] = cv2.GC_BGD; mask[fg > 0] = cv2.GC_FGD
    for r in A.bg_rect:
        x0, y0, x1, y1 = h2(r); mask[y0:y1, x0:x1] = cv2.GC_BGD
    if A.orange_bg:
        hsv = cv2.cvtColor(sm, cv2.COLOR_BGR2HSV); org = (hsv[:, :, 1] > 110) & (hsv[:, :, 2] > 150) & (hsv[:, :, 0] < 30)
        org[:, :fx + 120] = False; mask[org] = cv2.GC_BGD
    bg = np.zeros((1, 65)); fgm = np.zeros((1, 65))
    cv2.grabCut(sm, mask, None, bg, fgm, 4 if prev is None else 2, cv2.GC_INIT_WITH_MASK)
    m = np.where((mask == 1) | (mask == 3), 1, 0).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    if n > 1: m = (lab == 1 + np.argmax(st[1:, 4])).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8)); prev = m
    full = cv2.resize(m.astype(np.float32), (1920, 1080))
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255
    a = np.clip(guided(g, full, 21, 2e-4), 0, 1); a = np.clip(guided(g, a, 9, 1e-4), 0, 1)
    if pf is not None: a = 0.7 * a + 0.3 * pf
    pf = a
    if static is not None: a = np.maximum(a, static)
    cv2.imwrite(f'{A.out}/{i:04d}.png', (a * 255).astype(np.uint8))
print('done', A.n)
