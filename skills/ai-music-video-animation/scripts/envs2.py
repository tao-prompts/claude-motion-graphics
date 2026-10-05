# envs2.py — v2 digital-world locations: editor UI, code city, circuit board + GPU, latent space, arena.
import math
import numpy as np
import skia
from engine import *
from chars import C, heart_pts, star_pts, sparkle, brush, render_bot
from envs import bg, scribble_line, brace_pts, _tile, NAVY

TEAL, ORANGE, VIOLET, CREAM, YEL = '#5FF2D0', '#FF9A4A', '#B79CFF', '#F3EBD8', '#F2D06B'
NIGHT = '#121A36'

# ---------------------------------------------------------------- light helpers
def gline(P, col, w=4.0, key='gl', a=1.0, closed=False, core=True):
    """glowing line: wide soft halo (additive) + bright core"""
    c = CTX.canvas
    D = boil(densify(P, closed, 8), key, .8, closed)
    path = topath(D, closed)
    for wd, al in ((w * 6, .10), (w * 3, .18)):
        p = skia.Paint(AntiAlias=True, Color=hexc(col, int(255 * al * a))); p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(wd); p.setStrokeCap(skia.Paint.kRound_Cap); p.setStrokeJoin(skia.Paint.kRound_Join); p.setBlendMode(skia.BlendMode.kPlus)
        c.drawPath(path, p)
    if core:
        p = skia.Paint(AntiAlias=True, Color=hexc(mix(col, '#FFFFFF', .45), int(255 * a))); p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(w); p.setStrokeCap(skia.Paint.kRound_Cap); p.setStrokeJoin(skia.Paint.kRound_Join)
        c.drawPath(path, p)

def gbox(x, y, s, col, a=1.0, key='gb', glowr=2.2):
    """a glowing pixel square (shiny, not pixel-art)"""
    if a <= 0.02: return
    glow(x, y, s * glowr, col, .35 * a)
    fill(rect(x - s / 2, y - s / 2, s, s), mix(col, '#FFFFFF', .25), key=key, a=int(255 * a), tex=0, edge=.25, amp=.25)
    wash(rect(x - s / 2 + s * .15, y - s / 2 + s * .15, s * .3, s * .3), '#FFFFFF', key=key + 'h', a=int(200 * a))

def particles(t, key, n, x0, x1, y0, y1, cols=(TEAL, ORANGE, VIOLET), rise=120, size=(8, 20), sparkles=.35, a=1.0):
    """drifting, rising, twinkling particles: glowing squares + 4-point sparkles"""
    for i in range(n):
        per = (y1 - y0) / rise * (.7 + .6 * hash1(key, 'p', i))
        ph = ((t / per) + hash1(key, 'o', i)) % 1.0
        x = x0 + (x1 - x0) * hash1(key, 'x', i) + 25 * math.sin(t * .8 + i)
        y = y1 - (y1 - y0) * ph
        k = math.sin(math.pi * ph) * a
        tw = .55 + .45 * math.sin(t * (3 + 3 * hash1(key, 't', i)) + i)
        col = cols[i % len(cols)]
        s = size[0] + (size[1] - size[0]) * hash1(key, 's', i)
        if hash1(key, 'k', i) < sparkles:
            sparkle(x, y, s * 1.4 * tw, f'{key}s{i}', mix(col, '#FFFFFF', .5), int(255 * k))
            glow(x, y, s * 3, col, .3 * k * tw)
        else:
            gbox(x, y, s * (.8 + .2 * tw), col, k * (.6 + .4 * tw), key=f'{key}b{i}')

def aura(x, y, r, col, a=.35):
    glow(x, y, r, col, a)

def grid_floor(hz, col, x0=-1500, x1=W + 1500, vx=960, a=1.0, key='gf', spacing=150, rows=16):
    for i in range(-int((vx - x0) / spacing), int((x1 - vx) / spacing) + 1):
        xb = vx + i * spacing
        ax = vx + (xb - vx) * .3
        gline([(ax, hz), (xb + (xb - vx) * 1.4, 2400)], col, 1.6, key=f'{key}v{i}', a=.55 * a, core=False)
        CTX.canvas.drawPath(topath(np.array([(ax, hz), (xb + (xb - vx) * 1.4, 2400)]), False), _ps(col, int(150 * a), 1.4))
    for j in range(rows):
        yy = hz + 6 + (j ** 1.8) * 7
        CTX.canvas.drawPath(topath(np.array([(x0, yy), (x1, yy)]), False), _ps(col, int(150 * a), 1.4))
        if j % 3 == 0: gline([(x0, yy), (x1, yy)], col, 1.4, key=f'{key}h{j}', a=.4 * a, core=False)

