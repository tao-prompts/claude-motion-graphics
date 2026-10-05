# chars.py — Brush (walking paintbrush) and Render (AI blob), drawn from parameters every frame.
import math
import numpy as np
import skia
from engine import *

C = dict(
    wood='#C99A5B', woodDk='#9C6E3C', woodLt='#E6C28C',
    fer='#BDBBB4', ferDk='#8C8A84', ferLt='#ECEAE2',
    bri='#E2692A', briDk='#B4461C', briLt='#F29A55', briBase='#E9CFA2',
    limb='#7A5232', foot='#6B4628',
    teal='#86DCC3', tealDk='#4DB39A', tealLt='#C4F2E3', halo='#5DCBB2',
    blush='#F3A3A0', eye='#2A2230', white='#FFFDF6',
)

def _dir(a): return (math.sin(a), -math.cos(a))

def _rot(P, a, ox=0, oy=0):
    P = np.asarray(P, np.float64); c, s = math.cos(a), math.sin(a)
    x, y = P[:, 0] - ox, P[:, 1] - oy
    return np.stack([ox + x * c - y * s, oy + x * s + y * c], 1)

def _tr(P, x, y): P = np.asarray(P, np.float64); return P + np.array([x, y])

def shadow(x, y, rx, ry, a=70):
    shade(ell(x, y, rx, ry, 28), '#6A5A70', a, key=f'shd{int(x)}', blur=6)

# ================================================================ shared face parts
def eye_shape(kind, x, y, s, key, lookX=0, lookY=0, blink=0.0, big=False, flip=1):
    """s = eye height unit. big=True -> Render-style glossy eyes"""
    c = CTX.canvas
    lw = max(1.4, s * .16)
    if blink > .85 and kind not in ('happy', 'closed', 'x', 'heart', 'star'): kind = 'closed'
    if kind == 'happy':
        P = [(x - s * .55, y + s * .2), (x, y - s * .45), (x + s * .55, y + s * .2)]
        ink(catmull(P, False, 8), lw * 1.5, key=key, closed=False, amp=.4)
        return
    if kind == 'closed':
        P = [(x - s * .5, y), (x, y + s * .28), (x + s * .5, y)]
        ink(catmull(P, False, 8), lw * 1.4, key=key, closed=False, amp=.4)
        return
    if kind == 'x':
        for sg in (1, -1):
            ink([(x - s * .4, y - s * .4 * sg), (x + s * .4, y + s * .4 * sg)], lw * 1.3, key=key + str(sg), closed=False, amp=.3)
        return
    if kind == 'heart':
        hp = heart_pts(x, y, s * .62)
        fill(hp, '#E8566C', key=key, tex=.2, edge=.2, amp=.4, outline=lw * .8)
        return
    if kind == 'star':
        fill(star_pts(x, y, s * .75, .45, 5), '#F6C945', key=key, tex=.1, edge=.1, amp=.3, outline=lw * .8)
        return
    rx, ry = (s * .42, s * .55) if big else (s * .26, s * .5)
    if kind == 'wide': rx, ry = rx * 1.25, ry * 1.2
    if kind in ('angry', 'sad', 'narrow'): ry *= .8
    ry *= (1 - clamp(blink) * .9)
    ex, ey = x + lookX * s * .18, y + lookY * s * .14
    fill(ell(ex, ey, rx, ry, 24), C['eye'], key=key, tex=0, edge=0, amp=.3)
    if big or kind == 'wide':
        wash(ell(ex - rx * .32 * flip, ey - ry * .38, rx * .34, ry * .28, 14), C['white'], key=key + 'h')
        wash(ell(ex + rx * .3 * flip, ey + ry * .35, rx * .15, ry * .13, 10), C['white'], key=key + 'h2')
    else:
        wash(ell(ex - rx * .25, ey - ry * .45, rx * .32, ry * .2, 10), C['white'], key=key + 'h', a=200)

def brow(kind, x, y, s, side, key):
    if not kind: return
    # side: -1 left eye, +1 right eye (screen)
    if kind == 'angry': a, b = (x - s * .45 * side, y - s * .25), (x + s * .4 * side, y + s * .15)
    elif kind == 'sad': a, b = (x - s * .45 * side, y + s * .1), (x + s * .4 * side, y - s * .25)
    else: a, b = (x - s * .45, y - s * .08), (x + s * .45, y - s * .08)
    ink([a, b], max(1.6, s * .2), key=key, closed=False, amp=.3)

