"""Score, foley, ambience and voice for Ep. 6 · The Bifrost → out/mix.wav (48 kHz stereo).

Everything is synthesized (numpy), seeded, deterministic. The score and the picture share one grid:
100 BPM, eighth notes at 0.35 + 0.3·k s, bars at 1.55 + 2.4·n s (TREATMENT.md §7). Foley is driven by
events.json (window.EV from index.html, exported by events.mjs), so every sound sits on its frame.
Run: "$LIB/.venv/bin/python" mix.py
"""
import json, os, sys, wave
import numpy as np
from scipy.signal import resample_poly

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.environ.get('LIB', os.path.expanduser('~/lemo-opuscar'))
sys.path.insert(0, os.path.join(LIB, 'core', 'audio'))
import sfx  # noqa: E402  (library helpers: filters, whoosh, thump, pop, compress, limit, add)
from sfx import SR, bp, lp, hp, add, t_  # noqa: E402

rng = np.random.default_rng(606)
ev = json.load(open(os.path.join(HERE, 'events.json')))
DUR = ev['dur']; EV = ev['ev']
N = int(DUR * SR)

# ---------------- grid ----------------
BPM, E8, BEAT, BAR, BAR0, G0 = 100, 0.3, 0.6, 2.4, 1.55, 0.35
def on_grid(t): k = (t - G0) / E8; return abs(k - round(k)) * E8 < 0.002
PLAN = ['Dm', 'Bb', 'Gm', 'A']
ROOT = {'Dm': 38, 'Bb': 34, 'Gm': 43, 'A': 45}
PAD = {'Dm': [50, 53, 57], 'Bb': [50, 53, 58], 'Gm': [50, 55, 58], 'A': [49, 52, 57]}
PIZZ = {'Dm': [62, None, 65, None, 69, 67, 65, None], 'Bb': [62, None, 65, None, 70, 69, 65, None],
        'Gm': [62, None, 67, None, 70, 69, 67, None], 'A': [61, None, 64, None, 69, 67, 64, None]}
MARI = {'Dm': [74, None, 77, 81, None, 79, 77, None], 'Bb': [74, None, 77, 82, None, 81, 77, None],
        'Gm': [74, None, 79, 82, None, 81, 79, None], 'A': [73, None, 76, 81, None, 79, 76, None]}
hz = lambda m: 440.0 * 2 ** ((m - 69) / 12)
def chord_at(t): return PLAN[int(np.floor((t - BAR0) / BAR)) % 4]
def e8_at(t): return int(round(((t - BAR0) % BAR) / E8)) % 8

# ---------------- instruments ----------------
def env_adsr(d, a=0.005, r=0.03):
    n = len(t_(d)); e = np.ones(n); na, nr = max(1, int(a * SR)), max(1, int(r * SR))
    e[:na] = np.linspace(0, 1, na); e[-nr:] *= np.linspace(1, 0, nr); return e
def kick(v=1.0):
    d = 0.32; tt = t_(d); f = 45 + 85 * np.exp(-tt / 0.03)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / 0.11)
    x[:int(0.003 * SR)] += hp(sfx.noise(0.003), 2000) * 0.4
    return x * v
def snare(v=1.0):
    d = 0.2; tt = t_(d)
    return v * (bp(sfx.noise(d), 1500, 6000) * np.exp(-tt / 0.06) * 0.8 + np.sin(2 * np.pi * 190 * tt) * np.exp(-tt / 0.05) * 0.5)
def clap(v=1.0):
    d = 0.18; x = np.zeros(len(t_(d))); n = bp(sfx.noise(d), 900, 3500)
    for k, o in enumerate([0, 0.011, 0.022]):
        s = int(o * SR); m = len(x) - s; x[s:] += n[:m] * np.exp(-t_(d)[:m] / (0.008 if k < 2 else 0.06))
    return x * v * 0.9
def hat(v=1.0): d = 0.05; return hp(sfx.noise(d), 7000) * sfx.env_exp(d, 0.012) * v * 0.5
def snap(v=1.0):
    d = 0.06; tt = t_(d)
    return v * (bp(sfx.noise(d), 2000, 6000) * np.exp(-tt / 0.008) + 0.3 * np.sin(2 * np.pi * 2600 * tt) * np.exp(-tt / 0.01))
