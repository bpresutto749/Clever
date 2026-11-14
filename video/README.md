# Videos

Both videos are drawn frame by frame in Python (Pillow) and encoded with ffmpeg. Every number on
screen comes from this repository; nothing is filmed or hand-edited.

| video | length | what it shows |
|---|---|---|
| [`media/corewar_explainer.mp4`](../media/corewar_explainer.mp4) | 3 min 53 | the test we want, the game, why it works as a test, what we found, why the score can be trusted |
| [`media/corewar_demo.mp4`](../media/corewar_demo.mp4) | 2 min 54 | one real `harbor run` + OpenCode run (C5), replayed from its logs: the test, the run, the result, why the gap |

## Where the numbers come from

- Rewards, game scores and minutes: `runs/harbor/` (Harbor `result.json`, the verifier's
  `details.json` and `reward.txt`), `results/trajectories_harbor_v4.md`, FAILURES.md.
- The run replay (minutes, practice scores, log lines): run C5's event log and submission
  history in `runs/harbor/v4-opencode-opus-5.5/corewar-hill__X7kqQnj/`.
- The side-by-side game (the AI's program and the reference against Blizzard): replayed by
  `mars.py`, a small ICWS '94 simulator used only for drawing. `demo.py` asserts that each
  replayed game ends as pMARS says, and `check_mars.py` checks 90 rounds against pMARS (90/90).
- The 500-game tallies against Blizzard: the verifier's per-opponent results.

## Files

| file | content |
|---|---|
| `style.py` | palette, fonts, easing, panels, the judging-criteria rail, the memory background, `render()` |
| `explainer.py` | the presentation video, one function per scene |
| `demo.py` | the demo video, one function per scene |
| `mars.py` | the simulator that replays one game for the demo |
| `check_mars.py` | checks `mars.py` against pMARS |
| `build.py` | renders every scene and joins them into `media/` |

## Rebuild

Needs Python 3 with Pillow and NumPy, ffmpeg with libx264, the Inter fonts (`fonts-inter`) and
DejaVu Sans Mono, and pMARS built by `make pmars`.

```bash
make videos                        # both videos -> media/  (scenes in video/build/)
python3 video/build.py demo        # one video
python3 video/demo.py w11_fight    # one scene -> video/build/w11_fight.mp4
python3 video/check_mars.py        # the simulator used for drawing agrees with pMARS
```

Font locations can be overridden with `INTER_DIR` and `MONO_PREFIX`, and the scene folder with
`VIDEO_BUILD`.
