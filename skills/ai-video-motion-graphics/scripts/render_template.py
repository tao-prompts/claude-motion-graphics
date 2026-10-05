"""Skeleton frame renderer. Copy, fill in render(i), then:
  python render.py 0 N                       # or background chunks:
  setsid nohup python3 render.py 0 N > log.txt 2>&1 < /dev/null &      (poll: ls out | wc -l ; tail log.txt)
  ffmpeg -y -framerate 30 -i out/%04d.jpg -i mix.wav -map 0:v -map 1:a -c:v libx264 -preset slow -crf 17 \
         -pix_fmt yuv420p -c:a aac -b:a 256k -shortest -movflags +faststart final.mp4
Prep: ffmpeg -i talking_head.mp4 -q:v 2 th/%04d.jpg ; ffmpeg -i shot.mp4 -vf "fps=24,scale=W:H" -q:v 2 shot/%04d.jpg
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
from mg_kit import *
FPS = 30
N = len(os.listdir('th')) if os.path.isdir('th') else 0
def src_frame(folder, src_t, fps=24, total=None):
    n = int(round(src_t * fps)) + 1
    if total: n = min(max(n, 1), total)
    return load_rgb(f'{folder}/{n:04d}.jpg')
def render(i):
    t = i / FPS
    base = load_rgb(f'th/{i + 1:04d}.jpg')                 # talking head / background plate
    ui = Image.new('RGBA', (base.shape[1], base.shape[0]), (0, 0, 0, 0))
    # ... place cards / shots into `base`, draw captions & UI into `ui` using word times ...
    return composite(base, ui)
if __name__ == '__main__':
    a, b = int(sys.argv[1]), int(sys.argv[2]); os.makedirs('out', exist_ok=True)
    for i in range(a, min(b, N)): save_jpg(f'out/{i:04d}.jpg', render(i))
    print('done', a, b)
