# RL synthesis: training small models on the environment (stretch goal)

*Last updated: 15 November 2026, 06:45 EET. Combines the two training efforts:*
- *Alexandre: expert iteration on the school's GPU cluster, 7B / 14B / 32B
  (`training/CLUSTER_RUNS.md`);*
- *Benjamin: GRPO on Modal, 3B / 7B (`training/grpo/RESULTS.md`).*

*Earlier route-1 run and route 2 (prompting a frontier agent): `TRAINING.md`.*

## In one sentence

A small open model trained on the environment's reward **always improves, and the gain is real
and reproducible**. It improves by finding the cheapest pattern within its reach (the imp, the
example warrior, a retuned Dwarf). Those patterns pay **0.03 to 0.21**, against **0.71** for
the frontier agents and **1.00** for the human expert.

## Numbers for the presentation

Every number below is the environment's own reward on the hidden hill (0 = Dwarf, 1 = Toxic).
The hidden hill is never used for training, and is read on fresh samples after training.

| what the trained model writes | method, model | mean reward, base → trained | best single sample |
|---|---|---|---|
| **the imp** (`mov 0, 1` + dead code) | expert iteration, 7B (3 runs) | 0.000 → 0.030–0.032 | 0.06–0.09 |
| **its own small bombers** (no example in the prompt) | expert iteration, 14B (2 seeds) | 0.002–0.004 → 0.037–0.051 | 0.22, **0.36** |
| same | expert iteration, 32B, 7 rounds (2 seeds) | 0.011–0.015 → **0.059–0.082** | 0.30–0.33 |
| its own designs, small | GRPO, 7B, no warrior in the prompt | 0.000 → 0.004 | 0.06 |
| **the example warrior it was shown**, retuned | GRPO, 3B / 7B, Dwarf in the prompt | 0.003–0.012 → 0.023–0.084 | 0.19 (7B) |
| same | expert iteration, 7B, five examples in the prompt | 0.000–0.006 → 0.138–0.151 | 0.19–0.26 |
| **Dwarf with constants found by a script** | expert iteration + scripted constant search, 7B | 0.001–0.005 → 0.137–0.206 | 0.27 |
| *for comparison:* frontier agents (Claude Opus 5.5, shipped task) | | **0.713** | 0.741 |
| *for comparison:* human expert (Toxic) | | **1.000** | |

**Proposed slide** (it would replace the current `BONUS · TRAINING` scene, `s_train` in
`video/explainer.py`, which shows only the first 7B run: 0.000 → 0.032):

> **Small AIs learn from the game, then hit a wall.**
> 18 training runs, two methods (expert iteration, reinforcement learning), models from 3B to 32B.
> Every run improves, outside the noise. Each one learns the cheapest trick within its reach:
> - a one-line trick (0.03);
> - its own small programs (up to 0.08);
> - retuning the example it was shown (up to 0.21).
>
> AI agents: 0.71. Human expert: 1.00.

## What both efforts found, independently

1. **The reward can be climbed, from zero, and the gain replicates.**
   - All 18 runs evaluated on the hidden hill gain, with a 95% interval above zero.
   - A second seed confirms the gain at 7B (GRPO) and at 14B and 32B (expert iteration).
   - The size of the gain varies between seeds: 32B gains +0.071 and +0.045; 7B GRPO gains +0.040
     (step 150) and +0.019.
   - The one run with no gain had nothing to learn from: no base sample above Dwarf on the training
     pool.
2. **The optimiser takes the cheapest pattern within reach, whatever the method.**

   | cheapest pattern | method | how much of the reward it makes |
   |---|---|---|
   | the imp | expert iteration, 7B | 78–89 of 120 final samples |
   | the example stone | expert iteration, 7B | 45 of 59 valid samples (seed A), 59 of 64 (nearby seed) |
   | retuned Dwarfs | GRPO | 91% of the reward (7B), 100% (3B) |
   | retuned Dwarfs | expert iteration + constant search | 64 of 64 samples |

   Expert iteration only re-weights what the model can already sample. GRPO moves every sample,
   and still lands in the same place. This is a property of the task, not of one method.
