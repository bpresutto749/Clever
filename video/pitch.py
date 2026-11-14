#!/usr/bin/env python3
"""The combined video (about 6 minutes): the presentation's structure, with the demo's real run
woven into it. 1 the test we need, 2 the game, 3 how the test works, 4 what we found (all five runs,
then run C5 replayed, then one real game), then trust, training and the close.
Scenes taken from explainer.py and demo.py are redrawn here in the presentation's frame
(header, judging-criteria rail), with the same numbers.
usage: python video/pitch.py [all | <scene name>]   -> video/build/<scene>.mp4"""
import sys
import numpy as np
from PIL import Image, ImageDraw
from style import (W, H, F, M, BG, PANEL, LINE, FG, MUTED, DIM, TRACK, RED, GREEN, RED_L, GREEN_L, ACC, ACC_L,
                   clamp, ramp, mix, fade, text, panel, arrow, render, base, core_bg)
import style
import explainer as ex
import demo as dm

# the presentation's part 3 now also explains the test's mechanics
def head(d, t, kicker, title, k):
    style.head(d, t, kicker.replace("3 · WHY IT WORKS", "3 · HOW THE TEST WORKS"), title, k)
ex.head = head
P3, P4 = "3 · HOW THE TEST WORKS", "4 · WHAT WE FOUND"
BLUE_T = (60, 84, 150)

# ---------------------------------------------------------------- opening and part 2, adjusted
def s_question(t, dur):
    img, d, k = base(t, dur, set())
    a = ramp(t, 0.3, 0.8) * k
    text(d, (W / 2, 250), "THE QUESTION", F("Inter-Bold.otf", 30), ACC, a, "mm")
    text(d, (W / 2, 370), "Can AI coding agents match", F("InterDisplay-Black.otf", 76), FG, a, "mm")
    text(d, (W / 2, 465), "human experts at real design work?", F("InterDisplay-Black.otf", 76), FG, a, "mm")
    text(d, (W / 2, 580), "Not a quiz, and not brute force: real design, against opponents it never sees.",
         F("Inter-Medium.otf", 36), MUTED, ramp(t, 1.8, 0.8) * k, "mm")
    steps = ["The test we need", "The game", "How the test works", "What we found"]
    fnt = F("Inter-Bold.otf", 34)
    widths = [76 + d.textlength(s, font=fnt) for s in steps]
    x = (W - sum(widths) - 3 * 80) / 2
    for i, s in enumerate(steps):
        aa = ramp(t, 3.2 + i * 0.7, 0.6) * k
        d.ellipse((x, 700, x + 58, 758), fill=mix(ACC, aa))
        text(d, (x + 29, 729), str(i + 1), F("Inter-Black.otf", 30), BG, aa, "mm")
        text(d, (x + 76, 729), s, fnt, FG, aa, "lm")
        x += widths[i] + 80
    return img

def s_game(t, dur):
    img, d, k = base(t, dur, set())
    head(d, t, "2 · THE GAME: CORE WAR", "A game where programs fight", k)
    rows = [("Two programs share one", 0), ("memory of 8,000 cells.", 0), ("They take turns.", 1),
            ("Each tries to crash", 2), ("the other.", 2)]
    for (s, g), y in zip(rows, [330, 390, 480, 570, 630]):
        text(d, (120, y), s, F("Inter-SemiBold.otf", 48), FG, ramp(t, 0.8 + g * 1.4, 0.7) * k)
    if t > 5.2:
        text(d, (120, 740), "The last one running wins.", F("InterDisplay-Black.otf", 54), ACC, ramp(t, 5.2, 0.7) * k)
        text(d, (120, 815), "Both still running at the time limit: a draw.", F("Inter-Medium.otf", 34), MUTED, ramp(t, 6.2, 0.7) * k)
    pa = ramp(t, 0.6, 0.8) * k
    if pa > 0:
        core = core_bg(t * 0.55, 1.0).resize((820, 462), Image.BILINEAR)
        img.paste(core, (980, 320), Image.new("L", core.size, int(255 * pa)))
        d.rounded_rectangle((976, 316, 1804, 786), 14, outline=mix(LINE, pa), width=3)
        text(d, (980, 300), "the shared memory, live", F("Inter-SemiBold.otf", 24), MUTED, pa, "ls")
        for j, (c, lab) in enumerate(((RED, "program A drops bombs"), (style.BLUE, "program B copies itself"))):
            d.rounded_rectangle((980 + j * 410, 812, 1004 + j * 410, 836), 5, fill=mix(c, pa))
            text(d, (1016 + j * 410, 824), lab, F("Inter-SemiBold.otf", 26), FG, pa, "lm")
    return img