def bassnote(m, d=0.24, v=1.0):
    f = hz(m); tt = t_(d)
    x = sum(np.sin(2 * np.pi * f * k * tt) / k for k in (1, 2, 3, 5, 7))  # square-ish + 2nd harmonic: speaks on small speakers
    return lp(x, 900) * env_adsr(d, 0.004, 0.04) * (0.55 + 0.45 * np.exp(-tt / 0.12)) * v
def pizz(m, v=1.0):
    d = 0.45; tt = t_(d); f = hz(m)
    x = sum(np.sin(2 * np.pi * f * k * tt) / k * np.exp(-tt / (0.22 / k ** 0.7)) for k in range(1, 8))
    x[:int(0.004 * SR)] += bp(sfx.noise(0.004), 1500, 5000) * 0.3
    return x * v * 0.5
def marimba(m, v=1.0):
    d = 0.7; tt = t_(d); f = hz(m)
    return v * 0.5 * (np.sin(2 * np.pi * f * tt) * np.exp(-tt / 0.35) + 0.35 * np.sin(2 * np.pi * f * 3.99 * tt) * np.exp(-tt / 0.06))
def pad(ms, d, v=1.0):
    tt = t_(d); x = np.zeros(len(tt))
    for m in ms:
        for det in (-0.08, 0.08):
            f = hz(m + det)
            x += sum(((-1) ** ((k - 1) // 2)) * np.sin(2 * np.pi * f * k * tt) / k ** 2 for k in (1, 3, 5, 7))
    return lp(x, 2200) * env_adsr(d, min(0.5, d / 3), min(0.7, d / 3)) * v * 0.12
def bell(m, v=1.0):
    d = 1.2; tt = t_(d); f = hz(m)
    return v * 0.35 * (np.sin(2 * np.pi * f * tt) * np.exp(-tt / 0.5) + 0.4 * np.sin(2 * np.pi * f * 2.76 * tt) * np.exp(-tt / 0.18))

# ---------------- score ----------------
music = np.zeros((N, 2))
def sect(t):
    if t < 3.95: return 'cover'
    if t < 12.05: return 'roads'
    if t < 16.0: return 'underA'
    if t < 18.35: return 'underB'
    if t < 21.65: return 'underC'
    if t < 29.45: return 'cicada'
    if t < 44.75: return 'report'
    if t < 47.15: return 'hush'
    if t < 53.15: return 'state'
    if t < 55.0: return 'silence'
    if t < 58.25: return 'after'
    return 'final'
k = 0
while True:
    t = G0 + k * E8; k += 1
    if t >= DUR: break
    s, c, e = sect(t), chord_at(t), e8_at(t)
    R = ROOT[c]
    bassline = {0: R, 2: R, 3: R + 12, 5: R, 6: R + 7}
    if s == 'cover':
        if t >= BAR0 and e in bassline: add(music, bassnote(bassline[e], v=0.8), t)
        if t >= BAR0: add(music, hat(0.5 if e % 2 else 0.8), t, pan=0.3)
    elif s == 'roads':
        if e in bassline: add(music, bassnote(bassline[e], v=0.85), t)
        n = PIZZ[c][e]
        if n: add(music, pizz(n, 0.8), t, pan=-0.25)
        if e in (2, 6): add(music, snap(0.7), t, pan=0.35)
        if e == 0: add(music, kick(0.55), t)
        add(music, hat(0.35 if e % 2 else 0.55), t, pan=0.3)
    elif s == 'underA':
        if e in bassline: add(music, bassnote(bassline[e], v=0.75), t)
        if e in (2, 6): add(music, snap(0.55), t, pan=0.35)
    elif s == 'underB':
        if e in (0, 4): add(music, bassnote(R, d=0.5, v=0.6), t)
    elif s == 'underC':
        if e in (0, 4): add(music, bassnote(R, d=0.5, v=0.65), t)
        if e == 0: add(music, pad(PAD[c], BAR, 0.9), t)
    elif s == 'cicada':
        if e in bassline: add(music, bassnote(bassline[e], v=0.9), t)
        if e in (0, 4): add(music, kick(0.9), t)
        if e in (2, 6): add(music, snare(0.7), t, pan=0.1)
        add(music, hat(0.4 if e % 2 else 0.65), t, pan=0.3)
        n = MARI[c][e]
        if n: add(music, marimba(n, 0.75), t, pan=-0.2)
    elif s == 'report':
        if e == 0: add(music, pad(PAD[c], BAR, 0.8), t); add(music, bassnote(R, d=0.9, v=0.7), t); add(music, kick(0.45), t)
        if e == 4: add(music, bassnote(R + 7, d=0.6, v=0.55), t)
        if e in (0, 4):
            n = PIZZ[c][e]
            if n: add(music, pizz(n, 0.7), t, pan=-0.25)
    elif s == 'hush':
        if e == 0: add(music, pad(PAD[c], min(BAR, 47.15 - t), 0.5), t)
    elif s == 'state':
        if e in bassline: add(music, bassnote(bassline[e], v=0.9), t)
        if e in (0, 4): add(music, kick(0.85), t)
        if e in (2, 6): add(music, clap(0.8), t, pan=-0.1)
        add(music, hat(0.4 if e % 2 else 0.6), t, pan=0.3)
        n = PIZZ[c][e]
        if n: add(music, pizz(n, 0.7), t, pan=-0.25)
    elif s == 'after':
        if e in (0, 3, 6): add(music, bassnote(R if e != 3 else R + 12, v=0.55), t)
        if e in (2, 6): add(music, snap(0.45), t, pan=0.35)
    elif s == 'final':
        if t < 61.55 and e in (0, 2, 4, 6): add(music, bassnote(38, d=0.28, v=0.75), t)
        if abs(t - 61.55) < 1e-6: add(music, bassnote(38, d=1.6, v=0.9), t); add(music, bassnote(26 + 12, d=1.6, v=0.4), t)
        if abs(t - 58.25) < 1e-6: add(music, pad(PAD['Dm'], DUR - 58.25, 0.7), t)
# the sanctuary bloom: a marimba arpeggio up and a bell
for i, m in enumerate([62, 65, 69, 74, 77, 81]): add(music, marimba(m, 0.7), 18.35 + i * 0.075, pan=-0.3 + 0.12 * i)
add(music, bell(86, 0.5), 18.35 + 0.45)
# a short tag after the last stamp
for i, m in enumerate([74, 69, 62]): add(music, marimba(m, 0.55), 62.45 + i * 0.3)

# ---------------- foley ----------------
fol = np.zeros((N, 2))
def boom(f0, f1, d, v):
    tt = t_(d); f = f1 + (f0 - f1) * np.exp(-tt / (d / 4))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / (d / 2.5)) * v
def stamp(big=False, small=False, n=0):
    if small: x = boom(240 - 18 * n, 85, 0.16, 0.55); x[:300] += hp(sfx.noise(300 / SR), 2500) * 0.5; return x
    x = boom(150 if big else 175, 48 if big else 58, 0.38 if big else 0.28, 1.0)
    x[:300] += hp(sfx.noise(300 / SR), 2000) * 0.7
    if big:
        cr = np.zeros(len(x)); idx = rng.integers(0, int(0.2 * SR), 70); cr[idx] = rng.uniform(-1, 1, 70)
        x += lp(cr, 6000) * 0.5
    return x
def paper(v=1.0): d = 0.28; tt = t_(d); return bp(sfx.noise(d), 1500, 7000) * np.sin(np.pi * tt / d) ** 2 * v * 0.5
def keyclick(v=1.0, p=1.0): d = 0.035; tt = t_(d); return v * (bp(sfx.noise(d), 1500 * p, 5000 * p) * np.exp(-tt / 0.006) + 0.4 * np.sin(2 * np.pi * 180 * tt) * np.exp(-tt / 0.01))
def shutter(v=1.0):
    x = np.zeros(int(0.12 * SR)); a = keyclick(1, 1.3); b = keyclick(0.8, 1.1)
    x[:len(a)] += a; s = int(0.045 * SR); x[s:s + len(b)] += b; x += bp(sfx.noise(0.12), 3000, 9000) * sfx.env_exp(0.12, 0.02) * 0.3
    return x * v
def grind(d=0.9, v=1.0):
    tt = t_(d); x = lp(sfx.brown(d), 400) * (0.6 + 0.4 * np.sin(2 * np.pi * 17 * tt)) + 0.2 * bp(sfx.noise(d), 100, 180)
    return sfx.norm(x) * np.sin(np.pi * np.clip(tt / d, 0, 1)) ** 0.5 * v
def drip(v=1.0): d = 0.09; tt = t_(d); f = 900 + 1400 * tt / d; return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / 0.025) * v
def boing(v=1.0): d = 0.5; tt = t_(d); f = 260 * (1 + 0.5 * tt / d) * (1 + 0.15 * np.sin(2 * np.pi * 14 * tt) * np.exp(-tt / 0.2)); return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / 0.18) * v * 0.6
def hit(low=False, v=1.0):
    d = 0.5; tt = t_(d); base = 38 if low else 50
    stab = sum(np.sign(np.sin(2 * np.pi * hz(base + o) * tt)) for o in (0, 7, 12)) / 3
    return v * (np.r_[kick(1.0), np.zeros(len(tt))][:len(tt)] * 0.8 +lp(stab, 1400 if low else 2400) * np.exp(-tt / 0.14) * 0.45 + np.r_[snare(0.6), np.zeros(len(tt))][:len(tt)] * (0 if low else 1))
