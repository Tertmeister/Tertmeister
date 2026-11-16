# What the Songs Don't Tell You (YouTube Short)

- `short.mp4`: 1080x1920, 30 fps, 52 s, H.264 + AAC. Ready to upload as a Short.
- `words.json`: word-timed transcript (Whisper, "seated" corrected to "seeded").
- `render.py`: renderer. `python3 render.py audio.mp3 words.json out.mp4` (needs ffmpeg, numpy, Pillow).