CLOSED_MOUTHS = False
def mouth_shape(kind, x, y, s, key, openk=0.0):
    if CLOSED_MOUTHS:
        openk = 0.0
        if kind in ('open', 'O', 'wail'): kind = 'smile'
    lw = max(1.4, s * .15)
    if openk > .05 or kind in ('open', 'O', 'wail'):
        k = max(openk, .5 if kind == 'open' else .7 if kind == 'O' else .9)
        w = s * (.42 if kind != 'O' else .3) * (0.9 + .2 * k)
        h = s * (.12 + .45 * k)
        P = ell(x, y + h * .35, w, h, 22)
        fill(P, '#7A2A35', key=key, tex=0, edge=.2, amp=.3, outline=lw * .9)
        wash(ell(x, y + h * .35 + h * .45, w * .55, h * .35, 14), '#E8707E', key=key + 't')
        return
    if kind in ('smile', 'grin', None):
        P = [(x - s * .4, y - s * .05), (x, y + s * .22), (x + s * .4, y - s * .05)]
        ink(catmull(P, False, 8), lw, key=key, closed=False, amp=.3)
    elif kind == 'frown':
        P = [(x - s * .35, y + s * .15), (x, y - s * .1), (x + s * .35, y + s * .15)]
        ink(catmull(P, False, 8), lw, key=key, closed=False, amp=.3)
    elif kind == 'flat':
        ink([(x - s * .3, y), (x + s * .3, y)], lw, key=key, closed=False, amp=.3)
    elif kind == 'smirk':
        P = [(x - s * .35, y + s * .05), (x + s * .1, y + s * .08), (x + s * .38, y - s * .15)]
        ink(catmull(P, False, 8), lw, key=key, closed=False, amp=.3)
    elif kind == 'wobble':
        P = [(x - s * .4, y), (x - s * .2, y - s * .1), (x, y + s * .05), (x + s * .2, y - s * .1), (x + s * .4, y)]
        ink(catmull(P, False, 6), lw, key=key, closed=False, amp=.3)

def heart_pts(cx, cy, r, n=40):
    a = np.linspace(0, 2 * np.pi, n, endpoint=False)
    x = 16 * np.sin(a) ** 3
    y = -(13 * np.cos(a) - 5 * np.cos(2 * a) - 2 * np.cos(3 * a) - np.cos(4 * a))
    return np.stack([cx + x * r / 16, cy + y * r / 16], 1)

def star_pts(cx, cy, r, inner=.45, n=5, rot=0.0):
    P = []
    for i in range(n * 2):
        a = rot - math.pi / 2 + i * math.pi / n; rr = r if i % 2 == 0 else r * inner
        P.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return np.array(P)

def sparkle(x, y, r, key, col='#F6D45A', a=255):
    P = []
    for i in range(8):
        ang = -math.pi / 2 + i * math.pi / 4; rr = r if i % 2 == 0 else r * .22
        P.append((x + rr * math.cos(ang), y + rr * math.sin(ang)))
    fill(np.array(P), col, key=key, tex=0, edge=0, amp=.3, a=a, outline=max(1.2, r * .07))

