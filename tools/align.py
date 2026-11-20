"""Word timings for any recording (your own voice, an MP3, a finished narration) with Parakeet, offline.

usage: az align AUDIO [--script SCRIPT] [--out words.json] [--transcript transcript.txt]

Transcribes AUDIO with NVIDIA Parakeet TDT 0.6B v2 (sherpa-onnx export from the k2-fsa/sherpa-onnx GitHub
releases), cutting it at pauses into pieces of at most 15 s, and writes words.json: [[start, end, " word"], ...]
(the format faster-whisper wrote, so render.py and tighten.py read it unchanged).

With --script the words are lined up with the script: the output uses the script's own spelling and punctuation
(names come out right even when misheard), words the model missed get times from their neighbours, and every
difference between the recording and the script is listed, so the transcript can be confirmed before anything
is made. Without --script the transcript is printed and written beside the output (--transcript).
"""
import argparse, difflib, json, os, re, subprocess, sys, warnings

warnings.filterwarnings("ignore")
import numpy as np

MODELS = os.environ.get("AZUL_MODELS", os.path.expanduser("~/models"))
PARAKEET_DIR = os.path.join(MODELS, "parakeet-tdt-0.6b-v2-int8")
SR = 16000
MAX_CHUNK = 15.0


def die(msg):
    sys.exit(f"align: {msg}")


def load_audio(path):
    """Any format ffmpeg reads -> mono float32 at 16 kHz."""
    try:
        raw = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", path, "-ac", "1", "-ar", str(SR),
                              "-f", "f32le", "-"], check=True, capture_output=True).stdout
    except FileNotFoundError:
        die("ffmpeg is not on PATH (run sh tools/setup_env.sh)")
    except subprocess.CalledProcessError as e:
        die(f"ffmpeg cannot read {path}: {e.stderr.decode(errors='replace')[-300:]}")
    a = np.frombuffer(raw, np.float32).copy()
    if not len(a):
        die(f"{path} has no audio")
    return a