# ---------------------------------------------------------------- part 3: the test, concretely (from the demo)
def s_test(t, dur):
    img, d, k = base(t, dur, {"diff", "integ"})
    head(d, t, P3, "What the AI has to do", k)
    text(d, (120, 290), "The AI writes one program. That program then takes the test:", F("Inter-SemiBold.otf", 32), FG, ramp(t, 0.5, 0.6) * k)
    a1 = ramp(t, 1.2, 0.7) * k
    panel(d, (120, 350, 520, 490), a1, fill=RED_L, outline=RED, r=18)
    text(d, (320, 420), "the AI's program", F("Inter-Bold.otf", 34), RED, a1, "mm")
    a2 = ramp(t, 1.8, 0.7) * k
    arrow(d, (540, 420), (660, 420), MUTED, a2, width=6)
    text(d, (600, 378), "plays", F("Inter-SemiBold.otf", 24), MUTED, a2, "mm")
    for i in range(30):
        r, c = divmod(i, 10)
        x, y = 690 + c * 108, 345 + r * 50
        aa = ramp(t, 2.0 + i * 0.04, 0.4) * k
        d.rounded_rectangle((x, y, x + 96, y + 42), 10, fill=mix((222, 229, 244), aa), outline=mix((90, 112, 170), aa), width=2)
        text(d, (x + 48, y + 21), "?", F("Inter-Bold.otf", 22), (90, 112, 170), aa, "mm")
    text(d, (1230, 520), "30 secret opponents, 500 games against each", F("Inter-Bold.otf", 28), BLUE_T, ramp(t, 3.0) * k, "mm")
    if t > 3.8:
        aa = ramp(t, 3.8, 0.6) * k
        text(d, (120, 575), "Each game:  win = 3 points,  draw = 1,  loss = 0.", F("Inter-Bold.otf", 38), FG, aa)
        text(d, (120, 630), "So the game score = points won ÷ points possible, from 0 to 1.", F("Inter-SemiBold.otf", 32), MUTED, aa)
    if t > 6.0:
        aa = ramp(t, 6.0, 0.6) * k
        panel(d, (120, 700, 1800, 935), aa, fill=GREEN_L, outline=GREEN, r=18)
        text(d, (160, 748), "For comparison, a human expert's program takes exactly the same test.", F("Inter-Bold.otf", 34), GREEN, aa, "lm")
        text(d, (160, 805), "“Toxic”, by John Metcalf: rated #1 of 264 human-written programs (Elo, CodeClash ladder).", F("Inter-SemiBold.otf", 29), FG, aa, "lm")
        text(d, (160, 865), "Its game score: 0.487. Against opponents this strong, about 0.5 is top level.", F("Inter-SemiBold.otf", 29), FG,
             ramp(t, 7.4, 0.6) * k, "lm")
    return img

def s_rules(t, dur):
    img, d, k = base(t, dur, {"diff"})
    head(d, t, P3, "To prepare: 45 minutes and practice", k)
    steps = [("1", "It writes a program", "a small text file in Redcode, the game's assembly language"),
             ("2", "It practises", "against 30 practice opponents, and gets a practice score"),
             ("3", "It submits", "as often as it wants; only the last submission counts"),
             ("4", "It decides when to stop", "every reply from its tools shows a clock with the minutes left")]
    for i, (n, h, sub) in enumerate(steps):
        a = ramp(t, 0.8 + i * 1.3, 0.7) * k
        y = 280 + i * 136
        panel(d, (120, y, 1800, y + 118), a, r=18)
        d.ellipse((150, y + 29, 210, y + 89), fill=mix(FG, a))
        text(d, (180, y + 59), n, F("Inter-Black.otf", 30), BG, a, "mm")
        text(d, (240, y + 40), h, F("Inter-Bold.otf", 38), FG, a, "lm")
        text(d, (240, y + 88), sub, F("Inter-Medium.otf", 30), MUTED, a, "lm")
    if t > 6.4:
        aa = ramp(t, 6.4, 0.7) * k
        panel(d, (120, 832, 1800, 950), aa, fill=RED_L, outline=RED, r=18)
        text(d, (W / 2, 870), "But the practice opponents are not the secret ones.", F("Inter-Bold.otf", 36), RED, aa, "mm")
        text(d, (W / 2, 920), "Only at the end does a referee program run the real test. The AI never sees that score.",
             F("Inter-SemiBold.otf", 28), FG, ramp(t, 7.4, 0.6) * k, "mm")
    return img

