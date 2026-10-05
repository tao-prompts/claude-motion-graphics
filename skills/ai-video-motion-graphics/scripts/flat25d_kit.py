"""
flat25d_kit.py - Mode F (flat 2.5D animated explainer) toolkit for the ai-video-motion-graphics skill.

Everything is drawn with skia-python into 1920x1080 RGB frames:
  shape()        two-tone cel shape (base + hard shadow crescent + light rim) + banded overlay + grain texture
  band_fill()    "2.5D" shading: solid colour segments instead of smooth gradients
  wcirc/wpoly    slightly imperfect, hand-drawn outlines
  IsoR / iso_island / IsoRot / holo_island   rounded isometric blocks, biome islands, rotating cyan holograms
  person / dog / alien_profile / alien_back  characters (person() has 2-bone IK via hands_at=[(lx,ly),(rx,ry)])
  shop / ftower / esb / liberty / taxi ...   environment props (landmarks drawn in the same style)
  wire_version / block_mask / glitch_np / cyan_tint / zoom_img   glitch + transition building blocks
  post()         saturation lift, bloom, vignette, grain (call once per frame)
See examples/flat25d_example.py for a complete scene + render loop.
Requires: pip install skia-python numpy opencv-python-headless scipy
"""
import os, math, glob
import numpy as np, cv2, skia

W, H, FPS = 1920, 1080, 30
_HERE = os.path.dirname(os.path.abspath(__file__))
def _find_font(names):
    dirs = [os.path.join(_HERE, '..', 'assets', 'fonts'), os.path.join(_HERE, 'fonts'), '/usr/share/fonts', '/Library/Fonts', os.path.expanduser('~/Library/Fonts'), 'C:/Windows/Fonts']
    for d in dirs:
        for n in names:
            hits = glob.glob(os.path.join(d, '**', n), recursive=True)
            if hits: return skia.Typeface.MakeFromFile(hits[0])
    return skia.Typeface.MakeDefault() if hasattr(skia.Typeface, 'MakeDefault') else skia.Typeface('')
TF = _find_font(['Poppins-Bold.ttf'])
TFM = _find_font(['Poppins-Medium.ttf', 'Poppins-Bold.ttf'])
MONO = _find_font(['DejaVuSansMono.ttf', 'Menlo.ttc', 'consola.ttf'])
_fonts = {}

INK, GRN, YEL = '#1A0F3A', '#5CFF8A', '#FFD000'
PNK, CY_, GOLD, DARK, SHADOWC = '#FF2E9A', '#3FE6FF', '#FFB320', '#12052E', '#1E0C4A'
# ---- from anim
def rgb(h):
    h = h.lstrip('#'); return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)

def col(h, a=1.0):
    r, g, b = rgb(h); return skia.ColorSetARGB(int(max(0, min(1, a)) * 255), r, g, b)

def mix(h1, h2, k):
    a, b = rgb(h1), rgb(h2); return '#%02X%02X%02X' % tuple(int(a[i] * (1 - k) + b[i] * k) for i in range(3))

def P(h, a=1.0, blur=0, stroke=0, shader=None, dash=None):
    p = skia.Paint(AntiAlias=True, Color=col(h, a))
    if blur: p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    if stroke:
        p.setStyle(skia.Paint.kStroke_Style); p.setStrokeWidth(stroke)
        p.setStrokeCap(skia.Paint.kRound_Cap); p.setStrokeJoin(skia.Paint.kRound_Join)
    if shader is not None: p.setShader(shader)
    if dash: p.setPathEffect(skia.DashPathEffect.Make(dash[0], dash[1]))
    return p

def cl(x, a=0.0, b=1.0): return max(a, min(b, x))

def prog(t, t0, d): return cl((t - t0) / d)

def eo(x): return 1 - (1 - x) ** 3

def ei(x): return x ** 3

def eio(x): return 3 * x * x - 2 * x ** 3

def back(x, s=1.9):
    x = cl(x); return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2

def popk(t, t0, d=0.45): return back(prog(t, t0, d)) if t >= t0 else 0.0

def fade(t, t0, t1, d=0.25):
    return cl((t - t0) / d) * cl((t1 - t) / d)

def lerp(a, b, k): return a + (b - a) * k

def qb(p0, c, p2, k):
    return ((1 - k) ** 2 * p0[0] + 2 * (1 - k) * k * c[0] + k * k * p2[0], (1 - k) ** 2 * p0[1] + 2 * (1 - k) * k * c[1] + k * k * p2[1])

def blink(t, seed):
    per = 3.1 + seed * 0.7; ph = (t + seed * 1.37) % per
    if ph < 0.14: return 0.08 + 0.92 * abs(ph - 0.07) / 0.07
    return 1.0

def circle(cv, x, y, r, p): cv.drawCircle(x, y, r, p)

def oval(cv, x, y, rx, ry, p): cv.drawOval(skia.Rect.MakeLTRB(x - rx, y - ry, x + rx, y + ry), p)

def rrect(cv, x, y, w, h, r, p): cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x - w / 2, y - h / 2, w, h), r, r), p)

def star4(cv, x, y, r, p, th=0.18):
    pa = skia.Path(); pa.moveTo(x, y - r)
    pa.quadTo(x + r * th, y - r * th, x + r, y); pa.quadTo(x + r * th, y + r * th, x, y + r)
    pa.quadTo(x - r * th, y + r * th, x - r, y); pa.quadTo(x - r * th, y - r * th, x, y - r); pa.close()
    cv.drawPath(pa, p)

def text(cv, s, x, y, sz, h='#FFFFFF', a=1.0, glow=None, shadow=True, tf=None):
    f = font(sz, tf); w = f.measureText(s); bx, by = x - w / 2, y + sz * 0.35
    if a <= 0: return w
    if glow: cv.drawString(s, bx, by, f, P(glow, 0.7 * a, blur=sz * 0.18))
    if shadow: cv.drawString(s, bx, by + sz * 0.06, f, P(INK, 0.55 * a, blur=2))
    cv.drawString(s, bx, by, f, P(h, a))
    return w

def pill(cv, s, x, y, sz, bg, fg, a=1.0, k=1.0):
    if k <= 0 or a <= 0: return
    cv.save(); cv.translate(x, y); cv.scale(k, k)
    w = font(sz).measureText(s) + sz * 1.3; h = sz * 1.7
    rrect(cv, 0, 6, w, h, h / 2, P(INK, 0.45 * a, blur=6))
    rrect(cv, 0, 0, w, h, h / 2, P(bg, a))
    text(cv, s, 0, 0, sz, fg, a, shadow=False)
    cv.restore()

def trail(cv, pts, width, h, a=1.0, glow=True):
    n = len(pts)
    if n < 2: return
    for g in ([1, 0] if glow else [0]):
        for i in range(n - 1):
            k = 1 - i / (n - 1)
            w = width * (0.15 + 0.85 * k) * (2.2 if g else 1)
            p = P(h if not g else h, a * k * (0.35 if g else 0.9), blur=width * 0.6 if g else 0, stroke=w)
            cv.drawLine(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], p)

def burst(cv, x, y, t, t0, n, h, seed, spd=420, life=0.7, sz=10):
    if t < t0 or t > t0 + life: return
    rs = np.random.default_rng(seed); u = (t - t0) / life
    for i in range(n):
        ang = rs.uniform(0, 2 * np.pi); v = spd * rs.uniform(0.4, 1.0); s = sz * rs.uniform(0.6, 1.3)
        d = v * life * eo(u) * 0.6
        px, py = x + math.cos(ang) * d, y + math.sin(ang) * d
        star4(cv, px, py, s * (1 - u), P(h, 1 - u * 0.7))
        star4(cv, px, py, s * 1.8 * (1 - u), P(h, 0.4 * (1 - u), blur=s * 0.6))

def new():
    s = skia.Surface(W, H); return s

def toarr(s):
    return s.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)[:, :, :3].copy()

def cam(cv, cx, cy, z, rot=0.0):
    cv.translate(W / 2, H / 2); cv.scale(z, z); cv.rotate(rot); cv.translate(-cx, -cy)

def font(sz, tf=None):
    k = (sz, id(tf))
    if k not in _fonts: _fonts[k] = skia.Font(tf or TF, sz)
    return _fonts[k]

def check(cv, x, y, r, a=1.0, k=1.0):
    if k <= 0: return
    cv.save(); cv.translate(x, y); cv.scale(k, k)
    circle(cv, 0, 0, r * 1.3, P(GRN, 0.5 * a, blur=r * 0.4)); circle(cv, 0, 0, r, P('#22C55E', a))
    pa = skia.Path(); pa.moveTo(-r * 0.45, 0); pa.lineTo(-r * 0.1, r * 0.35); pa.lineTo(r * 0.5, -r * 0.35)
    cv.drawPath(pa, P('#FFFFFF', a, stroke=r * 0.22)); cv.restore()

# ---- from anim2
def rotm(ax, ay, az):
    cx, sx, cy, sy, cz, sz = math.cos(ax), math.sin(ax), math.cos(ay), math.sin(ay), math.cos(az), math.sin(az)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]]); Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]); Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx

def vgrad(cv, x0, y0, x1, y1, cols):
    sh = skia.GradientShader.MakeLinear([skia.Point(x0, y0), skia.Point(x1, y1)], [col(c) for c in cols])
    return P('#FFFFFF', shader=sh)

def text3d(cv, s, x, y, sz, top, side, a=1.0, glow=None, rot=0.0, k=1.0, depth=None):
    if k <= 0 or a <= 0: return
    depth = depth or max(4, int(sz * 0.09))
    cv.save(); cv.translate(x, y); cv.rotate(rot); cv.scale(k, k)
    if glow: text(cv, s, 0, depth * 0.5, sz, glow, a * 0.9, glow=glow, shadow=False)
    text(cv, s, depth * 0.4, depth + sz * 0.05, sz, SHADOWC, 0.55 * a, shadow=False)
    for d in range(depth, 0, -1): text(cv, s, d * 0.35, d, sz, side, a, shadow=False)
    text(cv, s, 0, 0, sz, top, a, shadow=False)
    cv.restore()

def lpulse(cv, x, y, r, t, a=1.0):
    circle(cv, x, y, r * 5, P('#4FC8FF', 0.22 * a, blur=r * 2))
    circle(cv, x, y, r * 2.2, P('#BFF4FF', 0.55 * a, blur=r * 0.8))
    oval(cv, x, y, r * 10, r * 0.22, P('#9FEFFF', 0.6 * a, blur=r * 0.15))
    oval(cv, x, y, r * 5, r * 0.08, P('#FFFFFF', 0.8 * a))
    cv.save(); cv.translate(x, y); cv.rotate(t * 20)
    star4(cv, 0, 0, r * 3.0, P('#FFFFFF', 0.55 * a), th=0.05); cv.rotate(45); star4(cv, 0, 0, r * 1.8, P('#CFF7FF', 0.45 * a), th=0.05)
    cv.restore()
    circle(cv, x, y, r, P('#FFFFFF', a)); circle(cv, x, y, r * 1.25, P('#FFFFFF', 0.6 * a, blur=r * 0.25))

def holo(cv, quad, w, h, hc, a, content, t=0.0):
    if a <= 0: return
    m = skia.Matrix(); m.setPolyToPoly([skia.Point(0, 0), skia.Point(w, 0), skia.Point(w, h), skia.Point(0, h)], [skia.Point(*q) for q in quad])
    cv.save(); cv.concat(m)
    rrect(cv, w / 2, h / 2, w + 30, h + 30, 30, P(hc, 0.35 * a, blur=26))
    rrect(cv, w / 2, h / 2, w, h, 22, P(mix(hc, INK, 0.75), 0.82 * a))
    cv.save(); cv.clipRRect(skia.RRect.MakeRectXY(skia.Rect.MakeWH(w, h), 22, 22), doAntiAlias=True)
    for yy in range(0, int(h), 7): cv.drawLine(0, yy + (t * 30) % 7, w, yy + (t * 30) % 7, P(hc, 0.07 * a, stroke=2))
    cv.drawRect(skia.Rect.MakeWH(w, 56), P(hc, 0.85 * a))
    cv.restore()
    rrect(cv, w / 2, h / 2, w, h, 22, P(hc, a, stroke=4))
    for (cx_, cy_, sx, sy) in ((0, 0, 1, 1), (w, 0, -1, 1), (w, h, -1, -1), (0, h, 1, -1)):
        pa = skia.Path(); pa.moveTo(cx_ + sx * -12, cy_ + sy * 40); pa.lineTo(cx_ + sx * -12, cy_ + sy * -12); pa.lineTo(cx_ + sx * 40, cy_ + sy * -12)
        cv.drawPath(pa, P('#FFFFFF', 0.85 * a, stroke=5))
    content(cv, w, h, a)
    cv.restore()

# ---- from flat
def lin(x0, y0, x1, y1, cols, pos=None):
    sh = skia.GradientShader.MakeLinear([skia.Point(x0, y0), skia.Point(x1, y1)], [col(c) if isinstance(c, str) else c for c in cols], pos)
    return skia.Paint(AntiAlias=True, Shader=sh)

def rad(x, y, r, cols, pos=None):
    sh = skia.GradientShader.MakeRadial(skia.Point(x, y), r, [col(c) if isinstance(c, str) else c for c in cols], pos)
    return skia.Paint(AntiAlias=True, Shader=sh)

def colA(h, a): return col(h, a)

def circ_path(x, y, r):
    p = skia.Path(); p.addCircle(x, y, r); return p

def blob_path(circles):
    p = skia.Path()
    for (x, y, r) in circles: p.addCircle(x, y, r)
    return p

def rr_path(x, y, w, h, r):
    p = skia.Path(); p.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x - w / 2, y - h / 2, w, h), r, r)); return p

