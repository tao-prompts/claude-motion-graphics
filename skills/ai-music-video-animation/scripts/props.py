# props.py — the 10 props / effects from props_2D.jpg, re-painted in code.
import math
import numpy as np
import skia
from engine import *
from chars import sparkle
from envs2 import gline, gbox

TEAL, ORANGE, LAV, GOLD, CREAM = '#5FF2D0', '#FF9A4A', '#B79CFF', '#F2C14E', '#F3EBD8'

def _xf(x, y, s, rot):
    c = CTX.canvas; c.save(); c.translate(x, y); c.rotate(math.degrees(rot)); c.scale(s, s)

# 1 KEYCAP -------------------------------------------------------------------------
def keycap(x, y, s=1.0, kind='play', col='#8EDCCB', rot=0.0, press=0.0, glowa=.6, key='kc'):
    """~180 wide at s=1. press 0..1 squashes it down"""
    _xf(x, y, s, rot)
    glow(0, 70, 150, TEAL, glowa)
    h = 60 * (1 - .5 * press)
    side = mix(col, '#2E2530', .3)
    fill(rrect(-90, -40 + 60 - h, 180, 120 - (60 - h), 24), side, key=key + 'sd', tex=.4, edge=.4, outline=4)
    fill(rrect(-74, -60 + (60 - h), 148, 100, 20), col, key=key + 'tp', tex=.45, edge=.35, outline=3.5)
    wash(rrect(-60, -50 + (60 - h), 70, 16, 8), '#FFFFFF', key=key + 'hl', a=120)
    sy = (60 - h)
    if kind == 'play':
        fill(np.array([(-18, -30 + sy), (-18, 22 + sy), (26, -4 + sy)]), '#2E3B45', key=key + 'ic', tex=0, edge=0)
    elif kind == 'enter':
        ink([(28, -30 + sy), (28, 0 + sy), (-22, 0 + sy)], 9, '#3A2A2A', key=key + 'ic', closed=False)
        fill(np.array([(-36, 0 + sy), (-18, -14 + sy), (-18, 14 + sy)]), '#3A2A2A', key=key + 'ia', tex=0, edge=0)
    CTX.canvas.restore()

# 2 CURSOR SHIP --------------------------------------------------------------------
def cursor_ship(x, y, s=1.0, rot=0.0, trail=1.0, key='cs'):
    """arrow points to the upper-right in local space; ~260 long at s=1"""
    _xf(x, y, s, rot)
    if trail > 0:
        for i, (dx, dy) in enumerate(((-120, 80), (-40, 130))):
            P = catmull([(dx, dy), (dx - 160, dy + 140), (dx - 330, dy + 300)], False, 6)
            gline(P, TEAL, 10, key=f'{key}tr{i}', a=.8 * trail)
            for q in range(5):
                gbox(dx - 60 - q * 55 + 12 * math.sin(CTX.t * 9 + q), dy + 50 + q * 50, 14 - q * 2, TEAL, trail * (1 - q / 6), key=f'{key}tp{i}{q}', glowr=1.6)
    P = np.array([(0, 0), (130, -140), (-40, -110), (10, -70), (-90, 20), (-50, 60), (40, -30)])
    P = np.array([(130, -150), (70, 40), (35, -10), (-60, 85), (-95, 50), (0, -40), (-55, -75)])
    fill(P, '#EDE7DA', key=key + 'b', tex=.5, edge=.45, outline=4.5)
    shade(np.array([(130, -150), (70, 40), (35, -10), (60, -60)]), '#B9B1A2', 140, key=key + 'sh')
    fill(ell(70, -95, 26, 18, 18, -.75), '#2E5966', key=key + 'cp', tex=.2, edge=.3, outline=3)
    wash(ell(62, -102, 9, 5, 10, -.75), '#BFF7F0', key=key + 'cph')
    for i, (ex, ey) in enumerate(((-10, 60), (-70, 0))):
        fill(ell(ex, ey, 18, 14, 14, -.75), '#7A8088', key=f'{key}e{i}', tex=.2, edge=.3, outline=3)
        glow(ex - 10, ey + 10, 50, TEAL, .8 * trail)
    CTX.canvas.restore()

