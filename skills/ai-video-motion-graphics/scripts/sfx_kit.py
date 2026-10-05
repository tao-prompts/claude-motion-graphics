"""Sound design helpers: synthesised UI cues + shot-audio beds mixed under a voice track.

    mx = Mixer.from_video('talking_head.mp4')          # voice = the video's audio
    mx.bed('shot1.mp4', src_off=0.2, t0=0.2, t1=2.4, gain=0.14)
    mx.whoosh(1.45, 0.03); mx.tick(3.4, 0.035); mx.chime(1.3, 0.02)
    mx.write('mix.wav', 'sfx_stem.wav')
Keep SFX subtle (gains 0.02-0.06 vs voice peak ~0.5). No whoosh on every cut.
"""
import subprocess, numpy as np
from scipy import signal
from scipy.io import wavfile
SR = 48000
def load_audio(path, sr=SR):
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', path, '-vn', '-ac', '2', '-ar', str(sr), '/tmp/_sfxkit.wav'], check=True)
    _, x = wavfile.read('/tmp/_sfxkit.wav'); return x.astype(np.float32) / 32768

class Mixer:
    def __init__(self, voice, seed=7):
        self.v = voice; self.N = len(voice); self.fx = np.zeros((self.N, 2), np.float32); self.beds = np.zeros_like(self.fx)
        self.rng = np.random.default_rng(seed)
    @classmethod
    def from_video(cls, path): return cls(load_audio(path))
    def T(self, n): return np.arange(n) / SR
    def nz(self, d): return self.rng.standard_normal(int(d * SR))
    def bp(self, x, lo, hi): return signal.sosfilt(signal.butter(2, [lo, hi], 'band', fs=SR, output='sos'), x)
    def env(self, d, a, dec): t = self.T(int(d * SR)); return np.minimum(1, t / a) * np.exp(-t * dec)
    def hump(self, d, p=2): n = int(d * SR); return np.sin(np.pi * np.arange(n) / n) ** p
    def put(self, t0, s, g, pan=0.0):
        i = int(t0 * SR); n = min(len(s), self.N - i)
        if n <= 0 or i < 0: return
        a = (pan + 1) * np.pi / 4; self.fx[i:i + n, 0] += s[:n] * g * np.cos(a); self.fx[i:i + n, 1] += s[:n] * g * np.sin(a)
    # --- cues
    def whoosh(self, t0, g, pan=0, d=0.4, lo=300, hi=5000):
        n = int(d * SR); x = self.nz(d); out = np.zeros(n); ch = 1024
        for s in range(0, n, ch):
            c = lo * (hi / lo) ** (s / n); out[s:s + ch] = self.bp(x[s:s + ch], max(c * 0.6, 40), min(c * 1.6, 20000))
        self.put(t0, out * self.hump(d), g, pan)
    def swish(self, t0, g, pan=0, d=0.35, lo=800, hi=7000): self.put(t0, self.bp(self.nz(d), lo, hi) * self.hump(d), g, pan)
    def tick(self, t0, g, pan=0, f=2400):
        d = 0.05; self.put(t0, np.sin(2 * np.pi * f * self.T(int(d * SR))) * self.env(d, 0.001, 90) + self.bp(self.nz(d), 3000, 9000) * self.env(d, 0.001, 120) * 0.4, g, pan)
    def chime(self, t0, g, f=880, pan=0):
        d = 1.0; t = self.T(int(d * SR)); s = sum(a * np.sin(2 * np.pi * f * m * t) * np.exp(-t * k) for m, a, k in [(1, 1, 4), (1.5, 0.5, 5), (2, 0.25, 7)])
        self.put(t0, s * np.minimum(1, t / 0.004), g, pan)
    def thud(self, t0, g):
        d = 0.35; t = self.T(int(d * SR)); f = 90 * np.exp(-t * 8) + 50; self.put(t0, np.sin(2 * np.pi * np.cumsum(f) / SR) * self.env(d, 0.003, 9), g)
    def sparkle(self, t0, g, pan=0, d=0.6):
        n = int(d * SR); self.put(t0, self.bp(self.nz(d), 5000, 14000) * (self.rng.random(n) > 0.93) * self.hump(d, 0.8), g, pan)
    def typing(self, t0, d, g, pan=0.5):
        k = t0
        while k < t0 + d: self.tick(k, g * self.rng.uniform(0.6, 1.0), pan, self.rng.uniform(3500, 5500)); k += self.rng.uniform(0.045, 0.08)
    def scribble(self, t0, g, pan=0, d=0.8):
        n = int(d * SR); s = self.bp(self.nz(d), 1500, 6500) * (0.45 + 0.55 * np.abs(np.sin(2 * np.pi * 7 * self.T(n)))) * self.hump(d, 0.6); self.put(t0, s, g, pan)
    # --- softer UI cues (user rejected whooshes: use these instead)
    def pop(self, t0, g, f0=420, f1=980, pan=0.0):
        """short rising blip - text/cards appearing"""
        d = 0.09; tt = self.T(int(d * SR)); f = f0 + (f1 - f0) * (tt / d) ** 0.5
        self.put(t0, np.sin(2 * np.pi * np.cumsum(f) / SR) * np.minimum(1, tt / 0.003) * np.exp(-tt * 38), g, pan)
    def swell(self, t0, g, root=392, pan=0.0, d=0.9):
        """soft tonal swell (major-ish chord, slow attack) - big words, panel/scene changes"""
        tt = self.T(int(d * SR)); env = np.minimum(1, tt / 0.18) * np.exp(-np.maximum(tt - 0.18, 0) * 4.5)
        s = sum(a * np.sin(2 * np.pi * root * m * tt) for m, a in [(1, 1), (1.25, 0.6), (1.5, 0.5), (2, 0.25)])
        self.put(t0, s * env / 2.3, g, pan)
    def glass(self, t0, g, pan=0.0):
        """glassy triple chime - UI panel materialising"""
        for k, f in enumerate((1568, 2093, 2637)): self.chime(t0 + 0.035 * k, g * (0.8 - 0.2 * k), f=f, pan=pan)
    # --- beds (the shots' own audio, quiet, aligned to where each shot plays)
    def bed(self, path, src_off, t0, t1, gain=0.15, fade_in=0.15, fade_out=0.15):
        src = load_audio(path); i0, i1 = int(t0 * SR), min(int(t1 * SR), self.N); n = i1 - i0; a = int(src_off * SR)
        x = src[a:a + n]
        if len(x) < n: x = np.pad(x, ((0, n - len(x)), (0, 0)))
        e = np.ones(n); k = int(fade_in * SR); e[:k] = np.linspace(0, 1, k); k = int(fade_out * SR); e[-k:] = np.minimum(e[-k:], np.linspace(1, 0, k))
        self.beds[i0:i1] += x * e[:, None] * gain
    def write(self, mix_path, stem_path=None, reverb=0.12):
        fx = self.fx
        if reverb:
            ir = self.rng.standard_normal(int(0.5 * SR)) * np.exp(-self.T(int(0.5 * SR)) * 8); ir /= np.sqrt((ir ** 2).sum())
            fx = fx + reverb * np.stack([signal.fftconvolve(fx[:, 0], ir)[:self.N], signal.fftconvolve(fx[:, 1], ir)[:self.N]], 1)
        stem = fx + self.beds; mix = self.v + stem; pk = np.abs(mix).max()
        if pk > 0.97: mix = mix / pk * 0.97
        wavfile.write(mix_path, SR, (mix * 32767).astype(np.int16))
        if stem_path: wavfile.write(stem_path, SR, (np.clip(stem, -1, 1) * 32767).astype(np.int16))
        return {'voice_peak': float(np.abs(self.v).max()), 'stem_peak': float(np.abs(stem).max())}
