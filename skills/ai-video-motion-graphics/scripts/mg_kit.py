"""Motion-graphics helpers for frame-by-frame rendering (numpy float RGB 0-1 frames + PIL RGBA UI layers).

Typical frame:  base = float32 HxWx3  ->  draw UI into a PIL RGBA layer  ->  composite(base, ui)
"""
import math, os
import cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1920, 1080
INK, CLAY, WHITE = (29, 27, 25), (217, 119, 87), (255, 255, 255)
GREEN, RED, DARK = (96, 170, 110), (214, 72, 64), (24, 22, 20)
import os as _os, glob as _glob
_SKILL_FONTS = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', 'assets', 'fonts')
_FONT_DIRS = [_SKILL_FONTS, '/usr/share/fonts', '/Library/Fonts', _os.path.expanduser('~/Library/Fonts'), 'C:/Windows/Fonts',
              _os.path.expandvars(r'%LOCALAPPDATA%/Microsoft/Windows/Fonts')]
def _ff(*names):
    # bundled/downloaded fonts first (scripts/setup_env.py), then system fonts, then DejaVu / PIL default
    for n in names:
        for d in _FONT_DIRS:
            if _os.path.isdir(d):
                h = _glob.glob(_os.path.join(d, '**', n), recursive=True)
                if h: return h[0]
    return names[-1]
_FONTS = {'B': _ff('Poppins-Bold.ttf', 'DejaVuSans-Bold.ttf'), 'M': _ff('Poppins-Medium.ttf', 'DejaVuSans.ttf'), 'R': _ff('Poppins-Regular.ttf', 'DejaVuSans.ttf'),
          'I': _ff('Lora-Italic-Variable.ttf', 'DejaVuSerif-Italic.ttf'), 'MONO': _ff('DejaVuSansMono.ttf', 'consola.ttf', 'Menlo.ttc')}
_fc = {}
def F(kind, size):
    k = (kind, int(size))
    if k not in _fc: _fc[k] = ImageFont.truetype(_FONTS[kind], int(size))
    return _fc[k]

# ---------------- easing
def cl(x, a=0.0, b=1.0): return max(a, min(b, x))
def eo(x): x = cl(x); return 1 - (1 - x) ** 3                       # ease-out cubic
def eio(x): x = cl(x); return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
def eob(x, c=1.6): x = cl(x); return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2   # ease-out back (overshoot)
def smooth(x): x = cl(x); return x * x * (3 - 2 * x)

# ---------------- compositing
def composite(base, ui):
    """base float RGB, ui PIL RGBA (same size) -> float RGB"""
    U = np.asarray(ui).astype(np.float32) / 255
    return base * (1 - U[:, :, 3:4]) + U[:, :, :3] * U[:, :, 3:4]
def load_rgb(path, size=None):
    im = cv2.imread(path)
    if size: im = cv2.resize(im, size, interpolation=cv2.INTER_AREA)
    return im[:, :, ::-1].astype(np.float32) / 255
def save_jpg(path, img): cv2.imwrite(path, (np.clip(img, 0, 1) * 255).astype(np.uint8)[:, :, ::-1], [cv2.IMWRITE_JPEG_QUALITY, 96])
_rm = {}
def rounded_mask(w, h, r):
    k = (w, h, r)
    if k not in _rm:
        m = Image.new('L', (w, h), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], r, fill=255)
        _rm[k] = np.asarray(m).astype(np.float32) / 255
    return _rm[k]
def soft_shadow_mask(rect, r=24, blur=22, off=(6, 18), strength=0.3, size=(W, H)):
    x0, y0, x1, y1 = rect; m = Image.new('L', size, 0)
    ImageDraw.Draw(m).rounded_rectangle([x0 + off[0], y0 + off[1], x1 + off[0], y1 + off[1]], r, fill=255)
    return np.asarray(m.filter(ImageFilter.GaussianBlur(blur))).astype(np.float32) / 255 * strength
