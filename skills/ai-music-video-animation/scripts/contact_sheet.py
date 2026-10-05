"""Contact sheet of chosen times: python3 contact_sheet.py <scene_module> 1.0,2.5,4.0 out.jpg [cols] [tile_width]"""
import sys, os, time, importlib, cv2, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, 'examples', 'code_and_ai')); sys.path.insert(0, os.getcwd())
mod = importlib.import_module(sys.argv[1])
ts = [float(x) for x in sys.argv[2].split(',')]; out = sys.argv[3]
cols = int(sys.argv[4]) if len(sys.argv) > 4 else 4; w = int(sys.argv[5]) if len(sys.argv) > 5 else 480
tiles = []
for t in ts:
    t0 = time.time(); im = cv2.resize(mod.render(t), (w, int(w * 9 / 16)), interpolation=cv2.INTER_AREA)
    for c, th in (((0, 0, 0), 3), ((255, 255, 255), 1)): cv2.putText(im, f'{t:.2f}', (6, 22), cv2.FONT_HERSHEY_SIMPLEX, .6, c, th)
    tiles.append(im); print(f'{t:.2f} {(time.time() - t0) * 1000:.0f}ms', flush=True)
while len(tiles) % cols: tiles.append(np.zeros_like(tiles[0]))
cv2.imwrite(out, np.vstack([np.hstack(tiles[i:i + cols]) for i in range(0, len(tiles), cols)]), [cv2.IMWRITE_JPEG_QUALITY, 88])
