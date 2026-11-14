#!/usr/bin/env python3
"""The full demo video (under 7 minutes): the presentation's structure with the real run inside it.
1 the test we need, 2 the game, 3 how the test works, 4 what we found (all five runs, then run C5
replayed, then one real game, then what goes wrong across the runs), 5 can the score be trusted,
then training and the close.
It only assembles scenes: the presentation's come from explainer.py, the run's from demo.py.
usage: python video/demo_full.py [all | <scene name>]   -> video/build/<scene>.mp4"""
import sys
from functools import partial
from PIL import Image
from style import F, LINE, FG, MUTED, RED, ACC, BLUE, ramp, mix, text, render, base, head, core_bg
import explainer as ex
import demo as dm

# here part 3 also explains how the test runs, so the presentation's part-3 scenes take its name
P3, P4 = "3 · HOW THE TEST WORKS", "4 · WHAT WE FOUND"
RUN = P4 + "  ·  RUN C5"
part3 = lambda scene: partial(scene, kicker=P3)

def s_game(t, dur):
    img, d, k = base(t, dur, set())
    head(d, t, "2 · THE GAME: CORE WAR", "A game where programs fight", k)
    rows = [("Two programs share one", 0), ("memory of 8,000 cells.", 0), ("They take turns.", 1),
            ("Each tries to crash", 2), ("the other.", 2)]
    for (s, g), y in zip(rows, [330, 390, 480, 570, 630]):
        text(d, (120, y), s, F("Inter-SemiBold.otf", 48), FG, ramp(t, 0.8 + g * 1.5, 0.7) * k)
    if t > 5.6:
        text(d, (120, 740), "The last one running wins.", F("InterDisplay-Black.otf", 54), ACC, ramp(t, 5.6, 0.7) * k)
        text(d, (120, 815), "Both still running at the time limit: a draw.", F("Inter-Medium.otf", 34), MUTED, ramp(t, 7.0, 0.7) * k)
    pa = ramp(t, 0.6, 0.8) * k
    if pa > 0:
        core = core_bg(t * 0.55, 1.0).resize((820, 462), Image.BILINEAR)
        img.paste(core, (980, 320), Image.new("L", core.size, int(255 * pa)))
        d.rounded_rectangle((976, 316, 1804, 786), 14, outline=mix(LINE, pa), width=3)
        text(d, (980, 300), "the shared memory, live", F("Inter-SemiBold.otf", 24), MUTED, pa, "ls")
        for j, (c, lab) in enumerate(((RED, "program A drops bombs"), (BLUE, "program B copies itself"))):
            d.rounded_rectangle((980 + j * 410, 812, 1004 + j * 410, 836), 5, fill=mix(c, pa))
            text(d, (1016 + j * 410, 824), lab, F("Inter-SemiBold.otf", 26), FG, pa, "lm")
    return img

bridge = ex.bridge
SCENES = [("f01_title", ex.s_title, 7.0),
          ("f02_question", ex.question(["The test we need", "The game", "How the test works", "What we found", "Can we trust it?"]), 9.5),
          ("f03_goal", ex.s_goal, 11.0), ("f04_need", ex.s_need, 12.0),
          ("f05_bridge", bridge("We found it in a game from 1984:", set(), "Core War, a game you play by writing programs."), 4.5),
          ("f06_game", s_game, 11.5), ("f07_player", ex.s_player, 10.5), ("f08_lang", ex.s_lang, 10.5), ("f09_rps", ex.s_rps, 11.0),
          ("f10_bridge", bridge("So how do we turn it into a test?", set()), 3.4),
          ("f11_test", dm.test(P3), 15.0), ("f12_rules", dm.rules(P3), 15.5),
          ("f13_fits", part3(ex.s_fits), 12.5), ("f14_tests", part3(ex.s_tests), 9.5),
          ("f15_space", part3(ex.s_space), 9.5), ("f16_design", part3(ex.s_design), 10.5),
          ("f17_bridge", bridge("So how do the best AI agents do?", {"gap"}), 3.4),
          ("f18_term", dm.term(P4, "How did they score?"), 9.5), ("f19_result", ex.s_result, 12.0),
          ("f20_bridge", bridge("Let's replay one run, from its own logs.", {"diff"},
                                "Run C5: the one that came closest to the expert in practice."), 4.6),
          ("f21_rep1", dm.replay(RUN + ", MINUTES 0 TO 3", "First, two quick tries", 0.0, 3.2), 20.0),
          ("f22_rep2", dm.replay(RUN + ", MINUTES 3 TO 12", "Then, it polishes one idea", 3.2, 12.5), 17.5),
          ("f23_rep3", dm.replay_end(RUN + ", MINUTES 12 TO 16"), 17.0),
          ("f24_reveal", dm.reveal(RUN), 13.0), ("f25_scale", dm.scale(RUN), 13.0),
          ("f26_fight", dm.fight(RUN), dm.INTRO + dm.SLOW + dm.FAST + dm.OUT), ("f27_stats", dm.stats(RUN), 9.5),
          ("f28_bridge", bridge("What goes wrong, across all five runs?", {"diff"}), 3.4),
          ("f29_clock", ex.s_clock, 11.0), ("f30_learned", ex.s_learned, 14.0), ("f31_real", ex.s_real, 12.5),
          ("f32_bridge", bridge("Can the score be trusted?", {"integ", "craft"}), 3.3),
          ("f33_cheat", ex.s_cheat, 11.0), ("f34_craft", ex.s_craft, 10.0),
          ("f35_bridge", bridge("Last question: can an AI learn from this game?", {"tie"}), 3.4),
          ("f36_train", ex.s_train, 10.5), ("f37_close", ex.s_close, 9.0)]

if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    for name, fn, dur in SCENES:
        if what in ("all", name):
            render(name, fn, dur); print("rendered", name, flush=True)
