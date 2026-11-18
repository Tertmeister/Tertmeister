import json, subprocess, sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

AUDIO, WORDS, OUT, CFG = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
cfg = json.load(open(CFG))
W, H, FPS = 1080, 1920, 30
HW, HH = W // 2, H // 2
_alen = float(subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',AUDIO],capture_output=True,text=True).stdout)
DUR = cfg.get('duration', round(_alen + 0.6, 2))
NF = int(DUR * FPS)
rng = np.random.default_rng(7)

# ---------- audio envelope ----------
pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", AUDIO, "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                     capture_output=True, check=True).stdout
a = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768
spf = 16000 // FPS
env = np.array([np.sqrt(np.mean(a[i*spf:(i+1)*spf]**2)) if i*spf < len(a) else 0 for i in range(NF)])
env = env / (np.percentile(env, 98) + 1e-6)
env = np.clip(np.convolve(env, np.ones(4)/4, "same"), 0, 1.2)

# ---------- words & chunks ----------
words = [(s, e, t.strip()) for s, e, t in json.load(open(WORDS))]
EMPH = {e.upper() for e in cfg["emphasis"]}
LAST = words[-1][1]
chunks, cur = [], []
for w in words:
    cur.append(w)
    txt = " ".join(x[2] for x in cur)
    if w[2][-1] in ".,?!" or len(cur) >= 3 or len(txt) >= 15:
        chunks.append(cur); cur = []
if cur: chunks.append(cur)
spans = []
for i, c in enumerate(chunks):
    st = c[0][0]
    nxt = chunks[i+1][0][0] if i + 1 < len(chunks) else DUR
    en = min(nxt, c[-1][1] + 0.7)
    if i + 1 == len(chunks) and cfg.get("hold_last"):
        en = DUR  # keep the final words on screen until the video ends
    spans.append((st, en, c))

# ---------- scene tints (time, rgb) ----------
KEYS = []
for i, (st, c) in enumerate(cfg["scenes"]):  # [start_time, [r,g,b]], 0.8s crossfade into each
    if i: KEYS.append((st - 0.4, KEYS[-1][1]))
    KEYS.append((st + (0.4 if i else 0), tuple(c)))
KEYS.append((DUR, KEYS[-1][1]))
def tint(t):
    for (t0, c0), (t1, c1) in zip(KEYS, KEYS[1:]):
        if t0 <= t <= t1:
            k = (t - t0) / max(t1 - t0, 1e-6); k = k*k*(3-2*k)
            return np.array(c0) * (1-k) + np.array(c1) * k
    return np.array(KEYS[-1][1])

# ---------- background brightness (cfg "brightness": [[time, factor], ...], eased between keys; default 1) ----------
BKEYS = sorted(cfg.get("brightness", []))
def bright(t):
    if not BKEYS: return 1.0
    if t <= BKEYS[0][0]: return BKEYS[0][1]
    for (t0, b0), (t1, b1) in zip(BKEYS, BKEYS[1:]):
        if t0 <= t <= t1:
            k = (t - t0) / max(t1 - t0, 1e-6); k = k*k*(3-2*k)
            return b0 * (1-k) + b1 * k
    return BKEYS[-1][1]

# ---------- background rotation (cfg "rotations": [[start_time, degrees], ...], 0.8 s eased) ----------
def rotate_bg(im, t):
    ang = 0.0
    for ts, deg in cfg.get("rotations", []):
        k = min(1.0, max(0.0, (t - ts) / 0.8)); k = k * k * (3 - 2 * k)
        ang += deg * k
    a = ang % 360
    if a < 1e-3 or a > 360 - 1e-3: return im
    if abs(a - 180) < 1e-3: return im.transpose(Image.ROTATE_180)
    r = math.radians(a); c, s_ = abs(math.cos(r)), abs(math.sin(r))
    sc = max((HW * c + HH * s_) / HW, (HW * s_ + HH * c) / HH)  # zoom so the rotated frame stays covered
    big = im.resize((int(HW * sc) + 2, int(HH * sc) + 2), Image.BILINEAR).rotate(a, resample=Image.BILINEAR)
    l = (big.width - HW) // 2; tp = (big.height - HH) // 2
    return big.crop((l, tp, l + HW, tp + HH))

