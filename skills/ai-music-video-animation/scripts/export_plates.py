"""Lip-sync stills for an AI video model: text hidden, mouths closed.
python3 export_plates.py <scene_module> name1=6.4,name2=13.9 out_dir"""
import sys, os, importlib, cv2
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, 'examples', 'code_and_ai')); sys.path.insert(0, os.getcwd())
mod = importlib.import_module(sys.argv[1])
import chars
chars.CLOSED_MOUTHS = True
for m in list(sys.modules.values()):
    if m is not None and hasattr(m, 'NOSING'): m.NOSING = True
    if m is not None and hasattr(m, 'SHOW_TEXT'): m.SHOW_TEXT = False
os.makedirs(sys.argv[3], exist_ok=True)
for item in sys.argv[2].split(','):
    name, t = item.split('='); cv2.imwrite(f'{sys.argv[3]}/{name}.png', mod.render(float(t)))
