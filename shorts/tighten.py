"""Shorten long pauses in a narration without touching the speech.

usage: python3 tighten.py in.wav words.json out.wav out_words.json [min_gap] [keep_ratio]

Every gap between consecutive words longer than `min_gap` seconds (default 0.45) is
shrunk to  min_gap + (gap - min_gap) * keep_ratio  (default keep_ratio 0.4).
The cut is taken from the middle of the gap, so at least min_gap/2 of silence stays
on each side of every word, and short crossfades avoid clicks. Word timings are
shifted to match.
"""
import json, sys, wave
import numpy as np

src, wsrc, dst, wdst = sys.argv[1:5]
MIN_GAP = float(sys.argv[5]) if len(sys.argv) > 5 else 0.45
KEEP = float(sys.argv[6]) if len(sys.argv) > 6 else 0.4

with wave.open(src, "rb") as f:
    sr, ch, sw = f.getframerate(), f.getnchannels(), f.getsampwidth()
    assert sw == 2, "expects 16-bit PCM"
    x = np.frombuffer(f.readframes(f.getnframes()), np.int16).reshape(-1, ch).astype(np.float32)

words = json.load(open(wsrc))
cuts = []  # (start_s, length_s)
for (s0, e0, _), (s1, e1, _) in zip(words, words[1:]):
    gap = s1 - e0
    if gap > MIN_GAP:
        keep = MIN_GAP + (gap - MIN_GAP) * KEEP
        cuts.append((e0 + keep / 2, gap - keep))

xf = int(0.01 * sr)  # 10 ms crossfade
out, pos = [], 0
for st, ln in cuts:
    a, b = int(st * sr), int((st + ln) * sr)
    seg = x[pos:a].copy()
    if out and len(seg) > xf:  # fade in after the previous cut
        seg[:xf] *= np.linspace(0, 1, xf)[:, None]
    if len(seg) > xf:  # fade out before this cut
        seg[-xf:] *= np.linspace(1, 0, xf)[:, None]
    out.append(seg); pos = b
tail = x[pos:].copy()
if out and len(tail) > xf:
    tail[:xf] *= np.linspace(0, 1, xf)[:, None]
out.append(tail)
y = np.concatenate(out)

with wave.open(dst, "wb") as f:
    f.setnchannels(ch); f.setsampwidth(2); f.setframerate(sr)
    f.writeframes(np.clip(y, -32768, 32767).astype(np.int16).tobytes())

def shift(t):
    return t - sum(ln for st, ln in cuts if st + ln <= t + 1e-9)
json.dump([[round(shift(s), 2), round(shift(e), 2), w] for s, e, w in words], open(wdst, "w"))
print(f"{len(x)/sr:.2f}s -> {len(y)/sr:.2f}s ({len(cuts)} pauses shortened)")
