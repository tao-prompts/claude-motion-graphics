# scenes3.py — v3: eight environments, props, integrated lyric text.
#  S1  0.00- 3.40 DESK          editor types Brush, run, dive into the screen
#  S2  3.40- 9.15 CODE WORLD    compiled by scanline; "made_with(code)" types into the sky behind him   [light whip]
#  S3  9.15-12.75 GPU CITY      surfs the palette hoverboard down the trace road; onion-skin frames;
#                               EVERY_FRAME == MINE lights up on the road; portal opens, he leaps in   [shiny squares]
#  S4 12.75-20.00 NEURAL GARDEN Render diffuses from noise + GENERATING bar; made_with(AI) forms in the
#                               constellation; prompt -> clones; merge   [iris on halo]
#  S6 20.00-24.05 DATA HIGHWAY  both race in on the lanes (hoverboard / cursor ship); CODE / AI paint onto
#                               their lanes   [cut on jump]
#  S7 24.05-26.40 STAGE         two-shot plate, giant play keycap slams, press_play() glows in the light   [flash]
#  S8 26.40-29.05 TIMELINE      running along the edit; lyrics typed as clips on the tracks   [brush wipe]
#  S8b29.05-31.30 DREAM CLOUD   dance party: clones, light ribbon, pixel fireworks, glowing notes   [code rain]
#  S9 31.30-35.40 STAGE         ring, ink splash + pixel firework high-five, come_alive() on the backdrop
#  S10 35.4-40.0  DESK          pull back; cursor ship flies out of the monitor; lamp off; end title
import math
import numpy as np
import skia
import scenes2 as S2
from scenes2 import *
from engine import *
from chars import *
from envs import desk, desk_night, codeworld, dream, stage, scribble_line
from envs2 import gline, gbox, particles, light_whip, data_rain_wipe, dive_streaks, _ps
from envs3 import *
from props import *
from fxtext import code_text, lettering, gen_bar, glyphs, text_width

SHOW_TEXT = True
OR, TE, LV = '#FF9A4A', '#5FF2D0', '#B79CFF'

def on_quad(fn, src, dst):
    """draw fn() in a local rectangle src=(x,y,w,h) mapped onto quad dst [(tl),(tr),(br),(bl)]"""
    x, y, w, h = src
    m = skia.Matrix()
    ok = m.setPolyToPoly([skia.Point(x, y), skia.Point(x + w, y), skia.Point(x + w, y + h), skia.Point(x, y + h)],
                         [skia.Point(*p) for p in dst])
    c = CTX.canvas; c.save(); c.concat(m); fn(); c.restore()

# ================================================================ S2 patches (text in the sky behind Brush)
S2.LINES_S2 = [(1170, 400, 280, ''), (1200, 460, 240, ''), (1180, 520, 260, ''), (1190, 580, 230, '')]
_orig_rain = S2.code_rain
def _rain_and_text(t, key='rain', n=34, y1=600):
    _orig_rain(t, key, n, y1)
    if SHOW_TEXT and 3.4 < t < 9.2:
        code_text(t, 'made_with(code)', 520, 470, 42, 5.45, 8.6, cols=(OR, '#FFC27A'), style='type', panel=False, scan=False, key='mwc', dur_in=.8)
        code_text(t, 'line_by_line();', 520, 545, 42, 6.86, 8.6, cols=('#3FCFB0',), style='decode', panel=False, scan=False, key='lbl', dur_in=.9)
S2.code_rain = _rain_and_text

# ================================================================ S3 GPU CITY ride
def s3_z(t):
    return kf(t, [(9.15, .05), (10.0, .22), (10.6, .42), (11.0, .6)], lambda k: k)
def s3_x(t):
    return .5 * math.sin((t - 9.15) * 2.4) * clamp((t - 9.15) * 1.5)