# ---------------------------------------------------------------- part 4: all five runs, then run C5
def s_term(t, dur):
    img, d, k = base(t, dur, {"craft"})
    head(d, t, P4, "Five runs of the same AI, one command", k)
    a = ramp(t, 0.3) * k
    panel(d, (120, 290, 1800, 620), a, fill=(250, 250, 251))
    n = int(clamp((t - 0.6) / 1.4) * len(dm.CMD))
    text(d, (160, 330), dm.CMD[:n], M(27), FG, a)
    prog = clamp((t - 2.3) / 4.2)
    if t > 2.3:
        secs = int(round(prog * (42 * 60 + 47)))
        text(d, (160, 410), f"{min(5, int(prog * 5.2))}/5 runs", M(30, True), FG, a)
        d.rounded_rectangle((420, 412, 1400, 438), 8, fill=mix(TRACK, a))
        d.rounded_rectangle((420, 412, 420 + 980 * prog, 438), 8, fill=mix(ACC, a))
        text(d, (1430, 425), f"{secs // 3600}:{secs // 60 % 60:02d}:{secs % 60:02d}", M(30, True), FG, a, "lm")
        text(d, (160, 500), "5 runs, up to 4 at a time, each alone in its own sealed box, each with 45 minutes.", F("Inter-Medium.otf", 30), MUTED, a)
        text(d, (160, 550), "Real time for all five: 42 min 47.", F("Inter-Medium.otf", 30), MUTED, a)
    if t > 6.6:
        text(d, (W / 2, 760), "How did they score?", F("InterDisplay-Bold.otf", 48), FG, ramp(t, 6.6, 0.6) * k, "mm")
    return img

def replay_frame(t, dur, m0, m1, kicker, title, hold=3.5):
    img, d, k = base(t, dur, {"diff"})
    head(d, t, kicker, title, k)
    lead = 0.8
    m = m0 + (m1 - m0) * clamp((t - lead) / max(0.1, dur - lead - hold))
    a = ramp(t, 0.3) * k
    items = [f for f in dm.FEED if m0 - 1e-6 <= f[0] <= m]
    if not items: items = [f for f in dm.FEED if f[0] <= m][-1:]
    y = 290
    for mm, act, why, log in items[-5:]:
        cur = (mm, act, why, log) == items[-1]
        text(d, (120, y), f"min {mm:4.1f}", M(26, True), ACC if cur else MUTED, a)
        text(d, (300, y - 2), act, F("Inter-Bold.otf" if cur else "Inter-SemiBold.otf", 32), FG if cur else MUTED, a)
        if why:
            text(d, (300, y + 40), why, F("Inter-Medium.otf", 27), ACC if cur else MUTED, a)
        y += 100 if why else 64
    cur = items[-1]
    if cur[3]:
        panel(d, (120, 830, 1180, 945), a, fill=(250, 250, 251), r=14)
        text(d, (140, 846), "from its log:", F("Inter-SemiBold.otf", 22), MUTED, a)
        text(d, (140, 880), cur[3][:72], M(24), FG, a)
    panel(d, (1260, 280, 1800, 390), a, r=18)
    text(d, (1290, 312), "the AI's clock", F("Inter-SemiBold.otf", 24), MUTED, a, "lm")
    text(d, (1290, 358), f"minute {m:4.1f} of 45", F("InterDisplay-Black.otf", 44), FG, a, "lm")
    cx0, cy0, cx1, cy1 = 1300, 500, 1770, 840
    panel(d, (1260, 415, 1800, 945), a, r=18)
    text(d, (1290, 445), "practice score of each submission", F("Inter-Bold.otf", 24), FG, a, "lm")
    lo, hi = 0.28, 0.53
    X = lambda mm: cx0 + (cx1 - cx0) * mm / 17
    Y = lambda v: cy1 - (cy1 - cy0) * (v - lo) / (hi - lo)
    for xx in range(cx0, cx1, 18):
        d.line((xx, Y(0.507), xx + 9, Y(0.507)), fill=mix(GREEN, a * 0.7), width=3)
    text(d, (cx1, Y(0.507) - 8), "the expert: 0.507", F("Inter-SemiBold.otf", 21), GREEN, a, "rs")
    xy = [(X(s[0]), Y(s[1])) for s in dm.SUBS if s[0] <= m]
    if len(xy) > 1: d.line(xy, fill=mix(RED, a), width=5)
    for p in xy: d.ellipse((p[0] - 8, p[1] - 8, p[0] + 8, p[1] + 8), fill=mix(RED, a))
    text(d, (1290, 875), "red: the AI's submissions", F("Inter-Bold.otf", 22), RED, a, "lm")
    text(d, (1290, 907), "x: minutes · y: practice score", F("Inter-Medium.otf", 21), MUTED, a, "lm")
    return img, d, k, m

