#!/usr/bin/env python3
"""The demo video (about 3 minutes): one real Harbor + OpenCode run (C5), replayed from its logs.
Part 1 the test, part 2 the run, part 3 the result, part 4 why the gap.
The side-by-side game is replayed by mars.py and each outcome is asserted against pMARS.
Every number on screen comes from runs/harbor/ and results/ (trajectories_harbor_v4.md, the verifier's details.json).
usage: python video/demo.py [all | <scene name>]   -> video/build/<scene>.mp4"""
import os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw
from style import (W, H, F, M, BG, LINE, FG, MUTED, DIM, TRACK, RED, GREEN, RED_L, GREEN_L,
                   clamp, ramp, mix, fade, text, panel, arrow, render, ROOT)
sys.path.insert(0, ROOT)
from arena import core
import mars

CMD = "$ harbor run -p harbor/corewar-hill -a opencode -m anthropic/claude-opus-5-5 -k 5 -o jobs"

# ---------------------------------------------------------------- one real game, replayed (checked against pMARS)
OPP = os.path.join(ROOT, "data", "hill", "blizzard.red")          # the secret opponent where the gap is largest
AI_SRC = os.path.join(ROOT, "runs", "harbor", "final-v4", "run_C5.red")   # the AI's final submission (run C5)
EX_SRC = os.path.join(ROOT, "data", "reference_toxic.red")         # the human reference (Toxic)
FPOS = 7253                                                         # same start position for both games
COLS2, ROWS2, CELL2 = 100, 80, 8
BLUE, BLUE_L = (60, 90, 170), (205, 214, 236)
FIGHTS = None

def run_fight(src):
    out = subprocess.run([str(core.PMARS), "-r", "1", "-F", str(FPOS), src, OPP], capture_output=True, text=True).stdout
    ws = mars.parse_listing(out)
    m = mars.Mars(ws[0], ws[1], FPOS); snaps = []
    def cb(mm, ex):
        snaps.append((mm.cycle, np.array(mm.owner, np.uint8), list(mm.q[0])[:300], list(mm.q[1])[:300], len(mm.q[0]), len(mm.q[1])))
    w = m.run(cb)
    assert w == mars.pmars_round(src, OPP, str(core.PMARS), FPOS)
    return snaps, w

def fights():
    global FIGHTS
    if FIGHTS is None:
        FIGHTS = (run_fight(AI_SRC), run_fight(EX_SRC))
        assert FIGHTS[0][1] == 2 and FIGHTS[1][1] == 1
    return FIGHTS

def grid2(owner, pa, pb, prog_l, prog_d):
    pal = np.array([[236, 238, 242], prog_l, BLUE_L], np.uint8)
    cells = pal[owner].copy()
    for p in pb: cells[p] = BLUE
    for p in pa: cells[p] = prog_d
    img = np.repeat(np.repeat(cells.reshape(ROWS2, COLS2, 3), CELL2, 0), CELL2, 1)
    msk = np.ones((CELL2, CELL2), bool); msk[6:, :] = False; msk[:, 6:] = False
    img = np.where(np.tile(msk, (ROWS2, COLS2))[..., None], img, 255)
    return Image.fromarray(img.astype(np.uint8), "RGB")

def pick(snaps, c):
    best = snaps[0]
    for s_ in snaps:
        if s_[0] <= c: best = s_
        else: break
    return best


BLUE_T = (60, 84, 150)
ACC = (37, 99, 235)            # neutral accent (not AI red, not expert green)
PARTS = ["The test", "The run", "The result", "Why the gap"]

def page(t, dur, kicker, title):
    img = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(img, "RGBA"); k = fade(t, dur)
    a = ramp(t, 0.0, 0.5) * k
    text(d, (120, 70), kicker, F("Inter-Bold.otf", 30), ACC, a)
    text(d, (120, 108), title, F("InterDisplay-Black.otf", 68), FG, a)
    return img, d, k

def part(i, extra=""):
    s = f"PART {i} OF 4  ·  {PARTS[i - 1].upper()}"
    return s + (f"  ·  {extra}" if extra else "")

def lines(d, x, y, rows, t, t0, gap, step, k):
    """rows: (text, font, colour); each appears `step` s after the previous one."""
    for i, (s, f, c) in enumerate(rows):
        text(d, (x, y + i * gap), s, f, c, ramp(t, t0 + i * step, 0.5) * k)

