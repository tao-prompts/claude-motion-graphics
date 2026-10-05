# envs3.py — environment sheet 2, re-painted in code: GPU city, data highway, neural garden, timeline studio.
import math
import numpy as np
import skia
from engine import *
from chars import sparkle, heart_pts
from envs import bg, _tile
from envs2 import gline, gbox, particles, _ps

TEAL, ORANGE, LAV, GOLD = '#5FF2D0', '#FF9A4A', '#B79CFF', '#F2C14E'

# ================================================================ GPU CITY (front view, road to the core)
GC_HZ = 600
def road_quad(z0, z1, w0=150, w1=1200, hz=GC_HZ, vx=960, ybot=1180):
    """perspective road band between depths z0..z1 (0 = horizon, 1 = bottom)"""
    def at(z):
        y = lerp(hz, ybot, z ** 1.6); w = lerp(w0, w1, z ** 1.6)
        return y, w
    ya, wa = at(z0); yb, wb = at(z1)
    return np.array([(vx - wa / 2, ya), (vx + wa / 2, ya), (vx + wb / 2, yb), (vx - wb / 2, yb)])
def road_pt(z, xoff, hz=GC_HZ, vx=960, w0=150, w1=1200, ybot=1180):
    """xoff in -1..1 across the road; returns (x, y, scale)"""
    y = lerp(hz, ybot, z ** 1.6); w = lerp(w0, w1, z ** 1.6)
    return vx + xoff * w / 2, y, w / w1