def s_rep1(t, dur): return replay_frame(t, dur, 0.0, 3.2, P4 + " · RUN C5, MINUTES 0 TO 3", "First, two quick tries")[0]
def s_rep2(t, dur): return replay_frame(t, dur, 3.2, 12.5, P4 + " · RUN C5, MINUTES 3 TO 12", "Then, it polishes one idea")[0]

def s_rep3(t, dur):
    img, d, k, m = replay_frame(t, dur, 12.5, 16.5, P4 + " · RUN C5, MINUTES 12 TO 16", "Finally, it stops", hold=7.0)
    t_box = 0.8 + (dur - 0.8 - 7.0) * (16.4 - 12.5) / 4.0 + 0.3
    if t > t_box:
        aa = ramp(t, t_box, 0.6) * k
        d.rounded_rectangle((120, 680, 1180, 790), 16, fill=mix(RED_L, aa), outline=mix(RED, aa), width=3)
        text(d, (150, 718), "It stops at minute 16.5, with 28.5 of its 45 minutes left.", F("Inter-Bold.otf", 31), RED, aa, "lm")
        text(d, (150, 765), "In practice, it is almost as good as the expert.", F("Inter-Medium.otf", 28), FG, aa, "lm")
    if t > t_box + 2.2:
        text(d, (120, 880), "But practice is not the test. Now the referee runs the real test.", F("Inter-Bold.otf", 30), FG,
             ramp(t, t_box + 2.2, 0.6) * k, "lm")
    return img

def s_reveal(t, dur):
    img, d, k = base(t, dur, {"gap"})
    head(d, t, P4, "Then the referee runs the real test", k)
    text(d, (120, 290), "The AI's last submission plays the 30 secret opponents, 500 games each.", F("Inter-SemiBold.otf", 32), FG, ramp(t, 0.5, 0.6) * k)
    a0 = ramp(t, 1.2, 0.6) * k
    c1, c2 = 1150, 1560
    text(d, (c1, 385), "the AI (run C5)", F("Inter-Bold.otf", 34), RED, a0, "mm")
    text(d, (c2, 385), "the expert", F("Inter-Bold.otf", 34), GREEN, a0, "mm")
    rows = (("In practice", "what the AI saw", "0.489", "0.507"),
            ("In the real test", "hidden from the AI until the end", "0.398", "0.487"))
    for i, (h, sub, va, ve) in enumerate(rows):
        aa = ramp(t, 1.8 + i * 1.8, 0.6) * k
        y = 425 + i * 160
        panel(d, (120, y, 1800, y + 138), aa, r=18)
        text(d, (160, y + 50), h, F("Inter-Bold.otf", 40), FG, aa, "lm")
        text(d, (160, y + 100), sub, F("Inter-Medium.otf", 28), MUTED, aa, "lm")
        text(d, (c1, y + 69), va, F("InterDisplay-Black.otf", 56), RED, aa, "mm")
        text(d, (c2, y + 69), ve, F("InterDisplay-Black.otf", 56), GREEN, aa, "mm")
    text(d, (W / 2, 820), "In practice, the AI was almost as good as the expert: 0.018 behind.", F("Inter-Bold.otf", 34), FG,
         ramp(t, 5.4, 0.6) * k, "mm")
    text(d, (W / 2, 880), "In the real test, it is clearly behind: 0.089.", F("Inter-Bold.otf", 34), RED, ramp(t, 7.0, 0.6) * k, "mm")
    return img