# ---------------------------------------------------------------- title
def x_title(t, dur):
    img = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(img, "RGBA"); k = fade(t, dur, 0.3, 0.5)
    text(d, (W / 2, 290), "DEMO", F("InterDisplay-Black.otf", 190), FG, ramp(t, 0.3, 0.7) * k, "mm")
    text(d, (W / 2, 440), "One real AI run, replayed from its own logs", F("Inter-Bold.otf", 50), ACC, ramp(t, 0.9, 0.7) * k, "mm")
    text(d, (W / 2, 520), "The question: can a top AI agent write a game program as strong as a human expert's?",
         F("Inter-SemiBold.otf", 36), FG, ramp(t, 1.6, 0.7) * k, "mm")
    text(d, (W / 2, 585), "run C5  ·  Claude Opus 5.5  ·  the challenge's official harness (Harbor + OpenCode)  ·  14 Nov 2026  ·  sped up",
         F("Inter-Medium.otf", 26), MUTED, ramp(t, 2.2, 0.7) * k, "mm")
    for i, name in enumerate(PARTS):
        a = ramp(t, 3.0 + i * 0.45, 0.5) * k
        cx = 300 + i * 440
        panel(d, (cx - 190, 720, cx + 190, 830), a, r=18)
        d.ellipse((cx - 160, 751, cx - 112, 799), fill=mix(ACC, a))
        text(d, (cx - 136, 775), str(i + 1), F("Inter-Black.otf", 26), BG, a, "mm")
        text(d, (cx - 92, 775), name, F("Inter-Bold.otf", 34), FG, a, "lm")
    return img

# ---------------------------------------------------------------- part 1: the game, the test, the rules
GAME_IMG = None
def x_game(t, dur):
    global GAME_IMG
    img, d, k = page(t, dur, part(1), "First, the game: Core War")
    if GAME_IMG is None:
        (sa, _), _ = fights()
        cyc, owner, pa, pb, na, nb = pick(sa, 3021)
        GAME_IMG = grid2(owner, pa, pb, (248, 185, 185), RED)
    a = ramp(t, 0.4, 0.6) * k
    img.paste(GAME_IMG, (120, 260), Image.new("L", GAME_IMG.size, int(255 * a)))
    d = ImageDraw.Draw(img, "RGBA")
    text(d, (120, 930), "a real game, mid-way: one program in red, the other in blue", F("Inter-SemiBold.otf", 24), MUTED, a)
    B, S = F("Inter-Bold.otf", 34), F("Inter-Medium.otf", 29)
    rows = [("Two programs share one memory", B, FG), ("of 8,000 cells.", S, MUTED), ("", S, FG),
            ("Each runs its own code and tries", B, FG), ("to crash the other, for instance", S, MUTED),
            ("by writing over its code.", S, MUTED), ("", S, FG),
            ("A program loses when none", B, FG), ("of its code is still running.", S, MUTED), ("", S, FG),
            ("Both still running at the time", B, FG), ("limit: a draw.", S, MUTED)]
    y = 290
    for i, (s, f, c) in enumerate(rows):
        grp = sum(1 for r in rows[:i] if r[0] == "")
        if s: text(d, (1000, y), s, f, c, ramp(t, 1.0 + grp * 1.6, 0.5) * k)
        y += 26 if s == "" else 46
    return img

