#!/bin/sh
# One-command build of Ep. 6 · The Bifrost (Lemo-Opuscar, Halftone Dossier, 1080x1920 @ 30 fps).
# Needs the Lemo-Opuscar library (core packages) and ffmpeg 7+. The narration in assets/ was made with
# Kokoro (am_michael, speed 1.0) from script.txt; its line spans are in assets/narration_lines.json.
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
LIB=${LIB:-$HOME/lemo-opuscar}
export LIB
[ -f "$LIB/core/render/video.mjs" ] || { echo "set LIB to the Lemo-Opuscar library folder"; exit 1; }
PY="$LIB/.venv/bin/python"

"$PY" "$HERE/voice.py"                                     # narration lines on the film timeline → out/voice.wav, timeline.json
cd "$LIB"
node core/render/events.mjs "$HERE" --size 1080x1920        # window.EV → events.json
node core/render/video.mjs "$HERE" --fps 30 --size 1080x1920 --workers 3 --out "$HERE/out/video.mp4"
"$PY" "$HERE/mix.py"                                       # score + foley + ambience + voice → out/mix.wav
sh core/render/mux.sh "$HERE/out/video.mp4" "$HERE/out/mix.wav" "$HERE/out/short_master.mp4" 30 1
# distribution copy: the halftone and paper dust make the master ~125 MB; 6 Mbps is visually the same
ffmpeg -hide_banner -loglevel error -y -i "$HERE/out/short_master.mp4" -c:v libx264 -preset slow -crf 23 -maxrate 6M -bufsize 12M \
  -tune grain -pix_fmt yuv420p -c:a copy -movflags +faststart "$HERE/short.mp4"
"$PY" - "$HERE" <<'EOF'
import json, sys
h = sys.argv[1]; tl = json.load(open(f"{h}/timeline.json")); L = tl["lines"]
cues = [{"t0": l["t0"], "t1": (L[i + 1]["t0"] if i + 1 < len(L) else tl["dur"]), "text": l["text"]} for i, l in enumerate(L)]
json.dump(cues, open(f"{h}/out/cues.json", "w"), indent=1)
EOF
"$PY" core/render/srt.py "$HERE/out/cues.json" "$HERE/subtitles_en.srt"
node core/render/still.mjs "$HERE" 63.0 --size 1080x1920 --out "$HERE/out/poster"
cp "$HERE/out/poster/t_63.0.jpg" "$HERE/poster.jpg"
echo "built $HERE/short.mp4"
