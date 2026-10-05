# engine.py — hand-painted 2D look in skia: boiling ink, watercolour washes, paper, camera, timing.
import math, zlib
import numpy as np
import skia

W, H, FPS = 1920, 1080, 24
BPM, OFFSET = 120.0, 0.05
BEAT = 60.0 / BPM
BOIL = 12  # boil drawings per second

INK = '#2E2530'
PAPER = '#EFE6D2'

# ---------------------------------------------------------------- maths / timing
def clamp(x, a=0.0, b=1.0): return a if x < a else b if x > b else x
def lerp(a, b, k): return a + (b - a) * k
def seg(t, a, b): return clamp((t - a) / (b - a)) if b != a else float(t >= a)
def ease(k): k = clamp(k); return k * k * (3 - 2 * k)
def easeIn(k): k = clamp(k); return k * k * k
def easeOut(k): k = clamp(k); return 1 - (1 - k) ** 3
def backOut(k, s=1.7):
    k = clamp(k) - 1; return 1 + k * k * ((s + 1) * k + s)
def elasticOut(k):
    k = clamp(k)
    if k in (0, 1): return k
    return 2 ** (-10 * k) * math.sin((k * 10 - .75) * (2 * math.pi / 3)) + 1
def kf(t, keys, fn=ease):
    """keys [(t, v), ...] ; v float or tuple"""
    if t <= keys[0][0]: return keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t <= t1:
            k = fn(seg(t, t0, t1))
            if isinstance(v0, (tuple, list)): return tuple(lerp(a, b, k) for a, b in zip(v0, v1))
            return lerp(v0, v1, k)
    return keys[-1][1]
def spring(t, t0, k=1.0, w=14.0, d=5.0):
    if t < t0: return 0.0
    x = t - t0; return k * math.exp(-d * x) * math.sin(w * x)
def bp(t): return (t - OFFSET) / BEAT
def pulse(t, k=6.0):
    b = bp(t)
    return math.exp(-k * (b - math.floor(b))) if b >= 0 else 0.0
def wob(t, f=1.0, ph=0.0): return math.sin((t * f + ph) * 2 * math.pi)
def hash1(*a): return (zlib.crc32(('|'.join(map(str, a))).encode()) & 0xffffffff) / 0xffffffff
def arcPt(p0, p1, h, k):
    return (lerp(p0[0], p1[0], k), lerp(p0[1], p1[1], k) - h * 4 * k * (1 - k))