def _ps(col, a, w):
    p = skia.Paint(AntiAlias=True, Color=hexc(col, a)); p.setStyle(skia.Paint.kStroke_Style); p.setStrokeWidth(w); p.setBlendMode(skia.BlendMode.kPlus)
    return p

def code_tokens(x, y, i, k, scale=1.0, key='ct', a=255):
    """one line of 'code' made of coloured rounded dashes (no letters). k = 0..1 typed"""
    r = hash1(key, 'ind', i)
    xx = x + int(r * 3) * 22 * scale
    n = 2 + int(hash1(key, 'n', i) * 4)
    total = 0; toks = []
    for j in range(n):
        ln = (18 + 60 * hash1(key, 'l', i, j)) * scale
        col = [ORANGE, TEAL, VIOLET, CREAM, YEL, TEAL][int(hash1(key, 'c', i, j) * 6)]
        toks.append((ln, col)); total += ln + 10 * scale
    shown = total * k; acc = 0
    for ln, col in toks:
        if acc >= shown: break
        l2 = min(ln, shown - acc)
        if l2 > 2:
            fill(rrect(xx + acc, y - 6 * scale, l2, 12 * scale, 6 * scale), col, key=f'{key}{i}_{acc:.0f}', tex=0, edge=0, amp=.2, a=a)
        acc += ln + 10 * scale
    return xx + min(shown, total)

# ================================================================ editor on the monitor
def editor(t, mx, my, mw, mh, type_k, preview_k, click=None, cursor=None):
    fill(rect(mx, my, mw, mh), '#1B2232', key='ed', tex=.2, edge=.1)
    fill(rect(mx, my, mw, 32), '#2B3448', key='edbar', tex=.2, edge=.1)
    for j, col in enumerate(('#E5675B', '#F2C14E', '#6CC57A')):
        fill(ell(mx + 20 + j * 20, my + 16, 6, 6, 10), col, key=f'dot{j}', tex=0, edge=0)
    # run button
    rbx, rby = mx + mw - 34, my + 16
    hot = click is not None and click > 0
    fill(ell(rbx, rby, 12, 12, 16), '#6CF2C8' if hot else '#3FAE8E', key='run', tex=0, edge=.2, outline=1.5)
    fill(np.array([(rbx - 4, rby - 6), (rbx - 4, rby + 6), (rbx + 6, rby)]), '#FFFFFF', key='runt', tex=0, edge=0)
    if hot:
        for q in range(2):
            rr = 14 + 40 * clamp(click * 1.5 - q * .3)
            if rr > 14: gline(ell(rbx, rby, rr, rr, 24), TEAL, 2, key=f'rip{q}', a=1 - clamp(click * 1.5 - q * .3), closed=True)
    # gutter + code
    nl = 12
    for i in range(nl):
        y = my + 58 + i * 26
        fill(rrect(mx + 12, y - 4, 16, 8, 4), '#4A5470', key=f'ln{i}', tex=0, edge=0)
        k = clamp(type_k * nl - i)
        if k > 0:
            ex = code_tokens(mx + 46, y, i, k, 1.0, key='ed')
            if 0 < k < 1 and (t * 3) % 1 < .6:
                fill(rect(ex + 3, y - 10, 3, 20), CREAM, key='cur', tex=0, edge=0)
    # preview pane with Brush being "compiled"
    px, py, pw, ph = mx + 420, my + 48, 200, 330
    fill(rect(px, py, pw, ph), '#141A28', key='pv', tex=.2, edge=.1, outline=1.5, ocol='#3A4560')
    c = CTX.canvas
    c.save(); c.clipRect(skia.Rect.MakeXYWH(px, py, pw, ph))
    for gx in range(0, pw, 20):
        c.drawLine(px + gx, py, px + gx, py + ph, _ps('#2C3A5A', 120, 1))
    for gy in range(0, ph, 20):
        c.drawLine(px, py + gy, px + pw, py + gy, _ps('#2C3A5A', 120, 1))
    if preview_k > 0:
        fy = py + ph - 30; top = fy - 23 * 12.5
        scan = lerp(fy + 10, top - 10, preview_k)
        c.save(); c.clipRect(skia.Rect.MakeLTRB(px, scan, px + pw, py + ph))
        c.saveLayerAlpha(None, 170)
        brush(px + pw / 2, fy, 12.5, dict(eyes='closed', mouth='flat', noShadow=True, key='PV', drip=0))
        c.restore(); c.restore()
        if preview_k < 1:
            gline([(px + 6, scan), (px + pw - 6, scan)], TEAL, 2.5, key='scan')
    c.restore()
    if cursor is not None:
        cx_, cy_ = cursor
        P = np.array([(cx_, cy_), (cx_, cy_ + 26), (cx_ + 7, cy_ + 20), (cx_ + 12, cy_ + 31), (cx_ + 17, cy_ + 29), (cx_ + 12, cy_ + 18), (cx_ + 20, cy_ + 18)])
        fill(P, '#FFFFFF', key='mouse', tex=0, edge=0, outline=2)
    return (rbx, rby), (px + pw / 2, py + ph / 2)