def emote(kind, x, y, s, k=1.0, age=0.0, key='em'):
    """painted reaction marks. k = pop 0..1"""
    if k <= 0: return
    sc = backOut(k) * s
    if kind == 'hearts':
        for i, (dx, dy, rr) in enumerate(((0, 0, 1), (1.1, -.9, .65), (-.8, -1.3, .5))):
            yy = y + dy * sc - (age * 30 % 40) * (i * .3)
            fill(heart_pts(x + dx * sc, yy, rr * sc * .6), '#E8566C', key=f'{key}h{i}', tex=.1, edge=.15, amp=.5, outline=2)
    elif kind == 'spark':
        sparkle(x, y, sc * .9, key + 'a'); sparkle(x + sc * .9, y + sc * .7, sc * .45, key + 'b')
    elif kind == 'excl':
        fill(np.array([(x - sc * .18, y - sc), (x + sc * .22, y - sc), (x + sc * .08, y + sc * .25), (x - sc * .08, y + sc * .25)]),
             '#F2B33D', key=key, tex=0, edge=.1, outline=2.5)
        fill(ell(x, y + sc * .55, sc * .14, sc * .14, 12), '#F2B33D', key=key + 'd', tex=0, edge=0, outline=2.5)
    elif kind == 'sweat':
        P = np.array([(x, y - sc * .6), (x + sc * .3, y), (x + sc * .25, y + sc * .25), (x, y + sc * .38), (x - sc * .25, y + sc * .25), (x - sc * .3, y)])
        fill(catmull(P, True, 5), '#8EC8EE', key=key, tex=0, edge=.1, outline=2)
    elif kind == 'music':
        for i in range(2):
            xx, yy = x + i * sc * .9, y - i * sc * .4 + math.sin(age * 6 + i) * 6
            col = ('#5FF2D0', '#FF9A4A')[i]
            glow(xx + sc * .2, yy - sc * .3, sc * 1.1, col, .8)
            ink([(xx + sc * .2, yy), (xx + sc * .2, yy - sc * .8), (xx + sc * .55, yy - sc * .62)], sc * .16, INK, key=f'{key}so{i}', closed=False)
            ink([(xx + sc * .2, yy), (xx + sc * .2, yy - sc * .8), (xx + sc * .55, yy - sc * .62)], sc * .09, col, key=f'{key}s{i}', closed=False)
            fill(ell(xx, yy, sc * .26, sc * .19, 14, -.4), col, key=f'{key}n{i}', tex=0, edge=.2, outline=max(2, sc * .05))
            wash(ell(xx - sc * .07, yy - sc * .06, sc * .08, sc * .05, 8), '#FFFFFF', key=f'{key}nh{i}', a=200)
    elif kind == 'q':
        P = [(x - sc * .3, y - sc * .5), (x, y - sc * .8), (x + sc * .35, y - sc * .5), (x, y - sc * .1), (x, y + sc * .15)]
        ink(catmull(P, False, 8), sc * .16, '#6D86BE', key=key, closed=False)
        fill(ell(x, y + sc * .45, sc * .1, sc * .1, 10), '#6D86BE', key=key + 'd', tex=0, edge=0)
    elif kind == 'anger':
        for i in range(4):
            a = i * math.pi / 2 + math.pi / 4
            P = [(x + math.cos(a) * sc * .15, y + math.sin(a) * sc * .15), (x + math.cos(a) * sc * .55, y + math.sin(a) * sc * .55)]
            ink(catmull([P[0], ((P[0][0] + P[1][0]) / 2 + math.cos(a + 1.2) * sc * .15, (P[0][1] + P[1][1]) / 2 + math.sin(a + 1.2) * sc * .15), P[1]], False, 6),
                sc * .14, '#D8423A', key=f'{key}{i}', closed=False)

