# What the Songs Don't Tell You (YouTube Shorts series)

Each episode folder holds `short.mp4` (1080x1920, ready to upload), the script, word timings and a `config.json`.

## Making an episode
1. Narration: your own audio, or Kokoro TTS (free, Apache-2.0), voice `am_michael`, speed 1.0.
2. Word timings: faster-whisper with `word_timestamps=True` -> `words.json`.
3. Mix: voice + `drone.py` music bed at -21 dB, light reverb, loudnorm -14 LUFS.
4. Render: `python3 render.py mix.wav words.json short.mp4 config.json`

`config.json`: `episode` (subtitle under the series title), `emphasis` (words shown in red when spoken),
`scenes` (list of `[start_seconds, [r,g,b]]` colour moods), `fire` (time ranges with extra embers), optional `duration`.
