# scenes.py — "Code & AI" music video, 40 s @ 24 fps, 120 BPM (downbeats on x.05 s)
#
# S1  0.00- 5.30 DESK        lamp clicks on, Brush is a drawing on paper, comes alive, dives into the monitor   [orange brush wipe]
# S2  5.30- 9.05 CODE WORLD  Brush lands, sings "made with code, line by line"; code lines write on   (LIP-SYNC PLATE 6.0-8.0)
# S3  9.05-12.70 CODE WIDE   cut on action mid-hop; each hop leaves an onion-skin frame; "every frame is mine" proud   [pixel dissolve]
# S4  12.70-20.0 DREAM       Render assembles from pixels (PLATE 13.7-14.4), types a prompt, "one one one" -> clones pop out,
#                            clones merge back on "show"   [iris on Render's halo]
# S6  20.0-24.05 STAGE WIDE  iris opens on play orb; both enter, spot each other, "Code" / "AI" point at themselves  [cut on jump]
# S7  24.05-26.4 TWO-SHOT    side by side (PLATE 24.3-25.0), "press play" orb blazes, "come alive" jump  [flash]
# S8  26.4-31.30 DANCE       low dutch angle: point at viewer, Render hops onto Brush's head; closer cut 29.05: spins  [wipe]
# S9  31.3-35.40 STAGE WIDE  Brush paints half a ring, Render pixels the other half, high-five on "come alive"
# S10 35.4-40.0  DESK        pull back: the stage is on the monitor; lamp clicks off; iris to black
import math, sys
import numpy as np
import skia
from engine import *
from chars import *
from envs import *
from envs2 import gline, gbox, particles, editor, light_whip, data_rain_wipe, dive_streaks, _ps

NOSING = False  # plates: force closed mouths

# ---------------------------------------------------------------- lyrics -> mouth
BRUSH_W = [5.42, 6.02, 6.20, 6.38, 6.86, 7.52, 8.00, 8.70, 9.24, 9.66, 9.98, 10.30, 10.72, 11.08, 11.54, 12.06]
RENDER_W = [12.78, 13.00, 13.22, 13.46, 14.42, 14.70, 15.06, 15.88, 16.04, 16.22, 16.62, 16.72, 17.00, 17.24, 17.60, 18.18, 18.52, 18.78, 19.22, 19.44]
BOTH_W = [22.66, 23.26, 23.42, 24.08, 24.20, 24.38, 25.02, 25.22, 25.80, 25.90, 26.24, 26.50, 26.90, 27.18, 27.36, 27.90, 28.20, 28.44,
          29.00, 29.16, 29.30, 29.68, 30.72, 30.98, 31.20, 34.88, 34.98, 35.30, 38.50, 38.98, 39.25]
def sing(t, words, end=None):
    if NOSING: return 0.0
    best = 0.0
    for i, w in enumerate(words):
        if t < w - .03: break
        nxt = words[i + 1] if i + 1 < len(words) else w + .5
        dur = min(.45, max(.16, nxt - w))
        x = t - (w - .03)
        if x <= dur:
            env = min(1, x / .05) * (1 - max(0, (x - dur * .6) / (dur * .4)))
            best = max(best, env * (.65 + .35 * abs(math.sin(x * 22))))
    return clamp(best)

# ---------------------------------------------------------------- acting helpers
def jump(t, t0, t1, h, crouch=.12):
    """returns (dy in u, sq). anticipation crouch before t0, squash-land after t1"""
    if t < t0 - crouch: return 0.0, 0.0
    if t < t0: return 0.0, .22 * ease(seg(t, t0 - crouch, t0))
    if t < t1:
        k = seg(t, t0, t1)
        return -h * 4 * k * (1 - k), -.16 * abs(2 * k - 1) ** 2
    x = t - t1
    return 0.0, .24 * math.exp(-10 * x) * math.cos(22 * x)
def take(t, t0, amt=.25):
    if t < t0: return 0.0
    x = t - t0; return -amt * math.exp(-9 * x) * math.cos(24 * x) if x < .6 else 0.0
def bounce(t, amt=.25, ph=0.0):
    b = bp(t) + ph
    return -amt * abs(math.sin(math.pi * b))
def faces(t, keys):
    """keys [(t, dict)]; returns merged dict with a blink-squint across each change"""
    cur = dict(keys[0][1]); last = keys[0][0]
    for tk, d in keys[1:]:
        if t >= tk: cur.update(d); last = tk
    for tk, d in keys[1:]:
        if tk - .06 <= t < tk + .03:
            cur['eyes'] = 'closed'
    return cur