# ---------------------------------------------------------------- colour
def hexc(h, a=255):
    h = h.lstrip('#'); return skia.ColorSetARGB(int(a), int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
def mix(a, b, k):
    a, b = a.lstrip('#'), b.lstrip('#')
    ca = [int(a[i:i + 2], 16) for i in (0, 2, 4)]; cb = [int(b[i:i + 2], 16) for i in (0, 2, 4)]
    return '#%02X%02X%02X' % tuple(int(round(lerp(x, y, clamp(k)))) for x, y in zip(ca, cb))

# ---------------------------------------------------------------- boil
class Ctx:
    t = 0.0
    bi = 0
    zoom = 1.0
    canvas = None
CTX = Ctx()

def rng(key):
    return np.random.default_rng(zlib.crc32(f'{key}|{CTX.bi}'.encode()))

# ---------------------------------------------------------------- textures
_rs = np.random.default_rng(7)
def _noise_img(n, scale_list, lo, hi, seed):
    r = np.random.default_rng(seed); acc = np.zeros((n, n), np.float32)
    import cv2
    for s, wgt in scale_list:
        m = max(2, n // s); a = r.random((m, m)).astype(np.float32)
        a = cv2.resize(a, (n, n), interpolation=cv2.INTER_CUBIC); acc += a * wgt
    acc = (acc - acc.min()) / (acc.max() - acc.min())
    return lo + (hi - lo) * acc
def _make_tex():
    import cv2
    n = 1024
    v = _noise_img(n, [(4, 1.0), (16, .7), (64, .5), (256, .35)], 0.0, 1.0, 3)
    a = (np.clip((v - .35) / .65, 0, 1) ** 1.3 * 120).astype(np.uint8)  # pigment granulation as alpha
    img = np.zeros((n, n, 4), np.uint8); img[..., 3] = a  # black with alpha -> multiply-ish darkening
    return skia.Image.fromarray(img, colorType=skia.ColorType.kRGBA_8888_ColorType, alphaType=skia.AlphaType.kPremul_AlphaType)
TEX = _make_tex()
TEXSH = TEX.makeShader(skia.TileMode.kRepeat, skia.TileMode.kRepeat, skia.SamplingOptions())
_TP = {}
def texpaint(var, alpha):
    q = (var, int(round(clamp(alpha) * 20)))
    p = _TP.get(q)
    if p is None:
        m = skia.Matrix(); m.setTranslate(var * 311.0, var * 577.0)
        p = skia.Paint(AntiAlias=True); p.setShader(TEXSH.makeWithLocalMatrix(m))
        p.setBlendMode(skia.BlendMode.kMultiply); p.setAlphaf(q[1] / 20); _TP[q] = p
    return p

def _make_paper():
    import cv2
    v = _noise_img(2048, [(2, .6), (8, .8), (40, .5), (300, .4), (1024, .5)], 0, 1, 11)[:H, :W]
    fib = np.random.default_rng(5).random((H, W)).astype(np.float32)
    fib = cv2.GaussianBlur(fib, (0, 0), 0.8)
    p = 0.945 + 0.055 * v + 0.03 * (fib - .5)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    vig = 1 - 0.13 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) ** 1.4
    return np.clip(p * vig, 0, 1.0)[..., None]
PAPERTEX = _make_paper()

# ---------------------------------------------------------------- geometry
def catmull(P, closed=False, n=8):
    P = np.asarray(P, np.float64)
    if len(P) < 3: return P
    if closed: Q = np.vstack([P[-1:], P, P[:2]])
    else: Q = np.vstack([P[:1], P, P[-1:]])
    out = []
    ts = np.linspace(0, 1, n, endpoint=False)[:, None]
    for i in range(1, len(Q) - 2):
        p0, p1, p2, p3 = Q[i - 1], Q[i], Q[i + 1], Q[i + 2]
        out.append(.5 * ((2 * p1) + (-p0 + p2) * ts + (2 * p0 - 5 * p1 + 4 * p2 - p3) * ts ** 2 + (-p0 + 3 * p1 - 3 * p2 + p3) * ts ** 3))
    out = np.vstack(out)
    if not closed: out = np.vstack([out, P[-1:]])
    return out

def ell(cx, cy, rx, ry, n=36, rot=0.0):
    a = np.linspace(0, 2 * np.pi, n, endpoint=False)
    x, y = rx * np.cos(a), ry * np.sin(a)
    c, s = math.cos(rot), math.sin(rot)
    return np.stack([cx + x * c - y * s, cy + x * s + y * c], 1)

def rrect(x, y, w, h, r, n=6):
    r = min(r, w / 2, h / 2); pts = []
    for cx, cy, a0 in ((x + w - r, y + r, -90), (x + w - r, y + h - r, 0), (x + r, y + h - r, 90), (x + r, y + r, 180)):
        for k in range(n + 1):
            a = math.radians(a0 + 90 * k / n); pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return np.array(pts)

def rect(x, y, w, h):
    return np.array([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], np.float64)

def densify(P, closed, step=6.0):
    P = np.asarray(P, np.float64)
    Q = np.vstack([P, P[:1]]) if closed else P
    out = []
    for a, b in zip(Q[:-1], Q[1:]):
        L = np.hypot(*(b - a)); n = max(1, int(L / step))
        out.append(a + (b - a) * np.linspace(0, 1, n, endpoint=False)[:, None])
    if not closed: out.append(P[-1:])
    return np.vstack(out)

def boil(P, key, amp, closed=True):
    """smooth low-frequency wobble along normals; changes 12x/sec"""
    P = np.asarray(P, np.float64)
    if amp <= 0 or len(P) < 3: return P
    r = rng(key); n = len(P)
    s = np.arange(n) / n
    off = np.zeros(n)
    for k in (1, 2, 3, 5):
        off += r.normal(0, 1) / k * np.sin(2 * np.pi * (k * s + r.random()))
    off += r.normal(0, .25, n)
    if closed: d = np.roll(P, -1, 0) - np.roll(P, 1, 0)
    else: d = np.gradient(P, axis=0)
    nrm = np.stack([-d[:, 1], d[:, 0]], 1); nrm /= np.maximum(np.hypot(nrm[:, 0], nrm[:, 1]), 1e-6)[:, None]
    return P + nrm * (off * amp)[:, None]

def topath(P, closed=True):
    p = skia.Path(); P = np.asarray(P)
    p.moveTo(float(P[0, 0]), float(P[0, 1]))
    for x, y in P[1:]: p.lineTo(float(x), float(y))
    if closed: p.close()
    return p

# ---------------------------------------------------------------- painting
def _paint(col, a=255, style='fill'):
    p = skia.Paint(AntiAlias=True)
    p.setColor(hexc(col, a) if isinstance(col, str) else col)
    if style == 'stroke': p.setStyle(skia.Paint.kStroke_Style)
    return p

def ribbon(P, w0, w1=None, key='r', closed=False, var=.35):
    """variable-width brush stroke polygon along P"""
    P = np.asarray(P, np.float64)
    n = len(P)
    if n < 2: return None
    if w1 is None: w1 = w0
    r = rng(key)
    s = np.linspace(0, 1, n)
    w = lerp(w0, w1, s)
    ph = r.random(3)
    w = w * (1 + var * (0.6 * np.sin(2 * np.pi * (1.3 * s + ph[0])) + .4 * np.sin(2 * np.pi * (3.7 * s + ph[1]))))
    if not closed:  # taper ends
        tp = np.minimum(1, np.minimum(s, 1 - s) * n / 5.0)
        w = w * (0.35 + 0.65 * np.sqrt(np.clip(tp, 0, 1)))
    if closed: d = np.roll(P, -1, 0) - np.roll(P, 1, 0)
    else: d = np.gradient(P, axis=0)
    nrm = np.stack([-d[:, 1], d[:, 0]], 1); nrm /= np.maximum(np.hypot(nrm[:, 0], nrm[:, 1]), 1e-6)[:, None]
    A = P + nrm * (w / 2)[:, None]; B = P - nrm * (w / 2)[:, None]
    if closed:
        p = topath(A); q = topath(B[::-1]); p.addPath(q); p.setFillType(skia.PathFillType.kWinding)
        return p
    return topath(np.vstack([A, B[::-1]]))

def ink(P, sw=3.0, col=INK, key='ink', closed=True, amp=None, a=255, var=.35, step=5.0):
    c = CTX.canvas
    if amp is None: amp = sw * .35
    D = densify(P, closed, step)
    D = boil(D, key + 'i', amp, closed)
    if closed:
        path = ribbon(D, sw, key=key, closed=True, var=var)
        pa = _paint(col, a); c.drawPath(path, pa)
    else:
        c.drawPath(ribbon(D, sw, key=key, closed=False, var=var), _paint(col, a))

def fill(P, col, key='f', a=255, tex=.55, edge=.4, amp=1.2, outline=0.0, ocol=INK, glowcol=None, smooth=False, step=6.0):
    """watercolour-ish flat wash: colour + pigment granulation + darkened edges (+ optional ink outline)"""
    c = CTX.canvas
    D = densify(P, True, step)
    D = boil(D, key, amp, True)
    path = topath(D)
    c.drawPath(path, _paint(col, a))
    if tex > 0:
        c.drawPath(path, texpaint(int(hash1(key) * 4), tex * a / 255))
    if edge > 0:
        ec = mix(col, '#2E2530', .45)
        for wdt, al in ((9, .3), (3.5, .6)):
            ep = _paint(ec, int(edge * a * al), 'stroke'); ep.setStrokeWidth(wdt)
            c.drawPath(path, ep)
    if outline > 0:
        ink(P, outline, ocol, key + 'o', True)
    return path

def wash(P, col, key='w', a=255):
    """plain flat shape with a slight boil, no texture (for small things)"""
    D = boil(densify(P, True, 6), key, .8, True)
    CTX.canvas.drawPath(topath(D), _paint(col, a))

def glow(x, y, r, col, a=.6):
    c = CTX.canvas
    if r <= 1 or a <= 0: return
    p = skia.Paint(AntiAlias=True)
    cc = hexc(col)
    cols = [skia.ColorSetA(cc, int(255 * clamp(a))), skia.ColorSetA(cc, int(100 * clamp(a))), skia.ColorSetA(cc, 0)]
    p.setShader(skia.GradientShader.MakeRadial((x, y), r, cols, [0, .4, 1]))
    p.setBlendMode(skia.BlendMode.kPlus)
    c.drawCircle(x, y, r, p)

def shade(P, col, a, key='sh', blur=0):
    """soft translucent shadow/tint (multiply)"""
    c = CTX.canvas
    D = boil(densify(P, True, 8), key, 1.5, True)
    p = _paint(col, a); p.setBlendMode(skia.BlendMode.kMultiply)
    if blur: p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    c.drawPath(topath(D), p)

def grad_rect(x, y, w, h, cols, pos=None, vertical=True):
    p = skia.Paint(AntiAlias=True)
    pts = [(x, y), (x, y + h)] if vertical else [(x, y), (x + w, y)]
    p.setShader(skia.GradientShader.MakeLinear(pts, [hexc(c) for c in cols], pos))
    CTX.canvas.drawRect(skia.Rect.MakeXYWH(x, y, w, h), p)
    # granulation on top
    tp = texpaint(0, .35)
    CTX.canvas.drawRect(skia.Rect.MakeXYWH(x, y, w, h), tp)

# ---------------------------------------------------------------- camera
class Cam:
    def __init__(self, cx=W / 2, cy=H / 2, zoom=1.0, rot=0.0): self.cx, self.cy, self.zoom, self.rot = cx, cy, zoom, rot
def cam_begin(cx, cy, zoom=1.0, rot=0.0):
    c = CTX.canvas; c.save()
    c.translate(W / 2, H / 2); c.rotate(rot); c.scale(zoom, zoom); c.translate(-cx, -cy)
    CTX.cam = (cx, cy, zoom, rot)
def cam_end():
    CTX.canvas.restore(); CTX.cam = (W / 2, H / 2, 1, 0)
def to_screen(x, y):
    cx, cy, z, r = getattr(CTX, 'cam', (W / 2, H / 2, 1, 0))
    a = math.radians(r); dx, dy = (x - cx) * z, (y - cy) * z
    return (W / 2 + dx * math.cos(a) - dy * math.sin(a), H / 2 + dx * math.sin(a) + dy * math.cos(a))
def shake(t, t0, amt=14, dur=.35):
    if t < t0 or t > t0 + dur: return (0, 0)
    k = 1 - (t - t0) / dur
    return (amt * k * math.sin(t * 91), amt * k * math.cos(t * 77))

# ---------------------------------------------------------------- full-frame effects (screen space)
def brush_wipe(p, cols=('#E2692A', '#7DD9BE'), key='wipe', direction=1):
    """fat strokes cover the frame (p 0->.5) then drag off (.5->1). cut under full cover (p=.5)"""
    if p <= 0 or p >= 1: return
    c = CTX.canvas
    n = 7
    for i in range(n):
        y = -60 + i * (H + 120) / (n - 1)
        d = i * .05
        a = easeInOut(seg(p, d, .5 - .02 * (n - i)))
        b = easeInOut(seg(p, .5 + d * .6, 1.0 - (n - i) * .015))
        x0, x1 = -300 + b * (W + 600), -300 + a * (W + 600)
        if direction < 0: x0, x1 = W - x1, W - x0
        if x1 - x0 < 2: continue
        P = np.array([[x0, y + 12 * math.sin(i)], [lerp(x0, x1, .5), y - 18], [x1, y + 8]])
        D = catmull(P, False, 12)
        path = ribbon(D, 260, 230, key=f'{key}{i}', var=.12)
        c.drawPath(path, _paint(cols[i % len(cols)]))
def easeInOut(k): return ease(k)

def iris(cx, cy, r, col=INK):
    c = CTX.canvas
    p = skia.Path(); p.addRect(skia.Rect.MakeXYWH(-50, -50, W + 100, H + 100))
    p.addPath(topath(boil(ell(cx, cy, max(r, 0.1), max(r, 0.1), 90), 'iris', 3)))
    p.setFillType(skia.PathFillType.kEvenOdd)
    c.drawPath(p, _paint(col))

def flash(k, col='#FFF6E0'):
    if k <= 0: return
    p = _paint(col, int(255 * clamp(k))); p.setBlendMode(skia.BlendMode.kScreen)
    CTX.canvas.drawRect(skia.Rect.MakeXYWH(0, 0, W, H), p)

def finish(arr_bgra):
    """multiply paper grain + vignette; returns BGR uint8"""
    f = arr_bgra[..., :3].astype(np.float32) * PAPERTEX
    return np.clip(f, 0, 255).astype(np.uint8)


def blob_union(circles, key, amp=1.5):
    """union of boiled circles -> one skia path (cumulus clouds, bushes)"""
    path = None
    for i, (cx, cy, r) in enumerate(circles):
        P = boil(ell(cx, cy, r, r * .92, max(16, int(r / 4))), f'{key}{i}', amp, True)
        p = topath(P)
        path = p if path is None else skia.Op(path, p, skia.PathOp.kUnion_PathOp)
    return path

def fillpath(path, col, key='fp', a=255, tex=.5, edge=.4, outline=0.0, ocol=INK):
    c = CTX.canvas
    c.drawPath(path, _paint(col, a))
    if tex > 0: c.drawPath(path, texpaint(int(hash1(key) * 4), tex * a / 255))
    if edge > 0:
        ec = mix(col, '#2E2530', .45)
        for wdt, al in ((9, .3), (3.5, .6)):
            ep = _paint(ec, int(edge * a * al), 'stroke'); ep.setStrokeWidth(wdt); c.drawPath(path, ep)
    if outline > 0:
        op = _paint(ocol, a, 'stroke'); op.setStrokeWidth(outline); op.setStrokeJoin(skia.Paint.kRound_Join)
        c.drawPath(path, op)
