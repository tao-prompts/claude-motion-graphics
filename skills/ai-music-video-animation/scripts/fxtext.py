# fxtext.py — painted lyric lettering with animated entrances (type, pixel-form, pop, write, wave) and exits.
import math
import numpy as np
import skia
from engine import *

import os
FD = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'fonts') + os.sep
TF = {
    'toon': skia.Typeface.MakeFromFile(FD + 'LuckiestGuy-Regular.ttf'),
    'marker': skia.Typeface.MakeFromFile(FD + 'PermanentMarker-Regular.ttf'),
    'mono': skia.Typeface.MakeFromFile(FD + 'SpaceMono-Bold.ttf'),
}
_GC = {}
def glyphs(text, face, size):
    """list of (char, path, advance) at origin; cached"""
    k = (text, face, size)
    if k in _GC: return _GC[k]
    f = skia.Font(TF[face], size)
    ids = f.textToGlyphs(text)
    ws = f.getWidths(ids)
    out = []
    for ch, g, w in zip(text, ids, ws):
        p = f.getPath(g)
        out.append((ch, p if p is not None else skia.Path(), w))
    _GC[k] = out
    return out

def text_width(text, face, size, track=0):
    return sum(w for _, _, w in glyphs(text, face, size)) + track * (len(text) - 1)

def _wobble_paint(col, w, a=255, seed=0):
    p = skia.Paint(AntiAlias=True, Color=hexc(col, a)); p.setStyle(skia.Paint.kStroke_Style); p.setStrokeWidth(w)
    p.setStrokeJoin(skia.Paint.kRound_Join)
    p.setPathEffect(skia.DiscretePathEffect.Make(10, 1.6, seed))
    return p

def paint_glyph(path, col, a=255, outline=INK, ow=6, hi='#FFFFFF', shadow=True, glowcol=None, key='g', tex=.5):
    c = CTX.canvas
    if path.isEmpty(): return
    seed = int(hash1(key) * 1000) + CTX.bi
    if glowcol:
        gp = skia.Paint(AntiAlias=True, Color=hexc(glowcol, int(120 * a / 255))); gp.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 14))
        gp.setBlendMode(skia.BlendMode.kPlus); c.drawPath(path, gp)
    if shadow:
        c.save(); c.translate(5, 7)
        sp = skia.Paint(AntiAlias=True, Color=hexc('#2E2530', int(110 * a / 255))); c.drawPath(path, sp)
        c.restore()
    # thick ink outline under the fill (gives a chunky cartoon rim)
    c.drawPath(path, _wobble_paint(outline, ow * 2, a, seed))
    fp = skia.Paint(AntiAlias=True, Color=hexc(col, a)); c.drawPath(path, fp)
    if tex > 0: c.drawPath(path, texpaint(int(hash1(key) * 4), tex * a / 255))
    if hi:
        c.save(); c.clipPath(path, doAntiAlias=True); c.translate(-3, -4)
        hp = skia.Paint(AntiAlias=True, Color=hexc(hi, int(70 * a / 255))); hp.setStyle(skia.Paint.kStroke_Style); hp.setStrokeWidth(5)
        c.drawPath(path, hp); c.restore()
    c.drawPath(path, _wobble_paint(outline, ow * .5, a, seed + 7))

