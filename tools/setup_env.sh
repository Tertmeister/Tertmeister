#!/bin/sh
# Azul production toolchain. Installs what is missing (finished steps are skipped), or reports with --check.
# Sources: GitHub releases (ffmpeg, Lemo-Opuscar, Kokoro, Parakeet, spaCy model) plus PyPI / npm packages.
# Paths: LIB=~/lemo-opuscar  AZUL_MODELS=~/models  AZUL_OPT=/opt  AZUL_BIN=/usr/local/bin. A failed step is
# reported and skipped, never fatal, so a session always starts; `sh tools/setup_env.sh --check` lists gaps.
H=${HOME:-/root}; LIB=${LIB:-$H/lemo-opuscar}; M=${AZUL_MODELS:-$H/models}; OPT=${AZUL_OPT:-/opt}
BIN=${AZUL_BIN:-/usr/local/bin}; INSTR=${AZUL_INSTRUMENTS-vsco2ce vcsl freepats}; LOG=${AZUL_LOG:-$H/.azul-setup.log}
for d in "$H/.local/bin" /opt/node22/bin /usr/local/bin; do [ -d "$d" ] && PATH="$d:$PATH"; done; export PATH
[ -z "$PLAYWRIGHT_BROWSERS_PATH" ] && [ -d /opt/pw-browsers ] && export PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers
PY=$LIB/.venv/bin/python; GH=https://github.com; CHECK=0; FAIL=""; [ "$1" = --check ] && CHECK=1
say() { echo "[azul] $*"; }
bad() { FAIL="$FAIL $1"; say "✗ $1: $2"; }
fetch() { curl -L --fail --retry 3 --retry-delay 2 --connect-timeout 20 -sS -o "$2" "$1"; }
sha() { [ "$(sha256sum "$1" 2>/dev/null | cut -d' ' -f1)" = "$2" ]; }
ffver() { "$1" -version 2>/dev/null | sed -n '1s/^ff[a-z]* version n\{0,1\}\([0-9][0-9]*\.[0-9]*\).*/\1/p'; }
major() { v=$(ffver "$1"); [ -n "$v" ] && [ "${v%%.*}" -ge 7 ]; }