# ================================================================ code city
def codecity(t, o=None):
    o = o or {}
    hz = o.get('horizon', 640)
    bg(NIGHT)
    grad_rect(-1500, -900, W + 3000, hz + 900, ['#0B1028', '#141C40', '#1F2B58'], [0, .65, 1])
    glow(960, hz, 900, '#3FD8C0', .22)
    # far data rain
    for i in range(26):
        x = -300 + i * 100 + 30 * hash1('dr', i)
        sp = 160 + 120 * hash1('drs', i)
        for j in range(5):
            y = ((t * sp + j * 140 + hash1('dro', i) * 700) % 760) - 120
            if y > hz - 40: continue
            fill(rrect(x, y, 5, 26, 2.5), TEAL if (i + j) % 3 else VIOLET, key=f'dr{i}_{j}', tex=0, edge=0, a=int(90 + 60 * hash1('dra', i, j)))
    # towers of code blocks
    for i in range(18):
        bw = 70 + 70 * hash1('tw', i); bh = 120 + 330 * hash1('th', i) ** 1.3
        bx = -420 + i * 160 + 40 * hash1('tx', i)
        if 640 < bx < 1220: bh *= .5
        fill(rect(bx, hz - bh, bw, bh), '#1D2A57' if i % 2 else '#22336A', key=f'tw{i}', tex=.3, edge=.2, outline=1.6, ocol='#4D6BC0')
        for r in range(int(bh / 34)):
            for q in range(int(bw / 26)):
                if hash1('win', i, r, q) < .45:
                    on = math.sin(t * (1 + 2 * hash1('wf', i, r, q)) + 9 * hash1('wp', i, r, q)) > -.3
                    col = [TEAL, ORANGE, VIOLET][int(hash1('wc', i, r, q) * 3)]
                    wash(rect(bx + 8 + q * 26, hz - bh + 12 + r * 34, 14, 8), col, key=f'w{i}{r}{q}', a=200 if on else 60)
    # sky code ribbons
    for i in range(5):
        yy = 90 + i * 70
        xs = -200 + ((t * 60 + i * 400) % 2400)
        P = [(xs - 600 + k * 60, yy + 14 * math.sin(k * .7 + t * 2 + i)) for k in range(11)]
        gline(catmull(P, False, 4), [TEAL, VIOLET, ORANGE][i % 3], 2.0, key=f'rib{i}', a=.5)
    # glowing brace gateways
    for side, bx in ((-1, 300), (1, 1620)):
        P = brace_pts(bx, hz - 600, 300, 595, side)
        fill(P, '#1C2650', key=f'gbr{side}', tex=.3, edge=.2)
        gline(P, ORANGE if side < 0 else TEAL, 4, key=f'gbo{side}', closed=True)
    # floor
    fill(np.array([(-1500, hz), (W + 1500, hz), (W + 1500, 2600), (-1500, 2600)]), '#10173A', key='cfl', tex=.35, edge=0, amp=.3)
    grid_floor(hz, TEAL, key='cg')
    gline([(-1500, hz), (W + 1500, hz)], TEAL, 3, key='hz')
    for i, (tx, ty, tw_, col) in enumerate(((240, hz + 140, 130, ORANGE), (1560, hz + 210, 150, TEAL), (520, hz + 380, 170, VIOLET), (1400, hz + 470, 160, ORANGE))):
        pk = .5 + .5 * pulse(t + i * .25, 3)
        P = np.array([(tx, ty), (tx + tw_, ty), (tx + tw_ * 1.1, ty + tw_ * .3), (tx + tw_ * .05, ty + tw_ * .3)])
        fill(P, col, key=f'ctl{i}', tex=0, edge=0, a=int(60 + 70 * pk))
    particles(t, 'ccp', 26, -200, 2100, 80, hz + 300, size=(7, 16))