def lettering(t, text, x, y, size, t0, t1=None, face='toon', cols=('#FF9A4A',), style='pop', out='pop', align='center',
              track=4, key='L', rot=0.0, glowcol=None, wave=0.0, outline=INK, beat=0.0, dur_in=None):
    """draw text at (x,y) baseline (screen or world space). t0 entrance start, t1 exit start."""
    if t < t0: return
    gl = glyphs(text, face, size)
    total = sum(w for _, _, w in gl) + track * (len(gl) - 1)
    x0 = x - total / 2 if align == 'center' else x
    n = len(gl)
    din = dur_in if dur_in else (.06 * n + .25)
    tout = .35
    c = CTX.canvas
    c.save(); c.translate(x, y); c.rotate(rot); c.translate(-x, -y)
    cx = x0
    for i, (ch, path, w) in enumerate(gl):
        lk = f'{key}{i}'
        col = cols[i % len(cols)]
        gx = cx; cx += w + track
        if ch == ' ': continue
        # entrance progress for this letter
        st = t0 + i * (din - .25) / max(1, n - 1) if style != 'type' else t0 + i * din / n
        k = seg(t, st, st + .25)
        ko = 0.0
        if t1 is not None:
            so = t1 + i * .03
            ko = seg(t, so, so + tout)
            if ko >= 1: continue
        if k <= 0: continue
        # per-letter transform
        b = path.getBounds(); lcx, lcy = gx + b.centerX(), y + b.centerY()
        dy = 0.0; sc = 1.0; rr = 0.0; a = 255
        if wave: dy += math.sin(t * 6 + i * .7) * wave
        if beat: dy -= abs(math.sin(math.pi * bp(t) + i * .35)) * beat
        if style == 'pop':
            sc = backOut(k, 2.6); dy -= (1 - easeOut(k)) * 60
        elif style == 'type':
            sc = 1.0 if k >= 1 else .3 + .7 * easeOut(k * 1.5)
        elif style == 'write':
            sc = 1.0
        elif style == 'drop':
            dy -= (1 - easeIn(k)) * 500; sc = 1.0
            if k >= 1: sq = math.exp(-10 * (t - st - .25)) * math.cos(25 * (t - st - .25)) * .25
            else: sq = 0
        elif style == 'pixel':
            # squares converge then the letter resolves
            _pixel_form(path, gx, y + dy, t, st, size, col, lk)
            if k < 1 and t < st + .5:
                kk = seg(t, st + .25, st + .5)
                if kk <= 0: continue
                a = int(255 * kk)
            sc = 1.0
        if out == 'pop' and ko > 0: sc *= 1 - easeIn(ko); a = int(a * (1 - ko))
        elif out == 'glitch' and ko > 0:
            _pixel_burst(path, gx, y + dy, ko, col, lk); a = int(a * (1 - min(1, ko * 3)))
        elif out == 'fly' and ko > 0: dy -= easeIn(ko) * 400; rr += ko * (i % 2 - .5)
        if a <= 0 or sc <= 0.01: continue
        c.save()
        c.translate(lcx, lcy + dy); c.rotate(math.degrees(rr) + (math.sin(t * 3 + i) * 2 if wave else 0)); c.scale(sc, sc); c.translate(-lcx, -lcy)
        c.translate(gx, y)
        if style == 'write' and k < 1:
            # reveal left->right like a marker stroke
            c.save(); c.clipRect(skia.Rect.MakeLTRB(b.left() - 10, b.top() - 20, b.left() + (b.width() + 20) * easeOut(k), b.bottom() + 20))
            paint_glyph(path, col, a, outline, max(3, size * .06), key=lk, glowcol=glowcol)
            c.restore()
        else:
            paint_glyph(path, col, a, outline, max(3, size * .06), key=lk, glowcol=glowcol)
        c.restore()
    # typing cursor
    if style == 'type' and t < t0 + din + .6 and (t1 is None or t < t1):
        typed = clamp((t - t0) / din)
        idx = min(n, int(typed * n + .999))
        cxp = x0 + sum(w + track for _, _, w in gl[:idx])
        if (t * 3) % 1 < .6:
            fill(rect(cxp + 4, y - size * .75, size * .12, size * .85), '#FFF6D8', key=key + 'cur', tex=0, edge=0, outline=3)
    c.restore()

_PTS = {}
def _glyph_points(path, n, key):
    k = (key, n)
    if k in _PTS: return _PTS[k]
    b = path.getBounds()
    r = np.random.default_rng(abs(hash(key)) % 9999)
    pts = []
    tries = 0
    while len(pts) < n and tries < n * 40:
        px, py = b.left() + r.random() * b.width(), b.top() + r.random() * b.height()
        if path.contains(px, py): pts.append((px, py))
        tries += 1
    _PTS[k] = pts
    return pts

def _pixel_form(path, gx, gy, t, st, size, col, key):
    k = seg(t, st - .15, st + .4)
    if k <= 0 or k >= 1: return
    pts = _glyph_points(path, 26, key)
    for j, (px, py) in enumerate(pts):
        kk = easeOut(clamp(k * 1.3 - hash1(key, j) * .3))
        a_ = hash1(key, 'a', j) * 2 * math.pi
        sx, sy = gx + px + math.cos(a_) * size * 1.6, gy + py + math.sin(a_) * size * 1.2
        x_, y_ = lerp(sx, gx + px, kk), lerp(sy, gy + py, kk)
        s = size * .13
        fill(rect(x_ - s / 2, y_ - s / 2, s, s), mix(col, '#FFFFFF', .3 * (j % 2)), key=f'{key}pf{j}', tex=0, edge=.2, amp=.2, outline=1.5,
             a=int(255 * (1 - clamp((k - .8) * 5))))

def _pixel_burst(path, gx, gy, k, col, key):
    pts = _glyph_points(path, 18, key)
    for j, (px, py) in enumerate(pts):
        a_ = hash1(key, 'b', j) * 2 * math.pi
        d = easeOut(k) * 120
        s = 12 * (1 - k)
        if s < 1: continue
        x_, y_ = gx + px + math.cos(a_) * d, gy + py + math.sin(a_) * d - k * 60
        fill(rect(x_ - s / 2, y_ - s / 2, s, s), col, key=f'{key}pb{j}', tex=0, edge=.2, amp=.2, outline=1.2, a=int(255 * (1 - k)))

