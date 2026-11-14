# Hill Climb: frontier agents vs 30 years of human Core War

*Break the Agent (AfterQuery), Junction 2026*

The agent must write an original Redcode warrior that holds up against a hidden hill of
30 human-written King-of-the-Hill warriors. Scoring uses the exact simulator, pMARS. The
agent gets that simulator, the language reference and 10 sparring warriors, through an
MCP server and local tools.

Frontier agents write working, competent warriors and still fall clearly short of a human
expert warrior. The reason is not the rules or compute. They optimise the 10 warriors they
can see, converge on one archetype, leave their own diagnosed weaknesses unfixed, and stop
with a third of their time left.

| | hidden-hill score | reward |
|---|---|---|
| **Human reference:** Toxic (John Metcalf), Elo #1 of 264 humans, fixed before any agent run | 0.486 | **1.000** |
| **Claude Opus 5.5:** 5 fresh runs, 45 min each | 0.373–0.462 | **0.754** (95% CI 0.626–0.882; 5/5 below) |
| Claude Opus 5.5 with lessons from FAILURES.md (1 run) | 0.387 | 0.700 |
| Claude Sonnet 5.5 (1 run) | 0.203 | 0.136 |
| CodeClash ladder warriors, July 2026 (Opus 4.8 / GPT-5.5 / Sonnet 5 / Gemini 3.5 Flash) | 0.077–0.339 | 0.000–0.552 |
| Best trivial or textbook warrior (5-line stone) | 0.228 | 0.215 |
| Do-nothing | 0.000 | 0.000 |

Scores are deterministic: pMARS fixed position series, 100 rounds × 30 opponents. Reruns
give identical numbers. Reward = `max(0, (hill − 0.1581) / (0.4856 − 0.1581))`, which puts
a one-line imp at 0 and the reference at 1.

## Why this weakness matters

Agents are increasingly asked to build things that face adversaries or distributions they
cannot see: exploit and defence code, bidding and trading strategies, game agents, code
that must survive fuzzing. The pattern here is the same everywhere: a small visible test
set, a hidden and adaptive opposition, and a simulator to iterate with.

Core War is the purest instance of that pattern:
- **exact:** the simulator is the judge;
- **cheap:** a few seconds per evaluation on 2 cores;
- **anchored:** decades of published human expert programs (Core War dates from 1984).

The measured failures (FAILURES.md):

1. **F1 — Goodhart on the visible set.** Sparring scores overestimate hidden scores for 6
   of 7 runs, by up to 0.12. The reference drops by 0.003. Run B *beats the human reference
   on sparring* (0.497 vs 0.489) and is the worst Opus run on the hidden hill.
2. **F2 — single-archetype convergence.** Four of five fresh Opus runs submitted a lone
   0.5c scanner, one a lone paper. Each tried and dropped composites within minutes. The
   reference and many hill warriors are composites (qscan → paper/imp).
3. **F3 — naming a weakness without fixing it.** Four of five runs reported that imp-based
   opponents beat them. That is exactly where the gap concentrates: 0.32–0.37 against those
   opponents, versus 0.45 for the reference.
4. **F4 — early stopping.** Every run stopped with 16–37 of 45 minutes unused, including
   the one told to use the whole budget.

## How the environment works

```
┌────────────── agent container (main) ──────────────┐     ┌──── MCP sidecar "arena" ────┐
│ OpenCode / any Harbor agent                        │ MCP │ get_rules  list/get_sparring │
│ /app/bin/pmars  /app/doc  /app/sparring            │────▶│ battle  battle_custom        │
│ /app/tools/battle.py  /app/submission.red          │     │ submit (last accepted counts)│
└────────────────────────────────────────────────────┘     │ status  → /results/*         │
                                                           └──────────────┬───────────────┘
                     artifacts: /results/submission.red, events.jsonl,    │
                                /app/submission.red (fallback)            ▼
                       ┌──── verifier container (separate, no network) ────────────┐
                       │ hidden hill (30)  · copy gate (hill + sparring)            │
                       │ corpus of 581 published warriors (similarity report)       │
                       │ pMARS as `nobody`, sanitised source, timeouts              │
                       │ → /logs/verifier/reward.json  + details.json               │
                       └────────────────────────────────────────────────────────────┘
```

**Hidden information.** The hidden hill exists only in the verifier image. The agent gets
no hill feedback at all, and the instruction does not reveal how the hill was selected.

**Validity.**
- A warrior that does not assemble scores 0.
- A near-copy of a sparring or hill warrior scores 0.
- The closest of 581 published warriors is reported for every submission.

**Robustness.**
- pMARS hangs on source lines longer than about 256 characters. We found this through a
  real LLM warrior. The sanitiser removes that path.
- pMARS runs unprivileged with timeouts, so even a crafted warrior that subverted the 1990s
  C code could not write the reward.

The full analysis and the 24-case regression sweep are in EXPLOITS.md.

## Reproduce

```bash
make test        # regression tests: anchors, determinism, sanitiser, copy gate, isolation
make eval        # no Docker: scores reference, baselines and all recorded runs → results/eval.md
make exploits    # 24 exploit and simple-strategy cases through the real verifier → results/exploits.md
make task lint   # regenerate harbor/corewar-hill from sources and lint it

# Judges' protocol with Harbor (needs Docker):
make harbor-reference              # oracle: submits the reference warrior via MCP
make harbor-nop                    # do-nothing
make harbor-agent MODEL=<provider/model>   # 3 OpenCode runs
```

Everything except the Harbor runs works with Python 3.10+ and a C compiler. pMARS is built
from the vendored source. The Harbor task was linted with `harbor lint`. Docker was not
available where it was built, so its end-to-end Harbor run is the step a judge does first.
All of its parts were tested individually:
- the MCP server and every tool, through a real MCP client;
- the verifier, on sidecar, fallback-file and empty artifacts;
- the oracle's submit client.

**Agent network.** The agent phase runs with `network_mode = "public"`, because the agent
must reach your model API. For an exploit-proof run, switch it to an allowlist with your
model host only (EXPLOITS.md, residual risk 1).

## Repository

| path | content |
|---|---|
| `arena/core.py` | the rules engine: sanitiser, assembler wrapper, copy gate, battles, hill score. Shared by sidecar, verifier and tools. |
| `arena/mcp_server.py`, `arena/RULES.md` | MCP sidecar |
| `task_src/` | instruction, verifier, local battle tool, lessons used in run G |
| `build_task.py` | generates the Harbor task `harbor/corewar-hill` (single source of truth) |
| `data/` | hill, sparring, reference, corpus, Elo ranking, split rule |
| `runs/` | every recorded agent warrior with a summary of the agent's own log (`run_*.md`) |
| `baselines/`, `exploits/` | trivial strategies and the exploit sweep |
| `training/` | training hill and the small-model expert-iteration pipeline |
| `FAILURES.md`, `EXPLOITS.md`, `TRAINING.md`, `DECISIONS.md`, `CREDITS.md` | analysis, integrity, upgrade path, what was fixed when, credits |

## Honest limits

- **Gap size.** The gap is clear but not enormous. The best Opus run reached 0.929. A
  stronger model might close more of it.
- **How the agent runs were made.** They were made with Claude agents in a local copy of
  the arena (same instruction, same tools, no MCP layer), not through Harbor + OpenCode.
- **Sample sizes.** The lessons result and the Sonnet result are single runs.
- **The upgrade path.** The small-model training (TRAINING.md) is built and CPU-tested but
  needs a GPU to run.