# 3 PALETTE HOVERBOARD ---------------------------------------------------------------
def palette_board(x, y, s=1.0, rot=0.0, thrust=1.0, key='pb'):
    """~300 wide at s=1, (x,y) = board centre top surface"""
    _xf(x, y, s, rot)
    for i, tx in enumerate((-90, 95)):
        glow(tx, 50, 70, TEAL, .7 * thrust)
        fill(rrect(tx - 18, 14, 36, 26, 8), '#6B6F78', key=f'{key}t{i}', tex=.2, edge=.3, outline=2.5)
        if thrust > 0:
            for q in range(4):
                gbox(tx + 8 * math.sin(CTX.t * 11 + q + i), 50 + q * 22, 11 - q * 2, TEAL, thrust * (1 - q / 5), key=f'{key}tb{i}{q}', glowr=1.5)
    P = ell(0, 0, 160, 58, 40)
    fill(P, '#B98A55', key=key + 'w', tex=.6, edge=.45, outline=4)
    fill(ell(0, 14, 160, 50, 40)[12:30], '#8C5E33', key=key + 'ed', tex=.3, edge=0) if False else None
    fill(ell(108, 4, 20, 14, 16), '#3A2E30', key=key + 'hole', tex=0, edge=.2, outline=2.5)
    for i, (bx, by, col) in enumerate(((-100, -10, '#3FB59C'), (-55, -30, '#E2692A'), (-5, -36, '#D8423A'), (-40, 12, '#F2C14E'), (20, 2, '#3F6CB4'), (60, -26, '#E9DFC9'))):
        P2 = boil(ell(bx, by, 22, 13, 14), f'{key}b{i}', 2.5, True)
        fill(P2, col, key=f'{key}bl{i}', tex=.2, edge=.3, amp=.8)
    CTX.canvas.restore()

# 4 GPU POWER-UP -----------------------------------------------------------------------
def gpu_prop(x, y, s=1.0, rot=0.0, t=0.0, key='gp'):
    _xf(x, y, s, rot)
    glow(0, 0, 260, TEAL, .35)
    fill(rrect(-170, -70, 340, 140, 18), '#2C303A', key=key + 'b', tex=.4, edge=.4, outline=4)
    for f, fx in enumerate((-95, 95)):
        fill(ell(fx, 0, 56, 56, 30), '#1A1D26', key=f'{key}f{f}', tex=.2, edge=.3, outline=3)
        ang = t * 14 * (1 if f else -1)
        for b in range(6):
            a0 = ang + b * math.pi / 3
            P = [(fx + 10 * math.cos(a0), 10 * math.sin(a0)), (fx + 50 * math.cos(a0 + .3), 50 * math.sin(a0 + .3)), (fx + 48 * math.cos(a0 + .75), 48 * math.sin(a0 + .75))]
            fill(np.array(P), '#596172', key=f'{key}bl{f}{b}', tex=0, edge=.2, amp=.3, outline=1.5)
        gline(ell(fx, 0, 16, 16, 16), TEAL, 3, key=f'{key}h{f}', closed=True)
    fill(rrect(-30, -30, 60, 60, 8), '#BFFFEE', key=key + 'c', tex=.2, edge=.3, outline=3)
    glow(0, 0, 90, TEAL, .9)
    for q in range(6):
        fill(rect(-120 + q * 46, 66, 24, 14), GOLD, key=f'{key}p{q}', tex=0, edge=.2, outline=1.5)
    for i, tx in enumerate((-140, 140)):
        glow(tx, 95, 60, TEAL, .7)
        for q in range(3): gbox(tx + 6 * math.sin(t * 10 + q), 100 + q * 22, 10 - q * 2, TEAL, 1 - q / 4, key=f'{key}j{i}{q}', glowr=1.4)
    CTX.canvas.restore()