def s3(t):
    core = .5 + .5 * ease(seg(t, 12.0, 12.3))
    sh = shake(t, 11.35, 14)
    cz = kf(t, [(9.15, 1.0), (11.9, 1.03), (12.25, 1.1)], ease)
    cam_begin(960 + sh[0], 540 + sh[1], cz)
    gpucity(t, dict(core=core))
    # road lettering
    if SHOW_TEXT and t > 10.3:
        k_out = seg(t, 12.25, 12.55)
        if k_out < 1:
            ya, wa = road_pt(.36, 0)[1], 0
            q = road_quad(.5, .7, 150 * 1.0, 1200)
            dst = [tuple(q[0]), tuple(q[1]), tuple(q[2]), tuple(q[3])]
            def txt():
                code_text(t, 'EVERY_FRAME == MINE', 40, 150, 104, 10.35, 12.3 if t > 12.3 else None, cols=(OR, '#FFD66B'), style='flicker', panel=False, scan=False, key='efm', dur_in=1.1)
            on_quad(txt, (0, 0, 1240, 200), dst)
    # portal behind him (mid-road)
    pk = seg(t, 11.55, 11.95)
    PX, PY, ps_ = road_pt(.3, 0)
    if pk > 0:
        portal(PX, PY - 150 * ps_ - 60, 160, t, pk * (1 + .3 * seg(t, 12.25, 12.6)), key='p3')
    u0 = 27
    def rider(tt, alpha=255, keyp='B'):
        z = s3_z(tt); xo = s3_x(tt)
        x, y, sc = road_pt(z, xo)
        hov = 26 * sc + 6 * math.sin(tt * 5)
        lean = .25 * math.cos((tt - 9.15) * 2.4)
        return x, y - hov, sc, lean
    # onion-skin frames + light trail while riding
    if t < 11.05:
        for q in (3, 2, 1):
            tt = t - q * .09
            if tt < 9.15: continue
            x, y, sc, lean = rider(tt)
            ghost(45 * (4 - q), lambda: (code_board(x, y + 4, sc * 1.0, lean * .3, 0, key=f'gpb{q}'),
                                         brush(x, y, u0 * sc, dict(eyes='happy', mouth='grin', sq=.12, rot=lean * .4, aL=.6, aR=.2, noShadow=True, key=f'GB{q}', seed=1.9))))
        TP = []
        for q in range(10):
            tt = t - q * .05
            if tt < 9.15: break
            x, y, sc, _ = rider(tt); TP.append((x, y + 30 * sc))
        if len(TP) > 2: gline(np.array(TP), TE, 8, key='tr3', a=.9)
    x, y, sc, lean = rider(min(t, 11.05))
    face = faces(t, [(0, dict(eyes='happy', mouth='grin')), (10.5, dict(eyes='dot', mouth='smile')), (11.05, dict(eyes='wide', mouth='O')),
                     (11.5, dict(eyes='dot', mouth='smile')), (12.06, dict(eyes='happy', mouth='grin'))])
    o = dict(face, seed=1.9, mouthOpen=sing(t, BRUSH_W), hair=-.3)
    if t < 11.05:
        code_board(x, y + 4, sc * 1.0, lean * .3, 1.0, key='pb3')
        o.update(sq=.12, rot=lean * .4, aL=.6, aR=.2, noShadow=True, head=.0)
        brush(x, y, u0 * sc, o)
    else:
        # hop off the board, land in front, board flies off
        k = seg(t, 11.05, 11.35)
        lx, ly, lsc = road_pt(.8, .1)
        bx_, by_ = arcPt((x, y), (lx, ly), 200, ease(k))
        uu = lerp(u0 * sc, u0 * lsc, ease(k))
        bk = seg(t, 11.05, 11.8)
        if bk < 1:
            code_board(lerp(x, 2300, easeIn(bk)), lerp(y, 200, easeIn(bk)), sc * 1.0, bk * 6, 1.0, key='pb3')
        _, s_ = jump(t, 11.05, 11.35, 0)
        if t < 11.35: s_ = -.15
        o.update(sq=s_ + take(t, 12.06, .28), head=0.0 if t > 11.5 else .15)
        if t > 12.0: o.update(aLpos=(bx_ - 1.1 * uu, by_ - 9.0 * uu), aRpos=(bx_ + 1.1 * uu, by_ - 9.0 * uu), aLbend=-1.2, aRbend=-1.2)
        if t > 12.25:
            kj = seg(t, 12.25, 12.6)
            jx, jy = arcPt((bx_, by_), (PX, PY - 150 * ps_), 300, easeIn(kj))
            o.update(eyes='happy', mouth='open', aL=1.3, aR=1.3, sq=-.15, noShadow=True, aLpos=None, aRpos=None)
            brush(jx, jy, uu * (1 - .75 * kj), o)
        else:
            brush(bx_, by_, uu, o)
        if 12.06 < t < 12.3: emote('spark', bx_ + 6 * uu, by_ - 23 * uu, 60, seg(t, 12.06, 12.2), key='s3sp')
    cam_end()
    if t < 9.35: light_whip(seg(t, 8.95, 9.35))
    if t > 12.5: wipe_shiny(seg(t, 12.5, 13.0), 'pd1')

