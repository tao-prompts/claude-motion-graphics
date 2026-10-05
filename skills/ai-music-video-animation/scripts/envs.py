# envs.py — the four painted locations, drawn in world space (1920x1080 + margins).
import math
import numpy as np
import skia
from engine import *
from chars import C, heart_pts, star_pts, sparkle

NAVY = '#2F4A7A'

def bg(col):
    CTX.canvas.drawRect(skia.Rect.MakeXYWH(-1500, -1500, W + 3000, H + 3000), skia.Paint(Color=hexc(col)))

def scribble_line(x0, y, length, key, col=INK, sw=2.5, amp=6, k=1.0, a=255):
    """an abstract handwriting/code line (no letters): loops and humps"""
    if k <= 0: return
    n = int(10 + length / 9)
    xs = np.linspace(x0, x0 + length * k, max(3, int(n * k)))
    r = np.random.default_rng(int(hash1(key) * 1e6))
    ph = r.random() * 10
    ys = y + amp * np.sin(xs * .09 + ph) * (0.6 + .4 * np.sin(xs * .013 + ph))
    ink(np.stack([xs, ys], 1), sw, col, key=key, closed=False, amp=.6, a=a, var=.3, step=4)

# ============================================================ 1. DESK AT NIGHT
def desk(t, o=None):
    o = o or {}
    lamp = o.get('lamp', 1.0)
    scr = o.get('screen', .6)
    bg('#3F4569')
    grad_rect(-1500, -600, W + 3000, 1300, ['#2E3352', '#454C74', '#535B82'], [0, .6, 1])
    # wall boards
    for i in range(-3, 14):
        x = i * 190 + 40
        ink([(x, -500), (x + 4, 650)], 2.0, '#2F3452', key=f'wb{i}', closed=False, a=150)
    # pinned papers
    for i, (px, py, pw, ph, rot) in enumerate(((150, 60, 170, 210, -.06), (1350, 40, 150, 180, .05), (1520, 260, 140, 170, -.04),
                                               (420, 30, 130, 150, .07), (1730, 90, 160, 190, .03), (-120, 300, 170, 200, .04))):
        P = rect(-pw / 2, -ph / 2, pw, ph)
        c, s = math.cos(rot), math.sin(rot)
        P = np.stack([px + P[:, 0] * c - P[:, 1] * s, py + P[:, 0] * s + P[:, 1] * c], 1)
        fill(P, '#E8DDC4', key=f'pp{i}', tex=.4, edge=.3, outline=1.6)
        for j in range(3):
            scribble_line(px - pw * .35, py - ph * .25 + j * 28, pw * .6, f'pps{i}{j}', '#7A7484', 1.5, 4)
        fill(ell(px, py - ph / 2 + 10, 8, 8, 12), '#D8584A', key=f'pin{i}', tex=0, edge=0, outline=1.2)
    # shelf + books (left)
    fill(rect(-300, 330, 560, 26), '#6E4A32', key='shelf', tex=.5, edge=.3, outline=2)
    bx = -280
    for i, (bw, bh, col) in enumerate(((44, 150, '#7D5BA6'), (36, 130, '#C86B4A'), (50, 160, '#4F7FA0'), (40, 120, '#D9A74A'), (46, 145, '#5E8F6A'), (38, 128, '#B65A6A'))):
        fill(rect(bx, 330 - bh, bw, bh), col, key=f'bk{i}', tex=.5, edge=.35, outline=1.8); bx += bw + 4
    # hanging plant leaves (top-left)
    for i in range(14):
        a = hash1('lf', i)
        lx = -60 + i * 26 + 30 * math.sin(i * 1.7)
        ly = -40 + (i % 5) * 70 + a * 60
        sway = math.sin(t * 1.3 + i) * 4
        P = heart_pts(lx + sway, ly, 34 + 10 * a)
        P = P[::-1]
        fill(P, '#6E9A4E' if i % 3 else '#5D8A45', key=f'lf{i}', tex=.4, edge=.4, outline=2)
        ink([(lx + sway, ly - 30), (lx + sway, ly + 15)], 1.6, '#3F6634', key=f'lv{i}', closed=False)
    # monitor
    mx, my, mw, mh = 640, 140, 640, 400
    fill(rect(mx + mw / 2 - 40, my + mh, 80, 90), '#3A3B46', key='mst', tex=.3, edge=.2, outline=2.5)
    fill(rect(mx + mw / 2 - 150, my + mh + 80, 300, 26), '#3A3B46', key='mbase', tex=.3, edge=.2, outline=2.5)
    fill(rrect(mx - 26, my - 26, mw + 52, mh + 52, 26), '#34353F', key='bezel', tex=.4, edge=.3, outline=3)
    screen_col = mix('#40606A', '#9FD8CB', scr)
    fill(rect(mx, my, mw, mh), screen_col, key='scr', tex=.25, edge=.25, outline=2)
    if scr > .05:
        fill(rect(mx + 140, my + 60, 360, 270), mix(screen_col, '#F2EEDC', .6 * scr), key='scv', tex=.2, edge=.15, outline=1.2)
        for j in range(4):
            fill(rect(mx + 30, my + 70 + j * 50, 80, 26), mix(screen_col, '#6FA7A6', .5), key=f'scp{j}', tex=0, edge=.1)
        for j in range(6):
            fill(rect(mx + 545 + (j % 2) * 38, my + 200 + (j // 2) * 38, 30, 30), ['#E79A5A', '#7DD9BE', '#8FA9D6', '#F2C14E', '#C9A0DC', '#7DD9BE'][j], key=f'sw{j}', tex=0, edge=.1, a=int(255 * scr))
        glow(mx + mw / 2, my + mh / 2, 620, '#4FC9B0', .32 * scr)
    if o.get('drawScreen'):
        o['drawScreen'](mx, my, mw, mh)
    # lamp (right)
    lx, ly = 1600, 610
    fill(ell(lx, ly, 90, 26, 24), '#33343C', key='lbase', tex=.3, edge=.2, outline=2.5)
    ink([(lx, ly - 10), (lx + 70, ly - 260), (lx - 40, ly - 420)], 14, '#33343C', key='larm', closed=False, amp=1, var=.1)
    ink([(lx, ly - 10), (lx + 70, ly - 260), (lx - 40, ly - 420)], 6, '#55565F', key='larm2', closed=False, amp=1, var=.1)
    shx, shy = 1470, 175
    shadeP = np.array([(shx - 60, shy - 80), (shx + 70, shy - 110), (shx + 150, shy + 60), (shx - 120, shy + 120)])
    if lamp > 0 and not o.get('noCone'):
        cone = np.array([(shx - 110, shy + 110), (shx + 140, shy + 55), (shx + 420, 1000), (shx - 900, 1100)])
        cp = skia.Paint(AntiAlias=True)
        cp.setShader(skia.GradientShader.MakeLinear([(shx, shy + 80), (shx - 300, 900)], [hexc('#FFD98A', int(90 * lamp)), hexc('#FFD98A', 0)]))
        cp.setBlendMode(skia.BlendMode.kPlus)
        CTX.canvas.drawPath(topath(cone), cp)
    fill(catmull(shadeP, True, 5), '#3A3B44', key='lshade', tex=.4, edge=.3, outline=3)
    fill(ell(shx + 15, shy + 88, 128, 30, 24, -.22), mix('#5B4A3A', '#FFE3A0', lamp), key='lmouth', tex=.2, edge=.2, outline=2)
    if lamp > 0:
        glow(shx + 10, shy + 95, 300, '#FFC86A', .75 * lamp)
        glow(shx - 200, 700, 700, '#FFB85A', .22 * lamp)
    # desk
    dy = 600
    fill(np.array([(-1500, dy), (W + 1500, dy), (W + 1500, 2600), (-1500, 2600)]), '#B47A40', key='desk', tex=.6, edge=0, amp=.5)
    fill(np.array([(-1500, dy - 8), (W + 1500, dy - 8), (W + 1500, dy + 24), (-1500, dy + 24)]), '#8C5A2E', key='dedge', tex=.4, edge=0)
    ink([(-1500, dy - 8), (W + 1500, dy - 8)], 3, key='dline', closed=False)
    for i in range(9):
        yy = dy + 60 + i * 70 + i * i * 6
        scribble_line(-400 + hash1('gx', i) * 600, yy, 1200 + hash1('gl', i) * 900, f'grain{i}', '#8E5A30', 2.0, 5, a=170)
    # props: mug with pencils (left)
    mgx, mgy = 330, 640
    for j, (col, ang, ln) in enumerate((('#E0B04A', -.25, 230), ('#D8584A', -.08, 260), ('#5C7FB0', .1, 240), ('#6E9A4E', .28, 210), ('#C9A0DC', -.4, 190))):
        bx, by = mgx + (j - 2) * 22, mgy - 120
        ex, ey = bx + math.sin(ang) * ln, by - math.cos(ang) * ln
        ink([(bx, by), (ex, ey)], 16, INK, key=f'pc{j}o', closed=False, var=.05, amp=1)
        ink([(bx, by), (ex, ey)], 11, col, key=f'pc{j}', closed=False, var=.05, amp=1)
    fill(rrect(mgx - 90, mgy - 170, 180, 190, 18), '#E9DFC9', key='mug', tex=.4, edge=.4, outline=2.5)
    ink(catmull([(mgx + 88, mgy - 130), (mgx + 140, mgy - 110), (mgx + 140, mgy - 50), (mgx + 88, mgy - 40)], False, 6), 12, '#E9DFC9', key='mgh', closed=False)
    for j in range(5):
        fill(ell(mgx - 50 + hash1('ms', j) * 100, mgy - 140 + hash1('mt', j) * 130, 14 + 8 * hash1('mr', j), 11, 12), ['#E79A5A', '#5C7FB0', '#D8584A', '#6E9A4E', '#F2C14E'][j], key=f'msp{j}', tex=.2, edge=.1)
    # ink bottle
    ib = 1400
    fill(rrect(ib - 60, 470, 120, 130, 22), '#2B2A35', key='ink1', tex=.3, edge=.3, outline=2.5)
    fill(rect(ib - 30, 440, 60, 36), '#4A4954', key='ink2', tex=.3, edge=.2, outline=2)
    wash(ell(ib - 25, 520, 12, 30, 12), '#6A6A80', key='inkh', a=150)
    # eraser + loose papers
    fill(np.array([(1650, 720), (1820, 700), (1840, 760), (1665, 785)]), '#E8DDC4', key='lp1', tex=.4, edge=.3, outline=2)
    fill(np.array([(80, 760), (300, 740), (320, 860), (95, 880)]), '#E8DDC4', key='lp2', tex=.4, edge=.3, outline=2)
    scribble_line(110, 790, 170, 'lp2s', '#7A7484', 1.6, 5); scribble_line(110, 830, 140, 'lp2t', '#7A7484', 1.6, 5)
    fill(rrect(1560, 860, 150, 70, 14), '#9FB6C8', key='eraser', tex=.4, edge=.3, outline=2)
    # main sheet (centre) where Brush is drawn
    fill(np.array([(640, 700), (1290, 690), (1310, 930), (620, 945)]), '#F0E7D2', key='sheet', tex=.35, edge=.3, outline=2.2)
    if lamp > 0:
        glow(960, 820, 520, '#FFC86A', .18 * lamp)

def desk_night(lamp, k=1.0):
    """darken everything when the lamp is off (screen space)"""
    a = int(150 * (1 - lamp) * k)
    if a <= 0: return
    p = skia.Paint(Color=hexc('#3C4470', a)); p.setBlendMode(skia.BlendMode.kMultiply)
    CTX.canvas.drawRect(skia.Rect.MakeXYWH(0, 0, W, H), p)

# ============================================================ 2. CODE WORLD
def codeworld(t, o=None):
    o = o or {}
    hz = o.get('horizon', 640)
    bg('#F1E8D4')
    grad_rect(-1500, -800, W + 3000, hz + 800, ['#EEE4CE', '#F3EBDA', '#F6EFDF'], [0, .7, 1])
    # sun disc
    fill(ell(1480, hz - 210, 90, 90, 32), '#F0B070', key='sun', tex=.4, edge=.2, a=220)
    # cloud band
    for i in range(16):
        cx = -500 + i * 190 + 40 * math.sin(i * 2.1) + math.sin(t * .3 + i) * 6
        r = 90 + 60 * hash1('cc', i)
        cy = hz - 40 - r * .45 - 30 * hash1('cy', i)
        circ = [(cx, cy, r * .7), (cx - r * .7, cy + r * .2, r * .5), (cx + r * .75, cy + r * .15, r * .55), (cx + r * .2, cy - r * .4, r * .5)]
        fillpath(blob_union(circ, f'cl{i}', 1.5), '#C2D3EA' if i % 2 else '#B3C8E6', key=f'cl{i}', tex=.5, edge=.35, a=240, outline=1.6, ocol='#4A6496')
    # block skyline
    for i in range(22):
        bw = 34 + 20 * hash1('bw', i); bh = 40 + 170 * hash1('bh', i) ** 1.5
        bx = -400 + i * 125 + 40 * hash1('bx', i)
        if 520 < bx < 1300 and bh > 90: bh *= .45
        col = ['#5E7FB8', '#8FA9D6', '#E79A5A', '#3F5E99', '#B7C7E4'][i % 5]
        fill(rect(bx, hz - bh, bw, bh), col, key=f'bl{i}', tex=.5, edge=.35, outline=1.8)
    # floating squares
    for i in range(18):
        fx = -300 + hash1('fx', i) * 2500; fy = 40 + hash1('fy', i) * (hz - 200)
        fy += math.sin(t * 1.4 + i) * 10
        s = 16 + 14 * hash1('fs', i)
        fill(rect(fx, fy, s, s), ['#E79A5A', '#8FA9D6', '#5E7FB8'][i % 3], key=f'fq{i}', tex=.2, edge=.2, a=220)
    # code lines in the sky
    lines = o.get('lines', 9)
    L = [(560, 70, 520, '{'), (600, 130, 430, ''), (600, 185, 480, ''), (640, 240, 300, ''), (600, 295, 520, ''), (560, 350, 260, '}'),
         (1250, 70, 300, '('), (1250, 130, 280, ''), (260, 120, 220, '')]
    for i, (lx, ly, ln, br) in enumerate(L):
        k = clamp(lines - i)
        if k <= 0: continue
        scribble_line(lx, ly, ln, f'code{i}', NAVY, 4.2, 9, k=easeOut(k))
        ink(catmull([(lx - 22, ly - 22), (lx - 34, ly), (lx - 22, ly + 22)], False, 6), 4.2, NAVY, key=f'cp{i}', closed=False, a=int(255 * clamp(k * 3)))
    # giant braces
    for side, bx in ((-1, 300), (1, 1620)):
        if o.get('noBraces'): break
        P = brace_pts(bx, hz - 590, 280, 585, side)
        Ps = P + np.array([side * 22, 16])
        fill(Ps, NAVY, key=f'brs{side}', tex=.4, edge=.2, outline=2.5)
        fill(P, '#E9D6B2', key=f'br{side}', tex=.6, edge=.45, outline=3)
    # ruler + compass
    fill(np.array([(-40, hz + 30), (190, hz + 30), (-40, hz - 300)]), '#E7D2AE', key='ruler', tex=.5, edge=.4, outline=2.5)
    fill(np.array([(20, hz), (110, hz), (20, hz - 120)]), '#F1E8D4', key='ruler2', tex=0, edge=.2, outline=2)
    cxp = 1730
    ink([(cxp, hz - 300), (cxp - 70, hz + 20)], 12, '#5C6070', key='cmp1', closed=False, var=.05)
    ink([(cxp, hz - 300), (cxp + 60, hz + 20)], 12, '#5C6070', key='cmp2', closed=False, var=.05)
    fill(ell(cxp, hz - 300, 18, 18, 14), '#3F4350', key='cmp3', tex=0, edge=0, outline=2)
    # floor
    fill(np.array([(-1500, hz), (W + 1500, hz), (W + 1500, 2600), (-1500, 2600)]), '#EEE2C6', key='floor', tex=.45, edge=0, amp=.3)
    vx, vy = 960, hz - 260
    c = CTX.canvas
    for i in range(-24, 25):
        x1 = 960 + i * 150
        ax = vx + (x1 - vx) * ((hz - vy) / (1400 - vy))
        ink([(ax, hz), (x1 + (x1 - vx) * .9, 2400)], 1.8, '#8FA2C4', key=f'gv{i}', closed=False, amp=.5, a=200)
    for j in range(16):
        yy = hz + 12 + (j ** 1.75) * 9
        ink([(-1500, yy), (W + 1500, yy)], 1.8, '#8FA2C4', key=f'gh{j}', closed=False, amp=.5, a=200)
    # colour tiles + cubes on the floor
    for i, (tx, ty, tw, col) in enumerate(((180, hz + 120, 90, '#E79A5A'), (1600, hz + 200, 110, '#5E7FB8'), (1380, hz + 60, 60, '#E79A5A'),
                                          (420, hz + 330, 130, '#8FA9D6'), (1700, hz + 380, 140, '#E79A5A'))):
        fill(np.array([(tx, ty), (tx + tw, ty), (tx + tw * 1.1, ty + tw * .35), (tx + tw * .05, ty + tw * .35)]), col, key=f'tl{i}', tex=.3, edge=.2, a=200)
    for i, (cx, cy, s) in enumerate(((-60, hz + 260, 150), (1860, hz + 140, 120))):
        fill(rect(cx, cy - s * .7, s, s * .7), '#F2EAD8', key=f'cb{i}', tex=.4, edge=.4, outline=2.5)
        fill(np.array([(cx, cy - s * .7), (cx + s, cy - s * .7), (cx + s * 1.15, cy - s * .9), (cx + s * .15, cy - s * .9)]), '#FBF6EA', key=f'cbt{i}', tex=.2, edge=.3, outline=2.5)
        for k in range(1, 4):
            ink([(cx + k * s / 4, cy - s * .7), (cx + k * s / 4, cy)], 1.4, '#8FA2C4', key=f'cbl{i}{k}', closed=False, a=180)

def brace_pts(x, y, w, h, side):
    """curly brace outline. side -1 '{' (hooks point right), +1 '}'"""
    s = -side
    spine = [(x + s * w * .42, y), (x + s * w * .12, y + h * .02), (x, y + h * .12), (x, y + h * .36), (x - s * w * .1, y + h * .455),
             (x - s * w * .3, y + h * .5), (x - s * w * .1, y + h * .545), (x, y + h * .64), (x, y + h * .88), (x + s * w * .12, y + h * .98), (x + s * w * .42, y + h)]
    S = catmull(spine, False, 8)
    d = np.gradient(S, axis=0); nrm = np.stack([-d[:, 1], d[:, 0]], 1); nrm /= np.hypot(nrm[:, 0], nrm[:, 1])[:, None]
    ss = np.linspace(0, 1, len(S))
    wd = (w * .15) * (.25 + .75 * np.sin(np.pi * np.clip(ss * 1.05 - .025, 0, 1)) ** .6) * (1 - .85 * np.exp(-((ss - .5) / .07) ** 2))
    A = S + nrm * wd[:, None]; B = S - nrm * wd[:, None]
    return np.vstack([A, B[::-1]])

# ============================================================ 3. AI DREAM CLOUD
def dream(t, o=None):
    o = o or {}
    hz = o.get('horizon', 640)
    bg('#8FCFCB')
    grad_rect(-1500, -800, W + 3000, hz + 900, ['#5FA9BE', '#7EC3C6', '#B5E0D4', '#E9F4E2'], [0, .45, .8, 1])
    glow(960, hz - 60, 700, '#FFF6D8', .35)
    # far stars
    for i in range(16):
        sx, sy = hash1('ds', i) * W, 40 + hash1('dy', i) * 360
        tw = .5 + .5 * math.sin(t * 3 + i * 1.7)
        if tw > .3: sparkle(sx, sy, 6 + 6 * tw, f'dst{i}', '#FFFBEA', int(255 * tw))
    # glowing ring
    rk = o.get('ring', 1.0)
    for i in range(22):
        a = math.pi + i * math.pi / 21 * 1.0
        if i / 22 > rk: break
        px, py = 960 + 230 * math.cos(a), hz - 20 + 230 * math.sin(a)
        fill(rrect(px - 10, py - 18, 20, 36, 8), '#EFFFF7', key=f'rg{i}', tex=0, edge=.1, a=220)
    glow(960, hz - 140, 320, '#C8FFF0', .3 * rk)
    # floating image tiles
    tiles = ((260, 230, 150, -.06), (420, 470, 130, .05), (1450, 210, 140, .04), (1330, 470, 120, -.05), (1660, 520, 150, .03), (170, 640, 120, .02))
    for i, (tx, ty, s, rot) in enumerate(tiles):
        ty += math.sin(t * 1.1 + i * 1.3) * 12
        _tile(tx, ty, s, rot, i, t)
    # pixel motes rising
    for i in range(34):
        per = 5 + 3 * hash1('pm', i)
        ph = ((t / per) + hash1('pp', i)) % 1
        px = hash1('px', i) * 2300 - 190
        py = hz + 300 - ph * 900
        s = 12 + 14 * hash1('pz', i)
        a = int(220 * math.sin(math.pi * ph))
        fill(rect(px, py, s, s), ['#D6FFF1', '#A6EAD6', '#C9C2F0'][i % 3], key=f'pmt{i}', tex=0, edge=.15, a=a)
    # cloud banks (back -> front)
    _clouds(hz - 90, 13, '#C2B4E6', 'cA', 160, t, 0.3)
    _clouds(hz + 10, 11, '#A7E3CF', 'cB', 210, t, 0.6)
    # floor of cloud
    fill(np.array([(-1500, hz + 70), (W + 1500, hz + 70), (W + 1500, 2600), (-1500, 2600)]), '#D5F0E4', key='dfl', tex=.35, edge=0, amp=.3)
    for j in range(6):
        scribble_line(-200 + 300 * hash1('fl', j), hz + 150 + j * 70 + j * j * 10, 900 + 600 * hash1('flw', j), f'dfs{j}', '#A9D9C8', 3, 8, a=160)
    if not o.get('noFront'):
        _clouds(1180, 9, '#BBA9E2', 'cC', 260, t, 1.0, xs=(-600, 2500))

def _clouds(y, n, col, key, r0, t, drift, xs=(-500, 2400)):
    for i in range(n):
        x = xs[0] + (xs[1] - xs[0]) * i / max(1, n - 1) + 60 * math.sin(i * 2.7) + math.sin(t * .25 + i) * 8 * drift
        r = r0 * (.7 + .5 * hash1(key, i))
        circ = [(x, y - r * .2, r * .62), (x - r * .55, y + r * .05, r * .45), (x + r * .6, y + r * .02, r * .5),
                (x - r * .2, y - r * .55, r * .45), (x + r * .3, y - r * .45, r * .38), (x - r * 1.0, y + r * .25, r * .3), (x + r * 1.05, y + r * .25, r * .32)]
        path = blob_union(circ, f'{key}{i}', 1.5)
        fillpath(path, col, key=f'{key}{i}', tex=.45, edge=.35, a=245)
        wash(ell(x - r * .25, y - r * .55, r * .35, r * .18, 18), mix(col, '#FFFFFF', .55), key=f'{key}h{i}', a=140)

def _tile(x, y, s, rot, i, t):
    c = CTX.canvas
    c.save(); c.translate(x, y); c.rotate(math.degrees(rot))
    glow(0, 0, s * 1.1, '#E8FFF4', .25)
    fill(rect(-s / 2 - 10, -s / 2 - 10, s + 20, s + 20), '#F4FBF4', key=f'tf{i}', tex=.2, edge=.3, outline=2)
    sky = ['#F3C8A0', '#BFD9EE', '#CFE6C9', '#F0D4E0', '#BFD9EE', '#F3C8A0'][i % 6]
    fill(rect(-s / 2, -s / 2, s, s), sky, key=f'ts{i}', tex=.3, edge=.2)
    if i % 3 == 2:
        fill(ell(0, s * .1, s * .2, s * .2, 18), '#4F8A5A', key=f'tt{i}', tex=.3, edge=.2)
        ink([(0, s * .25), (0, s * .5)], 4, '#5B4630', key=f'ttk{i}', closed=False)
    else:
        fill(np.array([(-s / 2, s * .5), (-s * .15, -s * .1), (s * .1, s * .2), (s * .3, 0), (s / 2, s * .3), (s / 2, s * .5)]), '#7C8FB8' if i % 2 else '#6F9A8E', key=f'tm{i}', tex=.3, edge=.2)
        fill(ell(s * .25, -s * .25, s * .1, s * .1, 14), '#FFE9B0', key=f'tsn{i}', tex=0, edge=0)
    c.restore()

# ============================================================ 4. SHARED STAGE
def stage(t, o=None):
    o = o or {}
    hz = o.get('horizon', 700)
    play = o.get('play', .4)
    bg('#3B5568')
    grad_rect(-1500, -800, W + 3000, hz + 800, ['#2C3E52', '#3E5E70', '#577C84'], [0, .6, 1])
    # light cone from the play orb
    cone = np.array([(900, 220), (1020, 220), (1420, hz + 120), (500, hz + 120)])
    cp = skia.Paint(AntiAlias=True)
    cp.setShader(skia.GradientShader.MakeLinear([(960, 220), (960, hz + 100)], [hexc('#FFF0B0', int(80 + 70 * play)), hexc('#FFF0B0', 15)]))
    cp.setBlendMode(skia.BlendMode.kPlus)
    CTX.canvas.drawPath(topath(boil(densify(cone, True, 20), 'cone', 3)), cp)
    # left: grid-paper cutout scenery
    for i, (cx, cy, r) in enumerate(((300, hz - 160, 110), (420, hz - 230, 120), (560, hz - 150, 100), (780, hz - 110, 80))):
        fill(ell(cx, cy, r, r * .8, 26), '#E9DDC2', key=f'gp{i}', tex=.4, edge=.4, outline=2.5)
        c = CTX.canvas; c.save(); c.clipPath(topath(ell(cx, cy, r, r * .8, 26)), doAntiAlias=True)
        for k in range(-6, 7):
            ink([(cx + k * 30, cy - r), (cx + k * 30, cy + r)], 1.2, '#9AA9C6', key=f'gpv{i}{k}', closed=False, a=170)
            ink([(cx - r, cy + k * 30), (cx + r, cy + k * 30)], 1.2, '#9AA9C6', key=f'gph{i}{k}', closed=False, a=170)
        c.restore()
    fill(rect(600, hz - 260, 40, 260), '#E9DDC2', key='trunk', tex=.4, edge=.4, outline=2.5)
    # right: pixel clouds
    for i in range(60):
        gx = 1300 + (i % 12) * 52 + (hash1('pcx', i) - .5) * 20
        gy = hz - 40 - (i // 12) * 50 - hash1('pcy', i) * 120 * (1 - abs((i % 12) - 6) / 7)
        s = 46
        col = ['#7FD3BC', '#A6E6D2', '#5DB9A2', '#C4F0E2'][i % 4]
        fill(rect(gx, gy, s, s), col, key=f'pxc{i}', tex=.3, edge=.25, outline=1.4)
    # floor: half paper, half pixels
    fill(np.array([(-1500, hz), (960, hz), (960, 2600), (-1500, 2600)]), '#EADFC6', key='sfl', tex=.45, edge=0, amp=.3)
    fill(np.array([(960, hz), (W + 1500, hz), (W + 1500, 2600), (960, 2600)]), '#9FDCCB', key='sfr', tex=.4, edge=0, amp=.3)
    for j in range(12):
        yy = hz + 10 + j ** 1.7 * 10
        ink([(-1500, yy), (960, yy)], 1.6, '#9AA9C6', key=f'sgh{j}', closed=False, a=180)
    for i in range(-14, 1):
        x1 = 960 + i * 130
        ink([(960 + (x1 - 960) * .35, hz), (x1 - (960 - x1) * .8, 2400)], 1.6, '#9AA9C6', key=f'sgv{i}', closed=False, a=180)
    for i in range(40):
        px = 980 + hash1('fpx', i) * 1300; py = hz + 20 + hash1('fpy', i) ** 1.4 * 420
        s = 26 + 30 * hash1('fps', i)
        fill(rect(px, py, s, s * .55), ['#7FD3BC', '#C4F0E2', '#5DB9A2'][i % 3], key=f'fpx{i}', tex=.2, edge=.2, outline=1.2)
    # spotlight pool
    glow(960, hz + 170, 520, '#FFE9A8', .28 + .2 * play)
    # curtains
    for side in (-1, 1):
        x0 = -200 if side < 0 else W + 200
        inner = 250 if side < 0 else W - 250
        P = np.array([(x0, -200), (inner, -200), (inner - side * 40, 300), (inner + side * 25, 700), (inner - side * 10, hz + 260), (x0, hz + 260)])
        fill(catmull(P, True, 6), '#C2532A', key=f'cur{side}', tex=.5, edge=.5, outline=3)
        for k in range(5):
            fx = lerp(x0, inner, (k + .5) / 5)
            ink([(fx, -100), (fx + side * 10, 300), (fx - side * 6, hz + 240)], 9, '#8E3519', key=f'cf{side}{k}', closed=False, a=150)
        fill(ell(inner - side * 10, 560, 26, 40, 14), '#E2A33A', key=f'tie{side}', tex=.3, edge=.3, outline=2)
    # valance
    P = [(-300, -200), (W + 300, -200), (W + 300, 70)]
    for k in range(13, -1, -1):
        x = -300 + k * (W + 600) / 13
        P += [(x + 80, 90), (x, 60)]
    fill(np.array(P), '#B74A25', key='val', tex=.5, edge=.4, outline=3)
    # filmstrip arcs
    for side in (-1, 1):
        S = [(960 + side * 190, 120), (960 + side * 450, 80), (960 + side * 760, 140)]
        S = catmull(S, False, 12)
        d = np.gradient(S, axis=0); nrm = np.stack([-d[:, 1], d[:, 0]], 1); nrm /= np.hypot(nrm[:, 0], nrm[:, 1])[:, None]
        A, B = S + nrm * 62, S - nrm * 62
        fill(np.vstack([A, B[::-1]]), '#3D3C46', key=f'fs{side}', tex=.3, edge=.3, outline=2.5)
        for k in range(4, len(S) - 3, 6):
            fx, fy = S[k]
            fill(rect(fx - 38, fy - 36, 76, 72), '#D9CDB4', key=f'ff{side}{k}', tex=.3, edge=.2, outline=1.5)
        for k in range(1, len(S) - 1, 2):
            for m in (52, -52):
                hx, hy = S[k] + nrm[k] * m
                wash(rect(hx - 6, hy - 5, 12, 10), '#D9CDB4', key=f'sp{side}{k}{m}')
    # hanging stars
    for i, (sx, sl) in enumerate(((330, 150), (520, 260), (1400, 260), (1590, 160), (1780, 120))):
        sy = 60 + sl + math.sin(t * 2 + i) * 6
        ink([(sx, 40), (sx, sy - 22)], 1.6, '#D9C89A', key=f'str{i}', closed=False, a=200)
        fill(star_pts(sx, sy, 30, .45, 5, math.sin(t * 1.5 + i) * .15), '#F2C14E', key=f'st{i}', tex=.2, edge=.3, outline=2)
        glow(sx, sy, 80, '#FFD970', .25)
    # play orb
    px, py, pr = 960, 190, 92
    glow(px, py, 380, '#7DFFD8', .25 + .5 * play)
    for k in range(14):
        a = k * 2 * math.pi / 14 + t * .2
        r0, r1 = pr * 1.3, pr * (1.55 + .35 * play)
        ink([(px + r0 * math.cos(a), py + r0 * math.sin(a)), (px + r1 * math.cos(a), py + r1 * math.sin(a))], 5, '#F7E7A0', key=f'ray{k}', closed=False, a=int(120 + 135 * play))
    fill(ell(px, py, pr, pr, 40), mix('#4FB59C', '#8FF0D2', play), key='orb', tex=.3, edge=.4, outline=3.5)
    fill(ell(px, py, pr * .78, pr * .78, 40), mix('#6FCFB6', '#C8FFEE', play), key='orb2', tex=.2, edge=.2)
    fill(np.array([(px - 28, py - 42), (px - 28, py + 42), (px + 44, py)]), '#F6FFF9', key='tri', tex=0, edge=.15, outline=2.5)
