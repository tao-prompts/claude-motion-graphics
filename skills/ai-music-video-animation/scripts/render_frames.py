"""Render frames of a scene module in parallel-safe, resumable chunks.
usage: python3 render_frames.py <scene_module> <start> <end> <step> <out_dir>
  e.g. two background workers on 2 CPUs:
  setsid nohup python3 render_frames.py scenes3 0 960 2 out/frames > w0.txt 2>&1 < /dev/null &
  setsid nohup python3 render_frames.py scenes3 1 960 2 out/frames > w1.txt 2>&1 < /dev/null &
The scene module must define render(t) -> BGR uint8 frame. Its folder is put on sys.path."""
import sys, os, importlib, cv2
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, 'examples', 'code_and_ai')); sys.path.insert(0, os.getcwd())
mod = importlib.import_module(sys.argv[1])
a, b, step, out = int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
fps = 24
os.makedirs(out, exist_ok=True)
for i in range(a, b, step):
    p = f'{out}/f{i:05d}.jpg'
    if os.path.exists(p): continue
    im = mod.render(i / fps)
    cv2.imwrite(p + '.tmp.jpg', im, [cv2.IMWRITE_JPEG_QUALITY, 95]); os.replace(p + '.tmp.jpg', p)
    if i % 48 == 0: print(i, flush=True)