# ================================================================ S4 NEURAL GARDEN (reuse v2 S4 with the garden as the world)
def _garden_world(t, o=None):
    garden(t, dict(beam=1.0 - .6 * seg(t, 13.6, 14.2)))
    if SHOW_TEXT:
        code_text(t, 'made_with(AI)', 960, 455, 76, 13.55, 15.5, cols=(TE, '#C9F7EA', LV), style='pixel', align='center', panel=False, scan=False, key='mwa', dur_in=.9)
        if t > 18.1:
            code_text(t, 'ready_for_the_show', 960, 300, 78, 18.25, 19.6, cols=('#FFD66B', OR), style='decode', align='center', panel=False, scan=False, key='rfs', beat=10, dur_in=.8)
        if 17.2 < t < 18.5:
            lettering(t, 'x6!', 1250, 330, 130, 17.24, 18.1, face='toon', cols=('#FFD66B',), style='pop', key='x6', glowcol='#FFD66B')
S2.dream = _garden_world
def s4(t):
    S2.s4(t)
    if SHOW_TEXT and 13.0 < t < 14.4:
        gen_bar(t, 960, 985, 560, 13.0, 13.55, key='genR')

# ================================================================ S6 DATA HIGHWAY
def s6_s(t):
    # ride the winding road the whole shot: fast at first, then a cruise
    return kf(t, [(20.0, .22), (21.7, .47), (24.05, .53)], lambda k: 1 - (1 - k) ** 2)
def rider_u(sc, base):
    return base * (max(sc, .02) / .35) ** .6
def s6_riders(t):
    s = s6_s(t)
    bx, by, bsc = hw_lane(s, -1.7)
    rx, ry, rsc = hw_lane(s + .012, 1.9)
    u_ = rider_u(bsc, 25)
    return s, (bx + 4 * u_, by, bsc), (rx - 7 * u_, ry - 1 * u_, rsc)
def s6_cam(t):
    s, (bx, by, bsc), (rx, ry, rsc) = s6_riders(t)
    bu = rider_u(bsc, 25)
    z = kf(t, [(20.0, 2.3), (21.7, 1.25), (24.05, 1.12)], ease)
    cx, cy = (bx + rx) / 2 + 60, (by + ry) / 2 - 7 * bu
    sh = math.sin(t * 13) * 3 * (1 - seg(t, 21.5, 22))
    return cx + sh, cy, z