# ---------- fog textures ----------
def noise(h, w, scale):
    small = rng.random((h // scale + 2, w // scale + 2)).astype(np.float32)
    img = Image.fromarray((small * 255).astype(np.uint8)).resize((w + 2*scale, h + 2*scale), Image.BICUBIC)
    img = img.filter(ImageFilter.GaussianBlur(scale / 2)).crop((scale, scale, w + scale, h + scale))
    return np.asarray(img, np.float32) / 255
FH = HH * 2
fogA = noise(FH, HW, 60); fogB = noise(FH, HW, 25)
for f in (fogA, fogB):
    f -= f.min(); f /= f.max()
fogA = np.vstack([fogA, fogA[::-1]]); fogB = np.vstack([fogB, fogB[::-1]])  # seamless vertical loop

yy, xx = np.mgrid[0:HH, 0:HW].astype(np.float32)
vig = 1 - 0.85 * np.clip(((xx/HW - .5)**2 * 1.6 + (yy/HH - .55)**2 * 1.1) * 2.2, 0, 1)
grad = (0.35 + 0.65 * (yy / HH))  # brighter toward bottom (firelight)

# ---------- embers ----------
NP = 140
px = rng.random(NP) * HW; py = rng.random(NP) * HH
pv = 15 + rng.random(NP) * 45; ps = rng.random(NP) * 6.28; pz = 0.4 + rng.random(NP)
sprite_r = 6
sy, sx = np.mgrid[-sprite_r:sprite_r+1, -sprite_r:sprite_r+1]
sprite = np.exp(-(sx**2 + sy**2) / 5.0).astype(np.float32)

# ---------- fonts ----------
F_CAP = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
F_SER = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
cap_font = ImageFont.truetype(F_CAP, 104)
title_font = ImageFont.truetype(F_SER, 40)
sub_font = ImageFont.truetype(F_SER, 28)

def spaced(draw, y, text, font, fill, spacing):
    widths = [draw.textlength(ch, font=font) for ch in text]
    total = sum(widths) + spacing * (len(text) - 1)
    x = (W - total) / 2
    for ch, w in zip(text, widths):
        draw.text((x, y), ch, font=font, fill=fill); x += w + spacing

title_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
td = ImageDraw.Draw(title_layer)
spaced(td, 150, "WHAT THE SONGS", title_font, (235, 205, 150, 235), 10)
spaced(td, 200, "DON'T TELL YOU", title_font, (235, 205, 150, 235), 10)
td.line([(W/2 - 120, 268), (W/2 + 120, 268)], fill=(200, 140, 70, 180), width=2)
if cfg.get("episode"): spaced(td, 290, cfg["episode"].upper(), sub_font, (210, 120, 80, 220), 6)
title_glow = title_layer.filter(ImageFilter.GaussianBlur(10))

cache = {}
def chunk_img(ci, active_idx):
    key = (ci, active_idx)
    if key in cache: return cache[key]
    c = spans[ci][2]
    toks = [w[2].upper() for w in c]
    d = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    sp = d.textlength(" ", font=cap_font)
    lines, line, lw = [], [], 0
    for i, t in enumerate(toks):
        tw = d.textlength(t, font=cap_font)
        if line and lw + sp + tw > 940:
            lines.append(line); line, lw = [], 0
        line.append((i, t, tw)); lw += (sp if len(line) > 1 else 0) + tw
    lines.append(line)
    lh = 124
    img = Image.new("RGBA", (W, lh * len(lines) + 60), (0, 0, 0, 0))
    dr = ImageDraw.Draw(img)
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0)); gd = ImageDraw.Draw(glow)
    for li, ln in enumerate(lines):
        total = sum(x[2] for x in ln) + sp * (len(ln) - 1)
        x = (W - total) / 2; y = 30 + li * lh
        for i, t, tw in ln:
            if i == active_idx:
                col = (255, 70, 50) if t in EMPH else (255, 196, 80)
                gd.text((x, y), t, font=cap_font, fill=col + (255,))
            elif i < active_idx:
                col = (245, 238, 225)
            else:
                col = (200, 195, 185)
            if i == active_idx:
                pass
            dr.text((x, y), t, font=cap_font, fill=col + (255,) if i != active_idx else col + (255,),
                    stroke_width=9, stroke_fill=(10, 6, 4, 255))
            x += tw + sp
    glow = glow.filter(ImageFilter.GaussianBlur(18))
    out = Image.alpha_composite(glow, img)
    cache[key] = out
    return out

ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                       "-r", str(FPS), "-i", "-", "-i", AUDIO, "-filter_complex",
                       "[1:a]apad,atrim=0:%f,afade=t=out:st=%f:d=0.8[a]" % (DUR, DUR - 0.9),
                       "-map", "0:v", "-map", "[a]", "-c:v", "libx264", "-preset", "slow", "-crf", "21",
                       "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", OUT],
                      stdin=subprocess.PIPE)