def gpucity(t, o=None):
    o = o or {}
    core = o.get('core', .6)
    bg('#1C262C')
    grad_rect(-1500, -900, W + 3000, GC_HZ + 900, ['#151D24', '#1F2B33', '#2A3A40'], [0, .6, 1])
    # board traces on the back wall
    for i in range(14):
        x = 560 + i * 60
        gline([(x, 0), (x, 120 + 30 * (i % 3)), (960 + (x - 960) * .3, 200)], TEAL, 1.5, key=f'bt{i}', a=.35, core=False)
    # fans
    for f, (fx, fy) in enumerate(((430, 240), (1490, 240))):
        R = 250
        fill(rrect(fx - R - 30, fy - R - 30, 2 * R + 60, 2 * R + 60, 40), '#2A343B', key=f'fh{f}', tex=.4, edge=.35, outline=3.5)
        fill(ell(fx, fy, R, R, 48), '#1B2228', key=f'fd{f}', tex=.3, edge=.3, outline=3)
        ang = t * 1.6 * (1 if f else -1)
        for b in range(9):
            a0 = ang + b * 2 * math.pi / 9
            P = [(fx + 60 * math.cos(a0), fy + 60 * math.sin(a0)), (fx + R * .9 * math.cos(a0 + .35), fy + R * .9 * math.sin(a0 + .35)),
                 (fx + R * .94 * math.cos(a0 + .7), fy + R * .94 * math.sin(a0 + .7)), (fx + 66 * math.cos(a0 + .45), fy + 66 * math.sin(a0 + .45))]
            fill(np.array(P), '#3B4C52', key=f'fb{f}{b}', tex=.2, edge=.3, outline=1.8, amp=.5)
        fill(ell(fx, fy, 62, 62, 30), '#222A30', key=f'fhb{f}', tex=.2, edge=.3, outline=3)
        gline(ell(fx, fy, 62, 62, 40), TEAL, 6, key=f'fr{f}', closed=True, a=.6 + .4 * core)
        glow(fx, fy, 260, TEAL, .12 + .1 * core)
    # core chip
    cx, cy = 960, 175
    fill(rect(cx - 140, cy - 120, 280, 240), '#26323A', key='cch', tex=.3, edge=.3, outline=3)
    for q in range(9):
        for side in (-1, 1):
            gline([(cx + side * 140, cy - 100 + q * 25), (cx + side * 175, cy - 100 + q * 25)], TEAL, 1.5, key=f'cp{q}{side}', a=.5, core=False)
    fill(rect(cx - 80, cy - 75, 160, 150), mix('#4FA896', '#D8FFF2', core), key='ccore', tex=.25, edge=.3, outline=3)
    glow(cx, cy, 200 + 250 * core, TEAL, .35 + .45 * core)
    # light shafts behind skyline
    for i in range(16):
        x = 260 + i * 92 + 30 * hash1('ls', i)
        if 860 < x < 1060: continue
        h = 220 + 200 * hash1('lh', i)
        p = skia.Paint(AntiAlias=True)
        p.setShader(skia.GradientShader.MakeLinear([(x, GC_HZ - h), (x, GC_HZ)], [hexc('#FFD9A0', 0), hexc('#FFD9A0', 90)]))
        CTX.canvas.drawRect(skia.Rect.MakeXYWH(x, GC_HZ - h, 22, h), p)
    # skyline (chip buildings) — receding toward the centre
    for side in (-1, 1):
        for i in range(10):
            d = i / 9  # 0 near edge, 1 near centre
            bw = lerp(150, 60, d); bh = lerp(430, 160, d) * (.75 + .5 * hash1('bh', side, i))
            bx = (lerp(-40, 820, d) if side < 0 else lerp(1960 - bw, 1100, d))
            by = GC_HZ + 40 - bh
            fill(rect(bx, by, bw, bh), '#232B33' if i % 2 else '#2B343C', key=f'b{side}{i}', tex=.35, edge=.3, outline=2.5)
            for r in range(int(bh / 32)):
                for q in range(int(bw / 26)):
                    if hash1('w', side, i, r, q) < .5:
                        on = math.sin(t * (1 + hash1('wf', side, i, r, q)) + 7 * hash1('wp', side, i, r, q)) > -.4
                        col = ORANGE if hash1('wc', side, i, r, q) < .65 else TEAL
                        wash(rect(bx + 8 + q * 26, by + 12 + r * 32, 13, 16), col, key=f'w{side}{i}{r}{q}', a=230 if on else 70)
            glow(bx + bw / 2, by + bh * .5, bw * 1.2, ORANGE, .06)
    # ground board
    fill(np.array([(-1500, GC_HZ), (W + 1500, GC_HZ), (W + 1500, 2600), (-1500, 2600)]), '#25343A', key='gnd', tex=.45, edge=0, amp=.3)
    fill(road_quad(0, 1.2), '#1A2329', key='road', tex=.4, edge=.2)
    # traces along the road (glowing, with right-angle bends)
    for side in (-1, 1):
        for j, (xo, col) in enumerate(((1.15, ORANGE), (1.45, TEAL), (1.9, ORANGE))):
            P = []
            for z in np.linspace(0, 1.15, 14):
                x, y, s = road_pt(z, side * xo)
                P.append((x, y))
            gline(np.array(P), col, 4, key=f'tr{side}{j}', a=.85)
        for k in range(5):
            z = .25 + k * .18
            x, y, s = road_pt(z, side * 1.15)
            x2, y2, _ = road_pt(z, side * 2.6)
            gline([(x, y), ((x + x2) / 2, y), (x2, y + 40 * s)], TEAL if k % 2 else ORANGE, 3, key=f'tb{side}{k}', a=.7)
            gline(ell(x2, y + 40 * s, 14 * s + 4, 8 * s + 3, 16), ORANGE, 3, key=f'via{side}{k}', closed=True)
    # pulses running down the road traces
    for i in range(8):
        z = ((t * .35 + i / 8) % 1.0) * 1.1
        side = 1 if i % 2 else -1
        x, y, s = road_pt(z, side * 1.15)
        glow(x, y, 40 * s + 10, ORANGE if i % 2 else TEAL, .8)
    # capacitors foreground
    for side in (-1, 1):
        for i, (cx_, cy_, r_) in enumerate(((140, 820, 110), (300, 980, 130), (90, 1060, 90))):
            x = cx_ if side < 0 else W - cx_
            fill(rect(x - r_, cy_ - r_ * 1.3, 2 * r_, r_ * 1.3), '#2E363C', key=f'cap{side}{i}', tex=.4, edge=.4, outline=3)
            fill(ell(x, cy_ - r_ * 1.3, r_, r_ * .32, 30), '#3E484E', key=f'capt{side}{i}', tex=.3, edge=.3, outline=3)
            wash(rect(x - r_ * .7, cy_ - r_ * 1.2, r_ * .18, r_ * 1.1), '#56626A', key=f'caph{side}{i}', a=160)
    particles(t, 'gcp', 24, -100, 2000, 100, 1100, cols=(TEAL, ORANGE), size=(6, 14))

