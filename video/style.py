#!/usr/bin/env python3
"""Shared drawing helpers for both videos: palette, fonts, easing, panels, the judging-criteria rail,
the animated memory background, and render() (frames piped to ffmpeg, one mp4 per scene)."""
import math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1920, 1080, 30
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))          # repository root
OUT = os.environ.get("VIDEO_BUILD", os.path.join(ROOT, "video", "build"))     # one mp4 per scene
os.makedirs(OUT, exist_ok=True)
FD = os.environ.get("INTER_DIR", "/usr/share/fonts/opentype/inter/")       # Inter + Inter Display (fonts-inter)
def F(name, size): return ImageFont.truetype(FD + name, size)
def M(size, bold=False):
    return ImageFont.truetype(os.environ.get("MONO_PREFIX", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono") + ("-Bold" if bold else "") + ".ttf", size)

BG = (255, 255, 255); PANEL = (246, 247, 249); LINE = (226, 229, 234)
FG = (17, 24, 39); MUTED = (100, 108, 122); DIM = (205, 210, 217); TRACK = (236, 238, 242)
RED = (220, 38, 38); GREEN = (22, 150, 70); RED_L = (254, 226, 226); GREEN_L = (220, 245, 228)
ACC = (37, 99, 235); ACC_L = (232, 240, 254); BLUE = (60, 90, 170)

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(x): x = clamp(x); return 1 - (1 - x) ** 3
def ramp(t, t0, dur=0.5): return ease((t - t0) / dur)
def mix(c, a): return tuple(int(v) for v in c) + (int(255 * clamp(a)),)
def fade(t, dur, fin=0.35, fout=0.35): return clamp(min(t / fin, (dur - t) / fout))
def text(d, xy, s, font, fill, a=1.0, anchor="la"): d.text(xy, s, font=font, fill=mix(fill, a), anchor=anchor)

# ---------------------------------------------------------------- light core-memory animation
COLS, ROWS, CELL = 96, 54, 20
N = COLS * ROWS
tA = np.full(N, np.inf); tB = np.full(N, np.inf)
for k in range(1400):
    p = (k * 1237) % N; tA[p] = min(tA[p], 0.15 + k * 0.0042)
seeds = [(4000, 0.0)]
for g in range(9):
    new = []
    for (s, t0) in seeds:
        for j in range(9): tB[(s + j) % N] = min(tB[(s + j) % N], t0 + j * 0.02)
        new.append(((s + 2741 * (g + 1) + 377 * len(new)) % N, t0 + 0.55))
    seeds = seeds + new

def core_bg(t, strength=1.0):
    base = np.array([238, 240, 243], float)
    col = np.tile(base, (N, 1))
    a = tA <= t; b = tB <= t
    col[b] = (198, 210, 238); col[a] = (247, 178, 178)
    col[(tA <= t) & (tA > t - 0.12)] = RED; col[(tB <= t) & (tB > t - 0.12)] = BLUE
    col = 255 + (col - 255) * strength
    img = np.repeat(np.repeat(col.reshape(ROWS, COLS, 3), CELL, 0), CELL, 1)
    m = np.ones((CELL, CELL), bool); m[16:, :] = False; m[:, 16:] = False
    out = np.where(np.tile(m, (ROWS, COLS))[..., None], img, 255.0)
    return Image.fromarray(out.astype(np.uint8), "RGB")

# ---------------------------------------------------------------- frame helpers
CRIT = [("gap", "Gap", "30"), ("diff", "Meaningful difficulty", "30"), ("integ", "Reward integrity", "25"),
        ("craft", "Craft", "15"), ("tie", "Tiebreaker", "training")]

def rail(d, active, a=1.0):
    y0, y1 = 1000, 1052
    d.line((120, 978, 1800, 978), fill=mix(LINE, a), width=2)
    text(d, (120, (y0 + y1) / 2), "JUDGING CRITERIA", F("Inter-Bold.otf", 20), MUTED, a, "lm")
    x = 330
    for key, name, pts in CRIT:
        on = key in active
        s = f"{name}  {pts}"
        f = F("Inter-Bold.otf" if on else "Inter-SemiBold.otf", 24)
        w = d.textlength(s, font=f) + 48
        if on:
            d.rounded_rectangle((x, y0, x + w, y1), 26, fill=mix(ACC, a))
            text(d, (x + w / 2, (y0 + y1) / 2), s, f, BG, a, "mm")
        else:
            d.rounded_rectangle((x, y0, x + w, y1), 26, outline=mix(DIM, a), width=2)
            text(d, (x + w / 2, (y0 + y1) / 2), s, f, MUTED, a, "mm")
        x += w + 16

def panel(d, box, a=1.0, fill=PANEL, outline=LINE, r=20, width=2):
    d.rounded_rectangle(box, r, fill=mix(fill, a), outline=mix(outline, a), width=width)

def head(d, t, kicker, title, k):
    a = ramp(t, 0.0, 0.45) * k
    text(d, (120, 92), kicker, F("Inter-Bold.otf", 30), ACC, a)
    text(d, (120, 132), title, F("InterDisplay-Black.otf", 80), FG, a)

def base(t, dur, active):
    img = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(img, "RGBA")
    rail(d, active)
    return img, d, fade(t, dur)

def tick(d, x, y, a, c=ACC):
    d.ellipse((x, y, x + 44, y + 44), fill=mix(c, a))
    d.line((x + 11, y + 23, x + 19, y + 32, x + 33, y + 13), fill=mix(BG, a), width=6, joint="curve")

def cross(d, x, y, a, c=RED):
    d.ellipse((x, y, x + 44, y + 44), fill=mix(c, a))
    d.line((x + 14, y + 14, x + 30, y + 30), fill=mix(BG, a), width=6)
    d.line((x + 30, y + 14, x + 14, y + 30), fill=mix(BG, a), width=6)

def arrow(d, p, q, c, a, width=6, head=24, shrink=0):
    (x0, y0), (x1, y1) = p, q
    ang = math.atan2(y1 - y0, x1 - x0)
    x0 += math.cos(ang) * shrink; y0 += math.sin(ang) * shrink
    x1 -= math.cos(ang) * shrink; y1 -= math.sin(ang) * shrink
    d.line((x0, y0, x1, y1), fill=mix(c, a), width=width)
    for s in (+1, -1):
        d.line((x1, y1, x1 - head * math.cos(ang + s * 0.45), y1 - head * math.sin(ang + s * 0.45)), fill=mix(c, a), width=width)

def hbar(d, t, x0, x1, y, h, v, c, t0, label, val, lab_font=34, val_font=38, lab_col=FG):
    a = ramp(t, t0); g = ramp(t, t0 + 0.2, 1.1)
    text(d, (x0 - 28, y + h / 2), label, F("Inter-Bold.otf", lab_font), lab_col, a, "rm")
    d.rounded_rectangle((x0, y, x1, y + h), 12, fill=mix(TRACK, a))
    wv = (x1 - x0) * v * g
    if wv > 2: d.rounded_rectangle((x0, y, x0 + wv, y + h), 12, fill=mix(c, a))
    text(d, (x0 + wv + 18, y + h / 2), val(g), F("Inter-Black.otf", val_font), MUTED if c == DIM else c, a, "lm")
    return a


DWARF = [("start  add.ab #4, bmb", "move 4 cells ahead"), ("       mov.i  bmb, @bmb", "drop a bomb there"),
         ("       jmp    start", "repeat"), ("bmb    dat    #0, #0", "the bomb")]

def render(name, fn, dur):
    tmp = os.path.join(OUT, f"{name}.tmp.mp4"); dst = os.path.join(OUT, f"{name}.mp4")
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast",
                          "-crf", "18", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for i in range(int(round(dur * FPS))):
        p.stdin.write(fn(i / FPS, dur).convert("RGB").tobytes())
    p.stdin.close()
    if p.wait() == 0: os.replace(tmp, dst)
    else: sys.exit(f"ffmpeg failed on {name}")