# 5 LOADING-RING PORTAL ---------------------------------------------------------------
def portal(x, y, r, t, k=1.0, key='pt', cols=(TEAL, '#A6F0DC')):
    if k <= 0: return
    r *= backOut(clamp(k), 1.4)
    glow(x, y, r * 1.9, '#9EF5DD', .55)
    # swirl
    for arm in range(3):
        P = []
        for q in range(26):
            f = q / 25
            a = t * 3 + arm * 2.094 + f * 5.5
            rr = r * .82 * (1 - f)
            P.append((x + rr * math.cos(a), y + rr * math.sin(a) * .95))
        gline(np.array(P), ['#BFFFEE', '#D8C8FF', '#FFF6D8'][arm], 9 * (1 - .3 * arm), key=f'{key}sw{arm}', a=.75)
    glow(x, y, r * .5, '#FFFBEA', .9)
    n = 11
    for i in range(n):
        a = -t * 1.6 + i * 2 * math.pi / n
        px, py = x + r * math.cos(a), y + r * math.sin(a)
        seg_ = rrect(-r * .2, -r * .1, r * .4, r * .2, r * .08)
        c = CTX.canvas; c.save(); c.translate(px, py); c.rotate(math.degrees(a + math.pi / 2))
        fill(seg_, cols[i % 2], key=f'{key}s{i}', tex=.3, edge=.4, outline=3, a=int(255 * (.55 + .45 * ((i + int(t * 8)) % n) / n)))
        c.restore()
    for i in range(10):
        a = hash1(key, i) * 6.28 + t * .5
        rr = r * (1.15 + .25 * hash1(key, 'r', i))
        gbox(x + rr * math.cos(a), y + rr * math.sin(a), 10 + 8 * hash1(key, 's', i), TEAL, .8, key=f'{key}q{i}', glowr=1.5)