def x_test(t, dur):
    img, d, k = page(t, dur, part(1), "What the AI has to do")
    text(d, (120, 230), "The AI writes one program. That program then takes the test:", F("Inter-SemiBold.otf", 34), FG, ramp(t, 0.5, 0.6) * k)
    a1 = ramp(t, 1.2, 0.7) * k
    panel(d, (120, 310, 520, 470), a1, fill=RED_L, outline=RED, r=18)
    text(d, (320, 390), "the AI's program", F("Inter-Bold.otf", 34), RED, a1, "mm")
    a2 = ramp(t, 1.8, 0.7) * k
    arrow(d, (540, 390), (660, 390), MUTED, a2, width=6)
    text(d, (600, 345), "plays", F("Inter-SemiBold.otf", 24), MUTED, a2, "mm")
    for i in range(30):
        r, c = divmod(i, 10)
        x, y = 690 + c * 108, 310 + r * 56
        aa = ramp(t, 2.0 + i * 0.04, 0.4) * k
        d.rounded_rectangle((x, y, x + 96, y + 46), 10, fill=mix((222, 229, 244), aa), outline=mix((90, 112, 170), aa), width=2)
        text(d, (x + 48, y + 23), "?", F("Inter-Bold.otf", 24), (90, 112, 170), aa, "mm")
    text(d, (1230, 500), "30 secret opponents, 500 games against each", F("Inter-Bold.otf", 30), BLUE_T, ramp(t, 3.0) * k, "mm")
    if t > 3.8:
        aa = ramp(t, 3.8, 0.6) * k
        text(d, (120, 570), "Each game:  win = 3 points,  draw = 1,  loss = 0.", F("Inter-Bold.otf", 40), FG, aa)
        text(d, (120, 630), "So the game score = points won ÷ points possible, from 0 to 1.", F("Inter-SemiBold.otf", 36), MUTED, aa)
    if t > 6.0:
        aa = ramp(t, 6.0, 0.6) * k
        panel(d, (120, 710, 1800, 950), aa, fill=GREEN_L, outline=GREEN, r=18)
        text(d, (160, 760), "For comparison, a human expert's program takes exactly the same test.", F("Inter-Bold.otf", 36), GREEN, aa, "lm")
        text(d, (160, 818), "“Toxic”, by John Metcalf: rated #1 of 264 human-written programs (Elo, CodeClash ladder).", F("Inter-SemiBold.otf", 30), FG, aa, "lm")
        text(d, (160, 880), "Its game score: 0.487. Against opponents this strong, about 0.5 is top level.", F("Inter-SemiBold.otf", 30), FG,
             ramp(t, 7.4, 0.6) * k, "lm")
    return img

def x_rules(t, dur):
    img, d, k = page(t, dur, part(1), "To prepare: 45 minutes and practice")
    steps = [("1", "It writes a program", "a small text file in Redcode, the game's assembly language"),
             ("2", "It practises", "against 30 practice opponents, and gets a practice score"),
             ("3", "It submits", "as often as it wants; only the last submission counts"),
             ("4", "It decides when to stop", "every reply from its tools shows a clock with the minutes left")]
    for i, (n, h, sub) in enumerate(steps):
        a = ramp(t, 0.8 + i * 1.3, 0.7) * k
        y = 250 + i * 145
        panel(d, (120, y, 1800, y + 124), a, r=18)
        d.ellipse((150, y + 32, 210, y + 92), fill=mix(FG, a))
        text(d, (180, y + 62), n, F("Inter-Black.otf", 30), BG, a, "mm")
        text(d, (240, y + 42), h, F("Inter-Bold.otf", 40), FG, a, "lm")
        text(d, (240, y + 94), sub, F("Inter-Medium.otf", 31), MUTED, a, "lm")
    if t > 6.4:
        aa = ramp(t, 6.4, 0.7) * k
        panel(d, (120, 850, 1800, 1010), aa, fill=RED_L, outline=RED, r=18)
        text(d, (W / 2, 900), "But the practice opponents are not the secret ones.", F("Inter-Bold.otf", 38), RED, aa, "mm")
        text(d, (W / 2, 960), "Only at the end does a referee program run the real test. The AI never sees that score.",
             F("Inter-SemiBold.otf", 30), FG, ramp(t, 7.4, 0.6) * k, "mm")
    return img

# ---------------------------------------------------------------- part 2: the run
def x_term(t, dur):
    img, d, k = page(t, dur, part(2), "Five runs of the same AI, one command")
    a = ramp(t, 0.3) * k
    panel(d, (120, 260, 1800, 600), a, fill=(250, 250, 251))
    n = int(clamp((t - 0.6) / 1.4) * len(CMD))
    text(d, (160, 300), CMD[:n], M(27), FG, a)
    prog = clamp((t - 2.3) / 4.2)
    if t > 2.3:
        secs = int(round(prog * (42 * 60 + 47)))
        text(d, (160, 380), f"{min(5, int(prog * 5.2))}/5 runs", M(30, True), FG, a)
        d.rounded_rectangle((420, 382, 1400, 408), 8, fill=mix(TRACK, a))
        d.rounded_rectangle((420, 382, 420 + 980 * prog, 408), 8, fill=mix(ACC, a))
        text(d, (1430, 395), f"{secs // 3600}:{secs // 60 % 60:02d}:{secs % 60:02d}", M(30, True), FG, a, "lm")
        text(d, (160, 470), "5 runs, up to 4 at a time, each alone in its own sealed box, each with 45 minutes.", F("Inter-Medium.otf", 30), MUTED, a)
        text(d, (160, 520), "Real time for all five: 42 min 47.", F("Inter-Medium.otf", 30), MUTED, a)
    if t > 6.6:
        aa = ramp(t, 6.6, 0.6) * k
        text(d, (W / 2, 720), "We follow run C5: the one that came closest to the expert in practice.", F("InterDisplay-Bold.otf", 42), FG, aa, "mm")
    return img

