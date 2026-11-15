# Route 3: GRPO on Modal (reinforcement learning on the environment's reward)

Routes 1 and 2 (TRAINING.md, training/mlx) use the score only to choose which samples to
imitate: expert iteration keeps the best quarter and fine-tunes on it. Here the score of
every sample is the learning signal. For each prompt the model writes a group of 8
warriors; GRPO raises the probability of the ones that scored above the group's mean and
lowers the others. That is on-policy RL with a policy gradient, one update per 64 samples.

**Status: set up, not yet run.** Results will go to REPORT.md in the run directory and to
TRAINING.md.

## What runs

| file | role |
|---|---|
| `reward.py` | the training reward: share of rounds won on the training pool (30 sparring + 60 training-hill warriors, 50 rounds each), 0 if the sample does not assemble or is a copy |
| `train.py` | TRL `GRPOTrainer`: Qwen2.5-Coder-7B-Instruct with a LoRA adapter (r = 16), vLLM generation on the same GPU, 8 prompts x 8 samples per step, every scored sample written to `samples.jsonl` |
| `evaluate.py` | after training, once: 64 fresh samples from the base model and 64 from the adapter, scored on the hidden hill with the environment's reward (100 rounds, as route 1), REPORT.md |
| `modal_app.py` | the same on a Modal A100 80 GB (or H100 with `GRPO_GPU=H100`) with 16 CPU cores for pMARS |

```bash
pip install modal && modal setup
modal run training/grpo/modal_app.py::smoke                          # 2 steps: checks the loop, time per step, base reward
modal run --detach training/grpo/modal_app.py::train --run qwen7b-grpo --max-steps 150
modal app logs corewar-grpo                                          # one JSON line per step
modal run training/grpo/modal_app.py::evaluate --run qwen7b-grpo
modal volume get corewar-grpo qwen7b-grpo training/grpo/runs/
```

Without Modal, `train.py` and `evaluate.py` run on any machine with one 80 GB GPU (`pip
install trl==1.17.1 vllm==0.31.0 peft datasets`, then `make -C pmars pmars`).

## Choices, and why

- **Reward: rounds won, not points.** The environment's reward counts a tie as 1 point and
  a win as 3; it is unchanged and is what `evaluate.py` measures. As a training signal from
  scratch, points have a cheap optimum: the one-line imp ties most rounds and kills nothing.
  On the training pool it scores 0.215 in points, more than most base-model samples, and
  route 1 converged on it. In wins, the imp is worth 0.022 and Dwarf 0.197. Base-model
  samples (64, from another prompt) spread from 0 to 0.26, and 31% win at least one round,
  so the groups have the variance GRPO needs. `--tie-weight` (0 to 1) puts ties back in.
- **Copies earn 0,** with the verifier's gate plus the short-warrior rule of
  `training/common.py`: without that rule, a published 3-to-5-instruction warrior followed by
  dead code passes the gate, and RL would find it.
- **Same prompts as the MLX run** (`training/mlx/prompts.py`): no warrior code in the prompt,
  so there is no example to hand back, and one archetype per prompt in turn, so every step
  asks for stones, papers, scanners, composites and free designs.
- **No KL penalty (beta = 0), TRL's default loss.** Learning rate 1e-5 for the adapter.

## Cost and time (estimates, to be replaced by the smoke run's numbers)

Modal lists an A100 80 GB at $0.000694/s (about $2.50/h), an H100 at $0.001097/s (about
$3.95/h; it needs a payment method on the account) and a CPU core at $0.0000131/s (16
cores: about $0.75/h). Scoring takes about 0.2 s of wall time per sample on 8 cores of an
Apple M5. One step (64 samples) should take on the order of a minute, so 150 steps are
about 2.5-3 h and $12-15.
