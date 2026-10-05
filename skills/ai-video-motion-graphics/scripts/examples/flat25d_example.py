"""Mode F example: two short scenes + an integrated (story-driven) transition, rendered with flat25d_kit.
Run:  python flat25d_example.py out_dir   -> writes JPG frames; encode with ffmpeg (see SKILL.md).
"""
import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import numpy as np, cv2, skia
from flat25d_kit import *

def street(t, hero_photo=0.0):
    s = new()
    with s as cv:
        cv.save(); cam(cv, 960, 615, 1.04)
        cv.drawRect(skia.Rect.MakeLTRB(-200, -200, W + 200, 800), lin(0, -200, 0, 780, ['#0670D8', '#13A2EE', '#6AD4F5']))
        rays(cv, 1580, 150, 16, '#FFFFFF', 0.09, t * 4, 0.07); circle(cv, 1580, 150, 92, P('#FFE45A'))
        cloud2(cv, 300 + t * 20, 160, 70, 1)
        liberty(cv, 1250, 960, t, 170)
        for i, (x, w, h, wall, trim, aw, sign) in enumerate([(-40, 330, 330, '#E0301E', '#FFB020', ('#FFFFFF', '#E8102E'), 'PIZZA'), (290, 330, 300, '#2456E0', '#FFC21A', None, 'CAFE'),
                                                             (620, 330, 280, '#8A2ED0', '#FF4FB0', None, None), (1120, 300, 170, '#14A86E', '#FFE07A', ('#FFFFFF', '#FF4A2A'), 'DELI'),
                                                             (1420, 520, 300, '#FF5A10', '#2456E0', None, None)]):
            shop(cv, x, 760, w, h, wall, trim, aw, sign, seed=i, t=t)
        cv.drawRect(skia.Rect.MakeLTRB(-200, 758, W + 200, 870), lin(0, 758, 0, 870, ['#F0B460', '#E09A40']))
        cv.drawRect(skia.Rect.MakeLTRB(-200, 886, W + 200, 1300), lin(0, 886, 0, 1100, ['#5A3A9A', '#3A2478']))
        tu = (t % 4) / 4; taxi(cv, lerp(-400, 2300, tu), 1060, 52, t)
        # hero with IK arms raising a camera
        hx, hy, hs = 960, 915, 44
        e = eo(min(1, hero_photo * 2)); cy_l = lerp(-4.0 * hs, -6.2 * hs, e)
        hands = [(lerp(-1.25 * hs, -0.85 * hs, e), lerp(-2.7 * hs, cy_l + 0.15 * hs, e)), (lerp(1.25 * hs, 0.85 * hs, e), lerp(-2.7 * hs, cy_l + 0.15 * hs, e))] if hero_photo > 0.05 else None
        person(cv, hx, hy, hs, '#B06A3E', '#2A160C', '#FFE0B0', '#1E4A8A', t, 0, jacket='#FF5A10', hair_style=1, seed=7, expr='happy', hands_at=hands)
        if hero_photo > 0.05:
            cy = hy + cy_l
            shape(cv, rr_path(hx, cy, 1.7 * hs, 1.05 * hs, 0.2 * hs), '#2A2A3A', '#14141E', '#4A4A5A', off=(0.1, 0.1))
            circle(cv, hx, cy, 0.28 * hs, P('#3A5AB8'))
            if hero_photo > 0.3:
                for d in (-1, 1): circle(cv, hx + d * 0.85 * hs, cy + 0.15 * hs, 0.3 * hs, P('#B06A3E'))
        cv.restore()
    return toarr(s)

def lab(t):
    s = new()
    with s as cv:
        cv.drawRect(skia.Rect.MakeWH(W, H), lin(0, 0, 0, H, ['#040A2E', '#0A1A5A', '#08123E']))
        desk = round_path([(380, 720), (1320, 720), (1360, 780), (360, 780)], 20)
        shape(cv, desk, '#2A3AA0', '#141E5A', '#5A6AE0', off=(0, 0.3), seed=6)
        oval(cv, 1030, 708, 95, 14, P(CY_, 0.95)); oval(cv, 1030, 708, 150, 40, P(CY_, 0.45, blur=20))
        holo_island(cv, 1030, 440 + 8 * math.sin(t * 2), 50, t, t * 1.1, 1.0, 1.0)
        circle(cv, 520, 420, 360, P(CY_, 0.3, blur=140))
        alien_profile(cv, 430, 900, 84, t, 'blue', 1.0, 1, hands_at=(640, 705))
        iso_island(cv, 1600, 300, 26, 'desert', t, 3)
        pill(cv, 'SIMULATING A WORLD...', 960, 70, 40, CY_, INK, 1, popk(t, 0.2, 0.4))
    return toarr(s)

def frame(t, i):
    if t < 2.0:
        img = street(t, hero_photo=min(1, max(0, (t - 0.6) / 0.6)))
        if t > 1.5:   # the world breaks into code (block-mask wireframe spreading over the frame)
            cov = eio(prog(t, 1.5, 0.4)); m = block_mask(t, cov); B = wire_version(img, t)
            img = glitch_np((img * (1 - m) + B * m).astype(np.uint8), t, 0.3 + 0.5 * cov)
    elif t < 2.25:    # integrated transition: code blocks resolve into the next scene
        p = (t - 2.0) / 0.25; A = wire_version(street(2.0), t); B = lab(t)
        m = block_mask(t, p, seed=3); img = (A * (1 - m) + B * m).astype(np.uint8)
    else:
        img = lab(t)
    return post(img, i)

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else 'out_example'; os.makedirs(out, exist_ok=True)
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 120
    for i in range(n):
        cv2.imwrite(f'{out}/{i:05d}.jpg', cv2.cvtColor(frame(i / FPS, i), cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 94])
    print('done', n, 'frames ->', out)