def s6(t):
    cx, cy, z = s6_cam(t)
    cam_begin(cx, cy, z, -3 * (1 - seg(t, 20.5, 21.8)))
    def ft(t):  # integrated flow speed (fast while riding, cruise after)
        if t < 21.5: return 2.5 * t
        if t < 22.2: x = t - 21.5; return 2.5 * 21.5 + 2.5 * x - 1.5 * x * x / (2 * .7)
        return 2.5 * 21.5 + 2.5 * .7 - 1.5 * .7 / 2 + (t - 22.2)
    highway(t, dict(ft=ft(t)))
    s, (bx, by, bsc), (rx, ry, rsc) = s6_riders(t)
    bob = math.sin(t * 4) * 6
    bu, ru = rider_u(bsc, 25), rider_u(rsc, 28)
    # light trails along their lanes + wind streaks rushing past
    for lane, col, kk, sv in ((-1.7, OR, 'tb', s), (1.9, TE, 'tr', s + .012)):
        P = [hw_lane(max(0, sv - d), lane)[:2] for d in np.linspace(0, .12, 12)]
        gline(np.array(P), col, 10 * rider_u(hw_lane(sv, lane)[2], 1) + 3, key=kk, a=.95)
    spd = 1 - .6 * seg(t, 21.5, 22.2)
    for i in range(10):
        ph = ((t * 2.2 + hash1('ws', i)) % 1.0)
        ox = (hash1('wx', i) - .5) * 30 * bu; oy = -hash1('wy', i) * 20 * bu
        x0, y0 = (bx + rx) / 2 + ox + (1 - ph) * 9 * bu, (by + ry) / 2 + oy - (1 - ph) * 5 * bu
        gline([(x0, y0), (x0 + 5 * bu * spd, y0 - 3 * bu * spd)], '#FFF3D8' if i % 2 else '#D8FFF4', 2.5, key=f'wind{i}', a=.6 * math.sin(math.pi * ph) * spd)
    # lyric words rise up out of the road behind each rider
    for word, t0, cols, keyw, (lx, ly) in (('CODE', 22.6, (OR, '#FFD66B'), 'lc', (bx + 14 * bu, by - 12 * bu)), ('AI', 23.15, (TE, '#C9F7EA'), 'la', (rx - 9 * ru, ry - 5 * ru))):
        if SHOW_TEXT and t > t0 - .1:
            c = CTX.canvas; c.save(); c.translate(lx, ly); sc_ = bu / 30; c.scale(sc_, sc_)
            rise = easeOut(seg(t, t0, t0 + .3))
            glow(0, 0, 160, cols[0], .5 * rise)
            code_text(t, word, 0, -10 - 30 * rise, 150, t0, None, cols=cols, style='pixel' if keyw == 'la' else 'type', align='center', panel=False, scan=False, key=keyw, dur_in=.3)
            c.restore()
    # Render on the cursor ship (lane behind)
    rface = faces(t, [(0, dict(eyes='happy', mouth='smile')), (21.95, dict(eyes='wide', mouth='O')), (22.15, dict(eyes='narrow', mouth='flat', brows='angry')),
                      (23.2, dict(eyes='happy', mouth='smile', brows=None)), (23.6, dict(eyes='normal', mouth='smile'))])
    ro = dict(rface, seed=2.2, head=.12 if t > 21.7 else 0, sq=take(t, 21.95, .3), mouthOpen=sing(t, BOTH_W[1:3]) if 23.1 < t < 23.9 else 0, glitch=.6, noShadow=True,
              lean=.5 * (1 - seg(t, 21.4, 21.9)))
    if 23.22 < t < 23.9: ro['aL'] = kf(t, [(23.22, -.6), (23.35, .35)])
    if t > 23.9: _, s_ = jump(t, 24.05, 24.3, 2); ro['sq'] = ro.get('sq', 0) + s_
    halo_disc(rx, ry + .2 * ru + bob, ru / 30, 1.0, key='hd6')
    render_bot(rx, ry - .9 * ru + bob, ru, ro)
    # Brush on the palette board
    bface = faces(t, [(0, dict(eyes='happy', mouth='grin')), (21.75, dict(eyes='wide', mouth='O')), (22.05, dict(eyes='narrow', mouth='flat', brows='angry')),
                      (22.66, dict(eyes='happy', mouth='smile', brows=None)), (23.6, dict(eyes='dot', mouth='smile'))])
    riding = t < 21.6
    bo = dict(bface, seed=1.9, head=-.12 if t > 21.7 else 0, sq=take(t, 21.75, .3) + (.12 if riding else 0), noShadow=True,
              mouthOpen=sing(t, BOTH_W[:1]) if 22.5 < t < 23.2 else 0, rot=(-.14 if riding else (-.05 if 22.1 < t < 22.6 else 0)),
              aL=.6 if riding else -1.0, aR=.25 if riding else -1.0, hair=-.45 if riding else 0)
    if 22.62 < t < 23.3:
        bo['aRpos'] = (bx + .3 * bu, by - 10 * bu); bo['aRbend'] = 1.0; bo['aL'] = .4
    if t > 23.9: _, s_ = jump(t, 24.05, 24.3, 2); bo['sq'] = bo.get('sq', 0) + s_
    code_board(bx, by + bob, bu / 24, -.08, 1.0, key='pb6')
    brush(bx, by - 4 + bob, bu, bo)
    if t > 21.75: emote('excl', bx + 4 * bu, by - 26 * bu, 50, seg(t, 21.75, 21.9) * (1 - seg(t, 22.4, 22.5)), key='e6a')
    if t > 21.95: emote('excl', rx + 3 * ru, ry - 9 * ru, 50, seg(t, 21.95, 22.1) * (1 - seg(t, 22.5, 22.6)), key='e6b')
    mx, my = to_screen((bx + rx) / 2, (by + ry) / 2 - 8 * bu)
    cam_end()
    if t < 20.5: iris(mx, my, lerp(0, 2600, easeIn(seg(t, 20.0, 20.5))))