# 6 FILM REEL -----------------------------------------------------------------------
def film_reel(x, y, s=1.0, t=0.0, unspool=1.0, key='fr'):
    _xf(x, y, s, 0)
    # strip: wavy ribbon from the reel
    n = int(4 + 14 * unspool)
    S = np.array([(40 + i * 34, 70 + 70 * math.sin(i * .5 - t * 3)) for i in range(n)])
    if len(S) > 2:
        S = catmull(S, False, 4)
        d = np.gradient(S, axis=0); nrm = np.stack([-d[:, 1], d[:, 0]], 1); nrm /= np.hypot(nrm[:, 0], nrm[:, 1])[:, None]
        A, B = S + nrm * 34, S - nrm * 34
        glow(S[len(S) // 2][0], S[len(S) // 2][1], 220, GOLD, .35)
        fill(np.vstack([A, B[::-1]]), '#5A4A30', key=key + 'st', tex=.3, edge=.3, outline=3)
        for q in range(2, len(S) - 2, 5):
            fx, fy = S[q]
            fill(rect(fx - 18, fy - 22, 36, 44), '#FFD98A', key=f'{key}fr{q}', tex=.2, edge=.3, a=230)
    fill(ell(0, 0, 110, 110, 40), '#8C8F96', key=key + 'r', tex=.4, edge=.4, outline=4)
    fill(ell(0, 0, 90, 90, 36), '#6B6E76', key=key + 'r2', tex=.3, edge=.2)
    ang = t * 2
    for h in range(5):
        a = ang + h * 2 * math.pi / 5
        fill(ell(52 * math.cos(a), 52 * math.sin(a), 22, 22, 16), '#2E2B33', key=f'{key}h{h}', tex=0, edge=.2, outline=2)
    fill(ell(0, 0, 14, 14, 14), '#2E2B33', key=key + 'hub', tex=0, edge=0, outline=2)
    CTX.canvas.restore()

# 7 DATA CUBE CHEST -----------------------------------------------------------------
def data_chest(x, y, s=1.0, t=0.0, open_=1.0, key='dc'):
    _xf(x, y, s, 0)
    glow(0, -80, 260 * (.4 + open_), GOLD, .5 * open_)
    for i in range(int(14 * open_)):
        ph = ((t * .8 + hash1(key, i)) % 1.0)
        px = (hash1(key, 'x', i) - .5) * 180; py = -60 - ph * 260
        gbox(px, py, 18 + 10 * hash1(key, 's', i), [GOLD, TEAL, '#FFE9A8'][i % 3], (1 - ph) * open_, key=f'{key}q{i}')
    # walls (front open box)
    fill(np.array([(-130, -40), (130, -40), (120, 90), (-120, 90)]), '#2E3038', key=key + 'f', tex=.4, edge=.4, outline=4)
    fill(np.array([(-130, -40), (-130 - 60 * open_, -150), (-100 - 40 * open_, -160), (-100, -40)]), '#3A3D47', key=key + 'l', tex=.3, edge=.3, outline=3)
    fill(np.array([(130, -40), (130 + 60 * open_, -150), (100 + 40 * open_, -160), (100, -40)]), '#3A3D47', key=key + 'r', tex=.3, edge=.3, outline=3)
    for i, (gx, gy) in enumerate(((-60, 25), (60, 25))):
        fill(np.array([(gx, gy - 26), (gx + 20, gy), (gx, gy + 26), (gx - 20, gy)]), GOLD, key=f'{key}g{i}', tex=0, edge=.2, outline=2)
        glow(gx, gy, 50, GOLD, .7)
    CTX.canvas.restore()

# 8 INK SPLASH BURST ----------------------------------------------------------------
def ink_splash(x, y, s, k, key='is', col='#E8792F'):
    """k 0..1: splat expands quickly then droplets fly and fade"""
    if k <= 0 or k >= 1: return
    e = easeOut(clamp(k * 2.2)); fade = 1 - clamp((k - .6) / .4)
    a = int(255 * fade)
    P = []
    for i in range(18):
        ang = i * 2 * math.pi / 18
        rr = (60 + 110 * hash1(key, 'arm', i) * (i % 2)) * e * s
        P.append((x + rr * math.cos(ang), y + rr * math.sin(ang) * .85))
    fill(catmull(P, True, 4), col, key=key + 'core', tex=.5, edge=.5, outline=3 * s, a=a)
    wash(ell(x, y, 40 * e * s, 30 * e * s, 16), '#FFC27A', key=key + 'hl', a=int(160 * fade))
    for i in range(16):
        ang = hash1(key, 'a', i) * 2 * math.pi
        d = (150 + 260 * hash1(key, 'd', i)) * easeOut(k) * s
        r_ = (8 + 18 * hash1(key, 'r', i)) * s * (1 - k * .5)
        dx, dy = x + d * math.cos(ang), y + d * math.sin(ang) + 120 * k * k * s
        P = np.array([(dx - math.cos(ang) * r_ * 2, dy - math.sin(ang) * r_ * 2)])
        fill(ell(dx, dy, r_ * 1.3, r_, 14, ang), col, key=f'{key}d{i}', tex=0, edge=.3, outline=2, a=a)

# 9 PIXEL FIREWORK ------------------------------------------------------------------
def pixel_firework(x, y, s, k, key='pf', cols=(TEAL, LAV, '#A6F0DC')):
    if k <= 0 or k >= 1: return
    fade = 1 - clamp((k - .5) / .5)
    glow(x, y, 260 * s * easeOut(k), '#FFFFFF', .5 * fade)
    for i in range(30):
        ang = i * 2 * math.pi / 30 + hash1(key, i) * .2
        d = (120 + 220 * hash1(key, 'd', i)) * easeOut(k) * s
        px, py = x + d * math.cos(ang), y + d * math.sin(ang) + 80 * k * k * s
        if i % 3 == 0:
            gline([(x + d * .55 * math.cos(ang), y + d * .55 * math.sin(ang)), (px, py)], cols[i % 3], 3 * s, key=f'{key}l{i}', a=fade)
        gbox(px, py, (14 + 10 * hash1(key, 's', i)) * s * (1 - .4 * k), cols[i % 3], fade, key=f'{key}b{i}')
    for i in range(6):
        ang = hash1(key, 'sa', i) * 6.28; d = 200 * s * easeOut(k) * (.6 + .6 * hash1(key, 'sd', i))
        sparkle(x + d * math.cos(ang), y + d * math.sin(ang), 30 * s * fade, f'{key}sp{i}', GOLD)

# 10 LIGHT RIBBON -------------------------------------------------------------------
def light_ribbon(x, y, rx, ry, t, k=1.0, key='lr', tilt=0.0):
    """a looping figure-eight ribbon, orange -> teal, drawing on with k"""
    if k <= 0: return
    n = 60
    pts = []
    for i in range(int(n * clamp(k)) + 1):
        f = i / n * 2 * math.pi + t * 1.5
        px = x + rx * math.sin(f)
        py = y + ry * math.sin(2 * f) * .5
        c_, s_ = math.cos(tilt), math.sin(tilt)
        pts.append((x + (px - x) * c_ - (py - y) * s_, y + (px - x) * s_ + (py - y) * c_))
    if len(pts) < 3: return
    P = np.array(pts)
    h = len(P) // 2
    gline(P[:h + 1], ORANGE, 12, key=key + 'a')
    gline(P[h:], TEAL, 12, key=key + 'b')
    for q in range(5):
        i = int((q / 5 + t * .3) % 1 * (len(P) - 1))
        sparkle(P[i][0], P[i][1] - 10, 18 + 6 * math.sin(t * 8 + q), f'{key}s{q}', '#FFF0B0')

# ---- digital ride platforms (v5) ------------------------------------------------
def code_board(x, y, s=1.0, rot=0.0, thrust=1.0, key='cb'):
    """Brush's ride: a floating orange code block '{ }' with glowing edges and pixel jets. ~300 wide at s=1"""
    _xf(x, y, s, rot)
    t = CTX.t
    for i, tx in enumerate((-95, 0, 95)):
        glow(tx, 46, 70, ORANGE, .55 * thrust)
        if thrust > 0:
            for q in range(4):
                gbox(tx + 7 * math.sin(t * 13 + q + i), 40 + q * 20, 11 - q * 2, ORANGE if q % 2 else '#FFD66B', thrust * (1 - q / 5), key=f'{key}j{i}{q}', glowr=1.5)
    glow(0, 0, 230, ORANGE, .35)
    body = rrect(-150, -26, 300, 52, 22)
    fill(body, '#2A2140', key=key + 'b', tex=.3, edge=.3, outline=4)
    gline(body, ORANGE, 5, key=key + 'e', closed=True)
    # side face (gives it thickness)
    fill(rrect(-146, 14, 292, 22, 10), '#1C1630', key=key + 's', tex=.2, edge=.2, outline=3)
    # glyphs on top: { } and code dashes
    for sx, ch in ((-110, '{'), (110, '}')):
        P = catmull([(sx + (10 if ch == '{' else -10), -16), (sx, -8), (sx - (8 if ch == '{' else -8), 0), (sx, 8), (sx + (10 if ch == '{' else -10), 16)], False, 4)
        gline(P, '#FFD66B', 4, key=f'{key}g{ch}')
    for q, (lx, ln, col) in enumerate(((-80, 60, TEAL), (-12, 40, ORANGE), (36, 46, LAV))):
        fill(rrect(lx, -6, ln, 12, 6), col, key=f'{key}d{q}', tex=0, edge=0)
    CTX.canvas.restore()

def halo_disc(x, y, s=1.0, thrust=1.0, key='hd'):
    """Render's ride: a glowing teal hover disc (a big halo) with pixel jets. ~280 wide at s=1"""
    _xf(x, y, s, 0)
    t = CTX.t
    glow(0, 10, 260, TEAL, .55)
    for i in range(7):
        a_ = i * 2 * math.pi / 7 + t * 2
        jx = 110 * math.cos(a_)
        if math.sin(a_) < 0: continue
        for q in range(3):
            gbox(jx + 5 * math.sin(t * 11 + q + i), 30 + q * 20, 10 - q * 2, TEAL, thrust * (1 - q / 4), key=f'{key}j{i}{q}', glowr=1.5)
    fill(ell(0, 0, 140, 36, 40), '#1E3A4A', key=key + 'b', tex=.3, edge=.3, a=220, outline=3.5)
    gline(ell(0, 0, 140, 36, 48), TEAL, 6, key=key + 'r', closed=True)
    gline(ell(0, 0, 96, 24, 40), '#C9F7EA', 3, key=key + 'r2', closed=True, a=.7)
    for i in range(9):
        a_ = i * 2 * math.pi / 9 - t * 3
        gbox(125 * math.cos(a_), 32 * math.sin(a_), 12, '#C9F7EA', .9, key=f'{key}o{i}', glowr=1.4)
    CTX.canvas.restore()