# ================================================================ DATA HIGHWAY (winding road to the swirl)
HW_P = [(1680, 85), (1500, 125), (1330, 170), (1300, 240), (1460, 300), (1640, 390), (1680, 520), (1520, 650), (1240, 790), (900, 960), (560, 1180), (200, 1450), (-200, 1750)]
_HW = None
def hw_center():
    global _HW
    if _HW is None:
        S = catmull(HW_P, False, 10)
        L = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(S, axis=0).T))])
        _HW = (S, L / L[-1])
    return _HW
def hw_at(s):
    """centre point, tangent, width at road parameter s (0 far .. 1 near)"""
    S, U = hw_center()
    x = np.interp(s, U, S[:, 0]); y = np.interp(s, U, S[:, 1])
    sa, sb = max(0, s - .006), min(1, s + .006)
    tx = np.interp(sb, U, S[:, 0]) - np.interp(sa, U, S[:, 0]); ty = np.interp(sb, U, S[:, 1]) - np.interp(sa, U, S[:, 1])
    L = math.hypot(tx, ty) + 1e-9
    w = lerp(26, 1500, s ** 2.2)
    return x, y, tx / L, ty / L, w
def hw_lane(s, lane):
    """lane -1 = orange (left/inner), +1 = teal. returns (x, y, scale)"""
    x, y, tx, ty, w = hw_at(s)
    nx, ny = -ty, tx
    return x + nx * lane * w * .25, y + ny * lane * w * .25, w / 980

