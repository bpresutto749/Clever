# Hill Climb: frontier agents vs 30 years of human Core War

*Break the Agent (AfterQuery), Junction 2026 · Harbor task `harbor/corewar-hill` · run it
with `harbor run -p harbor/corewar-hill -a opencode -m <provider/model>` (RUN_HARBOR.md)*

**Headline.** On the shipped task, through `harbor run` + OpenCode, Claude Opus 5.5 scores
**0.713** (5 runs, all ≤ 0.741, 95% CI 0.67–0.75) against **1.000** for the human reference
and 0.000 for doing nothing. Giving it a clock tripled the time it worked and did not move
the score.

## In three paragraphs

**What the agent has to do.** Write an original Core War warrior in Redcode and submit it
through the environment's MCP server. Core War is the 1984 programming game in which two
assembly programs share a circular memory and each tries to make the other crash. The
warrior is scored against a **hidden hill of 30 human-written King-of-the-Hill warriors**,
using the exact simulator (pMARS). To work with, the agent gets:
- that simulator;
- the language reference and a strategy primer;
- **30 black-box sparring opponents** drawn from the same ladder as the hill, with the same
  strength spread;
- a clock at the end of every server reply: minutes used and minutes left of the 45.

**Why it is hard.** Everything needed is available: rules, an exact simulator, a strategy
primer, and a representative test set whose scores track the hidden hill (r = 0.83 over 19
agent-level warriors, `results/proxy_check.md`). Frontier agents still plateau below a human expert's warrior,
**even on the opponents they can see**:
- **On the visible pool**, they reach 0.34–0.49, against 0.507 for the human reference.
  On the hidden hill, the same warriors stay at 0.32–0.40, against 0.487.
- **They converge on a single tuned archetype.** They try composite designs, find them weaker
  than that archetype, and abandon them, although the strongest human warriors are
  composites.
