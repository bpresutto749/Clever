# DECISIONS.md — what was fixed when, and what changed after results came in

These notes come from the session log. They are written so a reviewer can check that the
gap was not tuned after the fact.

## Fixed before any agent run on this task

- **Hidden hill.** Every 8th warrior of the CodeClash CC:Ladder Elo ranking, from
  rank 11 to rank 243, weakest first: 30 warriors (`data/split.json`).
- **Sparring pool.** Every 24th warrior from rank 7: 10 warriors, disjoint from the hill.
- **Reference.** Toxic, the Elo #1 of the 264 humans. It was chosen from the external
  ranking, not from our hill. Measured on our hill, it is not the strongest human: the
  top 8 humans score 0.475–0.532. We kept the pre-declared choice.
- **Score.** Standard King-of-the-Hill points (3 per win, 1 per tie), pMARS defaults,
  fixed position series.
- **Probes before the agents.** The CodeClash LLM warriors and the trivial warriors were
  measured first, to check the ceiling: LLM warriors 0.08–0.34, reference 0.48.

## Changed after the first three agent runs (A, B, C), and why

| change | effect on the comparison |
|---|---|
| **Rounds per opponent: 60 → 100.** Runs A–C were told 60. | Deterministic either way; only the precision of the estimate changes. Later raised to 500 (next section); all numbers in this repo now use 500. |
| **Reward rescaled.** `(hill − imp) / (reference − imp)` instead of the raw hill score. | An affine map: no ranking or gap test changes. We did it because a one-line imp collects 0.158 raw from ties, which would make "simple strategies earn little" hard to read. |
| **Copy gate: false positive fixed.** The first gate flagged run B's original warrior as a "copy". Its 40 decoy lines happened to contain the opcode pattern of a short published warrior. | Structural containment was removed. Exact containment was kept. |
| **Copy gate: scope narrowed.** It now zeroes only copies of hill or sparring warriors, and only reports the rest of the 581-warrior corpus. | The reference itself is a near-relative of another published warrior (Mercenary, similarity 0.88). A whole-corpus gate would have needed a whitelist for it (see EXPLOITS.md). |
| **Hill selection rule removed from the agent instruction.** | With internet access, an agent could otherwise reconstruct the hidden hill from the public ladder. |

## Changed after the first adversarial review (35/100), before the version-2 runs

A fresh critic agent broke version 1. Every fix below is covered by a regression case in
`make exploits` or `make test`.

| finding | fix |
|---|---|
| **Fatal.** Harbor re-creates artifacts in a separate verifier at their *source* path. The verifier looked under `/logs/artifacts`, so every submission, the oracle's included, would have scored 0. | Read `/results/submission.red`, then `/app/submission.red`. Never read `/logs/artifacts`, which the agent can write. |
| pMARS predefines `WARRIORS` and `ROUNDS`. A source could assemble as an imp for the copy check and as Halcyon in battle: reward 1.25. | Every check now uses the listing from the exact scoring context. |
| Lightly edited sparring warriors passed the gate (padding removed, one constant changed: rewards 1.04–1.19). 6 of the 10 sparring warriors beat the reference on the hill. | The sparring pool became **black boxes** (ids only, no source, no names). The gate also removes padding and uses contiguous-run containment. |
| The agent phase had public network access, and 6 public warriors not on the hill beat the reference. | Agent phase on an **allowlist** (sidecar + model APIs; extend with `--allow-agent-host`). |
| At 100 rounds, a cosmetic edit that re-draws the `-f` position series moved D2 by up to 0.05 in reward. | **500 rounds** per opponent. The standard error is reported for every score (about ±0.01 in reward). The anchors were recomputed at 500 rounds: imp 0.1650, reference 0.4866. |
| F3 ("the gap concentrates on imp-based opponents") was not supported by the data. | Claim removed. |
| `reward.json` carried non-reward keys, which Harbor aggregates. | Only `reward` and `hill_score` remain; everything else is in `details.json`. |

**What changed for the agent.**
- Sparring warriors became black boxes, reached through MCP or `tools/spar.py`.
- A short public strategy primer (`doc/strategy_primer.md`) was added, so that the
  difficulty cannot be put down to withheld community knowledge.
- Scoring moved to 500 rounds.

Because the agent's environment changed, these changes were followed by new runs: version 2,
`runs/v2-small-pool/`. Runs A–E2 and G (`runs/opus-5.5*`) were made in version 1 and are
kept as earlier evidence, rescored at 500 rounds.

## Changed after the second adversarial review (50/100), before the version-3 runs

| finding | fix |
|---|---|
| Under egress control, Harbor puts every service without explicit networking into the egress sidecar's network namespace, so `arena` would not resolve. The oracle hid this because `solve.sh` also wrote the fallback file. | MCP is now reached on `localhost:8000` in the default (allowlist) task, with a `corewar-hill-public` variant that uses `arena:8000`. `solve.sh` submits only through MCP, and the oracle was verified end to end (MCP submit → sidecar → verifier = 1.0). |
| Published warriors not on the hill beat the reference (forjohn 1.12, maelstrom 1.10). | The gate now covers all 581 published warriors. The only exemption is the reference's exact text, so editing it is gated and reproducing it earns exactly 1.0. Wildcard cloud domains were removed from the allowlist. |
| **"Withheld information."** The 10-warrior sparring pool predicted the hidden hill poorly: r = 0.54 over 36 agent-level warriors. The difficulty could be put down to a bad proxy. | **The sparring pool is now 30 warriors drawn from the same ladder as the hill, with the same strength spread** (`data/split.json`). On the same 36 warriors it correlates r = 0.87 with the hidden hill. It stays black-box. |
| A false claim in FAILURES.md: in version 1 the highest sparring score was D2, not B. | Corrected. |
| `os.cpu_count()` sized the battle pool by host CPUs; a timeout counted silently as a loss; the file was read before the size check. | `ARENA_WORKERS` (default 2); one retry with a 4× timeout; size checked first. |
| `submit` rejections revealed sparring membership. | `submit` no longer gates; only the verifier does. |

**What changed for the agent.**
- 30 black-box sparring warriors instead of 10.
- The full-corpus originality rule.

The 10-warrior runs are kept as **version 2** (`runs/v2-small-pool/`). The headline is
**version 3** (`runs/final-env/`), the environment shipped in `harbor/`.

## Runs excluded

- **D and E.** Killed at about 14 minutes by an API quota error. Kept in `runs/aborted/`
  and never scored on the hidden hill. They were replaced by D2 and E2 with identical
  instructions.
- **No run was discarded for its score.**

## Open choices we considered and rejected

| option | why we rejected it |
|---|---|
| A top-heavy hill (the 30 strongest warriors) | It might widen the gap, but choosing it after seeing results would be selection on the test set. |
| A whitelist entry so the reference passes a whole-corpus gate | It would be a special case only the oracle could use. |
| An LLM-evolved reference, Digital Red Queen style | Not reproducible within the event. The human expert is also the more meaningful bar. |