def poly_path(pts, rnd=0):
    p = skia.Path(); p.moveTo(*pts[0])
    for q in pts[1:]: p.lineTo(*q)
    p.close(); return p

def rpoly(cv, pts, paint, rnd=8):
    paint.setPathEffect(skia.CornerPathEffect.Make(rnd)); cv.drawPath(poly_path(pts), paint)

def rays(cv, x, y, n, hc, a, rot=0.0, width=0.09, R=2600):
    for k in range(n):
        ang = math.radians(rot + k * 360 / n)
        p = skia.Path(); p.moveTo(x, y)
        p.lineTo(x + math.cos(ang - width) * R, y + math.sin(ang - width) * R); p.lineTo(x + math.cos(ang + width) * R, y + math.sin(ang + width) * R); p.close()
        cv.drawPath(p, P(hc, a))

def bokeh(cv, seed, n, cols, t, a=1.0, rmin=10, rmax=60, W=1920, H=1080):
    rs = np.random.default_rng(seed); D = rs.uniform(0, 1, (n, 5))
    for i in range(n):
        x = (D[i, 0] * W + t * 8 * (D[i, 3] - 0.5)) % W; y = (D[i, 1] * H + t * 6 * (D[i, 4] - 0.5)) % H
        r = rmin + (rmax - rmin) * D[i, 2]
        circle(cv, x, y, r, P(cols[i % len(cols)], a * (0.15 + 0.25 * D[i, 3]), blur=r * 0.3))

def sparkles(cv, seed, n, t, hc='#FFFFFF', a=1.0, W=1920, H=1080, smin=4, smax=12):
    rs = np.random.default_rng(seed); D = rs.uniform(0, 1, (n, 4))
    for i in range(n):
        tw = 0.5 + 0.5 * math.sin(t * (1.5 + 2 * D[i, 2]) + D[i, 3] * 6)
        star4(cv, D[i, 0] * W, D[i, 1] * H, (smin + (smax - smin) * D[i, 2]) * (0.5 + 0.5 * tw), P(hc, a * (0.3 + 0.7 * tw)), th=0.12)

