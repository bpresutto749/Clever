# Hill Climb: frontier agents vs 30 years of human Core War

*Break the Agent (AfterQuery), Junction 2026*

The agent must write an original Redcode warrior and submit it. The warrior is scored
against a hidden hill of 30 human-written King-of-the-Hill warriors, using the exact
simulator (pMARS). To work with, the agent gets:
- the simulator;
- the language reference and a strategy primer;
- 10 black-box sparring opponents, through an MCP server.

Frontier agents write competent warriors and still fall well short of a human expert's.
The reason is not missing rules, missing compute or missing strategy knowledge. They climb
the score they can see, and the score they cannot see does not move.

| | hidden-hill score | reward |
|---|---|---|
| **Human reference:** Toxic (John Metcalf), Elo #1 of 264 humans, fixed before any agent run | 0.487 | **1.000** |
| **Claude Opus 5.5, final environment:** 5 fresh runs, 45 min each | 0.309–0.401 | **0.572** (95% CI 0.41–0.74; all 5 ≤ 0.733) |
| Claude Opus 5.5, version 1 of the environment (sparring sources visible, no primer): 5 runs | 0.372–0.465 | 0.732 (95% CI 0.59–0.88) |
| CodeClash ladder warriors, July 2026 (Opus 4.8 / GPT-5.5 / Sonnet 5 / Gemini 3.5 Flash) | 0.083–0.332 | 0.000–0.518 |
| Best trivial or textbook warrior (5-line stone) | 0.228 | 0.195 |
| Do-nothing | 0.000 | 0.000 |

**How to read the scores.**
- **Reward** = `max(0, (hill − 0.1650) / (0.4866 − 0.1650))`: a one-line imp gets 0 and the
  reference gets 1.
- **Hill score** = mean King-of-the-Hill points per round / 3, over 30 opponents × 500 rounds.
- **Reproducibility.** pMARS's fixed position series makes scores deterministic.
- **Noise.** The start-position standard error is about ±0.01 in reward, and `make eval`
  prints it for every warrior.

## The weakness, measured

The arena server timestamps every submission, so we can follow each agent's work. We scored
all 26 submissions of the final runs on both pools:

- **F1 — they optimise the visible set, and it does not transfer.**
  - After their first real draft, the agents raise their sparring score by **+0.084 on
    average** over 13–27 minutes. Their hidden-hill score moves **−0.006**.
  - In 3 of 5 runs, the final submission is worse on the hidden hill than an earlier one.
    H4 peaked at minute 13 with reward 0.66 and ended at 0.51.
  - H2 matches the human reference on sparring (0.488 vs 0.498) and scores 0.319 vs 0.487
    on the hill.
  - Every agent forecast its reward too high, by 0.06–0.52.
- **F2 — they diagnose the problem and select on noise anyway.** Four of five runs wrote that
  their best-of-many number was "optimistic", "flattering" or "a lucky draw". None held out
  a validation set, and each submitted that number.
- **F3 — their composites fit the sparring pool.** With the primer, 4 of 5 runs built
  p-space selectors tuned on the 10 visible opponents. They score 0.45–0.70. The one plain
  13-line paper scores 0.73.
- **F4 — they stop early.** All 12 Opus and Sonnet runs stopped with 13–37 of 45 minutes
  unused.

FAILURES.md has the tables, the agents' own words, and why this pattern matters for code
that faces hidden adversaries: exploits, defences, bidding agents, fuzzed services.

## How the environment works

```
┌──────────── agent container (main) ─────────────┐     ┌────── MCP sidecar "arena" ──────┐
│ OpenCode / any Harbor agent                     │ MCP │ get_rules  list_sparring (ids)  │
│ /app/bin/pmars   /app/doc (+ strategy primer)   │────▶│ battle  battle_custom           │
│ /app/tools/spar.py  /app/tools/battle.py        │     │ submit (last accepted counts)   │
│ /app/submission.red (fallback)                  │     │ status   → /results/*           │
└──── network: allowlist (model APIs only) ──────┘     │ 10 sparring warriors, black box │
                                                         └──────────────┬──────────────────┘
          artifacts (re-created at their source paths in the verifier): │
          /results/submission.red, events.jsonl, history/, /app/submission.red
                                                                         ▼
                ┌──── verifier container (separate, no network) ────────────────────┐
                │ hidden hill (30) · near-copy gate (hill + sparring)               │
                │ 581 published warriors (similarity report)                        │
                │ battle-context assembly · sanitised source · pMARS as `nobody`    │
                │ → /logs/verifier/reward.json {reward, hill_score} + details.json  │
                └───────────────────────────────────────────────────────────────────┘
```