def wipe_pixels(p, key='pd', cols=('#7DD9BE', '#4DB39A', '#C4F2E3', '#5DCBB2')):
    if p <= 0 or p >= 1: return
    cs = 120
    for gx in range(0, W // cs + 1):
        for gy in range(0, H // cs + 1):
            thr = hash1(key, gx, gy) * .8 + (gx / (W / cs)) * .2
            if p < .5: on = p * 2 > thr; k = clamp((p * 2 - thr) * 6)
            else: on = (p - .5) * 2 < thr; k = clamp((thr - (p - .5) * 2) * 6)
            if not on: continue
            s = cs * (.4 + .6 * k) + 2
            cx, cy = gx * cs + cs / 2, gy * cs + cs / 2
            fill(rect(cx - s / 2, cy - s / 2, s, s), cols[int(hash1(key, 'c', gx, gy) * 4)], key=f'{key}{gx}_{gy}', tex=.2, edge=.2, amp=.3, outline=1.5)

def ghost(alpha, fn):
    c = CTX.canvas; c.saveLayerAlpha(None, int(alpha)); fn(); c.restore()

def confetti(t, t0, n=40, key='cf'):
    if t < t0: return
    for i in range(n):
        st = t0 + hash1(key, 's', i) * 1.5
        if t < st: continue
        age = t - st
        x = hash1(key, 'x', i) * 2200 - 140 + math.sin(age * 2 + i) * 30
        y = -100 + age * (260 + 160 * hash1(key, 'v', i))
        if y > 1300: continue
        if i % 2:
            fill(heart_pts(x, y, 1)[:0] if False else catmull([(x, y - 16), (x + 10, y + 2), (x, y + 12), (x - 10, y + 2)], True, 4), C['bri'], key=f'{key}{i}', tex=0, edge=.2, outline=1.6)
        else:
            s = 18; fill(rect(x - s / 2, y - s / 2, s, s), C['teal'] if i % 4 else C['tealLt'], key=f'{key}{i}', tex=0, edge=.2, outline=1.4)

# ================================================================ S1 DESK: typing Brush into existence
PANE = (1160, 353)
def s1(t):
    lamp = 0.0 if t < 1.05 else (0.0 if 1.12 < t < 1.2 else 1.0)
    dive = seg(t, 2.6, 3.4)
    if t < 2.6:
        cz = kf(t, [(0, 1.0), (2.4, 1.55)], ease); cxx = 960; cyy = kf(t, [(0, 540), (2.4, 385)], ease)
    else:
        cz = lerp(1.55, 10.0, easeIn(dive)); cxx = lerp(960, PANE[0], ease(seg(t, 2.6, 3.1))); cyy = lerp(385, PANE[1], ease(seg(t, 2.6, 3.1)))
    cam_begin(cxx, cyy, cz)
    cur = None
    if t > 1.85:
        k = ease(seg(t, 1.9, 2.35)); cur = (lerp(1050, 1240, k), lerp(470, 150, k))
    click = seg(t, 2.42, 2.95) if t > 2.42 else None
    def screen(mx, my, mw, mh):
        editor(t, mx, my, mw, mh, seg(t, .3, 2.0), seg(t, .7, 2.3), click=click, cursor=cur)
        if click is not None:
            glow(PANE[0], PANE[1], 260, '#7DFFD8', .6 * math.sin(math.pi * clamp(click)))
    desk(t, dict(lamp=lamp, screen=1.0, noCone=t > 2.5, drawScreen=screen))
    cam_end()
    desk_night(lamp, 1.0)
    if t < .45:
        p = skia.Paint(Color=hexc('#000000', int(255 * (1 - t / .45)))); CTX.canvas.drawRect(skia.Rect.MakeXYWH(0, 0, W, H), p)
    if t > 2.65: dive_streaks(seg(t, 2.65, 3.4))
    if t > 3.15: flash(easeIn(seg(t, 3.15, 3.4)), '#E8FFF6')

# ================================================================ S2 CODE WORLD: compiled line by line, then the verse
LINES_S2 = [(480, 400, 290, ''), (510, 460, 240, ''), (1170, 400, 280, ''), (1200, 460, 240, ''), (490, 520, 270, ''), (1180, 520, 260, ''), (520, 580, 220, ''), (1190, 580, 230, '')]
GLINE_COLS = ('#FF9A4A', '#3FCFB0', '#8E7CFF', '#E8566C')
def code_rain(t, key='rain', n=34, y1=600):
    for i in range(n):
        x = -200 + hash1(key, 'x', i) * 2300
        sp = 120 + 140 * hash1(key, 's', i)
        y = ((t * sp + hash1(key, 'o', i) * 900) % (y1 + 200)) - 150
        ln = 18 + 40 * hash1(key, 'l', i)
        col = GLINE_COLS[i % 4]
        a = int(170 * (1 - clamp((y - (y1 - 150)) / 150)))
        if a > 10: fill(rrect(x, y, 10, ln, 5), col, key=f'{key}{i}', tex=0, edge=.2, a=a)
def glow_scribble(x0, y, length, key, col, k=1.0, sw=4.0):
    if k <= 0: return
    n = int(10 + length / 9)
    xs = np.linspace(x0, x0 + length * k, max(3, int(n * k)))
    ph = hash1(key) * 10
    ys = y + 8 * np.sin(xs * .09 + ph) * (0.6 + .4 * np.sin(xs * .013 + ph))
    gline(np.stack([xs, ys], 1), col, sw, key=key)
def s2(t):
    cz = kf(t, [(3.4, 1.12), (5.3, 1.25), (6.0, 1.25), (6.3, 1.85), (8.3, 1.9), (8.85, 1.3)], ease)
    cyy = kf(t, [(3.4, 610), (5.3, 600), (6.0, 600), (6.3, 640), (8.3, 640), (8.85, 600)], ease)
    cam_begin(960 + 4 * math.sin(t * .7), cyy, cz)
    codeworld(t, dict(lines=0))
    code_rain(t)
    lines = 0 if t < 6.86 else (t - 6.86) / .32
    for i, (lx, ly, ln, _) in enumerate(LINES_S2):
        k = clamp(lines - i)
        if k > 0:
            glow_scribble(lx, ly, ln, f'c2{i}', GLINE_COLS[i % 4], easeOut(k))
    x, y, u = 960, 1000, 28
    # code tokens fly in and assemble
    if t < 4.6:
        for i in range(46):
            st = 3.4 + hash1('ft', i) * .55
            k = seg(t, st, st + .55)
            if k <= 0 or k >= 1: continue
            tx = x + (hash1('tx', i) - .5) * 3.2 * u; ty = y - (.5 + hash1('ty', i) * 21.5) * u
            a_ = hash1('fa', i) * 2 * math.pi
            sx, sy = tx + math.cos(a_) * 1400, ty + math.sin(a_) * 900
            px, py = lerp(sx, tx, easeIn(k)), lerp(sy, ty, easeIn(k))
            ln = 30 + 50 * hash1('fl', i)
            fill(rrect(px - ln / 2, py - 7, ln, 14, 7), GLINE_COLS[i % 4], key=f'tok{i}', tex=0, edge=.2, amp=.2, outline=1.5)
    face = faces(t, [(0, dict(eyes='closed', mouth='flat')), (5.22, dict(eyes='dot', mouth='smile')), (5.5, dict(eyes='happy', mouth='smile')), (5.9, dict(eyes='dot', mouth='smile'))])
    sq = take(t, 5.22, .3)
    dy = bounce(t, .12) if t > 5.5 else 0
    if t > 8.85: sq += .2 * ease(seg(t, 8.85, 9.05))
    aR = kf(t, [(5.22, -1.15), (5.35, .7), (5.7, -1.15), (6.7, -1.15), (6.95, .55), (7.8, .55), (8.1, .3), (8.7, .3)])
    aL = kf(t, [(5.22, -1.15), (5.35, .6), (5.7, -1.15), (7.85, -1.15), (8.1, .55), (8.7, .4)])
    lookX = kf(t, [(6.7, 0), (6.9, .8), (7.8, .8), (8.0, -.8), (8.5, 0)])
    bo = dict(face, dy=dy, sq=sq, rot=.03 * math.sin(math.pi * bp(t)) if t > 5.4 else 0, aL=aL, aR=aR, lookX=lookX, lookY=-.3 if 6.9 < t < 8.5 else 0,
              mouthOpen=sing(t, BRUSH_W), hair=.15 * math.sin(math.pi * bp(t)), seed=1.9)
    build = seg(t, 3.8, 4.9)
    solid = seg(t, 4.9, 5.2)
    if t < 5.2:
        scan = lerp(y + 15, y - 23 * u - 15, ease(build))
        c = CTX.canvas
        if build > 0:
            c.save(); c.clipRect(skia.Rect.MakeLTRB(x - 400, scan, x + 400, y + 60))
            c.saveLayerAlpha(None, int(lerp(150, 255, solid)))
            brush(x, y, u, bo)
            c.restore()
            for j in range(int((y + 40 - scan) / 14)):
                yy = scan + j * 14
                c.drawLine(x - 3 * u, yy, x + 3 * u, yy, _ps('#5FF2D0', int(60 * (1 - solid)), 2))
            c.restore()
            if build < 1:
                gline([(x - 4 * u, scan), (x + 4 * u, scan)], '#3FCFB0', 5, key='scan2')
                for q in range(4):
                    sparkle(x - 3.5 * u + q * 2.3 * u + 20 * math.sin(t * 9 + q), scan - 6, 18 + 8 * math.sin(t * 13 + q), f'ssp{q}', '#FFF6D0')
        if solid > 0: glow(x, y - 11 * u, 500 * math.sin(math.pi * solid), '#FFF0C0', .7)
    else:
        brush(x, y, u, bo)
    if 5.25 < t < 6.0: emote('spark', 1210, 520, 46, seg(t, 5.25, 5.4), key='s2sp')
    particles(t, 's2p', 16, 300, 1650, 250, 1000, cols=GLINE_COLS, size=(8, 16))
    cam_end()
    if t < 3.65: flash(1 - seg(t, 3.4, 3.65), '#E8FFF6')
    if t > 8.95: light_whip(seg(t, 8.95, 9.35))

# ================================================================ S3 CODE WIDE, onion skin
HOPS = [(8.85, 9.35, 330, 620), (9.55, 9.95, 620, 910), (10.05, 10.45, 910, 1200)]
def s3_pose(t):
    x = HOPS[0][2]; dy = 0; sq = 0
    for (a, b, x0, x1) in HOPS:
        if t >= a:
            x = lerp(x0, x1, ease(seg(t, a, b)))
            d, s = jump(t, a, b, 3.2)
            if t < b + .5: dy, sq = d, s
    return x, dy, sq
def s3(t):
    cx = kf(t, [(9.15, 740), (10.6, 960), (12.75, 1010)])
    cz = kf(t, [(9.15, 1.05), (11.9, 1.07), (12.25, 1.14)], easeOut)
    cam_begin(cx, 700, cz)
    codeworld(t, dict(lines=9))
    code_rain(t, 'rain3')
    u, gy = 21, 930
    # portal to the AI world (right)
    pk = backOut(seg(t, 10.5, 11.0)); flare = seg(t, 12.25, 12.6)
    if pk > 0:
        PX, PY = 1600, 720
        glow(PX, PY, 300 * pk * (1 + flare), '#9EF5DD', .8)
        fill(ell(PX, PY, 150 * pk, 210 * pk, 40), mix('#A6E6D2', '#C9B8E3', .5 + .5 * math.sin(t * 2)), key='ptl', tex=.4, edge=.4, a=230)
        wash(ell(PX - 30 * pk, PY - 60 * pk, 60 * pk, 40 * pk, 20), '#F2FFF9', key='ptlh', a=140)
        for q in range(18):
            a_ = t * 1.4 + q * 2 * math.pi / 18
            gbox(PX + 175 * pk * math.cos(a_), PY + 235 * pk * math.sin(a_), 24 * pk, ('#5FF2D0', '#B79CFF', '#FFFFFF')[q % 3], 1.0, key=f'pq{q}')
    # ghosts at each takeoff point
    for i, (a, b, x0, x1) in enumerate(HOPS):
        tg = a if i else 9.15
        if t < tg: continue
        k = seg(t, tg, tg + .15)
        gpose = dict(eyes='dot', mouth='smile', head=.2, sq=-.1, aL=.5, aR=.9, seed=1.9, noShadow=True, key=f'G{i}')
        ghost(115 * k, lambda: brush(x0, gy - 10, u, gpose))
        if t > 11.05 + i * .12:
            fk = backOut(seg(t, 11.05 + i * .12, 11.3 + i * .12))
            fw, fh = 320 * fk, 540 * fk
            P = rrect(x0 - fw / 2, gy - fh + 30, fw, fh, 16)
            ink(P, 5, '#4A6496', key=f'fr{i}'); gline(P, '#3FCFB0', 3, key=f'frg{i}', closed=True, a=.8)
            for s_ in range(6):
                for side in (-1, 1):
                    hx = x0 + side * (fw / 2 - 18); hy = gy - fh + 70 + s_ * (fh - 80) / 5
                    wash(rect(hx - 7, hy - 6, 14, 12), '#4A6496', key=f'fh{i}{s_}{side}')
    x, dy, sq = s3_pose(t)
    # light trail from the bristles
    if t < 10.9:
        TP = []
        for q in range(9):
            xx, dd, _ = s3_pose(t - q * .045)
            TP.append((xx - 20, gy + dd * u - 20.5 * u))
        gline(np.array(TP), '#FF9A4A', 7, key='trail3', a=.9)
    head = .2 if t < 11.5 else kf(t, [(11.5, .2), (11.7, 0)])
    face = faces(t, [(0, dict(eyes='happy', mouth='smile')), (10.5, dict(eyes='dot', mouth='smile')), (11.05, dict(eyes='wide', mouth='O')),
                     (11.5, dict(eyes='dot', mouth='smile')), (12.06, dict(eyes='happy', mouth='grin'))])
    lookX = -1 if 10.9 < t < 11.5 else 0
    o = dict(face, dy=dy, sq=sq + take(t, 12.06, .28), head=head, lookX=lookX, seed=1.9, mouthOpen=sing(t, BRUSH_W),
             walk=None, hair=-.25 if dy < -.5 else .1 * math.sin(math.pi * bp(t)))
    if dy < -.2: o.update(aL=1.0, aR=1.2)
    else: o.update(aL=-.9, aR=-1.0)
    if t > 12.0:
        o.update(aLpos=(x - 1.1 * u, gy - 9.0 * u), aRpos=(x + 1.1 * u, gy - 9.0 * u), aLbend=-1.2, aRbend=-1.2)
    if 10.45 < t < 11.0:
        o.update(aL=kf(t, [(10.45, -.9), (10.6, .2)]))
    if t > 12.25:
        k = seg(t, 12.25, 12.6)
        jx, jy = arcPt((x, gy), (1600, 780), 260, easeIn(k))
        o.update(eyes='happy', mouth='open', aL=1.3, aR=1.3, sq=-.15, head=.2, noShadow=True)
        brush(jx, jy, u * (1 - .6 * k), o)
    else:
        brush(x, gy, u, o)
    if 12.06 < t < 12.3: emote('spark', x + 150, gy - 500, 50, seg(t, 12.06, 12.2), key='s3sp')
    particles(t, 's3p', 18, 200, 1800, 250, 1000, cols=GLINE_COLS, size=(8, 16))
    cam_end()
    if t < 9.35: light_whip(seg(t, 8.95, 9.35))
    if t > 12.5: wipe_shiny(seg(t, 12.5, 13.0), 'pd1')

# ================================================================ S4/S5 DREAM
PROMPT = (1330, 560)
CLONES = [(15.88, 540, 930, 21), (16.04, 1390, 920, 21), (16.22, 330, 1010, 24), (16.62, 1600, 1000, 24), (16.72, 700, 1060, 19), (17.00, 1210, 1060, 19)]
def s4(t):
    cz = kf(t, [(12.7, 1.35), (15.6, 1.35), (17.2, .95), (19.5, 1.0)], ease)
    cyy = kf(t, [(12.7, 700), (15.6, 700), (17.2, 640)], ease)
    cam_begin(960 + 5 * math.sin(t * .6), cyy, cz)
    dream(t, dict(ring=1.0))
    particles(t, 's4p', 22, -100, 2000, 150, 1050, cols=('#5FF2D0', '#B79CFF', '#FFFFFF'), size=(7, 15))
    x, gy, u = 930, 925, 40
    mat = 1.0
    mk = ease(seg(t, 12.95, 13.55))
    face = faces(t, [(0, dict(eyes='closed', mouth='smile')), (13.55, dict(eyes='normal', mouth='smile')), (15.06, dict(eyes='happy', mouth='smile')),
                     (15.9, dict(eyes='wide', mouth='O')), (17.3, dict(eyes='wide', mouth='grin')), (18.1, dict(eyes='happy', mouth='smile')),
                     (19.0, dict(eyes='normal', mouth='smile'))])
    o = dict(face, mat=mat, seed=2.2, mouthOpen=sing(t, RENDER_W) if mat >= 1 else 0, glitch=.25)
    sq = 0.0
    if t > 13.55: sq += take(t, 13.6, .3)
    dy = 0.0
    if 13.9 < t < 19.3: dy = bounce(t, .25)
    # typing
    head = 0.0
    if 14.2 < t < 15.6:
        head = .1; o['lookX'] = .8
        o['aR'] = kf(t, [(14.2, -.6), (14.4, .1), (15.0, .1), (15.06, .5), (15.2, .1)])
        o['dx'] = .6 * ease(seg(t, 14.2, 14.4))
    if 15.6 <= t < 17.3:
        o['lookX'] = math.sin(t * 9) * .9 if t > 16.0 else .6
    if 17.24 <= t: sq += take(t, 17.24, .35)
    if 18.18 <= t < 19.3:
        o['aL'] = .9 * abs(math.sin(math.pi * bp(t))); o['aR'] = .9 * abs(math.sin(math.pi * bp(t) + .5))
    if t >= 19.3:
        d, s = jump(t, 19.62, 20.2, 9)
        dy += d; sq += s + .25 * ease(seg(t, 19.35, 19.5)) * (1 - seg(t, 19.55, 19.62))
        o.update(eyes='happy', mouth='open', aL=1.3, aR=1.3)
    o.update(sq=sq, dy=dy, head=head)
    if mk < 1:
        ghost(255 * mk, lambda: render_bot(x, gy, u, dict(o, glitch=0)))
        r_ = np.random.default_rng(CTX.bi + 99)
        n = int(320 * (1 - mk))
        cx_, cy_ = x, gy - 3.2 * u
        for i in range(n):
            ang = r_.random() * 2 * math.pi; rr = math.sqrt(r_.random())
            px_ = cx_ + math.cos(ang) * rr * 4.4 * u * (1 + .8 * (1 - mk)); py_ = cy_ + math.sin(ang) * rr * 3.6 * u * (1 + .8 * (1 - mk))
            s_ = 6 + r_.random() * 14
            col = ('#5FF2D0', '#B79CFF', '#FFFFFF', '#4DB39A')[int(r_.random() * 4)]
            CTX.canvas.drawRect(skia.Rect.MakeXYWH(px_, py_, s_, s_), skia.Paint(Color=hexc(col, 220)))
        glow(cx_, cy_, 300, '#C8FFF0', .5 * (1 - mk))
        rb = dict(top=(x, gy - 6.2 * u))
    else:
        rb = render_bot(x, gy, u, o)
    # prompt bar
    if 14.25 < t < 15.9:
        k = backOut(seg(t, 14.25, 14.45)) * (1 - easeIn(seg(t, 15.6, 15.9)))
        px, py = PROMPT
        bw, bh = 360 * k, 74 * k
        if bw > 4:
            glow(px, py, 260 * k, '#BFFFEA', .25 + (.5 if 15.06 < t < 15.4 else 0))
            fill(rrect(px - bw / 2, py - bh / 2, bw, bh, bh / 2), '#EFFFF8', key='pb', a=225, tex=.1, edge=.2, outline=3)
            nd = int(clamp(seg(t, 14.42, 15.0)) * 7)
            for i in range(nd):
                fill(rrect(px - bw / 2 + 30 + i * 38, py - 7, 28, 14, 7), '#4DB39A', key=f'pd{i}', tex=0, edge=0)
            if (t * 2.5) % 1 < .6:
                ink([(px - bw / 2 + 36 + nd * 38, py - 20), (px - bw / 2 + 36 + nd * 38, py + 20)], 4, key='cur', closed=False)
            fill(ell(px + bw / 2 - 40, py, 24 * k, 24 * k, 18), '#4DB39A' if t < 15.06 else '#F2C14E', key='go', tex=0, edge=.2, outline=2.5)
            fill(np.array([(px + bw / 2 - 47, py - 11), (px + bw / 2 - 47, py + 11), (px + bw / 2 - 30, py)]) if k > .5 else rect(0, 0, 0, 0), '#FFFFFF', key='got', tex=0, edge=0)
        if 15.06 < t < 15.6: emote('spark', px + 150, py - 70, 50, seg(t, 15.06, 15.2), key='gosp')
    # clones
    for i, (tc, cx, cgy, cu) in enumerate(CLONES):
        if t < tc: continue
        if t > 19.62: continue
        k = seg(t, tc, tc + .35)
        if t < 19.3:
            px, py = arcPt(PROMPT, (cx, cgy), 260, easeOut(k)); sc = lerp(.3, 1, easeOut(k))
        else:
            m = easeIn(seg(t, 19.3, 19.6))
            px, py = lerp(cx, x, m), lerp(cgy, gy - 3 * u, m); sc = 1 - m * .8
        cf = [dict(eyes='wide', mouth='O'), dict(eyes='happy', mouth='open'), dict(eyes=['normal', 'wide'], mouth='wobble'),
              dict(eyes='heart', mouth='smile'), dict(eyes='x', mouth='flat'), dict(eyes='star', mouth='grin')][i]
        cdy = bounce(t, .3, i * .37) if 17.3 < t < 19.3 else 0
        render_bot(px, py, cu * sc, dict(cf, key=f'K{i}', seed=3 + i, glitch=1.0, dy=cdy, sq=take(t, tc + .35, .3) if k >= 1 else -.15,
                                         aL=.9 if 18.18 < t < 19.3 else -.6, aR=.9 if 18.18 < t < 19.3 else -.6, head=(-.12 if cx > 960 else .12) if t < 17.3 else 0,
                                         mouthOpen=sing(t, RENDER_W[15:]) if 18.1 < t < 19.3 else 0, glow=.15))
        if k < 1: emote('spark', px, py - 120 * sc, 30, math.sin(math.pi * k), key=f'cs{i}')
    if t > 19.6: glow(x, gy - 4 * u, 500 * seg(t, 19.6, 19.75) * (1 - seg(t, 19.75, 20)), '#C8FFF0', .8)
    cam_end()
    if t < 13.0: wipe_shiny(seg(t, 12.5, 13.0), 'pd1')
    if t > 19.68:
        hx, hy = to_screen(x, gy - 7.6 * u + jump(t, 19.62, 20.2, 9)[0] * u)
        hx, hy = (rb['top'][0], rb['top'][1])
        CTX.cam = (960 + 5 * math.sin(t * .6), cyy, cz, 0)
        sx, sy = to_screen(*rb['top'])
        iris(sx, sy - 40, lerp(1500, 0, easeIn(seg(t, 19.68, 20.0))))

# ================================================================ S6 STAGE meet
def s6(t):
    cz = kf(t, [(20.0, 1.08), (24.05, 1.25)])
    cyy = kf(t, [(20.0, 590), (24.05, 660)])
    play = .35 + .25 * pulse(t, 4)
    cam_begin(960, cyy, cz)
    stage(t, dict(play=play))
    particles(t, 's6p', 22, 100, 1800, 200, 1100, cols=GLINE_COLS, size=(8, 16))
    gy = 1000
    BU, RU = 22, 27
    # Brush walks in from the left
    bx = kf(t, [(20.25, -180), (21.55, 740)], lambda k: k)
    bwalk = None
    skate = t < 21.55
    bface = faces(t, [(0, dict(eyes='dot', mouth='smile')), (21.75, dict(eyes='wide', mouth='O')), (22.05, dict(eyes='narrow', mouth='flat', brows='angry')),
                      (22.66, dict(eyes='happy', mouth='smile', brows=None)), (23.6, dict(eyes='dot', mouth='smile'))])
    bo = dict(bface, head=.22 if t < 22.62 else (0.0 if t < 23.5 else .12), walk=bwalk, seed=1.9, sq=take(t, 21.75, .3),
              mouthOpen=sing(t, BOTH_W[:1]) if t < 23.2 else 0, rot=.06 if 22.1 < t < 22.6 else 0)
    if skate:
        bo.update(rot=-.12, aL=.35, aR=.1, hair=-.35, spread=.4, eyes='happy')
        ink([(bx - 900, gy - 2), (bx - 40, gy - 2)], 14, '#FF9A4A', key='bski', closed=False); gline([(bx - 900, gy - 4), (bx - 40, gy - 4)], '#FFB066', 5, key='bsk', a=.9)
    if 21.5 < t < 21.9:
        for q in range(6): sparkle(bx + 40 + q * 18, gy - 10 - 30 * math.sin(q + t * 20), 16 * (1 - seg(t, 21.5, 21.9)), f'bsks{q}', '#FFC27A')
    if 22.62 < t < 23.3:
        bo['aRpos'] = (bx + .3 * BU, gy - 9.5 * BU); bo['aRbend'] = 1.0; bo['aL'] = .4
    if t > 23.9: _, s = jump(t, 24.05, 24.3, 2); bo['sq'] = bo.get('sq', 0) + s
    brush(bx, gy, BU, bo)
    # Render bounces in from the right
    rx = kf(t, [(20.45, 2150), (21.65, 1190)])
    hopk = bp(t) % 1.0
    rdy = 0
    if 20.45 < t < 21.65: ink([(rx + 40, gy - 2), (rx + 1000, gy - 2)], 14, '#3FCFB0', key='rski', closed=False); gline([(rx + 40, gy - 4), (rx + 1000, gy - 4)], '#7FFFE0', 5, key='rsk', a=.9)
    if 21.6 < t < 22.0:
        for q in range(6): sparkle(rx - 60 - q * 18, gy - 10 - 30 * math.sin(q + t * 20), 16 * (1 - seg(t, 21.6, 22.0)), f'rsks{q}', '#BFFFF0')
    rface = faces(t, [(0, dict(eyes='normal', mouth='smile')), (21.95, dict(eyes='wide', mouth='O')), (22.15, dict(eyes='narrow', mouth='flat', brows='angry')),
                      (23.2, dict(eyes='happy', mouth='smile', brows=None)), (23.6, dict(eyes='normal', mouth='smile'))])
    ro = dict(rface, head=-.15 if t < 23.2 else (0 if t < 23.6 else -.1), dy=rdy, seed=2.2, sq=take(t, 21.95, .35) + (.1 if 20.45 < t < 21.65 and abs(math.sin(math.pi * bp(t))) < .15 else 0),
              mouthOpen=sing(t, BOTH_W[1:3]) if 23.1 < t < 23.9 else 0, lean=-.4 if 22.15 < t < 22.6 else 0)
    if 23.22 < t < 23.9: ro['aL'] = kf(t, [(23.22, -.6), (23.35, .35)]); ro['aLhook'] = None
    if t > 23.9: _, s = jump(t, 24.05, 24.3, 2); ro['sq'] = ro.get('sq', 0) + s
    render_bot(rx, gy, RU, ro)
    if t > 21.75: emote('excl', bx + 80, gy - 600, 50, seg(t, 21.75, 21.9) * (1 - seg(t, 22.4, 22.5)), key='e6a')
    if t > 21.95: emote('excl', rx + 60, gy - 330, 50, seg(t, 21.95, 22.1) * (1 - seg(t, 22.5, 22.6)), key='e6b')
    if t > 22.66: emote('spark', bx - 140, gy - 540, 44, seg(t, 22.66, 22.8) * (1 - seg(t, 23.3, 23.4)), key='e6c')
    if t > 23.3: emote('spark', rx + 200, gy - 290, 44, seg(t, 23.3, 23.45) * (1 - seg(t, 23.9, 24.0)), key='e6d')
    cam_end()
    if t < 20.5:
        iris(960, (190 - cyy) * cz + 540, lerp(0, 2300, easeIn(seg(t, 20.0, 20.5))))

# ================================================================ S7 TWO-SHOT
def s7(t):
    play = .4 + .25 * pulse(t, 4) if t < 25.0 else min(1, .4 + 2 * (t - 25.0))
    cam_begin(965 + 3 * math.sin(t * .8), 650, 1.4)
    stage(t, dict(play=play))
    particles(t, 's7p', 18, 300, 1650, 250, 1050, cols=GLINE_COLS, size=(8, 16))
    gy = 1015
    d, s = jump(t, 24.05, 24.3, 2.2, crouch=0)
    if t < 24.05: d, s = 0, 0
    lean = .07 * ease(seg(t, 24.3, 24.45)) * (1 - ease(seg(t, 24.95, 25.1)))
    pt = ease(seg(t, 25.0, 25.15))
    d2, s2_ = jump(t, 26.24, 26.7, 4)
    bface = faces(t, [(0, dict(eyes='happy', mouth='smile')), (24.3, dict(eyes='dot', mouth='smile')), (25.05, dict(eyes='wide', mouth='grin')), (26.2, dict(eyes='happy', mouth='open'))])
    rface = faces(t, [(0, dict(eyes='happy', mouth='smile')), (24.3, dict(eyes='normal', mouth='smile')), (25.1, dict(eyes='star', mouth='grin')), (26.2, dict(eyes='happy', mouth='open'))])
    beat = bounce(t, .1) if t < 25.0 else bounce(t, .25)
    bo = dict(bface, dy=d + d2 + beat, sq=s + s2_, rot=lean, seed=1.9, mouthOpen=sing(t, BOTH_W), lookY=-.6 * pt, lookX=.15)
    bo['aR'] = lerp(-1.1, 1.35, pt); bo['aL'] = lerp(-1.1, .3, pt)
    if t > 26.1: bo.update(aL=1.4, aR=1.4)
    brush(790, gy, 24, bo)
    ro = dict(rface, dy=d + d2 + beat * 1.2, sq=s + s2_, lean=-lean * 5, seed=2.2, mouthOpen=sing(t, BOTH_W), lookY=-.6 * pt, lookX=-.15)
    ro['aL'] = lerp(-.6, 1.4, pt); ro['aR'] = lerp(-.6, .4, pt)
    render_bot(1150, gy, 29, ro)
    if t > 25.05: emote('spark', 960, 420, 50, seg(t, 25.05, 25.2), key='s7sp')
    cam_end()
    if t > 26.2: flash(seg(t, 26.2, 26.4))

# ================================================================ S8 DANCE
def s8(t):
    closer = t >= 29.05
    if not closer:
        cz, cxx, cyy = 1.22, 990, 680
        rot = 2.5 * math.sin(math.pi * bp(t) * .5)
    else:
        cz, cxx, cyy = 1.5 + .03 * math.sin(t), 900, 560
        rot = -3 * math.sin(math.pi * bp(t) * .5)
    cam_begin(cxx, cyy, cz, rot)
    stage(t, dict(play=.7 + .3 * pulse(t, 3)))
    particles(t, 's8p', 30, 200, 1700, 150, 1100, cols=GLINE_COLS, size=(8, 18))
    gy = 1000
    bxx, rxx = 900, 1180
    bu, ru = 22, 26
    # Render hop onto Brush's head
    on_head = t >= 28.4
    bsq = 0.0
    if t > 28.4: bsq = .18 * math.exp(-6 * (t - 28.4)) * math.cos(16 * (t - 28.4))
    beat = bounce(t, .25)
    spin = 0.0
    for sb in (30.05, 31.05):
        if sb <= t < sb + .45: spin = ease(seg(t, sb, sb + .45))
    bface = faces(t, [(0, dict(eyes='happy', mouth='open')), (26.9, dict(eyes=['dot', 'closed'], mouth='grin')), (27.8, dict(eyes='dot', mouth='smile')),
                      (28.4, dict(eyes='wide', mouth='O')), (28.7, dict(eyes='happy', mouth='grin')), (29.05, dict(eyes='happy', mouth='open'))])
    bo = dict(bface, dy=beat, sq=bsq, seed=1.9, mouthOpen=sing(t, BOTH_W), head=spin, rot=.08 * math.sin(math.pi * bp(t)), hair=.3 * math.sin(math.pi * bp(t)))
    if 26.9 <= t < 27.8:
        bo['aR'] = -.35; bo['armLen'] = 3.6; bo['aL'] = -1.0  # point at the viewer
    elif t >= 29.05:
        bo['aL'] = .9 + .5 * math.sin(math.pi * bp(t)); bo['aR'] = .9 - .5 * math.sin(math.pi * bp(t))
    else:
        bo['aL'] = .2 * math.sin(math.pi * bp(t)); bo['aR'] = .3
    if t >= 28.4: bo['aL'], bo['aR'] = max(bo['aL'], .9), max(bo['aR'], .9)
    info = brush(bxx, gy, bu, bo)
    # brush top position (bristles tip area)
    topx, topy = info['top']
    seat = (topx, topy - 8.6 * bu)
    rface = faces(t, [(0, dict(eyes='happy', mouth='open')), (26.9, dict(eyes='normal', mouth='grin')), (27.8, dict(eyes='wide', mouth='smile')), (28.5, dict(eyes='happy', mouth='open'))])
    ro = dict(rface, seed=2.2, mouthOpen=sing(t, BOTH_W), head=spin * -1, glitch=.5)
    if t < 27.9:
        ro.update(dy=bounce(t, .3, .25))
        if 26.9 <= t < 27.8: ro['aL'] = .0; ro['aR'] = -.2
        render_bot(rxx, gy, ru, ro)
    else:
        k = seg(t, 27.9, 28.4)
        if k < 1:
            px, py = arcPt((rxx, gy), seat, 380, ease(k)); uu = lerp(ru, 16, ease(k))
            ro.update(sq=-.15, aL=1.2, aR=1.2, noShadow=True)
        else:
            px, py = seat; uu = 16
            ro.update(dy=bounce(t, .4, .5), sq=take(t, 28.4, .3), aL=.6 + .6 * abs(math.sin(math.pi * bp(t))), aR=.6 + .6 * abs(math.cos(math.pi * bp(t))), noShadow=True)
        render_bot(px, py, uu, ro)
    if t > 29.7:
        emote('music', 640, 420, 50, seg(t, 29.7, 29.9), age=t, key='mn1')
        emote('music', 1150, 380, 44, seg(t, 30.0, 30.2), age=t + 1, key='mn2')
    confetti(t, 29.05, 46, 'cf8')
    cam_end()
    if t < 26.55: flash(1 - seg(t, 26.4, 26.55))
    if t > 31.0: data_rain_wipe(seg(t, 31.0, 31.6))

# ================================================================ S9 rings + high five
RING_C, RING_R = (960, 690), 510
def ring_arc(t, a0, a1, t0, t1, n=60):
    k = ease(seg(t, t0, t1))
    if k <= 0: return None
    aa = np.linspace(a0, lerp(a0, a1, k), max(3, int(n * k)))
    return np.stack([RING_C[0] + RING_R * np.cos(aa), RING_C[1] + RING_R * .82 * np.sin(aa)], 1)
def s9(t, inner=False):
    cz = kf(t, [(31.3, 1.0), (34.7, 1.0), (35.4, 1.12)], ease)
    sh = shake(t, 34.9, 16) if not inner else (0, 0)
    cam_begin(960 + sh[0], 560 + sh[1], cz)
    stage(t, dict(play=.6 + .3 * pulse(t, 3)))
    particles(t, 's9p', 22, 100, 1800, 200, 1100, cols=GLINE_COLS, size=(8, 16))
    gy = 1000
    # ring halves behind the characters
    burst = seg(t, 34.9, 35.3)
    if burst < 1:
        P = ring_arc(t, math.pi / 2, math.pi * 1.5, 31.6, 32.5)
        if P is not None:
            ink(P, 34, C['bri'], key='ringA', closed=False, amp=2, var=.25)
            ink(P, 12, C['briLt'], key='ringA2', closed=False, amp=1.5, var=.25)
            gline(P, '#FF9A4A', 5, key='ringAg', a=.8)
        P2 = ring_arc(t, math.pi / 2, -math.pi / 2, 32.6, 33.5, 26)
        if P2 is not None:
            for i, (qx, qy) in enumerate(P2):
                s = 34 + 8 * math.sin(i * 1.3 + t * 4)
                gbox(qx, qy, s, ['#5FF2D0', '#A6F0DC', '#B79CFF'][i % 3], 1.0, key=f'rpx{i}')
        if t > 33.5:
            glow(RING_C[0], RING_C[1], 650, '#FFE6A0', .15 + .15 * pulse(t, 3))
    else:
        pass
    if 34.9 < t < 35.6:
        k = seg(t, 34.9, 35.6)
        for i in range(16):
            a = i * 2 * math.pi / 16
            r = RING_R * (1 + .6 * easeOut(k))
            sparkle(RING_C[0] + r * math.cos(a), RING_C[1] + r * .82 * math.sin(a), 30 * (1 - k), f'bs{i}')
    # characters
    hf = seg(t, 34.5, 34.88)
    bx = lerp(760, 860, ease(hf)); rx = lerp(1160, 1053, ease(hf))
    d, s = jump(t, 34.6, 35.15, 1.2)
    rd, rs = jump(t, 34.62, 35.18, 7.4)
    bface = faces(t, [(0, dict(eyes='happy', mouth='smile')), (31.6, dict(eyes='dot', mouth='grin', brows='up')), (32.6, dict(eyes='dot', mouth='O')),
                      (33.6, dict(eyes='happy', mouth='open')), (34.5, dict(eyes='dot', mouth='grin')), (34.9, dict(eyes='happy', mouth='open')), (35.4, dict(eyes='happy', mouth='smile'))])
    bo = dict(bface, seed=1.9, mouthOpen=sing(t, BOTH_W), dy=d + bounce(t, .15), sq=s)
    if 31.6 <= t < 32.6:
        k = seg(t, 31.6, 32.5)
        bo.update(head=-.15, bend=-.35 * math.sin(math.pi * k), rot=-.1, aL=lerp(-.5, 1.4, k), aR=.4, lookX=-1, lookY=-.5 + k)
    elif 32.6 <= t < 33.6:
        bo.update(head=.15, lookX=1, aL=-1.0, aR=-.6)
    elif 33.6 <= t < 34.5:
        bo.update(aL=.9 * abs(math.sin(math.pi * bp(t))), aR=.9 * abs(math.cos(math.pi * bp(t))), rot=.08 * math.sin(math.pi * bp(t)), head=.12)
    elif t >= 34.5:
        bo.update(head=.12 if t < 35.3 else 0, aR=kf(t, [(34.5, -.6), (34.85, .6)]), aL=-.9)
        if t > 35.3: bo.update(aR=1.2 + .25 * math.sin(t * 14), aL=-1)
    brush(bx, gy, 21, bo)
    rface = faces(t, [(0, dict(eyes='happy', mouth='smile')), (31.6, dict(eyes='wide', mouth='O')), (32.6, dict(eyes='narrow', mouth='grin')),
                      (33.6, dict(eyes='happy', mouth='open')), (34.5, dict(eyes='normal', mouth='grin')), (34.9, dict(eyes='happy', mouth='open')), (35.4, dict(eyes='happy', mouth='smile'))])
    ro = dict(rface, seed=2.2, mouthOpen=sing(t, BOTH_W), dy=rd + bounce(t, .2, .3), sq=rs, glitch=.4)
    if 31.6 <= t < 32.6: ro.update(head=-.12, lookX=-1)
    elif 32.6 <= t < 33.6:
        k = seg(t, 32.6, 33.5); ro.update(head=.1, aR=lerp(-.5, 1.4, k), aL=.3, lookX=1, lookY=.5 - k, glitch=1.0)
    elif 33.6 <= t < 34.5: ro.update(aL=.9 * abs(math.cos(math.pi * bp(t))), aR=.9 * abs(math.sin(math.pi * bp(t))), head=-.1)
    elif t >= 34.5:
        ro.update(head=-.1 if t < 35.3 else 0, aL=kf(t, [(34.5, -.6), (34.85, .9)]), aR=.6)
        if t > 35.3: ro.update(aL=1.0 + .3 * math.sin(t * 13 + 1), aR=-.6)
    render_bot(rx, gy, 25, ro)
    if 34.88 < t < 35.9:
        kb = seg(t, 34.88, 35.9)
        for q in range(28):
            a_ = hash1('hb', q) * 2 * math.pi; sp = 300 + 500 * hash1('hbs', q)
            px_, py_ = bx + 92 + math.cos(a_) * sp * easeOut(kb), gy - 262 + math.sin(a_) * sp * easeOut(kb) + 120 * kb * kb
            if q % 2: sparkle(px_, py_, 22 * (1 - kb), f'hbs{q}', '#FFF0B0')
            else: gbox(px_, py_, 22 * (1 - kb) + 2, ('#5FF2D0', '#FF9A4A', '#B79CFF')[q % 3], 1 - kb, key=f'hbb{q}')
    if 34.88 < t < 35.5:
        k = seg(t, 34.88, 35.5)
        hx, hy = bx + 92, gy - 262
        fill(star_pts(hx, hy, 140 * easeOut(k) * (1 - k * .6) + 1, .4, 8, k), '#FFE07A', key='hf', tex=0, edge=.2, outline=3, a=int(255 * (1 - k)))
    cam_end()
    if not inner:
        if t < 31.6: data_rain_wipe(seg(t, 31.0, 31.6))
        if 34.88 < t < 35.1: flash(.6 * (1 - seg(t, 34.88, 35.1)))

# ================================================================ S10 pull back
def s10(t):
    cz = kf(t, [(35.4, 3.0), (37.7, 1.0)], ease)
    cyy = kf(t, [(35.4, 340), (37.7, 545)], ease)
    lamp = 1.0 if t < 39.05 else (1.0 if 39.12 < t < 39.18 else 0.0)
    cam_begin(960, cyy, cz)
    def screen(mx, my, mw, mh):
        c = CTX.canvas
        c.save(); c.clipRect(skia.Rect.MakeXYWH(mx, my, mw, mh), doAntiAlias=True)
        s = mh / H
        c.translate(mx + mw / 2 - W * s / 2, my); c.scale(s, s)
        inner_stage(t)
        c.restore()
        glow(mx + mw / 2, my + mh / 2, 500, '#7DFFD8', .18)
    desk(t, dict(lamp=lamp, screen=1.0, drawScreen=screen))
    # a little doodle of the two of them left on the sheet
    ghost(90, lambda: (brush(905, 900, 7, dict(eyes='happy', mouth='smile', noShadow=True, aR=1.0, key='DB')),
                       render_bot(1010, 900, 9, dict(eyes='happy', mouth='smile', noShadow=True, aL=1.0, key='DR', glow=0, glitch=0))))
    cam_end()
    desk_night(lamp, .85)
    if t > 39.3:
        CTX.cam = (960, cyy, cz, 0)
        sx, sy = to_screen(960, 340)
        iris(sx, sy, lerp(900, 0, easeIn(seg(t, 39.3, 39.95))))

def inner_stage(t):
    """stage seen in the monitor during S10: continues S9's framing, then they wave; 'come alive' jump at 38.5"""
    tt = t
    CTX_cam = getattr(CTX, 'cam', None)
    c = CTX.canvas
    c.save()
    # S9 camera at its end (zoom 1.12 around 960,560) folded into the screen content
    c.translate(W / 2, H / 2); c.translate(-960, -560)
    stage(tt, dict(play=.7 + .3 * pulse(tt, 3)))
    particles(tt, 's10p', 22, 100, 1800, 200, 1100, cols=GLINE_COLS, size=(8, 16))
    gy = 1000
    d, s = jump(tt, 38.45, 38.95, 3)
    wave = math.sin(tt * 12)
    brush(880, gy, 21, dict(eyes='happy', mouth='smile', seed=1.9, mouthOpen=sing(tt, BOTH_W), dy=d + bounce(tt, .15), sq=s, aR=1.2 + .25 * wave, aL=-1 if tt < 38.4 else 1.3))
    render_bot(1060, gy, 25, dict(eyes='happy', mouth='smile', seed=2.2, mouthOpen=sing(tt, BOTH_W), dy=d + bounce(tt, .2, .3), sq=s, aL=1.0 + .3 * math.sin(tt * 13 + 1), aR=-.6 if tt < 38.4 else 1.3, glitch=.4))
    if tt > 38.95: confetti(tt, 38.95, 30, 'cf10')
    c.restore()
    if CTX_cam: CTX.cam = CTX_cam

# ================================================================ timeline
SHOTS = [(0.0, s1), (3.40, s2), (9.15, s3), (12.75, s4), (20.0, s6), (24.05, s7), (26.4, s8), (31.3, s9), (35.4, s10)]
DURATION = 40.0

def draw(t):
    fn = SHOTS[0][1]
    for st, f in SHOTS:
        if t >= st: fn = f
    fn(t)

def render(t):
    CTX.t = t; CTX.bi = int(t * BOIL)
    s = skia.Surface(W, H); c = s.getCanvas(); CTX.canvas = c
    CTX.cam = (W / 2, H / 2, 1, 0)
    c.clear(hexc(PAPER))
    draw(t)
    return finish(s.makeImageSnapshot().toarray())


def wipe_shiny(p, key='pd'):
    """shiny glowing-square dissolve (borrowed pixel look, painted squares + glints)"""
    if p <= 0 or p >= 1: return
    cs = 120
    for gx in range(0, W // cs + 1):
        for gy in range(0, H // cs + 1):
            thr = hash1(key, gx, gy) * .8 + (gx / (W / cs)) * .2
            if p < .5: on = p * 2 > thr; k = clamp((p * 2 - thr) * 6)
            else: on = (p - .5) * 2 < thr; k = clamp((thr - (p - .5) * 2) * 6)
            if not on: continue
            s = cs * (.4 + .6 * k) + 2
            cx, cy = gx * cs + cs / 2, gy * cs + cs / 2
            col = ('#7DD9BE', '#4DB39A', '#C4F2E3', '#B79CFF')[int(hash1(key, 'c', gx, gy) * 4)]
            fill(rect(cx - s / 2, cy - s / 2, s, s), col, key=f'{key}{gx}_{gy}', tex=.2, edge=.2, amp=.3, outline=1.5)
            if hash1(key, 'g', gx, gy) < .25 and k > .5:
                sparkle(cx + s * .25, cy - s * .25, 18, f'{key}g{gx}{gy}', '#FFFFFF')
