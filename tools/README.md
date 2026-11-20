# Production toolkit (both series)

Free, offline tools for narration, timing, sound and delivery, all installed from GitHub releases (plus PyPI and
npm packages). `tools/az` is the single entry point; every command takes `-h`.

```sh
sh tools/setup_env.sh        # install whatever is missing (safe to re-run; also the cloud environment's setup script)
tools/az doctor              # what is installed
```

## Commands

| Command | What it does |
|---|---|
| `az narrate SCRIPT OUTDIR --voice am_michael` | Narrates a script with Kokoro on this machine: `narration.wav`, `narration_lines.json` (exact span of every line), `words.json` (every word's timing, from the voice model itself), `narration_phonemes.json`. Then transcribes each line with Parakeet and lists lines that came out different. |
| `az narrate SCRIPT OUTDIR --check` | No audio: lists every word outside the dictionary (names, coinages) and how it will be said. Safe during script review. |
| `az say "text" out.wav` | One line, e.g. to audition a name. |
| `az align AUDIO --script script.txt` | Word timings for any recording (your own voice, an MP3) with Parakeet, lined up with the script's spelling; lists every difference so the transcript can be confirmed. |
| `az place ASSETS FILM --open 0.9 --gap 0.6 --tail 4` | Lays the lines on the film timeline (what each episode's `voice.py` did): `out/voice.wav`, `timeline.json`, `words_film.json`. `--pin 5=36.1` holds a line to a picture beat. |
| `az fx IN.wav OUT.wav --preset narrator\|study\|crypt` | A mic'd, finished voice: rumble cut, warmth, presence, gentle compression; `study` adds a small wooden room (Bestiary), `crypt` a long stone tail (Songs). Timing is untouched. `--deess` for harsh s sounds. |
| `az deliver MASTER.mp4 short.mp4 --vmaf` | The upload copy (x264, CRF 22, 6 Mbit/s cap; two passes if it would pass 95 MB), then checks: under 3 min, 9:16, loudness −14 LUFS / −1 dBTP, size, fast start; VMAF against the master. `--check FILM.mp4` checks only. |
| `az tighten …` | `shorts/tighten.py`: shortens long pauses only. |
| `az lint [PATHS]` | ruff (Python, rules in `ruff.toml`) and ShellCheck (every `.sh`) over the repository. |
| `az selftest` | 20 s end to end on a test sentence: narrate → place → fx → align → deliver check. Run it in a new session. |
| `az py …` | The toolchain's Python (the library's venv: numpy, soundfile, sampler, pluck, Pedalboard …). |

Voices: Kokoro's 54 voices, or a blend such as `--voice "bm_george*0.7+bm_lewis*0.3"`. `--speed` uses Kokoro's
own speaking rate (better than speeding the audio up afterwards). Pronunciations: `tools/lexicon.json` (all
episodes) or a `lexicon.json` beside the script, `"Name": "/phonemes/"` or `"Name": "RESPELLING"`; inline
`[Aquarion](/əkwˈɛɹiən/)` in a script works too.

## An episode with these tools

1. Write the script → **the user approves it** (repo `CLAUDE.md`, rule 1). `az narrate script.txt assets --check`
   (no audio) may be shown alongside the script so names can be vetoed with it.
2. `az narrate script.txt assets --voice am_michael` (Songs) or `--voice bm_george` (Bestiary).
3. Optional: `az fx assets/narration.wav assets/narration_fx.wav --preset crypt` (keep the dry take too).
4. `az place assets . --open 0.9 --gap 0.6 --tail 4` → `timeline.json`, `out/voice.wav`, `words_film.json`.
5. Picture and score as before (`index.html` / `film.js`, `mix.py`), master with `mux.sh`.
6. `az deliver out/short_master.mp4 short.mp4 --vmaf`.

Scoring with real instruments in `mix.py` (the library's sampler; 97 sampled instruments, see
`~/lemo-opuscar/core/audio/INSTRUMENTS.md`):

```python
import os, sys; sys.path.insert(0, os.environ.get("LIB", os.path.expanduser("~/lemo-opuscar")))
from core.audio import sampler as S
bed = S.render([(0.0, 'cellos', 'D2', 6.0, .55, -.2), (0.1, 'harpsichord', 'A3', 1.0, .6, .3),
                (4.1, 'glass', 'D5', 3.0, .5, 0)], dur=8)       # (t, instrument, pitch, dur, velocity, pan)
bed = S.room(bed, size=.5, mix=.2)
print('\n'.join(S.credits(['cellos', 'harpsichord', 'glass'])))   # lines for CREDITS
```

Good fits: Bestiary (`harpsichord`, `cellos`, `cellos_pizz`, `contrabass_pizz`, `glass`, `harp`, `hand_chimes`,
`recorder`, `organ_soft`); Songs (`cellos`, `contrabass`, `violins_trem`, `organ`, `organ_pedal`, `tubular_bells`,
`timpani`, `gran_cassa`, `gong`, `sus_cymbal` bowed, `vibraphone_bowed`).

## What is installed, and from where

| Part | Source | Where |
|---|---|---|
| ffmpeg + ffprobe 8.1 (x264/x265/AV1, loudnorm, rubberband, libass, zscale, VMAF, de-esser) | github.com/BtbN/FFmpeg-Builds (checksum verified) | `/opt/ffmpeg-8.1`, linked in `/usr/local/bin` |
| Lemo-Opuscar library + core, voice, music packages, Kokoro v1.0 model | github.com/lemomo-ai/lemo-opuscar | `~/lemo-opuscar` |
| Sampled instruments: VSCO 2 CE, VCSL, FreePats (also Salamander piano, Karoryfer on demand) | lemo-opuscar `assets` release (checksums verified) | `~/lemo-opuscar/core/audio/instruments` |
| Kokoro v1.1 export (only its duration head is used) + voices | github.com/thewh1teagle/kokoro-onnx `model-files-v1.1` (pinned sha256) | `~/models/kokoro-v1.1`, `~/models/kokoro-durations` |
| Parakeet TDT 0.6B v2, int8 (NVIDIA, CC BY 4.0) | github.com/k2-fsa/sherpa-onnx `asr-models` (pinned sha256) | `~/models/parakeet-tdt-0.6b-v2-int8` |
| misaki (Kokoro's own phonemizer), spaCy `en_core_web_sm` | PyPI; github.com/explosion/spacy-models | library venv |
| sherpa-onnx, Pedalboard, pyloudnorm, onnx | PyPI (github.com/k2-fsa, spotify, csteinmetz1, onnx) | library venv |
| ruff, ShellCheck | PyPI (github.com/astral-sh/ruff, koalaman/shellcheck) | library venv |

A from-scratch install (empty folders, every download) took 3 min 31 s and 4.1 GB here; with everything present the
script finishes in about a second.

## Why these, and what was measured

- **Narration without the sandbox.** Same Kokoro model and voices as the Higgsfield-sandbox narrations, run here:
  about 2.5 s of compute per 10 s of speech, no cold starts, no uploads. misaki is the phonemizer Kokoro was trained
  with (dictionary first, espeak-ng only for unknown words); the library's own `tts.py` sends raw espeak symbols
  for every word instead.
- **Sound from v1.0, timing from v1.1.** The v1.1 export has a duration output but measured 3–6 dB duller above
  1 kHz than v1.0 with a strong sub-40 Hz offset; v1.0 is deterministic and matches the PyTorch release. Both share
  the duration predictor (frames × 600 = the v1.0 audio length exactly), so the v1.1 duration head (cut out with
  onnx: 50 ms per line) times the v1.0 audio. Word starts land within 0.04 s of the real speech onsets.
- **Parakeet instead of Whisper** (Whisper's models are on huggingface.co, which this environment blocks). On Plate
  I's narration its word starts are unbiased (median within 0.03 s of the speech onsets; the Whisper timings the plate
  was cut to ran 0.09 s late), and it transcribed the 2:15 narration in 12 s.
- **Delivery.** Plate I's upload copy from its master: 71 MB, VMAF 96.4 (looks the same as the master).

Licences: the tools are open source (ffmpeg GPL build, Pedalboard GPL-3.0, Kokoro/misaki/sherpa-onnx Apache-2.0,
spaCy MIT); none of them puts terms on the films. Samples are CC0 except the Salamander piano (CC BY 3.0) and the
MuldjordKit drums (CC BY 4.0), which `S.credits()` writes into CREDITS when used.
