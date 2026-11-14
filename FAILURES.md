# FAILURES.md — what frontier agents get wrong on this task

## Evidence

**17 complete agent runs, in three versions of the environment, all 45 minutes.**

| version | visible opponents | primer | runs | where |
|---|---|---|---|---|
| **v3 (shipped)** | 30 black-box warriors from the same ladder as the hill (r = 0.83 with the hidden hill over 19 agent-level final warriors; `results/proxy_check.md`) | yes | Opus 5.5 J1–J5 | `runs/final-env/` |
| v2 | 10 black-box warriors (r = 0.57) | yes | Opus 5.5 H1–H5 | `runs/v2-small-pool/` |
| v1 | the same 10, with their source code visible | no | Opus 5.5 A, B, C, D2, E2; Opus + lessons G; Sonnet 5.5 F | `runs/opus-5.5*`, `runs/sonnet-5.5` |

**What each run leaves behind.**
- From v2 on, the arena server timestamps every submission and keeps its source
  (`runs/*/sidecar/`).
- For every run: the agent's working directory (`runs/*/workdirs/*.tar.gz`) and a summary of
  its own final report (`run_*.md`).

**Where the numbers come from.**
- `results/eval.md` (`make eval`; every score with its start-position standard error, about
  ±0.01 in reward);
- `results/trajectories*.md` and `results/stop_early*.md`.

**Outside evidence.** The final LLM warriors from CodeClash's CC:Ladder (July 2026).

## Headline

| | visible pool | hidden-hill score | reward (0 = Dwarf, 1 = human reference) |
|---|---|---|---|
| human reference (Toxic, fixed before any run) | 0.507 (v3 pool) | 0.487 | 1.000 |
| **Opus 5.5, v3, 5 runs** | **0.349–0.455** | 0.320–0.394 | **mean 0.671, 95% CI [0.55, 0.79]**; all ≤ 0.728 |
| Opus 5.5, v2, 5 runs | | 0.309–0.401 | mean 0.595, CI [0.44, 0.75] |
| Opus 5.5, v1, 5 runs | | 0.372–0.465 | mean 0.746, CI [0.61, 0.88] |
| Opus 5.5 + lessons (v1, 1 run) | | 0.390 | 0.716 |
| Sonnet 5.5 (v1, 1 run) | | 0.195 | 0.140 |
| CodeClash ladder warriors (Opus 4.8, GPT-5.5, Sonnet 5, Gemini 3.5 Flash) | | 0.083–0.332 | 0.000–0.543 |

None of the 17 runs reached the reference.
- The closest is v1's D2 at 0.936. Its hill score is 0.465 against 0.487, a margin of about
  four combined standard errors.
- In v3, the margins are 0.27–0.49 in reward.

Rewards use the Dwarf anchor (README, "The zero point was changed after the fact"). It was
adopted after all runs had been scored, and every reward was recomputed from the stored raw
scores (`results/rescored_dwarf_anchor.md`). The order of the runs is unchanged.

## F1. A plateau below human level, even on the opponents the agent can see

In v3, the visible pool is a faithful proxy: 30 warriors drawn from the same ladder as the
hidden hill, with the same strength spread. Every agent's final warrior scores below the
human reference *on that visible pool*:

| | J1 | J2 | J3 | J4 | J5 | reference |
|---|---|---|---|---|---|---|
| visible (30 sparring) | 0.407 | 0.455 | 0.349 | 0.389 | 0.392 | **0.507** |
| hidden hill | 0.394 | 0.375 | 0.320 | 0.393 | 0.394 | **0.487** |

So the shortfall is not missing information. The agents can measure, at will and with the
scoring settings, that their warrior is weaker than a strong human one against
representative opposition, and they cannot close the gap.

**Most of the progress comes from the first draft.** Every v3 submission was scored on both
pools (`results/trajectories.md`):

| run | first real draft (visible ≥ 0.30) → final: minutes | visible | hidden |
|---|---|---|---|
| J1 | 3.4 → 33.1 | 0.325 → 0.407 | 0.351 → 0.394 (best: 0.416 at minute 4.4) |
| J2 | 5.1 → 23.9 | 0.387 → 0.455 | 0.323 → 0.375 |
| J3 | 6.2 → 23.5 | 0.342 → 0.349 | 0.329 → 0.320 |
| J4 | 15.4 → 30.9 | 0.381 → 0.389 | 0.398 → 0.393 |
| J5 | 4.9 → 32.2 | 0.365 → 0.392 | 0.396 → 0.394 |

- After the first real draft, the remaining 15–30 minutes add +0.038 visible and +0.016
  hidden on average.
- In every run, the final submission is not the agent's best on the hidden hill. For J2, J4
  and J5 the difference is within noise.
- J1's is not: it had reward 0.79 at minute 4 and finished at 0.73.