# 1. ffmpeg + ffprobe (BtbN static GPL build; 8.1 while it is published, else the newest release line)
ff_ok() { major "$BIN/ffmpeg" && major "$BIN/ffprobe"; }
ff_get() {
  R=$GH/BtbN/FFmpeg-Builds/releases/download/latest; t=$(mktemp -d "$OPT/.azul-ff.XXXXXX") || return 1
  fetch "$R/checksums.sha256" "$t/sums" || { rm -rf "$t"; return 1; }
  f=$(grep -o 'ffmpeg-n8\.1-latest-linux64-gpl-8\.1\.tar\.xz' "$t/sums" | head -1)
  [ -n "$f" ] || f=$(grep -o 'ffmpeg-n[0-9]*\.[0-9]*-latest-linux64-gpl-[0-9.]*\.tar\.xz' "$t/sums" | sort -V | tail -1)
  [ -n "$f" ] && fetch "$R/$f" "$t/$f" && (cd "$t" && grep " $f\$" sums | sha256sum -c --quiet -) || { rm -rf "$t"; return 1; }
  v=${f##*-gpl-}; v=${v%.tar.xz}; mkdir "$t/x" && tar -xJf "$t/$f" -C "$t/x" --no-same-owner || { rm -rf "$t"; return 1; }
  rm -rf "$OPT/ffmpeg-$v" && mv "$t/x/${f%.tar.xz}" "$OPT/ffmpeg-$v" && rm -rf "$t" || return 1
  for b in ffmpeg ffprobe ffplay; do ln -sfn "$OPT/ffmpeg-$v/bin/$b" "$BIN/$b" || return 1; done
}

# 2. Lemo-Opuscar library with its core, voice (Kokoro v1.0) and music packages
lib_ok() { [ -f "$LIB/core/render/video.mjs" ] && [ -f "$LIB/node_modules/.lemo-ok" ] && [ -f "$LIB/.venv/.lemo-voice" ] &&
  [ -f "$LIB/.venv/.lemo-music" ] && [ -f "$LIB/core/tts/kokoro-v1.0.onnx" ]; }
lib_get() {
  if [ ! -d "$LIB" ]; then
    git clone --quiet --depth 1 --filter=blob:none --sparse --branch main "$GH/lemomo-ai/lemo-opuscar.git" "$LIB" || return 1
    (cd "$LIB" && git sparse-checkout set --no-cone '/*' '!/styles/*/demo/' '!/styleboard/' '!/docs/readme/' \
      '!/docs/cover.jpg' '!/styles/*/poster.jpg') && git -C "$LIB" config lemo.managed true || return 1
  fi
  LEMO_OPUSCAR_HOME="$LIB" sh "$LIB/plugin/skills/lemo-opuscar/scripts/setup.sh" deps voice music >>"$LOG" 2>&1
}

# 3. Sampled instruments (CC0 / CC BY, from the library's "assets" release; checksums checked by fetch.sh)
in_ok() { [ -d "$LIB/core/audio/instruments/$1" ] && [ ! -e "$LIB/.release/instruments-$1.tar.download" ]; }
in_get() { (cd "$LIB" && sh tools/fetch.sh instruments "$1" >>"$LOG" 2>&1); }

# 4. Python extras for tools/ (misaki without its PyTorch extra; spaCy's English model from its GitHub release; linters)
REQ="kokoro-onnx==0.6.1 sherpa-onnx==2.0.2 pedalboard==0.9.26 pyloudnorm==0.2.0 onnx==1.23.2 spacy==3.8.18 num2words==0.5.14 regex
ruff==0.17.6 shellcheck-py==0.11.0.1"
SPACY="en_core_web_sm @ $GH/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl"
pip_() { if command -v uv >/dev/null; then uv pip install --quiet --python "$PY" "$@"; else "$PY" -m pip install -q "$@"; fi; }
py_ok() { [ "$(cat "$LIB/.venv/.azul-tools" 2>/dev/null)" = "$REQ misaki==0.7.4" ] &&
  "$PY" -I -c 'import kokoro_onnx, misaki.en, sherpa_onnx, pedalboard, onnx, spacy; spacy.load("en_core_web_sm")' 2>/dev/null; }
py_get() { [ -x "$PY" ] && pip_ $REQ >>"$LOG" 2>&1 && pip_ --no-deps misaki==0.7.4 >>"$LOG" 2>&1 &&
  pip_ "$SPACY" >>"$LOG" 2>&1 && echo "$REQ misaki==0.7.4" > "$LIB/.venv/.azul-tools"; }

# 5. Kokoro v1.1 export (only its duration head is used: exact word timings) and the voices
K=$GH/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1
KS="kokoro-v1.0.onnx:beb0d1848dee9a49da392cc3df26958d46cfa35d321edf434f52949153f0df3a
voices-v1.0.bin:bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d"
ko_ok() { [ -f "$M/kokoro-v1.1/.ok" ] && [ -s "$M/kokoro-v1.1/voices-v1.0.bin" ] && [ -s "$M/kokoro-durations/durations.onnx" ]; }
ko_get() {
  d=$M/kokoro-v1.1; mkdir -p "$d" "$M/kokoro-durations" || return 1
  for e in $KS; do f=${e%%:*}; h=${e#*:}; sha "$d/$f" "$h" && continue
    fetch "$K/$f" "$d/$f.part" && sha "$d/$f.part" "$h" && mv "$d/$f.part" "$d/$f" || { rm -f "$d/$f.part"; return 1; }; done
  "$PY" -I -c 'import sys, onnx.utils as u; u.extract_model(sys.argv[1], sys.argv[2], ["input_ids", "style", "speed"],
    ["duration"], check_model=False)' "$d/kokoro-v1.0.onnx" "$M/kokoro-durations/durations.onnx" >>"$LOG" 2>&1 && touch "$d/.ok"
}

# 6. Parakeet TDT 0.6B v2 (NVIDIA, CC BY 4.0) in the sherpa-onnx export: speech check and word timings
PK=sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8; PKH=6fc4426b54aa549a0019b8a75b8dea59164e71790a37ac56a045ad57f915f714
pk_ok() { [ -s "$M/parakeet-tdt-0.6b-v2-int8/encoder.int8.onnx" ] && [ -s "$M/parakeet-tdt-0.6b-v2-int8/tokens.txt" ]; }
pk_get() {
  mkdir -p "$M" && t=$(mktemp -d "$M/.azul-pk.XXXXXX") || return 1
  fetch "$GH/k2-fsa/sherpa-onnx/releases/download/asr-models/$PK.tar.bz2" "$t/a" || { rm -rf "$t"; return 1; }
  sha "$t/a" "$PKH" || { say "Parakeet archive changed upstream: $(sha256sum "$t/a" | cut -c1-64)"; rm -rf "$t"; return 1; }
  mkdir "$t/x" && tar -xjf "$t/a" -C "$t/x" --no-same-owner && rm -rf "$t/x/$PK/test_wavs" "$M/parakeet-tdt-0.6b-v2-int8" &&
    mv "$t/x/$PK" "$M/parakeet-tdt-0.6b-v2-int8"; r=$?; rm -rf "$t"; return $r
}

step() {  # step NAME "CHECK [ARG]" "INSTALL [ARG]"
  if $2; then say "✓ $1"; elif [ $CHECK = 1 ]; then bad "$1" "missing"
  else say "… installing $1"; if $3 && $2; then say "✓ $1"; else bad "$1" "failed (log: $LOG)"; fi; fi
}
[ $CHECK = 1 ] || { mkdir -p "$M" "$OPT" "$BIN"; : >>"$LOG"; }
step "ffmpeg + ffprobe 7 or newer" ff_ok ff_get
step "Lemo-Opuscar library and packages ($LIB)" lib_ok lib_get
for l in $INSTR; do step "instruments: $l" "in_ok $l" "in_get $l"; done
step "Python extras (misaki, sherpa-onnx, pedalboard, spaCy model)" py_ok py_get
step "Kokoro v1.1 duration model + voices ($M)" ko_ok ko_get
step "Parakeet speech model ($M)" pk_ok pk_get
say "ffmpeg $(ffver "$BIN/ffmpeg"), ffprobe $(ffver "$BIN/ffprobe"), library $LIB, models $M"
if [ -z "$FAIL" ]; then say "toolchain ready: tools/az narrate | say | align | place | fx | deliver | lint | selftest"
else say "not ready:$FAIL  (run again: sh tools/setup_env.sh; details in $LOG)"; [ $CHECK = 1 ] && exit 1; fi
exit 0