# (minute, what it did, why / what it means, a real line from its log)
FEED = [(0.0, "Reads the rules and the strategy notes", "Everything it needs is provided.", "$ ls /app/doc; head -50 /app/doc/strategy_primer.md"),
        (0.2, "Writes its first program: a stone", "A stone drops bombs (code that crashes whoever runs it) over memory.", ";name Pebble Clear   (its own file, stone.red)"),
        (1.1, "Tries six different bombing distances", "The distance between bombs decides where they land.", "$ for st in 3315 2365 3044 5363 1871 3359; do ..."),
        (2.2, "Submits the stone", "Practice score 0.311. An early submission counts even if time runs out.", "$ python3 /app/tools/spar.py --submit st2791.red"),
        (3.0, "Switches style: a scanner it calls “Glance”", "A scanner looks for the enemy, then attacks it.", ";name Glance   (sc14.red)"),
        (3.2, "Submits Glance", "Practice score jumps to 0.411.", "$ python3 /app/tools/spar.py --submit sc14.red"),
        (5.1, "Tunes the scan: dozens of variants", "Each test is real games against the 30 practice opponents.", '$ for p in "20 10" "24 12" "16 8" "28 14" "32 16"; do ...'),
        (6.0, "Submits the best version", "Practice score 0.472.", "$ python3 /app/tools/spar.py --submit best.red"),
        (7.7, "Tries switching styles from game to game", "It scores lower, so the AI drops the idea.", ";name Glance PS   (remembers past games to pick a style)"),
        (10.7, "Submits a new version", "Practice score 0.485.", "$ python3 /app/tools/spar.py --submit na.red"),
        (12.5, "Moves where the scan starts, submits again", "Practice score 0.489: almost the expert's 0.507.", "$ python3 /app/tools/spar.py --submit b2.red"),
        (13.0, "Keeps trying small changes", "None of them beats 0.489 in practice.", "$ ... spar.py x.red --rounds 300 | tail -1"),
        (16.1, "Checks its submission", "", "$ python3 /app/tools/spar.py --status"),
        (16.4, "Stops and writes its report", "“It scores 0.489 on the sparring set” (its practice opponents).", "")]
SUBS = [(2.2, 0.311), (3.2, 0.411), (6.0, 0.472), (10.7, 0.485), (12.5, 0.489)]

def replay_frame(t, dur, m0, m1, kicker, title, hold=3.5):
    img, d, k = page(t, dur, kicker, title)
    lead = 0.8
    m = m0 + (m1 - m0) * clamp((t - lead) / max(0.1, dur - lead - hold))
    a = ramp(t, 0.3) * k
    items = [f for f in FEED if m0 - 1e-6 <= f[0] <= m]
    if not items: items = [f for f in FEED if f[0] <= m][-1:]
    y = 260
    for mm, act, why, log in items[-5:]:
        cur = (mm, act, why, log) == items[-1]
        text(d, (120, y), f"min {mm:4.1f}", M(26, True), ACC if cur else MUTED, a)
        text(d, (300, y - 2), act, F("Inter-Bold.otf" if cur else "Inter-SemiBold.otf", 32), FG if cur else MUTED, a)
        if why:
            text(d, (300, y + 40), why, F("Inter-Medium.otf", 27), ACC if cur else MUTED, a)
        y += 100 if why else 64
    cur = items[-1]
    if cur[3]:
        panel(d, (120, 840, 1180, 960), a, fill=(250, 250, 251), r=14)
        text(d, (140, 856), "from its log:", F("Inter-SemiBold.otf", 22), MUTED, a)
        text(d, (140, 888), cur[3][:72], M(24), FG, a)
    panel(d, (1260, 250, 1800, 370), a, r=18)
    text(d, (1290, 285), "the AI's clock", F("Inter-SemiBold.otf", 24), MUTED, a, "lm")
    text(d, (1290, 335), f"minute {m:4.1f} of 45", F("InterDisplay-Black.otf", 44), FG, a, "lm")
    cx0, cy0, cx1, cy1 = 1300, 480, 1770, 850
    panel(d, (1260, 400, 1800, 960), a, r=18)
    text(d, (1290, 430), "practice score of each submission", F("Inter-Bold.otf", 24), FG, a, "lm")
    lo, hi = 0.28, 0.53
    X = lambda mm: cx0 + (cx1 - cx0) * mm / 17
    Y = lambda v: cy1 - (cy1 - cy0) * (v - lo) / (hi - lo)
    for xx in range(cx0, cx1, 18):
        d.line((xx, Y(0.507), xx + 9, Y(0.507)), fill=mix(GREEN, a * 0.7), width=3)
    text(d, (cx1, Y(0.507) - 8), "the expert: 0.507", F("Inter-SemiBold.otf", 21), GREEN, a, "rs")
    xy = [(X(s[0]), Y(s[1])) for s in SUBS if s[0] <= m]
    if len(xy) > 1: d.line(xy, fill=mix(RED, a), width=5)
    for p in xy: d.ellipse((p[0] - 8, p[1] - 8, p[0] + 8, p[1] + 8), fill=mix(RED, a))
    text(d, (1290, 878), "red: the AI's submissions", F("Inter-Bold.otf", 22), RED, a, "lm")
    text(d, (1290, 912), "x: minutes · y: practice score", F("Inter-Medium.otf", 21), MUTED, a, "lm")
    return img, d, k, m