# ================================================================ circuit board run (side view, wide world)
GPU_X, GPU_W, GPU_TOP = 3300, 760, 610
def circuit(t, o=None):
    o = o or {}
    camx = o.get('camx', 960)
    gy = 900  # trace / ground level
    bg('#0C2226')
    c = CTX.canvas
    grad_rect(camx - 2000, -900, 4000, 2400, ['#0A1B22', '#0F2A30', '#14383C'], [0, .6, 1])
    # far parallax chips (move at 50%)
    c.save(); c.translate(camx * .5, 0)
    for i in range(14):
        x = -800 + i * 420 + 120 * hash1('fc', i)
        w_ = 180 + 160 * hash1('fcw', i); h_ = 160 + 260 * hash1('fch', i)
        fill(rect(x, gy - 120 - h_, w_, h_), '#14363B', key=f'fc{i}', tex=.3, edge=.2, outline=1.5, ocol='#25555A')
        for q in range(int(w_ / 30)):
            wash(rect(x + 10 + q * 30, gy - 130 - h_ - 10, 10, 12), '#25555A', key=f'fcp{i}{q}')
        gline([(x + w_ / 2, gy - 120), (x + w_ / 2, gy - 60), (x + w_ / 2 + 140, gy - 60)], TEAL, 1.5, key=f'ftr{i}', a=.35, core=False)
    c.restore()
    # board
    fill(np.array([(camx - 2200, gy - 40), (camx + 2200, gy - 40), (camx + 2200, 2600), (camx - 2200, 2600)]), '#17423F', key='pcb', tex=.45, edge=0, amp=.3)
    # traces on board (teal faint), main orange track
    for j in range(5):
        yy = gy + 40 + j * 45
        P = [(camx - 2200, yy)]
        P += [(x, yy + (18 if (int(x / 300) + j) % 2 else 0)) for x in np.arange(math.floor((camx - 2200) / 150) * 150, camx + 2200, 150)]
        gline(np.array(P), TEAL if j % 2 else '#3FC0A0', 2, key=f'tr{j}', a=.35, core=False)
    gline([(camx - 2200, gy), (camx + 2200, gy)], ORANGE, 5, key='track', a=.9)
    # pulses along the main track
    for i in range(6):
        px = camx - 1200 + ((t * 900 + i * 420) % 2400)
        glow(px, gy, 50, ORANGE, .6); wash(ell(px, gy, 9, 9, 10), '#FFE3C0', key=f'tp{i}')
    # components (world positions)
    for i in range(10):
        x = 200 + i * 360 + 80 * hash1('cmp', i)
        if x > GPU_X - 300: break
        if abs(x - camx) > 1300: continue
        kind = i % 3
        if kind == 0:  # chip
            w_, h_ = 150, 90
            fill(rect(x, gy - 40 - h_, w_, h_), '#1C1F28', key=f'ch{i}', tex=.3, edge=.3, outline=2.5)
            for q in range(6):
                fill(rect(x + 10 + q * 23, gy - 42, 8, 14), '#B8BCC6', key=f'pin{i}{q}', tex=0, edge=0, outline=1)
            wash(ell(x + 20, gy - 40 - h_ + 18, 7, 7, 10), '#3A3F4C', key=f'chd{i}')
        elif kind == 1:  # capacitor
            fill(rect(x, gy - 150, 70, 110), '#3C5AA8', key=f'cap{i}', tex=.3, edge=.3, outline=2.5)
            fill(ell(x + 35, gy - 150, 35, 12, 18), '#9AA6C8', key=f'capt{i}', tex=.2, edge=.2, outline=2)
            wash(rect(x + 12, gy - 140, 10, 90), '#6F86C8', key=f'caph{i}', a=150)
        else:  # resistor
            fill(rrect(x, gy - 80, 110, 34, 16), '#D9B98A', key=f'res{i}', tex=.3, edge=.3, outline=2.2)
            for q, col in enumerate(('#B4461C', '#2E2530', '#E2A33A')):
                wash(rect(x + 26 + q * 22, gy - 80, 9, 34), col, key=f'rb{i}{q}')
            ink([(x - 20, gy - 63), (x, gy - 63)], 3, '#B8BCC6', key=f'rl{i}', closed=False)
            ink([(x + 110, gy - 63), (x + 130, gy - 63)], 3, '#B8BCC6', key=f'rr{i}', closed=False)
    gpu(t, o.get('gpu_glow', .3), o.get('fan', 1.0))
    particles(t, 'cip', 20, camx - 1100, camx + 1100, 100, gy, cols=(TEAL, ORANGE), size=(6, 14))