3. **The cheap patterns pay little.** The best of them, a Dwarf tuned by a script, gives
   0.21. The reward has no shortcut to the agents' level. This supports the *reward integrity*
   criterion.
4. **Model size matters more than samples or steps.**
   - Without an example in the prompt, the 7B model stays on the imp at every budget (256 to
     2,040 samples per round).
   - The 14B and 32B models write working bombers from the task text alone.
   - The 32B model keeps improving with rounds: 0.044 after round 3, 0.082 after round 6.
   - With no example in the prompt, GRPO at 7B gains only 0.004. All 7 of its rewarded samples
     are designs of its own; the best is a stone/imp composite (0.055).
5. **Feedback does not teach a small model to design.**
   - *Expert iteration with the sparring table after each draft (2 revision turns):* revised drafts
     score lower than first drafts, before and after training. The 32B gain is higher (0.070
     against 0.044 at equal rounds), but because the best of three drafts is kept.
   - *GRPO with the `spar` tool:* the 7B model never made a tool call. A quarter of its replies
     wrote a well-formed call inside a markdown block. The two-turn variant runs end to end, but
     its first optimiser step fails inside TRL (`training/grpo/README.md`).

   This matches FAILURES.md: the hard part is design, not tuning or access to information.
6. **Training found a hole in the copy gate.**
   - The containment test needs 6 or more instructions. So a published warrior of 3 to 5
     instructions, followed by dead code, passes the gate.
   - Gymnosperm Trickery + 3 `dat` lines earns 0.577 at 500 rounds.
   - Status: every training scorer treats such a sample as a copy. The verifier fix (with the
     `errors="replace"` fix for pMARS output) is on branch `gate-short-warriors`, **not on main
     yet**.

## Read with care

- **Not one experiment.** The two efforts use different prompts, training rewards and evaluation
  sizes, so compare their trends, not their decimals.
  - Expert iteration: one prompt per archetype; selection on points; 120 evaluation samples, 64
    for some runs.
  - GRPO: one prompt with or without the Dwarf; reward = rounds won, so the imp earns 0.022
    instead of 0.215; 65 evaluation samples.
- **The hidden hill was read more than once for two runs.**
  - The 32B seed-A run was read after rounds 3 and 6.
  - The GRPO 7B main run was read at steps 50, 100, 150 and 200. Its 200 steps were set before
    the run, so no checkpoint was picked on the hill.
  - Every other run was read once.
- **The runs with example warriors or a scripted search reproduce what they were given.** Their
  numbers are not evidence of design. The only evidence of design by the model is the 14B/32B
  bombers and the GRPO no-Dwarf control, and it is small: 0.004 to 0.082.
- **Every final sample file was opened** before the samples were described above.

## Still running (as of 06:40 EET, 15 November)

| run | where | state | training signal so far (not the hidden hill) |
|---|---|---|---|
| GRPO Qwen2.5-Coder-14B, 100 steps | Modal | step ~88 | samples that win a round: 58% → 80% |
| GRPO Gemma 4 12B, 100 steps | Modal | step ~63 | 64% → 72% |
| GRPO Qwen3-8B, 150 steps | Modal | step ~29 | 82% → 84% |
| GRPO 7B, Dwarf variants earn 0 in training (`--gate-example`), 150 steps | Modal | step ~106 | 29% → 70%: the model finds winning designs other than the Dwarf |
| expert iteration 7B, seed B | cluster | evaluation running | |

These rows will be replaced by hidden-hill results as the runs finish.

## Update log

- 15 Nov 06:45 EET: first version (cluster runs from `training/CLUSTER_RUNS.md`, GRPO results up
  to commit 9e0b152).
