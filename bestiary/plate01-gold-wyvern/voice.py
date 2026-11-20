"""Place the narration lines on the film's timeline.

Reads assets/narration.wav (Kokoro bm_george, sped 5 % with ffmpeg atempo, one take, lines back to back with
pauses) and assets/narration_lines.json ([start, end, text] per line, exact sample
spans from the TTS run). Each line keeps its own audio untouched; lines are moved
so the film opens with a short beat before the first word and every caption can
hold for its spoken line + 0.6 s (DIRECTOR.md section 7) before the next one starts.

Writes out/voice.wav (24 kHz mono) and timeline.json (lines with film times).
"""
import json, os, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OPEN = 0.9         # seconds of film before the first word (the burin is already cutting)
MIN_GAP = 0.6      # caption hold after speech

with wave.open(os.path.join(HERE, "assets/narration.wav")) as f:
    sr = f.getframerate()
    x = np.frombuffer(f.readframes(f.getnframes()), np.int16)
lines = json.load(open(os.path.join(HERE, "assets/narration_lines.json")))

placed, prev = [], None
for i, (s, e, text) in enumerate(lines):
    if prev is None:
        ns = OPEN
    else:
        ps, pe, pns = prev
        ns = max(pns + (s - ps), pns + (pe - ps) + MIN_GAP)
    placed.append({"i": i, "t0": round(ns, 3), "t1": round(ns + (e - s), 3), "text": text, "src": [s, e]})
    prev = (s, e, ns)

tail = 4.0  # the finished plate holds after the last word
dur = round(placed[-1]["t1"] + tail, 2)
y = np.zeros(int(dur * sr), np.int16)
for L in placed:
    a, b = int(L["src"][0] * sr), int(L["src"][1] * sr)
    seg = x[a:b]
    at = int(L["t0"] * sr)
    y[at:at + len(seg)] = seg[: len(y) - at]

os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
with wave.open(os.path.join(HERE, "out/voice.wav"), "wb") as f:
    f.setnchannels(1); f.setsampwidth(2); f.setframerate(sr); f.writeframes(y.tobytes())
json.dump({"dur": dur, "lines": placed}, open(os.path.join(HERE, "timeline.json"), "w"), indent=1)
for L in placed:
    print(f'{L["t0"]:6.2f}-{L["t1"]:6.2f}  {L["text"]}')
print("DUR", dur)