# ================================================================ BRUSH
def brush(x, y, u, o=None):
    """(x,y) ground point between the feet; u unit (total height ~19.5u)."""
    o = o or {}
    t = CTX.t
    key = o.get('key', 'B')
    c = CTX.canvas
    sq = o.get('sq', 0.0)
    rot = o.get('rot', 0.0)
    bend = o.get('bend', 0.0)
    head = o.get('head', 0.0)  # heading turns, 0 front, +.25 right
    flipH = math.sin(head * 2 * math.pi)
    front = math.cos(head * 2 * math.pi)
    x += o.get('dx', 0) * u; y += o.get('dy', 0) * u
    hop = o.get('lift', 0.0) * u  # feet off the ground
    if not o.get('noShadow'):
        shadow(x, y + u * .15, u * 2.6 * (1 - min(.5, hop / (u * 10))), u * .55, 60)
    y -= hop
    sw = max(2.0, u * .17)  # outline

    # ---- legs + feet
    walk = o.get('walk')
    hipY = y - 3.0 * u * (1 - sq * .6)
    base = (x, hipY)
    legs = []
    for i, side in enumerate((-1, 1)):
        fx = x + side * .85 * u + o.get('spread', 0) * side * u
        fy = y
        if walk is not None:
            ph = (walk + i * .5) % 1.0
            swing = math.cos(ph * 2 * math.pi)
            fx += swing * 1.1 * u * (1 if flipH >= 0 else -1) * min(1, abs(flipH) * 2 + .3)
            if ph < .5: fy -= math.sin(ph * 2 * math.pi) * 1.0 * u
        fx += o.get('footL' if side < 0 else 'footR', (0, 0))[0] * u
        fy += o.get('footL' if side < 0 else 'footR', (0, 0))[1] * u
        hx = x + side * .42 * u
        legs.append(((hx, hipY + .3 * u), (fx, fy), side))
    for (h0, f, side) in legs:
        mid = ((h0[0] + f[0]) / 2 + side * .25 * u, (h0[1] + f[1]) / 2)
        P = catmull([h0, mid, (f[0], f[1] - .25 * u)], False, 8)
        _limb(P, u, key + f'leg{side}')
    for (h0, f, side) in legs:
        toe = side if abs(flipH) < .5 else (1 if flipH > 0 else -1)
        fill(ell(f[0] + toe * .3 * u, f[1] - .22 * u, .72 * u, .33 * u, 22), C['foot'], key=key + f'ft{side}', tex=.3, edge=.3, amp=.6, outline=sw * .8)

    # ---- spine
    L = 8.7 * u * (1 - sq) * o.get('stretch', 1.0)
    a0 = rot
    bx, by = base
    mx, my = bx + _dir(a0)[0] * L * .5, by + _dir(a0)[1] * L * .5
    a1 = rot + bend
    tx, ty = mx + _dir(a1)[0] * L * .5, my + _dir(a1)[1] * L * .5
    def spine(s):
        q = 1 - s
        return (q * q * bx + 2 * q * s * mx + s * s * tx, q * q * by + 2 * q * s * my + s * s * ty)
    S = np.array([spine(s) for s in np.linspace(0, 1, 18)])
    d = np.gradient(S, axis=0); nrm = np.stack([-d[:, 1], d[:, 0]], 1); nrm /= np.hypot(nrm[:, 0], nrm[:, 1])[:, None]
    s = np.linspace(0, 1, 18)
    wid = np.interp(s, [0, .3, .7, 1], [1.5, 1.85, 1.65, 1.45]) * u * (1 + sq * .4)
    A = S + nrm * (wid / 2)[:, None]; B = S - nrm * (wid / 2)[:, None]
    # rounded bottom cap
    ang0 = math.atan2(nrm[0, 1], nrm[0, 0])
    cap = [(S[0, 0] + math.cos(ang0 + k) * wid[0] / 2, S[0, 1] + math.sin(ang0 + k) * wid[0] / 2) for k in np.linspace(0, math.pi, 9)]
    # cap goes from A side around the bottom to B side; direction of spine is up so bottom = -tangent side
    tang = d[0] / np.hypot(*d[0])
    capP = []
    for k in np.linspace(0, math.pi, 9):
        v = np.array([nrm[0, 0], nrm[0, 1]]) * math.cos(k) - tang * math.sin(k)
        capP.append(S[0] + v * wid[0] / 2)
    handle = np.vstack([A[::-1], np.array(capP), B])  # top-A ... bottom ... B-top
    # arms behind? (far arm when turned)
    arms = _arms(o, S, nrm, wid, u, key, flipH)
    if abs(flipH) > .6:
        _draw_arm(arms[0 if flipH > 0 else 1], u, sw, o, key)
    fill(handle, C['wood'], key=key + 'hd', tex=.6, edge=.45, amp=.5, outline=sw)
    # shading strip + grain
    sh = S - nrm * (wid * (.25 - .2 * flipH))[:, None]
    shade(np.vstack([sh, (S - nrm * (wid / 2 - 2)[:, None])[::-1]]), C['woodDk'], 110, key=key + 'hs')
    for gi, off in enumerate((.12, -.05)):
        G = (S + nrm * (wid * (off + .15 * flipH))[:, None])[2:14]
        ink(G, sw * .35, C['woodDk'], key=key + f'gr{gi}', closed=False, amp=.6, a=170)

    # ---- ferrule + face + bristles in top frame
    ta = math.atan2(d[-1, 0], -d[-1, 1])  # angle from vertical
    c.save(); c.translate(tx, ty); c.rotate(math.degrees(ta))
    fw0, fw1, fh = 2.75 * u * (1 + sq * .3), 2.9 * u * (1 + sq * .3), 3.8 * u * (1 - sq * .5)
    fer = np.array([(-fw0 / 2, .15 * u), (fw0 / 2, .15 * u), (fw1 / 2, -fh), (-fw1 / 2, -fh)])
    fill(fer, C['fer'], key=key + 'fe', tex=.35, edge=.4, amp=.4)
    hx = (-.55 - .35 * flipH) * u
    wash(np.array([(hx - .18 * u, -.1 * u), (hx + .18 * u, -.1 * u), (hx + .18 * u, -fh + .2 * u), (hx - .18 * u, -fh + .2 * u)]), C['ferLt'], key=key + 'fl', a=200)
    shade(np.array([(fw0 * (.25 - .15 * flipH), .1 * u), (fw0 / 2, .1 * u), (fw1 / 2, -fh), (fw1 * (.25 - .15 * flipH), -fh)]), C['ferDk'], 120, key=key + 'fd')
    ink(fer, sw, key=key + 'feo')
    for cy in (-.42 * u, -fh + .42 * u):
        ink([(-fw0 / 2 + 2, cy), (fw0 / 2 - 2, cy)], sw * .5, C['ferDk'], key=key + f'cr{cy:.0f}', closed=False, amp=.4)

    # face
    if front > -.25 and not o.get('noFace'):
        fs = u * 1.0  # face unit
        fx = flipH * .7 * u
        sp = .56 * u * (.55 + .45 * abs(front))
        ey = -fh * .62
        blink = _blink(t, o.get('seed', 1.3))
        ek = o.get('eyes', 'dot')
        lx, ly = o.get('lookX', 0), o.get('lookY', 0)
        for side in (-1, 1):
            ek2 = ek[0 if side < 0 else 1] if isinstance(ek, (list, tuple)) else ek
            eye_shape(ek2, fx + side * sp, ey, fs * 1.0, key + f'e{side}', lx, ly, blink)
            brow(o.get('brows'), fx + side * sp, ey - .72 * u, fs * .75, side, key + f'b{side}')
        mouth_shape(o.get('mouth', 'smile'), fx, ey + 1.15 * u, fs * 1.0, key + 'm', o.get('mouthOpen', 0.0))
        if o.get('blush', 0) > 0:
            for side in (-1, 1):
                shade(ell(fx + side * .8 * u, ey + .55 * u, .3 * u, .14 * u, 14), '#E88A86', int(160 * o['blush']), key=key + f'bl{side}', blur=2)

    # bristles
    c.save(); c.translate(0, -fh + .1 * u)
    sway = o.get('hair', 0.0) + .12 * math.sin(t * 2.3 + o.get('seed', 1.3))
    _bristles(u, sw, sway, key, o)
    c.restore()
    c.restore()

    if abs(flipH) > .6:
        _draw_arm(arms[1 if flipH > 0 else 0], u, sw, o, key)
    else:
        for a in arms: _draw_arm(a, u, sw, o, key)
    return dict(top=(tx, ty), base=base, hands=[a['hand'] for a in arms], spine=S)

