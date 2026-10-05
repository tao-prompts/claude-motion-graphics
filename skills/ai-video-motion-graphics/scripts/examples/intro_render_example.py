# APPROVED EXAMPLE (Tao Prompts - Beginner Guide 2026 intro, v7). Expects in cwd: th/ p2/ p3/ p4/ frame folders, matte/ + matte2/ (person_matte.py),
# dark_grid.png (see ../../assets/dark_grid.jpg), the Part 3/4 asset PNGs and refs/. Usage: python intro_render_example.py test 60 300  |  python intro_render_example.py 0 330

import os, sys, math, glob
sys.path.insert(0, glob.glob('/root/.claude/skills/synced/*/ai-video-motion-graphics/scripts')[0])
import cv2, numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from mg_kit import *
CLAY = (1, 254, 129)        # accent: green (from reference)
SKY = (54, 138, 214)        # effect clips on the timeline
AUDIO = (22, 168, 96)       # audio clip / check marks: saturated green, a step darker than the accent
import mg_kit; mg_kit.GREEN = AUDIO

FPS = 30
END = 22.0
NF = int(END * FPS)
T1 = 4.95          # cut to part 2 ("And") - talking-head file has a jump cut at 4.967s, stay before it
TX0, TX1 = 11.72, 12.02   # part 2 -> grid transition
T4 = 16.30         # "So let's dive"
PINK = (214, 88, 150)
SOFT = (120, 116, 112)
LSOFT = (175, 180, 190)
LPINK = (255, 160, 205)
PASTEL = (1, 254, 129)      # green accent (Part 1)

# ------------------------------------------------ loaders
_cache = {}
def frame(folder, n, size=None):
    tot = len(os.listdir(folder)); n = min(max(n, 1), tot); k = (folder, n, size)
    if k not in _cache:
        if len(_cache) > 40: _cache.clear()
        _cache[k] = load_rgb(f'{folder}/{n:04d}.jpg', size)
    return _cache[k]
def src24(folder, src_t, size=None): return frame(folder, int(round(src_t * 24)) + 1, size)

def cover(img, w, h):
    """float RGB -> cover-crop to w x h"""
    ih, iw = img.shape[:2]; s = max(w / iw, h / ih)
    r = cv2.resize(img, (max(w, int(iw * s + .5)), max(h, int(ih * s + .5))), interpolation=cv2.INTER_AREA)
    y0 = (r.shape[0] - h) // 2; x0 = (r.shape[1] - w) // 2
    return r[y0:y0 + h, x0:x0 + w]
_img = {}
def asset(path, w, h):
    k = (path, w, h)
    if k not in _img: _img[k] = cover(load_rgb(path), w, h)
    return _img[k]

GRID = cv2.resize(load_rgb('dark_grid.png'), (1920, 1086), interpolation=cv2.INTER_AREA)[3:1083]
GRID = np.clip(GRID * 1.0, 0, 1)

def pil_of(img): return Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))