def highway(t, o=None):
    o = o or {}
    bg('#1A1636')
    grad_rect(-1500, -900, W + 3000, 2800, ['#120F2C', '#211C48', '#2E2758'], [0, .5, 1])
    # swirl galaxy top-right
    gx, gy = 1700, 90
    glow(gx, gy, 420, '#FFB070', .35); glow(gx, gy, 160, '#FFF0C0', .6)
    for arm in range(3):
        P = [(gx + (20 + q * 9) * math.cos(t * .4 + arm * 2.1 + q * .22), gy + (20 + q * 9) * .7 * math.sin(t * .4 + arm * 2.1 + q * .22)) for q in range(30)]
        gline(np.array(P), ['#FFB070', '#C9A0FF', '#FFE0A0'][arm], 3, key=f'gal{arm}', a=.5, core=False)
    # stars + speed streaks
    for i in range(40):
        sx, sy = hash1('hs', i) * 2000, hash1('hy', i) * 700
        tw = .5 + .5 * math.sin(t * 3 + i)
        if tw > .4: wash(rect(sx, sy, 5, 5), '#FFFBEA', key=f'hst{i}', a=int(200 * tw))
    for i in range(14):
        ph = ((t * .9 + hash1('sk', i)) % 1.0)
        y = 40 + hash1('sy', i) * 600
        x = lerp(-300, 2200, ph)
        col = [TEAL, ORANGE, '#E86AA8', LAV][i % 4]
        gline([(x - 220, y + 60), (x, y)], col, 3, key=f'skr{i}', a=.7 * math.sin(math.pi * ph))
    # road: draw from far to near as quads
    S, U = hw_center()
    N = 60
    prev = None
    for k in range(N + 1):
        s = k / N
        x, y, tx, ty, w = hw_at(s)
        nx, ny = -ty, tx
        cur = (x, y, nx, ny, w)
        if prev:
            px, py, pnx, pny, pw = prev
            def q(a, b):
                return np.array([(px + pnx * pw * a, py + pny * pw * a), (px + pnx * pw * b, py + pny * pw * b),
                                 (x + nx * w * b, y + ny * w * b), (x + nx * w * a, y + ny * w * a)])
            # side wall
            wall = np.array([(px + pnx * pw * .62, py + pny * pw * .62), (x + nx * w * .62, y + ny * w * .62),
                             (x + nx * w * .62, y + ny * w * .62 + 60 * w / 1250 + 4), (px + pnx * pw * .62, py + pny * pw * .62 + 60 * pw / 1250 + 4)])
            qa, qb = topath(q(-.55, 0)), topath(q(0, .55))
            CTX.canvas.drawPath(qa, skia.Paint(AntiAlias=True, Color=hexc(mix('#B85A28', '#FF9A4A', s))))
            CTX.canvas.drawPath(qb, skia.Paint(AntiAlias=True, Color=hexc(mix('#2A8C7C', '#5FE0C4', s))))
            CTX.canvas.drawPath(qa, texpaint(1, .35)); CTX.canvas.drawPath(qb, texpaint(2, .35))
            CTX.canvas.drawPath(topath(q(-.62, -.55)), skia.Paint(AntiAlias=True, Color=hexc('#3A3260')))
            CTX.canvas.drawPath(topath(q(.55, .62)), skia.Paint(AntiAlias=True, Color=hexc('#3A3260')))
        prev = cur
    # texture over road + glowing edge lines + flowing dashes
    E = []
    for side in (-.62, .62, 0):
        P = []
        for k in range(N + 1):
            x, y, tx, ty, w = hw_at(k / N); P.append((x - ty * w * side, y + tx * w * side))
        gline(np.array(P), '#FFE6C0' if side == 0 else (ORANGE if side < 0 else TEAL), 2 + 3 * (side != 0), key=f'he{side}', a=.8)
    for lane in (-1, 1):
        for i in range(10):
            s0 = ((o.get('ft', t) * .28 + i / 10) % 1.0)
            pts = [hw_lane(min(1, s0 + d), lane * .9)[:2] for d in (0, .03)]
            sc = hw_lane(s0, lane)[2]
            gline(np.array(pts), '#FFF3D8' if lane < 0 else '#E8FFF8', 2 + 6 * sc, key=f'hd{lane}{i}', a=.8)
    # pillars under the road edge (near half)
    for k in range(6, 20):
        s = k / 20
        x, y, tx, ty, w = hw_at(s)
        bx, by = x + ty * w * .62, y - tx * w * .62 + 10
        if s > .3:
            fill(rect(bx - 8 * w / 1250 - 3, by, 16 * w / 1250 + 6, 260 * w / 1250 + 20), '#2B2547', key=f'pl{k}', tex=0, edge=.2, outline=1.5)
    # data cubes riding the road
    for i in range(9):
        s = ((o.get('ft', t) * .22 + i / 9) % 1.0)
        lane = 1 if i % 2 else -1
        x, y, sc = hw_lane(s, lane * .55)
        hov = 70 * sc + 10 + 8 * math.sin(t * 3 + i)
        cube(x, y - hov, 90 * sc + 8, TEAL if i % 3 else ORANGE, key=f'cb{i}')
    particles(t, 'hwp', 18, -100, 2000, 100, 1100, cols=(TEAL, ORANGE, LAV), size=(5, 12))

def cube(x, y, s, col, key='cu', a=1.0):
    h = s / 2
    glow(x, y, s * 1.4, col, .45 * a)
    front = np.array([(x - h, y - h + s * .15), (x + h * .6, y - h + s * .15), (x + h * .6, y + h), (x - h, y + h)])
    top = np.array([(x - h, y - h + s * .15), (x - h * .6, y - h - s * .15), (x + h, y - h - s * .15), (x + h * .6, y - h + s * .15)])
    side = np.array([(x + h * .6, y - h + s * .15), (x + h, y - h - s * .15), (x + h, y + h - s * .3), (x + h * .6, y + h)])
    for P, k in ((front, .35), (top, .55), (side, .2)):
        CTX.canvas.drawPath(topath(P), skia.Paint(AntiAlias=True, Color=hexc(mix(col, '#FFFFFF', k), int(150 * a))))
    for P in (front, top, side):
        gline(P, col, max(1.5, s * .03), key=key + str(len(P)), closed=True, a=a)