def s_scale(t, dur):
    img, d, k = base(t, dur, {"gap"})
    head(d, t, P4, "How far behind, exactly?", k)
    x0, x1 = 240, 1680
    def axis(y, lo, hi, label, ticks, t0):
        a = ramp(t, t0, 0.6) * k
        text(d, (120, y - 76), label, F("Inter-Bold.otf", 30), FG, a)
        d.line((x0, y, x1, y), fill=mix(MUTED, a), width=4)
        for n, (v, lab, c, up) in enumerate(ticks):
            X = x0 + (x1 - x0) * (v - lo) / (hi - lo)
            aa = ramp(t, t0 + 0.4 + 0.6 * n, 0.5) * k
            d.ellipse((X - 12, y - 12, X + 12, y + 12), fill=mix(c, aa))
            text(d, (X, y + (30 if not up else -26)), lab, F("Inter-Bold.otf", 28), c, aa, "mt" if not up else "mb")
    axis(420, 0.10, 0.55, "Game score in the real test",
         [(0.1475, "beginner (Dwarf) 0.148", MUTED, False), (0.487, "the expert 0.487", GREEN, False),
          (0.398, "the AI (run C5) 0.398", RED, True)], 0.5)
    if t > 3.6:
        text(d, (W / 2, 560), "↓  the official reward rescales it: Dwarf, the textbook beginner's program = 0, the expert = 1  ↓",
             F("Inter-SemiBold.otf", 29), MUTED, ramp(t, 3.6, 0.6) * k, "mm")
    if t > 4.8:
        axis(745, -0.12, 1.12, "Reward",
             [(0.0, "0  beginner", MUTED, False), (1.0, "1  the expert", GREEN, False), (0.740, "the AI 0.740", RED, True)], 4.8)
    if t > 8.0:
        aa = ramp(t, 8.0, 0.6) * k
        text(d, (W / 2, 875), "Reward 0.74: three quarters of the way from beginner to expert, and a quarter short.",
             F("Inter-Bold.otf", 32), FG, aa, "mm")
        text(d, (W / 2, 930), "the referee's file:  reward.txt = 0.739615", M(25), MUTED, aa, "mm")
    return img

# ---------------------------------------------------------------- part 4: one real game, in the presentation's frame
CELL = 7
INTRO, SLOW, FAST, OUT = dm.INTRO, dm.SLOW, dm.FAST, dm.OUT

def grid(owner, pa, pb, prog_l, prog_d):
    pal = np.array([[236, 238, 242], prog_l, dm.BLUE_L], np.uint8)
    cells = pal[owner].copy()
    for p in pb: cells[p] = dm.BLUE
    for p in pa: cells[p] = prog_d
    img = np.repeat(np.repeat(cells.reshape(dm.ROWS2, dm.COLS2, 3), CELL, 0), CELL, 1)
    msk = np.ones((CELL, CELL), bool); msk[5:, :] = False; msk[:, 5:] = False
    img = np.where(np.tile(msk, (dm.ROWS2, dm.COLS2))[..., None], img, 255)
    return Image.fromarray(img.astype(np.uint8), "RGB")