def gen_bar(t, x, y, w, t0, t1, done_hold=.45, key='gen'):
    """'GENERATING' progress bar: glass pill, filling stripes, percent, then DONE pop"""
    if t < t0 or t > t1 + done_hold + .3: return
    kin = backOut(seg(t, t0, t0 + .2))
    kout = 1 - easeIn(seg(t, t1 + done_hold, t1 + done_hold + .3))
    s = kin * kout
    if s <= .02: return
    h = 54 * s; ww = w * s
    prog = clamp(seg(t, t0 + .15, t1) ** .8)
    glow(x, y, ww * .7, '#7DFFD8', .3)
    fill(rrect(x - ww / 2, y - h / 2, ww, h, h / 2), '#EFFFF8', key=key + 'bg', a=235, tex=.1, edge=.2, outline=3.5)
    iw = (ww - 16) * prog
    if iw > 6:
        fill(rrect(x - ww / 2 + 8, y - h / 2 + 8, iw, h - 16, (h - 16) / 2), '#3FCFB0' if prog < 1 else '#F2C14E', key=key + 'fl', tex=.2, edge=.2)
        c = CTX.canvas
        c.save(); c.clipRect(skia.Rect.MakeXYWH(x - ww / 2 + 8, y - h / 2 + 8, iw, h - 16))
        for q in range(int(ww / 26) + 3):
            sx = x - ww / 2 + q * 26 - ((t * 120) % 26)
            P = np.array([(sx, y + h / 2), (sx + 12, y + h / 2), (sx + 12 + h, y - h / 2), (sx + h, y - h / 2)])
            c.drawPath(topath(P), skia.Paint(AntiAlias=True, Color=hexc('#FFFFFF', 60)))
        c.restore()
    label = 'GENERATING' if prog < 1 else 'DONE!'
    pct = f'{int(prog * 100):d}%'
    lettering(t, label, x - ww / 2 + 10, y - h / 2 - 16, 34 * s, t0 - 1, face='mono', cols=('#2E6F62',) if prog < 1 else ('#E2692A',),
              style='type', dur_in=.01, align='left', track=2, key=key + ('L' if prog < 1 else 'D'), outline='#FFFFFF')
    lettering(t, pct, x + ww / 2 - 10 - text_width(pct, 'mono', 34 * s, 2), y - h / 2 - 16, 34 * s, t0 - 1, face='mono', cols=('#2E6F62',),
              style='type', dur_in=.01, align='left', track=2, key=key + 'P', outline='#FFFFFF')
    if prog >= 1:
        kk = seg(t, t1, t1 + .4)
        for q in range(8):
            a_ = q * math.pi / 4
            from chars import sparkle
            sparkle(x + math.cos(a_) * (ww * .55 + 60 * kk), y + math.sin(a_) * (h + 50 * kk), 20 * (1 - kk), f'{key}sp{q}', '#FFE07A')

# ================================================================ DIGITAL / CODE text (glowing terminal lettering)
GLYPHSET = '01<>/{}[]#$%&*+=?;:_'
def _glow_draw(path, col, a, glowr=14, core=True, outline=None):
    c = CTX.canvas
    for r_, al in ((glowr * 1.6, .35), (glowr * .6, .55)):
        gp = skia.Paint(AntiAlias=True, Color=hexc(col, int(255 * al * a / 255)))
        gp.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, r_)); gp.setBlendMode(skia.BlendMode.kPlus)
        c.drawPath(path, gp)
    if outline:
        op = skia.Paint(AntiAlias=True, Color=hexc(outline, int(a * .85))); op.setStyle(skia.Paint.kStroke_Style); op.setStrokeWidth(5)
        op.setStrokeJoin(skia.Paint.kRound_Join); c.drawPath(path, op)
    c.drawPath(path, skia.Paint(AntiAlias=True, Color=hexc(mix(col, '#FFFFFF', .3) if core else col, a)))