# ================================================================ STAGE extras (S7 keycap + text, S9 backdrop text)
_orig_stage = S2.stage
def _stage_plus(t, o=None):
    _orig_stage(t, o)
    if 24.0 < t < 26.4:
        if t > 24.8:
            k = seg(t, 24.8, 24.98)
            ky = lerp(300, 1010, easeIn(k)) if k < 1 else 1010
            press = math.sin(math.pi * seg(t, 25.0, 25.25))
            keycap(968, ky - 40, 1.0, 'play', '#8EDCCB', 0, press, glowa=.6 + .4 * press, key='kc7')
            if t > 25.0:
                kk = seg(t, 25.0, 25.6)
                gline(ell(968, 1010, 120 + 500 * kk, 30 + 120 * kk, 48), TE, 6, key='kr', closed=True, a=1 - kk)
        if SHOW_TEXT and t < 25.0:
            code_text(t, 'CODE + AI', 965, 430, 110, 24.05, 24.85, cols=(OR, OR, OR, OR, '#FFFFFF', '#FFFFFF', '#FFFFFF', TE, TE), style='flicker', align='center', panel=False, scan=False, key='cai7', dur_in=.15)
        if SHOW_TEXT and t > 25.05:
            code_text(t, 'press_play()', 965, 400, 70, 25.1, 26.15, cols=(TE, '#E8FFF8'), style='decode', align='center', panel=True, scan=True, key='pp', dur_in=.35)
    if 33.5 < t < 35.4:
        k = seg(t, 33.5, 33.9) * (1 - seg(t, 34.88, 35.2))
        for q in range(22):
            ph = q / 22 * 2 * math.pi + (t - 33.5) * 2.4
            d = math.sin(ph)
            if d > 0: continue  # back half sits behind the characters
            x, y = 970 + 430 * math.cos(ph), 840 + 90 * d - 140 * math.sin((t - 33.5) * 3 + q * .3) * .2
            gbox(x, y, 20 + 10 * d, (OR, TE, LV)[q % 3], k * .8, key=f'or9{q}')
    if t > 31.3:
        # finale dressing: sweeping beams, floating props, fireworks on the beat
        for i, (x0, col) in enumerate(((300, OR), (1620, TE), (700, LV), (1220, '#FFD66B'))):
            a_ = math.sin(t * 1.3 + i * 1.7) * .5
            gline([(x0, -50), (x0 + math.sin(a_) * 900, 1100)], col, 30, key=f'beam{i}', a=.25, core=False)
        light_ribbon(960, 560, 640, 330, t, seg(t, 31.5, 32.4), key='lr9')
        gpu_prop(430, 330 + 14 * math.sin(t * 2), .45, .1 * math.sin(t), t, key='gp9')
        keycap(1530, 360 + 12 * math.sin(t * 2.3 + 1), .55, 'play', '#8EDCCB', .15 * math.sin(t * 1.7), key='kc9a')
        keycap(1400, 250 + 12 * math.sin(t * 2.1 + 2), .45, 'enter', '#E8875A', -.2, key='kc9b')
        data_chest(380, 1000, .7, t, 1.0, key='dc9')
        film_reel(1560, 960, .5, t, .7 + .3 * math.sin(t * 2), key='fr9')
        beat_i = int(bp(t))
        for q in range(2):
            bt = OFFSET + (beat_i - q) * BEAT
            fx = 380 + hash1('fwx', beat_i - q) * 1160; fy = 140 + hash1('fwy', beat_i - q) * 280
            pixel_firework(fx, fy, .6, seg(t, bt, bt + 1.0), key=f'fw9{(beat_i - q) % 6}')
        particles(t, 's9more', 36, 250, 1670, 100, 1050, cols=(OR, TE, LV, '#FFD66B'), size=(8, 18))
        confetti(t, 31.6, 40, 'cf9')
    if SHOW_TEXT and 34.6 < t < 37.2:
        code_text(t, 'come_alive();', 960, 400, 120, 34.86, 36.7, cols=('#FFD66B', OR, TE), style='pixel', align='center', panel=False, scan=False, key='cav', dur_in=.5)
S2.stage = _stage_plus

def s7(t):
    S2.s7(t)
    if SHOW_TEXT and t > 26.2:
        code_text(t, 'come_alive()', 960, 300, 120, 26.22, None, cols=('#FFD66B', OR), style='pixel', align='center', panel=False, scan=False, key='ca7', dur_in=.25)

