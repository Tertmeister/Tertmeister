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
2. Narration: `tools/az narrate script.txt assets --voice bm_george` (local Kokoro, word timings included; see
   `tools/README.md`). Plate I was narrated in the Higgsfield sandbox, with faster-whisper timings.
3. `voice.py` places the lines (≥ 0.6 s between lines for the subtitle slip); for a new plate `tools/az place assets .
   --open 0.9 --gap 0.6 --tail 4` does the same.
4. `TREATMENT.md` (structures, shot list, beat sheet, cue map) before drawing.
5. `figures.js` draws the subjects; `film.js` holds the timeline, camera, roundels, lettering and events.
6. `build.sh` renders, scores (`mix.py`, which can use the library's sampled instruments), masters (ffmpeg 7+), writes
   the subtitles and the poster; `tools/az deliver out/short_master.mp4 short.mp4 --vmaf` makes and checks the upload copy.

Each plate folder carries its `CREDITS`; the engraving engine in `engine/` is MIT-licensed library code.
