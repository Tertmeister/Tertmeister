"""Score, foley, room and voice for A Bestiary of Azul · Plate I → out/mix.wav (48 kHz stereo).

All synthesized (numpy/scipy), seeded and deterministic. The score sits on the picture's grid: 75 BPM, eighth
notes at 0.1 + 0.4·k s, bars at 0.1 + 3.2·n s (TREATMENT.md §7). Foley follows events.json (window.EV).
Run: "$LIB/.venv/bin/python" mix.py
"""
import json, os, sys, wave
import numpy as np
from scipy.signal import resample_poly

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.environ.get('LIB', os.path.expanduser('~/lemo-opuscar'))
sys.path.insert(0, os.path.join(LIB, 'core', 'audio'))
import sfx  # noqa: E402
from sfx import SR, bp, lp, hp, add, t_  # noqa: E402

rng = np.random.default_rng(1101)
ev = json.load(open(os.path.join(HERE, 'events.json')))
DUR = ev['dur']; EV = ev['ev']; N = int(DUR * SR)
E8, BEAT, BAR, G0 = 0.4, 0.8, 3.2, 0.1
hz = lambda m: 440.0 * 2 ** ((m - 69) / 12)
PLAN = ['Dm', 'Gm', 'C', 'A']
CH = {'Dm': [50, 53, 57, 62], 'Gm': [43, 50, 55, 58], 'C': [48, 52, 55, 60], 'A': [45, 49, 52, 57]}
ROOT = {'Dm': 38, 'Gm': 43, 'C': 36, 'A': 33}
chord_at = lambda t: PLAN[int(np.floor((t - G0) / BAR)) % 4]
def e8_at(t): return int(round(((t - G0) % BAR) / E8)) % 8
def on_grid(t): k = (t - G0) / E8; return abs(k - round(k)) * E8 < 0.002

# ---------------- instruments ----------------
def harpsi(m, v=1.0, d=1.6):
    tt = t_(d); f = hz(m); x = np.zeros(len(tt))
    for k in range(1, 15):
        if f * k > 9000: break
        x += np.sin(2 * np.pi * f * k * tt + k) * (1 / k ** 0.75) * np.exp(-tt / (1.1 / k ** 0.55))
    x[:int(0.003 * SR)] += hp(sfx.noise(0.003), 3000) * 0.6                  # the quill's pluck
    rel = np.ones(len(tt)); r = int(0.05 * SR); rel[-r:] = np.linspace(1, 0, r)
    return x * rel * v * 0.16
def cello(m, d, v=1.0):
    tt = t_(d); f = hz(m) * (1 + 0.004 * np.sin(2 * np.pi * 5.4 * tt) * np.clip(tt / 0.6, 0, 1))
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = sum(np.sin(k * ph) / k ** 1.15 for k in range(1, 12))
    env = np.minimum(1, tt / 0.35) * np.minimum(1, (d - tt) / 0.6).clip(0, 1)
    return lp(x + 0.02 * sfx.noise(d), 2400) * env * v * 0.22
def glass(ms, d=2.6, v=1.0):
    tt = t_(d); x = np.zeros(len(tt))
    for m in ms:
        f = hz(m); x += (np.sin(2 * np.pi * f * tt) + 0.25 * np.sin(2 * np.pi * 2 * f * tt) + 0.08 * np.sin(2 * np.pi * 3 * f * tt)) * (1 + 0.06 * np.sin(2 * np.pi * 5 * tt))
    env = np.minimum(1, tt / 0.18) * np.exp(-tt / (d * 0.55))
    return x * env * v * 0.09
def pizzbass(m, v=1.0):
    d = 0.9; tt = t_(d); f = hz(m)
    x = sum(np.sin(2 * np.pi * f * k * tt) / k ** 1.4 * np.exp(-tt / (0.45 / k ** 0.6)) for k in range(1, 6))
    x[:int(0.004 * SR)] += lp(sfx.noise(0.004), 1500) * 0.3
    return x * v * 1.1
def ting(f=3400, v=1.0): d = 1.0; tt = t_(d); return (np.sin(2 * np.pi * f * tt) + 0.4 * np.sin(2 * np.pi * f * 2.71 * tt) * np.exp(-tt / 0.08)) * np.exp(-tt / 0.32) * v * 0.18

