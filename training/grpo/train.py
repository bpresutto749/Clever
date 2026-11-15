#!/usr/bin/env python3
"""GRPO on the Core War environment: the model writes warriors, the training pool scores them,
and the score of each sample, relative to the other samples of its prompt, is the gradient.

Same prompts as the MLX expert-iteration run (training/mlx/prompts.py): a compact Redcode
reference, the strategy primer's archetypes in a few lines (no warrior code), and one task per
archetype (stone, paper, scanner, stone/imp, free), so every step asks for every style.
Reward: training/grpo/reward.py (rounds won on the training pool; 0 for copies). The hidden
hill is used once, by evaluate.py, after training.

Every scored sample is appended to OUT/samples.jsonl (step, archetype, wins, ties, reward,
source), so the run can be read warrior by warrior.

usage: train.py --model Qwen/Qwen2.5-Coder-7B-Instruct --out runs/qwen7b-grpo --max-steps 150
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent / "mlx"))
from reward import Scorer, summary  # noqa: E402  (before torch: see Scorer)
from common import extract  # noqa: E402
from prompts import ARCHETYPES, messages  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Qwen/Qwen2.5-Coder-7B-Instruct")
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-steps", type=int, default=150)
    ap.add_argument("--prompts-per-step", type=int, default=8)
    ap.add_argument("--num-generations", type=int, default=8, help="samples per prompt (the GRPO group)")
    ap.add_argument("--micro-batch", type=int, default=8)
    ap.add_argument("--lr", type=float, default=1e-5)
    ap.add_argument("--lora-r", type=int, default=16)
    ap.add_argument("--max-completion", type=int, default=768)
    ap.add_argument("--save-steps", type=int, default=25)
    ap.add_argument("--vllm-memory", type=float, default=0.3)
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    scorer = Scorer(a.workers)
    scorer.warm()

    # One process, one GPU: vLLM's colocate mode still expects a torch.distributed setup.
    for k, v in {"RANK": "0", "LOCAL_RANK": "0", "WORLD_SIZE": "1", "MASTER_ADDR": "127.0.0.1", "MASTER_PORT": "29511"}.items():
        os.environ.setdefault(k, v)
    import torch
    import transformers
    import trl
    from datasets import Dataset
    from peft import LoraConfig
    from trl import GRPOConfig, GRPOTrainer

    batch = a.prompts_per_step * a.num_generations             # samples per optimiser step
    assert batch % a.micro_batch == 0
    n_rows = max(a.max_steps * a.prompts_per_step, 5 * 40)
    names = [n for n, _ in ARCHETYPES]
    ds = Dataset.from_list([{"prompt": messages(names[i % len(names)]), "arch": names[i % len(names)]} for i in range(n_rows)])

    log = open(out / "samples.jsonl", "a")
    calls = {"n": 0, "t": time.time()}

    def corewar_reward(completions, arch=None, **kw):
        texts = [c[-1]["content"] if isinstance(c, list) else c for c in completions]
        srcs = [extract(t) for t in texts]
        res = scorer(srcs)
        calls["n"] += 1
        for s, r, ar in zip(srcs, res, arch or [None] * len(srcs)):
            log.write(json.dumps({"call": calls["n"], "arch": ar, **r, "source": s}) + "\n")
        log.flush()
        print(json.dumps({"call": calls["n"], "elapsed_s": round(time.time() - calls["t"]), **summary(res)}), flush=True)
        return [r["reward"] for r in res]

    cfg = GRPOConfig(
        output_dir=str(out),
        max_steps=a.max_steps,
        learning_rate=a.lr,
        per_device_train_batch_size=a.micro_batch,
        gradient_accumulation_steps=batch // a.micro_batch,
        num_generations=a.num_generations,
        max_completion_length=a.max_completion,
        temperature=1.0,
        beta=0.0,
        use_vllm=True,
        vllm_mode="colocate",
        vllm_gpu_memory_utilization=a.vllm_memory,
        vllm_max_model_length=4096,
        bf16=True,
        gradient_checkpointing=True,
        logging_steps=1,
        save_steps=a.save_steps,
        report_to="none",
        seed=a.seed,
    )
    peft = LoraConfig(r=a.lora_r, lora_alpha=2 * a.lora_r, lora_dropout=0.05, target_modules="all-linear", task_type="CAUSAL_LM")
    (out / "config.json").write_text(json.dumps({
        **vars(a), "samples_per_step": batch,
        "reward": {"rounds": int(os.environ.get("GRPO_ROUNDS", "50")), "tie_weight": float(os.environ.get("GRPO_TIE_WEIGHT", "0"))},
        "versions": {"trl": trl.__version__, "transformers": transformers.__version__, "torch": torch.__version__},
    }, indent=1))

    trainer = GRPOTrainer(model=a.model, reward_funcs=corewar_reward, args=cfg, train_dataset=ds, peft_config=peft)
    resume = any(out.glob("checkpoint-*"))
    trainer.train(resume_from_checkpoint=True if resume else None)
    trainer.save_model(str(out / "final"))
    print("saved adapter to", out / "final", flush=True)


if __name__ == "__main__":
    main()