# ================================================================ S8 TIMELINE run
def s8(t):
    cx = kf(t, [(26.4, 760), (29.05, 1160)], lambda k: k)
    cam_begin(cx, 600, 1.08)
    timeline(t)
    # lyric clips on the tracks
    if SHOW_TEXT:
        for word, x0, y0, t0, t1, col, keyw, st in (('you.write(words)', 300, 292, 26.9, 28.6, '#E08A3A', 'yw', 'type'), ('we.make(it.move)', 1000, 292, 27.9, None, '#3FAE8E', 'wm', 'decode')):
            if t < t0: continue
            k = clamp((t - t0) / .7)
            wfull = text_width(word, 'mono', 50) + 50
            hgt = 70
            fill(rrect(x0, y0, max(30, wfull * (k if st == 'type' else 1)), hgt, 12), col, key=keyw + 'clip', tex=.4, edge=.4, outline=3)
            code_text(t, word, x0 + 25, y0 + hgt * .74, 50, t0, t1, cols=('#FFF6E0',), style=st, panel=False, scan=False, key=keyw,
                      wave=6 if keyw == 'wm' and t > 28.2 else 0, dur_in=.6)
            if keyw == 'wm':
                for q in range(5):
                    kx = x0 + 40 + q * 90
                    kp = backOut(seg(t, 28.0 + q * .08, 28.25 + q * .08))
                    if kp > 0:
                        P = np.array([(kx, 262 - 20 * kp), (kx + 14 * kp, 262), (kx, 262 + 20 * kp), (kx - 14 * kp, 262)])
                        glow(kx, 262, 40, '#F2C14E', .5); fill(P, '#F2B84E', key=f'kfp{q}', tex=0, edge=.2, outline=2)
    film_reel(1820, 780, .55, t, .6 + .4 * math.sin(t), key='fr8')
    gy = 880
    bxx = kf(t, [(26.4, 420), (29.05, 1460)], lambda k: k)
    walk = (t - 26.4) * 2.2
    bu, ru = 22, 26
    bface = faces(t, [(0, dict(eyes='happy', mouth='open')), (26.9, dict(eyes=['dot', 'closed'], mouth='grin')), (27.8, dict(eyes='dot', mouth='smile')),
                      (28.4, dict(eyes='wide', mouth='O')), (28.7, dict(eyes='happy', mouth='grin'))])
    bsq = .18 * math.exp(-6 * (t - 28.4)) * math.cos(16 * (t - 28.4)) if t > 28.4 else 0
    bo = dict(bface, seed=1.9, mouthOpen=sing(t, BOTH_W), head=.22, walk=walk, dy=-abs(math.sin(walk * math.pi)) * .3, sq=bsq,
              aL=-1.0 + .5 * math.sin(walk * math.pi * 2), aR=-1.0 - .5 * math.sin(walk * math.pi * 2), rot=.08)
    if 26.9 <= t < 27.8: bo.update(head=0, walk=None, aR=-.35, armLen=3.6, aL=-1.0, dy=0)
    if t >= 28.4: bo['aL'], bo['aR'] = .9, .9
    if 26.9 <= t < 27.8: bxx = kf(26.9, [(26.4, 420), (29.05, 1460)], lambda k: k) + (t - 26.9) * 120
    info = brush(bxx, gy, bu, bo)
    topx, topy = info['top']; seat = (topx, topy - 8.6 * bu)
    rface = faces(t, [(0, dict(eyes='happy', mouth='open')), (26.9, dict(eyes='normal', mouth='grin')), (27.8, dict(eyes='wide', mouth='smile')), (28.5, dict(eyes='happy', mouth='open'))])
    ro = dict(rface, seed=2.2, mouthOpen=sing(t, BOTH_W), glitch=.5, head=.1)
    rxx = bxx + 300
    if t < 27.9:
        ro.update(dy=bounce(t, .5, .25))
        if 26.9 <= t < 27.8: ro.update(aL=0, aR=-.2, head=0)
        render_bot(rxx, gy, ru, ro)
    else:
        k = seg(t, 27.9, 28.4)
        if k < 1:
            px, py = arcPt((rxx, gy), seat, 380, ease(k)); uu = lerp(ru, 16, ease(k))
            ro.update(sq=-.15, aL=1.2, aR=1.2, noShadow=True)
        else:
            px, py = seat; uu = 16
            ro.update(dy=bounce(t, .4, .5), sq=take(t, 28.4, .3), aL=.6 + .6 * abs(math.sin(math.pi * bp(t))), aR=.9, noShadow=True)
        render_bot(px, py, uu, ro)
    cam_end()
    if t < 26.55: flash(1 - seg(t, 26.4, 26.55))
    if SHOW_TEXT and t < 27.6:
        code_text(t, 'come_alive()', 960, 300, 120, 26.22, 27.2, cols=('#FFD66B', OR), style='pixel', out='glitch', align='center', panel=False, scan=False, key='ca7', dur_in=.25)