# smooth noise fields for generation reveals
_nz = {}
def noise(w, h, seed=0):
    k = (w, h, seed)
    if k not in _nz:
        rng = np.random.default_rng(seed); a = rng.random((h // 24 + 2, w // 24 + 2)).astype(np.float32)
        a = cv2.resize(a, (w, h), interpolation=cv2.INTER_CUBIC); a = (a - a.min()) / (a.max() - a.min())
        b = rng.random((h // 6 + 2, w // 6 + 2)).astype(np.float32); b = cv2.resize(b, (w, h), interpolation=cv2.INTER_CUBIC)
        _nz[k] = np.clip(0.8 * a + 0.2 * b, 0, 1)
    return _nz[k]

def gen_card(img, p, seed=0, nw=0.6):
    """'generating' reveal of a float RGB image: returns (rgb, alpha) with bright edge band"""
    h, w = img.shape[:2]
    if p >= 1: return img, np.ones((h, w, 1), np.float32)
    yy = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    field = nw * noise(w, h, seed) + (1 - nw) * yy
    v = p * 1.2 - field
    a = np.clip(v / 0.10, 0, 1)[:, :, None]
    edge = np.clip(1 - np.abs(v - 0.02) / 0.05, 0, 1)[:, :, None] * (p < 1)
    rgb = img * (0.6 + 0.4 * a) + edge * 0.9
    return np.clip(rgb, 0, 1), np.clip(a + edge * 0.8, 0, 1)

def place(base, img, x, y, alpha_img=None, r=18, a=1.0, shadow=0.28, scale=1.0, border=0.45):
    """rounded card with optional per-pixel alpha, scale about its centre"""
    h, w = img.shape[:2]
    if scale != 1.0:
        nw, nh = max(2, int(w * scale)), max(2, int(h * scale))
        x += (w - nw) / 2; y += (h - nh) / 2
        img = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR)
        if alpha_img is not None: alpha_img = cv2.resize(alpha_img, (nw, nh))[:, :, None]
        w, h, r = nw, nh, max(2, int(r * scale))
    if a <= 0.01: return base
    x, y = int(round(x)), int(round(y))
    if shadow > 0:
        gm = soft_shadow_mask((x - 4, y - 4, x + w + 4, y + h + 4), r + 6, 26, (0, 0), shadow * a * 0.35, (base.shape[1], base.shape[0]))[:, :, None]
        base += (1 - base) * gm
    m = rounded_mask(w, h, r)[:, :, None] * a
    if alpha_img is not None: m = m * alpha_img
    X0, Y0 = max(x, 0), max(y, 0); X1, Y1 = min(x + w, base.shape[1]), min(y + h, base.shape[0])
    if X1 <= X0 or Y1 <= Y0: return base
    sub = img[Y0 - y:Y1 - y, X0 - x:X1 - x]; mm = m[Y0 - y:Y1 - y, X0 - x:X1 - x]
    base[Y0:Y1, X0:X1] = base[Y0:Y1, X0:X1] * (1 - mm) + sub * mm
    if border > 0:
        e = Image.new('L', (w, h), 0); ImageDraw.Draw(e).rounded_rectangle([0, 0, w - 1, h - 1], r, outline=255, width=2)
        em = np.asarray(e).astype(np.float32)[:, :, None] / 255 * border * a
        if alpha_img is not None: em = em * np.clip(alpha_img * 1.5, 0, 1)
        em = em[Y0 - y:Y1 - y, X0 - x:X1 - x]
        base[Y0:Y1, X0:X1] = base[Y0:Y1, X0:X1] * (1 - em) + em
    return base

def text_img(s, font, col, pad=24, alpha=255):
    b = font.getbbox(s); w = b[2] + 2 * pad; h = font.size * 2 + 2 * pad
    im = Image.new('RGBA', (int(w), int(h)), (0, 0, 0, 0)); ImageDraw.Draw(im).text((pad, pad), s, font=font, fill=col + (alpha,))
    return im
def halo(im, col=(255, 255, 255), blur=14, a=0.75):
    A = np.asarray(im)[:, :, 3].astype(np.float32) / 255
    s = Image.fromarray(np.clip(A * 255 * a * 1.6, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(blur))
    b = Image.new('RGBA', im.size, col + (0,)); b.putalpha(Image.fromarray((np.asarray(s).astype(np.float32) * a).astype(np.uint8)))
    o = Image.new('RGBA', im.size, (0, 0, 0, 0)); o.alpha_composite(b); o.alpha_composite(im); return o

def word_rise(ui, s, font, col, x, y, t, t0, dur=0.35, rise=30, a=1.0, glow=True, anchor='l'):
    u = (t - t0) / dur
    if u <= 0 or a <= 0.01: return
    im = text_img(s, font, col)
    if glow == 'shadow': im = shadowed(shadowed(im, (0, 5), 12, 0.8), (0, 0), 4, 0.5)
    elif glow == 'tight': im = shadowed(shadowed(im, (0, 3), 3, 0.45), (0, 1), 1, 0.35)
    elif glow: im = halo(im)
    xx = x - (font.getlength(s) if anchor == 'r' else font.getlength(s) / 2 if anchor == 'c' else 0)
    paste(ui, im, xx - 24, y - 24 + (1 - eo(u)) * rise, cl(u * 1.8) * a)

def caption(ui, parts, font, cx, y, t, a=1.0):
    """parts=[(word, colour, t_in)] centred word-synced caption on light background"""
    tot = sum(font.getlength(w + ' ') for w, _, _ in parts) - font.getlength(' ')
    x = cx - tot / 2
    for w, c, ti in parts:
        word_rise(ui, w, font, c, x, y, t, ti - 0.05, 0.32, 26, a, glow=('tight' if c != INK else False))
        x += font.getlength(w + ' ')

# ================================================= PART 1
TERMES = '/usr/share/texmf/fonts/opentype/public/tex-gyre/texgyretermes-bolditalic.otf'
ITF = ImageFont.truetype(TERMES, 100); ITB = ImageFont.truetype(TERMES, 128); BIGF = F('B', 270)
_letters = {}
def big_word(ui, word, t, t_in, t_out, y=110, col=WHITE):
    if t < t_in or t > t_out + 0.4: return
    track = 14
    widths = [BIGF.getlength(c) + track for c in word]; tot = sum(widths) - track
    sc = min(1.0, 1780 / tot); f = F('B', int(270 * sc)) if sc < 1 else BIGF
    widths = [f.getlength(c) + track * sc for c in word]; tot = sum(widths) - track * sc
    x = 960 - tot / 2
    for k, c in enumerate(word):
        kk = (word, c, f.size)
        if kk not in _letters: _letters[kk] = shadowed(shadowed(text_img(c, f, col, pad=40), (0, 8), 18, 0.55), (0, 0), 4, 0.35)
        u_in = (t - t_in - 0.035 * k) / 0.55; u_out = (t - t_out - 0.025 * k) / 0.3
        if u_in > 0:
            dy = (1 - eob(u_in, 1.2)) * 90 - eio(u_out) * 70
            a = cl(u_in * 2.5) * (1 - cl(u_out))
            paste(ui, _letters[kk], x - 40, y - 40 + dy, a)
        x += widths[k]

def part1(t):
    i = int(round(t * FPS)) + 1
    img = frame('th', i).copy(); m = cv2.imread(f'matte/{min(i,150):04d}.png', 0).astype(np.float32)[:, :, None] / 255
    ui = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    # screen 0: small italic lines on the right
    SH = 'shadow'
    o0 = cl((t - 1.18) / 0.25)
    word_rise(ui, 'What you', ITF, WHITE, 1215, 215 - 30 * o0, t, 0.02, a=1 - o0, glow=SH)
    word_rise(ui, 'just watched', ITF, WHITE, 1215, 322 - 30 * o0, t, 0.40, a=1 - o0, glow=SH)
    big_word(ui, 'CINEMATIC', t, 1.36, 2.40)
    o1 = cl((t - 2.40) / 0.25)
    word_rise(ui, 'short', ITB, PASTEL, 1240, 430 - 40 * o1, t, 1.85, a=1 - o1, glow=SH)
    word_rise(ui, 'film', ITB, PASTEL, 1240 + ITB.getlength('short '), 430 - 40 * o1, t, 2.26, a=1 - o1, glow=SH)
    big_word(ui, 'GENERATED', t, 2.50, 4.55)
    o2 = cl((t - 4.55) / 0.3)
    word_rise(ui, 'completely', ITF, WHITE, 1235, 430 - 40 * o2, t, 3.12, a=1 - o2, glow=SH)
    word_rise(ui, 'using', ITF, WHITE, 1235, 545 - 40 * o2, t, 3.84, a=1 - o2, glow=SH)
    word_rise(ui, 'AI', F('B', 124), PASTEL, 1235 + ITF.getlength('using '), 518 - 40 * o2, t, 4.28, a=1 - o2, glow=SH)
    person = img
    dk = smooth(t / 0.4) * (1 - smooth((t - 4.65) / 0.3))
    img = img * (1 - 0.26 * dk * BGDARK)
    out = composite(img, ui)
    out = out * (1 - m) + person * m
    # gentle cinematic grade + push-in
    g = 0.5 + 0.5 * smooth(t / 1.2)
    out = np.clip((out - 0.5) * (1 + 0.06 * g) + 0.5, 0, 1)
    s = 1.0 + 0.055 * eio(t / 4.9)
    M = np.float32([[s, 0, 960 * (1 - s)], [0, s, 380 * (1 - s)]])
    out = cv2.warpAffine(out, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return vignette(out, 0.22)

_hz = np.zeros((H, W), np.float32)
cv2.ellipse(_hz, (1560, 500), (430, 210), 0, 0, 360, 1.0, -1)
HAZE = (cv2.GaussianBlur(_hz, (0, 0), 90) * 0.78)[:, :, None]
BGDARK = np.clip(1.15 - np.linspace(0, 1, H, dtype=np.float32)[:, None, None] * 0.6, 0, 1)
_vig = None
def vignette(img, k):
    global _vig
    if _vig is None:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); d = np.sqrt(((xx - 960) / 960) ** 2 + ((yy - 540) / 540) ** 2)
        _vig = np.clip(d - 0.55, 0, 1)[:, :, None] ** 1.5
    return img * (1 - k * _vig)

# ================================================= PART 2 (glass UI in perspective)
CW, CH = 1580, 860           # UI canvas (wide panel to match the drawn perspective)
PX, PY, PW = 40, 40, 1500    # panel rect inside canvas (height animates)
PHF = 780
COLR = PX + 790               # right column x
SLOTS = [(PX + 140 + k * 334, PY + 290, 300, 300) for k in range(4)]            # phase A: big row
SLOTS_B = [(PX + 620 + k * 136, PY + 154, 120, 120) for k in range(4)]            # phase B: compact strip
MORPH = 8.0
REFS = [('Part 3 identity sheet.png', 'Identity'), ('Part 3 - costumes front.png', 'Wardrobe'),
        ('Part 3 - Location.png', 'Location'), ('Part 3 - Card.png', 'Relic')]
DROP = [6.0 + 0.48 * k for k in range(4)]
FLY = 0.46
ORIGIN = (330, 700)          # laptop screen, in frame coords
PROMPT = ('Cinematic live action, ARRI Alexa 65. @wanderer crosses the frozen cavern toward '
          '@relic, cold blue light shafts, drifting ice dust.')
TY0, TY1 = 8.75, 11.0
_thumbs = {}
def thumb(k, s=300, h=None):
    h = h or s; kk = (k, s, h)
    if kk not in _thumbs:
        a = (asset(REFS[k][0], s, h) * 255).astype(np.uint8); im = Image.fromarray(a).convert('RGBA')
        mk = Image.new('L', (s, h), 0); ImageDraw.Draw(mk).rounded_rectangle([0, 0, s - 1, h - 1], max(4, s // 10), fill=255); im.putalpha(mk)
        _thumbs[kk] = im
    return _thumbs[kk]
def wrap(s, font, width):
    lines, cur = [], ''
    for w in s.split(' '):
        tst = (cur + ' ' + w).strip()
        if font.getlength(tst) > width and cur: lines.append(cur); cur = w
        else: cur = tst
    return lines + [cur]
PF = F('R', 46); PFB = F('B', 46)
PLINES = wrap(PROMPT, PF, 1110)

def cursor(d, x, y, a, press=0.0, s=1.25):
    s = s * (1.0 - 0.12 * press)
    pts = [(0, 0), (0, 34), (9, 26), (15, 40), (21, 37), (15, 24), (27, 24)]
    P = [(x + px * s, y + py * s) for px, py in pts]
    d.polygon([(px + 2, py + 3) for px, py in P], fill=(0, 0, 0, int(80 * a)))
    d.polygon(P, fill=(255, 255, 255, int(255 * a)), outline=(20, 20, 20, int(255 * a)))

def sparkle_shape(d, cx, cy, r, col):
    pts = []
    for k in range(8):
        ang = k * math.pi / 4; rr = r if k % 2 == 0 else r * 0.32
        pts.append((cx + rr * math.sin(ang), cy - rr * math.cos(ang)))
    d.polygon(pts, fill=col)

def panel_h(t):
    return 190 + (PHF - 190) * eio((t - 5.45) / 0.45)

def grad_img(w, h, r, a, dark=0.0):
    mk = Image.new('L', (w, h), 0); ImageDraw.Draw(mk).rounded_rectangle([0, 0, w - 1, h - 1], r, fill=255)
    xs = np.linspace(0, 1, w)[None, :, None]
    gc = (np.array(PINK) * (1 - xs) + np.array(CLAY) * xs) * np.ones((h, 1, 1)) * (1 - dark)
    return Image.fromarray(np.dstack([gc, np.asarray(mk)[:, :, None] * a]).astype(np.uint8), 'RGBA')

def ui_canvas(t):
    ui = Image.new('RGBA', (CW, CH), (0, 0, 0, 0)); d = ImageDraw.Draw(ui)
    pa = eo((t - 5.18) / 0.45)
    if pa <= 0: return ui, pa
    PH = panel_h(t)
    A = lambda a: int(255 * a * pa)
    d.rounded_rectangle([PX, PY, PX + PW, PY + PH], 44, outline=(255, 255, 255, A(0.35)), width=3)
    d.rounded_rectangle([PX + 3, PY + 3, PX + PW - 3, PY + 130], 42, fill=(255, 255, 255, A(0.05)))
    hx, hy = PX + 110, PY + 34
    d.rounded_rectangle([hx, hy, hx + 72, hy + 72], 20, fill=(255, 255, 255, A(0.12)))
    for k, hh in enumerate((22, 38, 28, 46)):
        d.rounded_rectangle([hx + 14 + k * 12, hy + 57 - hh, hx + 21 + k * 12, hy + 57], 3, fill=(PINK if k == 3 else (235, 200, 190)) + (A(1),))
    d.text((hx + 96, hy - 4), 'Model', font=F('M', 30), fill=LSOFT + (A(1),))
    d.text((hx + 96, hy + 26), 'Seedance 2.5', font=F('B', 52), fill=WHITE + (A(1),))
    d.line([(PX + PW - 70, hy + 20), (PX + PW - 54, hy + 36), (PX + PW - 70, hy + 52)], fill=WHITE + (A(0.6),), width=5)
    ra = eo((t - 5.6) / 0.4)
    if ra > 0:
        RA = lambda a: int(255 * a * pa * ra)
        mA = eio((t - MORPH) / 0.3)                 # phase A -> B
        d.line([(PX + 36, PY + 140), (PX + PW - 36, PY + 140)], fill=(255, 255, 255, RA(0.18)), width=2)
        if mA < 1:
            ta = 1 - mA
            d.text((PX + 140, PY + 190 - 20 * mA), 'Visual references', font=F('B', 44), fill=WHITE + (RA(ta),))
            n_in = sum(1 for k in range(4) if t > DROP[k] + FLY)
            d.text((PX + PW - 110, PY + 198 - 20 * mA), f'{n_in} of 4 added', font=F('M', 34), fill=LSOFT + (RA(ta),), anchor='ra')
            box = [PX + 116, PY + 266, PX + 140 + 3 * 334 + 324, PY + 614]
            d.rounded_rectangle(box, 32, fill=(255, 255, 255, RA(0.05 * ta)))
            gm = Image.new('L', (CW, CH), 0); ImageDraw.Draw(gm).rounded_rectangle(box, 32, outline=255, width=4)
            xs = np.linspace(0, 1, CW)[None, :, None]
            gcol = (np.array(PINK) * (1 - xs) + np.array(CLAY) * xs) * np.ones((CH, 1, 1))
            ui.alpha_composite(Image.fromarray(np.dstack([gcol, np.asarray(gm)[:, :, None] * ra * pa * 0.95 * ta]).astype(np.uint8), 'RGBA'))
        lb = eo((t - MORPH - 0.3) / 0.3)
        if lb > 0:
            d.text((PX + 620 + 4 * 136 + 14, PY + 214), '4 references', font=F('B', 34), fill=WHITE + (RA(lb),), anchor='lm')
        for k, (x, y, w, h) in enumerate(SLOTS):
            u = (t - DROP[k]) / FLY
            if u < 1:
                for xx in range(x, x + w, 16):
                    d.line([(xx, y), (min(xx + 8, x + w), y)], fill=SOFT + (RA(0.6),), width=2); d.line([(xx, y + h), (min(xx + 8, x + w), y + h)], fill=SOFT + (RA(0.6),), width=2)
                for yy in range(y, y + h, 16):
                    d.line([(x, yy), (x, min(yy + 8, y + h))], fill=SOFT + (RA(0.6),), width=2); d.line([(x + w, yy), (x + w, min(yy + 8, y + h))], fill=SOFT + (RA(0.6),), width=2)
                d.text((x + w / 2, y + h / 2), '+', font=F('M', 64), fill=SOFT + (RA(0.65),), anchor='mm')
            else:
                mk = eio((t - MORPH - 0.05 * k) / 0.45)
                bx, by, bw, bh = SLOTS_B[k]
                X = x + (bx - x) * mk; Y = y + (by - y) * mk; Wd = w + (bw - w) * mk
                bnc = 1 + 0.07 * math.sin(math.pi * cl((u - 1) / 0.6)) if u < 1.6 else 1.0
                sw = max(8, int(Wd * bnc)); paste(ui, thumb(k, sw), X + (Wd - sw) / 2, Y + (Wd - sw) / 2, pa)
    qa = eo((t - 8.4) / 0.4)
    if qa > 0:
        QA = lambda a: int(255 * a * pa * qa); rz = (1 - qa) * 40
        d.text((PX + 170, PY + 296 + rz), 'Describe your video', font=F('B', 44), fill=WHITE + (QA(1),))
        pb = [PX + 170, PY + 356 + rz, PX + PW - 90, PY + 650 + rz]
        d.rounded_rectangle(pb, 28, fill=(255, 255, 255, QA(0.07)), outline=(255, 255, 255, QA(0.28)), width=2)
        nch = int(len(PROMPT) * cl((t - TY0) / (TY1 - TY0)))
        shown = 0; ly = pb[1] + 30; lines_drawn = []
        for ln in PLINES:
            if shown >= nch: break
            lines_drawn.append(ln[:nch - shown]); shown += len(ln) + 1
        cx, cy = pb[0] + 34, ly
        for li, ln in enumerate(lines_drawn):
            x = pb[0] + 34; y = ly + li * 66
            for wd in ln.split(' '):
                if not wd: continue
                if wd.startswith('@'):
                    tw = PFB.getlength(wd)
                    d.text((x, y), wd, font=PFB, fill=LPINK + (QA(1),)); x += tw + PF.getlength(' ')
                else:
                    d.text((x, y), wd, font=PF, fill=WHITE + (QA(0.95),)); x += PF.getlength(wd + ' ')
            cx, cy = x - PF.getlength(' '), y
        if (t * 2.2) % 1 < 0.6 or TY0 < t < TY1:
            d.rectangle([cx + 4, cy + 8, cx + 8, cy + 58], fill=WHITE + (QA(0.9),))
        press = cl(1 - abs(t - 11.3) / 0.12)
        bx0, by0, bx1, by1 = PX + PW - 110 - 360, PY + 672 + rz, PX + PW - 110, PY + 748 + rz
        bx0, by0, bx1, by1 = int(bx0), int(by0), int(bx1), int(by1)
        ui.alpha_composite(grad_img(bx1 - bx0, by1 - by0, 38, qa * pa, 0.12 * press), (bx0, by0))
        sparkle_shape(d, bx0 + 64, (by0 + by1) / 2, 19, (255, 255, 255, QA(1)))
        d.text((bx0 + 98, (by0 + by1) / 2), 'Generate', font=F('B', 40), fill=(255, 255, 255, QA(1)), anchor='lm')
        rp = (t - 11.3) / 0.5
        if 0 < rp < 1:
            r = 40 * eo(rp)
            d.rounded_rectangle([bx0 - r, by0 - r, bx1 + r, by1 + r], 38 + r, outline=CLAY + (int(220 * (1 - rp) * pa),), width=3)
        if 10.95 < t < 11.7:
            ca = cl((t - 10.95) / 0.15) * (1 - cl((t - 11.5) / 0.2))
            u = eo((t - 10.95) / 0.3); bx, by = bx0 + 210, by0 + 40
            cursor(d, bx + 160 * (1 - u), by + 90 * (1 - u), ca * pa, cl(1 - abs(t - 11.3) / 0.1), 1.7)
    return ui, pa

DRAWN = np.float32([(705.6, 58.8), (1812.5, 50.9), (1805.7, 787.0), (718.0, 554.0)])   # your hand-drawn outline
_HP = cv2.getPerspectiveTransform(np.float32([[PX, PY], [PX + PW, PY], [PX + PW, PY + PHF], [PX, PY + PHF]]), DRAWN)
_CQ = cv2.perspectiveTransform(np.float32([[[0, 0], [CW, 0], [CW, CH], [0, CH]]]), _HP)[0]
def part2_ui_quad(t):
    pa = eo((t - 5.18) / 0.45)
    c = _CQ.mean(0); s = 0.92 + 0.08 * pa
    q = (_CQ - c) * s + c + np.float32([40 * (1 - pa), 6 * math.sin(t * 1.25)])
    return [tuple(p) for p in q]

def part2(t, with_ui=True):
    src = 0.35 + (t - T1)
    base = src24('p2', src).copy(); plate = base.copy()
    if not with_ui: return base
    ui, pa = ui_canvas(t)
    if pa <= 0: return base
    q = part2_ui_quad(t)
    shape = Image.new('L', (CW, CH), 0); ImageDraw.Draw(shape).rounded_rectangle([PX, PY, PX + PW, PY + panel_h(t)], 44, fill=255)
    shape = np.asarray(shape).astype(np.float32) / 255
    Mg = np.zeros((H, W, 3), np.float32); warp_rgba(Mg, np.dstack([np.ones((CH, CW, 3), np.float32), shape[:, :, None]]), q)
    Ms = Mg[:, :, :1]
    shadow = cv2.GaussianBlur(np.roll(np.roll(Ms, 26, 0), 10, 1), (0, 0), 26)[:, :, None]
    base = base * (1 - 0.30 * shadow * pa)
    blur = cv2.GaussianBlur(base, (0, 0), 20)
    glass = np.clip(blur * 0.36 + np.array([0.03, 0.035, 0.05], np.float32), 0, 1)
    base = base * (1 - Ms * pa * 0.96) + glass * Ms * pa * 0.96
    U = np.asarray(ui).astype(np.float32) / 255
    U[:, :, 3] *= np.clip(cv2.dilate(shape, np.ones((7, 7), np.uint8)), 0, 1)
    warp_rgba(base, U, q)
    mi = min(max(int(round(src * 24)) + 1, 1), 185)
    fm = cv2.imread(f'matte2/{mi:04d}.png', 0).astype(np.float32)[:, :, None] / 255
    base = base * (1 - fm) + plate * fm
    # reference images flying from the laptop into their slots (screen space)
    Hm = cv2.getPerspectiveTransform(np.float32([[0, 0], [CW, 0], [CW, CH], [0, CH]]), np.float32(q))
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); any_ = False
    for k, (x, y, w, h) in enumerate(SLOTS):
        u = (t - DROP[k]) / FLY
        if not (0 < u < 1): continue
        any_ = True
        pts = cv2.perspectiveTransform(np.float32([[[x, y], [x + w, y], [x + w, y + h], [x, y + h]]]), Hm)[0]
        tc = pts.mean(0); ts = float(np.linalg.norm(pts[1] - pts[0]))
        e = eio(u); cx = ORIGIN[0] + (tc[0] - ORIGIN[0]) * e; cy = ORIGIN[1] + (tc[1] - ORIGIN[1]) * e + math.sin(math.pi * u) * 70
        size = int(70 + (ts - 70) * eo(u) + 30 * math.sin(math.pi * u))
        im = thumb(k, max(size, 8)).rotate(-10 * (1 - e), Image.BICUBIC, expand=True)
        im = shadowed(im, (0, 14), 16, 0.4)
        paste(lay, im, cx - im.size[0] / 2, cy - im.size[1] / 2, cl(u * 5))
        cursor(d, cx + size * 0.28, cy + size * 0.25, cl(u * 5) * cl((1 - u) * 6))
        # spark at the laptop as it leaves
        if u < 0.35:
            g = 1 - u / 0.35; d.ellipse([ORIGIN[0] - 40 * g, ORIGIN[1] - 40 * g, ORIGIN[0] + 40 * g, ORIGIN[1] + 40 * g], outline=CLAY + (int(200 * g),), width=3)
    if any_: base = composite(base, lay)
    return base

# ================================================= PART 3 (grid, asset generation -> video)
A3 = [('refs/frame53_crop.png', 'Real photo'), ('Part 3 identity sheet.png', 'Character'), ('Part 3 - costumes front.png', 'Wardrobe'),
      ('Part 3 - Card.png', 'Prop'), ('Part 3 - Location.png', 'Location')]
G3 = [11.98, 12.20, 12.50, 12.80, 13.06]
CWD, CHT = 330, 186
ROWX = [67 + k * (CWD + 34) for k in range(5)]; ROWY = 390
TOPW, TOPH = 250, 141
TOP = [(int((1920 - (5 * TOPW + 4 * 30)) / 2) + k * (TOPW + 30), 34, TOPW, TOPH) for k in range(5)]
VC = (475, 342, 970, 416)          # video card x,y,w,h (p3 aspect 2.33)
CONV0, CONV1 = 13.40, 13.85

def chip(ui, text, cx, y, a, dark=False, font=None):
    font = font or F('M', 28); tw = font.getlength(text); w = tw + 40; h = 50
    im = Image.new('RGBA', (int(w) + 30, h + 30), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([15, 15, 15 + w, 15 + h], 25, fill=(CLAY if dark else WHITE) + (240,), width=1)
    d.text((15 + w / 2, 15 + h / 2), text, font=font, fill=INK + (255,), anchor='mm')
    im = shadowed(im, (0, 6), 10, 0.18)
    paste(ui, im, cx - w / 2 - 15, y - 15, a)

def p3_video(t):
    sz = (VC[2], VC[3])
    if t < 15.1: return src24('p3', 3.0 + (t - 14.1), sz)
    return src24('p3', 6.0 + (t - 15.1), sz)

def bez(p0, p1, p2, u):
    return ((1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * p1[0] + u * u * p2[0], (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * p1[1] + u * u * p2[1])

def loading_card(base, ui, img, x, y, t0, t, dur, a=1.0):
    """dark placeholder -> video loads top-to-bottom behind a progress bar"""
    h, w = img.shape[:2]; x, y = int(x), int(y)
    pa = eo((t - t0) / 0.12) * a
    prog = eio((t - t0 - 0.08) / dur)
    ph = np.full((h, w, 3), np.array((22, 25, 32), np.float32) / 255)
    base = place(base, ph, x, y, r=26, a=pa, shadow=0.3 * pa)
    if prog > 0:
        edge = h * prog; yy = np.arange(h, dtype=np.float32)[:, None, None]
        m = np.clip((edge - yy) / 10, 0, 1) * np.ones((1, w, 1), np.float32)
        base = place(base, img, x, y, m, r=26, a=a, shadow=0, border=0.45 * prog)
    d = ImageDraw.Draw(ui)
    if 0 < prog < 1:
        ey = y + h * prog
        d.line([(x + 6, ey), (x + w - 6, ey)], fill=CLAY + (int(230 * a),), width=3)
    ba = pa * (1 - cl((t - t0 - 0.08 - dur) / 0.2))
    if ba > 0:
        bw = int(w * 0.46); bx = x + (w - bw) / 2; by = y + h - 70
        lab = f'Generating video  {int(round(prog * 100))}%'
        d.rounded_rectangle([bx - 28, by - 72, bx + bw + 28, by + 34], 22, fill=(14, 16, 22, int(185 * ba)))
        im = text_img(lab, F('B', 30), WHITE); paste(ui, shadowed(im, (0, 3), 6, 0.8), bx - 24, by - 60 - 24, ba)
        d.rounded_rectangle([bx, by, bx + bw, by + 12], 6, fill=(255, 255, 255, int(60 * ba)))
        if prog > 0: d.rounded_rectangle([bx, by, bx + max(12, bw * prog), by + 12], 6, fill=CLAY + (int(255 * ba),))
    return base

def part3(t, ui=None, out_a=1.0, dy=0.0):
    base = GRID.copy(); own = ui is None
    if own: ui = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ui)
    cu = eio((t - CONV0) / (CONV1 - CONV0))
    for k, (path, lab) in enumerate(A3):
        p = (t - G3[k]) / 0.42
        if p <= 0: continue
        img = asset(path, CWD, CHT); rgb, al = gen_card(img, p, seed=k + 3)
        pop = 0.9 + 0.1 * eob(p * 1.4, 1.4)
        x0, y0 = ROWX[k], ROWY; tx, ty, tw, th = TOP[k]
        w = CWD + (tw - CWD) * cu; h = CHT + (th - CHT) * cu
        x = x0 + (tx - x0) * cu; y = y0 + (ty - y0) * cu + dy
        cw_, ch_ = max(2, int(w * pop)), max(2, int(h * pop))
        r = cv2.resize(rgb, (cw_, ch_), interpolation=cv2.INTER_AREA); ra = cv2.resize(al, (cw_, ch_))[:, :, None]
        place(base, r, x + (w - cw_) / 2, y + (h - ch_) / 2, ra, r=int(18 * w / CWD), a=out_a, shadow=0.25 * cl(p) ** 3)
        la = cl((p - 0.6) / 0.4) * out_a
        if la > 0:
            ly = ROWY + CHT + 22 + (TOP[k][1] + TOPH + 14 - (ROWY + CHT + 22)) * cu + dy
            chip(ui, lab, x + w / 2, ly, la * (1 - 0.35 * cu), dark=(k == 0), font=F('M', int(28 - 4 * cu)))
    # caption 1
    c1 = 1 - cl((t - 13.30) / 0.2)
    if t < 13.6: caption(ui, [('Design', WHITE, 12.14), ('your', WHITE, 12.54), ('AI', CLAY, 12.83), ('world', CLAY, 12.97)], F("B", 72), 960, 690, t, c1 * out_a)
    # arrows from every asset down into the video
    vx, vy, vw, vh = VC
    ga = cl((t - 13.80) / 0.35)
    la = ga * (1 - cl((t - 15.6) / 0.4)) * out_a
    if la > 0:
        ui_main = ui; ui = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ui)
        for k, (tx, ty, tw, th) in enumerate(TOP):
            p0 = (tx + tw / 2, ty + th + 62 + dy); p2 = (vx + vw * (0.14 + 0.18 * k), vy - 10 + dy)
            p1 = (p0[0] + (p2[0] - p0[0]) * 0.15, p0[1] + (p2[1] - p0[1]) * 0.75)
            n = 40; grow = eo(ga)
            pts = [bez(p0, p1, p2, j / n * grow) for j in range(n + 1)]
            d.line(pts, fill=CLAY + (int(235 * la),), width=5, joint='curve')
            if grow > 0.97:
                e = pts[-1]; b_ = pts[-3]; ux, uy = e[0] - b_[0], e[1] - b_[1]; L = math.hypot(ux, uy) or 1; ux, uy = ux / L, uy / L
                d.polygon([(e[0] + ux * 6, e[1] + uy * 6), (e[0] - ux * 22 - uy * 14, e[1] - uy * 22 + ux * 14), (e[0] - ux * 22 + uy * 14, e[1] - uy * 22 - ux * 14)], fill=CLAY + (int(255 * la),))
                f = ((t - 14.1) * 1.3 + k * 0.2) % 1
                c = bez(p0, p1, p2, f)
                d.ellipse([c[0] - 7, c[1] - 7, c[0] + 7, c[1] + 7], fill=CLAY + (int(255 * la),), outline=WHITE + (int(255 * la),), width=2)
        ui_main.alpha_composite(shadowed(shadowed(ui, (0, 3), 5, 0.75), (0, 0), 2, 0.5)); ui = ui_main; d = ImageDraw.Draw(ui)
    # video card generating then playing
    vp = (t - 14.0) / 0.5
    if vp > 0:
        img = p3_video(max(t, 14.1))
        base = loading_card(base, ui, img, vx, vy + dy, 14.0, t, 0.5, out_a)
    # caption 2 (centre, under the video)
    c2 = 1 - cl((t - 15.95) / 0.3)
    if t > 13.5: caption(ui, [('Preserve', WHITE, 13.68), ('visual', CLAY, 14.13), ('consistency', CLAY, 14.47)], F('B', 72), 960, 800 + dy, t, c2 * out_a)
    if own: return composite(base, ui)
    return base

# ================================================= PART 4 (4-step list on the left, stage on the right)
STEPS = ['Ideation', 'Asset generation', 'Video animation', 'Post-production']
SA = [16.90, 17.85, 18.90, 19.95]; DONE_END = 21.55
LX, LW, LH, LY0, LGAP = 70, 600, 150, 215, 180
IDEA = 'A lone wanderer guards a golden relic in a frozen cavern, until a chrome assassin arrives.'
SCX = 1300                                   # stage centre x
VID4 = (735, 300, 1130, 485)
MON = (1000, 215, 600, 258)
TL = (730, 505, 1140, 390)

def step_state(k, t):
    if t < SA[k]: return 0
    nxt = SA[k + 1] if k < 3 else DONE_END
    return 1 if t < nxt else 2

def active_pos(t):
    """continuous index of the highlighted step (slides between rows)"""
    p = 0.0
    for k in range(1, 4): p += eio((t - SA[k]) / 0.4)
    return p

def mix(c0, c1, u): return tuple(int(a + (b - a) * u) for a, b in zip(c0, c1))

def steplist(ui, t):
    d = ImageDraw.Draw(ui)
    ha = eo((t - 16.55) / 0.4)
    if ha > 0:
        paste(ui, text_img('The 4-step process', F('B', 58), WHITE), LX - 24, LY0 - 120 - 24 + (1 - ha) * 30, ha)
    ap = active_pos(t); hl_on = eo((t - SA[0]) / 0.3) * (1 - eo((t - DONE_END) / 0.4))
    rows = []
    for k in range(4):
        u = (t - (16.62 + 0.09 * k)) / 0.45
        rows.append((u, cl(u * 2), LX - (1 - eo(u)) * 60, LY0 + k * LGAP))
    # connector line
    cxl = LX + 70
    if rows[0][0] > 0:
        y0 = LY0 + LH / 2; y1 = LY0 + 3 * LGAP + LH / 2; la = rows[3][1]
        d.line([(cxl, y0), (cxl, y1)], fill=(80, 86, 98, int(255 * la)), width=5)
        yp = y0 + (y1 - y0) * cl(ap / 3) * (1 if t >= SA[0] else 0)
        if t >= SA[0]: d.line([(cxl, y0), (cxl, yp)], fill=CLAY + (255,), width=6)
    # base cards
    for k, (u, a, x, y) in enumerate(rows):
        if u <= 0: continue
        im = Image.new('RGBA', (LW + 60, LH + 50), (0, 0, 0, 0)); ImageDraw.Draw(im).rounded_rectangle([20, 20, 20 + LW, 20 + LH], 34, fill=(255, 255, 255, 16), outline=(255, 255, 255, 50), width=2)
        paste(ui, im, x - 20, y - 20, a)
    # sliding highlight
    if hl_on > 0:
        hy = LY0 + ap * LGAP; grow = 1 + 0.03 * math.sin(math.pi * cl((ap % 1)))
        im = Image.new('RGBA', (LW + 80, LH + 60), (0, 0, 0, 0)); ImageDraw.Draw(im).rounded_rectangle([20, 20, 20 + LW + 20, 20 + LH], 34, fill=WHITE + (255,))
        paste(ui, shadowed(im, (0, 12), 18, 0.5), LX - 30, hy - 20, hl_on)
    for k, (u, a, x, y) in enumerate(rows):
        if u <= 0: continue
        on = cl(1 - abs(ap - k)) * hl_on if t >= SA[0] else 0.0
        st = step_state(k, t)
        cx, cy = x + 70, y + LH / 2
        if st == 2 and on < 0.5:
            ic = glow_icon('check', 64).resize((150, 150), Image.LANCZOS); paste(ui, ic, cx - 75, cy - 75, a)
        else:
            r = 38 + 6 * on
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=mix((52, 58, 70), CLAY, on) + (int(255 * a),))
            d.text((cx, cy + 1), str(k + 1), font=F('B', 40), fill=mix(WHITE, INK, on) + (int(255 * a),), anchor='mm')
        tc = mix(WHITE if st == 2 else (140, 146, 158), INK, on)
        d.text((x + 135, cy - 22), f'STEP {k + 1}', font=F('M', 24), fill=mix((140, 146, 158), (0, 150, 76), on) + (int(255 * a),), anchor='lm')
        d.text((x + 135, cy + 20), STEPS[k], font=F('B', 46), fill=tc + (int(255 * a),), anchor='lm')

def stage_header(ui, t):
    """big 'STEP N  name' title above the stage that swaps on each step change"""
    for k in range(4):
        t_in = SA[k]; t_out = SA[k + 1] if k < 3 else 99
        u = (t - t_in - (0.16 if k else 0)) / 0.4; v = (t - t_out + 0.02) / 0.18
        if u <= 0 or v >= 1: continue
        a = cl(u * 2) * (1 - cl(v)); dy = (1 - eo(u)) * 40 - eio(v) * 40
        y = 78 + dy
        pl = shadowed(pill(f'STEP {k + 1}', F('B', 30), fill=CLAY, text_col=INK, h=56, pad=22), (0, 3), 6, 0.3)
        paste(ui, pl, 735, y + 8, a)
        tim = text_img(STEPS[k], F('B', 66), WHITE)
        paste(ui, tim, 735 + pl.size[0] + 18 - 24, y - 24 - 12, a)

def idea_card(t):
    w, h = 900, 360; im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], 30, fill=(30, 34, 44, 245))
    d.ellipse([44, 46, 62, 64], fill=CLAY + (255,)); d.text((78, 55), 'Film idea', font=F('B', 32), fill=WHITE + (255,), anchor='lm')
    d.line([(44, 100), (w - 44, 100)], fill=(255, 255, 255, 40), width=2)
    n = int(len(IDEA) * cl((t - 17.0) / 0.8)); f = F('I', 50)
    lines = wrap(IDEA[:n], f, w - 100) if n else ['']
    y = 128
    for ln in lines: d.text((48, y), ln, font=f, fill=WHITE + (255,)); y += 66
    if (t * 2.2) % 1 < 0.6 or t < 17.8:
        lx = 48 + f.getlength(lines[-1]); d.rectangle([lx + 4, y - 58, lx + 8, y - 8], fill=CLAY + (255,))
    return np.asarray(im).astype(np.float32) / 255

def p4_video(t, size):
    return src24('p4', 1.0 + max(0.0, t - 19.15), size)   # p4 frames start at source 4.0s -> plays from 5.0s

def lerp(a, b, u): return tuple(x + (y - x) * u for x, y in zip(a, b))

TLCLIPS = [  # track, start, len (0..1 of width), source time or 'aud'
    (0, 0.00, 0.20, 1.2), (0, 0.205, 0.17, 3.5), (0, 0.38, 0.24, 5.2), (0, 0.625, 0.18, 7.4), (0, 0.81, 0.19, 9.4),
    (2, 0.00, 0.62, 'aud'), (2, 0.625, 0.375, 'aud')]
def timeline(base, ui, t, a):
    x0, y0, w, h = TL
    base = place(base, np.full((h, w, 3), np.array((24, 27, 34), np.float32) / 255), x0, y0, r=26, a=a, shadow=0.3)
    d = ImageDraw.Draw(ui); A = lambda k: int(255 * k * a)
    lx = x0 + 110; lw = w - 140
    # ruler
    for k in range(0, 41):
        xx = lx + lw * k / 40; big = k % 5 == 0
        d.line([(xx, y0 + 26), (xx, y0 + (50 if big else 40))], fill=(255, 255, 255, A(0.45 if big else 0.25)), width=2)
        if big: d.text((xx + 5, y0 + 18), f'00:{k // 5 * 4:02d}', font=F('R', 18), fill=(255, 255, 255, A(0.5)))
    rows = [(y0 + 80, 76, 'V2'), (y0 + 170, 96, 'V1'), (y0 + 280, 76, 'A1')]
    rows = [(y0 + 84, 128, 'V1'), (y0 + 246, 90, 'A1')]
    for (ry, rh, nm) in rows:
        d.rounded_rectangle([x0 + 22, ry, x0 + 86, ry + rh], 12, fill=(255, 255, 255, A(0.08)))
        d.text((x0 + 54, ry + rh / 2), nm, font=F('B', 22), fill=(255, 255, 255, A(0.7)), anchor='mm')
        d.line([(lx, ry + rh + 6), (lx + lw, ry + rh + 6)], fill=(255, 255, 255, A(0.06)), width=1)
    ui_main = ui; ui = Image.new('RGBA', ui_main.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ui)
    order = [0, 1, 5, 2, 3, 4, 6]
    trackmap = {0: 0, 2: 1}
    for oi, ci in enumerate(order):
        tr, st, ln, src = TLCLIPS[ci]
        u = (t - (20.12 + 0.1 * oi)) / 0.35
        if u <= 0: continue
        ry, rh, _ = rows[trackmap[tr]]
        cx = lx + lw * st + (1 - eo(u)) * 260; cw = lw * ln - 4
        aa = cl(u * 2) * a
        if src == 'aud':
            d.rounded_rectangle([cx, ry, cx + cw, ry + rh], 10, fill=AUDIO + (int(255 * aa * 0.95),))
            rng = np.random.default_rng(ci)
            for xx in np.arange(cx + 8, cx + cw - 8, 7):
                hh = (0.25 + 0.75 * abs(math.sin(xx * 0.05 + ci)) * rng.random()) * (rh - 20) / 2
                d.line([(xx, ry + rh / 2 - hh), (xx, ry + rh / 2 + hh)], fill=(235, 255, 238, int(220 * aa)), width=3)
        elif src in ('Mask', 'Color grade'):
            d.rounded_rectangle([cx, ry, cx + cw, ry + rh], 10, fill=SKY + (int(240 * aa),))
            d.text((cx + 16, ry + rh / 2), src, font=F('B', 24), fill=WHITE + (int(255 * aa),), anchor='lm')
        else:
            tw = max(4, int(cw)); strip = np.zeros((rh, tw, 3), np.float32)
            fr = src24('p4', src, (int(rh * 2.33), rh)) if False else cover(frame('p4', int(src * 24) + 1), int(rh * 2.33), rh)
            for xx in range(0, tw, fr.shape[1]): strip[:, xx:xx + fr.shape[1]] = fr[:, :min(fr.shape[1], tw - xx)]
            sim = Image.fromarray((strip * 255).astype(np.uint8)).convert('RGBA')
            mk = Image.new('L', sim.size, 0); ImageDraw.Draw(mk).rounded_rectangle([0, 0, tw - 1, rh - 1], 10, fill=int(255 * aa)); sim.putalpha(mk)
            ui.alpha_composite(sim, (int(cx), int(ry)))
            d.rounded_rectangle([cx, ry, cx + cw, ry + rh], 10, outline=(255, 255, 255, int(150 * aa)), width=2)
    cm = Image.new('L', ui.size, 0); ImageDraw.Draw(cm).rectangle([lx - 2, y0, lx + lw + 2, y0 + h], fill=255)
    arr = np.array(ui); arr[:, :, 3] = (arr[:, :, 3].astype(np.float32) * np.asarray(cm) / 255).astype(np.uint8)
    ui_main.alpha_composite(Image.fromarray(arr)); ui = ui_main; d = ImageDraw.Draw(ui)
    # blade cut flash on V1 at 21.05
    cf = 1 - abs(t - 21.05) / 0.15
    if cf > 0:
        cxp = lx + lw * 0.5; d.line([(cxp, y0 + 70), (cxp, y0 + 350)], fill=(255, 255, 255, A(cf)), width=4)
    # playhead
    pu = cl((t - 20.35) / 1.6)
    if t > 20.3:
        px = lx + lw * (0.04 + 0.6 * eio(pu))
        d.line([(px, y0 + 20), (px, y0 + h - 18)], fill=CLAY + (A(1),), width=4)
        d.polygon([(px - 12, y0 + 14), (px + 12, y0 + 14), (px, y0 + 32)], fill=CLAY + (A(1),))
    return base

def part4(t):
    ui = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ex = eio((t - T4) / 0.4)
    if ex < 1: base = part3(t, ui, out_a=1 - ex, dy=-80 * ex)
    else: base = GRID.copy()
    # step 1: idea card
    ia = eo((t - 16.9) / 0.35)
    iout = eio((t - 17.85) / 0.35)
    if ia > 0 and iout < 1:
        card = idea_card(t)
        place(base, card[:, :, :3], SCX - 450, 360 - 80 * iout, card[:, :, 3:], r=30, a=ia * (1 - iout), shadow=0.25, scale=0.94 + 0.06 * ia)
    # step 2: assets generate side by side, step 3: they fly into the video
    fu = eio((t - 18.9) / 0.45)
    AS = [('Part 4 - Lightsaber.png', 'Lightsaber', 17.98, (SCX - 570, 330)), ('Part 4 - exoskeleton.png', 'Chrome assassin', 18.25, (SCX + 10, 330))]
    for j, (path, lab, g0, pos) in enumerate(AS):
        p = (t - g0) / 0.42
        if p <= 0 or fu >= 1: continue
        img = asset(path, 560, 315); rgb, al = gen_card(img, p, seed=20 + j)
        tgt = (SCX - 90, VID4[1] + VID4[3] / 2 - 25, 180, 101)
        x, y, w, h = lerp((pos[0], pos[1], 560, 315), tgt, fu)
        w, h = max(2, int(w)), max(2, int(h))
        if w != 560: rgb = cv2.resize(rgb, (w, h), interpolation=cv2.INTER_AREA); al = cv2.resize(al, (w, h))[:, :, None]
        place(base, rgb, x, y, al, r=max(8, int(22 * w / 560)), a=1 - cl((fu - 0.75) / 0.25), shadow=0.25 * cl(p) ** 3)
        la = cl((p - 0.6) / 0.4) * (1 - cl(fu * 4))
        if la > 0: chip(ui, lab, pos[0] + 280, pos[1] + 340, la)
    # step 3 video card, step 4 it moves up into a preview monitor
    vp = (t - 19.08) / 0.45
    if vp > 0:
        mv = eio((t - 19.95) / 0.5)
        vx, vy, vw, vh = lerp(VID4, MON, mv); vw, vh = int(vw), int(vh)
        img = p4_video(t, (vw, vh))
        base = loading_card(base, ui, img, vx, vy, 19.08, t, 0.45, 1.0)
    # step 4 timeline
    ta = eo((t - 20.02) / 0.4)
    if ta > 0:
        x0, y0, w, h = TL
        TLsave = TL
        globals()['TL'] = (x0, int(y0 + (1 - ta) * 60), w, h)
        base = timeline(base, ui, t, ta)
        globals()['TL'] = TLsave
    steplist(ui, t)
    stage_header(ui, t)
    return composite(base, ui)

# ================================================= main
def render(i):
    t = i / FPS
    if t < 4.85: return part1(t)
    if t < 5.05:                                   # smooth zoom-blend: frozen last clean head frame -> desk shot
        u = eio((t - 4.85) / 0.2)
        a = part1(min(t, 4.93)); M = cv2.getRotationMatrix2D((960, 420), 0, 1 + 0.06 * u)
        a = cv2.GaussianBlur(cv2.warpAffine(a, M, (W, H), borderMode=cv2.BORDER_REFLECT), (0, 0), 0.1 + 6 * u)
        b = part2(t); M = cv2.getRotationMatrix2D((960, 420), 0, 1.05 - 0.05 * u)
        b = cv2.warpAffine(b, M, (W, H), borderMode=cv2.BORDER_REFLECT)
        if u < 1: b = cv2.GaussianBlur(b, (0, 0), 0.1 + 6 * (1 - u))
        return a * (1 - u) + b * u
    if t < TX0: return part2(t)
    if t < TX1:
        u = eio((t - TX0) / (TX1 - TX0))
        a = part2(t); M = cv2.getRotationMatrix2D((960, 540), 0, 1 + 0.08 * u)
        a = cv2.warpAffine(a, M, (W, H), borderMode=cv2.BORDER_REFLECT)
        a = cv2.GaussianBlur(a, (0, 0), 0.1 + 10 * u)
        b = part3(t); M = cv2.getRotationMatrix2D((960, 540), 0, 1.05 - 0.05 * u)
        b = cv2.warpAffine(b, M, (W, H), borderMode=cv2.BORDER_REFLECT)
        return a * (1 - u) + b * u
    if t < T4: return part3(t)
    return part4(t)

if __name__ == '__main__':
    os.makedirs('out', exist_ok=True)
    if sys.argv[1] == 'test':
        ids = [int(x) for x in sys.argv[2:]]
        for i in ids: save_jpg(f'/tmp/claude-0/t_{i:04d}.jpg', render(i))
    else:
        a, b = int(sys.argv[1]), int(sys.argv[2])
        for i in range(a, min(b, NF)): save_jpg(f'out/{i:04d}.jpg', render(i))
        print('done', a, b, flush=True)