def _blink(t, seed):
    period = 3.1 + seed % 1.7
    ph = (t + seed * 1.37) % period
    return clamp(1 - abs(ph - .08) / .08) if ph < .16 else 0.0

def _limb(P, u, key, col=None):
    """thin noodle limb with ink outline"""
    c = CTX.canvas
    D = boil(densify(P, False, 5), key, .25 * u * .1 + .6, False)
    c.drawPath(ribbon(D, .58 * u, .55 * u, key=key + 'o', var=.12), skia.Paint(AntiAlias=True, Color=hexc(INK)))
    c.drawPath(ribbon(D, .3 * u, .28 * u, key=key + 'i', var=.1), skia.Paint(AntiAlias=True, Color=hexc(col or C['limb'])))

def _arms(o, S, nrm, wid, u, key, flipH):
    out = []
    si = 13  # shoulder index on spine
    for side, akey in ((-1, 'aL'), (1, 'aR')):
        sh = S[si] + nrm[si] * (wid[si] / 2 * .85) * (-side if nrm[si][0] < 0 else side) * 1
        # make sure 'side' -1 is screen-left
        sh = np.array([S[si][0] + side * wid[si] * .42, S[si][1]])
        a = o.get(akey, -1.15)
        ln = o.get('armLen', 4.3) * u
        hand = (sh[0] + side * math.cos(a) * ln, sh[1] - math.sin(a) * ln)
        if o.get(akey + 'pos') is not None: hand = o[akey + 'pos']
        bendA = o.get(akey + 'bend', .35)
        mx, my = (sh[0] + hand[0]) / 2, (sh[1] + hand[1]) / 2
        dx, dy = hand[0] - sh[0], hand[1] - sh[1]; Lh = math.hypot(dx, dy) + 1e-6
        # elbow offset perpendicular (droop)
        px, py = -dy / Lh, dx / Lh
        if py < 0: px, py = -px, -py
        el = (mx + px * bendA * u, my + py * bendA * u)
        out.append(dict(P=catmull([tuple(sh), el, hand], False, 8), hand=hand, side=side, ang=a, key=akey))
    return out