# ================================================================ S8b DREAM party
CLONE_FACES = [dict(eyes='happy', mouth='open'), dict(eyes='star', mouth='grin'), dict(eyes='heart', mouth='smile'), dict(eyes='happy', mouth='grin'), dict(eyes='normal', mouth='open'), dict(eyes='happy', mouth='smile')]
def orbit_angle(t):
    return 1.7 * (t - 29.05) + .6 * ease(seg(t, 29.05, 29.6))
def s8b(t, inset=False):
    """dance party with an orbiting camera: the world pans, the duo turn through their drawn views,
    and the clones circle them in depth (behind -> in front)."""
    a = orbit_angle(t)
    pan = -a * 420
    rot = -2.0 * math.sin(math.pi * bp(t) * .5)
    cxw = 960 + pan
    cam_begin(cxw, 660, 1.15, rot)
    dream(t, dict(ring=1.0))
    for i, (tb, fx, fy) in enumerate(((29.55, -260, 260), (30.05, 420, 220), (30.55, -60, 160), (31.05, 260, 300))):
        pixel_firework(cxw + fx, fy, .9, seg(t, tb, tb + 1.0), key=f'fw{i}')
    gy, bu = 1010, 24
    R, Rz = 640, 70
    def clone(i):
        ph = a + i * 2 * math.pi / 6
        d = math.sin(ph)  # +1 = in front
        x = cxw + R * math.cos(ph); y = gy - 40 + Rz * d
        sc = 1 + .16 * d
        render_bot(x, y, 18 * sc, dict(CLONE_FACES[i], key=f'P{i}', seed=3 + i, glitch=.6, dy=bounce(t, .5, i * .37), head=-math.cos(ph) * .15,
                                       aL=.5 + .6 * abs(math.sin(math.pi * bp(t) + i)), aR=.5 + .6 * abs(math.cos(math.pi * bp(t) + i)), glow=.15))
    def ring(front):
        n = 48
        for k in range(n):
            p0 = k / n * 2 * math.pi + a * 1.3; p1 = (k + 1) / n * 2 * math.pi + a * 1.3
            if (math.sin(p0) > 0) != front: continue
            P = [(cxw + 640 * math.cos(p0), gy - 300 + 150 * math.sin(p0)), (cxw + 640 * math.cos(p1), gy - 300 + 150 * math.sin(p1))]
            gline(P, OR if k < n / 2 else TE, 9, key=f'orb{k}', a=.9 * seg(t, 29.1, 29.6))
        for q in range(8):
            p = q / 8 * 2 * math.pi - a * 2
            if (math.sin(p) > 0) != front: continue
            sparkle(cxw + 640 * math.cos(p), gy - 300 + 150 * math.sin(p) - 8, 22, f'orbs{q}', '#FFF0B0')
    order = sorted(range(6), key=lambda i: math.sin(a + i * 2 * math.pi / 6))
    ring(False)
    for i in order:
        if math.sin(a + i * 2 * math.pi / 6) <= 0: clone(i)
    spin = (a / (2 * math.pi)) % 1.0
    bo = dict(eyes='happy', mouth='open', seed=1.9, mouthOpen=sing(t, BOTH_W), head=-spin * .999, dy=bounce(t, .25), rot=.08 * math.sin(math.pi * bp(t)),
              aL=.9 + .5 * math.sin(math.pi * bp(t)), aR=.9 - .5 * math.sin(math.pi * bp(t)), hair=.3 * math.sin(math.pi * bp(t)))
    info = brush(cxw, gy, bu, bo)
    topx, topy = info['top']
    render_bot(topx, topy - 8.6 * bu, 17, dict(eyes='happy', mouth='open', seed=2.2, mouthOpen=sing(t, BOTH_W), head=-spin * .999, dy=bounce(t, .4, .5), noShadow=True,
                                                aL=.6 + .6 * abs(math.sin(math.pi * bp(t))), aR=.6 + .6 * abs(math.cos(math.pi * bp(t))), glitch=.5))
    for i in order:
        if math.sin(a + i * 2 * math.pi / 6) > 0: clone(i)
    ring(True)
    if t > 29.7:
        emote('music', cxw - 380, 480, 60, seg(t, 29.7, 29.9), age=t, key='mn1')
        emote('music', cxw + 330, 430, 54, seg(t, 30.0, 30.2), age=t + 1, key='mn2')
    confetti(t, 29.05, 40, 'cf8b')
    cam_end()
    if SHOW_TEXT and t > 29.1:
        code_text(t, 'in_the_groove', 70, 190, 92, 29.15, 30.95, cols=(TE, '#FFD66B', OR), style='pixel', align='left', panel=False, scan=False, key='itg', beat=16, dur_in=.5)
    if not inset and t > 31.0: data_rain_wipe(seg(t, 31.0, 31.6))