## F2. Converging on one archetype and abandoning composites

All five v3 runs built p-space selectors (switch strategy per opponent or after losses), and
several built quick-scan openings. All of them found these weaker than their tuned single
warrior and dropped them, giving the same reason in their own words:
- J1: "the bigger footprint and switching cost cancel the gain";
- J2: "the longer code weakens the scanner, and selection does not make up for it";
- J4: "the decision code, not empty, serves as a target for scanners. So I abandoned
  p-space";
- J5: "the code is about 86 lines, so it is easier to find".

**What they submitted instead.**
- J1: a silk paper.
- J2: a scanner.
- J3: a stone.
- J4, J5: a paper with a stone running in parallel, the simplest possible combination.

The same happened in v1: four lone scanners and one lone paper.

The human reference is a composite: its strategy line reads "qscan -> paper/imp". By a
keyword count of the hill's own strategy lines, qscan appears in 14 of 30 hill warriors and
imps in 10.

The agents diagnose correctly why a naive composite loses: footprint, decision overhead,
boot timing. They then treat that as a reason to stop rather than as the engineering problem
to solve.

## F3. With a small visible set, they optimise the visible score, and it does not transfer

v2 is the same environment with 10 visible opponents (r = 0.57 with the hidden hill). There:
- the visible score rose by **+0.084** on average after the first real draft;
- the hidden score moved **−0.006** (`results/trajectories_v2.md`);
- run H2 matched the reference's visible score (0.488 vs 0.498) while scoring 0.319 vs 0.487
  hidden;
- every agent projected its hidden score from its sparring score, and all five projections
  overshot, by 0.02–0.17 in hill score (H2: projected 0.488, actual 0.319).

With v3's faithful pool, the same behaviour transfers partly: +0.038 visible, +0.016 hidden.

The agents optimise whatever they can see, with no allowance for how representative it is.
They never built a held-out set, although the primer says that "a warrior is only as good as
the set of opponents it was tested against".

## F4. Naming the noise and selecting on it anyway

Across v2 and v3, most runs wrote that their best-of-many number was inflated, and then
submitted it:
- H1: "the 200-round figure is optimistic";
- H2: "0.488 is probably a bit flattering";
- H3: "probably a lucky draw";
- J2: "differences of 0.01 between variants are probably noise with respect to the hidden
  hill";
- J4: "its lead over the paper alone (+0.003) is at noise level".

None reports holding out any sparring warrior, or any of its own warriors, for the final
choice.

## F5. Stopping early with budget left

| | v3: J1 | J2 | J3 | J4 | J5 | v2: H1–H5 | v1: A–E2, G | v1: F (Sonnet) |
|---|---|---|---|---|---|---|---|---|
| minutes used of 45 | ~35 | ~30 | ~27 | ~33 | ~33 | 27–32 | 25–28 | ~8 |

All 17 runs stopped with 10–37 minutes unused, convinced they had converged. That includes
G, whose instructions said "use the whole time budget".

## F6. Telling them does not fix it

**Run G (v1)** received a lessons section derived from F1–F5: validation discipline, an
archetype test set, composites, the whole budget.
- It followed the method advice and built a composite.
- It stopped at 28 minutes.
- It scored 0.716, inside the fresh runs' range.

**v2 and v3** give every run a strategy primer that describes the archetypes, the classic
triangle, composites and testing practice. The failures persist.

Prompt-level knowledge does not close this gap. That is why the upgrade path is training on
environment experience (TRAINING.md).

## The stop-early baseline

Each run's last accepted submission at a cutoff (`results/rescored_dwarf_anchor.md`, v3):

| | 5 min | 10 min | 20 min | final |
|---|---|---|---|---|
| mean reward of the 5 v3 runs | 0.50 | 0.57 | 0.69 | 0.67 |

**The early drafts are not trivial programs.**
- Trivial and textbook programs earn 0.00–0.24.
- Doing nothing earns 0.
- A frontier model's 5-minute draft is a working silk paper or stone, which earns about half
  the reference's reward.

**After 20 minutes, the reward stops growing.** That is F1 seen from the other side: the
reward tracks warrior strength, and the agents stop getting stronger. The reference shows
where strength can go: 1.0.

## Why this matters beyond Core War

Agents increasingly write code that is judged against adversaries or distributions they
cannot fully see:
- exploit and defence code;
- trading and bidding strategies;
- game agents;
- code that must survive fuzzing or red-teaming.

This task isolates that situation:
- **exact:** the simulator is the judge;
- **cheap:** a few seconds per evaluation;
- **anchored:** decades of human expert programs, so "stronger" is a measured fact.

The agent's behaviour is the failure:
- it plateaus at the first archetype that works;
- it abandons the harder composite designs that experts use, after diagnosing exactly why
  its first attempt failed;
- it optimises whatever test set it is given;
- it stops while budget remains.