def _draw_arm(a, u, sw, o, key):
    _limb(a['P'], u, key + a['key'])
    hx, hy = a['hand']
    d = a['P'][-1] - a['P'][-3]; ang = math.atan2(d[1], d[0])
    fill(ell(hx + math.cos(ang) * .2 * u, hy + math.sin(ang) * .2 * u, .48 * u, .4 * u, 20, ang), C['foot'], key=key + a['key'] + 'h', tex=.3, edge=.3, amp=.5, outline=sw * .75)
    hook = o.get(a['key'] + 'hook')
    if hook: hook(hx, hy, ang)

def _bristles(u, sw, sway, key, o):
    """local frame: y=0 at ferrule top, up negative"""
    bw = 1.5 * u
    tipx = sway * 2.2 * u
    P = [(-bw, .2 * u), (-bw * 1.28, -1.3 * u), (-bw * 1.3, -2.9 * u), (-bw * 1.05 + tipx * .3, -4.3 * u),
         (-bw * .95 + tipx * .5, -5.3 * u), (-bw * .45 + tipx * .5, -4.6 * u), (-.1 * u + tipx * .8, -5.9 * u),
         (tipx + .9 * u, -6.7 * u), (.55 * u + tipx * .65, -5.0 * u), (bw * .7 + tipx * .7, -5.6 * u),
         (bw * 1.0 + tipx * .4, -4.0 * u), (bw * 1.32, -2.5 * u), (bw * 1.2, -1.0 * u), (bw, .2 * u)]
    P = catmull(P, True, 6)
    fill(P, C['bri'], key=key + 'br', tex=.5, edge=.5, amp=.9)
    # lighter base where the bristles are clean
    base = catmull([(-bw * 1.02, .25 * u), (-bw * 1.2, -.9 * u), (0, -1.2 * u + .1 * u), (bw * 1.15, -.8 * u), (bw * 1.02, .25 * u)], True, 6)
    c = CTX.canvas
    c.save(); c.clipPath(topath(P), doAntiAlias=True)
    fill(base, C['briBase'], key=key + 'bb', tex=.3, edge=.25, amp=.8)
    for i in range(6):
        xx = -bw + (i + .5) * 2 * bw / 6
        Q = [(xx, -.8 * u), (xx + tipx * .25 + (i - 2.5) * .12 * u, -3.0 * u), (xx * .6 + tipx * .7, -5.0 * u)]
        ink(catmull(Q, False, 6), sw * .45, C['briDk'], key=key + f'bs{i}', closed=False, a=200)
    c.restore()
    ink(P, sw, key=key + 'bro')
    # paint drip on the right
    dk = o.get('drip', 1.0)
    if dk > 0:
        dy = (.9 + .5 * (math.sin(CTX.t * 1.7) * .5 + .5)) * u * dk
        dx = bw * 1.3
        ink([(dx - .1 * u, -1.6 * u), (dx, -1.6 * u + dy * .6)], sw * 1.8, C['bri'], key=key + 'dr', closed=False, amp=.3)
        drop = catmull([(dx, -1.6 * u + dy * .45), (dx + .32 * u, -1.6 * u + dy + .15 * u), (dx, -1.6 * u + dy + .45 * u), (dx - .32 * u, -1.6 * u + dy + .15 * u)], True, 5)
        fill(drop, C['bri'], key=key + 'dd', tex=0, edge=.2, amp=.3, outline=sw * .7)

