# Videos

All the videos are drawn frame by frame in Python (Pillow) and encoded with ffmpeg. Every number on
screen comes from this repository; nothing is filmed or hand-edited.

| video | length | what it shows |
|---|---|---|
| [`media/corewar_pitch_1min59.mp4`](../media/corewar_pitch_1min59.mp4) | 1 min 59 | **the pitch**: the test we want, the game, the test, what we found (the gap, one run, one game, three everyday mistakes), why the score can be trusted |
| [`media/corewar_demo_full.mp4`](../media/corewar_demo_full.mp4) | 6 min 42 | **the full demo**: the same argument in detail, with one real `harbor run` + OpenCode run (C5) replayed from its logs, the real test, and one real game; shown as a screen demo (dark app window, recording timecode) |
| [`media/corewar_explainer.mp4`](../media/corewar_explainer.mp4) | 3 min 53 | shorter cut: the presentation alone |
| [`media/corewar_demo.mp4`](../media/corewar_demo.mp4) | 3 min 15 | shorter cut: the run alone (the test, the run, the result, why the gap) |

The full demo uses the same scenes in a dark theme (`VIDEO_THEME=dark`, set by `demo_full.py`). The colours mean the same thing everywhere: red is the AI, green is the human expert, blue is
everything else (headings, opponents, the criteria rail).

## Where the numbers come from

- Rewards, game scores and minutes: `runs/harbor/` (Harbor `result.json`, the verifier's
  `details.json` and `reward.txt`), `results/trajectories_harbor_v4.md`, FAILURES.md.
- The run replay (minutes, practice scores, log lines): run C5's event log and submission
  history in `runs/harbor/v4-opencode-opus-5.5/corewar-hill__X7kqQnj/`.
- The side-by-side game (the AI's program and the reference against Blizzard): replayed by
  `mars.py`, a small ICWS '94 simulator used only for drawing. `demo.py` asserts that each
  replayed game ends as pMARS says, and `check_mars.py` checks 90 rounds against pMARS (90/90).
- The 500-game tallies against Blizzard: the verifier's per-opponent results.
- "0 of 27 AI runs": the 5 shipped (v4) Harbor runs and the 22 earlier ones listed in FAILURES.md.

## Files

| file | content |
|---|---|
| `style.py` | palette, fonts, easing, anti-aliased shapes, panels, the judging-criteria rail, the memory background, `render()` |
| `explainer.py` | the presentation's scenes, one function per scene |
| `demo.py` | the run's scenes (the test, the replay, the result, the game), shared by the demo and the full demo |
| `pitch.py` | the pitch: eleven scenes of its own, 119 seconds |
| `demo_full.py` | the full demo: assembles scenes from `explainer.py` and `demo.py` |
| `mars.py` | the simulator that replays one game for the demo |
| `check_mars.py` | checks `mars.py` against pMARS |
| `audit.py` | checks a video without encoding it: text out of frame, overlapping text, and reading time per scene |
| `build.py` | renders every scene and joins them into `media/` |

## Rebuild

Needs Python 3 with Pillow and NumPy, ffmpeg with libx264, the Inter fonts (`fonts-inter`) and
DejaVu Sans Mono, and pMARS built by `make pmars`.

```bash
make videos                        # checks, then all the videos -> media/  (scenes in video/build/)
python3 video/build.py pitch       # one video
python3 video/demo.py w11_fight    # one scene -> video/build/w11_fight.mp4
python3 video/audit.py pitch 4     # layout and reading-time check, at 4 words per second
python3 video/check_mars.py        # the simulator used for drawing agrees with pMARS
```

Font locations can be overridden with `INTER_DIR` and `MONO_PREFIX`, and the scene folder with
`VIDEO_BUILD`.