def pieces(a, max_len=MAX_CHUNK, min_sil=0.2):
    """Cut points inside pauses so that no piece is longer than max_len (Parakeet degrades on long clips)."""
    hop = SR // 100
    n = len(a) // hop
    if n * hop < len(a):
        n += 1
    fr = np.pad(a, (0, n * hop - len(a))).reshape(n, hop)
    db = 20 * np.log10(np.sqrt((fr ** 2).mean(1)) + 1e-9)
    db -= db.max()
    quiet = db < -35
    mids, i = [], 0
    while i < n:
        if quiet[i]:
            j = i
            while j < n and quiet[j]:
                j += 1
            if (j - i) / 100 >= min_sil:
                mids.append((i + j) // 2)
            i = j
        else:
            i += 1
    bounds, s, lim = [0], 0, int(max_len * 100)
    while n - s > lim:
        cand = [c for c in mids if s + 200 < c <= s + lim]
        c = max(cand) if cand else s + 800 + int(np.argmin(db[s + 800:s + lim]))
        bounds.append(c)
        s = c
    bounds.append(n)
    return [(b0 * hop, min(len(a), b1 * hop)) for b0, b1 in zip(bounds, bounds[1:]) if b1 > b0]


def recognizer():
    import sherpa_onnx
    d = PARAKEET_DIR
    if not os.path.exists(f"{d}/encoder.int8.onnx"):
        die(f"the Parakeet model is not in {d}: run  sh tools/setup_env.sh")
    return sherpa_onnx.OfflineRecognizer.from_transducer(
        encoder=f"{d}/encoder.int8.onnx", decoder=f"{d}/decoder.int8.onnx", joiner=f"{d}/joiner.int8.onnx",
        tokens=f"{d}/tokens.txt", model_type="nemo_transducer", num_threads=min(4, os.cpu_count() or 1))


def transcribe(a):
    rec, words = recognizer(), []
    for p0, p1 in pieces(a):
        seg = a[p0:p1]
        pk = np.abs(seg).max()
        if pk < 1e-4:
            continue
        st = rec.create_stream()
        st.accept_waveform(SR, (seg / pk * 0.5).astype(np.float32))
        rec.decode_stream(st)
        r, off = st.result, p0 / SR
        for tok, ts, du in zip(r.tokens, r.timestamps, r.durations):
            core = tok.strip()
            if not core:
                continue
            punct = not any(c.isalnum() for c in core)
            if words and (punct or not tok.startswith(" ")):
                words[-1][2] += core                 # word piece or punctuation: same word
                if not punct:
                    words[-1][1] = round(off + ts + du, 3)
            else:
                words.append([round(off + ts, 3), round(off + ts + du, 3), " " + core])
    return words


def subtokens(text):
    from num2words import num2words
    t = re.sub(r"\d+(?:\.\d+)?", lambda m: " " + num2words(float(m.group()) if "." in m.group() else int(m.group())) + " ", text)
    t = t.lower().replace("’", "'").replace("-", " ").replace("—", " ")
    return [w for w in re.sub(r"[^a-z0-9' ]", " ", t).split() if w.strip("'")]


def align(heard, script_text):
    """Give every script word a time from the recognised words; return (words, differences)."""
    sw = script_text.split()
    a, ai = [], []
    for i, w in enumerate(sw):
        for t in subtokens(w):
            a.append(t); ai.append(i)
    b, bi = [], []
    for j, (_, _, w) in enumerate(heard):
        for t in subtokens(w):
            b.append(t); bi.append(j)
    span = [[None, None] for _ in sw]

    def give(i, t0, t1):
        s = span[i]
        s[0] = t0 if s[0] is None else min(s[0], t0)
        s[1] = t1 if s[1] is None else max(s[1], t1)

    diffs = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op == "equal":
            for k in range(i2 - i1):
                h = heard[bi[j1 + k]]
                give(ai[i1 + k], h[0], h[1])
            continue
        diffs.append(f"script '{' '.join(a[i1:i2]) or '∅'}'  heard '{' '.join(b[j1:j2]) or '∅'}'")
        if op == "replace":                           # misheard words: share the heard span by length
            ws = sorted(set(ai[i1:i2]))
            hs = sorted(set(bi[j1:j2]))
            t0, t1 = heard[hs[0]][0], heard[hs[-1]][1]
            lens = np.array([len(sw[i]) for i in ws], float)
            edges = t0 + (t1 - t0) * np.concatenate([[0], np.cumsum(lens) / lens.sum()])
            for k, i in enumerate(ws):
                give(i, float(edges[k]), float(edges[k + 1]))
    # words nobody heard: interpolate between their neighbours, by length
    i = 0
    while i < len(sw):
        if span[i][0] is not None:
            i += 1
            continue
        j = i
        while j < len(sw) and span[j][0] is None:
            j += 1
        t0 = span[i - 1][1] if i > 0 else (heard[0][0] if heard else 0.0)
        t1 = span[j][0] if j < len(sw) else (heard[-1][1] if heard else t0)
        lens = np.array([len(sw[k]) for k in range(i, j)], float)
        edges = t0 + (max(t1, t0) - t0) * np.concatenate([[0], np.cumsum(lens) / lens.sum()])
        for k in range(i, j):
            span[k] = [float(edges[k - i]), float(edges[k - i + 1])]
        i = j
    out = [[round(s[0], 3), round(max(s[0], s[1]), 3), " " + w] for s, w in zip(span, sw)]
    return out, diffs


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("audio")
    ap.add_argument("--script", help="the text that was read (lines starting with # and [pause] lines are ignored)")
    ap.add_argument("--out", default="words.json")
    ap.add_argument("--transcript", help="where to write the plain transcript (default: beside --out)")
    o = ap.parse_args()

    a = load_audio(o.audio)
    heard = transcribe(a)
    text = " ".join(w.strip() for _, _, w in heard)
    tr = o.transcript or os.path.join(os.path.dirname(os.path.abspath(o.out)), "transcript.txt")
    open(tr, "w", encoding="utf-8").write(text + "\n")
    print(f"{o.audio}: {len(a) / SR:.2f} s, {len(heard)} words heard")
    if o.script:
        lines = [l.strip() for l in open(o.script, encoding="utf-8").read().splitlines()]
        script = " ".join(l for l in lines if l and not l.startswith("#") and not re.fullmatch(r"\[pause[^\]]*\]", l, re.I))
        words, diffs = align(heard, script)
        print(f"lined up with {o.script}: {len(words)} words")
        print("recording matches the script word for word" if not diffs else
              f"{len(diffs)} difference(s) between recording and script:\n  " + "\n  ".join(diffs))
    else:
        words = heard
        print("transcript (confirm it before using it):\n" + text)
    json.dump(words, open(o.out, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"wrote {o.out} and {tr}")


if __name__ == "__main__":
    main()