# ---------------- score ----------------
mus = np.zeros((N, 2))
def section(t):
    if t < 27.0: return 'I'
    if t < 55.5: return 'II'
    if t < 80.0: return 'III'
    if t < 81.3: return 'silence'
    if t < 84.5: return 'arc'
    if t < 108.8: return 'IV'
    if t < 131.9: return 'V'
    if t < 133.3: return 'silence'
    if t < 136.5: return 'cadence'
    return 'end'
k = 0
while True:
    t = G0 + k * E8; k += 1
    if t >= DUR: break
    s, c, e = section(t), chord_at(t), e8_at(t)
    ch, R = CH[c], ROOT[c]
    if s in ('I', 'II', 'III', 'IV', 'V') and t >= 0.9 and (e == 0 or (e == 4 and s in ('II', 'V'))): add(mus, pizzbass(R, 0.9 if s in ('II', 'V') else 0.7), t, pan=-0.1)
    if s == 'I':
        if t < 0.9: continue
        if e in (0, 4): add(mus, harpsi(R + 12, 0.7), t, pan=-0.2)
        if e in (1, 3, 5, 7): add(mus, harpsi(ch[(e // 2) % 4] + 12, 0.45), t, pan=0.25)
    elif s == 'II':
        add(mus, harpsi(R + 12 if e % 4 == 0 else ch[e % 4] + 12, 0.75 if e % 2 == 0 else 0.5), t, pan=-0.15 if e % 2 == 0 else 0.2)
        if e == 0: add(mus, harpsi(R, 0.6, 2.4), t, pan=-0.3)
    elif s == 'III':
        if e in (0, 2, 4, 6): add(mus, harpsi(ch[(e // 2) % 4] + 12, 0.55), t, pan=0.1 * (e - 3))
        if e == 0: add(mus, harpsi(R, 0.5, 2.4), t, pan=-0.3)
    elif s == 'IV':
        if e in (0, 3, 6): add(mus, harpsi(ch[e % 4] + 24, 0.35, 0.5), t, pan=0.3)
        if e == 0: add(mus, harpsi(R + 12, 0.45, 1.2), t, pan=-0.2)
    elif s == 'V':
        if t < 117.3:
            if e in (0, 4): add(mus, harpsi(R + 12, 0.45), t)
        else:                                        # the doctrine: a firm walking bass in quarters, chords on the beat
            if e % 2 == 0: add(mus, harpsi(R + [0, 3, 5, 7][(e // 2) % 4], 0.8, 0.7), t, pan=-0.25)
            if e in (0, 4): add(mus, harpsi(ch[2] + 12, 0.55), t, pan=0.25); add(mus, harpsi(ch[3] + 12, 0.5), t, pan=0.3)
# colour moments: glass harmonica on the gold and on the arc, the cello when the sacs fill and on the red
add(mus, glass([74, 77, 81], 3.4, 1.0), 4.1); add(mus, cello(38, 4.2, 0.55), 4.1)
add(mus, cello(50, 3.6, 0.8), 51.7); add(mus, cello(57, 3.6, 0.6), 51.7)
add(mus, glass([69, 74, 78], 3.0, 1.1), 83.3)
for i, m in enumerate([81, 84, 88]): add(mus, ting(hz(m), 0.6), 95.7 + i * 0.4)
add(mus, cello(38, 3.4, 0.9), 133.3)
# the cadence: A (dominant) then a rolled D minor, and a long low D
for i, m in enumerate([45, 52, 57, 61]): add(mus, harpsi(m, 0.7, 2.0), 134.1 + i * 0.05)
for i, m in enumerate([38, 50, 53, 57, 62]): add(mus, harpsi(m, 0.8, 3.2), 135.7 + i * 0.07)
add(mus, cello(38, 5.0, 0.7), 135.7)

# ---------------- foley ----------------
fol = np.zeros((N, 2))
def burin(d, v=1.0):
    tt = t_(d); x = bp(sfx.noise(d), 2600, 9000) * (0.6 + 0.4 * np.abs(np.sin(2 * np.pi * 6.5 * tt)))
    for f in (1180, 2310, 3470): x += 0.04 * np.sin(2 * np.pi * f * tt)
    ch = np.zeros(len(tt)); idx = rng.integers(0, len(tt), int(d * 30)); ch[idx] = rng.uniform(-1, 1, len(idx)); x += hp(ch, 3000) * 0.6
    env = np.minimum(1, tt / 0.08) * np.minimum(1, (d - tt) / 0.1).clip(0, 1)
    return x * env * v * 0.09
def tick(v=1.0): d = 0.025; tt = t_(d); return bp(sfx.noise(d), 3000, 8000) * np.exp(-tt / 0.004) * v
def scratch(d, v=1.0):
    x = np.zeros(int(d * SR) + 1); t = 0.0
    while t < d:
        n = int(0.09 * SR); s = int(t * SR); y = bp(sfx.noise(0.09), 2000, 6000) * np.hanning(n); x[s:s + n] += y[:len(x) - s] * rng.uniform(0.4, 0.8); t += 0.25
    return x * v * 0.3
def whoosh_paper(d, v=1.0): tt = t_(d); return bp(sfx.noise(d), 600, 4000) * np.sin(np.pi * tt / d) ** 1.5 * v * 0.35
def plip(v=1.0): d = 0.12; tt = t_(d); f = 700 + 900 * np.exp(-tt / 0.02); return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / 0.035) * v * 0.6
def brush(v=1.0): d = 0.6; tt = t_(d); return bp(sfx.noise(d), 800, 5000) * np.sin(np.pi * tt / d) ** 2 * v * 0.25
def thunder(v=1.0):
    d = 4.0; tt = t_(d); x = lp(sfx.brown(d), 180) * (0.5 + 0.5 * np.abs(np.sin(2 * np.pi * 0.9 * tt + 1)))
    return sfx.norm(x) * np.minimum(1, tt / 0.6) * np.exp(-tt / 1.6) * v
def wingbeat(v=1.0):
    d = 0.55; tt = t_(d); x = lp(sfx.noise(d), 500) * np.sin(np.pi * np.clip(tt / 0.35, 0, 1)) ** 2
    return sfx.norm(x + 0.5 * np.sin(2 * np.pi * 70 * tt) * np.exp(-tt / 0.12)) * v
def hum(d, v=1.0):
    tt = t_(d); x = sum(np.sin(2 * np.pi * 60 * k * tt) / k for k in (1, 2, 3, 5)) * (1 + 0.3 * np.sin(2 * np.pi * 4 * tt))
    return x * np.minimum(1, tt / 0.2) * np.minimum(1, (d - tt) / 0.4).clip(0, 1) * v * 0.12
def crackle(d, v=1.0, big=False):
    n = int(d * SR); x = np.zeros(n); cnt = int(d * (220 if big else 120)); idx = rng.integers(0, n, cnt)
    x[idx] = rng.uniform(-1, 1, cnt) * rng.uniform(0.3, 1, cnt); x = hp(x, 1500) + 0.2 * bp(sfx.noise(d), 3000, 9000)
    tt = np.arange(n) / SR; return x * np.minimum(1, tt / 0.05) * np.minimum(1, (d - tt) / 0.3).clip(0, 1) * v * (0.5 if big else 0.35)
def clack(v=1.0): d = 0.5; tt = t_(d); return (hp(sfx.noise(d), 2000) * np.exp(-tt / 0.006) + 0.3 * np.sin(2 * np.pi * 2200 * tt) * np.exp(-tt / 0.09) + 0.2 * np.sin(2 * np.pi * 3550 * tt) * np.exp(-tt / 0.06)) * v
def stone(v=1.0): d = 0.08; tt = t_(d); return (bp(sfx.noise(d), 900, 4000) * np.exp(-tt / 0.01) + 0.3 * np.sin(2 * np.pi * 620 * tt) * np.exp(-tt / 0.02)) * v
def rub(d, v=1.0): tt = t_(d); return bp(sfx.noise(d), 400, 2500) * np.sin(np.pi * tt / d) * v * 0.3
def rain(d, v=1.0):
    n = int(d * SR); x = bp(sfx.noise(d), 1500, 9000)[:n] * 0.08; tt = np.arange(n) / SR
    for s in rng.integers(0, n - 2000, int(d * 25)): x[s:s + 2000] += plip(rng.uniform(0.1, 0.35))[:2000][:n - s]
    return x * np.minimum(1, tt / 1.5) * np.minimum(1, (d - tt) / 1.5).clip(0, 1) * v
def chitter(d, v=1.0):
    n = int(d * SR); tt = np.arange(n) / SR; x = bp(sfx.noise(d), 3000, 7000)[:n] * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 22 * tt)))
    gate = (np.sin(2 * np.pi * 0.7 * tt + 1) > 0.3).astype(float)
    return x * gate * np.minimum(1, (d - tt) / 0.5).clip(0, 1) * v * 0.12
def buzz(d, v=1.0):
    n = int(d * SR); tt = np.arange(n) / SR; x = np.sign(np.sin(2 * np.pi * 100 * tt)) * 0.3 + crackle(d, 0.6)[:n]
    return lp(x, 3000) * np.minimum(1, tt / 0.5) * np.minimum(1, (d - tt) / 1.0).clip(0, 1) * v * 0.08
def press(v=1.0):
    d = 1.0; tt = t_(d); x = lp(sfx.brown(d), 160) * np.minimum(1, tt / 0.3) * (tt < 0.36)
    x = sfx.norm(x) * 0.5; th = sfx.thump(1.0, 60); s = int(0.35 * SR); x[s:s + len(th)] += th[:len(x) - s]; return x * v
def steel(v=1.0):
    d = 1.4; tt = t_(d); x = sum(a * np.sin(2 * np.pi * 820 * r * tt) * np.exp(-tt / dk) for r, a, dk in [(1, 1, 0.5), (2.76, 0.6, 0.3), (5.4, 0.35, 0.15), (8.9, 0.2, 0.08)])
    x = x + hp(sfx.noise(d), 3000) * np.exp(-tt / 0.01); b = int(0.22 * SR); x[b:] += 0.4 * x[:len(x) - b]; return x * v * 0.35
def bowstring(v=1.0): d = 0.7; tt = t_(d); f = 120 * (1 + 0.3 * np.exp(-tt / 0.03)); return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / 0.18) + 0.4 * sfx.whoosh(d)[:len(tt)]) * v * 0.6

for e in EV:
    t, ty = e['t'], e['type']
    if ty == 'burin': add(fol, burin(e['until'] - t), t, 0.8, pan=rng.uniform(-0.3, 0.3))
    elif ty == 'arcburin': add(fol, burin(e['until'] - t, 2.2), t, 1.0)
    elif ty == 'letters':
        for i in range(max(2, int(e['n']))): add(fol, tick(rng.uniform(0.15, 0.3)), t + i * e['dur'] / max(2, e['n']))
    elif ty == 'quill': add(fol, scratch(e['dur']), t, 0.6)
    elif ty == 'ring': add(fol, ting(4200, 0.8), t); add(fol, whoosh_paper(0.4, 0.4), t)
    elif ty == 'travel': add(fol, whoosh_paper(e['until'] - t + 0.2), t, 0.8)
    elif ty == 'land': add(fol, stone(0.4), t); add(mus, harpsi(38, 0.5, 1.2), t)
    elif ty == 'drop': add(fol, plip(0.8), t); add(fol, brush(1.0), t + 0.08)
    elif ty == 'thunder': add(fol, thunder(1.0), t, 0.55)
    elif ty == 'wingbeat': add(fol, wingbeat(1.0), t, 0.7); add(fol, wingbeat(0.6), t + 0.8, 0.5)
    elif ty == 'hum': add(fol, hum(e['dur']), t, 0.8)
    elif ty == 'pebbles':
        for i in range(3): add(fol, stone(0.8), t + 0.35 * i + 0.1)
    elif ty == 'burnish': add(fol, rub(e['until'] - t + 0.1), t, 0.8)
    elif ty == 'clack': add(fol, clack(1.0), t, 0.8)
    elif ty == 'crystal': add(fol, ting(3600, 0.7), t)
    elif ty == 'crackle': add(fol, crackle(e['dur'], 1.0, bool(e.get('big'))), t, 1.0)
    elif ty == 'ting': add(fol, ting(3800, 0.6), t)
    elif ty == 'rain': add(fol, rain(e['until'] - t), t, 0.9)
    elif ty == 'chitter': add(fol, chitter(e['until'] - t), t, 1.0, pan=0.3)
    elif ty == 'buzz': add(fol, buzz(e['until'] - t), t, 1.0, pan=-0.2)
    elif ty == 'press': add(fol, press(1.0), t - 0.35, 0.8)
    elif ty == 'steel': add(fol, steel(1.0), t, 0.8)
    elif ty == 'bowstring': add(fol, bowstring(1.0), t, 0.9)

# ---------------- room: a quiet workroom with a faint clock; low wind at the end ----------------
room = np.zeros((N, 2))
bed = lp(sfx.brown(DUR), 700)[:N]; bed = sfx.norm(bed) * 0.006; room[:, 0] += bed; room[:, 1] += bed
for s in np.arange(0.5, DUR, 1.0): add(room, tick(0.05), s, pan=0.5)
wind = sfx.norm(lp(sfx.brown(DUR), 260))[:N] * 0.05
for e in EV:
    if e['type'] == 'wind':
        w = np.zeros(N); a, b = int(e['t'] * SR), N; w[a:b] = np.minimum(1, (np.arange(b - a)) / SR / 1.5); room[:, 0] += wind * w; room[:, 1] += wind * w

# ---------------- voice ----------------
with wave.open(os.path.join(HERE, 'out', 'voice.wav')) as f:
    vsr = f.getframerate(); v = np.frombuffer(f.readframes(f.getnframes()), np.int16).astype(np.float64) / 32768
v = resample_poly(v, SR, vsr)[:N]; v = np.r_[v, np.zeros(N - len(v))]
v = sfx.compress(hp(v, 80), thr=0.18, ratio=3.0)
act = np.abs(v) > 0.01
v *= 10 ** (-18 / 20) / np.sqrt(np.mean(v[act] ** 2))
venv = lp(np.abs(v), 6); venv = np.clip(venv / (venv.max() * 0.25), 0, 1)

# ---------------- mix ----------------
mrms = np.sqrt(np.mean(mus[int(27 * SR):int(55 * SR)] ** 2))
mus *= 10 ** (-25 / 20) / max(mrms, 1e-9)                         # music ~7 dB under the voice before ducking
mix = mus * (1 - 0.5 * venv)[:, None] + fol * 0.55 * (1 - 0.25 * venv)[:, None] + room
# real silences: music, foley and room cut (short fades); the voice is untouched
gate = np.ones(N)
for e in EV:
    if e['type'] == 'silence':
        a, b, r = int(e['t'] * SR), int(e['until'] * SR), int(0.06 * SR)
        gate[a:b] = 0; gate[a - r:a] = np.linspace(1, 0, r); gate[b - r:b] = np.minimum(gate[b - r:b], 1)
mix *= gate[:, None]
mix[:, 0] += v; mix[:, 1] += v
for ch in (0, 1): mix[:, ch] = sfx.limit(mix[:, ch], 0.95)
fade = np.ones(N); r = int(1.2 * SR); fade[-r:] = np.linspace(1, 0, r); mix *= fade[:, None]
with wave.open(os.path.join(HERE, 'out', 'mix.wav'), 'wb') as f:
    f.setnchannels(2); f.setsampwidth(2); f.setframerate(SR); f.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())

# ---------------- checks ----------------
hits = [e for e in EV if e['type'] in ('drop', 'ring', 'land', 'wingbeat', 'clack', 'crystal', 'crackle', 'press', 'steel', 'bowstring', 'thunder', 'pebbles', 'glass', 'cello', 'lowcello')]
off = [(e['type'], e['t']) for e in hits if not on_grid(e['t'])]
print(f"cuecheck: {len(hits) - len(off)}/{len(hits)} hits on the eighth-note grid" + (f"; OFF: {off}" if off else " (0 ms)"))
def band(x, lo, hi):
    X = np.abs(np.fft.rfft(x[:, 0] + x[:, 1])); fr = np.fft.rfftfreq(len(x), 1 / SR); return 10 * np.log10(np.sum(X[(fr >= lo) & (fr < hi)] ** 2) + 1e-12)
print(f"low band 20–120 Hz vs 120 Hz–8 kHz: {band(mix, 20, 120) - band(mix, 120, 8000):+.1f} dB (aim ≈ −3)")
sil = [e for e in EV if e['type'] == 'silence']
for e in sil:
    a, b = int((e['t'] + 0.1) * SR), int(e['until'] * SR); seg = (mix[a:b, 0] - v[a:b]); print(f"silence {e['t']}–{e['until']}: non-voice peak {20*np.log10(np.abs(seg).max()+1e-12):.0f} dBFS")
print('wrote out/mix.wav', round(N / SR, 2), 's')