def gpu(t, core=.3, fan=1.0):
    x0, w_, top = GPU_X, GPU_W, GPU_TOP
    gy = 900
    glow(x0 + w_ / 2, top + 150, 700, TEAL, .15 + .4 * core)
    # board / shroud
    fill(rrect(x0, top, w_, gy - top - 20, 28), '#2A2F3C', key='gpu', tex=.4, edge=.4, outline=3.5)
    fill(rrect(x0 + 20, top + 20, w_ - 40, 60, 14), '#3A4152', key='gpuTop', tex=.3, edge=.3, outline=2.5)
    gline([(x0 + 40, top + 50), (x0 + w_ - 40, top + 50)], TEAL, 3, key='gpuStrip', a=.6 + .4 * core)
    for f, fx in enumerate((x0 + w_ * .28, x0 + w_ * .72)):
        fy = top + 170; R = 110
        fill(ell(fx, fy, R, R, 40), '#1A1D26', key=f'fan{f}', tex=.3, edge=.3, outline=3)
        ang = t * (6 + 30 * fan) * (1 if f else -1)
        for b in range(7):
            a0 = ang + b * 2 * math.pi / 7
            P = [(fx + 18 * math.cos(a0), fy + 18 * math.sin(a0)), (fx + R * .92 * math.cos(a0 + .25), fy + R * .92 * math.sin(a0 + .25)),
                 (fx + R * .92 * math.cos(a0 + .65), fy + R * .92 * math.sin(a0 + .65)), (fx + 22 * math.cos(a0 + .5), fy + 22 * math.sin(a0 + .5))]
            fill(np.array(P), '#596172', key=f'bl{f}{b}', tex=0, edge=.3, outline=1.8, amp=.4)
        fill(ell(fx, fy, 26, 26, 20), mix('#3A4152', TEAL, core), key=f'hub{f}', tex=0, edge=.2, outline=2.5)
        glow(fx, fy, 140, TEAL, .25 * core)
    # core window between fans
    cxw, cyw = x0 + w_ / 2, top + 170
    fill(rrect(cxw - 48, cyw - 48, 96, 96, 12), mix('#2B4A50', '#C8FFF0', core), key='core', tex=.2, edge=.3, outline=3)
    glow(cxw, cyw, 160 + 300 * core, TEAL, .4 + .5 * core)
    for q in range(10):
        fill(rect(x0 + 40 + q * 70, gy - 32, 34, 18), '#D8B04A', key=f'gpin{q}', tex=0, edge=.2, outline=1.4)
    return (cxw, cyw)