def roll(d, v=1.0):
    x = np.zeros(int(d * SR) + SR // 2); t = 0.0
    while t < d:
        p = t / d; s = int(t * SR); sn = snare(0.25 + 0.75 * p) * 0.6; x[s:s + len(sn)] += sn[:len(x) - s]
        t += lerp(0.075, 0.035, p)
    tt = np.arange(len(x)) / SR; f = 200 + 1000 * np.clip(tt / d, 0, 1) ** 2
    x += 0.15 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.clip(tt / d, 0, 1) * (tt < d)
    return x * v
lerp = lambda a, b, p: a + (b - a) * p
def scribble(d, v=1.0):
    x = np.zeros(int(d * SR)); t = 0.0
    while t < d:
        s = int(t * SR); n = bp(sfx.noise(0.05), 2500, 6500) * np.hanning(int(0.05 * SR)); x[s:s + len(n)] += n[:len(x) - s] * rng.uniform(0.3, 0.7)
        t += rng.uniform(0.06, 0.14)
    return x * v * 0.35

for e in EV:
    t, ty = e['t'], e['type']
    if ty == 'stamp': add(fol, stamp(e.get('big'), e.get('small'), e.get('n', 0)), t, 1.0 if not e.get('small') else 0.7)
    elif ty == 'slam': add(fol, kick(1.0), t, 0.9); add(fol, lp(sfx.noise(0.25), 500) * sfx.env_exp(0.25, 0.06), t, 0.6)
    elif ty == 'whoosh': add(fol, sfx.whoosh(0.4), t - 0.1, 0.45)
    elif ty == 'rumble': add(fol, sfx.rumble(1.2), t, 0.5)
    elif ty == 'paper': add(fol, paper(), t, 0.7)
    elif ty == 'pen': add(fol, scribble(e['d']), t, 0.6)
    elif ty == 'click': add(fol, sfx.click(1.3), t, 0.8)
    elif ty == 'grind': add(fol, grind(e['d']), t, 0.55)
    elif ty == 'bloom': add(fol, hp(sfx.noise(1.4), 5000) * np.sin(np.pi * t_(1.4) / 1.4) ** 2 * 0.08, t - 0.4, 1.0)
    elif ty == 'drips':
        tt = t + 0.4
        while tt < t + e['d'] - 0.3:
            add(fol, drip(), tt, 0.25, pan=rng.uniform(-0.6, 0.6)); tt += rng.uniform(0.9, 1.8)
    elif ty == 'thump': add(fol, sfx.thump(1.0, 70), t, 0.8)
    elif ty == 'type':
        for i in range(e['n']): add(fol, keyclick(rng.uniform(0.5, 0.8), rng.uniform(0.9, 1.15)), t + i * e['rate'], 0.45)
    elif ty == 'shutter': add(fol, shutter(), t, 0.8)
    elif ty == 'roll': add(fol, roll(e['d']), t, 0.6)
    elif ty == 'zoom': add(fol, sfx.whoosh(0.3), t - 0.05, 0.5)
    elif ty == 'hit': add(fol, hit(bool(e.get('low'))), t, 0.75)
    elif ty == 'boing': add(fol, boing(), t, 0.8)
    elif ty == 'pop': add(fol, sfx.pop(0.5), t, 0.35)

# ---------------- ambience ----------------
amb = np.zeros((N, 2))
room = lp(sfx.brown(DUR), 900) * 0.012
amb[:len(room), 0] += room; amb[:len(room), 1] += room
def window(a, b, f=0.6):
    w = np.zeros(N); s, e = int(a * SR), min(N, int(b * SR)); w[s:e] = 1
    r = int(f * SR); w[s:s + r] *= np.linspace(0, 1, r); w[e - r:e] *= np.linspace(1, 0, r); return w
wind = sfx.norm(lp(sfx.brown(DUR), 300)) * 0.05
earth = sfx.norm(lp(sfx.brown(DUR), 120)) * 0.04
amb[:, 0] += wind[:N] * window(12.05, 21.65) + earth[:N] * window(4.3, 12.05)
amb[:, 1] += wind[:N] * window(12.05, 21.65) + earth[:N] * window(4.3, 12.05)
amb[:, 0] += wind[:N] * window(58.25, DUR) * 0.6; amb[:, 1] += wind[:N] * window(58.25, DUR) * 0.6

# ---------------- voice ----------------
with wave.open(os.path.join(HERE, 'out', 'voice.wav')) as f:
    vsr = f.getframerate(); v = np.frombuffer(f.readframes(f.getnframes()), np.int16).astype(np.float64) / 32768
v = resample_poly(v, SR, vsr)[:N]
v = np.r_[v, np.zeros(N - len(v))]
v = sfx.compress(hp(v, 80), thr=0.18, ratio=3.0)
act = np.abs(v) > 0.01
v *= 10 ** (-18 / 20) / np.sqrt(np.mean(v[act] ** 2))           # voice RMS −18 dBFS while speaking
venv = lp(np.abs(v), 8); venv = np.clip(venv / (venv.max() * 0.25), 0, 1)
duck = 1 - 0.5 * venv                                            # music about −6 dB under the voice

# ---------------- mix ----------------
mrms = np.sqrt(np.mean(music[int(4 * SR):int(12 * SR)] ** 2))
music *= 10 ** (-27 / 20) / max(mrms, 1e-9)                       # music ~9–10 dB under the voice once ducked
mix = music * duck[:, None] + fol * 0.32 + amb
mix[:, 0] += v; mix[:, 1] += v
for ch in (0, 1): mix[:, ch] = sfx.limit(mix[:, ch], 0.95)
fade = np.ones(N); r = int(0.4 * SR); fade[-r:] = np.linspace(1, 0, r)
mix *= fade[:, None]
os.makedirs(os.path.join(HERE, 'out'), exist_ok=True)
with wave.open(os.path.join(HERE, 'out', 'mix.wav'), 'wb') as f:
    f.setnchannels(2); f.setsampwidth(2); f.setframerate(SR)
    f.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())

# ---------------- checks ----------------
hits = [e for e in EV if e['type'] in ('stamp', 'slam', 'hit', 'shutter', 'thump', 'click', 'bloom', 'zoom', 'boing')]
off = [e for e in hits if not on_grid(e['t'])]
print(f"cuecheck: {len(hits) - len(off)}/{len(hits)} hits on the eighth-note grid" + (f"; OFF: {off}" if off else " (0 ms)"))
def band(x, lo, hi):
    X = np.abs(np.fft.rfft(x[:, 0] + x[:, 1])); fr = np.fft.rfftfreq(len(x), 1 / SR)
    return 10 * np.log10(np.sum(X[(fr >= lo) & (fr < hi)] ** 2) + 1e-12)
print(f"low band 20–120 Hz vs 120 Hz–8 kHz: {band(mix, 20, 120) - band(mix, 120, 8000):+.1f} dB (total band energy; aim ≈ −3)")
print('wrote out/mix.wav', round(N / SR, 2), 's')