# ================================================================ NEURAL GARDEN
NG_HZ = 640
def garden(t, o=None):
    o = o or {}
    beam = o.get('beam', 1.0)
    bg('#1E2148')
    grad_rect(-1500, -900, W + 3000, NG_HZ + 900, ['#181A3E', '#262A5A', '#3A4474'], [0, .55, 1])
    for i in range(40):
        sx, sy = hash1('ns', i) * 2100 - 90, hash1('ny', i) * 520
        tw = .5 + .5 * math.sin(t * 2.6 + i)
        if tw > .45: wash(rect(sx, sy, 4, 4), '#FFF8E0', key=f'nst{i}', a=int(200 * tw))
    # constellation network
    nodes = [(hash1('nx', i) * 2100 - 90, 60 + hash1('nyy', i) ** 1.2 * 380) for i in range(34)]
    for i, (x, y) in enumerate(nodes):
        for j in range(i + 1, len(nodes)):
            x2, y2 = nodes[j]
            if math.hypot(x - x2, y - y2) < 230 and hash1('ne', i, j) < .55:
                CTX.canvas.drawLine(x, y, x2, y2, _ps('#9FE8D0' if (i + j) % 2 else '#F2D79A', 90, 1.6))
                ph = (t * .6 + hash1('nep', i, j)) % 1.0
                if hash1('nepp', i, j) < .35: glow(lerp(x, x2, ph), lerp(y, y2, ph), 22, TEAL, .7)
    for i, (x, y) in enumerate(nodes):
        pk = .5 + .5 * math.sin(t * 2 + i)
        col = TEAL if i % 3 else GOLD
        glow(x, y, 34, col, .3 + .4 * pk)
        wash(ell(x, y, 6, 6, 10), mix(col, '#FFFFFF', .5), key=f'nn{i}', a=255)
    # light beam from the sky
    if beam > 0:
        bp_ = skia.Paint(AntiAlias=True)
        bp_.setShader(skia.GradientShader.MakeLinear([(960, -100), (960, NG_HZ)], [hexc('#BFFFEA', int(150 * beam)), hexc('#BFFFEA', int(30 * beam))]))
        bp_.setBlendMode(skia.BlendMode.kPlus)
        CTX.canvas.drawPath(topath(np.array([(900, -100), (1020, -100), (1060, NG_HZ - 80), (860, NG_HZ - 80)])), bp_)
        glow(960, NG_HZ - 100, 260, TEAL, .4 * beam)
    # hills (back to front)
    for li, (hy, col, amp, ph) in enumerate(((NG_HZ - 130, '#3D3F78', 90, .3), (NG_HZ - 70, '#47528A', 70, 1.7), (NG_HZ - 20, '#3E6A78', 60, 2.9))):
        P = [(-1500, 2000)] + [(x, hy - amp * (.5 + .5 * math.sin(x * .004 + ph)) - (50 if li == 1 and 700 < x < 1220 else 0)) for x in range(-1500, 3500, 80)] + [(3500, 2000)]
        fill(np.array(P), col, key=f'hl{li}', tex=.5, edge=.3, outline=2, amp=1.2)
        for q in range(6):
            fx = -100 + q * 380 + 100 * hash1('hd', li, q)
            wash(ell(fx, hy - 10, 50, 20, 14), mix(col, '#FFFFFF', .12), key=f'hdot{li}{q}', a=120)
    # meadow
    fill(np.array([(-1500, NG_HZ), (W + 1500, NG_HZ), (W + 1500, 2600), (-1500, 2600)]), '#4E7C78', key='mead', tex=.45, edge=0, amp=.4)
    grad_rect(-1500, NG_HZ, W + 3000, 600, ['#3F6A6E', '#5E8E82'], [0, 1])
    # lantern flowers
    for i, (x, h, r) in enumerate(((60, 520, 70), (160, 360, 40), (300, 470, 55), (420, 300, 30), (560, 250, 26), (1360, 260, 28), (1520, 330, 36), (1640, 470, 56), (1780, 380, 44), (1880, 520, 66), (760, 180, 18), (1180, 190, 20))):
        base_y = NG_HZ + 260 + (60 if r > 50 else 0)
        sway = math.sin(t * 1.2 + i) * 10
        top = (x + sway, base_y - h)
        ink(catmull([(x, base_y), (x + sway * .3 - 15, base_y - h * .5), top], False, 6), max(3, r * .12), '#2A2F40', key=f'stem{i}', closed=False)
        glow(top[0], top[1], r * 3, GOLD, .45)
        fill(ell(top[0], top[1], r, r, 30), '#F6D38A', key=f'lan{i}', tex=.3, edge=.3, outline=2.5)
        wash(ell(top[0] - r * .25, top[1] - r * .25, r * .4, r * .3, 14), '#FFF6DA', key=f'lanh{i}', a=200)
        fill(np.array([(top[0] - r * .45, top[1] + r * .8), (top[0], top[1] + r * .5), (top[0] + r * .45, top[1] + r * .8), (top[0], top[1] + r * 1.05)]), '#3A3F55', key=f'cal{i}', tex=0, edge=.2, outline=1.5)
    # foreground leaves
    for side in (-1, 1):
        for i in range(6):
            bx = (60 + i * 70) if side < 0 else (W - 60 - i * 70)
            by = 1080 + 20 * hash1('lfy', side, i)
            ang = (-.6 + i * .15) * side
            L = 220 + 120 * hash1('lfl', side, i)
            P = catmull([(bx, by), (bx + math.sin(ang) * L * .5 - side * 40, by - L * .55), (bx + math.sin(ang) * L, by - L), (bx + math.sin(ang) * L * .5 + side * 40, by - L * .45)], True, 6)
            fill(P, '#2C2E52' if i % 2 else '#3A3368', key=f'lf{side}{i}', tex=.4, edge=.3, outline=2.5)
        for i in range(3):
            bx = (240 + i * 140) if side < 0 else (W - 240 - i * 140)
            fill(ell(bx, 1030 + 30 * i, 120 - 20 * i, 70, 24), '#5A4C8C', key=f'bush{side}{i}', tex=.4, edge=.3, outline=2.5)
    # fireflies
    for i in range(26):
        x = hash1('ff', i) * 2000 - 40 + 40 * math.sin(t * .7 + i)
        y = NG_HZ - 100 + hash1('fy', i) * 460 + 20 * math.sin(t * 1.1 + i * 2)
        tw = .5 + .5 * math.sin(t * 4 + i * 1.9)
        glow(x, y, 26, GOLD, .7 * tw); wash(ell(x, y, 4, 4, 8), '#FFF3C8', key=f'ffd{i}', a=int(255 * tw))