def x_rep1(t, dur): return replay_frame(t, dur, 0.0, 3.2, part(2, "MINUTES 0 TO 3"), "First, two quick tries")[0]
def x_rep2(t, dur): return replay_frame(t, dur, 3.2, 12.5, part(2, "MINUTES 3 TO 12"), "Then, it polishes one idea")[0]

def x_rep3(t, dur):
    img, d, k, m = replay_frame(t, dur, 12.5, 16.5, part(2, "MINUTES 12 TO 16"), "Finally, it stops", hold=7.0)
    t_box = 0.8 + (dur - 0.8 - 7.0) * (16.4 - 12.5) / 4.0 + 0.3
    if t > t_box:
        aa = ramp(t, t_box, 0.6) * k
        d.rounded_rectangle((120, 700, 1180, 820), 16, fill=mix(RED_L, aa), outline=mix(RED, aa), width=3)
        text(d, (150, 740), "It stops at minute 16.5, with 28.5 of its 45 minutes left.", F("Inter-Bold.otf", 31), RED, aa, "lm")
        text(d, (150, 790), "In practice, it is almost as good as the expert.", F("Inter-Medium.otf", 28), FG, aa, "lm")
    if t > t_box + 2.2:
        text(d, (W / 2, 1015), "But practice is not the test. Now the referee runs the real test.", F("Inter-Bold.otf", 34), FG,
             ramp(t, t_box + 2.2, 0.6) * k, "mm")
    return img

# ---------------------------------------------------------------- part 3: the result
def x_reveal(t, dur):
    img, d, k = page(t, dur, part(3), "Then the referee runs the real test")
    text(d, (120, 250), "The AI's last submission plays the 30 secret opponents, 500 games each.", F("Inter-SemiBold.otf", 34), FG, ramp(t, 0.5, 0.6) * k)
    a0 = ramp(t, 1.2, 0.6) * k
    c1, c2 = 1150, 1560
    text(d, (c1, 350), "the AI (run C5)", F("Inter-Bold.otf", 34), RED, a0, "mm")
    text(d, (c2, 350), "the expert", F("Inter-Bold.otf", 34), GREEN, a0, "mm")
    rows = (("In practice", "what the AI saw", "0.489", "0.507"),
            ("In the real test", "hidden from the AI until the end", "0.398", "0.487"))
    for i, (h, sub, va, ve) in enumerate(rows):
        aa = ramp(t, 1.8 + i * 1.8, 0.6) * k
        y = 400 + i * 170
        panel(d, (120, y, 1800, y + 140), aa, r=18)
        text(d, (160, y + 50), h, F("Inter-Bold.otf", 40), FG, aa, "lm")
        text(d, (160, y + 100), sub, F("Inter-Medium.otf", 28), MUTED, aa, "lm")
        text(d, (c1, y + 70), va, F("InterDisplay-Black.otf", 56), RED, aa, "mm")
        text(d, (c2, y + 70), ve, F("InterDisplay-Black.otf", 56), GREEN, aa, "mm")
    text(d, (W / 2, 800), "In practice, the AI was almost as good as the expert: 0.018 behind.", F("Inter-Bold.otf", 36), FG,
         ramp(t, 5.4, 0.6) * k, "mm")
    text(d, (W / 2, 866), "In the real test, it is clearly behind: 0.089.", F("Inter-Bold.otf", 36), RED, ramp(t, 7.0, 0.6) * k, "mm")
    return img