**Integrity.** The agent never sees hill or sparring code or names, and gets no hill
feedback. Each of the following scores 0 and has a regression case:
- copies of hill or sparring warriors, including padded, retuned or embedded copies;
- assembly-context tricks (`WARRIORS` / `ROUNDS`);
- pMARS hangs and oversized files;
- planted files in `/logs/artifacts`.

The first adversarial review found five real holes; all of them are closed (DECISIONS.md).
EXPLOITS.md lists every attack and the remaining risks.

## Reproduce

```bash
make test        # regression tests: anchors, determinism, sanitiser, gate, assembly context, isolation
make eval        # no Docker: reference, baselines, every recorded run (with standard errors) → results/eval.md
make exploits    # 29 exploit and simple-strategy cases through the real verifier, plus the stop-early table
make task lint   # regenerate harbor/corewar-hill from sources and lint it

# Judges' protocol with Harbor (needs Docker):
make harbor-reference              # oracle: submits the reference through the MCP server
make harbor-nop                    # do-nothing
make harbor-agent MODEL=<provider/model>   # 3 OpenCode runs; add --allow-agent-host if your endpoint is unusual
# Docker host without Harbor egress control: append TASK=harbor/corewar-hill-public (public agent network)
```

**Requirements.** Everything except the Harbor runs needs only Python 3.10+, `mcp==1.30.0`
and a C compiler (pMARS is built from the vendored source).

**What has and has not been run.**
- The Harbor task passes `harbor lint`.
- Its artifact layout was checked against Harbor's own artifact handler.
- Its parts were each tested here:
  - the MCP server and every tool, through a real MCP client;
  - the oracle's submit client, sidecar to verifier, with reward exactly 1.0;
  - the verifier, on every artifact case.
- Docker was not available on the build machine, so a full `harbor run` has not been done
  yet.

## Repository

| path | content |
|---|---|
| `arena/core.py` | the rules engine: sanitiser, battle-context assembler, near-copy gate, battles, hill score. Shared by the sidecar, the verifier and every tool. |
| `arena/mcp_server.py`, `arena/RULES.md` | MCP sidecar (black-box sparring, submission history) |
| `task_src/` | instruction, verifier, agent-side tools, lessons used in run G |
| `build_task.py` | generates the Harbor task `harbor/corewar-hill` (single source of truth) |
| `data/` | hill, sparring, reference, corpus, Elo ranking, split rule |
| `doc/` | what the agent gets: language reference, beginners' guide, ICWS '94 draft, pMARS manual, strategy primer |
| `runs/` | `final-env/` (H1–H5 with full submission histories), version-1 runs, CodeClash warriors, aborted runs. Each has a summary of the agent's own log. |
| `baselines/`, `exploits/` | trivial strategies, exploit sweep, stop-early and trajectory scripts |
| `training/` | training hill (disjoint from the hidden hill) and the small-model expert-iteration pipeline |
| `FAILURES.md`, `EXPLOITS.md`, `TRAINING.md`, `DECISIONS.md`, `CREDITS.md` | analysis, integrity, upgrade path, what was fixed when, credits |

## Honest limits

- **How the agent runs were made.** They were made with Claude agents in a local copy of the
  arena, with the same instruction, simulator and sparring server (reached through
  `tools/spar.py`, which calls the same MCP tools). They were not made through Harbor +
  OpenCode, and no non-Claude model was run in the final environment.
- **Gap size depends on the model.** The best single run anywhere reached 0.93 (version 1). A
  stronger model may close more of the gap.
- **The upgrade path.** The small-model training (TRAINING.md) is built and CPU-tested, but
  needs a GPU to run.
