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
| **Rounds per opponent: 60 → 100.** Runs A–C were told 60. | Deterministic either way; only the precision of the estimate changes. All numbers in this repo use 100. |
| **Reward rescaled.** `(hill − imp) / (reference − imp)` instead of the raw hill score. | An affine map: no ranking or gap test changes. We did it because a one-line imp collects 0.158 raw from ties, which would make "simple strategies earn little" hard to read. |
| **Copy gate: false positive fixed.** The first gate flagged run B's original warrior as a "copy". Its 40 decoy lines happened to contain the opcode pattern of a short published warrior. | Structural containment was removed. Exact containment was kept. |
| **Copy gate: scope narrowed.** It now zeroes only copies of hill or sparring warriors, and only reports the rest of the 581-warrior corpus. | The reference itself is a near-relative of another published warrior (Mercenary, similarity 0.88). A whole-corpus gate would have needed a whitelist for it (see EXPLOITS.md). |
| **Hill selection rule removed from the agent instruction.** | With internet access, an agent could otherwise reconstruct the hidden hill from the public ladder. |

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
