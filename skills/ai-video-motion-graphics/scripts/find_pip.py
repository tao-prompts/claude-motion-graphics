"""Locate a picture-in-picture box in a talking-head frame by diffing against the known background plate.
CLI: python find_pip.py frame.jpg background.png   (background resized to 1920x1086 and cropped 3:1083 by default)"""
import sys, cv2, numpy as np
def find_pip(frame_path, bg_path, thresh=45):
    G = cv2.resize(cv2.imread(bg_path), (1920, 1086), interpolation=cv2.INTER_AREA)[3:1083].astype(float)
    f = cv2.imread(frame_path).astype(float)
    d = (np.abs(f - G).max(2) > thresh).astype(np.uint8); d = cv2.morphologyEx(d, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(d); k = 1 + np.argmax(st[1:, 4]); x, y, w, h, a = st[k]
    return int(x), int(y), int(x + w), int(y + h)
def find_pip_over_black(frame_path, thresh=18):
    g = cv2.imread(frame_path).max(2); ys, xs = np.where(g > thresh); return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())
if __name__ == '__main__':
    print(find_pip(sys.argv[1], sys.argv[2]) if len(sys.argv) > 2 else find_pip_over_black(sys.argv[1]))
