# TRAINING.md — using the environment to make agents better

The environment produces a dense, exact, cheap reward: a few seconds per warrior on 2
cores. It also has a clean train/test split.

## Data separation

| set | warriors | used for |
|---|---|---|
| hidden evaluation hill | 30 (`data/hill`) | final measurement only, once |
| sparring pool | 30 (`data/sparring`) | the agent's visible opponents, and part of the training reward |
| training hill | 60 (`training/train_hill`) | the rest of the training reward |

The training hill is built by `training/make_train_hill.py` from the 581-warrior public
corpus. It excludes:
- every hill warrior and every warrior of both sparring pools;
- every relative of those warriors (similarity ≥ 0.6, stricter than the 0.8 gate);
- duplicates.

That leaves 401 eligible warriors. The 60 are sampled from them with a fixed seed.

**How well each pool predicts the hidden hill** (`training/check_proxy.py` →
`results/proxy_check.md`, 31 recorded final warriors, 100 rounds):

| pool | all warriors: Pearson / Spearman | agent-level warriors (hidden ≥ 0.30, n = 19): Pearson / Spearman |
|---|---|---|
| sparring (30) | 0.98 / 0.92 | **0.83 / 0.66** |
| training hill (60) | 0.94 / 0.82 | 0.39 / 0.28 |
| earlier 10-warrior pool | 0.94 / 0.87 | 0.57 / 0.49 |

The training reward therefore combines the sparring pool, which ranks agent-level warriors
well, with the training hill, which adds breadth. The hidden hill is never used for training
or selection.

## Route 1: small model, expert iteration (`training/`)

```
bash training/run_expert_iteration.sh Qwen/Qwen2.5-Coder-7B-Instruct 3 256
```

Each round:
1. **`generate.py`** samples 256 warriors with vLLM. The prompt is the task plus the Redcode
   reference.
2. **`score.py`** scores them on the training reward pool.
3. **`select_sft.py`** keeps the top 25% of the valid, original, de-duplicated samples.
   Training never rewards a near-copy of any of the 581 published warriors, the same rule as
   the verifier, so the model cannot learn to regurgitate.
4. **`sft_lora.py`** fine-tunes a LoRA (r = 16) on the kept samples, which then generates
   the next round.

At the end, the script draws 64 fresh samples from the base model and 64 from the final
adapter. It scores both once on the hidden hill and writes a report with the mean reward,
the best-of-64 and a 95% interval on the difference (`report.py`).

**Status: not run.** It needs one GPU with at least 24 GB, for about 2–4 hours. With Modal
credits: `pip install modal && modal setup`, then `modal run training/modal_app.py`.
`training/modal_app.py` builds pMARS in an A100 container and runs the same script; it has
not been executed either.
- Every CPU step (pool construction, scoring, selection, report) was tested here on existing
  warriors.
- The two GPU scripts (`generate.py`, `sft_lora.py`) compile, but have not been executed.

## Route 2: telling a frontier agent what went wrong (run G, and the primer)

**Run G (version 1)** received `task_src/lessons.md`, appended to the same instruction. Its
four points are general:
- treat sparring as validation;
- build an archetype test set with random positions;
- composites dominate hills;
- use the whole budget.

It contains no warrior code and no hidden-hill content.

| | reward |
|---|---|
| G | 0.700 |
| fresh Opus runs of the same version (A, B, C, D2, E2) | 0.643–0.933 (mean 0.732) |

G followed the method advice and built a composite, which no fresh v1 run did. It still
stopped at 28 of 45 minutes.

**Versions 2 and 3** give every run `doc/strategy_primer.md`, which carries the same
general advice. Their means are 0.572 and 0.653, and the failure modes of FAILURES.md
persist.

Prompting changes the agents' process, not their result. That is the case for using the
environment as a training signal (Route 1).

## What a trained agent should learn here

The environment exposes the failure modes directly, so a training run can target them:

| failure | what exposes it |
|---|---|
| plateau below expert level | the reward, and the sparring score against the reference's 0.507 |
| single-archetype convergence | the per-opponent breakdown in `details.json` |
| optimising the visible set | the sparring-vs-hidden comparison over the submission history |
| early stopping | the timestamped event log `events.jsonl` |
