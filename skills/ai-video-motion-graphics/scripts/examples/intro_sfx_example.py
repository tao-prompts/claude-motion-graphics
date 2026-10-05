import sys, glob, numpy as np
sys.path.insert(0, glob.glob('/root/.claude/skills/synced/*/ai-video-motion-graphics/scripts')[0])
from sfx_kit import Mixer, load_audio, SR
v = load_audio('th.mp4'); N = int(22.0 * SR); v = np.pad(v, ((0, max(0, N - len(v))), (0, 0)))[:N]
mx = Mixer(v)
def pop(t0, g, f0=420, f1=980, pan=0.0):
    d = 0.09; tt = mx.T(int(d * SR)); f = f0 + (f1 - f0) * (tt / d) ** 0.5
    mx.put(t0, np.sin(2 * np.pi * np.cumsum(f) / SR) * np.minimum(1, tt / 0.003) * np.exp(-tt * 38), g, pan)
def swell(t0, g, root=392, pan=0.0, d=0.9):
    tt = mx.T(int(d * SR)); env = np.minimum(1, tt / 0.18) * np.exp(-np.maximum(tt - 0.18, 0) * 4.5)
    s = sum(a * np.sin(2 * np.pi * root * m * tt) for m, a in [(1, 1), (1.25, 0.6), (1.5, 0.5), (2, 0.25)])
    mx.put(t0, s * env / 2.3, g, pan)
def glass(t0, g, pan=0.0):
    for k, f in enumerate((1568, 2093, 2637)): mx.chime(t0 + 0.035 * k, g * (0.8 - 0.2 * k), f=f, pan=pan)
# Part 1: text pops + soft low hits
pop(0.02, 0.02, pan=0.4); pop(0.40, 0.02, pan=0.4)
swell(1.30, 0.03, root=262); mx.thud(1.40, 0.045)
pop(1.85, 0.022, pan=0.4)
swell(2.44, 0.03, root=294); mx.thud(2.52, 0.045)
pop(3.12, 0.02, pan=0.4); pop(3.84, 0.02, pan=0.4); mx.sparkle(4.28, 0.018, pan=0.4)
# Part 2
mx.bed('p2.mp4', 0.35, 4.97, 11.9, gain=0.10)
glass(5.18, 0.012, pan=0.5); swell(5.15, 0.022, root=523, pan=0.5)
for k in range(4):
    t0 = 6.0 + 0.48 * k; pop(t0, 0.018, 380, 760, pan=-0.4 + 0.25 * k); mx.tick(t0 + 0.46, 0.03, pan=0.4)
swell(8.0, 0.02, root=523, pan=0.5); pop(8.45, 0.016, 500, 900, pan=0.5)
mx.typing(8.55, 2.4, 0.016, pan=0.45)
mx.tick(11.30, 0.04, pan=0.5, f=1800); mx.chime(11.32, 0.018, f=988, pan=0.5); mx.sparkle(11.33, 0.018, pan=0.5)
# Part 3
swell(11.70, 0.025, root=330)
for k, t0 in enumerate([11.98, 12.20, 12.50, 12.80, 13.06]): mx.sparkle(t0, 0.012, pan=-0.6 + 0.3 * k, d=0.4); pop(t0 + 0.3, 0.014, 500, 1000, pan=-0.6 + 0.3 * k)
swell(13.40, 0.022, root=392)
for k in range(5): mx.tick(13.85 + 0.05 * k, 0.014, pan=-0.6 + 0.3 * k, f=2200)
mx.chime(14.6, 0.014, f=660); mx.chime(19.62, 0.012, f=740)
mx.bed('p3.mp4', 3.0, 14.1, 15.1, gain=0.14, fade_out=0.05); mx.bed('p3.mp4', 6.0, 15.1, 16.35, gain=0.14, fade_in=0.05)
# Part 4
swell(16.3, 0.022, root=349)
for k in range(4): pop(16.62 + 0.09 * k + 0.08, 0.014, 450, 900, pan=-0.5)
for t0 in (16.9, 17.85, 18.9, 19.95): mx.tick(t0, 0.035, f=1600, pan=-0.4); pop(t0 + 0.16, 0.016, 520, 1040, pan=0.3)
mx.typing(17.0, 0.8, 0.014, pan=0.3)
mx.sparkle(17.98, 0.014, pan=0.1); mx.sparkle(18.25, 0.014, pan=0.5)
swell(18.9, 0.022, root=440, pan=0.3)
for oi in range(7): mx.tick(20.12 + 0.1 * oi + 0.25, 0.018, pan=0.1 + 0.08 * oi, f=2600)
mx.tick(21.05, 0.03, f=1200)
mx.chime(21.55, 0.016, f=880)
print(mx.write('mix.wav', 'sfx_stem.wav'))
