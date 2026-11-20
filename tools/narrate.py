"""Narrate a script locally with Kokoro: no credits, no network, exact line spans and word timings.

usage:
  az narrate SCRIPT OUTDIR [--voice V] [--speed S] [--gap SEC] [--split lines|sentences]
                           [--lexicon FILE] [--check] [--no-verify]
  az say "some text" OUT.wav [--voice V] [--speed S]          (one-off line, e.g. to audition a name)

SCRIPT    plain text. Every non-empty line is one narration line (--split sentences splits paragraphs into
          sentences instead). Lines starting with # are skipped. A line "[pause 1.5]" adds 1.5 s of extra
          silence before the next line. Inline pronunciation: [Aquarion](/əkwˈɛɹiən/) (misaki phonemes).
OUTDIR    receives
            narration.wav           24 kHz mono 16-bit, the lines back to back with --gap seconds between them
            narration_lines.json    [[start, end, text], ...]  exact span of every line in narration.wav
            words.json              [[start, end, " word"], ...] from the voice model's own phoneme durations
                                    (the same format faster-whisper wrote, so render.py and tighten.py read it)
            narration_phonemes.json what each word was turned into, and where that pronunciation came from
--voice   a Kokoro voice (am_michael, bm_george, ...) or a blend such as "bm_george*0.7+bm_lewis*0.3".
          Default: $AZUL_VOICE, else am_michael. am_/af_ voices speak US English, bm_/bf_ voices British.
--speed   Kokoro's own speaking rate (0.5-2.0); better than speeding the audio up afterwards.
--check   print how every word outside the dictionary (names, coinages) will be pronounced, and stop (no audio).
--lexicon JSON {"Aquarion": "/əkwˈɛɹiən/", "Bifrost": "BIFF-rost"}: a value in slashes is phonemes, anything
          else is a respelling read as written. Default: lexicon.json beside the script, plus tools/lexicon.json.
After narrating, every line is transcribed with Parakeet and lines that came out different are listed
(made-up names often differ: listen to those). --no-verify skips that.

Pipeline: misaki (the phonemizer Kokoro was trained with: dictionary first, espeak-ng only for unknown words)
-> Kokoro v1.0 ONNX for the sound (the library's model, deterministic, matches the PyTorch release) and the
duration head of the kokoro-onnx model-files-v1.1 export for the timing of every phoneme (same predictor, so its
frames x 600 equal the v1.0 audio length exactly). Measured on speech onsets: word starts within about 0.04 s.
"""
import argparse, difflib, json, os, re, sys, time, warnings

warnings.filterwarnings("ignore")
import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
MODELS = os.environ.get("AZUL_MODELS", os.path.expanduser("~/models"))
LIB = os.environ.get("LIB", os.path.expanduser("~/lemo-opuscar"))
AUDIO_MODEL = os.path.join(LIB, "core", "tts", "kokoro-v1.0.onnx")
DUR_MODEL = os.path.join(MODELS, "kokoro-durations", "durations.onnx")
VOICES = os.path.join(MODELS, "kokoro-v1.1", "voices-v1.0.bin")
PARAKEET_DIR = os.path.join(MODELS, "parakeet-tdt-0.6b-v2-int8")
SR = 24000
MAX_TOKENS = 510                 # Kokoro's context: one line must fit in one take
LEAD, TAIL, FADE = 0.04, 0.10, 0.005   # air kept before / after each line, and the edge fade (s)


def die(msg):
    sys.exit(f"narrate: {msg}")


# ---------- script and lexicon ----------
SENT = re.compile(r"(?<=[.!?…])[\"”’)]*\s+(?=[\"“‘(\[]?[A-Z0-9])")


def read_script(path, split):
    items = []
    for raw in open(path, encoding="utf-8").read().splitlines():
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        m = re.fullmatch(r"\[pause\s+([\d.]+)\s*s?\]", s, re.I)
        if m:
            items.append(("pause", float(m.group(1))))
        elif split == "sentences":
            items += [("line", x.strip()) for x in SENT.split(s) if x.strip()]
        else:
            items.append(("line", s))
    if not any(k == "line" for k, _ in items):
        die(f"{path} has no narration lines")
    return items


def load_lexicon(paths, g2p):
    lex = {}
    for p in paths:
        if p and os.path.exists(p):
            for k, v in json.load(open(p, encoding="utf-8")).items():
                if k.startswith("_"):
                    continue
                v = v.strip()
                lex[k] = v[1:-1] if v.startswith("/") and v.endswith("/") else g2p(v)[0].strip()
    return lex


def apply_lexicon(text, lex):
    for k in sorted(lex, key=len, reverse=True):
        text = re.sub(rf"(?<![\w\[/]){re.escape(k)}(?![\w\]])", f"[{k}](/{lex[k]}/)", text)
    return text


