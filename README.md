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
- **On the visible pool**, they reach 0.35–0.46, against 0.507 for the human reference.
- **They converge on a single tuned archetype.** They try composite designs, find them weaker
  than that archetype, and abandon them, although the strongest human warriors are
  composites.
- **They stop early.** Every run stopped with 10–18 of 45 minutes unused.
- **They mistake the visible score for the real one.** With a smaller visible pool, they
  optimised it while the hidden score stayed flat or fell (FAILURES.md).

This is the shape of agent work on anything judged against hidden, adaptive opposition:
exploit and defence code, bidding agents, code under fuzzing.

**How it is scored.**
- **Hill score.** Each warrior plays 500 rounds against each of the 30 hidden warriors (3
  points per win, 1 per tie). The hill score is the mean points per round / 3.
- **Reward.** The verifier writes `reward = clip((hill − 0.1650) / (0.4866 − 0.1650), 0, 1)`
  to `/logs/verifier/reward.txt`. A one-line imp gets 0, and the human reference (Toxic,
  John Metcalf, Elo #1 of 264 humans, fixed before any agent run) gets 1.
- **Reproducibility.** Scores are deterministic: pMARS fixed position series, standard error
  about ±0.01.
- **Copies.** A near-copy of any of 581 published warriors scores 0.

## Results

| | visible pool (30) | hidden-hill score | reward |
|---|---|---|---|
| **Human reference** (Toxic) | 0.507 | 0.487 | **1.000** |
| **Claude Opus 5.5, shipped environment, 5 fresh runs × 45 min** | 0.349–0.455 | 0.320–0.394 | **0.653** (95% CI 0.53–0.78; all 5 ≤ 0.713) |
| Claude Opus 5.5, version 2 (10 black-box sparring), 5 runs | — | 0.309–0.401 | 0.572 (CI 0.41–0.74) |
| Claude Opus 5.5, version 1 (10 visible sparring sources, no primer), 5 runs | — | 0.372–0.465 | 0.732 (CI 0.59–0.88) |
| Claude Sonnet 5.5, version 1, 1 run | — | 0.195 | 0.093 |
| CodeClash ladder warriors, July 2026 (Opus 4.8 / GPT-5.5 / Sonnet 5 / Gemini 3.5 Flash) | — | 0.083–0.332 | 0.000–0.518 |
| Best trivial or textbook warrior (5-line stone) | — | 0.228 | 0.195 |
| Do-nothing | — | 0.000 | 0.000 |

None of the 17 Opus or Sonnet runs, across three environment versions, reached the reference.
The best reached 0.933. Every number comes from `make eval` (`results/eval.md`). Run
histories, agents' working directories and their own reports are in `runs/`.

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
| TRAINING.md | the upgrade path: training a small model on a disjoint training hill |
| DECISIONS.md | what was fixed before the agent runs, and what changed after which review |
| RUN_HARBOR.md | Harbor commands and what to look at in a run |
| CREDITS.md | pMARS (GPL), CodeClash, Digital Red Queen, and the warrior authors |

## Honest limits

- **How the agent runs were made.** The recorded agent runs were made with Claude agents in
  a local copy of the arena, with the same instruction, simulator and sparring server
  (reached through `tools/spar.py`, which calls the same MCP tools). They were not made
  through Harbor + OpenCode, and no non-Claude model was run.
- **What remains to run.**
  - A Harbor + OpenCode run log is the first thing to add; see RUN_HARBOR.md.
  - The small-model training (TRAINING.md) is built and CPU-tested, but needs a GPU.