# ================================================================ latent space (AI world)
NODES = [(x, 150 + j * (430 / (n - 1))) for x, n in ((230, 5), (620, 6), (1300, 6), (1690, 5)) for j in range(n)]
def latent(t, o=None):
    o = o or {}
    hz = o.get('horizon', 660)
    bg('#171437')
    grad_rect(-1500, -900, W + 3000, hz + 900, ['#120F2E', '#1F1E50', '#2A3468'], [0, .6, 1])
    glow(960, hz - 120, 800, '#7F6CFF', .22)
    glow(960, hz - 60, 500, TEAL, .2)
    # stars
    for i in range(30):
        sx, sy = hash1('ls', i) * W, 30 + hash1('ly', i) * 520
        tw = .5 + .5 * math.sin(t * 3 + i * 1.7)
        if tw > .35: sparkle(sx, sy, 5 + 6 * tw, f'lst{i}', '#FFFBEA', int(220 * tw))
    # network edges + pulses
    cols = [[p for p in NODES if p[0] == x] for x in (230, 620, 1300, 1690)]
    k = 0
    for a_, b_ in ((0, 1), (1, 2), (2, 3)):
        for i, p in enumerate(cols[a_]):
            for j, q in enumerate(cols[b_]):
                if hash1('edge', a_, i, j) > .55: continue
                CTX.canvas.drawLine(p[0], p[1], q[0], q[1], _ps('#8E7CFF', 70, 1.6))
                ph = ((t * (.5 + hash1('ps', a_, i, j))) + hash1('po', a_, i, j)) % 1.0
                px_, py_ = lerp(p[0], q[0], ph), lerp(p[1], q[1], ph)
                glow(px_, py_, 30, TEAL if k % 2 else VIOLET, .7); k += 1
    for i, (nx, ny) in enumerate(NODES):
        pk = .5 + .5 * math.sin(t * 2.5 + i)
        glow(nx, ny, 60, VIOLET if i % 2 else TEAL, .25 + .3 * pk)
        fill(ell(nx, ny, 16, 16, 18), mix('#3A2F7A', '#E6DFFF', pk * .6), key=f'nd{i}', tex=0, edge=.2, outline=2.2)
    # floating generated images
    tiles = ((420, 240, 120, -.06), (1500, 230, 120, .05), (840, 120, 90, .04), (1100, 400, 80, -.05))
    for i, (tx, ty, s, rot) in enumerate(tiles):
        ty += math.sin(t * 1.1 + i * 1.3) * 12
        glow(tx, ty, s * 1.4, '#E8FFF4', .2)
        _tile(tx, ty, s, rot, i, t)
    # platform
    fill(np.array([(-1500, hz), (W + 1500, hz), (W + 1500, 2600), (-1500, 2600)]), '#1A1B45', key='lfl', tex=.35, edge=0, amp=.3)
    grid_floor(hz, VIOLET, key='lg', a=.8)
    gline([(-1500, hz), (W + 1500, hz)], VIOLET, 2.5, key='lhz', a=.8)
    pk = .5 + .5 * pulse(t, 3)
    fill(ell(960, hz + 280, 520, 110, 48), '#2A2F6A', key='plat', tex=.3, edge=.3, a=230)
    gline(ell(960, hz + 280, 520, 110, 64), TEAL, 4, key='platr', a=.6 + .4 * pk, closed=True)
    gline(ell(960, hz + 280, 400, 82, 64), VIOLET, 2.5, key='platr2', a=.5, closed=True)
    particles(t, 'lp', 30, -200, 2100, 60, hz + 400, cols=(TEAL, VIOLET, '#FFD9F0'), size=(6, 15))

