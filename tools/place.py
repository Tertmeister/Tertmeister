"""Place the narration lines on a film's timeline (the voice.py every episode had, made general).

usage: az place ASSETS FILM [--open 0.9] [--gap 0.6] [--tail 4.0] [--pin LINE=SECONDS ...]

Reads ASSETS/narration.wav and ASSETS/narration_lines.json ([start, end, text] per line, as az narrate writes
them) and, when present, ASSETS/words.json. Each line keeps its own audio untouched; lines are moved so the film
opens with --open seconds before the first word and every caption can hold for its spoken line + --gap seconds
before the next line starts (a longer pause in the narration is kept). --pin 5=36.1 starts line 5 (0-based) at
36.1 s, or as soon after as the line before allows. The film ends --tail seconds after the last word.

Writes FILM/out/voice.wav (narration sample rate, mono 16-bit), FILM/timeline.json ({"dur", "lines": [{"i", "t0",
"t1", "text", "src"}]}) and, with words.json, FILM/words_film.json ([t0, t1, word, line] in film time).
"""
import argparse, json, os, sys
import numpy as np
import soundfile as sf


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("assets")
    ap.add_argument("film")
    ap.add_argument("--open", type=float, default=0.9, help="film seconds before the first word")
    ap.add_argument("--gap", type=float, default=0.6, help="caption hold after each line")
    ap.add_argument("--tail", type=float, default=4.0, help="film seconds after the last word")
    ap.add_argument("--pin", action="append", default=[], metavar="LINE=SECONDS")
    o = ap.parse_args()

    x, sr = sf.read(os.path.join(o.assets, "narration.wav"), dtype="int16")
    if x.ndim > 1:
        x = x[:, 0]
    lines = json.load(open(os.path.join(o.assets, "narration_lines.json"), encoding="utf-8"))
    pins = {}
    for p in o.pin:
        i, _, t = p.partition("=")
        pins[int(i)] = float(t)
    bad = [i for i in pins if not 0 <= i < len(lines)]
    if bad:
        sys.exit(f"place: --pin line {bad[0]} does not exist (there are {len(lines)} lines, numbered from 0)")

    placed, prev = [], None
    for i, (s, e, text) in enumerate(lines):
        if prev is None:
            ns = o.open
        else:
            ps, pe, pns = prev
            ns = max(pns + (s - ps), pns + (pe - ps) + o.gap)
        if i in pins:  # the pinned time, unless the line before is still speaking (then right after its hold)
            ns = pins[i] if prev is None else max(pins[i], pns + (pe - ps) + o.gap)
        placed.append({"i": i, "t0": round(ns, 3), "t1": round(ns + (e - s), 3), "text": text, "src": [s, e]})
        prev = (s, e, ns)

    dur = round(placed[-1]["t1"] + o.tail, 2)
    y = np.zeros(int(dur * sr), np.int16)
    for L in placed:
        a, b = int(L["src"][0] * sr), int(L["src"][1] * sr)
        seg, at = x[a:b], int(L["t0"] * sr)
        y[at:at + len(seg)] = seg[: len(y) - at]
    os.makedirs(os.path.join(o.film, "out"), exist_ok=True)
    sf.write(os.path.join(o.film, "out", "voice.wav"), y, sr, subtype="PCM_16")
    json.dump({"dur": dur, "lines": placed}, open(os.path.join(o.film, "timeline.json"), "w", encoding="utf-8"),
              indent=1, ensure_ascii=False)

    wpath = os.path.join(o.assets, "words.json")
    if os.path.exists(wpath):
        film_words = []
        for s, e, w in json.load(open(wpath, encoding="utf-8")):
            L = next((L for L in placed if L["src"][0] - 0.05 <= s <= L["src"][1] + 0.05), None)
            if L is None:
                continue
            d = L["t0"] - L["src"][0]
            film_words.append([round(s + d, 3), round(e + d, 3), w.strip(), L["i"]])
        json.dump(film_words, open(os.path.join(o.film, "words_film.json"), "w", encoding="utf-8"), ensure_ascii=False)
    for L in placed:
        print(f'{L["t0"]:7.2f}-{L["t1"]:7.2f}  {L["text"]}')
    print("DUR", dur)


if __name__ == "__main__":
    main()