def glitch_np(img, t, amp, seed=0, band=None):
    import cv2
    rs = np.random.default_rng(int(t * 100) + seed); out = img.copy(); H, W = img.shape[:2]
    edges = np.sort(rs.integers(0, H, 14))
    for y0, y1 in zip(np.r_[0, edges], np.r_[edges, H]):
        if rs.random() < 0.6: out[y0:y1] = np.roll(img[y0:y1], int(rs.uniform(-1, 1) * 160 * amp), axis=1)
    for _ in range(int(10 * amp)):
        x0, y0 = rs.integers(0, W - 200), rs.integers(0, H - 120); w_, h_ = rs.integers(80, 360), rs.integers(30, 140)
        blk = out[y0:y0 + h_, x0:x0 + w_]
        if blk.size: out[y0:y0 + h_, x0:x0 + w_] = cv2.resize(cv2.resize(blk, (max(1, w_ // 16), max(1, h_ // 16)), interpolation=cv2.INTER_AREA), (blk.shape[1], blk.shape[0]), interpolation=cv2.INTER_NEAREST)
    sh = int(18 * amp); out[:, :, 0] = np.roll(out[:, :, 0], sh, 1); out[:, :, 2] = np.roll(out[:, :, 2], -sh, 1)
    return out

def bubble(cv, x, y, s, icon, k):
    if k <= 0: return
    cv.save(); cv.translate(x, y); cv.scale(k, k)
    circle(cv, -0.4 * s, 0.8 * s, 0.1 * s, P('#FFFFFF')); circle(cv, -0.2 * s, 0.55 * s, 0.15 * s, P('#FFFFFF'))
    rrect(cv, 4, 8, 1.35 * s, 1.0 * s, 0.48 * s, P('#2A0F5C', 0.25))
    rrect(cv, 0, 0, 1.35 * s, 1.0 * s, 0.48 * s, P('#FFFFFF'))
    if icon == 'bulb':
        circle(cv, 0, -0.07 * s, 0.34 * s, P('#FFD23F', 0.5, blur=0.12 * s)); circle(cv, 0, -0.07 * s, 0.25 * s, P('#FFD23F'))
        rrect(cv, 0, 0.25 * s, 0.2 * s, 0.14 * s, 0.04 * s, P('#8C85B8')); circle(cv, -0.08 * s, -0.15 * s, 0.07 * s, P('#FFFFFF', 0.9))
    elif icon == 'heart':
        pa = skia.Path(); pa.moveTo(0, 0.27 * s)
        pa.cubicTo(-0.58 * s, -0.12 * s, -0.26 * s, -0.5 * s, 0, -0.19 * s); pa.cubicTo(0.26 * s, -0.5 * s, 0.58 * s, -0.12 * s, 0, 0.27 * s); pa.close()
        cv.drawPath(pa, P('#FF4F7A'))
    elif icon == 'note':
        circle(cv, -0.1 * s, 0.15 * s, 0.13 * s, P('#7B3FF2')); cv.drawLine(0.02 * s, 0.15 * s, 0.02 * s, -0.3 * s, P('#7B3FF2', 1, stroke=0.07 * s)); cv.drawLine(0.02 * s, -0.3 * s, 0.22 * s, -0.2 * s, P('#7B3FF2', 1, stroke=0.07 * s))
    elif icon == 'smile':
        circle(cv, 0, 0, 0.3 * s, P('#FFD23F')); circle(cv, -0.1 * s, -0.06 * s, 0.04 * s, P(INK)); circle(cv, 0.1 * s, -0.06 * s, 0.04 * s, P(INK))
        pa = skia.Path(); pa.moveTo(-0.14 * s, 0.07 * s); pa.quadTo(0, 0.2 * s, 0.14 * s, 0.07 * s); cv.drawPath(pa, P(INK, 1, stroke=0.05 * s))
    cv.restore()

# ---- from sim
def _noise_tex(n=256, seed=2):
    rs = np.random.default_rng(seed); acc = np.zeros((n, n), np.float32)
    for sc, amp in ((4, 1.0), (8, 0.6), (32, 0.35), (128, 0.25)):
        g = rs.standard_normal((sc, sc)).astype(np.float32)
        g = cv2.resize(g, (n, n), interpolation=cv2.INTER_CUBIC); acc += g * amp
    fine = rs.standard_normal((n, n)).astype(np.float32) * 0.35
    acc = acc / acc.std() * 0.55 + fine
    v = np.clip(128 + acc * 22, 0, 255).astype(np.uint8)
    a = np.dstack([v, v, v, np.full_like(v, 255)])
    return skia.Image.fromarray(np.ascontiguousarray(a), colorType=skia.kRGBA_8888_ColorType)

def pin(cv, x, y, s, hc, label, a=1.0, k=1.0):
    if k <= 0: return
    cv.save(); cv.translate(x, y); cv.scale(k, k)
    pa = skia.Path(); pa.moveTo(0, 0); pa.cubicTo(-0.2 * s, -0.35 * s, -0.55 * s, -0.6 * s, -0.55 * s, -1.0 * s)
    pa.cubicTo(-0.55 * s, -1.35 * s, -0.3 * s, -1.55 * s, 0, -1.55 * s); pa.cubicTo(0.3 * s, -1.55 * s, 0.55 * s, -1.35 * s, 0.55 * s, -1.0 * s)
    pa.cubicTo(0.55 * s, -0.6 * s, 0.2 * s, -0.35 * s, 0, 0); pa.close()
    cv.save(); cv.translate(6, 10); cv.drawPath(pa, P(SHADOWC, 0.4 * a, blur=8)); cv.restore()
    cv.drawPath(pa, vgrad(cv, -0.55 * s, 0, 0.55 * s, 0, [mix(hc, '#FFFFFF', 0.25), hc, mix(hc, INK, 0.3)]))
    circle(cv, 0, -1.0 * s, 0.24 * s, P('#FFFFFF', a))
    cv.drawArc(skia.Rect.MakeLTRB(-0.45 * s, -1.45 * s, 0.45 * s, -0.55 * s), 200, 60, False, P('#FFFFFF', 0.6 * a, stroke=0.06 * s))
    cv.restore()
    if label: pill(cv, label, x, y - 1.95 * s * k, 34, hc, '#FFFFFF', a, k)

def cursor(cv, x, y, s, a=1.0):
    pa = skia.Path(); pts = [(0, 0), (0, 1.0), (0.26, 0.76), (0.44, 1.16), (0.6, 1.09), (0.42, 0.7), (0.76, 0.7)]
    pa.moveTo(x + pts[0][0] * s, y + pts[0][1] * s)
    for (u, v) in pts[1:]: pa.lineTo(x + u * s, y + v * s)
    pa.close()
    cv.save(); cv.translate(10, 16); cv.drawPath(pa, P(SHADOWC, 0.5 * a, blur=12)); cv.restore()
    p = P('#FFFFFF', a); p.setPathEffect(skia.CornerPathEffect.Make(s * 0.04)); cv.drawPath(pa, p)
    p = P('#1A1240', a, stroke=s * 0.05); p.setPathEffect(skia.CornerPathEffect.Make(s * 0.04)); cv.drawPath(pa, p)

def magnifier(cv, x, y, r, a=1.0):
    cv.save(); cv.translate(x, y)
    cv.drawLine(r * 0.72, r * 0.72, r * 1.75, r * 1.75, P('#3A2A80', a, stroke=r * 0.32)); cv.drawLine(r * 0.75, r * 0.75, r * 1.7, r * 1.7, P('#6A55D0', a, stroke=r * 0.2))
    circle(cv, 0, 0, r, P('#BFEAFF', 0.18 * a)); circle(cv, 0, 0, r, P('#F2EFFC', a, stroke=r * 0.16)); circle(cv, 0, 0, r * 1.08, P('#9C93C8', a, stroke=r * 0.04))
    cv.drawArc(skia.Rect.MakeLTRB(-r * 0.7, -r * 0.7, r * 0.7, r * 0.7), 200, 60, False, P('#FFFFFF', 0.7 * a, stroke=r * 0.07))
    cv.restore()

def dust(cv, t, n=40, seed=5, a=1.0, hc='#CDB8FF'):
    rs = np.random.default_rng(seed); D = rs.uniform(0, 1, (n, 5))
    for i in range(n):
        x = (D[i, 0] * W + t * (10 + 30 * D[i, 2])) % W; y = (D[i, 1] * H - t * (8 + 20 * D[i, 3])) % H
        circle(cv, x, y, 1.2 + 2.5 * D[i, 2], P(hc, a * (0.15 + 0.35 * D[i, 4])))

# ---- from art
def smooth_path(pts):
    n = len(pts); p = skia.Path(); p.moveTo(*pts[0])
    for i in range(n):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6); c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        p.cubicTo(*c1, *c2, *p2)
    p.close(); return p

def round_path(pts, r):
    n = len(pts); p = skia.Path()
    for i in range(n):
        p0, p1, p2 = pts[i - 1], pts[i], pts[(i + 1) % n]
        d1 = math.dist(p0, p1) + 1e-6; d2 = math.dist(p1, p2) + 1e-6; rr = min(r, d1 * 0.45, d2 * 0.45)
        a = (p1[0] + (p0[0] - p1[0]) * rr / d1, p1[1] + (p0[1] - p1[1]) * rr / d1); b = (p1[0] + (p2[0] - p1[0]) * rr / d2, p1[1] + (p2[1] - p1[1]) * rr / d2)
        (p.moveTo if i == 0 else p.lineTo)(*a); p.quadTo(*p1, *b)
    p.close(); return p

def wnoise(seed, a):
    rs = np.random.default_rng(abs(int(seed)) % 100000); ph = rs.uniform(0, 6.3, 4)
    return 0.5 * math.sin(2 * a + ph[0]) + 0.3 * math.sin(3 * a + ph[1]) + 0.2 * math.sin(5 * a + ph[2])

def wcirc(x, y, r, seed=0, amp=0.04, n=36):
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n; rr = r * (1 + amp * wnoise(seed, a)); pts.append((x + rr * math.cos(a), y + rr * math.sin(a)))
    return smooth_path(pts)

def woval(x, y, rx, ry, seed=0, amp=0.04, n=36):
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n; f = 1 + amp * wnoise(seed, a); pts.append((x + rx * f * math.cos(a), y + ry * f * math.sin(a)))
    return smooth_path(pts)

def wblob(circles, seed=0, amp=0.05):
    p = skia.Path()
    for i, (x, y, r) in enumerate(circles): p.addPath(wcirc(x, y, r, seed + i, amp))
    return p

def wpoly(pts, r=8, seed=0, amp=2.5, step=40):
    out = []; n = len(pts); s = 0
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]; L = math.dist(a, b); m = max(1, int(L / step))
        nx, ny = (-(b[1] - a[1]) / (L + 1e-6), (b[0] - a[0]) / (L + 1e-6))
        for j in range(m):
            k = j / m; off = 0 if j == 0 else amp * wnoise(seed, s * 0.05)
            out.append((a[0] + (b[0] - a[0]) * k + nx * off, a[1] + (b[1] - a[1]) * k + ny * off)); s += L / m
    return round_path(out, r)

def band_fill(cv, path, p0, p1, cols, a=1.0):
    cv.save(); cv.clipPath(path, doAntiAlias=True)
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]; L = math.hypot(dx, dy) + 1e-6; ux, uy = dx / L, dy / L; nx, ny = -uy, ux; n = len(cols); big = 5000
    for i, c in enumerate(cols):
        t0 = i / n * L - (big if i == 0 else 0); t1 = (i + 1) / n * L + (big if i == n - 1 else 0)
        q = [(p0[0] + ux * t0 + nx * big, p0[1] + uy * t0 + ny * big), (p0[0] + ux * t1 + nx * big, p0[1] + uy * t1 + ny * big),
             (p0[0] + ux * t1 - nx * big, p0[1] + uy * t1 - ny * big), (p0[0] + ux * t0 - nx * big, p0[1] + uy * t0 - ny * big)]
        pp = skia.Path(); pp.moveTo(*q[0]); [pp.lineTo(*z) for z in q[1:]]; pp.close()
        cv.drawPath(pp, P(c, a) if isinstance(c, str) else P(c[0], c[1] * a))
    cv.restore()

def ramp(base, n=4, hi=0.2, lo=0.3):
    return [mix(base, '#FFFFFF', hi * (1 - i / (n - 1)) * 1.0) if i < (n - 1) / 2 else mix(base, DARK, lo * (i / (n - 1))) for i in range(n)]

def finish(cv, path, seed=0, tex=0.32, grad=1.0, light=(-1, -1), blot=True):
    b = path.getBounds(); x0, y0, x1, y1 = b.left(), b.top(), b.right(), b.bottom()
    if grad > 0:
        band_fill(cv, path, (x0, y0), (x1, y1), [('#FFFFFF', 0.13 * grad), ('#FFFFFF', 0.0), ('#FFFFFF', 0.0), (DARK, 0.1 * grad), (DARK, 0.2 * grad)])
    if tex > 0:
        cv.save(); cv.clipPath(path, doAntiAlias=True)
        p3 = skia.Paint(AntiAlias=True, Shader=TEXSH, Alphaf=tex * 0.75); p3.setBlendMode(skia.BlendMode.kOverlay); cv.drawRect(b, p3)
        cv.restore()

def shape(cv, path, base, shade=None, light=None, off=(0.1, 0.1), hoff=(-0.05, -0.05), seed=0, tex=0.42, grad=1.0, a=1.0, rim=None):
    """Two-tone cel shape + imperfect gradient + texture (the core look)."""
    bb = path.getBounds(); sz = max(bb.width(), bb.height())
    shade = shade or mix(base, DARK, 0.38)
    cv.save(); cv.clipPath(path, doAntiAlias=True)
    cv.drawPath(path, P(shade, a))
    cv.save(); cv.translate(-off[0] * sz, -off[1] * sz); cv.drawPath(path, P(base, a)); cv.restore()
    if light:
        q = skia.Path(path); q.offset(-hoff[0] * sz, -hoff[1] * sz)
        res = skia.Op(path, q, skia.PathOp.kDifference_PathOp)
        if res: cv.drawPath(res, P(light, a))
    cv.restore()
    finish(cv, path, seed, tex, grad)
    if rim: cv.drawPath(path, P(rim[0], rim[1], stroke=rim[2]))

def ao(cv, x, y, rx, ry, a=0.35): oval(cv, x, y, rx, ry, P(DARK, a, blur=max(1, ry * 0.5)))

def sphere(cv, x, y, r, base, seed=0, a=1.0, glow=None):
    if glow: circle(cv, x, y, r * 1.6, P(glow, 0.4 * a, blur=r * 0.5))
    p = wcirc(x, y, r, seed, 0.02)
    cv.drawPath(p, P(mix(base, DARK, 0.45), a))
    cv.save(); cv.clipPath(p, doAntiAlias=True)
    for (f, dx, c) in ((0.9, -0.08, mix(base, DARK, 0.2)), (0.75, -0.16, base), (0.52, -0.26, mix(base, '#FFFFFF', 0.18)), (0.26, -0.38, mix(base, '#FFFFFF', 0.4))):
        cv.drawPath(wcirc(x + dx * r, y + dx * r * 1.1, r * f, seed + 1, 0.03), P(c, a))
    cv.restore()
    finish(cv, p, seed, 0.25, 0.0)
    cv.drawArc(skia.Rect.MakeLTRB(x - r * 0.8, y - r * 0.8, x + r * 0.8, y + r * 0.8), 200, 55, False, P('#FFFFFF', 0.5 * a, stroke=r * 0.07))

class IsoR:
    def __init__(s, x, y, k): s.x, s.y, s.k = x, y, k
    def p(s, u, v, z): return (s.x + (u - v) * s.k, s.y + (u + v) * s.k * 0.5 - z * s.k)
    def block(s, cv, u0, v0, u1, v1, z0, z1, top, left, right, r=None, tex=0.38, seed=0, a=1.0):
        P_ = s.p; k = s.k; r = r if r is not None else k * 0.16
        sil = [P_(u0, v0, z1), P_(u1, v0, z1), P_(u1, v0, z0), P_(u1, v1, z0), P_(u0, v1, z0), P_(u0, v1, z1)]
        cv.drawPath(round_path(sil, r * 1.2), P(mix(right, DARK, 0.4), a))
        L = round_path([P_(u0, v1, z1), P_(u1, v1, z1), P_(u1, v1, z0), P_(u0, v1, z0)], r)
        q0, q1 = P_(u0, v1, z1), P_(u0, v1, z0)
        band_fill(cv, L, q0, q1, [left, mix(left, DARK, 0.1), mix(left, DARK, 0.2), mix(left, DARK, 0.3)], a)
        R = round_path([P_(u1, v0, z1), P_(u1, v1, z1), P_(u1, v1, z0), P_(u1, v0, z0)], r)
        q0, q1 = P_(u1, v1, z1), P_(u1, v1, z0)
        band_fill(cv, R, q0, q1, [right, mix(right, DARK, 0.1), mix(right, DARK, 0.2), mix(right, DARK, 0.3)], a)
        T = round_path([P_(u0, v0, z1), P_(u1, v0, z1), P_(u1, v1, z1), P_(u0, v1, z1)], r)
        q0, q1 = P_(u0, v0, z1), P_(u1, v1, z1)
        band_fill(cv, T, q0, q1, [mix(top, '#FFFFFF', 0.22), mix(top, '#FFFFFF', 0.1), top, mix(top, DARK, 0.08)], a)
        if tex > 0:
            for pth in (L, R, T): finish(cv, pth, seed, tex, 0.0, blot=False)
        cv.save(); cv.clipPath(T, doAntiAlias=True); cv.drawPath(T, P('#FFFFFF', 0.45 * a, stroke=max(2, k * 0.09))); cv.restore()
        cv.save(); cv.clipPath(L, doAntiAlias=True); cv.drawPath(L, P('#FFFFFF', 0.12 * a, stroke=max(2, k * 0.06))); cv.restore()
    def roof(s, cv, u0, v0, u1, v1, z0, z1, front, back_, gable, r=None):
        P_ = s.p; vm = (v0 + v1) / 2; r = r if r is not None else s.k * 0.08
        cv.drawPath(round_path([P_(u0, v0, z0), P_(u1, v0, z0), P_(u1, vm, z1), P_(u0, vm, z1)], r), P(back_))
        cv.drawPath(round_path([P_(u1, v0, z0), P_(u1, v1, z0), P_(u1, vm, z1)], r), P(gable))
        F = round_path([P_(u0, vm, z1), P_(u1, vm, z1), P_(u1, v1, z0), P_(u0, v1, z0)], r)
        a_, b_ = P_(u0, vm, z1), P_(u0, v1, z0)
        band_fill(cv, F, a_, b_, [mix(front, '#FFFFFF', 0.15), front, mix(front, DARK, 0.15)])
        finish(cv, F, 3, 0.4, 0.0, blot=False)
    def pyramid(s, cv, u0, v0, u1, v1, z0, z1, c1, c2):
        P_ = s.p; um, vm = (u0 + u1) / 2, (v0 + v1) / 2; r = s.k * 0.1
        A = round_path([P_(u0, v1, z0), P_(u1, v1, z0), P_(um, vm, z1)], r); B = round_path([P_(u1, v0, z0), P_(u1, v1, z0), P_(um, vm, z1)], r)
        cv.drawPath(A, P(c1)); cv.drawPath(B, P(c2)); finish(cv, A, 1, 0.4, 0.5); finish(cv, B, 2, 0.4, 0.5)

def tree(cv, x, y, s, t=0.0, seed=0, pal=('#3CC23A', '#1E8A2A', '#8CF05A'), trunk='#7A3A14'):
    sw = math.sin(t * 1.2 + seed) * 0.03 * s
    ao(cv, x, y, 0.7 * s, 0.16 * s)
    cv.drawPath(wpoly([(x - 0.1 * s, y), (x - 0.06 * s, y - 0.95 * s), (x + 0.06 * s, y - 0.95 * s), (x + 0.1 * s, y)], 3, seed, 0.5), P(trunk))
    shape(cv, wblob([(x - 0.42 * s + sw, y - 1.05 * s, 0.46 * s), (x + 0.42 * s + sw, y - 1.1 * s, 0.44 * s), (x + sw * 1.3, y - 1.55 * s, 0.58 * s), (x + sw, y - 0.95 * s, 0.42 * s)], seed, 0.06),
          pal[0], pal[1], pal[2], off=(0.1, 0.12), hoff=(-0.04, -0.05), seed=seed)

def pine(cv, x, y, s, pal=('#26B85A', '#127A3E'), seed=0, snow=False):
    ao(cv, x, y, 0.45 * s, 0.12 * s)
    cv.drawPath(wpoly([(x - 0.07 * s, y), (x - 0.07 * s, y - 0.4 * s), (x + 0.07 * s, y - 0.4 * s), (x + 0.07 * s, y)], 2), P('#6A3010'))
    for i, (w, yy) in enumerate(((0.55, 0.3), (0.44, 0.75), (0.32, 1.15))):
        A = wpoly([(x - w * s, y - yy * s), (x, y - (yy + 0.75) * s), (x + w * s, y - yy * s)], 0.08 * s, seed + i, 1.5)
        cv.drawPath(A, P(pal[0])); cv.save(); cv.clipPath(A, doAntiAlias=True); cv.drawRect(skia.Rect.MakeLTRB(x, y - 3 * s, x + s, y), P(pal[1])); cv.restore()
        if snow: cv.save(); cv.clipPath(A, doAntiAlias=True); cv.drawRect(skia.Rect.MakeLTRB(x - s, y - (yy + 0.8) * s, x + s, y - (yy + 0.5) * s), P('#FFFFFF', 0.95)); cv.restore()
        finish(cv, A, seed + i, 0.35, 0.5, blot=False)

def iso_island(cv, x, y, k, biome, t, seed=0, kpop=1.0, glow=None, people=True):
    if kpop <= 0: return
    cv.save(); cv.translate(x, y); cv.scale(kpop, kpop); cv.translate(-x, -y)
    I = IsoR(x, y, k); top, left, right, d1, d2 = BIOMES[biome]
    if glow: circle(cv, x, y, 4.2 * k, P(glow, 0.45, blur=k * 1.3))
    I.block(cv, -0.9, -0.9, 0.9, 0.9, -2.7, -1.8, d2, mix(d1, DARK, 0.3), mix(d2, DARK, 0.4), seed=seed)
    I.block(cv, -1.5, -1.5, 1.5, 1.5, -1.9, -1.0, d1, mix(d1, DARK, 0.15), mix(d2, DARK, 0.25), seed=seed + 1)
    I.block(cv, -2, -2, 2, 2, -1.05, -0.3, d1, d1, d2, seed=seed + 2)
    I.block(cv, -2.06, -2.06, 2.06, 2.06, -0.32, 0, top, left, right, seed=seed + 3)
    rs = np.random.default_rng(seed)
    for i in range(8):
        u, v = rs.uniform(-1.8, 1.8), rs.uniform(-1.8, 1.8); q = I.p(u, v, 0)
        oval(cv, q[0], q[1], 0.12 * k, 0.05 * k, P(mix(top, '#FFFFFF', 0.3), 0.6))
    props = []
    if biome in ('village', 'gold'):
        props += [(-1.0, -0.8, 'house', ('#FFE0B0', '#F03A3A')), (0.6, -1.1, 'house', ('#DDE8FF', '#2F5BEA')), (1.0, 0.8, 'tree', 0), (-1.2, 0.9, 'tree', 1)]
        if people: props.append((0.2, 0.3, 'person', 0))
    elif biome == 'desert': props += [(-0.3, -0.5, 'pyr', 1.6), (1.1, 0.9, 'cactus', 0), (-1.2, 1.1, 'cactus', 1), (1.2, -1.2, 'pyr', 0.8)]
    elif biome == 'snow': props += [(-1.0, -1.0, 'spine', 0), (0.9, -0.8, 'spine', 1), (-0.2, 0.2, 'igloo', 0), (1.1, 1.0, 'spine', 2), (-1.2, 1.0, 'spine', 3)]
    elif biome == 'ocean': props += [(0.0, 0.0, 'isle', 0)]
    elif biome == 'volcano': props += [(0.0, -0.2, 'volc', 0), (1.3, 1.2, 'rock', 0), (-1.3, 1.0, 'rock', 1)]
    elif biome == 'city':
        for i in range(5):
            u, v = -1.2 + (i % 3) * 1.1, -1.0 + (i // 3) * 1.4
            props.append((u, v, 'tower', (rs.uniform(1.0, 3.0), ['#FF4FB0', '#22D2FF', '#FFC21A', '#8A4BFF', '#FF6A1A'][i])))
    elif biome == 'forest':
        for i in range(7): props.append((rs.uniform(-1.6, 1.6), rs.uniform(-1.6, 1.6), 'pine' if i % 2 else 'tree', i))
    elif biome == 'candy': props += [(-0.8, -0.6, 'lolly', '#FF2E9A'), (0.8, 0.4, 'lolly', '#22D2FF'), (0.2, -1.2, 'lolly', '#FFC21A')]
    props.sort(key=lambda q: q[0] + q[1])
    for (u, v, kind, arg) in props:
        bx, by = I.p(u, v, 0)
        if kind == 'house':
            wc, rc = arg
            I.block(cv, u - 0.35, v - 0.35, u + 0.35, v + 0.35, 0, 0.55, wc, mix(wc, '#8A5AC8', 0.3), mix(wc, '#5A3A9A', 0.45), r=k * 0.06, seed=seed)
            I.roof(cv, u - 0.44, v - 0.44, u + 0.44, v + 0.44, 0.55, 1.05, rc, mix(rc, '#FFFFFF', 0.2), mix(wc, '#8A5AC8', 0.3))
            q = I.p(u - 0.05, v + 0.36, 0.3); rrect(cv, q[0], q[1], 0.16 * k, 0.16 * k, 0.04 * k, P('#FFC83A'))
        elif kind == 'tree': tree(cv, bx, by, 0.8 * k, t, arg)
        elif kind == 'pine': pine(cv, bx, by, 0.9 * k, seed=arg)
        elif kind == 'spine': pine(cv, bx, by, 0.9 * k, ('#1EAA7A', '#0E6A5A'), seed=arg, snow=True)
        elif kind == 'person': person(cv, bx, by, 0.11 * k, SKINS[seed % 5], '#2A160C', '#FF4A3A', '#2A3A8A', t, t * 8 + seed, seed=seed)
        elif kind == 'pyr': I.pyramid(cv, u - 0.6 * arg / 1.6, v - 0.6 * arg / 1.6, u + 0.6 * arg / 1.6, v + 0.6 * arg / 1.6, 0, 1.6 * arg / 1.6, '#FFD27A', '#D88A2A')
        elif kind == 'cactus':
            c = P('#1EA84A', 1, stroke=0.22 * k); cv.drawLine(bx, by, bx, by - 0.9 * k, c)
            c2 = P('#1EA84A', 1, stroke=0.14 * k); cv.drawLine(bx, by - 0.5 * k, bx + 0.25 * k, by - 0.5 * k, c2); cv.drawLine(bx + 0.25 * k, by - 0.5 * k, bx + 0.25 * k, by - 0.75 * k, c2)
            cv.drawLine(bx - 0.04 * k, by - 0.1 * k, bx - 0.04 * k, by - 0.8 * k, P('#7AF07A', 0.6, stroke=0.05 * k))
        elif kind == 'igloo':
            pa = skia.Path(); pa.addArc(skia.Rect.MakeLTRB(bx - 0.6 * k, by - 0.6 * k, bx + 0.6 * k, by + 0.6 * k), 180, 180); pa.close()
            shape(cv, pa, '#FFFFFF', '#A8C4F0', None, off=(0.1, 0.0)); rrect(cv, bx + 0.25 * k, by - 0.12 * k, 0.24 * k, 0.24 * k, 0.1 * k, P('#3A4A90'))
        elif kind == 'isle':
            shape(cv, woval(bx, by, 0.95 * k, 0.48 * k, seed), '#F2C860', '#C89A30', '#FFE6A0', off=(0.0, 0.12))
            cv.drawLine(bx, by, bx + 0.15 * k, by - 1.0 * k, P('#8A4A1A', 1, stroke=0.1 * k))
            for j in range(5):
                aa = math.radians(-160 + j * 35); ex, ey = bx + 0.15 * k + math.cos(aa) * 0.6 * k, by - 1.0 * k + math.sin(aa) * 0.3 * k + 0.2 * k
                pa = skia.Path(); pa.moveTo(bx + 0.15 * k, by - 1.0 * k); pa.quadTo((bx + ex) / 2, by - 1.25 * k, ex, ey); cv.drawPath(pa, P('#1EAA3A', 1, stroke=0.12 * k))
            for j in range(3):
                ph = (t * 0.5 + j / 3) % 1; ww = I.p(-1.6 + ph * 3.2, 1.3 - j * 1.1, 0.01); cv.drawLine(ww[0] - 0.2 * k, ww[1], ww[0] + 0.2 * k, ww[1], P('#FFFFFF', 0.7, stroke=2))
        elif kind == 'volc':
            pa = wpoly([(bx - 1.2 * k, by), (bx - 0.3 * k, by - 1.5 * k), (bx + 0.3 * k, by - 1.5 * k), (bx + 1.2 * k, by)], 0.15 * k, seed, 2)
            shape(cv, pa, '#7A4AB8', '#4A2A86', None, off=(0.14, 0.0))
            oval(cv, bx, by - 1.5 * k, 0.32 * k, 0.1 * k, P('#FF6A00')); circle(cv, bx, by - 1.55 * k, 0.6 * k, P('#FF4A00', 0.5, blur=0.25 * k))
            cv.drawLine(bx + 0.1 * k, by - 1.45 * k, bx + 0.35 * k, by - 0.6 * k, P('#FF7A00', 1, stroke=0.1 * k))
            for j in range(3):
                ph = (t * 0.6 + j / 3) % 1; circle(cv, bx + 0.2 * k * ph, by - (1.8 + 1.2 * ph) * k, (0.2 + 0.3 * ph) * k, P('#B8A0E0', 0.8 * (1 - ph)))
        elif kind == 'rock': shape(cv, wblob([(bx, by - 0.15 * k, 0.25 * k), (bx + 0.2 * k, by - 0.1 * k, 0.18 * k)], seed), '#7A5AB0', '#4A2E82', None, off=(0.1, 0.1))
        elif kind == 'tower':
            h_, c = arg
            I.block(cv, u - 0.3, v - 0.3, u + 0.3, v + 0.3, 0, h_, mix(c, '#FFFFFF', 0.3), c, mix(c, DARK, 0.35), r=k * 0.08)
            for j in range(int(h_ * 3)):
                q = I.p(u + 0.3, v - 0.1, 0.2 + j * 0.3); rrect(cv, q[0] + 0.05 * k, q[1] - 0.03 * k, 0.08 * k, 0.08 * k, 2, P('#FFF0A0', 0.95))
        elif kind == 'lolly':
            cv.drawLine(bx, by, bx, by - 1.0 * k, P('#FFFFFF', 1, stroke=0.08 * k)); sphere(cv, bx, by - 1.2 * k, 0.35 * k, arg, seed)
    cv.restore()

def person(cv, x, y, s, skin, hair, shirt, pants, t=0.0, walk=0.0, facing=1, back_view=False, wave=0.0, hair_style=0, look=0.0, arm_l=None, arm_r=None, seed=0, expr='calm', jacket=None, up=0.0, hands_at=None):
    cv.save(); cv.translate(x, y); cv.scale(facing, 1)
    sw = math.sin(walk) * 0.55 * s if walk else 0
    bob = abs(math.sin(walk)) * 0.12 * s if walk else 0
    ao(cv, 0, 0, 1.5 * s, 0.32 * s, 0.3)
    sk_s = mix(skin, '#6A1E3A', 0.32); sh_s = mix(shirt, DARK, 0.32); pa_s = mix(pants, DARK, 0.3)
    for d, c in ((-1, pa_s), (1, pants)):
        lx = d * 0.36 * s; fx = lx + (sw if d > 0 else -sw)
        cv.drawLine(lx, -2.6 * s - bob, fx, -0.3 * s, P(c, 1, stroke=0.62 * s))
        cv.drawPath(round_path([(fx - 0.3 * s, -0.42 * s), (fx + 0.55 * s, -0.42 * s), (fx + 0.6 * s, 0), (fx - 0.35 * s, 0)], 0.15 * s), P('#24152E'))
    def arm(side, ang):
        sx_, sy_ = side * 0.98 * s, -4.75 * s - bob; a = math.radians(ang)
        ex, ey = sx_ + math.sin(a) * 1.2 * s * side, sy_ + math.cos(a) * 1.2 * s
        hx, hy = ex + math.sin(a * 1.15) * 1.1 * s * side, ey + math.cos(a * 1.15) * 1.1 * s
        if hands_at is not None:
            tx, ty = hands_at[0] if side < 0 else hands_at[1]
            L1, L2 = 1.2 * s, 1.1 * s; dx, dy = tx - sx_, ty - sy_; d = min(max(math.hypot(dx, dy), 1e-3), L1 + L2 - 1e-3)
            base = math.atan2(dy, dx); ca = (L1 * L1 + d * d - L2 * L2) / (2 * L1 * d); aa = math.acos(max(-1, min(1, ca)))
            best = None
            for sg in (1, -1):
                exx, eyy = sx_ + L1 * math.cos(base + sg * aa), sy_ + L1 * math.sin(base + sg * aa)
                sc_ = exx * side * 0.4 + eyy
                if best is None or sc_ > best[2]: best = (exx, eyy, sc_)
            ex, ey = best[0], best[1]; hx, hy = sx_ + dx * d / max(math.hypot(dx, dy), 1e-3), sy_ + dy * d / max(math.hypot(dx, dy), 1e-3)
        pa = skia.Path(); pa.moveTo(sx_, sy_); pa.lineTo(ex, ey); pa.lineTo(hx, hy)
        cv.drawPath(pa, P((jacket or shirt) if side > 0 else mix(jacket or shirt, DARK, 0.3), 1, stroke=0.58 * s))
        circle(cv, hx, hy, 0.3 * s, P(skin if side > 0 else sk_s))
    al = arm_l if arm_l is not None else 12 + 18 * math.sin(walk + math.pi) if walk else 10
    ar = arm_r if arm_r is not None else ((12 + 18 * math.sin(walk)) if walk else 10)
    if wave: ar = 150 + 20 * math.sin(t * 10)
    arm(-1, al)
    tor = round_path([(-1.08 * s, -5.1 * s - bob), (1.08 * s, -5.1 * s - bob), (0.95 * s, -2.4 * s - bob), (-0.95 * s, -2.4 * s - bob)], 0.55 * s)
    shape(cv, tor, jacket or shirt, mix(jacket or shirt, DARK, 0.32), mix(jacket or shirt, '#FFFFFF', 0.25), off=(0.14, 0.0), hoff=(-0.06, 0), seed=seed)
    if jacket:
        cv.drawPath(round_path([(-0.35 * s, -5.05 * s - bob), (0.35 * s, -5.05 * s - bob), (0.22 * s, -2.5 * s - bob), (-0.22 * s, -2.5 * s - bob)], 0.1 * s), P(shirt))
        cv.drawLine(-0.36 * s, -5.0 * s - bob, -0.1 * s, -4.3 * s - bob, P(mix(jacket, DARK, 0.35), 1, stroke=0.12 * s)); cv.drawLine(0.36 * s, -5.0 * s - bob, 0.1 * s, -4.3 * s - bob, P(mix(jacket, DARK, 0.35), 1, stroke=0.12 * s))
    arm(1, ar)
    rrect(cv, 0, -5.25 * s - bob, 0.45 * s, 0.4 * s, 0.1 * s, P(sk_s))
    hy = -6.3 * s - bob - up * 0.15 * s
    hx = look * 0.12 * s
    hp = woval(hx, hy, 0.95 * s, 1.05 * s, seed, 0.02)
    shape(cv, hp, skin, sk_s, mix(skin, '#FFFFFF', 0.22), off=(0.12, 0.06), hoff=(-0.05, -0.05), seed=seed, tex=0.3)
    hc_s = mix(hair, '#000000', 0.3)
    if back_view:
        hp2 = wblob([(hx + dx * s, hy + dy * s, r * s) for dx, dy, r in ((-0.6, -0.4, 0.6), (0.6, -0.4, 0.6), (0, -0.7, 0.65), (-0.75, 0.2, 0.5), (0.75, 0.2, 0.5), (0, 0.1, 0.8))], seed)
        shape(cv, hp2, hair, hc_s, mix(hair, '#FFFFFF', 0.2), off=(0.1, 0.05), seed=seed)
    else:
        fx = look * 0.28 * s; fy = -up * 0.18 * s
        if hair_style == 1:
            shape(cv, wblob([(hx + dx * s, hy + dy * s, r * s) for dx, dy, r in ((-0.7, -0.55, 0.52), (0.7, -0.55, 0.52), (0, -0.9, 0.58), (-0.95, 0.0, 0.4), (0.95, 0.0, 0.4), (-0.35, -0.85, 0.45), (0.35, -0.9, 0.45))], seed), hair, hc_s, mix(hair, '#FFFFFF', 0.15), off=(0.06, 0.05), seed=seed)
        elif hair_style == 2:
            hp2 = skia.Path(); hp2.addArc(skia.Rect.MakeLTRB(hx - 1.05 * s, hy - 1.15 * s, hx + 1.05 * s, hy + 0.95 * s), 185, 170); hp2.close(); cv.drawPath(hp2, P(hair))
            oval(cv, hx + 0.85 * s, hy + 0.3 * s, 0.3 * s, 0.7 * s, P(hair)); oval(cv, hx - 0.85 * s, hy + 0.3 * s, 0.3 * s, 0.7 * s, P(hair))
        else:
            hp2 = skia.Path(); hp2.addArc(skia.Rect.MakeLTRB(hx - 1.05 * s, hy - 1.15 * s, hx + 1.05 * s, hy + 0.9 * s), 180, 180); hp2.close()
            shape(cv, hp2, hair, hc_s, None, off=(0.06, 0.04), seed=seed); oval(cv, hx - 0.82 * s, hy - 0.1 * s, 0.25 * s, 0.45 * s, P(hair))
        b = blink(t, seed)
        big = expr == 'surprised'
        for d in (-1, 1):
            ex_, ey_ = hx + fx + d * 0.36 * s, hy + 0.05 * s + fy
            if big: oval(cv, ex_, ey_, 0.17 * s, 0.22 * s * b, P('#FFFFFF')); circle(cv, ex_, ey_, 0.09 * s, P('#1A0A20'))
            else: oval(cv, ex_, ey_, 0.1 * s, 0.15 * s * b, P('#1A0A20')); circle(cv, ex_ - 0.03 * s, ey_ - 0.05 * s, 0.035 * s, P('#FFFFFF', 0.9 * (b > 0.5)))
            cv.drawLine(ex_ - 0.15 * s, ey_ - (0.38 if big else 0.28) * s, ex_ + 0.15 * s, ey_ - (0.42 if big else 0.3) * s, P(hc_s, 1, stroke=0.08 * s))
            oval(cv, hx + fx + d * 0.6 * s, hy + 0.38 * s + fy, 0.16 * s, 0.09 * s, P('#FF4A6A', 0.4))
        if big: oval(cv, hx + fx, hy + 0.55 * s + fy, 0.13 * s, 0.17 * s, P('#5A0E2A'))
        elif expr == 'happy':
            pa = skia.Path(); pa.moveTo(hx + fx - 0.26 * s, hy + 0.42 * s + fy); pa.quadTo(hx + fx, hy + 0.75 * s + fy, hx + fx + 0.26 * s, hy + 0.42 * s + fy); pa.close(); cv.drawPath(pa, P('#6A0E2A'))
        else:
            pa = skia.Path(); pa.moveTo(hx + fx - 0.2 * s, hy + 0.48 * s + fy); pa.quadTo(hx + fx, hy + 0.62 * s + fy, hx + fx + 0.2 * s, hy + 0.48 * s + fy); cv.drawPath(pa, P('#6A0E2A', 1, stroke=0.09 * s))
    cv.restore()

def dog(cv, x, y, s, t, walk, col_='#C8762E', facing=1):
    cv.save(); cv.translate(x, y); cv.scale(facing, 1)
    ao(cv, 0, 0, 1.3 * s, 0.25 * s, 0.3)
    for i, lx in enumerate((-0.7, -0.4, 0.45, 0.75)):
        sw = math.sin(walk + i * math.pi) * 0.25 * s
        cv.drawLine(lx * s, -0.9 * s, lx * s + sw, 0, P(mix(col_, DARK, 0.25 if i % 2 else 0), 1, stroke=0.24 * s))
    shape(cv, woval(0, -1.1 * s, 1.15 * s, 0.5 * s, 3, 0.03), col_, mix(col_, DARK, 0.3), mix(col_, '#FFFFFF', 0.25), off=(0, 0.12))
    cv.drawLine(-1.05 * s, -1.25 * s, -1.5 * s, -1.75 * s + math.sin(t * 12) * 0.15 * s, P(col_, 1, stroke=0.18 * s))
    shape(cv, wcirc(1.15 * s, -1.65 * s, 0.48 * s, 5), col_, mix(col_, DARK, 0.3), None, off=(0.1, 0.1))
    oval(cv, 1.55 * s, -1.55 * s, 0.3 * s, 0.2 * s, P(mix(col_, '#FFFFFF', 0.3))); circle(cv, 1.8 * s, -1.6 * s, 0.09 * s, P('#1A0A20'))
    circle(cv, 1.25 * s, -1.75 * s, 0.07 * s, P('#1A0A20'))
    oval(cv, 0.9 * s, -1.6 * s, 0.16 * s, 0.38 * s, P(mix(col_, DARK, 0.4)))
    cv.restore()

def _alien_head_profile(cv, hx, hy, s, t, pal, eye_look=0.0, seed=0):
    skin, shade, light, mark = pal
    pts = [(0.55, 0.95), (0.92, 0.6), (1.04, 0.32), (0.98, 0.14), (1.1, -0.02), (0.98, -0.2), (0.96, -0.55), (0.8, -0.95), (0.35, -1.45), (-0.3, -1.85), (-0.95, -1.78),
           (-1.3, -1.25), (-1.05, -0.5), (-0.55, 0.12), (-0.08, 0.55), (0.25, 0.86)]
    hp = smooth_path([(hx + u * s, hy + v * s) for u, v in pts])
    shape(cv, hp, skin, shade, light, off=(0.08, 0.06), hoff=(-0.03, -0.04), seed=seed)
    cv.save(); cv.clipPath(hp, doAntiAlias=True); q = skia.Path(hp); q.offset(-0.08 * s, 0.05 * s); res = skia.Op(hp, q, skia.PathOp.kDifference_PathOp)
    if res: cv.drawPath(res, P(mark, 0.55))
    cv.restore()
    cv.save(); cv.clipPath(hp, doAntiAlias=True)
    oval(cv, hx + 0.55 * s, hy + 0.22 * s, 0.32 * s, 0.18 * s, P(shade, 0.6))
    for i in range(7):
        a = i / 6; px = lerp(0.75, -0.95, a); py = -0.75 - 0.95 * math.sin(math.pi * (0.25 + 0.6 * a))
        g = 0.6 + 0.4 * math.sin(t * 2 + i * 0.7)
        circle(cv, hx + px * s, hy + py * s, 0.055 * s * (1.2 - a * 0.4), P(mark, g)); circle(cv, hx + px * s, hy + py * s, 0.13 * s, P(mark, 0.25 * g, blur=0.05 * s))
    for (u, v) in ((-0.6, -1.2), (-0.8, -0.9), (-0.45, -1.45)): circle(cv, hx + u * s, hy + v * s, 0.04 * s, P(mark, 0.5))
    cv.restore()
    b = blink(t, seed + 5)
    cv.save(); cv.translate(hx + 0.62 * s, hy - 0.3 * s); cv.rotate(-14)
    oval(cv, 0, 0, 0.27 * s, 0.13 * s * b, P('#06020F'))
    if b > 0.5:
        oval(cv, -0.08 * s + eye_look * 0.05 * s, -0.04 * s, 0.09 * s, 0.035 * s, P(mark, 0.85))
    cv.drawArc(skia.Rect.MakeLTRB(-0.3 * s, -0.2 * s, 0.3 * s, 0.14 * s), 200, 140, False, P(shade, 1, stroke=0.04 * s))
    cv.restore()
    cv.drawLine(hx + 0.8 * s, hy + 0.5 * s, hx + 0.95 * s, hy + 0.48 * s, P(shade, 1, stroke=0.035 * s))

def _alien_head_front(cv, hx, hy, s, t, pal, seed=0, look=(0, 0)):
    skin, shade, light, mark = pal
    pts = [(0, 1.0), (0.35, 0.8), (0.62, 0.35), (0.78, -0.25), (0.85, -0.9), (0.62, -1.55), (0, -1.85), (-0.62, -1.55), (-0.85, -0.9), (-0.78, -0.25), (-0.62, 0.35), (-0.35, 0.8)]
    hp = smooth_path([(hx + u * s, hy + v * s) for u, v in pts])
    shape(cv, hp, skin, shade, light, off=(0.1, 0.04), hoff=(-0.03, -0.03), seed=seed)
    cv.save(); cv.clipPath(hp, doAntiAlias=True)
    for d in (-1, 1):
        for i in range(5):
            a = i / 4; px = d * (0.25 + 0.35 * a); py = -0.75 - 0.6 * a
            circle(cv, hx + px * s, hy + py * s, 0.05 * s, P(mark, 0.8)); circle(cv, hx + px * s, hy + py * s, 0.12 * s, P(mark, 0.25, blur=0.05 * s))
        oval(cv, hx + d * 0.5 * s, hy + 0.2 * s, 0.22 * s, 0.12 * s, P(shade, 0.5))
    cv.restore()
    b = blink(t, seed + 9)
    for d in (-1, 1):
        cv.save(); cv.translate(hx + d * 0.38 * s + look[0] * 0.05 * s, hy - 0.3 * s); cv.rotate(-d * 22)
        oval(cv, 0, 0, 0.3 * s, 0.14 * s * b, P('#06020F'))
        if b > 0.5: oval(cv, -0.08 * s, -0.04 * s, 0.1 * s, 0.035 * s, P(mark, 0.85))
        cv.restore()
    for d in (-1, 1): oval(cv, hx + d * 0.06 * s, hy + 0.28 * s, 0.025 * s, 0.05 * s, P(shade))
    cv.drawLine(hx - 0.15 * s, hy + 0.6 * s, hx + 0.15 * s, hy + 0.6 * s, P(shade, 1, stroke=0.04 * s))

def alien_profile(cv, x, y, s, t, kind='blue', typing=1.0, seed=0, head_turn=0.0, chair=True, hands_at=None):
    """Seated alien in profile facing right; (x, y) = hip. s ~ head half-height."""
    pal = ALIEN[kind]; suit, panel, trim = SUIT
    if chair:
        shape(cv, wpoly([(x - 1.5 * s, y + 0.5 * s), (x - 1.35 * s, y - 3.0 * s), (x - 0.85 * s, y - 3.1 * s), (x - 0.75 * s, y + 0.5 * s)], 0.3 * s, seed), '#2A1C66', '#170E40', '#4A38A0', off=(0.15, 0), seed=seed)
        rrect(cv, x + 0.2 * s, y + 0.55 * s, 2.4 * s, 0.35 * s, 0.15 * s, P('#1E1450'))
        cv.drawLine(x + 0.2 * s, y + 0.7 * s, x + 0.2 * s, y + 2.2 * s, P('#170E40', 1, stroke=0.3 * s))
    hx_, hy_ = hands_at if hands_at else (x + 2.0 * s, y - 1.55 * s)
    sh = (x + 0.05 * s, y - 2.75 * s)
    def arm(dx, dy, front):
        el = (x + 0.6 * s + dx, y - 1.15 * s + dy)
        c = suit if front else mix(suit, DARK, 0.45)
        pa = skia.Path(); pa.moveTo(sh[0] + dx, sh[1] + dy); pa.lineTo(*el); pa.lineTo(hx_ + dx - 0.35 * s, hy_ + dy + 0.05 * s)
        cv.drawPath(pa, P(c, 1, stroke=0.55 * s)); cv.drawPath(pa, P(panel if front else mix(panel, DARK, 0.45), 1, stroke=0.16 * s))
        cv.drawLine(hx_ + dx - 0.5 * s, hy_ + dy - 0.22 * s, hx_ + dx - 0.5 * s, hy_ + dy + 0.28 * s, P(trim, 1, stroke=0.12 * s))
        skin = pal[0] if front else pal[1]
        shape(cv, woval(hx_ + dx - 0.15 * s, hy_ + dy, 0.4 * s, 0.24 * s, seed), skin, pal[1], None, off=(0, 0.15), tex=0.25)
        for f in range(4):
            tap = max(0, math.sin(t * 13 + f * 1.9 + dx)) * 0.14 * s * typing
            fx0 = hx_ + dx + 0.1 * s + f * 0.03 * s; fy0 = hy_ + dy - 0.1 * s + f * 0.08 * s
            pa = skia.Path(); pa.moveTo(fx0, fy0); pa.quadTo(fx0 + 0.42 * s, fy0 - 0.08 * s - tap, fx0 + 0.62 * s, fy0 + 0.22 * s - tap)
            cv.drawPath(pa, P(skin, 1, stroke=0.11 * s))
            circle(cv, fx0 + 0.62 * s, fy0 + 0.22 * s - tap, 0.05 * s, P(pal[3], 0.6))
    arm(-0.2 * s, -0.1 * s, False)
    # legs
    th = round_path([(x - 0.6 * s, y - 0.35 * s), (x + 1.55 * s, y - 0.2 * s), (x + 1.6 * s, y + 0.35 * s), (x - 0.6 * s, y + 0.3 * s)], 0.3 * s)
    shape(cv, th, suit, mix(suit, '#000000', 0.4), panel, off=(0, -0.1), hoff=(0, 0.05), seed=seed)
    cv.drawPath(round_path([(x + 1.25 * s, y), (x + 1.65 * s, y), (x + 1.75 * s, y + 1.9 * s), (x + 1.35 * s, y + 1.9 * s)], 0.2 * s), P(mix(suit, DARK, 0.2)))
    rrect(cv, x + 1.75 * s, y + 1.95 * s, 0.75 * s, 0.25 * s, 0.1 * s, P('#0E0A28'))
    # torso
    tor = smooth_path([(x - 0.65 * s, y + 0.1 * s), (x - 0.85 * s, y - 1.2 * s), (x - 0.78 * s, y - 2.5 * s), (x - 0.3 * s, y - 3.15 * s), (x + 0.3 * s, y - 3.2 * s),
                       (x + 0.75 * s, y - 2.55 * s), (x + 0.7 * s, y - 1.3 * s), (x + 0.6 * s, y + 0.1 * s)])
    shape(cv, tor, suit, mix(suit, '#000000', 0.4), panel, off=(-0.1, 0.0), hoff=(0.04, 0.0), seed=seed)
    cv.save(); cv.clipPath(tor, doAntiAlias=True)
    pa = skia.Path(); pa.moveTo(x + 0.4 * s, y - 3.1 * s); pa.quadTo(x + 0.72 * s, y - 2.0 * s, x + 0.5 * s, y + 0.1 * s)
    cv.drawPath(pa, P(trim, 0.9, stroke=0.07 * s)); cv.drawPath(pa, P(trim, 0.4, blur=0.08 * s, stroke=0.2 * s))
    cv.restore()
    # neck + collar + head
    neck = smooth_path([(x - 0.1 * s, y - 2.9 * s), (x + 0.15 * s, y - 4.55 * s), (x + 0.6 * s, y - 4.5 * s), (x + 0.45 * s, y - 2.9 * s)])
    shape(cv, neck, pal[1], mix(pal[1], DARK, 0.3), pal[0], off=(0.1, 0), hoff=(-0.05, 0), tex=0.3)
    shape(cv, smooth_path([(x - 0.45 * s, y - 2.85 * s), (x - 0.3 * s, y - 3.55 * s), (x + 0.15 * s, y - 3.6 * s), (x + 0.55 * s, y - 3.25 * s), (x + 0.55 * s, y - 2.85 * s)]), panel, mix(panel, DARK, 0.45), mix(panel, '#FFFFFF', 0.15), off=(0.08, 0), seed=seed)
    hx, hy = x + 0.6 * s, y - 5.4 * s
    if head_turn < 0.5: _alien_head_profile(cv, hx, hy, s, t, pal, seed=seed)
    else: _alien_head_front(cv, hx - 0.1 * s, hy - 0.1 * s, s * 0.95, t, pal, seed=seed)
    shape(cv, woval(x + 0.0 * s, y - 2.65 * s, 0.55 * s, 0.38 * s, seed), panel, mix(panel, DARK, 0.4), mix(panel, '#FFFFFF', 0.2), off=(0.05, 0.12), seed=seed)
    cv.drawArc(skia.Rect.MakeLTRB(x - 0.5 * s, y - 3.0 * s, x + 0.55 * s, y - 2.3 * s), 200, 140, False, P(trim, 0.9, stroke=0.06 * s))
    arm(0, 0, True)

def alien_back(cv, x, y, s, t, kind='blue', turn=0.0, seed=0):
    """Over-the-shoulder view from behind; turn 0..1 -> head turns to camera."""
    pal = ALIEN[kind]; suit, panel, trim = SUIT
    tor = smooth_path([(x - 1.6 * s, y + 2.0 * s), (x - 1.75 * s, y - 0.5 * s), (x - 1.55 * s, y - 2.0 * s), (x - 0.6 * s, y - 2.55 * s), (x + 0.6 * s, y - 2.55 * s),
                       (x + 1.55 * s, y - 2.0 * s), (x + 1.75 * s, y - 0.5 * s), (x + 1.6 * s, y + 2.0 * s)])
    shape(cv, tor, suit, mix(suit, '#000000', 0.4), panel, off=(-0.06, 0.0), hoff=(0.03, 0), seed=seed)
    cv.save(); cv.clipPath(tor, doAntiAlias=True)
    cv.drawLine(x, y - 2.6 * s, x, y + 2.0 * s, P(trim, 0.8, stroke=0.08 * s)); cv.drawLine(x, y - 2.6 * s, x, y + 2.0 * s, P(trim, 0.3, blur=0.1 * s, stroke=0.25 * s))
    for d in (-1, 1):
        pa = skia.Path(); pa.moveTo(x + d * 0.5 * s, y - 2.3 * s); pa.quadTo(x + d * 1.2 * s, y - 1.0 * s, x + d * 0.9 * s, y + 2.0 * s); cv.drawPath(pa, P(panel, 0.8, stroke=0.12 * s))
    cv.restore()
    for d in (-1, 1): shape(cv, woval(x + d * 1.3 * s, y - 1.95 * s, 0.6 * s, 0.4 * s, seed + d + 3), panel, mix(panel, DARK, 0.4), mix(panel, '#FFFFFF', 0.2), off=(0.05, 0.12))
    shape(cv, smooth_path([(x - 0.33 * s, y - 2.3 * s), (x - 0.28 * s, y - 3.7 * s), (x + 0.28 * s, y - 3.7 * s), (x + 0.33 * s, y - 2.3 * s)]), pal[1], mix(pal[1], DARK, 0.3), pal[0], off=(0.1, 0), hoff=(-0.05, 0))
    shape(cv, smooth_path([(x - 0.75 * s, y - 2.2 * s), (x - 0.55 * s, y - 2.95 * s), (x + 0.55 * s, y - 2.95 * s), (x + 0.75 * s, y - 2.2 * s)]), panel, mix(panel, DARK, 0.45), mix(panel, '#FFFFFF', 0.15), off=(0.08, 0))
    hx, hy = x + turn * 0.1 * s, y - 4.75 * s
    if turn < 0.5:
        pts = [(0, 0.95), (0.55, 0.6), (0.8, -0.2), (0.82, -1.0), (0.5, -1.8), (-0.1, -2.1), (-0.68, -1.75), (-0.92, -0.9), (-0.78, 0.1), (-0.45, 0.75)]
        hp = smooth_path([(hx + u * s, hy + v * s) for u, v in pts])
        shape(cv, hp, pal[0], pal[1], pal[2], off=(0.08, 0.04), seed=seed)
        cv.save(); cv.clipPath(hp, doAntiAlias=True)
        for i in range(6):
            yy = hy + (-1.75 + i * 0.32) * s; circle(cv, hx - 0.05 * s, yy, 0.06 * s, P(pal[3], 0.85)); circle(cv, hx - 0.05 * s, yy, 0.14 * s, P(pal[3], 0.25, blur=0.06 * s))
        cv.restore()
    else:
        _alien_head_front(cv, hx, hy, s, t, pal, seed=seed, look=(0, 0))

def shop(cv, x, base, w, h, wall, trim, aw=None, sign=None, seed=0, t=0.0, depth=0.18, lit=0.0):
    """Front-facing shop with a visible right side for 3D feel. x = left edge."""
    dx = w * depth; dy = -w * depth * 0.45
    side = mix(wall, DARK, 0.4)
    S = wpoly([(x + w, base), (x + w + dx, base + dy), (x + w + dx, base - h + dy), (x + w, base - h)], 6, seed, 1.5)
    shape(cv, S, side, mix(side, DARK, 0.3), None, off=(0, 0.0), seed=seed, tex=0.4)
    roof = wpoly([(x - 0.04 * w, base - h), (x + w, base - h), (x + w + dx, base - h + dy), (x + 0.04 * w + dx, base - h + dy)], 6, seed + 1, 1)
    F = wpoly([(x, base), (x + w, base), (x + w, base - h), (x, base - h)], 8, seed, 2)
    shape(cv, F, wall, mix(wall, DARK, 0.25), mix(wall, '#FFFFFF', 0.18), off=(0.03, 0.0), hoff=(-0.015, 0), seed=seed)
    cv.drawPath(roof, P(mix(trim, '#FFFFFF', 0.15)))
    rrect(cv, x + w / 2, base - h, w * 1.08, h * 0.06, 8, P(trim))
    floors = max(1, int(h / 150))
    for f in range(1, floors):
        fy = base - h + f * (h - 150) / max(1, floors - 1) * 0 + (f - 1) * 150 + 90
        for j in range(3):
            wx = x + w * (0.2 + 0.3 * j); on = lit > 0 and ((j + f + seed) % 3 == 0)
            cv.drawPath(round_path([(wx - w * 0.09, fy - 36), (wx + w * 0.09, fy - 36), (wx + w * 0.09, fy + 36), (wx - w * 0.09, fy + 36)], 10), P(mix(trim, DARK, 0.2)))
            wp = round_path([(wx - w * 0.07, fy - 30), (wx + w * 0.07, fy - 30), (wx + w * 0.07, fy + 30), (wx - w * 0.07, fy + 30)], 8)
            band_fill(cv, wp, (wx, fy - 30), (wx, fy + 30), ['#9AF0FF', '#5AC8FF', '#2A8AE0'] if not on else ['#FFF0A0', '#FFC24A', '#FF9A2A'])
            cv.drawLine(wx - w * 0.05, fy - 10, wx - w * 0.01, fy - 26, P('#FFFFFF', 0.55, stroke=4))
    # ground floor: door + window + awning
    dw = w * 0.22
    cv.drawPath(round_path([(x + w * 0.12, base), (x + w * 0.12, base - 120), (x + w * 0.12 + dw, base - 120), (x + w * 0.12 + dw, base)], 12), P(mix(trim, DARK, 0.3)))
    circle(cv, x + w * 0.12 + dw * 0.8, base - 60, 5, P(YEL))
    sw_ = round_path([(x + w * 0.45, base - 20), (x + w * 0.45, base - 115), (x + w * 0.9, base - 115), (x + w * 0.9, base - 20)], 10)
    band_fill(cv, sw_, (0, base - 115), (0, base - 20), ['#9AF0FF', '#5AB8F0', '#2A7AD0']); cv.drawLine(x + w * 0.5, base - 35, x + w * 0.6, base - 105, P('#FFFFFF', 0.5, stroke=6))
    if aw:
        n = 6; ay = base - 135
        for i in range(n):
            ax0 = x + w * 0.04 + i * w * 0.92 / n
            pa = skia.Path(); pa.moveTo(ax0, ay - 40); pa.lineTo(ax0 + w * 0.92 / n, ay - 40); pa.lineTo(ax0 + w * 0.92 / n, ay); pa.quadTo(ax0 + w * 0.46 / n, ay + 22, ax0, ay); pa.close()
            cv.drawPath(pa, P(aw[i % 2]))
        cv.drawRect(skia.Rect.MakeLTRB(x + w * 0.04, ay - 46, x + w * 0.96, ay - 38), P(mix(aw[0], DARK, 0.3)))
    if sign:
        sy = base - 175 - (0 if not aw else 30)
        rrect(cv, x + w / 2, sy, w * 0.7, 46, 14, P(mix(trim, DARK, 0.2))); rrect(cv, x + w / 2, sy - 3, w * 0.7, 46, 14, P(trim))
        text(cv, sign, x + w / 2, sy - 3, 30, '#FFFFFF', 1, shadow=False, tf=TF)

def ftower(cv, x, base, w, h, body, neon, t, seed=0, top='spire', a=1.0):
    """Futuristic tapered tower with cylindrical shading + neon edges."""
    tw = w * 0.62
    pts = [(x - w / 2, base), (x - tw / 2, base - h), (x + tw / 2, base - h), (x + w / 2, base)]
    B = round_path(pts, 18)
    band_fill(cv, B, (x - w / 2, 0), (x + w / 2, 0), [mix(body, DARK, 0.35), mix(body, '#FFFFFF', 0.08), mix(body, '#FFFFFF', 0.2), body, mix(body, DARK, 0.25), mix(body, DARK, 0.5)])
    finish(cv, B, seed, 0.35, 0.3, blot=False)
    for i in range(int(h / 46)):
        yy = base - 30 - i * 46; k_ = (base - yy) / h; ww = lerp(w, tw, k_) * 0.8
        on = math.sin(t * 1.5 + i * 0.8 + seed) > -0.4
        cv.drawLine(x - ww / 2, yy, x + ww / 2, yy, P('#FFE9A0' if (i + seed) % 4 == 0 else neon, 0.75 if on else 0.25, stroke=5))
    for d in (-1, 1):
        cv.drawLine(x + d * w / 2, base, x + d * tw / 2, base - h, P(neon, 0.9, stroke=4)); cv.drawLine(x + d * w / 2, base, x + d * tw / 2, base - h, P(neon, 0.35, blur=8, stroke=14))
    ty = base - h
    if top == 'spire':
        sp = round_path([(x - tw / 2, ty), (x, ty - h * 0.35), (x + tw / 2, ty)], 6)
        band_fill(cv, sp, (x - tw / 2, 0), (x + tw / 2, 0), [mix(body, '#FFFFFF', 0.15), body, mix(body, DARK, 0.4)])
        circle(cv, x, ty - h * 0.35, 8, P(PNK)); circle(cv, x, ty - h * 0.35, 22, P(PNK, 0.4 + 0.3 * math.sin(t * 4 + seed), blur=10))
    elif top == 'ring':
        oval(cv, x, ty - 30, tw * 1.1, tw * 0.3, P(neon, 0.9, stroke=8)); oval(cv, x, ty - 30, tw * 1.1, tw * 0.3, P(neon, 0.35, blur=12, stroke=24))
        sphere(cv, x, ty - 30, tw * 0.32, mix(body, '#FFFFFF', 0.2), seed)
    elif top == 'dome':
        dp = skia.Path(); dp.addArc(skia.Rect.MakeLTRB(x - tw * 0.55, ty - tw * 0.55, x + tw * 0.55, ty + tw * 0.55), 180, 180); dp.close()
        cv.drawPath(dp, rad(x - tw * 0.2, ty - tw * 0.3, tw * 0.7, ['#BFF8FF', neon, mix(neon, DARK, 0.5)]))

# ---- from sim3
def cloud2(cv, x, y, s, seed=0, a=1.0):
    p = wblob([(x - 1.1 * s, y + 0.15 * s, 0.6 * s), (x - 0.4 * s, y - 0.35 * s, 0.8 * s), (x + 0.5 * s, y - 0.15 * s, 0.7 * s), (x + 1.2 * s, y + 0.2 * s, 0.5 * s), (x, y + 0.25 * s, 0.6 * s)], seed, 0.04)
    clip = skia.Path(); clip.addRect(skia.Rect.MakeLTRB(x - 3 * s, y - 3 * s, x + 3 * s, y + 0.6 * s))
    pp = skia.Op(p, clip, skia.PathOp.kIntersect_PathOp) or p
    shape(cv, pp, '#FFFFFF', '#8EC8F0', None, off=(0.0, 0.12), seed=seed, tex=0.3, grad=0.5, a=a)

def esb(cv, x, base_y, t, top_y=95):
    """Empire State Building, flat 2.5D (banded facade + side face)."""
    k = (base_y - top_y) / 490.0
    cv.save(); cv.translate(x, top_y); cv.scale(k, k); cv.translate(-x, -30)
    base = 520
    tiers = [(250, base, 300), (196, 300, 262), (150, 262, 232), (112, 232, 206), (84, 206, 184)]
    for (w, y0, y1) in tiers:
        dx = w * 0.12; dy = -w * 0.04
        side = round_path([(x + w / 2, y0), (x + w / 2 + dx, y0 + dy), (x + w / 2 + dx, y1 + dy), (x + w / 2, y1)], 3)
        band_fill(cv, side, (x + w / 2, 0), (x + w / 2 + dx, 0), ['#9A8A7A', '#86766A'])
        F = round_path([(x - w / 2, y0), (x + w / 2, y0), (x + w / 2, y1), (x - w / 2, y1)], 3)
        band_fill(cv, F, (x - w / 2, 0), (x + w / 2, 0), ['#FFF2D6', '#F2E2C0', '#E6D2AC', '#D6C098', '#C4AC84'])
        cv.save(); cv.clipPath(F, doAntiAlias=True)
        for i in range(int(w / 16)):
            xx = x - w / 2 + 8 + i * 16
            cv.drawLine(xx, y1, xx, y0, P('#7A6A86', 0.55, stroke=4))
        rs = np.random.default_rng(int(w))
        for _ in range(int(w / 6)):
            circle(cv, x - w / 2 + rs.uniform(6, w - 6), rs.uniform(y1, y0), 2.2, P('#FFE27A', 0.8))
        cv.restore()
        finish(cv, F, int(w), 0.3, 0.0)
        cv.drawLine(x - w / 2 - 4, y1, x + w / 2 + dx, y1 + dy, P('#FFFFFF', 0.6, stroke=4))
    # crown fins + mast + antenna
    for i in range(5):
        fx = x - 34 + i * 17; cv.drawLine(fx, 184, fx, 170, P('#E6D2AC', 1, stroke=6))
    mast = round_path([(x - 26, 184), (x - 12, 120), (x + 12, 120), (x + 26, 184)], 6)
    band_fill(cv, mast, (x - 26, 0), (x + 26, 0), ['#F2E2C0', '#D6C098', '#B09C78'])
    rrect(cv, x, 122, 34, 10, 4, P('#C8B08A'))
    cv.drawLine(x, 120, x, 40, P('#D0C0A8', 1, stroke=6)); cv.drawLine(x, 70, x, 30, P('#B8A890', 1, stroke=3))
    on = 0.5 + 0.5 * math.sin(t * 5)
    circle(cv, x, 32, 5, P('#FF3A3A', 0.6 + 0.4 * on)); circle(cv, x, 32, 16, P('#FF3A3A', 0.35 * on, blur=6))
    cv.restore()

def liberty(cv, x, base_y, t, top_y=60):
    """Statue of Liberty on its pedestal, flat 2.5D banded."""
    k = (base_y - top_y) / 560.0
    cv.save(); cv.translate(x, top_y); cv.scale(k, k); cv.translate(-x, 0)
    G = ['#8AF0D2', '#5CD4B0', '#3EB896', '#2A9A7E', '#1E7A66']
    stone = ['#F2DCB8', '#E0C69C', '#C8AA80', '#A88A64']
    # pedestal (tiers)
    for (w, y0, y1) in ((170, 560, 470), (140, 470, 420), (156, 420, 404), (118, 404, 330), (132, 330, 316)):
        F = round_path([(x - w / 2, y0), (x + w / 2, y0), (x + w / 2, y1), (x - w / 2, y1)], 3)
        band_fill(cv, F, (x - w / 2, 0), (x + w / 2, 0), stone)
        side = round_path([(x + w / 2, y0), (x + w / 2 + w * 0.1, y0 - 5), (x + w / 2 + w * 0.1, y1 - 5), (x + w / 2, y1)], 2)
        cv.drawPath(side, P('#8A6E50'))
        cv.drawLine(x - w / 2, y1, x + w / 2, y1, P('#FFF2D8', 0.7, stroke=3))
    for i in range(3):
        rrect(cv, x - 34 + i * 34, 370, 16, 50, 4, P('#8A6E50'))
    # robe (body)
    robe = smooth_path([(x - 34, 316), (x - 40, 250), (x - 34, 180), (x - 26, 140), (x - 10, 118), (x + 14, 118), (x + 28, 138), (x + 34, 190), (x + 40, 260), (x + 36, 316)])
    band_fill(cv, robe, (x - 40, 0), (x + 40, 0), G)
    cv.save(); cv.clipPath(robe, doAntiAlias=True)
    for (x0, y0, x1, y1) in ((-24, 316, -14, 160), (-6, 316, 2, 170), (14, 316, 16, 190), (28, 316, 22, 200), (-30, 220, 20, 150)):
        cv.drawLine(x + x0, y0, x + x1, y1, P('#1E7A66', 0.55, stroke=3))
    cv.restore()
    finish(cv, robe, 4, 0.3, 0.0)
    # base plinth of statue
    cv.drawPath(round_path([(x - 42, 316), (x + 42, 316), (x + 38, 302), (x - 38, 302)], 3), P('#3EB896'))
    # left arm + tablet
    tab = round_path([(x + 22, 168), (x + 46, 160), (x + 52, 214), (x + 28, 222)], 4)
    band_fill(cv, tab, (x + 22, 0), (x + 52, 0), ['#8AF0D2', '#5CD4B0', '#3EB896']); cv.drawLine(x + 27, 172, x + 47, 166, P('#1E7A66', 0.6, stroke=2))
    cv.drawLine(x + 20, 140, x + 30, 190, P('#3EB896', 1, stroke=12))
    # raised right arm + torch
    arm = smooth_path([(x - 26, 140), (x - 34, 100), (x - 36, 52), (x - 30, 30), (x - 22, 32), (x - 20, 60), (x - 14, 104), (x - 12, 130)])
    band_fill(cv, arm, (x - 36, 0), (x - 12, 0), G[:4])
    cv.drawPath(round_path([(x - 36, 30), (x - 18, 30), (x - 20, 6), (x - 34, 6)], 3), P('#5CD4B0'))
    cv.drawPath(round_path([(x - 42, 8), (x - 12, 8), (x - 16, -2), (x - 38, -2)], 3), P('#3EB896'))
    fl = 1 + 0.08 * math.sin(t * 9)
    circle(cv, x - 27, -14, 26, P('#FFC21A', 0.45, blur=12))
    flame = smooth_path([(x - 37, -2), (x - 36, -16 * fl), (x - 27, -32 * fl), (x - 18, -16 * fl), (x - 17, -2)])
    band_fill(cv, flame, (x - 37, 0), (x - 17, 0), ['#FFE45A', '#FFC21A', '#F0A000'])
    # head + crown
    head = wcirc(x - 2, 104, 15, 3, 0.02)
    band_fill(cv, head, (x - 17, 0), (x + 13, 0), ['#8AF0D2', '#5CD4B0', '#3EB896'])
    cv.drawLine(x - 8, 108, x + 2, 108, P('#1E7A66', 0.6, stroke=2))
    for i in range(7):
        ang = math.radians(-160 + i * 23)
        cv.drawPath(round_path([(x - 2 + math.cos(ang - 0.12) * 12, 92 + math.sin(ang - 0.12) * 6), (x - 2 + math.cos(ang) * 34, 92 + math.sin(ang) * 22), (x - 2 + math.cos(ang + 0.12) * 12, 92 + math.sin(ang + 0.12) * 6)], 2), P('#5CD4B0'))
    cv.drawPath(round_path([(x - 16, 96), (x + 12, 96), (x + 10, 88), (x - 14, 88)], 3), P('#3EB896'))
    cv.restore()

def taxi(cv, x, y, s, t, d=1):
    cv.save(); cv.translate(x, y); cv.scale(d, 1)
    ao(cv, 0, 0, 2.4 * s, 0.25 * s)
    body = round_path([(-2.2 * s, -0.25 * s), (2.3 * s, -0.25 * s), (2.3 * s, -0.95 * s), (1.2 * s, -1.05 * s), (0.7 * s, -1.65 * s), (-1.1 * s, -1.65 * s), (-1.6 * s, -1.05 * s), (-2.2 * s, -1.0 * s)], 0.25 * s)
    band_fill(cv, body, (0, -1.65 * s), (0, -0.25 * s), ['#FFE45A', '#FFD000', '#F0B800', '#D89A00'])
    for (a_, b_) in (((-1.0, -1.55), (-0.1, -1.1)), ((0.05, -1.55), (0.65, -1.1))):
        cv.drawPath(round_path([(a_[0] * s, a_[1] * s), (b_[0] * s, a_[1] * s), (b_[0] * s + (0.35 * s if b_[0] > 0.5 else 0), b_[1] * s), (a_[0] * s - 0.3 * s if a_[0] < -0.5 else a_[0] * s, b_[1] * s)], 0.08 * s), P('#5AB8F0'))
    for i in range(8): cv.drawRect(skia.Rect.MakeXYWH(-1.9 * s + i * 0.45 * s, -0.75 * s, 0.22 * s, 0.14 * s), P('#1A1A2A'))
    rrect(cv, -0.2 * s, -1.8 * s, 0.9 * s, 0.3 * s, 0.08 * s, P('#FFFFFF')); text(cv, 'TAXI', -0.2 * s, -1.8 * s, 0.24 * s, '#1A1A2A', 1, shadow=False, tf=TF)
    for wx in (-1.4, 1.5):
        circle(cv, wx * s, -0.2 * s, 0.45 * s, P('#1A1A2A')); circle(cv, wx * s, -0.2 * s, 0.22 * s, P('#C8C8D8'))
    oval(cv, 2.25 * s, -0.8 * s, 0.1 * s, 0.12 * s, P('#FFF6C0'))
    cv.restore()

def hotdog_cart(cv, x, y, t):
    ao(cv, x, y, 120, 16)
    for wx in (-70, 70): circle(cv, x + wx, y - 18, 20, P('#1A1A2A')); circle(cv, x + wx, y - 18, 9, P('#C8C8D8'))
    cart = round_path([(x - 110, y - 30), (x + 110, y - 30), (x + 110, y - 140), (x - 110, y - 140)], 14)
    band_fill(cv, cart, (x - 110, 0), (x + 110, 0), ['#F2F4FF', '#D8DCEC', '#B8BCD0', '#9A9EB8'])
    rrect(cv, x, y - 95, 170, 40, 8, P('#E8102E')); text(cv, 'HOT DOGS', x, y - 95, 26, '#FFFFFF', 1, shadow=False, tf=TF)
    cv.drawLine(x, y - 140, x, y - 290, P('#3A3A4A', 1, stroke=6))
    for i in range(6):
        a0 = 180 + i * 30
        pa = skia.Path(); pa.moveTo(x, y - 300); pa.arcTo(skia.Rect.MakeLTRB(x - 150, y - 360, x + 150, y - 240), a0, 30, False); pa.close()
        cv.drawPath(pa, P('#1E5AE0' if i % 2 else '#FFD000'))

def street_sign(cv, x, y):
    for i, (txt, dy) in enumerate((('5 AV', 0), ('W 34 ST', 46))):
        rrect(cv, x + 70, y + dy, 150, 38, 6, P('#0E7A3A')); rrect(cv, x + 70, y + dy, 142, 30, 4, P('#FFFFFF', 1, stroke=2))
        text(cv, txt, x + 70, y + dy, 22, '#FFFFFF', 1, shadow=False, tf=TF)

def skyway(cv, pts, t, hc, n=14, sp=0.25, seed=0):
    pa = skia.Path(); pa.moveTo(*pts[0]); pa.cubicTo(*pts[1], *pts[2], *pts[3])
    cv.drawPath(pa, P(hc, 0.25, stroke=14, blur=6)); cv.drawPath(pa, P(hc, 0.5, stroke=3))
    meas = skia.PathMeasure(pa, False); L = meas.getLength()
    for i in range(n):
        u = (t * sp + i / n + seed * 0.13) % 1
        pos = meas.getPosTan(u * L)
        if pos:
            (px, py), _ = pos
            circle(cv, px, py, 9, P('#FFFFFF', 0.5, blur=5)); circle(cv, px, py, 4, P('#FFFFFF'))

def saucer(cv, x, y, s, hc, d=1):
    cv.drawLine(x - d * 4 * s, y, x, y, P(hc, 0.5, stroke=s * 0.3)); cv.drawLine(x - d * 4 * s, y, x, y, P(hc, 0.25, blur=s * 0.3, stroke=s * 0.9))
    shape(cv, woval(x, y, 1.6 * s, 0.45 * s, 2), '#D8D0FF', '#7A70C0', '#FFFFFF', off=(0, 0.2), tex=0.2)
    dp = skia.Path(); dp.addArc(skia.Rect.MakeLTRB(x - 0.7 * s, y - 0.75 * s, x + 0.7 * s, y + 0.45 * s), 180, 180); dp.close()
    cv.drawPath(dp, rad(x - 0.2 * s, y - 0.4 * s, s, ['#BFF8FF', hc]))
    for i in range(3): circle(cv, x - 0.8 * s + i * 0.8 * s, y + 0.15 * s, 0.1 * s, P(YEL))

def world_computer(cv, x, base, t, h=640):
    for i in range(4):
        ph = (t * 0.45 + i / 4) % 1; yy = lerp(base - 160, base - h, ph)
        oval(cv, x, yy, 230 - ph * 80, 46 - ph * 14, P(CY_, 0.8 * (1 - ph), stroke=6)); oval(cv, x, yy, 230 - ph * 80, 46 - ph * 14, P(CY_, 0.3 * (1 - ph), blur=10, stroke=18))
    zig = round_path([(x - 420, base), (x - 330, base - 120), (x + 330, base - 120), (x + 420, base)], 20)
    band_fill(cv, zig, (x - 420, 0), (x + 420, 0), ['#22106A', '#4A2AB0', '#6A4AE0', '#4A2AB0', '#2A1478', '#14083E']); finish(cv, zig, 1, 0.3, 0.0)
    for i in range(9): rrect(cv, x - 280 + i * 70, base - 60, 30, 14, 6, P(CY_, 0.5 + 0.5 * math.sin(t * 3 + i)))
    col_ = round_path([(x - 110, base - 120), (x - 80, base - h), (x + 80, base - h), (x + 110, base - 120)], 16)
    band_fill(cv, col_, (x - 110, 0), (x + 110, 0), ['#2A1A7A', '#5A4AD0', '#8A7AFF', '#B8ACFF', '#6A5AE0', '#3A2AA0', '#1E0E5A']); finish(cv, col_, 3, 0.3, 0.0)
    for i in range(int((h - 140) / 40)):
        yy = base - 150 - i * 40; cv.drawLine(x - 70, yy, x + 70, yy, P(CY_, 0.35 + 0.35 * math.sin(t * 4 - i * 0.5), stroke=4))
    ty = base - h
    oval(cv, x, ty, 190, 48, P('#3A2A9A')); oval(cv, x, ty - 8, 170, 40, P('#6A5AE0'))
    circle(cv, x, ty - 90, 150, P(CY_, 0.35, blur=60)); sphere(cv, x, ty - 90, 72, '#7AF0FF', 4)
    cv.drawRect(skia.Rect.MakeLTRB(x - 30, -200, x + 30, ty - 120), lin(0, ty - 120, 0, -200, [colA(CY_, 0.75), colA(CY_, 0.0)]))

def code_lines(cv, x, y, n_chars, sz=30, lh=46, a=1.0):
    left = n_chars
    for i, (ln, _) in enumerate(CODE):
        if left <= 0: break
        shown = ln[:left]; left -= len(ln)
        tx = x
        toks = []
        import re
        for m in re.finditer(r'[A-Za-z_]+|\d+|[^A-Za-z_\d]+', shown): toks.append(m.group(0))
        for tok in toks:
            c = '#FFFFFF'
            if tok in ('import', 'True'): c = '#FF7AF0'
            elif tok.isdigit(): c = '#FFD000'
            elif tok in ('Sim', 'reality'): c = CY_
            elif tok in ('create', 'add', 'spawn', 'run'): c = '#7AFF9A'
            elif tok.strip() in ('>', '=', '(', ')', '.', ',', '()'): c = '#B8A8FF'
            f = font(sz, MONO); cv.drawString(tok, tx, y + i * lh, f, P(c, a)); tx += f.measureText(tok)
        if left <= 0 and len(shown) < len(ln) or (left <= 0 and i == len(CODE) - 1):
            if int((y + n_chars) * 0 + 1) and (int(n_chars * 0.2) % 2 == 0 or True): rrect(cv, tx + 10, y + i * lh - 10, 14, 30, 2, P(CY_, 0.9))

class IsoRot(IsoR):
    def __init__(s, x, y, k, yaw): super().__init__(x, y, k); s.c, s.sn = math.cos(yaw), math.sin(yaw)
    def rot(s, u, v): return u * s.c - v * s.sn, u * s.sn + v * s.c
    def p(s, u, v, z):
        ur, vr = s.rot(u, v); return (s.x + (ur - vr) * s.k, s.y + (ur + vr) * s.k * 0.5 - z * s.k)
    def d(s, u, v): ur, vr = s.rot(u, v); return ur + vr
    def rblock(s, cv, u0, v0, u1, v1, z0, z1, top, left, right):
        P_ = s.p; k = s.k
        faces = [((u0, v0), (u1, v0), (0, -1)), ((u1, v0), (u1, v1), (1, 0)), ((u1, v1), (u0, v1), (0, 1)), ((u0, v1), (u0, v0), (-1, 0))]
        vis = []
        for (a_, b_, n) in faces:
            nr = s.rot(*n)
            if nr[0] + nr[1] > 0.02: vis.append((s.d((a_[0] + b_[0]) / 2, (a_[1] + b_[1]) / 2), a_, b_, nr))
        vis.sort()
        for (_, a_, b_, nr) in vis:
            c = left if (nr[0] - nr[1]) < 0 else right
            pts = [P_(a_[0], a_[1], z1), P_(b_[0], b_[1], z1), P_(b_[0], b_[1], z0), P_(a_[0], a_[1], z0)]
            pth = round_path(pts, k * 0.1); q0, q1 = pts[0], pts[3]
            band_fill(cv, pth, q0, q1, [c, mix(c, DARK, 0.12), mix(c, DARK, 0.25)])
        T = round_path([P_(u0, v0, z1), P_(u1, v0, z1), P_(u1, v1, z1), P_(u0, v1, z1)], k * 0.12)
        band_fill(cv, T, P_(u0, v0, z1), P_(u1, v1, z1), [mix(top, '#FFFFFF', 0.2), mix(top, '#FFFFFF', 0.08), top])
        cv.save(); cv.clipPath(T, doAntiAlias=True); cv.drawPath(T, P('#FFFFFF', 0.4, stroke=max(2, k * 0.08))); cv.restore()
    def rroof(s, cv, u0, v0, u1, v1, z0, z1, c):
        P_ = s.p; um, vm = (u0 + u1) / 2, (v0 + v1) / 2
        tris = [((u0, v0), (u1, v0), (0, -1)), ((u1, v0), (u1, v1), (1, 0)), ((u1, v1), (u0, v1), (0, 1)), ((u0, v1), (u0, v0), (-1, 0))]
        vis = []
        for (a_, b_, n) in tris:
            nr = s.rot(*n)
            if nr[0] + nr[1] > -0.4: vis.append((nr[0] + nr[1], a_, b_, nr))
        vis.sort()
        for (_, a_, b_, nr) in vis:
            cc = mix(c, '#FFFFFF', 0.18) if (nr[0] - nr[1]) < 0 else mix(c, DARK, 0.2)
            cv.drawPath(round_path([P_(a_[0], a_[1], z0), P_(b_[0], b_[1], z0), P_(um, vm, z1)], s.k * 0.05), P(cc))

def holo_island(cv, cx, cy, k, t, yaw, a=1.0, kpop=1.0):
    if kpop <= 0 or a <= 0: return
    S = 900
    surf = skia.Surface(S, S)
    with surf as c2:
        I = IsoRot(S / 2, S / 2 + 40, k, yaw); top, left, right, d1, d2 = BIOMES['village']
        I.rblock(c2, -0.9, -0.9, 0.9, 0.9, -2.7, -1.8, d2, mix(d1, DARK, 0.3), mix(d2, DARK, 0.4))
        I.rblock(c2, -1.5, -1.5, 1.5, 1.5, -1.9, -1.0, d1, mix(d1, DARK, 0.15), mix(d2, DARK, 0.25))
        I.rblock(c2, -2, -2, 2, 2, -1.05, -0.3, d1, d1, d2)
        I.rblock(c2, -2.06, -2.06, 2.06, 2.06, -0.32, 0, top, left, right)
        props = [(-1.0, -0.8, 'house', '#F03A3A'), (0.6, -1.1, 'house', '#2F5BEA'), (1.0, 0.8, 'tree', 0), (-1.2, 0.9, 'tree', 1), (0.9, -0.2, 'tree', 2), (-0.2, 1.2, 'house', '#FFB020')]
        props.sort(key=lambda q: I.d(q[0], q[1]))
        for (u, v, kind, arg) in props:
            if kind == 'house':
                I.rblock(c2, u - 0.35, v - 0.35, u + 0.35, v + 0.35, 0, 0.55, '#FFE0B0', '#D8B890', '#B89870')
                I.rroof(c2, u - 0.42, v - 0.42, u + 0.42, v + 0.42, 0.55, 1.05, arg)
            else:
                bx, by = I.p(u, v, 0); tree(c2, bx, by, 0.8 * k, t, arg)
    arr = surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType).astype(np.float32)
    al = arr[..., 3:4] / 255.0
    lum = arr[..., :3].mean(2, keepdims=True) / 255.0
    cyan = np.array([63, 230, 255], np.float32)
    rgb = arr[..., :3] * 0.45 + (cyan * (0.35 + 0.9 * lum)) * 0.55
    sl = ((np.arange(S) // 3) % 2 == 0).astype(np.float32)[:, None, None]
    rgb = rgb * (0.82 + 0.18 * sl)
    fl = 0.85 + 0.15 * math.sin(t * 40) * math.sin(t * 7)
    alpha = np.clip(al * 0.92 * a * fl, 0, 1)
    out = np.dstack([np.clip(rgb, 0, 255), alpha * 255]).astype(np.uint8)
    # premultiply for skia
    pm = out.astype(np.float32); pm[..., :3] *= pm[..., 3:4] / 255.0
    img = skia.Image.fromarray(np.ascontiguousarray(pm.astype(np.uint8)), colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kPremul_AlphaType)
    cv.save(); cv.translate(cx, cy); cv.scale(kpop, kpop)
    gp = skia.Paint(ImageFilter=skia.ImageFilters.Blur(18, 18), Alphaf=0.6); gp.setBlendMode(skia.BlendMode.kPlus)
    cv.drawImage(img, -S / 2, -S / 2, skia.SamplingOptions(), gp)
    cv.drawImage(img, -S / 2, -S / 2)
    cv.restore()

def wire_version(img, t):
    g = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY); e = cv2.Canny(g, 50, 140); e = cv2.dilate(e, np.ones((2, 2), np.uint8))
    out = np.zeros_like(img); out[:] = (14, 10, 52)
    out[::40, :] = (30, 90, 160); out[:, ::40] = (30, 90, 160)
    out[e > 0] = (63, 230, 255)
    rs = np.random.default_rng(int(t * 30))
    for _ in range(90):
        x, y = rs.integers(0, W - 20), rs.integers(20, H)
        cv2.putText(out, str(rs.integers(0, 2)), (int(x), int(y)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (63, 230, 255), 1, cv2.LINE_AA)
    return out

def cyan_tint(img, k):
    f = img.astype(np.float32); lum = f.mean(2, keepdims=True)
    c = np.array([63, 230, 255], np.float32) * (0.3 + lum / 255.0)
    out = f * (1 - 0.65 * k) + c * 0.65 * k
    out[::4] *= (1 - 0.25 * k)
    return np.clip(out, 0, 255).astype(np.uint8)

def block_mask(t, cov, cw=160, ch=135, seed=0):
    rs = np.random.default_rng(int(t * 15) + seed * 1000)
    m = (rs.random((H // ch + 1, W // cw + 1)) < cov).astype(np.float32)
    return cv2.resize(m, ((W // cw + 1) * cw, (H // ch + 1) * ch), interpolation=cv2.INTER_NEAREST)[:H, :W, None]

def zoom_img(a, z, c=(W / 2, H / 2)):
    M = cv2.getRotationMatrix2D(c, 0, z); return cv2.warpAffine(a, M, (W, H), borderMode=cv2.BORDER_REPLICATE)

def post(a, i):
    global VIG
    if VIG is None:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
        VIG = (1 - 0.25 * np.clip(r - 0.45, 0, 1) ** 1.5)[..., None]
    hsv = cv2.cvtColor(a, cv2.COLOR_RGB2HSV).astype(np.float32)
    hsv[..., 1] = np.clip(hsv[..., 1] * 1.14, 0, 255)
    f = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB).astype(np.float32)
    f = (f - 128) * 1.05 + 128
    lum = f.max(2, keepdims=True); br = f * np.clip((lum - 205) / 50, 0, 1)
    sm = cv2.GaussianBlur(cv2.resize(br, (W // 4, H // 4), interpolation=cv2.INTER_AREA), (0, 0), 8)
    f = f + cv2.resize(sm, (W, H)) * 0.3
    f = f * VIG + GRAIN[(i // 2) % 4] * 3.0
    return np.clip(f, 0, 255).astype(np.uint8)

BIOMES = {
    'village': ('#5FD22E', '#3E9E24', '#2C7A1A', '#E0761E', '#B4560F'), 'desert': ('#FFB52E', '#E0861A', '#B8640E', '#D4701A', '#A8520E'),
    'snow': ('#EEF4FF', '#9DB8E8', '#6F8FD0', '#5868B0', '#434F98'), 'ocean': ('#18A8F2', '#0B78D0', '#0858A6', '#E8B84A', '#BE8C26'),
    'volcano': ('#5E2E92', '#40206E', '#2C1450', '#3A1A5A', '#26103E'), 'city': ('#7F8CFF', '#5560E0', '#3A42B4', '#4A3A9A', '#33287A'),
    'forest': ('#2EBE4E', '#1E8E38', '#146A2A', '#C8661A', '#984A10'), 'candy': ('#FF4FC0', '#D2309A', '#A61E78', '#FFB52E', '#DA861A'),
    'gold': ('#FFD34A', '#E8A21E', '#C07A10', '#E0761E', '#B4560F')}

SKINS = ['#E0A070', '#B06A3E', '#7A4426', '#F0BE90', '#965A32']

ALIEN = {'blue': ('#2EC6E0', '#1786A8', '#8AF2FF', '#FFFFFF'), 'violet': ('#B07AFF', '#7A48D8', '#DCC4FF', '#FFF06A'), 'green': ('#4CE08A', '#22A060', '#A8FFC8', '#FFFFFF')}

SUIT = ('#B0146E', '#E8408E', '#FFC21A')

CODE = [("> import reality", ['#FF7AF0', '#FFFFFF']), ("world = Sim.create(seed=4812331)", ['#FFFFFF']), ("world.add(physics, time, light)", ['#FFFFFF']),
        ("world.spawn(life, minds=True)", ['#FFFFFF']), ("world.run()", ['#7AFF9A'])]
# ---- module-level resources
TEX = _noise_tex()
TEXSH = TEX.makeShader(skia.TileMode.kRepeat, skia.TileMode.kRepeat)
GRAIN = [cv2.resize(np.random.default_rng(i).normal(0, 1, (H // 2, W // 2)).astype(np.float32), (W, H))[..., None] for i in range(4)]
VIG = None