for f in range(NF):
    t = f / FPS
    e = env[f]
    col = tint(t) / 255.0
    oa = int(t * 18) % FH; ob = int(t * 40) % FH
    fog = 0.55 * fogA[oa:oa+HH] + 0.45 * fogB[ob:ob+HH]
    fog = np.clip((fog - 0.25) * 1.6, 0, 1)
    lum = (0.10 + 0.55 * fog * grad) * vig * (0.85 + 0.25 * e)
    frame = lum[..., None] * col[None, None, :] * 2.2
    # embers
    fire = 1.6 if any(a_ <= t < b_ for a_, b_ in cfg.get('fire', [])) else 1.0
    glowmap = np.zeros((HH, HW), np.float32)
    yspd = pv * pz * fire
    cy = (py - yspd * t) % (HH + 20) - 10
    cx = (px + 18 * np.sin(t * 0.8 + ps) * pz) % HW
    br = (0.5 + 0.5 * np.sin(t * 6 + ps * 3)) * pz * 0.9
    for x, y, b in zip(cx.astype(int), cy.astype(int), br):
        x0, y0 = x - sprite_r, y - sprite_r
        if x0 < 0 or y0 < 0 or x0 + 2*sprite_r + 1 > HW or y0 + 2*sprite_r + 1 > HH: continue
        glowmap[y0:y0+2*sprite_r+1, x0:x0+2*sprite_r+1] += sprite * b
    frame += glowmap[..., None] * np.array([1.0, 0.55, 0.18])[None, None, :]
    frame += rng.normal(0, 0.008, (HH, HW, 1)).astype(np.float32)  # grain
    # fade in/out
    fade = min(1, t / 0.4) * min(1, max(0, (DUR - t) / 0.9))
    frame = np.clip(frame * fade * bright(t), 0, 1)
    img = rotate_bg(Image.fromarray((frame * 255).astype(np.uint8)), t).resize((W, H), Image.BILINEAR).convert("RGBA")

    # title
    img.alpha_composite(title_glow); img.alpha_composite(title_layer)

    # captions
    for ci, (st, en, c) in enumerate(spans):
        if st <= t < en:
            ai = -1
            for i, w in enumerate(c):
                if t >= w[0]: ai = i
            ci_img = chunk_img(ci, ai)
            age = t - st
            s = 1.0 if age > 0.14 else 0.82 + 0.18 * (1 - (1 - age / 0.14) ** 3) + 0.04 * math.sin(age / 0.14 * math.pi)
            alpha = min(1, age / 0.08) * min(1, (en - t) / 0.12)
            if abs(s - 1) > 1e-3:
                ci_img = ci_img.resize((int(ci_img.width * s), int(ci_img.height * s)), Image.BILINEAR)
            if alpha < 1:
                ci_img = ci_img.copy(); a_ = ci_img.getchannel("A").point(lambda v: int(v * alpha)); ci_img.putalpha(a_)
            img.alpha_composite(ci_img, ((W - ci_img.width) // 2, 1180 - ci_img.height // 2))
            break

    # progress bar
    d = ImageDraw.Draw(img)
    d.rectangle([80, 1760, W - 80, 1766], fill=(70, 58, 48))
    d.rectangle([80, 1760, 80 + int((W - 160) * min(1, t / LAST)), 1766], fill=(255, 180, 80, 220))

    ff.stdin.write(img.convert("RGB").tobytes())
    if f % 150 == 0: print(f"{f}/{NF}", flush=True)

ff.stdin.close(); ff.wait()
print("done", ff.returncode)