# ================================================================ RENDER
def blob_pts(u, sq=0.0, n=60, lean=0.0):
    pts = []
    for k in range(n):
        th = 2 * math.pi * k / n
        cx, sn = math.cos(th), math.sin(th)
        if sn < 0:  # top dome
            px = 3.45 * u * cx * (1 + .03 * sn)
            py = -2.75 * u + 3.45 * u * sn
        else:  # bottom: flat-ish
            px = 3.55 * u * math.copysign(abs(cx) ** .8, cx)
            py = -2.75 * u + 2.75 * u * (sn ** .38)
        px += lean * (py / (-6.2 * u)) * u * 1.2
        pts.append((px, py))
    P = np.array(pts)
    P[:, 0] *= (1 + sq * .55)
    P[:, 1] *= (1 - sq)
    return P

def render_bot(x, y, u, o=None):
    """Render: gumdrop blob. (x,y) ground point. ~6.2u tall, halo above."""
    o = o or {}
    t = CTX.t
    key = o.get('key', 'R')
    c = CTX.canvas
    sq = o.get('sq', 0.0)
    head = o.get('head', 0.0)
    flipH = math.sin(head * 2 * math.pi); front = math.cos(head * 2 * math.pi)
    lift = o.get('lift', 0.0) * u
    x += o.get('dx', 0) * u; y += o.get('dy', 0) * u
    sw = max(2.0, u * .19)
    if not o.get('noShadow'):
        shadow(x, y + u * .2, u * 3.4 * (1 - min(.6, lift / (u * 12))), u * .7, 60)
    yb = y - lift
    rot = o.get('rot', 0.0)
    c.save(); c.translate(x, yb); c.rotate(math.degrees(rot))
    mat = o.get('mat', 1.0)  # materialise 0..1
    P = blob_pts(u, sq, lean=o.get('lean', 0.0))
    top = -6.2 * u * (1 - sq)
    # glow
    if o.get('glow', .35) > 0: glow(0, top * .5, 6 * u, '#6FE0C4', o.get('glow', .35) * mat)
    # arms (behind-ish, nubs at sides)
    for side, akey in ((-1, 'aL'), (1, 'aR')):
        a = o.get(akey, -.6)
        sx, sy = side * 3.25 * u * (1 + sq * .55), -2.2 * u * (1 - sq)
        ln = 1.5 * u
        ex, ey = sx + side * math.cos(a) * ln, sy - math.sin(a) * ln
        arm = catmull([(sx - side * .3 * u, sy + .1 * u), ((sx + ex) / 2, (sy + ey) / 2 + .1 * u), (ex, ey)], False, 6)
        if mat > .5:
            D = boil(densify(arm, False, 4), key + akey, .5, False)
            c.drawPath(ribbon(D, 1.25 * u, 1.0 * u, key=key + akey + 'o', var=.08), skia.Paint(AntiAlias=True, Color=hexc(INK)))
            c.drawPath(ribbon(D, .9 * u, .68 * u, key=key + akey + 'i', var=.08), skia.Paint(AntiAlias=True, Color=hexc(C['teal'])))
            hk = o.get(akey + 'hook')
            if hk: hk(*_xf(c, ex, ey))
    if mat >= .999:
        fill(P, C['teal'], key=key + 'body', tex=.28, edge=.45, amp=.6)
        cc = CTX.canvas
        cc.save(); cc.clipPath(topath(P), doAntiAlias=True)
        # inner light + bottom shade + spots
        wash(ell(-1.0 * u - flipH * u, top * .62, 2.0 * u, 1.6 * u, 24, -.3), C['tealLt'], key=key + 'il', a=150)
        shade(ell(0, -.2 * u, 4.2 * u, 1.6 * u, 24), C['tealDk'], 140, key=key + 'bs', blur=8)
        for i in range(6):
            sx = (hash1(key, i) - .5) * 5 * u; sy = top * (.25 + .6 * hash1(key, i, 'y'))
            wash(ell(sx, sy, .22 * u, .18 * u, 10), C['tealLt'], key=key + f'sp{i}', a=170)
        cc.restore()
        ink(P, sw, key=key + 'out')
    # pixel glitch / materialise squares
    g = o.get('glitch', .15)
    _pixels(u, P, top, g, mat, key, o)
    # face
    if mat >= .999 and front > -.3 and not o.get('noFace'):
        fx = flipH * 1.3 * u
        sp = 1.3 * u * (.6 + .4 * abs(front))
        ey = top * .53
        blink = _blink(t, o.get('seed', 2.1))
        ek = o.get('eyes', 'normal')
        lx, ly = o.get('lookX', 0), o.get('lookY', 0)
        for side in (-1, 1):
            ek2 = ek[0 if side < 0 else 1] if isinstance(ek, (list, tuple)) else ek
            eye_shape(ek2, fx + side * sp, ey, u * 1.45, key + f'e{side}', lx, ly, blink, big=True)
            brow(o.get('brows'), fx + side * sp, ey - 1.05 * u, u * .8, side, key + f'b{side}')
            shade(ell(fx + side * 2.15 * u, ey + 1.0 * u, .55 * u, .32 * u, 16), '#F08A90', 150, key=key + f'bl{side}', blur=3)
        mouth_shape(o.get('mouth', 'smile'), fx, ey + 1.0 * u, u * .9, key + 'm', o.get('mouthOpen', 0.0))
    # halo
    if mat > .3:
        hy = top - 1.4 * u + math.sin(t * 3.1) * .25 * u + o.get('haloDy', 0) * u
        _halo(0 + flipH * .4 * u, hy, u, sw, key, clamp((mat - .3) / .5), o.get('haloSpin', t * .6))
    c.restore()
    return dict(top=(x, yb + top), center=(x, yb + top * .5))