def s_fight(t, dur):
    img, d, k = base(t, dur, {"diff"})
    head(d, t, P4, "Why the gap? One game of the real test", k)
    (sa, wa), (sb, wb) = dm.fights()
    last = sa[-1][0]
    c = dm.step_at(t, last)
    a = ramp(t, 0.3) * k
    gy, gw, gh = 318, dm.COLS2 * CELL, dm.ROWS2 * CELL
    panels = [(170, sa, (248, 185, 185), RED, "the AI's program (red)", "Glance", False),
              (1050, sb, (180, 226, 196), GREEN, "the expert's program (green)", "Toxic", True)]
    for x, snaps, light, dark, title, nm, win in panels:
        cyc, owner, pa, pb, na, nb = dm.pick(snaps, c)
        g = grid(owner, pa, pb, light, dark)
        img.paste(g, (x, gy), Image.new("L", g.size, int(255 * a)))
        d = ImageDraw.Draw(img, "RGBA")
        text(d, (x, 306), title + "  vs  Blizzard (blue)", F("Inter-Bold.otf", 24), dark, a, "ls")
        text(d, (x, gy + gh + 22), f"{nm}: {na:,} process{'es' if na != 1 else ''} running  ·  Blizzard: {nb:,}", F("Inter-Bold.otf", 23), FG, a, "lm")
        end = snaps[-1][0]
        if win and t >= INTRO and c >= 9:
            aa = ramp(t, INTRO + SLOW * 9 / 60, 0.4) * k
            y0 = gy + 72 * CELL
            d.rounded_rectangle((x - 5, y0 - 5, x + gw + 5, y0 + 2 * CELL + 5), 8, outline=mix(GREEN, aa), width=4)
            d.rounded_rectangle((x + 90, y0 - 56, x + 610, y0 - 12), 10, fill=mix((255, 255, 255), aa), outline=mix(GREEN, aa), width=2)
            text(d, (x + 350, y0 - 34), "its bombs land on Blizzard's code", F("Inter-Bold.otf", 25), GREEN, aa, "mm")
        if t >= INTRO and c >= end:
            t_end = INTRO + (SLOW * end / 60 if end <= 60 else SLOW + FAST * (end - 60) / (last - 60))
            aa = ramp(t, t_end, 0.4) * k
            msg = f"wins at step {end:,}" if win else f"loses at step {end:,}"
            d.rounded_rectangle((x + 110, 500, x + 590, 590), 20, fill=mix((255, 255, 255), aa), outline=mix(dark, aa), width=4)
            text(d, (x + 350, 545), msg, F("InterDisplay-Black.otf", 38), dark, aa, "mm")
    ff = " · fast-forward" if 60 < c < last else ""
    text(d, (1750, 266), f"step {int(min(c, last)):,}{ff}", F("Inter-Bold.otf", 26), FG, a, "rm")
    text(d, (170, 266), "dark = code running   ·   light = memory it has written   ·   a program loses when none of its code runs",
         F("Inter-SemiBold.otf", 21), MUTED, a * clamp((t - INTRO + 0.5) / 0.5), "lm")
    if t < INTRO:
        aa = ramp(t, 0.6, 0.6) * k * clamp((INTRO - t) / 0.4)
        d.rounded_rectangle((380, 330, 1540, 790), 24, fill=mix((255, 255, 255), aa * 0.97), outline=mix(LINE, aa), width=3)
        text(d, (960, 385), "How to read this", F("Inter-Black.otf", 40), FG, aa, "mm")
        rows = [("One game against Blizzard: the secret opponent where the gap is largest.", FG),
                ("Left: the AI's program (red). Right: the expert's (green).", FG),
                ("Same opponent (blue), same starting positions.", MUTED),
                ("Dark squares: code running. Light squares: memory it has written.", FG),
                ("A program loses when none of its code is still running.", FG)]
        for jj, (s_, cc) in enumerate(rows):
            text(d, (430, 460 + jj * 62), s_, F("Inter-SemiBold.otf", 30), cc, ramp(t, 1.0 + jj * 0.9, 0.5) * aa, "lm")
    elif t < INTRO + SLOW:
        if c < dm.WIN_E:
            cap, t0 = "The expert starts with a quick search: it checks spots across memory to find the opponent.", INTRO + 0.3
        else:
            cap, t0 = "Found and bombed: the expert wins at step 41. The AI's program is still searching.", INTRO + SLOW * dm.WIN_E / 60
        text(d, (W / 2, 946), cap, F("Inter-Bold.otf", 28), GREEN, ramp(t, t0, 0.4) * k, "mm")
    else:
        if c < 8300:
            cap, t0 = "The AI writes bombs all over memory (red), but Blizzard's code keeps running (blue counter).", INTRO + SLOW + 0.4
        else:
            cap, t0 = "Then the AI's running processes drop to zero: it loses at step 9,060.", INTRO + SLOW + FAST * (8300 - 60) / (last - 60)
        text(d, (W / 2, 946), cap, F("Inter-Bold.otf", 28), RED, ramp(t, t0, 0.4) * k, "mm")
    return img

