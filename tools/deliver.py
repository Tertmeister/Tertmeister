"""Make the upload copy of a finished film and check it before it goes anywhere.

usage: az deliver MASTER.mp4 OUT.mp4 [--crf 22] [--max-mb 95] [--vmaf] [--hevc]
       az deliver --check FILM.mp4                 (only the checks, no encode)

Encodes OUT from MASTER (x264 slow, CRF 22 capped at 6 Mbit/s as the episodes' build.sh does; the audio is copied
when it is already AAC). If OUT would be over --max-mb (GitHub refuses files over 100 MB) it is encoded again in
two passes at the bitrate that fits. Then checks: length under YouTube Shorts' 3 minutes, a 9:16 frame (1080x1920
recommended), frame rate, file size, loudness (-14 LUFS +-1, true peak <= -1 dBTP), 48 or 44.1 kHz audio and a moov atom
at the front (fast start). --vmaf scores OUT against MASTER with Netflix's VMAF (95+ looks the same as the master).
--hevc writes HEVC (x265, tagged hvc1 for Apple devices) instead: about the same quality in two thirds the size.
"""
import argparse, json, os, re, subprocess, sys


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def probe(path):
    r = run(["ffprobe", "-v", "error", "-show_entries",
             "format=duration,size:stream=codec_type,codec_name,width,height,r_frame_rate,sample_rate,channels,pix_fmt",
             "-of", "json", path])
    if r.returncode:
        sys.exit(f"deliver: ffprobe cannot read {path}: {r.stderr.strip()[-300:]}")
    j = json.loads(r.stdout)
    v = next((s for s in j["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in j["streams"] if s["codec_type"] == "audio"), None)
    return j["format"], v, a


def loudness(path):
    r = run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-map", "0:a:0", "-af", "ebur128=peak=true", "-f", "null", "-"])
    txt = r.stderr[r.stderr.rfind("Summary:"):]
    i = re.search(r"I:\s+(-?[\d.]+) LUFS", txt)
    tp = re.search(r"Peak:\s+(-?[\d.]+) dBFS", txt)
    return (float(i.group(1)) if i else None), (float(tp.group(1)) if tp else None)


def faststart(path):
    with open(path, "rb") as f:
        head = f.read(1 << 16)
    m, d = head.find(b"moov"), head.find(b"mdat")
    return m != -1 and (d == -1 or m < d)


def encode(master, out, crf, hevc, bitrate=None):
    _, _, a = probe(master)
    acodec = ["-c:a", "copy"] if a and a["codec_name"] == "aac" else ["-c:a", "aac", "-b:a", "192k", "-ar", "48000"]
    if hevc:
        v = ["-c:v", "libx265", "-preset", "slow", "-tag:v", "hvc1", "-x265-params", "log-level=error"]
    else:
        v = ["-c:v", "libx264", "-preset", "slow"]
    base = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", master] + v + ["-pix_fmt", "yuv420p"]
    if bitrate is None:
        cmd = base + ["-crf", str(crf + (2 if hevc else 0)), "-maxrate", "6M", "-bufsize", "12M"] + acodec + ["-movflags", "+faststart", out]
        r = run(cmd)
        if r.returncode:
            sys.exit(f"deliver: encode failed: {r.stderr.strip()[-400:]}")
        return
    log = out + ".2pass"
    p1 = base + ["-b:v", f"{bitrate}k", "-maxrate", f"{int(bitrate * 1.5)}k", "-bufsize", f"{bitrate * 2}k"]
    if hevc:
        p1 = [x if x != "log-level=error" else f"log-level=error:pass=1:stats={log}" for x in p1]
        p2 = [x if x != "log-level=error" else f"log-level=error:pass=2:stats={log}" for x in base] + p1[len(base):]
        steps = [p1 + ["-an", "-f", "null", os.devnull], p2 + acodec + ["-movflags", "+faststart", out]]
    else:
        steps = [p1 + ["-pass", "1", "-passlogfile", log, "-an", "-f", "null", os.devnull],
                 p1 + ["-pass", "2", "-passlogfile", log] + acodec + ["-movflags", "+faststart", out]]
    for cmd in steps:
        r = run(cmd)
        if r.returncode:
            sys.exit(f"deliver: two-pass encode failed: {r.stderr.strip()[-400:]}")
    for f in os.listdir(os.path.dirname(os.path.abspath(out))):
        if f.startswith(os.path.basename(log)):
            os.remove(os.path.join(os.path.dirname(os.path.abspath(out)), f))


def vmaf(dist, ref):
    th = str(os.cpu_count() or 2)
    graph = (f"[0:v]format=yuv420p,setpts=PTS-STARTPTS[d];[1:v]format=yuv420p,setpts=PTS-STARTPTS[r];"
             f"[d][r]libvmaf=n_subsample=6:n_threads={th}")
    r = run(["ffmpeg", "-hide_banner", "-nostats", "-i", dist, "-i", ref, "-lavfi", graph, "-f", "null", "-"])
    m = re.search(r"VMAF score:\s*([\d.]+)", r.stderr)
    return float(m.group(1)) if m else None


def check(path, max_mb):
    fmt, v, a = probe(path)
    dur, size = float(fmt["duration"]), int(fmt["size"]) / 1e6
    rows = []
    ok = lambda c: "✓" if c else "✗"
    rows.append((ok(dur <= 180), f"length {dur:.1f} s (Shorts: up to 3 min)"))
    if v:
        w, h = v["width"], v["height"]
        num, den = (int(x) for x in v["r_frame_rate"].split("/"))
        rows.append((ok(abs(w / h - 9 / 16) < 0.01), f"frame {w}x{h} ({'9:16' if abs(w / h - 9 / 16) < 0.01 else 'not 9:16'})"
                     + ("" if (w, h) == (1080, 1920) else ", 1080x1920 recommended")))
        rows.append(("✓", f"{num / den:.3g} fps, {v['codec_name']} {v.get('pix_fmt', '')}"))
    else:
        rows.append(("✗", "no video stream"))
    rows.append((ok(size <= max_mb), f"size {size:.1f} MB (limit {max_mb} MB for the repository)"))
    if a:
        i, tp = loudness(path)
        rows.append((ok(i is not None and abs(i + 14) <= 1), f"loudness {i} LUFS (target -14 +-1)"))
        rows.append((ok(tp is not None and tp <= -1.0), f"true peak {tp} dBTP (at most -1)"))
        rows.append((ok(a.get("sample_rate") in ("48000", "44100")), f"audio {a['codec_name']} {a.get('sample_rate')} Hz, {a.get('channels')} ch (YouTube: 48 or 44.1 kHz)"))
    else:
        rows.append(("✗", "no audio stream"))
    rows.append((ok(faststart(path)), "fast start (index at the front)"))
    for mark, text in rows:
        print(f"  {mark} {text}")
    return all(m == "✓" for m, _ in rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("master")
    ap.add_argument("out", nargs="?")
    ap.add_argument("--crf", type=int, default=22)
    ap.add_argument("--max-mb", type=float, default=95.0)
    ap.add_argument("--vmaf", action="store_true")
    ap.add_argument("--hevc", action="store_true")
    ap.add_argument("--check", action="store_true", help="only check MASTER, no encode")
    o = ap.parse_args()
    if o.check or not o.out:
        print(o.master)
        sys.exit(0 if check(o.master, o.max_mb) else 1)
    if os.path.abspath(o.master) == os.path.abspath(o.out):
        sys.exit("deliver: OUT must be a different file from MASTER")
    encode(o.master, o.out, o.crf, o.hevc)
    fmt, _, a = probe(o.out)
    size = int(fmt["size"]) / 1e6
    if size > o.max_mb:
        dur = float(fmt["duration"])
        akbps = 200 if a else 0
        kbps = int((o.max_mb * 8e3 * 0.97) / dur - akbps)
        print(f"{size:.1f} MB is over {o.max_mb} MB: encoding again in two passes at {kbps} kbit/s")
        encode(o.master, o.out, o.crf, o.hevc, bitrate=kbps)
    print(o.out)
    good = check(o.out, o.max_mb)
    if o.vmaf:
        s = vmaf(o.out, o.master)
        print(f"  {'✓' if s and s >= 93 else '!'} VMAF {s:.1f} against the master (95+ looks the same)" if s else "  ! VMAF could not be measured")
    sys.exit(0 if good else 1)


if __name__ == "__main__":
    main()
