"""One-time setup for the ai-video-motion-graphics skill. Claude runs this automatically before the first render:
    python scripts/setup_env.py
- installs missing Python packages (numpy, opencv, scipy, pillow, skia-python, faster-whisper)
- makes sure the Poppins fonts are available: uses an installed copy if one exists, otherwise downloads
  Poppins (SIL Open Font License) from the official Google Fonts repository into <skill>/assets/fonts/
- checks that ffmpeg is on PATH
Safe to run repeatedly; it only does what is missing.
"""
import os, sys, glob, shutil, subprocess, importlib, urllib.request

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_DIR = os.path.join(SKILL, 'assets', 'fonts')
PKGS = {'numpy': 'numpy', 'cv2': 'opencv-python-headless', 'scipy': 'scipy', 'PIL': 'pillow', 'skia': 'skia-python', 'faster_whisper': 'faster-whisper'}
FONTS = ['Poppins-Bold.ttf', 'Poppins-Medium.ttf', 'Poppins-Regular.ttf']
URLS = ['https://github.com/google/fonts/raw/main/ofl/poppins/{f}', 'https://raw.githubusercontent.com/google/fonts/main/ofl/poppins/{f}']
LICENSE_URLS = ['https://raw.githubusercontent.com/google/fonts/main/ofl/poppins/OFL.txt']
SYSTEM_DIRS = ['/usr/share/fonts', '/usr/local/share/fonts', os.path.expanduser('~/.fonts'), os.path.expanduser('~/.local/share/fonts'),
               '/Library/Fonts', os.path.expanduser('~/Library/Fonts'), 'C:/Windows/Fonts', os.path.expandvars(r'%LOCALAPPDATA%/Microsoft/Windows/Fonts')]

def pip_install(names):
    base = [sys.executable, '-m', 'pip', 'install', '-q'] + names
    for extra in ([], ['--user'], ['--break-system-packages']):
        if subprocess.run(base + extra).returncode == 0: return True
    return False

def ensure_packages():
    missing = []
    for mod, pkg in PKGS.items():
        try: importlib.import_module(mod)
        except Exception: missing.append(pkg)
    if missing:
        print('installing python packages:', ' '.join(missing))
        if not pip_install(missing): print('  WARNING: pip install failed for', missing)
    else: print('python packages: ok')

def find_font(name):
    for d in [FONT_DIR] + SYSTEM_DIRS:
        hits = glob.glob(os.path.join(d, '**', name), recursive=True) if os.path.isdir(d) else []
        if hits: return hits[0]
    return None

def download(urls, dest):
    for u in urls:
        try:
            req = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'})
            data = urllib.request.urlopen(req, timeout=30).read()
            if len(data) > 1000 or dest.endswith('.txt'):
                open(dest, 'wb').write(data); return True
        except Exception as e:
            last = e
    return False

def ensure_fonts():
    os.makedirs(FONT_DIR, exist_ok=True)
    for f in FONTS:
        p = find_font(f)
        if p:
            if not p.startswith(FONT_DIR): shutil.copy(p, os.path.join(FONT_DIR, f))
            print('font ok:', f); continue
        ok = download([u.format(f=f) for u in URLS], os.path.join(FONT_DIR, f))
        print(('downloaded: ' if ok else 'WARNING could not download (fallback font will be used): ') + f)
    lic = os.path.join(FONT_DIR, 'OFL.txt')
    if not os.path.exists(lic): download(LICENSE_URLS, lic)

def ensure_ffmpeg():
    print('ffmpeg: ok' if shutil.which('ffmpeg') else 'WARNING: ffmpeg not found on PATH - install it (e.g. winget install ffmpeg / brew install ffmpeg / apt install ffmpeg)')

if __name__ == '__main__':
    ensure_packages(); ensure_fonts(); ensure_ffmpeg()
    print('setup complete; fonts folder:', FONT_DIR)