# ================================================================ arena (meeting place)
def arena(t, o=None):
    o = o or {}
    hz = o.get('horizon', 700)
    play = o.get('play', .4)
    bg(NIGHT)
    grad_rect(-1500, -900, W + 3000, hz + 900, ['#0C1230', '#17204A', '#22305E'], [0, .6, 1])
    # back wall circuit traces: orange left, teal right
    for i in range(9):
        y0 = 120 + i * 60
        Pl = [(-300, y0), (200 + 40 * i, y0), (260 + 40 * i, y0 + 50), (520 - 20 * i, y0 + 50)]
        Pr = [(W + 300, y0), (W - 200 - 40 * i, y0), (W - 260 - 40 * i, y0 + 50), (W - 520 + 20 * i, y0 + 50)]
        gline(Pl, ORANGE, 2, key=f'awl{i}', a=.45, core=False); gline(Pr, TEAL, 2, key=f'awr{i}', a=.45, core=False)
        for P, col, kk in ((Pl, ORANGE, 'l'), (Pr, TEAL, 'r')):
            ph = ((t * .6 + i * .13) % 1.0)
            seg_i = min(2, int(ph * 3)); f_ = ph * 3 - seg_i
            px_, py_ = lerp(P[seg_i][0], P[seg_i + 1][0], f_), lerp(P[seg_i][1], P[seg_i + 1][1], f_)
            glow(px_, py_, 36, col, .7)
    # light cone from the play orb
    cone = np.array([(900, 220), (1020, 220), (1420, hz + 120), (500, hz + 120)])
    cp = skia.Paint(AntiAlias=True)
    cp.setShader(skia.GradientShader.MakeLinear([(960, 220), (960, hz + 100)], [hexc('#BFFFF0', int(60 + 70 * play)), hexc('#BFFFF0', 10)]))
    cp.setBlendMode(skia.BlendMode.kPlus)
    CTX.canvas.drawPath(topath(boil(densify(cone, True, 20), 'acone', 3)), cp)
    # side data towers
    for side in (-1, 1):
        for k in range(9):
            bx = (60 if side < 0 else W - 60 - 150) + side * 0 + (k % 2) * 30 * -side
            by = hz - 70 - k * 78
            col = ORANGE if side < 0 else TEAL
            on = .5 + .5 * math.sin(t * 4 + k * .9 + side)
            fill(rect(bx, by, 150, 64), '#1B2550', key=f'blk{side}{k}', tex=.3, edge=.2, outline=2, ocol=mix(col, '#1B2550', .3))
            for q in range(3):
                wash(rect(bx + 16 + q * 44, by + 26, 28, 10), col, key=f'bw{side}{k}{q}', a=int(80 + 160 * on * hash1('bo', side, k, q)))
        glow(110 if side < 0 else W - 110, hz - 350, 380, ORANGE if side < 0 else TEAL, .15)
    # filmstrips
    for side in (-1, 1):
        S = catmull([(960 + side * 190, 120), (960 + side * 450, 80), (960 + side * 760, 140)], False, 12)
        d = np.gradient(S, axis=0); nrm = np.stack([-d[:, 1], d[:, 0]], 1); nrm /= np.hypot(nrm[:, 0], nrm[:, 1])[:, None]
        A, B = S + nrm * 58, S - nrm * 58
        fill(np.vstack([A, B[::-1]]), '#262B3C', key=f'afs{side}', tex=.3, edge=.3, outline=2.5)
        for k in range(4, len(S) - 3, 6):
            fx, fy = S[k]
            fl = .5 + .5 * math.sin(t * 5 + k)
            fill(rect(fx - 36, fy - 34, 72, 68), mix('#2E4A66', TEAL if side > 0 else ORANGE, .25 + .35 * fl), key=f'aff{side}{k}', tex=.2, edge=.2, outline=1.5)
        for k in range(1, len(S) - 1, 2):
            for m in (49, -49):
                hx, hy = S[k] + nrm[k] * m
                wash(rect(hx - 6, hy - 5, 12, 10), '#D9CDB4', key=f'asp{side}{k}{m}')
    # floor: orange-grid left, teal-grid right
    fill(np.array([(-1500, hz), (W + 1500, hz), (W + 1500, 2600), (-1500, 2600)]), '#10173A', key='afl', tex=.35, edge=0, amp=.3)
    c = CTX.canvas
    c.save(); c.clipRect(skia.Rect.MakeLTRB(-1500, hz - 2, 960, 2600)); grid_floor(hz, ORANGE, key='agl', a=.9); c.restore()
    c.save(); c.clipRect(skia.Rect.MakeLTRB(960, hz - 2, W + 1500, 2600)); grid_floor(hz, TEAL, key='agr', a=.9); c.restore()
    gline([(-1500, hz), (960, hz)], ORANGE, 3, key='ahl'); gline([(960, hz), (W + 1500, hz)], TEAL, 3, key='ahr')
    # light roads
    gline([(-1500, hz + 300), (700, hz + 300)], ORANGE, 6, key='rdl', a=.8)
    gline([(1220, hz + 300), (W + 1500, hz + 300)], TEAL, 6, key='rdr', a=.8)
    pk = .5 + .5 * pulse(t, 3)
    gline(ell(960, hz + 300, 300, 60, 64), mix(ORANGE, TEAL, .5), 4, key='apl', a=.5 + .5 * pk, closed=True)
    glow(960, hz + 200, 520, '#FFE9A8', .12 + .15 * play)
    # play orb
    px, py, pr = 960, 190, 88
    glow(px, py, 380, '#7DFFD8', .25 + .55 * play)
    for k in range(14):
        a = k * 2 * math.pi / 14 + t * .2
        r0, r1 = pr * 1.3, pr * (1.55 + .35 * play)
        gline([(px + r0 * math.cos(a), py + r0 * math.sin(a)), (px + r1 * math.cos(a), py + r1 * math.sin(a))], '#F7E7A0', 3, key=f'aray{k}', a=.4 + .6 * play)
    fill(ell(px, py, pr, pr, 40), mix('#3FA58E', '#8FF0D2', play), key='aorb', tex=.3, edge=.4, outline=3.5)
    fill(ell(px, py, pr * .78, pr * .78, 40), mix('#5FBFA6', '#C8FFEE', play), key='aorb2', tex=.2, edge=.2)
    fill(np.array([(px - 28, py - 42), (px - 28, py + 42), (px + 44, py)]), '#F6FFF9', key='atri', tex=0, edge=.15, outline=2.5)
    particles(t, 'ap', 26, -100, 2000, 80, hz + 350, size=(6, 15))