def code_text(t, text, x, y, size, t0, t1=None, cols=('#5FF2D0',), style='type', out='glitch', align='left', key='CT',
              panel=True, beat=0.0, wave=0.0, outline='#0E1530', scan=True, dur_in=None):
    """glowing monospace lettering. style: type | decode | pixel | flicker. out: glitch | delete | pop"""
    if t < t0: return
    gl = glyphs(text, 'mono', size)
    n = len(gl)
    total = sum(w for _, _, w in gl)
    x0 = x - total / 2 if align == 'center' else x
    din = dur_in if dur_in else min(1.0, .035 * n + .15)
    c = CTX.canvas
    if panel:
        pa = seg(t, t0 - .15, t0) * (1 - (seg(t, t1 + .2, t1 + .45) if t1 else 0))
        if pa > 0:
            pad = size * .45
            P = rrect(x0 - pad, y - size * 1.0 - size * .3, total + pad * 2, size * 1.65, 14)
            CTX.canvas.save(); CTX.canvas.translate(6, 8); CTX.canvas.drawPath(topath(P), skia.Paint(AntiAlias=True, Color=hexc('#2E2530', int(90 * pa)))); CTX.canvas.restore()
            CTX.canvas.drawPath(topath(P), skia.Paint(AntiAlias=True, Color=hexc('#0E1530', int(215 * pa))))
            CTX.canvas.drawPath(topath(rrect(x0 - pad, y - size * 1.3, total + pad * 2, size * .3, 14)), skia.Paint(AntiAlias=True, Color=hexc('#22305E', int(200 * pa))))
            for j_, cc_ in enumerate(('#E5675B', '#F2C14E', '#6CC57A')):
                CTX.canvas.drawCircle(x0 - pad + 18 + j_ * 18, y - size * 1.15, 5, skia.Paint(AntiAlias=True, Color=hexc(cc_, int(255 * pa))))
            from envs2 import gline
            gline(P, cols[0], 2, key=key + 'pn', a=.8 * pa, closed=True)
    cx = x0
    for i, (ch, path, w) in enumerate(gl):
        gx = cx; cx += w
        if ch == ' ': continue
        col = cols[i % len(cols)]
        st = t0 + din * i / max(1, n)
        if t < st: continue
        a = 255; dy = 0.0; dx = 0.0
        if beat: dy -= abs(math.sin(math.pi * bp(t) + i * .3)) * beat
        if wave: dy += math.sin(t * 7 + i * .6) * wave
        drawp = path
        if style == 'decode':
            res = st + .12 + .16 * hash1(key, 'r', i)
            if t < res:
                g = GLYPHSET[int(hash1(key, i, CTX.bi) * len(GLYPHSET))]
                drawp = glyphs(g, 'mono', size)[0][1]
                a = 170
        elif style == 'flicker':
            k = seg(t, st, st + .3)
            if k < 1 and hash1(key, i, CTX.bi) > k: a = 60
        elif style == 'pixel':
            if t < st + .35:
                _pixel_form(path, gx, y + dy, t, st + .2, size, col, f'{key}{i}')
                if t < st + .3: continue
        if t1 is not None:
            if out == 'delete':
                if t > t1 + (n - 1 - i) * .025: continue
            elif out == 'glitch':
                ko = seg(t, t1 + hash1(key, 'o', i) * .15, t1 + .2 + hash1(key, 'o', i) * .15)
                if ko >= 1: continue
                if ko > 0:
                    _pixel_burst(path, gx, y + dy, ko, col, f'{key}{i}'); a = int(a * (1 - ko))
                    dx += (hash1(key, 'gx', i, CTX.bi) - .5) * 40 * ko
            elif out == 'pop':
                ko = seg(t, t1 + i * .02, t1 + .25 + i * .02)
                if ko >= 1: continue
                a = int(a * (1 - ko))
        # occasional glitch jitter while alive
        if hash1(key, 'j', CTX.bi) > .93: dx += (hash1(key, 'jj', i, CTX.bi) - .5) * 14
        c.save(); c.translate(gx + dx, y + dy)
        if hash1(key, 'ca', CTX.bi) > .8:  # chromatic split flash
            for off, cc in ((-4, '#FF5A8A'), (4, '#5AD8FF')):
                c.save(); c.translate(off, 0)
                c.drawPath(drawp, skia.Paint(AntiAlias=True, Color=hexc(cc, int(a * .35)))); c.restore()
        _glow_draw(drawp, col, a, glowr=size * .14, outline=outline)
        c.restore()
    # scanlines over the text block
    if scan:
        for yy in np.arange(y - size * .85, y + size * .2, 5):
            c.drawLine(x0 - 10, yy, x0 + total + 10, yy, skia.Paint(Color=hexc('#0E1530', 40), StrokeWidth=1.6))
    # block cursor
    typed_all = t > t0 + din
    if style in ('type', 'decode') and (t1 is None or t < t1) and (t * 2.5) % 1 < .55:
        idx = n if typed_all else int(clamp((t - t0) / din) * n)
        cxp = x0 + sum(w for _, _, w in gl[:idx])
        P = rect(cxp + 4, y - size * .72, size * .5, size * .82)
        _glow_draw(topath(P), cols[-1], 220, glowr=size * .1)
