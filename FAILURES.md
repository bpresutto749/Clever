# FAILURES.md — what frontier agents get wrong on this task

## Evidence

**Final environment** (`runs/final-env/`). 5 fresh Claude Opus 5.5 runs (H1–H5) under the
exact conditions of the Harbor task:
- 45 minutes;
- pMARS and the documentation, including the strategy primer;
- 10 black-box sparring warriors, reached through the arena server;
- every submission timestamped and kept by the server.

**Version 1** (`runs/opus-5.5*`, `runs/sonnet-5.5`). 7 earlier runs: 5 Opus, 1 Opus with
lessons, 1 Sonnet 5.5. The sparring sources were visible and there was no primer. These runs
are rescored at 500 rounds and kept as supporting evidence.

**Outside evidence.** The 4 final LLM warriors from CodeClash's CC:Ladder (July 2026).

**Where the numbers come from:**
- `results/eval.md` (`make eval`);
- `results/trajectories.md` (every submission scored on sparring and on the hill);
- `results/stop_early.md`.

## Headline

| | hidden-hill score | reward (0 = one-line imp, 1 = human reference) |
|---|---|---|
| human reference (Toxic, fixed before any run) | 0.487 | 1.000 |
| **Opus 5.5, final environment, 5 runs** | 0.309–0.401 | **mean 0.572, 95% CI [0.41, 0.74]**; every run ≤ 0.733 |
| Opus 5.5, version 1, 5 runs | 0.372–0.465 | mean 0.732, 95% CI [0.59, 0.88] |
| Opus 5.5 + lessons, version 1 (1 run) | 0.390 | 0.700 |
| Sonnet 5.5, version 1 (1 run) | 0.195 | 0.093 |
| CodeClash ladder warriors (Opus 4.8, GPT-5.5, Sonnet 5, Gemini 3.5 Flash) | 0.083–0.332 | 0.000–0.518 |

Each score's start-position standard error is about ±0.003 in hill score, or ±0.01 in reward
(`make eval`).
- In the final environment, the reference beats every run by 0.27–0.55 in reward.
- The smallest margin anywhere is version-1 run D2's: 0.067, about five combined standard
  errors.

The agents are not short of means:
- they write working Redcode;
- they have the exact scoring simulator;
- they each ran between 139 and 527 sparring battles;
- in the final environment, they have a primer covering the archetypes, the classic triangle
  and composite designs.

The failures below are decisions.

## F1. Optimising the visible set: the agent's own trajectory shows it

The arena server keeps every submission with a timestamp. We scored all 26 of them on both
the sparring pool (what the agent sees) and the hidden hill (what it is rewarded on). The
sparring score rises with every submission in every run, because agents submit only
improvements. The hidden score does not follow:

| run | first real draft (sparring ≥ 0.30): minute, sparring → hidden | final: minute, sparring → hidden | change, sparring / hidden |
|---|---|---|---|
| H1 | 6.2: 0.377 → 0.394 | 19.3: 0.436 → 0.401 | +0.059 / +0.007 |
| H2 | 2.8: 0.341 → 0.330 | 28.5: 0.488 → 0.319 | +0.147 / −0.011 |
| H3 | 6.2: 0.316 → 0.331 | 28.7: 0.376 → 0.309 | +0.060 / −0.022 |
| H4 | 2.7: 0.318 → 0.345 | 30.1: 0.421 → 0.329 | +0.103 / −0.016 |
| H5 | 1.4: 0.360 → 0.378 | 18.3: 0.409 → 0.388 | +0.049 / +0.010 |
| **mean** | | | **+0.084 / −0.006** |

"Real draft" is set at a sparring score of 0.30 because a one-line imp gets 0.18 on that pool.

After their first real draft, agents spend 13–27 minutes raising their visible score
by 0.08 on average. That is worth about 0.26 of reward if it transferred; on the hidden hill
it is worth nothing.

**Some runs make themselves worse.**
- In 3 of the 5 runs, the final submission is not the agent's best on the hidden hill.
- H4's best hidden score came at minute 13 (reward 0.66). After 17 more minutes of sparring
  tuning, it ended at 0.51.
- H3's best was its first real draft, at minute 6.

**H2 reaches the reference's visible level without its hidden level.** Its sparring score
(0.488) is level with the human reference's on the same pool (0.498). Its hidden score is
0.319, against 0.487. The human warrior loses 0.011 from sparring to hill; the five final
runs lose 0.021–0.169.

