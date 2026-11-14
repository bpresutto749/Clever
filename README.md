# Hill Climb: frontier agents vs 30 years of human Core War

*Break the Agent (AfterQuery), Junction 2026 · Harbor task `harbor/corewar-hill` · run it
with `harbor run -p harbor/corewar-hill -a opencode -m <provider/model>` (RUN_HARBOR.md)*

## In three paragraphs

**What the agent has to do.** Write an original Core War warrior in Redcode and submit it
through the environment's MCP server. Core War is the 1984 programming game in which two
assembly programs share a circular memory and each tries to make the other crash. The
warrior is scored against a **hidden hill of 30 human-written King-of-the-Hill warriors**,
using the exact simulator (pMARS). To work with, the agent gets:
- that simulator;
- the language reference and a strategy primer;
- **30 black-box sparring opponents** drawn from the same ladder as the hill, with the same
  strength spread.

**Why it is hard.** Everything needed is available: rules, an exact simulator, a strategy
primer, and a representative test set whose scores track the hidden hill (r = 0.83 over 19
agent-level warriors, `results/proxy_check.md`). Frontier agents still plateau far below a human expert's warrior,
**even on the opponents they can see**:
- **On the visible pool**, they reach 0.34–0.46, against 0.507 for the human reference.
- **They converge on a single tuned archetype.** They try composite designs, find them weaker
  than that archetype, and abandon them, although the strongest human warriors are
  composites.
- **They stop early.** Every local run stopped with 10–18 of 45 minutes unused. Through
  Harbor + OpenCode, the five runs stopped after 4–14 minutes, and three of them said they
  had run out of time ("I ran out of the 45 minutes"). None ran `date`.
- **They mistake the visible score for the real one.** With a smaller visible pool, they
  optimised it while the hidden score stayed flat or fell (FAILURES.md).

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
| **Claude Opus 5.5 via `harbor run` + OpenCode, 5 runs (each stopped itself after 4–14 min)** | 0.342–0.422 | 0.362–0.398 | **0.704** (95% CI 0.65–0.76; all 5 ≤ 0.739) |
| **Claude Opus 5.5, shipped environment, 5 fresh runs × 45 min** | 0.349–0.455 | 0.320–0.394 | **0.671** (95% CI 0.55–0.79; all 5 ≤ 0.728) |
| Claude Opus 5.5, version 2 (10 black-box sparring), 5 runs | — | 0.309–0.401 | 0.595 (CI 0.44–0.75) |
| Claude Opus 5.5, version 1 (10 visible sparring sources, no primer), 5 runs | — | 0.372–0.465 | 0.746 (CI 0.61–0.88) |
| Claude Sonnet 5.5, version 1, 1 run | — | 0.195 | 0.140 |
| CodeClash ladder warriors, July 2026 (Opus 4.8 / GPT-5.5 / Sonnet 5 / Gemini 3.5 Flash) | — | 0.083–0.332 | 0.000–0.543 |
| Best trivial warrior (5-line stone); one-line imp | — | 0.228; 0.165 | 0.237; 0.052 |
| Qwen2.5-Coder-7B-Instruct after 4 rounds of expert iteration on the environment (base model: 0.000), 64 samples | — | 0.124 mean | 0.032 mean (best 0.060) |
| Dwarf (the documentation's example; a published warrior, so as a submission the copy gate gives 0) | — | 0.147 | 0.000 |
| Do-nothing | — | 0.000 | 0.000 |

None of the 22 Opus or Sonnet runs, across three environment versions and two harnesses,
reached the reference. The best reached 0.936. Every number comes from `make eval`
(`results/eval.md`). For the Harbor runs, `make eval` rescores the five submissions outside
Docker and matches the reward the Harbor verifier wrote (to the 4 decimals `eval.md` reports) (`runs/harbor/`,
`results/trajectories_harbor.md`). Run histories, agents' working directories and their own
reports are in `runs/`.

**Real Harbor runs** (Harbor 0.25.0, Docker Desktop, macOS arm64, egress control on;
logs in `runs/harbor/`):

| `harbor run -p harbor/corewar-hill …` | reward | wall time | cost |
|---|---|---|---|
| `-a oracle` | 1.000 | 1 min 09 | — |
| `-a nop` | 0.000 | 27 s | — |
| `-a opencode -m anthropic/claude-opus-5-5 -k 1` | 0.739 | 5 min 33 (agent 4.1 min) | $0.50 |
| `-a opencode -m anthropic/claude-opus-5-5 -k 4` (4 concurrent trials) | 0.736, 0.732, 0.681, 0.632 | 15 min 45 (agents 4.4–13.6 min) | $2.04 |

Per-run details, and which trial directory is which run (OC1–OC5), are in
`runs/harbor/README.md`.

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
│ /app/submission.red (fallback)                  │     │ status   → /results/*           │
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
  (reached through `tools/spar.py`, which calls the same MCP tools). Only the five runs
  in `runs/harbor/` went through Harbor + OpenCode. No non-Claude model was run.
- **Concurrency.** Runs J1–J3 and then J4–J5 ran concurrently, sharing one 2-CPU machine.
  Harbor gives each trial its own 2 CPUs.
- **Stop-early.** A frontier model's 5-minute draft is already a working warrior: stop-early
  at 5 minutes earns 0.50 on average in the local runs (0.65 in the Harbor runs), against
  0.67 (0.70) for the full runs. Through Harbor the agents stop on their own after 4–14
  minutes, so their result is their own stop-early baseline. The reward measures warrior
  strength, not effort; what it shows is that more minutes do not buy these agents
  strength. FAILURES.md reads this as the plateau it is.
- **What remains to run.**
  - More Harbor + OpenCode runs, and a non-Claude model; see RUN_HARBOR.md.
  - The small-model training (TRAINING.md) ran once: Qwen2.5-Coder-7B goes from 0.000 to
    0.032 mean reward on the hidden hill (95% CI of the gain +0.027 to +0.037). It learned
    to write valid code and converged on the imp, which the reward pays little.