- **More time does not help them.** Without a clock (v3), the five Harbor runs stopped
  after 4–14 minutes, and three said they had run out of time ("I ran out of the 45
  minutes"). With a clock in every reply (v4, shipped), they worked 16–33 minutes, played
  up to 637 battles, and their reward did not move: 0.704 → 0.713. One stopped "with about
  22 minutes left on the clock".
- **They mistake the visible score for the real one.** In v4, two of the five runs spent
  their extra minutes raising the visible score and lowering the hidden one (C1: visible
  0.390 → 0.437, hidden 0.391 → 0.373), and the best visible score, 0.489, is 0.018 from
  the reference on the visible pool and 0.089 below it on the hidden hill (FAILURES.md).

This is the shape of agent work on anything judged against hidden, adaptive opposition:
exploit and defence code, bidding agents, code under fuzzing.

**How it is scored.**
- **Hill score.** Each warrior plays 500 rounds against each of the 30 hidden warriors (3
  points per win, 1 per tie). The hill score is the mean points per round / 3.
- **Reward.** The verifier writes `reward = clip((hill − 0.1475) / (0.4866 − 0.1475), 0, 1)`
  to `/logs/verifier/reward.txt`.
  - Dwarf gets 0. It is A. K. Dewdney's classic bomber and the example warrior in the agent's
    own documentation.
  - The human reference gets 1. It is Toxic, by John Metcalf, Elo #1 of 264 humans, fixed
    before any agent run.
  - The upper clip at 1 is the challenge's [0, 1] rule; no run comes near it.
- **Reproducibility.** Scores are deterministic: pMARS fixed position series, standard error
  about ±0.01.
- **Copies.** A near-copy of any of 581 published warriors scores 0.
- **The zero point was changed after the fact.** Until all 17 recorded runs had been scored,
  including the five final runs (J1–J5), the zero point was a one-line imp (`mov.i #0, 1`,
  hill 0.1650). It is now Dwarf (hill 0.1475).
  - Why: the imp never kills anything and scores only through ties, which makes it a
    degenerate zero. Dwarf is the canonical first warrior and the very example the agent is
    handed, so reward 0 now reads "no better than the textbook example".
  - Every reward was recomputed from the stored raw hill scores, without rerunning any agent
    (`exploits/rescore_anchor.py` → `results/rescored_dwarf_anchor.md`).
  - Both anchors are affine maps of the same raw score, so the order of the runs is unchanged.
    Every agent's reward rises slightly (v3 mean 0.653 → 0.671), and the gap to the reference
    in raw hill score is untouched.

## Results

| | visible pool (30) | hidden-hill score | reward |
|---|---|---|---|
| **Human reference** (Toxic) | 0.507 | 0.487 | **1.000** |
| **Claude Opus 5.5, shipped environment (v4, with clock), `harbor run` + OpenCode, 5 runs (agents worked 16–33 min)** | 0.382–0.489 | 0.373–0.399 | **0.713** (95% CI 0.67–0.75; all 5 ≤ 0.741) |
| Claude Opus 5.5, v3 (no clock), `harbor run` + OpenCode, 5 runs (agents stopped after 4–14 min) | 0.342–0.422 | 0.362–0.398 | 0.704 (CI 0.65–0.76; all 5 ≤ 0.739) |
| Claude Opus 5.5, v3, local Claude agent harness, 5 runs (25–35 min used) | 0.349–0.455 | 0.320–0.394 | 0.671 (CI 0.55–0.79; all 5 ≤ 0.728) |
| Claude Opus 5.5, version 2 (10 black-box sparring), 5 runs | — | 0.309–0.401 | 0.595 (CI 0.44–0.75) |
| Claude Opus 5.5, version 1 (10 visible sparring sources, no primer), 5 runs | — | 0.372–0.465 | 0.746 (CI 0.61–0.88) |
| Claude Sonnet 5.5, version 1, 1 run | — | 0.195 | 0.140 |
| CodeClash ladder warriors, July 2026 (Opus 4.8 / GPT-5.5 / Sonnet 5 / Gemini 3.5 Flash) | — | 0.083–0.332 | 0.000–0.543 |
| Best trivial warrior (5-line stone); one-line imp | — | 0.228; 0.165 | 0.237; 0.052 |
| Qwen2.5-Coder-7B-Instruct after 4 rounds of expert iteration on the environment (base model: 0.000), 64 samples | — | 0.124 mean | 0.032 mean (best 0.060) |
| Dwarf (the documentation's example; a published warrior, so as a submission the copy gate gives 0) | — | 0.147 | 0.000 |
| Do-nothing | — | 0.000 | 0.000 |

None of the 27 Opus or Sonnet runs, across four environment versions and two harnesses,
reached the reference. The best reached 0.936. Every number comes from `make eval`
(`results/eval.md`). For the Harbor runs, `make eval` rescores the ten submissions outside
Docker and matches the reward the Harbor verifier wrote (to the 4 decimals `eval.md` reports) (`runs/harbor/`,
`results/trajectories_harbor*.md`). Run histories, agents' working directories and their own
reports are in `runs/`.

**Real Harbor runs** (Harbor 0.25.0, Docker Desktop, macOS arm64, egress control on;
logs in `runs/harbor/`):

| `harbor run -p harbor/corewar-hill …` | reward | wall time | cost |
|---|---|---|---|
| `-a oracle` | 1.000 | 1 min 09 | — |
| `-a nop` | 0.000 | 27 s | — |
| `-a opencode -m anthropic/claude-opus-5-5 -k 1` | 0.739 | 5 min 33 (agent 4.1 min) | $0.50 |
| `-a opencode -m anthropic/claude-opus-5-5 -k 4` (4 concurrent trials) | 0.736, 0.732, 0.681, 0.632 | 15 min 45 (agents 4.4–13.6 min) | $2.04 |
| **v4** `-a oracle` | 1.000 | 39 s | — |
| **v4** `-a opencode -m anthropic/claude-opus-5-5 -k 5` (4 concurrent, then 1) | 0.741, 0.740, 0.727, 0.692, 0.666 | 42 min 47 (agents 16.5–32.7 min) | $11.75 |
| **v4.1** (as shipped) `-a oracle`; `-a nop` | 1.000; 0.000 | 49 s; 32 s | — |

The first five agent rows are v3 (OC1–OC5), the last v4 (C1–C5). Per-run details, and which
trial directory is which run, are in `runs/harbor/README.md`.

**v4 = v3 + the clock.** The clock was added after the v3 Harbor runs, in which agents
stopped after 4 minutes saying they had run out of time: an agent with no way to read the
time left could argue the budget was withheld. The reward, the hill, the sparring pool, the
verifier and the rest of the instruction are unchanged (DECISIONS.md).

Every OpenCode trial is flagged `NonZeroAgentExitCodeError`: OpenCode prints an `EPIPE: broken
pipe` error when it starts and exits with code 1 after the agent finishes normally (the
last event of every trial is `step_finish`, reason `stop`). The verifier still runs and the
reward stands.
An earlier attempt that failed on an empty API credit balance, before any model call, is
kept in `runs/harbor/opencode-opus-5.5-no-credit` and not counted.

## How the environment works

```
┌──────────── agent container (main) ─────────────┐     ┌────── MCP sidecar "arena" ──────┐
│ OpenCode / any Harbor agent                     │ MCP │ get_rules  list_sparring (ids)  │
│ /app/bin/pmars   /app/doc (+ strategy primer)   │────▶│ battle  battle_custom           │
│ /app/tools/spar.py  /app/tools/battle.py        │     │ submit (last accepted counts)   │
│ /app/submission.red (fallback)                  │     │ status · clock  → /results/*    │
└──── network: allowlist (model APIs only) ──────┘     │ 30 sparring warriors, black box │
                                                         └──────────────┬──────────────────┘
          artifacts (re-created at their source paths in the verifier): │
          /results/submission.red, events.jsonl, history/, /app/submission.red
                                                                         ▼
                ┌──── verifier container (separate, no network) ────────────────────┐
                │ hidden hill (30) · near-copy gate (581 published warriors)        │
                │ battle-context assembly · sanitised source · pMARS as `nobody`    │
                │ → /logs/verifier/reward.txt  +  details.json                      │
                └───────────────────────────────────────────────────────────────────┘
```

**Integrity.** The agent never sees hill or sparring code or names, and gets no hill
feedback. Each of the following scores 0 and has a regression case in `make exploits`:
- copies of published warriors, including padded, retuned or embedded copies;
- assembly-context tricks (`WARRIORS` / `ROUNDS`);
- pMARS hangs and oversized files;
- planted files in `/logs/artifacts`.

The oracle reaches exactly 1.0 only through the MCP path. Two adversarial reviews found real
holes (35/100, then 50/100); every one is closed (DECISIONS.md). EXPLOITS.md lists every
attack and the remaining risks.

## Reproduce

```bash
make test        # regression tests: anchors, determinism, sanitiser, gate, assembly context, isolation
make eval        # no Docker: reference, baselines, every recorded run (with standard errors)
make exploits    # exploit and simple-strategy cases through the real verifier, plus stop-early tables
make trajectories  # every submission of every run on its visible pool and on the hidden hill
make task lint   # regenerate harbor/corewar-hill(-public) from sources and lint them
make harbor-reference && make harbor-nop && make harbor-agent MODEL=<provider/model>   # Docker + API key
```

## Files

| file | content |
|---|---|
| FAILURES.md | the evidence for each failure mode, in tables and in the agents' own words |
| EXPLOITS.md | every attack on the reward and what stops it |
| TRAINING.md | training a small model on the environment: Qwen2.5-Coder-7B, expert iteration, base 0.000 → 0.032 on the hidden hill |
| DECISIONS.md | what was fixed before the agent runs, and what changed after which review |
| RUN_HARBOR.md | Harbor commands and what to look at in a run |
| CREDITS.md | pMARS (GPL), CodeClash, Digital Red Queen, and the warrior authors |

## Honest limits

- **How the agent runs were made.** The 17 earlier runs were made with Claude agents in a
  local copy of the arena, with the same instruction, simulator and sparring server
  (reached through `tools/spar.py`, which calls the same MCP tools). Only the ten runs
  in `runs/harbor/` went through Harbor + OpenCode. No non-Claude model was run.
- **The copy gate was corrected once after the runs (v4.1).** It had flagged one of the 85
  recorded submissions, run C1's first (a 12-instruction silk paper, replaced 18 minutes
  later), because its structure matched one building block of a larger published warrior.
  The rule given to the agent allows published techniques, so the gate now flags structural
  matches only against half or more of a published warrior. No reported reward changed, and
  every exploit case still scores 0 (DECISIONS.md, EXPLOITS.md).
- **Concurrency.** Runs J1–J3 and then J4–J5 ran concurrently, sharing one 2-CPU machine.
  The Harbor trials ran up to 4 at a time on one laptop (Docker Desktop, macOS arm64), so
  their battles shared its CPUs; each trial was still capped at its own 2 CPUs.
- **Stop-early.** A frontier model's 5-minute draft is already a working warrior. In v4,
  cutting each run at 5 minutes earns 0.63 on average, at 20 minutes 0.74, and the final
  submissions 0.71 (local v3: 0.50, 0.69, 0.67). The reward measures warrior strength, not
  effort; what it shows is that more minutes do not buy these agents strength, and in two
  v4 runs they cost some. FAILURES.md reads this as the plateau it is.
- **What remains to run.**
  - More Harbor + OpenCode runs, and a non-Claude model; see RUN_HARBOR.md.
  - The small-model training (TRAINING.md) ran once: Qwen2.5-Coder-7B goes from 0.000 to
    0.032 mean reward on the hidden hill (95% CI of the gain +0.027 to +0.037). It learned
    to write valid code and converged on the imp, which the reward pays little.
