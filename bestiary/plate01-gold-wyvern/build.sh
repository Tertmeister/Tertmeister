#!/bin/sh
# One-command build of A Bestiary of Azul · Plate I · The Gold Wyvern
# (Lemo-Opuscar, Copperplate Engraving, 1080x1920 @ 24 fps). Needs the library (core packages) and ffmpeg 7+.
# The narration in assets/ was made with Kokoro bm_george from script.txt, sped 5 % (pitch kept).
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
LIB=${LIB:-$HOME/lemo-opuscar}
export LIB
[ -f "$LIB/core/render/video.mjs" ] || { echo "set LIB to the Lemo-Opuscar library folder"; exit 1; }
PY="$LIB/.venv/bin/python"

"$PY" "$HERE/voice.py"                                     # narration lines on the film timeline → out/voice.wav, timeline.json
cd "$LIB"
node core/render/events.mjs "$HERE" --size 1080x1920        # window.EV → events.json
node core/render/video.mjs "$HERE" --fps 24 --size 1080x1920 --workers 3 --out "$HERE/out/video.mp4"
"$PY" "$HERE/mix.py"                                       # score + foley + room + voice → out/mix.wav
sh core/render/mux.sh "$HERE/out/video.mp4" "$HERE/out/mix.wav" "$HERE/out/short_master.mp4" 24 0
# distribution copy at YouTube's own quality ceiling (the master is very large)
ffmpeg -hide_banner -loglevel error -y -i "$HERE/out/short_master.mp4" -c:v libx264 -preset slow -crf 22 -maxrate 6M -bufsize 12M \
  -pix_fmt yuv420p -c:a copy -movflags +faststart "$HERE/short.mp4"
"$PY" - "$HERE" <<'EOF'
import json, sys
h = sys.argv[1]; tl = json.load(open(f"{h}/timeline.json")); L = tl["lines"]
cues = [{"t0": max(0, l["t0"] - 0.1), "t1": (L[i + 1]["t0"] - 0.1 if i + 1 < len(L) else l["t1"] + 0.6), "text": l["text"]} for i, l in enumerate(L)]
json.dump(cues, open(f"{h}/out/cues.json", "w"), indent=1)
EOF
"$PY" core/render/srt.py "$HERE/out/cues.json" "$HERE/subtitles_en.srt"
node core/render/still.mjs "$HERE" 139.5 --size 1080x1920 --out "$HERE/out/poster"
cp "$HERE/out/poster/t_139.5.jpg" "$HERE/poster.jpg"
echo "built $HERE/short.mp4"
