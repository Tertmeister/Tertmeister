"""Give a dry TTS narration a mic'd, finished sound (Spotify Pedalboard + ffmpeg's de-esser).

usage: az fx IN.wav OUT.wav [--preset narrator|study|crypt] [--deess] [--list]

Presets (each one is EQ -> compression -> optional room -> limiter; timing is untouched, so line spans and word
timings stay valid):
  narrator  close, dry and warm: rumble cut, a little body, less boxiness, presence for clarity. Use when the
            film's mix.py adds its own room.
  study     narrator + a small wood-panelled room (A Bestiary of Azul: the mage at a desk).
  crypt     darker and heavier with a long stone tail (What the Songs Don't Tell You).
--deess   tame harsh s sounds first (ffmpeg deesser).
Writes the same sample rate and length as IN (mono stays mono), peak-limited at -1 dBFS.
"""
import argparse, os, subprocess, sys, tempfile
import numpy as np
import soundfile as sf


# Pedalboard's Reverb is JUCE's: the dry signal is scaled by 2 (dry_level 0.5 = unity) and the wet level was
# measured on Kokoro narration (room 0.16: wet 0.2 = -18.5 dB; room 0.62: wet 0.23 = about -13 dB).
def chain(preset):
    from pedalboard import (Pedalboard, HighpassFilter, LowShelfFilter, PeakFilter, HighShelfFilter, Compressor,
                            Reverb, Limiter, Gain)
    eq = [HighpassFilter(cutoff_frequency_hz=75),
          LowShelfFilter(cutoff_frequency_hz=180, gain_db=1.5, q=0.7),
          PeakFilter(cutoff_frequency_hz=420, gain_db=-2.0, q=1.1),
          PeakFilter(cutoff_frequency_hz=3300, gain_db=2.0, q=0.9),
          HighShelfFilter(cutoff_frequency_hz=8500, gain_db=1.0, q=0.7)]
    comp = [Compressor(threshold_db=-20, ratio=2.5, attack_ms=6, release_ms=90), Gain(gain_db=2.0)]
    if preset == "narrator":
        room = []
    elif preset == "study":
        room = [Reverb(room_size=0.16, damping=0.65, wet_level=0.2, dry_level=0.5, width=0.6)]   # room ~18 dB under the voice
    elif preset == "crypt":
        eq[1] = LowShelfFilter(cutoff_frequency_hz=160, gain_db=2.5, q=0.7)
        eq[4] = HighShelfFilter(cutoff_frequency_hz=6500, gain_db=-2.0, q=0.7)
        room = [Reverb(room_size=0.62, damping=0.55, wet_level=0.23, dry_level=0.5, width=0.8)]  # tail ~13 dB under the voice
    else:
        sys.exit(f"fx: unknown preset {preset!r} (narrator, study, crypt)")
    return Pedalboard(eq + comp + room + [Limiter(threshold_db=-1.0, release_ms=60)])


def deess(path_in, path_out):
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", path_in,
                    "-af", "deesser=i=0.45:m=0.5:f=0.5:s=o", "-c:a", "pcm_f32le", path_out], check=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inp", nargs="?")
    ap.add_argument("out", nargs="?")
    ap.add_argument("--preset", default="narrator")
    ap.add_argument("--deess", action="store_true")
    ap.add_argument("--list", action="store_true")
    o = ap.parse_args()
    if o.list or not (o.inp and o.out):
        print(__doc__)
        return
    src = o.inp
    tmp = None
    if o.deess:
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
        deess(o.inp, tmp)
        src = tmp
    x, sr = sf.read(src, dtype="float32", always_2d=True)
    info = sf.info(o.inp)
    y = chain(o.preset)(x.T.copy(), sr).T
    if x.shape[1] == 1:
        y = y[:, :1]
    y = y[: len(x)]
    y = np.clip(y, -1, 1)
    sub = info.subtype if info.subtype in ("PCM_16", "PCM_24", "FLOAT") else "PCM_16"
    sf.write(o.out, y if y.shape[1] > 1 else y[:, 0], sr, subtype=sub)
    if tmp:
        os.unlink(tmp)
    rms = lambda a: 20 * np.log10(np.sqrt((a ** 2).mean()) + 1e-9)
    print(f"{o.out}: preset {o.preset}{' + de-ess' if o.deess else ''}, {len(y) / sr:.2f} s @ {sr} Hz, "
          f"RMS {rms(x):.1f} -> {rms(y):.1f} dBFS, peak {20 * np.log10(np.abs(y).max() + 1e-9):.1f} dBFS")


if __name__ == "__main__":
    main()
