"""Find hard cuts / jump cuts inside a clip (e.g. a talking head assembled from several takes).
   python find_jump_cuts.py FRAMES_DIR [fps] [ratio]
Prints frames whose change vs the previous frame is > ratio x the local median.
WHY: a section cut placed even one frame after a source jump cut flashes the next take for 1 frame and reads as a
'jump' in the transition. Cut on the frame BEFORE the jump and blend from a frozen last clean frame (hold <=0.1s)."""
import cv2, numpy as np, os, sys
d = sys.argv[1]; fps = float(sys.argv[2]) if len(sys.argv) > 2 else 30; ratio = float(sys.argv[3]) if len(sys.argv) > 3 else 4
fs = sorted(os.listdir(d)); prev = None; diffs = []
for f in fs:
    a = cv2.resize(cv2.imread(os.path.join(d, f), 0), (320, 180)).astype(np.float32)
    diffs.append(0 if prev is None else float(np.abs(a - prev).mean())); prev = a
diffs = np.array(diffs)
for i in range(1, len(diffs)):
    med = np.median(diffs[max(1, i - 15):i + 15]) + 0.3
    if diffs[i] > ratio * med: print(f'frame {i + 1} (t={i / fps:.3f}s): diff {diffs[i]:.1f} vs median {med:.1f}')