# ================================================================ S9 extras: ink splash + pixel firework at the high-five
def s9(t):
    S2.s9(t)
    if 33.5 < t < 35.4:
        cz = kf(t, [(31.3, 1.0), (34.7, 1.0), (35.4, 1.12)], ease)
        cam_begin(960, 560, cz)
        k = seg(t, 33.5, 33.9) * (1 - seg(t, 34.88, 35.2))
        for q in range(22):
            ph = q / 22 * 2 * math.pi + (t - 33.5) * 2.4
            d = math.sin(ph)
            if d <= 0: continue  # only the front half is drawn over the characters
            x, y = 970 + 430 * math.cos(ph), 840 + 90 * d - 140 * math.sin((t - 33.5) * 3 + q * .3) * .2
            gbox(x, y, 20 + 10 * d, (OR, TE, LV)[q % 3], k, key=f'or9{q}')
        cam_end()
    if t > 31.6:
        cz = kf(t, [(31.3, 1.0), (34.7, 1.0), (35.4, 1.12)], ease)
        cam_begin(960, 560, cz)
        ink_splash(RING_C[0] - RING_R + 20, RING_C[1] - 60, 1.0, seg(t, 32.45, 33.3), key='is9a')
        pixel_firework(RING_C[0] + RING_R - 20, RING_C[1] - 60, 1.0, seg(t, 33.45, 34.4), key='pf9a')
        ink_splash(952, 738, 1.3, seg(t, 34.9, 35.6), key='is9b')
        pixel_firework(952, 738, 1.3, seg(t, 34.92, 35.7), key='pf9b')
        cam_end()

# ================================================================ S10 extras: cursor ship escapes the monitor; end title on screen
_orig_inner = S2.inner_stage
def _inner_plus(t):
    _orig_inner(t)
    if SHOW_TEXT and t > 38.6:
        code_text(t, '> code + ai', 960, 300, 110, 38.7, None, cols=(OR, OR, OR, OR, OR, OR, '#FFFFFF', '#FFFFFF', TE, TE, TE), style='type', align='center', panel=True, scan=True, key='end', dur_in=.5)
S2.inner_stage = _inner_plus
def s10(t):
    S2.s10(t)

SHOTS = [(0.0, s1), (3.40, s2), (9.15, s3), (12.75, s4), (20.0, s6), (24.05, s7), (26.4, s8), (29.05, s8b), (31.3, s9), (35.4, s10)]
def playhead_scrub(t, t0=28.8, t1=29.3):
    k = ease(seg(t, t0, t1)); x = lerp(-60, W + 60, k)
    s8(t)
    c = CTX.canvas; c.save(); c.clipRect(skia.Rect.MakeLTRB(-10, -10, x, H + 10)); s8b(t, inset=True); c.restore()
    gline([(x, -20), (x, H + 20)], OR, 10, key='scrub')
    fill(np.array([(x - 30, 0), (x + 30, 0), (x, 46)]), '#FFB45A', key='scrubh', tex=0, edge=.2, outline=3)
    glow(x, H / 2, 420, OR, .5)
def draw(t):
    if 28.8 <= t < 29.3:
        playhead_scrub(t); return
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