# ---------- engines ----------
def lang_of(spec):
    return "en-gb" if spec.strip()[:1] == "b" else "en-us"


def make_g2p(spec):
    import espeakng_loader
    from phonemizer.backend.espeak.wrapper import EspeakWrapper
    EspeakWrapper.set_library(espeakng_loader.get_library_path())   # misaki's fallback needs it registered
    EspeakWrapper.set_data_path(espeakng_loader.get_data_path())
    from misaki import en, espeak
    brit = lang_of(spec) == "en-gb"
    return en.G2P(trf=False, british=brit, fallback=espeak.EspeakFallback(british=brit))


class Engine:
    """Kokoro v1.0 for the sound + the v1.1 duration head for the timing of every phoneme."""

    def __init__(self, spec):
        import onnxruntime as ort
        from kokoro_onnx.config import DEFAULT_VOCAB
        for p, what in ((AUDIO_MODEL, "Kokoro v1.0 model"), (DUR_MODEL, "Kokoro duration model"), (VOICES, "Kokoro voices")):
            if not os.path.exists(p):
                die(f"the {what} is missing ({p}): run  sh tools/setup_env.sh")
        prov = ["CPUExecutionProvider"]
        self.audio = ort.InferenceSession(AUDIO_MODEL, providers=prov)
        self.dur = ort.InferenceSession(DUR_MODEL, providers=prov)
        self.tok_in = self.audio.get_inputs()[0].name           # 'tokens' in the v1.0 export
        self.vocab = DEFAULT_VOCAB
        voices = np.load(VOICES)
        total, style = 0.0, None
        for part in spec.split("+"):
            name, _, w = part.strip().partition("*")
            if name not in voices.files:
                die(f"unknown voice '{name}'. Available: {' '.join(sorted(voices.files))}")
            w = float(w) if w else 1.0
            style = voices[name] * w if style is None else style + voices[name] * w
            total += w
        self.style = (style / total).astype(np.float32)        # (510, 1, 256): one row per phoneme count

    def run(self, tokens, speed):
        ids = np.array([[0, *tokens, 0]], np.int64)
        common = {"style": self.style[min(len(tokens), len(self.style)) - 1],
                  "speed": np.array([speed], np.float32)}
        audio = self.audio.run(None, {self.tok_in: ids, **common})[0].ravel().astype(np.float32)
        dur = self.dur.run(None, {"input_ids": ids, **common})[0].ravel().astype(np.int64)
        return audio, dur


SOURCE = {5: "dictionary", 4: "dictionary", 3: "derived", 2: "guessed (espeak rules)", 1: "guessed (espeak rules)"}


def words_of(tokens, lexwords):
    """Group misaki tokens into words (split where the text has whitespace). Returns the phoneme string misaki
    built (''.join(phonemes + whitespace)) and for each word its text, its span in that string and its source."""
    s, words, cur = "", [], None
    for t in tokens:
        p = t.phonemes or ""
        if cur is None:
            cur = {"text": "", "a": None, "b": None, "ps": "", "src": None}
        a = len(s)
        s += p
        cur["text"] += t.text + t.whitespace
        if any(ch.isalpha() for ch in p):
            cur["a"] = a if cur["a"] is None else cur["a"]
            cur["b"] = len(s)
            cur["ps"] += p
            src = "lexicon" if t.text in lexwords else SOURCE.get(t.rating, "unknown")
            cur["src"] = src if cur["src"] in (None, "dictionary") else cur["src"]
        s += t.whitespace
        if t.whitespace:
            words.append(cur)
            cur = None
    if cur:
        words.append(cur)
    out = []
    for w in words:
        w["text"] = w["text"].strip()
        if not w["text"]:
            continue
        if w["a"] is None and out:            # stray punctuation such as a spaced dash: keep it with the word before
            out[-1]["text"] += " " + w["text"]
            continue
        out.append(w)
    return s, out