def put_card(base, img, x, y, r=24, alpha=1.0, shadow=True):
    """place float RGB img as a rounded card with soft shadow at (x,y)"""
    h, w = img.shape[:2]
    if shadow: base *= (1 - soft_shadow_mask((x, y, x + w, y + h), r + 2, size=(base.shape[1], base.shape[0]))[:, :, None] * alpha)
    m = rounded_mask(w, h, r)[:, :, None] * alpha
    X0, Y0 = max(int(x), 0), max(int(y), 0); X1, Y1 = min(int(x) + w, base.shape[1]), min(int(y) + h, base.shape[0])
    sub = img[Y0 - int(y):Y1 - int(y), X0 - int(x):X1 - int(x)]; mm = m[Y0 - int(y):Y1 - int(y), X0 - int(x):X1 - int(x)]
    base[Y0:Y1, X0:X1] = base[Y0:Y1, X0:X1] * (1 - mm) + sub * mm
    return base
def bottom_gradient(img, start=0.45, strength=0.62, amount=1.0):
    """darken the lower part of a frame so white captions read"""
    h = img.shape[0]; yy = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
    return img * (1 - np.clip((yy - start) / (1 - start), 0, 1) * strength * amount)
def dim(img, k, amount=0.30, desat=0.40):
    g = img.mean(2, keepdims=True); return (img * (1 - desat * k) + g * desat * k) * (1 - amount * k)

# ---------------- text
def shadowed(im, off=(0, 6), blur=10, a=0.55):
    A = np.asarray(im)[:, :, 3].astype(np.float32) / 255
    s = Image.fromarray((A * 255 * a).astype(np.uint8)).filter(ImageFilter.GaussianBlur(blur))
    b = Image.new('RGBA', im.size, (0, 0, 0, 0)); b.putalpha(s)
    o = Image.new('RGBA', im.size, (0, 0, 0, 0)); o.alpha_composite(b, off); o.alpha_composite(im); return o
def strong_shadow(im): return shadowed(shadowed(im, (0, 4), 10, 0.75), (0, 0), 3, 0.6)
def words_line(ui, words, font, x, y, t, center=False, shadow=True, rise=26, dur=0.3):
    """word-synced caption. words=[(text, rgb, t_in)]. Returns end x."""
    tot = sum(font.getlength(w + ' ') for w, _, _ in words)
    if center: x -= tot / 2
    for w, col, ti in words:
        adv = font.getlength(w + ' '); u = (t - ti) / dur
        if u > 0:
            asc, desc = font.getmetrics(); hh = asc + desc + 30
            li = Image.new('RGBA', (int(adv) + 30, hh), (0, 0, 0, 0)); ImageDraw.Draw(li).text((10, 10), w, font=font, fill=col + (255,))
            if shadow: li = strong_shadow(li)
            arr = np.array(li); arr[:, :, 3] = (arr[:, :, 3] * cl(u * 2)).astype(np.uint8)
            ui.alpha_composite(Image.fromarray(arr), (int(x - 10), int(y - 10 + (1 - eo(u)) * rise)))
        x += adv
    return x
def ink_bbox(s, font, x, y):
    """visible glyph bounds of text drawn at (x,y) with anchor 'la' (for centring pills)"""
    x0 = y0 = 1e9; x1 = y1 = -1e9; xc = x
    for c in s:
        if c != ' ':
            b = font.getbbox(c); x0 = min(x0, xc + b[0]); y0 = min(y0, y + b[1]); x1 = max(x1, xc + b[2]); y1 = max(y1, y + b[3])
        xc += font.getlength(c)
    return x0, y0, x1, y1
