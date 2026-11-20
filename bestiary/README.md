# A Bestiary of Azul (YouTube Shorts series)

A mage-naturalist's field notes on the creatures and ecology of Azul, one engraved plate per episode.
Each episode is built with the Lemo-Opuscar plugin's **Copperplate Engraving** style: a portrait plate
(1080×1920, 24 fps) that engraves itself while the narrator teaches, magnification roundels for the parts that
matter, hand-laid colour only on the part being taught, and the finished plate as the last shot.

| Plate | Folder | Subject |
|---|---|---|
| I | `plate01-gold-wyvern/` | The Gold Wyvern (*Dracunculus fulgur*) |

## Making a plate
1. Script → user approval (repo `CLAUDE.md`, rule 1).
2. Narration: Kokoro `bm_george` (generated in the Higgsfield sandbox), word timings with faster-whisper.
3. `voice.py` places the lines (≥ 0.6 s between lines for the subtitle slip).
4. `TREATMENT.md` (structures, shot list, beat sheet, cue map) before drawing.
5. `figures.js` draws the subjects; `film.js` holds the timeline, camera, roundels, lettering and events.
6. `build.sh` renders, scores (`mix.py`), masters (ffmpeg 7+), writes the subtitles and the poster.

Each plate folder carries its `CREDITS`; the engraving engine in `engine/` is MIT-licensed library code.