def synth(eng, g2p, text, speed, lex, sp=0.0, cp=0.0):
    """One line -> (audio float32 @24k, words with times in that audio, phoneme string)."""
    from kokoro_onnx.pauses import insert as insert_pauses
    from kokoro_onnx.sliding import Timing
    _, toks = g2p(apply_lexicon(text, lex))
    s, words = words_of(toks, set(lex))
    keep = []                                   # positions in s that become model tokens (spaces collapsed)
    for i, c in enumerate(s):
        if c in eng.vocab and not (c == " " and (not keep or s[keep[-1]] == " ")):
            keep.append(i)
    while keep and s[keep[-1]] == " ":
        keep.pop()
    if not keep:
        die(f"no phonemes for: {text!r}")
    if len(keep) > MAX_TOKENS:
        die(f"this line is too long for one take ({len(keep)} phonemes, at most {MAX_TOKENS}); split it: {text[:70]}...")
    audio, dur = eng.run([eng.vocab[s[i]] for i in keep], speed)
    edges = np.concatenate([[0], np.cumsum(dur)]) * (len(audio) / max(1, int(dur.sum())))   # padded-token bounds
    tim = [Timing(s[ci], float(edges[t + 1] / SR), float(edges[t + 2] / SR)) for t, ci in enumerate(keep)]
    audio, tim = insert_pauses(audio, tim, SR, sp, cp)          # a no-op at 0 / 0 (Kokoro's own pauses)
    pos = {ci: t for t, ci in enumerate(keep)}
    for w in words:
        ts = [pos[i] for i in range(w["a"] or 0, w["b"] or 0) if i in pos]
        w["t0"], w["t1"] = (tim[min(ts)].start, tim[max(ts)].end) if ts else (None, None)
    for i, w in enumerate(words):                # words without a phoneme the model knows: from the neighbours
        if w["t0"] is None:
            prev = next((x["t1"] for x in reversed(words[:i]) if x["t1"] is not None), 0.0)
            nxt = next((x["t0"] for x in words[i + 1:] if x["t0"] is not None), len(audio) / SR)
            w["t0"], w["t1"] = prev, max(prev, nxt)
    # no offset, trim to the sound keeping a little air, fade the edges, and move the word times with the trim
    audio = audio - float(audio.mean())
    env = np.abs(audio)
    nz = np.where(env > env.max() * 0.015)[0]
    a0, a1 = (max(0, nz[0] - int(LEAD * SR)), min(len(audio), nz[-1] + int(TAIL * SR))) if len(nz) else (0, len(audio))
    audio = audio[a0:a1].copy()
    f = min(int(FADE * SR), len(audio) // 2)
    if f:
        ramp = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, f))
        audio[:f] *= ramp
        audio[-f:] *= ramp[::-1]
    n = len(audio) / SR
    for w in words:
        w["t0"] = min(max(0.0, w["t0"] - a0 / SR), n)
        w["t1"] = min(max(w["t0"], w["t1"] - a0 / SR), n)
    return audio.astype(np.float32), words, s


# ---------- speech check ----------
def norm_words(text):
    from num2words import num2words
    text = re.sub(r"\d+(?:\.\d+)?", lambda m: " " + num2words(float(m.group()) if "." in m.group() else int(m.group())) + " ", text)
    text = text.lower().replace("’", "'").replace("-", " ").replace("—", " ").replace(",", " ")
    return [w for w in re.sub(r"[^a-z0-9' ]", " ", text).split() if w.strip("'")]


class Ear:
    def __init__(self):
        import sherpa_onnx
        d = PARAKEET_DIR
        if not os.path.exists(f"{d}/encoder.int8.onnx"):
            raise FileNotFoundError(f"{d} (run sh tools/setup_env.sh)")
        self.rec = sherpa_onnx.OfflineRecognizer.from_transducer(
            encoder=f"{d}/encoder.int8.onnx", decoder=f"{d}/decoder.int8.onnx", joiner=f"{d}/joiner.int8.onnx",
            tokens=f"{d}/tokens.txt", model_type="nemo_transducer", num_threads=min(4, os.cpu_count() or 1))

    def hear(self, audio, sr):
        import soxr
        a = soxr.resample(audio.astype(np.float32), sr, 16000) if sr != 16000 else audio.astype(np.float32)
        a = a / (np.abs(a).max() + 1e-9) * 0.5
        st = self.rec.create_stream()
        st.accept_waveform(16000, a)
        self.rec.decode_stream(st)
        return st.result


def diff_words(said, heard):
    a, b = norm_words(said), norm_words(heard)
    out = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op != "equal":
            out.append(f"{' '.join(a[i1:i2]) or '∅'} -> {' '.join(b[j1:j2]) or '∅'}")
    return out


