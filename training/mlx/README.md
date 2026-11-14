# Expert iteration on a Mac (Apple Silicon, MLX)

The same expert-iteration loop as `training/run_expert_iteration.sh`, on Apple Silicon with
[MLX](https://github.com/ml-explore/mlx-lm): Qwen2.5-Coder-7B-Instruct in 4 bits plus a LoRA
adapter. No GPU server needed.

```bash
bash training/mlx/setup.sh     # once: native pMARS build, .venv-mlx with mlx-lm, model download, checks
bash training/mlx/run.sh       # starts in the background and keeps the Mac awake; log in training/mlx/runs/<name>/run.log
```

Each round: `gen.py` samples N warriors (batched), `score.py` scores them on the training
pool (30 sparring + 60 training-hill warriors, never the hidden hill), `pick.py` keeps the best
quarter **of each archetype** over all rounds so far, and `mlx_lm lora` fine-tunes a fresh
adapter from the base model on them. At the end, base and final adapter each draw fresh samples
that are scored once on the hidden hill, and `report.py` writes `REPORT.md`.

What changed from the first run (GPU, vLLM, TRAINING.md), and why:

| | first run | this run |
|---|---|---|
| prompt | task + the full Redcode reference | task + a compact Redcode reference + the strategy primer's archetypes (no code), shorter so LoRA trains fast on a laptop |
| prompts per round | one | one per archetype (stone, paper, scanner, stone/imp, free), in turn |
| selection | top 25% overall | top 25% within each archetype: the first run collapsed onto the imp, the cheapest strategy the reward allows |
| reply format | free text, code block extracted | the reply starts inside a code block, so every sample is one warrior |

The reward, the gate on copies, the training pool and the held-out evaluation are unchanged.