# ================================================================ transitions (screen space)
def light_whip(p, col=ORANGE, key='lw'):
    """a huge light trail sweeps left->right; full cover around p=.5"""
    if p <= 0 or p >= 1: return
    c = CTX.canvas
    head = lerp(-600, W + 2200, easeIn(p) if p < .5 else .5 + (p - .5))
    head = lerp(-400, W + 1800, p)
    tail = head - 2400
    for i in range(9):
        y = -80 + i * 155
        P = [(tail, y + 30 * math.sin(i)), (head - 300, y), (head, y - 10)]
        D = catmull(P, False, 10)
        cc = [ORANGE, '#FFC27A', '#FFE3C0', ORANGE][i % 4]
        path = ribbon(D, 60, 190, key=f'{key}{i}', var=.08)
        pt = skia.Paint(AntiAlias=True, Color=hexc(cc, 255)); c.drawPath(path, pt)
    for i in range(14):
        y = hash1(key, 'y', i) * H
        x = head - 200 - hash1(key, 'x', i) * 1600
        ink([(x - 300, y), (x, y)], 5, '#FFF6E0', key=f'{key}s{i}', closed=False, a=200)

def noise_dissolve(p, key='nd', cols=(TEAL, VIOLET, '#FFFFFF', '#2A3468')):
    """diffusion-style noise speckles cover the frame (p 0->.5) then clear (.5->1)"""
    if p <= 0 or p >= 1: return
    cover = math.sin(math.pi * p)
    c = CTX.canvas
    bgp = skia.Paint(Color=hexc('#1A1F45', int(255 * clamp(cover * 1.6 - .3))))
    c.drawRect(skia.Rect.MakeXYWH(0, 0, W, H), bgp)
    n = int(900 * cover)
    r = np.random.default_rng(int(p * 1000) + 7)
    xs = r.random(n) * W; ys = r.random(n) * H; ss = 6 + r.random(n) * 26; cs = r.integers(0, len(cols), n)
    for i in range(n):
        pp = skia.Paint(Color=hexc(cols[cs[i]], int(200 * cover)))
        c.drawRect(skia.Rect.MakeXYWH(xs[i], ys[i], ss[i], ss[i]), pp)

def data_rain_wipe(p, key='drw'):
    if p <= 0 or p >= 1: return
    c = CTX.canvas
    cols = 24; cw = W / cols
    for i in range(cols):
        d = hash1(key, i) * .25
        a = easeIn(seg(p, d * .6, d * .6 + .3)); b = easeIn(seg(p, .52 + d * .8, .8 + d * .8))
        y1 = -100 + a * (H + 200); y0 = -100 + b * (H + 200)
        if y1 - y0 < 2: continue
        col = TEAL if i % 3 else (ORANGE if i % 2 else VIOLET)
        fill(rect(i * cw - 1, y0, cw + 2, y1 - y0), mix('#141C40', col, .25), key=f'{key}{i}', tex=.2, edge=0, amp=.3)
        for j in range(int((y1 - y0) / 40)):
            yy = y0 + j * 40 + 10
            fill(rrect(i * cw + cw * .3, yy, cw * .4, 22, 6), col, key=f'{key}{i}_{j}', tex=0, edge=0, a=int(120 + 120 * hash1(key, i, j)))
        glow(i * cw + cw / 2, y1, 90, col, .6)

def dive_streaks(p, cx=W / 2, cy=H / 2, key='ds', cols=(TEAL, ORANGE, VIOLET, CREAM)):
    """streaks radiating from the centre as the camera dives into the screen"""
    if p <= 0: return
    for i in range(40):
        a = hash1(key, 'a', i) * 2 * math.pi
        sp = .5 + hash1(key, 's', i)
        r0 = (hash1(key, 'r', i) * 200 + p * 2200 * sp) % 1600
        r1 = r0 + 60 + 400 * p * sp
        x0, y0 = cx + r0 * math.cos(a), cy + r0 * math.sin(a)
        x1, y1 = cx + r1 * math.cos(a), cy + r1 * math.sin(a)
        gline([(x0, y0), (x1, y1)], cols[i % len(cols)], 3 + 4 * p, key=f'{key}{i}', a=clamp(p * 2))