# ---------- main ----------
def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("script", help="script file, or the text itself with --say")
    ap.add_argument("out", help="output folder (or a .wav path with --say)")
    ap.add_argument("--say", action="store_true", help="speak SCRIPT as text into the wav OUT")
    ap.add_argument("--voice", default=os.environ.get("AZUL_VOICE", "am_michael"))
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--gap", type=float, default=0.45, help="silence between lines in narration.wav (s)")
    ap.add_argument("--split", choices=("lines", "sentences"), default="lines")
    ap.add_argument("--lexicon", action="append", default=None)
    ap.add_argument("--sentence-pause", type=float, default=0.0, help="least pause after . ! ? inside a line (0 = Kokoro's own)")
    ap.add_argument("--clause-pause", type=float, default=0.0, help="least pause after , ; : inside a line (0 = Kokoro's own)")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--no-verify", action="store_true")
    o = ap.parse_args()
    if not 0.5 <= o.speed <= 2.0:
        die("--speed must be between 0.5 and 2.0")

    t0 = time.time()
    g2p = make_g2p(o.voice)
    if o.say:
        lex = load_lexicon(o.lexicon or [os.path.join(HERE, "lexicon.json")], g2p)
        eng = Engine(o.voice)
        audio, words, s = synth(eng, g2p, o.script, o.speed, lex, o.sentence_pause, o.clause_pause)
        os.makedirs(os.path.dirname(os.path.abspath(o.out)), exist_ok=True)
        sf.write(o.out, audio, SR, subtype="PCM_16")
        print(f"{o.out}  {len(audio) / SR:.2f} s  /{s.strip()}/")
        return

    items = read_script(o.script, o.split)
    lexfiles = o.lexicon or [os.path.join(os.path.dirname(os.path.abspath(o.script)), "lexicon.json"),
                             os.path.join(HERE, "lexicon.json")]
    lex = load_lexicon(lexfiles, g2p)

    if o.check:
        seen = {}
        for kind, text in items:
            if kind != "line":
                continue
            _, toks = g2p(apply_lexicon(text, lex))
            for w in words_of(toks, set(lex))[1]:
                if w["src"] not in ("dictionary", "derived"):
                    seen.setdefault(w["text"].strip(".,;:!?\"“”‘’()—…"), (w["ps"], w["src"]))
        print(f"{len(seen)} words not in the dictionary, pronounced by rule or by your lexicon "
              f"(voice {o.voice}, {lang_of(o.voice)}):")
        for w, (ps, src) in seen.items():
            print(f"  {w:24s} /{ps}/   {src}")
        print("Fix one with a lexicon entry or inline [word](/phonemes/); audition it with: az say \"word\" out.wav")
        return

    eng = Engine(o.voice)
    os.makedirs(o.out, exist_ok=True)
    gap = np.zeros(int(o.gap * SR), np.float32)
    parts, lines, allwords, review, pos, extra = [], [], [], [], 0, 0.0
    for kind, val in items:
        if kind == "pause":
            extra += val
            continue
        if lines:
            pad = np.concatenate([gap, np.zeros(int(extra * SR), np.float32)])
            parts.append(pad)
            pos += len(pad)
        extra = 0.0
        audio, words, s = synth(eng, g2p, val, o.speed, lex, o.sentence_pause, o.clause_pause)
        t_line = pos / SR
        lines.append([round(t_line, 3), round(t_line + len(audio) / SR, 3), val])
        for w in words:
            allwords.append([round(t_line + w["t0"], 3), round(t_line + w["t1"], 3), " " + w["text"]])
        review.append({"line": len(lines) - 1, "text": val, "phonemes": s.strip(),
                       "words": [[w["text"], w["ps"], w["src"]] for w in words]})
        parts.append(audio)
        pos += len(audio)
        print(f"{lines[-1][0]:7.2f}-{lines[-1][1]:7.2f}  {val}")
    y = np.concatenate(parts)
    peak = float(np.abs(y).max())
    if peak > 0.98:
        y *= 0.98 / peak
    sf.write(os.path.join(o.out, "narration.wav"), y, SR, subtype="PCM_16")
    json.dump(lines, open(os.path.join(o.out, "narration_lines.json"), "w", encoding="utf-8"), indent=0, ensure_ascii=False)
    json.dump(allwords, open(os.path.join(o.out, "words.json"), "w", encoding="utf-8"), ensure_ascii=False)
    json.dump({"voice": o.voice, "speed": o.speed, "lang": lang_of(o.voice), "lines": review},
              open(os.path.join(o.out, "narration_phonemes.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(f"narration.wav  {len(y) / SR:.2f} s, {len(lines)} lines, {len(allwords)} words, "
          f"voice {o.voice} speed {o.speed}  ({time.time() - t0:.1f} s)")

    if not o.no_verify:
        try:
            ear = Ear()
        except Exception as e:  # the check is a help, not a requirement
            print(f"(speech check skipped: {e})")
            return
        bad = 0
        for i, (a, b, text) in enumerate(lines):
            d = diff_words(text, ear.hear(y[int(a * SR):int(b * SR)], SR).text)
            if d:
                bad += 1
                print(f"  line {i}: heard differently: " + "; ".join(d))
        print("speech check: every line heard as written" if not bad else
              f"speech check: {bad} line(s) heard differently (names often are: listen to those lines)")


if __name__ == "__main__":
    main()
