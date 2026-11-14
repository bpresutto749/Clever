# TRAINING.md — using the environment to make agents better

The environment produces a dense, exact, cheap reward: a few seconds per warrior on 2 cores.
It also comes with a natural train/test split. Here is how to train on it without
touching the evaluation.

## Data separation

| set | warriors | used for |
|---|---|---|
| hidden evaluation hill | 30 (`data/hill`) | final measurement only |
| sparring pool | 10 (`data/sparring`) | given to the agent |
| training hill | 60 (`training/train_hill`, built by `training/make_train_hill.py`) | training reward |

The training hill is drawn from the 581-warrior public corpus, after removing:
- every hill and sparring warrior;
- every relative of them (similarity ≥ 0.6, stricter than the 0.8 gate);
- duplicates between the two corpora.

That leaves 425 eligible warriors. The 60 were sampled from them with a fixed seed.

As a proxy, the training hill ranks warriors like the hidden hill. Over 19 warriors
(the reference, 8 agent and LLM warriors, 10 trivial or textbook warriors), Pearson 0.93 and Spearman 0.94.
That set has large spreads, so the correlation says the proxy is sound, not that it
separates close agents.

## Route 1: small model, expert iteration (`training/`)

```
bash training/run_expert_iteration.sh Qwen/Qwen2.5-Coder-7B-Instruct 3 256
```

Each round:
1. **`generate.py`** samples 256 warriors with vLLM. The prompt is the task plus the
   Redcode reference.
2. **`score.py`** scores them on the training hill.
3. **`select_sft.py`** keeps the top 25% of the valid, original, de-duplicated samples.
   Training never rewards a sample that is a near-copy of *any* of the 581 published
   warriors. That is stricter than the evaluation gate, so the model cannot learn to
   regurgitate.
4. **`sft_lora.py`** fine-tunes a LoRA (r = 16) on the kept samples, which then
   generates the next round.

At the end, the script draws 64 fresh samples from the base model and 64 from the final
adapter. It scores both once on the hidden hill and writes a report with the mean reward,
the best-of-64 and a 95% interval on the difference (`report.py`).

**Status: not run yet. It needs one GPU with at least 24 GB, for about 2–4 hours.**
- Every CPU step (training-hill construction, scoring, selection, report) was tested
  here on existing warriors.
- The two GPU scripts (`generate.py`, `sft_lora.py`) compile, but have not been executed.

## Route 2: frontier agent with lessons from FAILURES.md (run G)

Run G received `task_src/lessons.md`, appended to the same instruction. Its four points
are general: treat sparring as validation; build an archetype test set and use random
positions; composites dominate hills; use the whole budget. It contains no warrior code
and no hidden-hill content.

| | reward |
|---|---|
| G | 0.700 |
| fresh Opus runs (A, B, C, D2, E2) | 0.657 – 0.929 (mean 0.754) |

- G did follow the validation advice.
- G built a composite, which no fresh run submitted.
- G still stopped at 28 of 45 minutes.

**Conclusion from one run:** telling the agent what to do changes its process, not its
result. This supports using the environment as a training signal (Route 1) rather than
a prompt fix.

## What a trained agent should learn here

The reward exposes the four failure modes of FAILURES.md directly:
- **overfitting the visible set:** the sparring-vs-hill gap;
- **single-archetype convergence;**
- **unfixed known weaknesses:** the per-opponent breakdown in `details.json`;
- **early stopping:** the agent's MCP event log `events.jsonl` records every battle and
  submission with timestamps.

An RL run with a training hill as reward and the evaluation hill held out is the
cleanest test of whether a model can learn to generalise rather than to fit what it
sees.