def s_stats(t, dur):
    img, d, k = base(t, dur, {"diff"})
    head(d, t, P4, "Not luck: 500 games, same opponent", k)
    groups = [("the AI's program", [(0, "wins"), (147, "draws"), (353, "losses")], RED),
              ("the expert's program", [(119, "wins"), (365, "draws"), (16, "losses")], GREEN)]
    g = ramp(t, 0.9, 1.0)
    for gi, (lab, vals, col) in enumerate(groups):
        a = ramp(t, 0.5, 0.6) * k
        y = 290 + gi * 270
        text(d, (120, y), lab, F("Inter-Bold.otf", 38), col, a)
        x = 120; small = []
        for v, name in vals:
            w = 1680 * v / 500 * g
            c = col if name == "wins" else (DIM if name == "draws" else (120, 128, 140))
            if w > 2: d.rounded_rectangle((x, y + 62, x + w, y + 138), 10, fill=mix(c, a))
            if v > 40: text(d, (x + w / 2, y + 100), f"{v} {name}", F("Inter-Bold.otf", 28), FG if name == "draws" else BG, a * clamp((g - 0.85) / 0.15), "mm")
            else: small.append(f"{v} {name}")
            x += w
        if small:
            text(d, (120, y + 175), "  ·  ".join(small), F("Inter-Bold.otf", 28), MUTED, a * clamp((g - 0.85) / 0.15), "lm")
    if t > 3.4:
        aa = ramp(t, 3.4, 0.6) * k
        text(d, (W / 2, 860), "Blizzard is the opponent where the gap is largest. Over all 30, the expert does better against 22.",
             F("Inter-SemiBold.otf", 30), FG, aa, "mm")
        text(d, (W / 2, 915), "Scored by pMARS, the game's official simulator.", F("Inter-Medium.otf", 27), MUTED, aa, "mm")
    return img

bridge = ex.bridge
SCENES = [("p01_title", ex.s_title, 7.5), ("p02_question", s_question, 9.0), ("p03_goal", ex.s_goal, 10.0), ("p04_need", ex.s_need, 11.5),
          ("p05_bridge", bridge("We found it in a game from 1984:", set(), "Core War, a game you play by writing programs."), 4.5),
          ("p06_game", s_game, 11.0), ("p07_player", ex.s_player, 10.5), ("p08_lang", ex.s_lang, 10.5), ("p09_rps", ex.s_rps, 11.5),
          ("p10_bridge", bridge("So how do we turn it into a test?", set()), 3.8),
          ("p11_test", s_test, 12.0), ("p12_rules", s_rules, 13.0),
          ("p13_fits", ex.s_fits, 12.0), ("p14_tests", ex.s_tests, 10.0), ("p15_space", ex.s_space, 9.5), ("p16_design", ex.s_design, 10.0),
          ("p17_bridge", bridge("So how do the best AI agents do?", {"gap"}), 3.8),
          ("p18_term", s_term, 9.5), ("p19_result", ex.s_result, 11.5),
          ("p20_bridge", bridge("Let's replay one run, from its own logs.", {"diff"},
                                "Run C5: the one that came closest to the expert in practice."), 4.5),
          ("p21_rep1", s_rep1, 14.0), ("p22_rep2", s_rep2, 18.0), ("p23_rep3", s_rep3, 15.0),
          ("p24_reveal", s_reveal, 12.0), ("p25_scale", s_scale, 12.5),
          ("p26_fight", s_fight, INTRO + SLOW + FAST + OUT), ("p27_stats", s_stats, 9.0),
          ("p28_bridge", bridge("What goes wrong, across all five runs?", {"diff"}), 3.8),
          ("p29_clock", ex.s_clock, 11.0), ("p30_learned", ex.s_learned, 14.0), ("p31_real", ex.s_real, 10.0),
          ("p32_bridge", bridge("Can the score be trusted?", {"integ", "craft"}), 3.5),
          ("p33_cheat", ex.s_cheat, 10.0), ("p34_craft", ex.s_craft, 10.5),
          ("p35_bridge", bridge("Last question: can an AI learn from this game?", {"tie"}), 3.8),
          ("p36_train", ex.s_train, 10.5), ("p37_close", ex.s_close, 10.0)]

if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    for name, fn, dur in SCENES:
        if what in ("all", name):
            render(name, fn, dur); print("rendered", name, flush=True)