def _xf(c, x, y):
    m = c.getTotalMatrix(); p = m.mapXY(x, y); return (p.x(), p.y())

def _halo(x, y, u, sw, key, k, spin):
    n = 9; rx, ry = 1.7 * u, .48 * u
    for i in range(n):
        a = spin * 2 * math.pi + i * 2 * math.pi / n
        if k < (i + 1) / n * .999 and k < 1: continue
        px, py = x + rx * math.cos(a), y + ry * math.sin(a)
        rr = .26 * u
        pts = ell(px, py, rr * 1.15, rr * .7, 10, a + math.pi / 2 if False else math.atan2(ry * math.cos(a), -rx * math.sin(a)))
        fill(pts, C['halo'], key=key + f'hl{i}', tex=0, edge=.15, amp=.25, outline=max(1.4, sw * .5))

def _pixels(u, P, top, g, mat, key, o):
    t = CTX.t
    if mat < .999:
        # squares gather into the body shape
        n = 70
        for i in range(n):
            hx, hy = hash1(key, 'px', i), hash1(key, 'py', i)
            tx = (hx - .5) * 6.2 * u; ty = top * (.08 + .85 * hy)
            dly = hash1(key, 'pd', i) * .45
            k = easeOut(seg(mat, dly, dly + .55))
            sx = tx + (hash1(key, 'sx', i) - .5) * 26 * u; sy = ty + (hash1(key, 'sy', i) - .8) * 16 * u
            px, py = lerp(sx, tx, k), lerp(sy, ty, k)
            s = u * (.55 + .5 * hash1(key, 'ps', i)) * (.4 + .6 * k)
            col = C['teal'] if i % 3 else (C['tealLt'] if i % 2 else C['halo'])
            fill(rect(px - s / 2, py - s / 2, s, s), col, key=key + f'pm{i}', tex=0, edge=.15, amp=.2, outline=max(1.2, u * .08), a=int(255 * clamp(k * 3)))
        return
    n = int(10 * g)
    for i in range(n):
        side = 1 if hash1(key, 'gs', i) > .4 else -1
        per = 1.2 + hash1(key, 'gp', i)
        ph = ((t / per) + hash1(key, 'gph', i)) % 1.0
        bx = side * (3.0 + ph * 2.2 + hash1(key, 'gx', i) * .6) * u
        by = top * (.15 + .55 * hash1(key, 'gy', i)) - ph * .8 * u
        s = u * (.5 + .4 * hash1(key, 'gz', i)) * (1 - ph * .6)
        fill(rect(bx - s / 2, by - s / 2, s, s), C['teal'] if i % 2 else C['tealLt'], key=key + f'g{i}', tex=0, edge=.2, amp=.2,
             outline=max(1.2, u * .08), a=int(255 * (1 - ph)))
