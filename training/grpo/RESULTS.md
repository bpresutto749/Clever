# GRPO results (route 3), in progress

Updated as runs finish. Every number below was measured by the scripts in this directory. The
evaluations use the environment's reward on the hidden hill, which is never used for training
(100 rounds per opponent, 65 fresh samples per model).

## Main run: Qwen2.5-Coder-7B-Instruct, 200 steps

Prompt: the MLX run's, plus the documentation's Dwarf as a syntax example. Training reward:
the share of rounds won on the training pool. Sampling: temperature 0.8, top_p 0.95.
Configuration and reports: `results/qwen7b-grpo/`.

| | base | step 50 | step 100 | step 150 | **step 200 (final)** |
|---|---|---|---|---|---|
| mean reward on the hidden hill | 0.0034 | 0.0074 | 0.0257 | 0.0431 | **0.0525** |
| gain, 95% CI (Welch) | | -0.006 to +0.014 | +0.008 to +0.037 | +0.023 to +0.057 | **+0.030 to +0.068** |
| samples with reward > 0 | 3% | 6% | 25% | 38% | **46%** |
| mean raw hill score (0 below Dwarf is not applied) | 0.014 | 0.043 | 0.078 | 0.110 | **0.120** |
| valid samples (of 65) | 39-43 | 49 | 57 | 60 | **60** |
| best sample | 0.177 | 0.177 | 0.177 | 0.177 | **0.194** |

(The base model is resampled at each evaluation with the same seed; its numbers vary slightly
between evaluations because vLLM batches differently.)

**Where the reward comes from.** Up to step 150, the best sample is the documentation's Dwarf
with its step changed from 4 to 3364, a constant that appears in the prompt's syntax notes
(0.177). The final model's best (0.194) is the same loop followed by an imp block that never
runs. Split by structure:

| structure of the samples with reward > 0 | step 150: samples, share of the reward | step 200: samples, share |
|---|---|---|
| the Dwarf with other constants | 12, 63% | 18, 74% |
| contains the Dwarf's loop (often followed by code that never runs) | 7, 27% | 6, 17% |
| other | 6, 10% | 6, 9% |

Without the Dwarf shapes, the mean reward goes from 0.0007 (base) to 0.0045 at step 150. GRPO amplified
the strongest pattern within the model's reach, which here is retuning the example it was
shown. That is the same mechanism as the imp in route 1 and the example stone in Alexandre's
expert iteration.

## Control and replicate (150 steps, same settings unless stated)

| run | change | training: share of samples that win a round, start → end | hidden hill |
|---|---|---|---|
| main | none | 31% → 75% (step 150) | above |
| seed 1 | another seed | 34% → 73% | 0.0034 → **0.0228** (95% CI of the gain +0.005 to +0.034); reward > 0: 3% → 23%; raw hill score 0.014 → 0.087; 74% of the reward from Dwarf shapes |
| no Dwarf | the prompt has no warrior code | 2-13% → 33% | 0.0000 → **0.0040** (95% CI of the gain +0.001 to +0.007); reward > 0: 0% → 11%; raw hill score 0.001 → 0.033; valid 26 → 42 of 65 |

The replicate follows the main run step for step in training; on the hidden hill its gain at
step 150 is half the main run's (0.023 against 0.043), in the same direction and also outside
the noise. Without the Dwarf, learning starts from far
fewer winning samples and stays slow.

**The control separates the two effects.** All 7 control samples with reward > 0 are other
designs than the Dwarf (best: a stone/imp composite, 0.055). The main run's reward outside the
Dwarf shapes is 0.0045 at step 150, about the control's 0.0040. With or without the example,
GRPO teaches the 7B model a small, real gain on designs of its own; the example in the prompt
adds retuned Dwarfs on top of it, which make up 90% of the main run's reward.

## Other models (same prompt, reward and sampling)

| model | steps | hidden hill: mean reward, base → trained (95% CI of the gain) | reward > 0 | valid (of 65) | share of the reward from Dwarf shapes, trained |
|---|---|---|---|---|---|
| Qwen2.5-Coder-3B-Instruct | 150 | 0.0118 → **0.0837** (+0.051 to +0.092) | 9% → 69% | 32 → 63 | **100%** (81% the Dwarf with other constants, 19% its loop) |

The smallest model gains the most, and all of its gain is retuned Dwarfs: it collapses onto
the example more completely than the 7B (91%).

## Prompt choice (`probe.py`, base model, 60 samples each)

| prompt | sampling | valid | won a round |
|---|---|---|---|
| MLX run's | T 1.0 | 8 | 1.7% |
| MLX run's | T 0.8, top_p 0.95 | 24 | 13% |
| MLX run's + Dwarf | T 0.8, top_p 0.95 | 36 | 35% |
| route 1's (full Redcode reference) | T 0.8, top_p 0.95 | 29 | 5% |

Other base models, same prompt and sampling:

| model | valid | won a round | copies |
|---|---|---|---|
| Qwen2.5-Coder-3B-Instruct | 34 | 40% | 3 |
| Qwen3-8B (thinking off) | 51 | 68% | 8 |
| Qwen2.5-Coder-14B-Instruct | 41 | 48% | 1 |
| Gemma 4 12B (gemma-4-12B-it) | 37 | 60% | 0 |

## Running

- Qwen2.5-Coder-3B, 150 steps.
- Qwen2.5-Coder-14B, 100 steps (H200).
- Gemma 4 12B, 100 steps (H200).
- Qwen3-8B, 150 steps.
- Qwen2.5-Coder-7B with `--gate-example`, 150 steps: Dwarf variants earn 0 in training, to
  see what the model learns when retuning the example does not pay.