def pill(text, font, fill=CLAY, text_col=WHITE, pad=20, h=54, alpha=245):
    tw = font.getlength(text); w = int(tw + 2 * pad)
    im = Image.new('RGBA', (w + 4, h + 4), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([2, 2, w, h], h // 2, fill=fill + (alpha,)); d.text((pad + 2, h / 2 + 2), text, font=font, fill=text_col + (255,), anchor='lm')
    return im
def paste(ui, im, x, y, a=1.0, anchor='lt'):
    if a <= 0.01: return
    if a < 1: arr = np.array(im); arr[:, :, 3] = (arr[:, :, 3] * a).astype(np.uint8); im = Image.fromarray(arr)
    if anchor == 'c': x -= im.size[0] / 2; y -= im.size[1] / 2
    ui.alpha_composite(im, (int(x), int(y)))

# ---------------- icons
def glow_icon(kind, size):
    """'check' (green) or 'cross' (red) disc with white rim + coloured glow. size = disc diameter-ish in px."""
    S = 200; im = Image.new('RGBA', (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = S / 2; r = 36
    col = GREEN if kind == 'check' else RED
    g = Image.new('RGBA', (S, S), (0, 0, 0, 0)); ImageDraw.Draw(g).ellipse([c - r - 6, c - r - 6, c + r + 6, c + r + 6], fill=col + (255,))
    g = g.filter(ImageFilter.GaussianBlur(16)); arr = np.array(g); arr[:, :, 3] = np.clip(arr[:, :, 3].astype(int) * 2, 0, 255).astype(np.uint8)
    im.alpha_composite(Image.fromarray(arr))
    d.ellipse([c - r - 3, c - r - 3, c + r + 3, c + r + 3], fill=WHITE + (255,)); d.ellipse([c - r, c - r, c + r, c + r], fill=col + (255,))
    if kind == 'check': d.line([(c - 17, c + 1), (c - 5, c + 13), (c + 18, c - 12)], fill=WHITE + (255,), width=8, joint='curve')
    else: d.line([(c - 13, c - 13), (c + 13, c + 13)], fill=WHITE + (255,), width=8); d.line([(c + 13, c - 13), (c - 13, c + 13)], fill=WHITE + (255,), width=8)
    k = max(size, 1) / 80.0; return im.resize((max(1, int(S * k)), max(1, int(S * k))), Image.LANCZOS)
def logo_from_file(path, size, rot=0.0):
    """official logo file -> RGBA, resized in premultiplied space (no dark fringes)"""
    lg = Image.open(path).convert('RGBa')
    return lg.resize((size, size), Image.LANCZOS).rotate(rot, Image.BICUBIC, expand=True).convert('RGBA')

# ---------------- frosted glass & slider
def frosted(base, box, r, a, tint=0.22, darken=0.72, border=0.55):
    x0, y0, x1, y1 = [int(round(v)) for v in box]; Hh, Ww = base.shape[:2]
    X0c, Y0c, X1c, Y1c = max(x0, 0), max(y0, 0), min(x1, Ww), min(y1, Hh)
    if X1c <= X0c or Y1c <= Y0c or a <= 0: return base
    p = 30; PX0, PY0, PX1, PY1 = max(X0c - p, 0), max(Y0c - p, 0), min(X1c + p, Ww), min(Y1c + p, Hh)
    blur = cv2.GaussianBlur(base[PY0:PY1, PX0:PX1], (0, 0), 14)[Y0c - PY0:Y1c - PY0, X0c - PX0:X1c - PX0]
    glass = np.clip(blur * darken + tint, 0, 1)
    m = Image.new('L', (x1 - x0, y1 - y0), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, x1 - x0 - 1, y1 - y0 - 1], r, fill=255)
    e = Image.new('L', (x1 - x0, y1 - y0), 0); ImageDraw.Draw(e).rounded_rectangle([0, 0, x1 - x0 - 1, y1 - y0 - 1], r, outline=255, width=2)
    sl = (slice(Y0c - y0, Y1c - y0), slice(X0c - x0, X1c - x0))
    mk = (np.asarray(m).astype(np.float32) / 255)[sl][:, :, None] * a; ek = (np.asarray(e).astype(np.float32) / 255)[sl][:, :, None] * a * border
    out = base.copy(); reg = out[Y0c:Y1c, X0c:X1c]; reg[:] = reg * (1 - mk) + glass * mk; reg[:] = reg * (1 - ek) + ek
    return out
def slider_curve(t, t0, mid=0.46, crawl=0.10):
    """glide in -> slow crawl through the middle -> accelerate out. None before t0."""
    if t < t0: return None
    return cl(mid * eo((t - t0) / 0.8) + crawl * smooth((t - t0 - 0.5) / 2.05) + (1 - mid - crawl) * eio((t - t0 - 2.3) / 0.95))
class BeforeAfterSlider:
    """reveal `after` from the left over `before`. Draws divider, frosted handle and frosted labels."""
    def __init__(self, left_label="With motion graphics", right_label="AI video only", font=None):
        self.ll, self.rl, self.f = left_label, right_label, font or F('M', 28)
    def render(self, before, after, p, alpha=1.0):
        Hh, Ww = before.shape[:2]; xs = int(p * Ww); img = before.copy(); img[:, :xs] = after[:, :xs]
        if alpha <= 0: return img, None
        X = np.arange(Ww, dtype=np.float32)[None, :]; xd = p * Ww
        img = np.clip(img + (np.exp(-((X - xd) / 9) ** 2) * 0.35 * alpha)[:, :, None], 0, 1)
        line = np.clip(1 - np.abs(X - xd) / 1.2, 0, 1) * 0.95 * alpha; img = img * (1 - line[:, :, None]) + line[:, :, None]
        img = frosted(img, (xd - 26, Hh / 2 - 64, xd + 26, Hh / 2 + 64), 26, alpha)
        ui = Image.new('RGBA', (Ww, Hh), (0, 0, 0, 0)); d = ImageDraw.Draw(ui); hy = Hh / 2
        for s in (-1, 1):
            cx = xd + s * 9; d.line([(cx - s * 4, hy - 9), (cx + s * 3, hy), (cx - s * 4, hy + 9)], fill=WHITE + (int(255 * alpha),), width=3, joint='curve')
        for txt, a_, left in ((self.ll, cl((p - 0.12) / 0.1) * alpha, True), (self.rl, cl((0.88 - p) / 0.1) * alpha, False)):
            if a_ <= 0.01: continue
            tw = self.f.getlength(txt); bw, bh = tw + 48, 56; bx = 56 if left else Ww - 56 - bw; by = Hh - 56 - bh
            img = frosted(img, (bx, by, bx + bw, by + bh), 28, a_)
            if left: d.ellipse([bx + 20, by + bh / 2 - 5, bx + 30, by + bh / 2 + 5], fill=CLAY + (int(255 * a_),))
            d.text((bx + (38 if left else 24), by + bh / 2 + 1), txt, font=self.f, fill=WHITE + (int(255 * a_),), anchor='lm')
        return img, ui

# ---------------- transitions
def whip(img_a, img_b, u):
    """horizontal whip-pan transition between two same-size frames, u in 0..1"""
    w = img_a.shape[1]; dx = int(eio(u) * w); out = np.zeros_like(img_a)
    out[:, :w - dx] = img_a[:, dx:]; out[:, w - dx:] = img_b[:, :dx]
    return cv2.blur(out, (int(1 + 60 * math.sin(math.pi * cl(u))), 1))
def diagonal_wipe_mask(w, h, u, slant=0.35, feather=6):
    """right->left slanted reveal mask (1 = revealed)"""
    ys = np.arange(h, dtype=np.float32)[:, None]; xs = np.arange(w, dtype=np.float32)[None, :]
    edge = (w + 300) * (1 - eio(u)) - 150 + (ys - h / 2) * slant
    return np.clip((xs - edge) / feather, 0, 1), edge

# ---------------- 3D projection helpers
FOC = 1500.0
def rot(ry=0.0, rx=0.0, rz=0.0):
    cy, sy, cx, sx, cz, sz = math.cos(ry), math.sin(ry), math.cos(rx), math.sin(rx), math.cos(rz), math.sin(rz)
    return np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]) @ np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]]) @ np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