# ================================================================ TIMELINE STUDIO
TL_FLOOR = 640
def playhead_x(t):
    return 200 + ((t - 26.0) / 6.0) * 1500

def timeline(t, o=None):
    o = o or {}
    bg('#232833')
    grad_rect(-1500, -900, W + 3000, TL_FLOOR + 900, ['#1C2029', '#262C38', '#2E3542'], [0, .6, 1])
    rows = [(40, 95), (150, 240), (290, 360), (410, 560)]
    for i, (y0, y1) in enumerate(rows):
        fill(rect(-1500, y0 - 10, W + 3000, y1 - y0 + 20), '#2A303C' if i % 2 else '#262B36', key=f'row{i}', tex=.3, edge=0, amp=.3)
        CTX.canvas.drawLine(-1500, y0 - 10, W + 1500, y0 - 10, _ps('#3C4456', 255, 2))
    # row 0: small clips
    for i, (x, w, col) in enumerate(((-40, 160, '#C9653A'), (1540, 260, '#C24E44'), (980, 120, '#5A8E86'))):
        fill(rrect(x, 48, w, 44, 10), col, key=f'r0{i}', tex=.4, edge=.4, outline=2.5)
    # row 1: film clips with thumbnails
    for i, (x, w) in enumerate(((-30, 560), (680, 720), (1520, 560))):
        fill(rrect(x, 158, w, 76, 12), '#3E4A62', key=f'r1{i}', tex=.35, edge=.35, outline=3)
        for q in range(int(w / 120)):
            sky = ['#B9A6D8', '#E9B88A', '#A9C6DE', '#C9B0D6'][(i + q) % 4]
            tx = x + 10 + q * 120
            fill(rect(tx, 166, 110, 60), sky, key=f'th{i}{q}', tex=.3, edge=.2)
            fill(np.array([(tx, 226), (tx + 30, 196), (tx + 55, 212), (tx + 80, 190), (tx + 110, 214), (tx + 110, 226)]), '#566C88' if q % 2 else '#4F7A6C', key=f'thm{i}{q}', tex=.2, edge=.1)
    # row 2: colour clips
    for i, (x, w, col) in enumerate(((-60, 120, '#C9883A'), (130, 600, '#5E9A78'), (1220, 420, '#E08A3A'), (1820, 300, '#5E9A78'))):
        fill(rrect(x, 298, w, 58, 14), col, key=f'r2{i}', tex=.5, edge=.4, outline=3)
    # row 3: audio waveform
    fill(rect(-1500, 418, W + 3000, 136), '#2F4C4E', key='wavebg', tex=.3, edge=0)
    for i in range(110):
        x = -40 + i * 18
        env = abs(math.sin(i * .21)) * .6 + .4 * abs(math.sin(i * .053 + 1))
        live = 1 + .35 * math.sin(t * 8 + i * .7) * (1 if abs(x - playhead_x(t)) < 220 else .2)
        h = 60 * env * live * (.6 + .4 * hash1('wv', i))
        CTX.canvas.drawLine(x, 486 - h, x, 486 + h, _ps('#7FE6C8', 230, 6))
    # keyframes
    for i, (x, y) in enumerate(((420, 130), (1080, 130), (1700, 130), (540, 390), (1600, 390), (900, 30))):
        pk = .5 + .5 * math.sin(t * 3 + i)
        P = np.array([(x, y - 22), (x + 16, y), (x, y + 22), (x - 16, y)])
        glow(x, y, 50, GOLD, .3 + .3 * pk)
        fill(P, '#F2B84E', key=f'kf{i}', tex=0, edge=.2, outline=2.5)
    # playhead
    px = playhead_x(t)
    gline([(px, 30), (px, TL_FLOOR + 10)], ORANGE, 6, key='ph')
    fill(np.array([(px - 16, 4), (px - 16, 56), (px + 26, 30)]), '#FFB45A', key='phh', tex=0, edge=.2, outline=3)
    glow(px, TL_FLOOR, 200, ORANGE, .4)
    # floor stage
    fill(np.array([(-1500, TL_FLOOR), (W + 1500, TL_FLOOR), (W + 1500, 2600), (-1500, 2600)]), '#BFA27A', key='tfl', tex=.5, edge=0, amp=.3)
    fill(np.array([(-1500, TL_FLOOR), (W + 1500, TL_FLOOR), (W + 1500, TL_FLOOR + 30), (-1500, TL_FLOOR + 30)]), '#8C7350', key='tfle', tex=.3, edge=0)
    for j in range(7):
        yy = TL_FLOOR + 30 + j ** 1.6 * 22
        CTX.canvas.drawLine(-1500, yy, W + 1500, yy, _ps('#8C7350', 140, 2))
    for i in range(-10, 11):
        x1 = 960 + i * 220
        CTX.canvas.drawLine(960 + (x1 - 960) * .45, TL_FLOOR + 30, x1 + (x1 - 960) * .8, 1400, _ps('#8C7350', 120, 2))
    # front ledges with knobs
    for side in (-1, 1):
        x0 = -200 if side < 0 else W - 360
        fill(rect(x0, 900, 560, 200), '#2E3440', key=f'led{side}', tex=.4, edge=.3, outline=3)
        for q in range(2):
            kx = x0 + 150 + q * 220
            fill(rect(kx - 40, 860, 80, 80), '#262B35', key=f'kn{side}{q}', tex=.3, edge=.3, outline=2.5)
            fill(ell(kx, 860, 40, 14, 20), '#3A4150', key=f'knt{side}{q}', tex=.2, edge=.2, outline=2)
    particles(t, 'tlp', 16, 0, 1900, 100, 1050, cols=(GOLD, TEAL, ORANGE), size=(6, 13))