**The agents' own forecasts are miscalibrated in the same direction.** Each run converted its
sparring score into an expected reward. All five forecasts were too high:

| | H1 | H2 | H3 | H4 | H5 |
|---|---|---|---|---|---|
| forecast | 0.84 | ~1.0 | ~0.6 | 0.80 | 0.76 |
| actual | 0.73 | 0.48 | 0.45 | 0.51 | 0.70 |

The same pattern is in version 1: the run with the highest sparring score there (B, above the
reference on sparring) was the lowest Opus run on the hill.

## F2. Knowing about selection bias, and selecting on it anyway

Four of the five final runs wrote, in their own reports, that their number was inflated by
choosing the best of many noisy variants:
- H1: "the 200-round figure is optimistic";
- H2: "0.488 is probably a bit flattering … neighbouring settings give 0.44–0.45";
- H3: "0.376 is probably a lucky draw";
- H4: "differences of ±0.02 are of the order of the noise".

Each then submitted that best-of-many variant anyway. None reports holding out any sparring
warrior, or any of its own warriors, as a validation set for the final choice. The primer
says: "a warrior is only as good as the set of opponents it was tested against … do not
trust differences that are smaller than the noise".

## F3. Composites that learn the sparring pool

With the primer, 4 of the 5 final runs built p-space selectors that pick a component per
opponent (H2, H3, H4, H5). Version 1 had no composite among its 5 fresh runs. The selectors
were tuned on the 10 sparring warriors:
- exploration length;
- scoring weights;
- which arms to include.

The four selectors score 0.45–0.70. The only lone warrior (H1, a 13-line paper) scored
highest (0.73).

The reference is a composite too (qscan → paper/imp). The failure is not choosing composites;
it is fitting the combination to what is visible.

## F4. Stopping early with budget left

| run | H1 | H2 | H3 | H4 | H5 | v1: A | B | C | D2 | E2 | F | G |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| minutes used of 45 | ~31 | ~29 | ~30 | ~32 | ~27 | ~28 | ~27 | ~28 | ~25 | ~28 | ~8 | ~28 |

All 12 runs stopped with 13–37 minutes unused. That includes G, whose instructions said "use
the whole time budget". Given F1, more time spent the same way would not have helped. The
time was available for validation, and none of the runs used it that way.

## F5. Being told does not fix it (version 1, one run)

Run G received a four-point lessons section (`task_src/lessons.md`): validation discipline,
an archetype test set with random positions, composites, and using the whole budget.
- It followed the method advice.
- It built a composite.
- It still stopped at 28 minutes.
- It scored 0.700, inside the fresh runs' range.

The final environment's primer carries the same general advice, and F1–F3 persist. Prompting
does not close this gap. That is why the upgrade path is training on environment experience
(TRAINING.md).

## The stop-early baseline, read correctly

Scoring each run's last accepted submission at a cutoff (`results/stop_early.md`):

| | 5 min | 10 min | 20 min | final |
|---|---|---|---|---|
| mean reward of the 5 final runs | 0.35 | 0.55 | 0.59 | 0.57 |

**Before 5 minutes, an agent has little.** Two of the five runs had only a placeholder dwarf
or a weak first draft (reward 0), and the textbook drafts score 0.00–0.20.

**After 10 minutes, the reward stops growing.** The 10-minute baseline is a real Opus draft,
and the remaining 35 minutes add nothing on average. This is F1 seen from the other side, not
a weakness of the reward: the reference earns 1.0, and no trivial program earns more than
0.20.

## Why this matters beyond Core War

Agents increasingly write code that is judged against adversaries or distributions they
cannot see:
- exploit and defence code;
- trading and bidding strategies;
- game agents;
- code that must survive fuzzing or red-teaming.

They get a small visible test set and a simulator, and they are told the test set is not the
target. This task isolates exactly that:
- **exact:** the simulator is the judge;
- **cheap:** a few seconds per evaluation;
- **anchored:** decades of human expert programs, so "stronger" is not hypothetical.

The agent's behaviour is the failure. Even when told, it:
- climbs the visible score;
- discounts its own warnings about noise and selection;
- fits its adaptive logic to what it sees;
- stops when the visible number stops moving.

These are the behaviours that make agent-written code pass the visible tests and fail on the
hidden ones.