def x_scale(t, dur):
    img, d, k = page(t, dur, part(3), "How far behind, exactly?")
    x0, x1 = 240, 1680
    def axis(y, lo, hi, label, ticks, t0):
        a = ramp(t, t0, 0.6) * k
        text(d, (120, y - 80), label, F("Inter-Bold.otf", 32), FG, a)
        d.line((x0, y, x1, y), fill=mix(MUTED, a), width=4)
        for n, (v, lab, c, up) in enumerate(ticks):
            X = x0 + (x1 - x0) * (v - lo) / (hi - lo)
            aa = ramp(t, t0 + 0.4 + 0.6 * n, 0.5) * k
            d.ellipse((X - 12, y - 12, X + 12, y + 12), fill=mix(c, aa))
            text(d, (X, y + (30 if not up else -26)), lab, F("Inter-Bold.otf", 28), c, aa, "mt" if not up else "mb")
    axis(390, 0.10, 0.55, "Game score in the real test",
         [(0.1475, "beginner (Dwarf) 0.148", MUTED, False), (0.487, "the expert 0.487", GREEN, False),
          (0.398, "the AI (run C5) 0.398", RED, True)], 0.5)
    if t > 3.6:
        aa = ramp(t, 3.6, 0.6) * k
        text(d, (W / 2, 540), "↓  the official reward rescales it: Dwarf, the textbook beginner's program = 0, the expert = 1  ↓",
             F("Inter-SemiBold.otf", 29), MUTED, aa, "mm")
    if t > 4.8:
        axis(740, -0.12, 1.12, "Reward",
             [(0.0, "0  beginner", MUTED, False), (1.0, "1  the expert", GREEN, False), (0.740, "the AI 0.740", RED, True)], 4.8)
    if t > 8.0:
        aa = ramp(t, 8.0, 0.6) * k
        text(d, (W / 2, 900), "Reward 0.74: three quarters of the way from beginner to expert, and a quarter short.",
             F("Inter-Bold.otf", 34), FG, aa, "mm")
        text(d, (W / 2, 965), "the referee's file:  reward.txt = 0.739615", M(26), MUTED, aa, "mm")
    return img

# ---------------------------------------------------------------- part 4: why the gap
INTRO, SLOW, FAST, OUT = 7.0, 8.0, 10.0, 4.0
WIN_E = 41

def step_at(t, last):
    if t < INTRO: return 0
    if t < INTRO + SLOW: return 60 * (t - INTRO) / SLOW
    return 60 + (last - 60) * clamp((t - INTRO - SLOW) / FAST)