def quad3d(w, h, cx, cy, s=1.0, R=None, z=0.0, f=FOC):
    R = np.eye(3) if R is None else R
    P = (np.array([[-w / 2, -h / 2, z], [w / 2, -h / 2, z], [w / 2, h / 2, z], [-w / 2, h / 2, z]]) * s) @ R.T
    return [(cx + f * X / (f + Z), cy + f * Y / (f + Z)) for X, Y, Z in P]
def tilted_plate(w, h, ang, lift, sc, cx, cy, f=1700.0):
    """plate tilted back by `ang` rad around X, lifted by `lift` px (for exploded layer stacks)"""
    pts = []
    for x, y in [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]:
        x *= sc; y *= sc; Y = y * math.cos(ang) - lift; Z = y * math.sin(ang); pts.append((cx + f * x / (f + Z), cy + f * Y / (f + Z)))
    return pts
def warp_rgba(canvas, rgba, quad):
    """premultiplied perspective warp of float RGBA onto float RGB canvas (in place)"""
    h, w = rgba.shape[:2]; dst = np.float32(quad); Hh, Ww = canvas.shape[:2]
    x0, y0 = np.floor(dst.min(0)).astype(int) - 2; x1, y1 = np.ceil(dst.max(0)).astype(int) + 2
    x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, Ww), min(y1, Hh)
    if x1 <= x0 or y1 <= y0: return
    M = cv2.getPerspectiveTransform(np.float32([[0, 0], [w, 0], [w, h], [0, h]]), dst - np.float32([x0, y0]))
    pm = np.dstack([rgba[:, :, :3] * rgba[:, :, 3:4], rgba[:, :, 3:4]])
    wi = cv2.warpPerspective(pm, M, (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR, borderValue=0)
    al = np.clip(wi[:, :, 3:4], 0, 1); reg = canvas[y0:y1, x0:x1]; reg[:] = reg * (1 - al) + wi[:, :, :3]

# ---------------- callouts (use sparingly: 2-3 max)
def dotted_box(d, box, a, t=0.0, step=18):
    x0, y0, x1, y1 = box; ph = (t * 36) % step; segs = []
    for x in np.arange(x0 + ph, x1, step): segs += [((x, y0), (min(x + 9, x1), y0)), ((x, y1), (min(x + 9, x1), y1))]
    for y in np.arange(y0 + ph, y1, step): segs += [((x0, y), (x0, min(y + 9, y1))), ((x1, y), (x1, min(y + 9, y1)))]
    for p0, p1 in segs: d.line([p0, p1], fill=(0, 0, 0, int(120 * a)), width=7)
    for p0, p1 in segs: d.line([p0, p1], fill=WHITE + (int(255 * a),), width=3)
def dotted_arrow(d, p0, p1, a, grow=1.0):
    L = math.dist(p0, p1); ux, uy = (p1[0] - p0[0]) / max(L, 1), (p1[1] - p0[1]) / max(L, 1)
    for k in range(int(L * grow / 16)):
        c = (p0[0] + ux * (k * 16 + 4), p0[1] + uy * (k * 16 + 4))
        d.ellipse([c[0] - 5, c[1] - 5, c[0] + 5, c[1] + 5], fill=(0, 0, 0, int(110 * a))); d.ellipse([c[0] - 3.5, c[1] - 3.5, c[0] + 3.5, c[1] + 3.5], fill=WHITE + (int(255 * a),))
    if grow >= 0.98:
        bx, by = p1[0] - ux * 22, p1[1] - uy * 22; px, py = -uy * 12, ux * 12
        d.polygon([p1, (bx + px, by + py), (bx - px, by - py)], fill=WHITE + (int(255 * a),))
def white_label(ui, text, pos, a, font=None):
    font = font or F('B', 40); li = Image.new('RGBA', (int(font.getlength(text)) + 60, int(font.size * 2.2)), (0, 0, 0, 0))
    ImageDraw.Draw(li).text((30, 20), text, font=font, fill=WHITE + (255,)); li = shadowed(shadowed(li, (0, 3), 9, 0.95), (0, 0), 4, 0.8)
    paste(ui, li, pos[0] - 30, pos[1] - 20, a)

if __name__ == '__main__':
    # self-test: synthetic before/after frame with captions and icons
    before = np.full((H, W, 3), 0.25, np.float32); after = before.copy(); after[200:400, 200:700] = [0.2, 0.7, 0.8]
    img, sl_ui = BeforeAfterSlider().render(before, after, slider_curve(6.0, 4.65))
    img = bottom_gradient(img)
    ui = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ui.alpha_composite(sl_ui)
    words_line(ui, [("But", WHITE, 0), ("it", WHITE, 0), ("struggles", WHITE, 0)], F('B', 56), W / 2, 685, 1.0, center=True)
    x = words_line(ui, [("precise", CLAY, 0), ("control", CLAY, 0)], F('B', 96), W / 2, 752, 1.0, center=True)
    ic = glow_icon('cross', 80); paste(ui, ic, x + 10, 806 - ic.size[1] / 2)
    out = composite(img, ui); save_jpg('/tmp/mg_kit_selftest.jpg', out); print('ok /tmp/mg_kit_selftest.jpg')


# =====================================================================
# Additions (Beginner Guide 2026 intro): dark-theme cards, loading reveal,
# AR glass panel fitted to a hand-drawn outline, tight text shadows.
# =====================================================================
PASTEL_OK = False   # reminder: pastel accents (yellow/green) read badly - pick saturated accents
ACCENT_GREEN = (1, 254, 129)     # user-approved accent on the dark grid
DEEP_GREEN = (22, 168, 96)       # audio clips / check marks (same saturation family, darker)
SKY = (54, 138, 214)             # secondary clip colour
DARK_CARD = (22, 25, 32)

def tight_shadow(im):
    """small crisp shadow for coloured words on light/dark grids (big blurry shadows look smudgy)"""
    return shadowed(shadowed(im, (0, 3), 3, 0.45), (0, 1), 1, 0.35)

def text_shadow_footage(im):
    """white text over bright footage: strong soft shadow"""
    return shadowed(shadowed(im, (0, 5), 12, 0.8), (0, 0), 4, 0.5)

def place_card(base, img, x, y, alpha_img=None, r=18, a=1.0, glow=0.28, border=0.45):
    """rounded card for DARK backgrounds: thin white border + faint white glow (a black drop shadow is invisible on dark).
    alpha_img: optional HxWx1 reveal alpha."""
    h, w = img.shape[:2]; x, y = int(round(x)), int(round(y))
    if a <= 0.01: return base
    if glow > 0:
        gm = soft_shadow_mask((x - 4, y - 4, x + w + 4, y + h + 4), r + 6, 26, (0, 0), glow * a * 0.35, (base.shape[1], base.shape[0]))[:, :, None]
        base += (1 - base) * gm
    m = rounded_mask(w, h, r)[:, :, None] * a
    if alpha_img is not None: m = m * alpha_img
    X0, Y0 = max(x, 0), max(y, 0); X1, Y1 = min(x + w, base.shape[1]), min(y + h, base.shape[0])
    if X1 <= X0 or Y1 <= Y0: return base
    sl = (slice(Y0 - y, Y1 - y), slice(X0 - x, X1 - x))
    base[Y0:Y1, X0:X1] = base[Y0:Y1, X0:X1] * (1 - m[sl]) + img[sl] * m[sl]
    if border > 0:
        e = Image.new('L', (w, h), 0); ImageDraw.Draw(e).rounded_rectangle([0, 0, w - 1, h - 1], r, outline=255, width=2)
        em = np.asarray(e).astype(np.float32)[:, :, None] / 255 * border * a
        if alpha_img is not None: em = em * np.clip(alpha_img * 1.5, 0, 1)
        base[Y0:Y1, X0:X1] = base[Y0:Y1, X0:X1] * (1 - em[sl]) + em[sl]
    return base

def loading_card(base, ui, img, x, y, t0, t, dur=0.5, a=1.0, accent=ACCENT_GREEN, label='Generating video'):
    """'AI video generating' reveal: dark placeholder -> progress bar fills while the clip loads top-to-bottom.
    Preferred over noisy dissolves for generated-video moments (user feedback: tighter, reads as loading)."""
    h, w = img.shape[:2]; x, y = int(x), int(y)
    pa = eo((t - t0) / 0.12) * a; prog = eio((t - t0 - 0.08) / dur)
    base = place_card(base, np.full((h, w, 3), np.array(DARK_CARD, np.float32) / 255), x, y, r=26, a=pa, glow=0.3 * pa)
    if prog > 0:
        yy = np.arange(h, dtype=np.float32)[:, None, None]
        m = np.clip((h * prog - yy) / 10, 0, 1) * np.ones((1, w, 1), np.float32)
        base = place_card(base, img, x, y, m, r=26, a=a, glow=0, border=0.45 * prog)
    d = ImageDraw.Draw(ui)
    if 0 < prog < 1: d.line([(x + 6, y + h * prog), (x + w - 6, y + h * prog)], fill=accent + (int(230 * a),), width=3)
    ba = pa * (1 - cl((t - t0 - 0.08 - dur) / 0.2))
    if ba > 0:
        bw = int(w * 0.46); bx = x + (w - bw) / 2; by = y + h - 70
        d.rounded_rectangle([bx - 28, by - 72, bx + bw + 28, by + 34], 22, fill=(14, 16, 22, int(185 * ba)))
        f = F('B', 30); lab = f'{label}  {int(round(prog * 100))}%'
        im = Image.new('RGBA', (int(f.getlength(lab)) + 48, 90), (0, 0, 0, 0)); ImageDraw.Draw(im).text((24, 24), lab, font=f, fill=WHITE + (255,))
        paste(ui, shadowed(im, (0, 3), 6, 0.8), bx - 24, by - 84, ba)
        d.rounded_rectangle([bx, by, bx + bw, by + 12], 6, fill=(255, 255, 255, int(60 * ba)))
        if prog > 0: d.rounded_rectangle([bx, by, bx + max(12, bw * prog), by + 12], 6, fill=accent + (int(255 * ba),))
    return base

def canvas_quad_from_outline(outline, panel_rect, canvas_size):
    """Map a UI canvas so that `panel_rect` (x0,y0,x1,y1 in canvas px) lands exactly on a user-drawn 4-point
    outline (TL,TR,BR,BL in frame px). Returns the canvas-corner quad for warp_rgba.
    Tip: size the panel with a WIDE aspect (~1.9:1 for a strongly foreshortened outline) or the text looks squashed."""
    x0, y0, x1, y1 = panel_rect; cw, ch = canvas_size
    Hp = cv2.getPerspectiveTransform(np.float32([[x0, y0], [x1, y0], [x1, y1], [x0, y1]]), np.float32(outline))
    return cv2.perspectiveTransform(np.float32([[[0, 0], [cw, 0], [cw, ch], [0, ch]]]), Hp)[0], Hp

def glass_panel(base, ui_rgba, quad, shape_alpha, a=1.0, dark=True):
    """composite a warped frosted-glass UI panel. ui_rgba: float HxWx4 canvas; shape_alpha: float HxW panel mask (canvas).
    dark=True -> dark translucent glass with white text (user's preferred look over a bright room)."""
    Hh, Ww = base.shape[:2]
    Mg = np.zeros((Hh, Ww, 3), np.float32); warp_rgba(Mg, np.dstack([np.ones(shape_alpha.shape + (3,), np.float32), shape_alpha[:, :, None]]), quad)
    Ms = Mg[:, :, :1]
    sh = cv2.GaussianBlur(np.roll(np.roll(Ms, 26, 0), 10, 1), (0, 0), 26)[:, :, None]
    base = base * (1 - 0.30 * sh * a)
    blur = cv2.GaussianBlur(base, (0, 0), 20)
    glass = np.clip(blur * 0.36 + np.array([0.03, 0.035, 0.05], np.float32), 0, 1) if dark else np.clip(blur * 0.55 + 0.42, 0, 1)
    base = base * (1 - Ms * a * 0.96) + glass * Ms * a * 0.96
    U = ui_rgba.copy(); U[:, :, 3] *= np.clip(cv2.dilate(shape_alpha, np.ones((7, 7), np.uint8)), 0, 1)
    warp_rgba(base, U, quad)
    return base

def canvas_to_screen(Hm_canvas, pts):
    """canvas points -> frame points (e.g. to fly thumbnails in screen space into a warped slot)"""
    return cv2.perspectiveTransform(np.float32([pts]), Hm_canvas)[0]
