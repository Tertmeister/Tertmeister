# What the Songs Don't Tell You (YouTube Shorts series)

Each episode folder holds `short.mp4` (1080x1920, ready to upload), the script, word timings and a `config.json`.

## Making an episode
1. Narration: your own audio, or Kokoro TTS (free, Apache-2.0), voice `am_michael`, speed 1.0, now run locally:
   `tools/az narrate script.txt <episode>/assets --voice am_michael` (see `tools/README.md`). Check made-up names
   first with `--check` (no audio): it lists how every word outside the dictionary will be said.
2. Word timings: `az narrate` writes `words.json` itself. For your own recording:
   `tools/az align audio.mp3 --script script.txt --out words.json` (Parakeet), confirm the transcript it prints;
   the output uses the script's spelling (the captions use this text).
3. Too long? `python3 tighten.py narration.wav words.json tight.wav words_tight.json` shortens only the
   long pauses (speech untouched) and shifts the timings to match.
4. Mix: voice + `drone.py` music bed at -21 dB, light reverb, loudnorm -14 LUFS.
5. Render: `python3 render.py mix.wav words.json short.mp4 config.json`, then check it: `tools/az deliver --check short.mp4`

## `config.json`
- `episode`: subtitle under the series title.
- `emphasis`: words shown in red when spoken (uppercase, with their punctuation, e.g. `"DEAD."`).
- `scenes`: list of `[start_seconds, [r,g,b]]` colour moods (0.8 s crossfade).
- `fire`: time ranges with extra, faster embers.
- `rotations`: list of `[start_seconds, degrees]`; the background turns by that much over 0.8 s.
- `brightness`: list of `[seconds, factor]` keyframes, eased; 1 = normal, 0.2 = near black, 1.5 = bloom, 0 = black.
- `hold_last`: keep the final caption on screen until the video ends.
- `duration`: optional fixed length in seconds (default: audio length + 0.6 s).

## Episodes made with Lemo-Opuscar
Ep. 6 (`ep06-the-bifrost/`) is built with the Lemo-Opuscar plugin's **Halftone Dossier** style instead of
`render.py`: everything is drawn in code in its `index.html`, scored in `mix.py`, and `build.sh` rebuilds the
whole film (needs the library at `~/lemo-opuscar` with its core packages, and ffmpeg 7+). Its `TREATMENT.md`
has the shot list, beat sheet and cue map; `CREDITS` lists the fonts and tools.