def x_fight(t, dur):
    img, d, k = page(t, dur, part(4), "Why? Watch one game of the real test")
    (sa, wa), (sb, wb) = fights()
    last = sa[-1][0]
    c = step_at(t, last)
    a = ramp(t, 0.3) * k
    panels = [(120, sa, (248, 185, 185), RED, "the AI's program (red)", "Glance", False),
              (1000, sb, (180, 226, 196), GREEN, "the expert's program (green)", "Toxic", True)]
    for x, snaps, light, dark, title, nm, win in panels:
        cyc, owner, pa, pb, na, nb = pick(snaps, c)
        g = grid2(owner, pa, pb, light, dark)
        img.paste(g, (x, 300), Image.new("L", g.size, int(255 * a)))
        d = ImageDraw.Draw(img, "RGBA")
        text(d, (x, 272), title + "  vs  Blizzard (blue)", F("Inter-Bold.otf", 26), dark, a, "lm")
        text(d, (x, 300 + ROWS2 * CELL2 + 26), f"{nm}: {na:,} process{'es' if na != 1 else ''} running   ·   Blizzard: {nb:,}", F("Inter-Bold.otf", 25), FG, a, "lm")
        end = snaps[-1][0]
        if win and t >= INTRO and c >= 9:
            aa = ramp(t, INTRO + SLOW * 9 / 60, 0.4) * k
            d.rounded_rectangle((x - 6, 300 + 72 * CELL2 - 6, x + COLS2 * CELL2 + 6, 300 + 74 * CELL2 + 6), 8, outline=mix(GREEN, aa), width=4)
            d.rounded_rectangle((x + 120, 300 + 72 * CELL2 - 62, x + 680, 300 + 72 * CELL2 - 14), 10, fill=mix((255, 255, 255), aa), outline=mix(GREEN, aa), width=2)
            text(d, (x + 400, 300 + 72 * CELL2 - 38), "its bombs land on Blizzard's code", F("Inter-Bold.otf", 26), GREEN, aa, "mm")
        if t >= INTRO and c >= end:
            t_end = INTRO + (SLOW * end / 60 if end <= 60 else SLOW + FAST * (end - 60) / (last - 60))
            aa = ramp(t, t_end, 0.4) * k
            msg = f"wins at step {end:,}" if win else f"loses at step {end:,}"
            d.rounded_rectangle((x + 150, 520, x + 650, 620), 20, fill=mix((255, 255, 255), aa), outline=mix(dark, aa), width=4)
            text(d, (x + 400, 570), msg, F("InterDisplay-Black.otf", 40), dark, aa, "mm")
    ff = " · fast-forward" if c > 60 and c < last else ""
    text(d, (1800, 222), f"step {int(min(c, last)):,}{ff}", F("Inter-Bold.otf", 28), FG, a, "rm")
    text(d, (120, 222), "dark = code running   ·   light = memory it has written   ·   a program loses when none of its code runs",
         F("Inter-SemiBold.otf", 22), MUTED, a * clamp((t - INTRO + 0.5) / 0.5), "lm")
    if t < INTRO:
        aa = ramp(t, 0.6, 0.6) * k * clamp((INTRO - t) / 0.4)
        d.rounded_rectangle((380, 360, 1540, 820), 24, fill=mix((255, 255, 255), aa * 0.97), outline=mix(LINE, aa), width=3)
        text(d, (960, 415), "How to read this", F("Inter-Black.otf", 40), FG, aa, "mm")
        rows = [("One game against Blizzard: the secret opponent where the gap is largest.", FG),
                ("Left: the AI's program (red). Right: the expert's (green).", FG),
                ("Same opponent (blue), same starting positions.", MUTED),
                ("Dark squares: code running. Light squares: memory it has written.", FG),
                ("A program loses when none of its code is still running.", FG)]
        for jj, (s_, cc) in enumerate(rows):
            text(d, (430, 490 + jj * 62), s_, F("Inter-SemiBold.otf", 30), cc, ramp(t, 1.0 + jj * 0.9, 0.5) * aa, "lm")
    elif t < INTRO + SLOW:
        if c < WIN_E:
            cap, col, t0 = "The expert starts with a quick search: it checks spots across memory to find the opponent.", GREEN, INTRO + 0.3
        else:
            cap, col, t0 = "Found and bombed: the expert wins at step 41. The AI's program is still searching.", GREEN, INTRO + SLOW * WIN_E / 60
        text(d, (W / 2, 1010), cap, F("Inter-Bold.otf", 30), col, ramp(t, t0, 0.4) * k, "mm")
    else:
        if c < 8300:
            cap, t0 = "The AI writes bombs all over memory (red), but Blizzard's code keeps running (blue counter).", INTRO + SLOW + 0.4
        else:
            cap, t0 = "Then the AI's running processes drop to zero: it loses at step 9,060.", INTRO + SLOW + FAST * (8300 - 60) / (last - 60)
        text(d, (W / 2, 1010), cap, F("Inter-Bold.otf", 30), RED, ramp(t, t0, 0.4) * k, "mm")
    return img

def x_stats(t, dur):
    img, d, k = page(t, dur, part(4), "Not bad luck: 500 games, same opponent")
    groups = [("the AI's program", [(0, "wins"), (147, "draws"), (353, "losses")], RED),
              ("the expert's program", [(119, "wins"), (365, "draws"), (16, "losses")], GREEN)]
    g = ramp(t, 0.9, 1.0)
    for gi, (lab, vals, col) in enumerate(groups):
        a = ramp(t, 0.5, 0.6) * k
        y = 270 + gi * 290
        text(d, (120, y), lab, F("Inter-Bold.otf", 40), col, a)
        x = 120; small = []
        for v, name in vals:
            w = 1680 * v / 500 * g
            c = col if name == "wins" else (DIM if name == "draws" else (120, 128, 140))
            if w > 2: d.rounded_rectangle((x, y + 70, x + w, y + 150), 10, fill=mix(c, a))
            if v > 40: text(d, (x + w / 2, y + 110), f"{v} {name}", F("Inter-Bold.otf", 28), FG if name == "draws" else BG, a * clamp((g - 0.85) / 0.15), "mm")
            else: small.append(f"{v} {name}")
            x += w
        if small:
            text(d, (120, y + 190), "  ·  ".join(small), F("Inter-Bold.otf", 28), MUTED, a * clamp((g - 0.85) / 0.15), "lm")
    if t > 3.4:
        aa = ramp(t, 3.4, 0.6) * k
        text(d, (W / 2, 880), "Blizzard is the opponent where the gap is largest. Over all 30, the expert does better against 22.",
             F("Inter-SemiBold.otf", 31), FG, aa, "mm")
        text(d, (W / 2, 940), "Scored by pMARS, the game's official simulator.", F("Inter-Medium.otf", 28), MUTED, aa, "mm")
    return img

# ---------------------------------------------------------------- conclusion
RUNS = [("run C1", 0.665968), ("run C2", 0.740794), ("run C3", 0.691915), ("run C4", 0.727166), ("run C5", 0.739615)]

def x_end(t, dur):
    img, d, k = page(t, dur, "CONCLUSION", "Not just this run: all five fall short")
    bx0, bx1 = 330, 1560
    g = ramp(t, 0.7, 0.9)
    for i, (lab, r) in enumerate(RUNS):
        a = ramp(t, 0.5, 0.5) * k
        y = 250 + i * 72; hl = lab == "run C5"
        text(d, (120, y + 24), lab, F("Inter-Bold.otf" if hl else "Inter-SemiBold.otf", 30), FG if hl else MUTED, a, "lm")
        d.rounded_rectangle((bx0, y, bx1, y + 48), 10, fill=mix(TRACK, a))
        w = (bx1 - bx0) * r * g
        if w > 2: d.rounded_rectangle((bx0, y, bx0 + w, y + 48), 10, fill=mix(RED if hl else (236, 120, 120), a))
        text(d, (bx0 + w + 16, y + 24), f"{r:.3f}", F("Inter-Bold.otf", 28), RED, a * clamp((g - 0.85) / 0.15), "lm")
    ae = ramp(t, 1.8, 0.5) * k
    for yy in range(235, 610, 16):
        d.line((bx1, yy, bx1, yy + 8), fill=mix(GREEN, ae), width=4)
    text(d, (bx1 + 16, 270), "expert = 1", F("Inter-Bold.otf", 30), GREEN, ae, "lm")
    rows = [("Mean reward 0.713. None of the five reaches the expert.", F("Inter-Bold.otf", 38), FG),
            ("All five stopped with 12 to 29 of their 45 minutes unused.", F("Inter-SemiBold.otf", 32), FG),
            ("None opens with a quick search, the expert's first move.", F("Inter-SemiBold.otf", 32), FG)]
    for i, (s, f, c) in enumerate(rows):
        text(d, (W / 2, 690 + i * 62), s, f, c, ramp(t, 2.8 + i * 1.3, 0.6) * k, "mm")
    if t > 7.2:
        aa = ramp(t, 7.2, 0.6) * k
        panel(d, (220, 885, 1700, 965), aa, fill=(239, 244, 255), outline=ACC, r=16)
        text(d, (W / 2, 925), "The AI writes working programs fast, but stops short of expert-level design.",
             F("Inter-Bold.otf", 34), ACC, aa, "mm")
        text(d, (W / 2, 1015), "Every number in this demo comes from the runs' own log files.", F("Inter-Medium.otf", 26), MUTED, aa, "mm")
    return img

SCENES = [("w01_title", x_title, 7.5),
          ("w02_game", x_game, 10.0), ("w03_test", x_test, 12.0), ("w04_rules", x_rules, 13.0),
          ("w05_term", x_term, 9.5), ("w06_rep1", x_rep1, 14.0), ("w07_rep2", x_rep2, 18.0), ("w08_rep3", x_rep3, 15.0),
          ("w09_reveal", x_reveal, 12.0), ("w10_scale", x_scale, 12.5),
          ("w11_fight", x_fight, INTRO + SLOW + FAST + OUT), ("w12_stats", x_stats, 9.0),
          ("w13_end", x_end, 12.5)]

if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    for name, fn, dur in SCENES:
        if what in ("all", name):
            render(name, fn, dur); print("rendered", name, flush=True)
