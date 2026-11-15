#!/usr/bin/env python3
"""Held-out evaluation of a GRPO run: fresh samples from the base model and from the trained
adapter, scored once on the hidden hill with the environment's own reward (0 at Dwarf, 1 at
the reference), 100 rounds per opponent and the same copy gate as training, as in route 1.

Both models get the same prompts (one per archetype, in turn), the same sampling settings
as training (temperature 1.0) and the same seeds.

usage: evaluate.py --run runs/qwen7b-grpo [--adapter runs/qwen7b-grpo/final] [--n 64]
writes RUN/base.eval.jsonl, RUN/final.eval.jsonl and RUN/REPORT.md
"""
import argparse
import importlib.util
import json
import math
import os
import statistics
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import reward as _reward  # noqa: E402,F401  (loads training/common.py without putting training/ on sys.path)
from common import EVAL_HILL, extract, read_jsonl, reward, score_many, write_jsonl  # noqa: E402
# training/mlx/prompts.py, loaded from its file: putting training/mlx on sys.path would make
# a directory named "mlx" importable, and transformers would take it for Apple's MLX library.
_spec = importlib.util.spec_from_file_location("mlx_prompts", HERE.parent / "mlx" / "prompts.py")
_prompts = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_prompts)
ARCHETYPES, messages = _prompts.ARCHETYPES, _prompts.messages


def sample(model, adapter, n, max_tokens, seed):
    from vllm import LLM, SamplingParams
    from vllm.lora.request import LoRARequest

    llm = LLM(model=model, enable_lora=True, max_lora_rank=64, max_model_len=4096, seed=seed)
    tok = llm.get_tokenizer()
    names = [a for a, _ in ARCHETYPES]
    per = math.ceil(n / len(names))
    prompts = [tok.apply_chat_template(messages(a), tokenize=False, add_generation_prompt=True) for a in names]
    out = {}
    for tag, lora in (("base", None), ("final", LoRARequest("adapter", 1, adapter))):
        sp = SamplingParams(n=per, temperature=1.0, max_tokens=max_tokens, seed=seed)
        gens = llm.generate(prompts, sp, lora_request=lora)
        rows = [{"arch": a, "text": o.text, "source": extract(o.text)} for a, g in zip(names, gens) for o in g.outputs]
        out[tag] = rows[:n] if len(rows) == n else rows
    return out


def score(rows, workers):
    res = score_many([r["source"] for r in rows], EVAL_HILL, rounds=100, workers=workers)
    for r, s in zip(rows, res):
        r.update({f"eval_{k}": v for k, v in s.items()})
        r["eval_reward"] = reward(s["score"]) if s["valid"] and not s["copy"] else 0.0
    return rows


def training_curve(run):
    p = run / "samples.jsonl"
    if not p.exists():
        return []
    by = defaultdict(list)
    for r in read_jsonl(p):
        by[r["call"]].append(r)
    lines = ["| step | samples | valid | copies | won a round | mean training reward | best |", "|---|---|---|---|---|---|---|"]
    steps = sorted(by)
    for c in sorted(set(steps[:: max(1, len(steps) // 10)] + steps[-1:])):
        rs = by[c]
        rw = [r["reward"] for r in rs]
        lines.append(f"| {c} | {len(rs)} | {sum(r['valid'] for r in rs)} | {sum(bool(r['copy']) for r in rs)} | "
                     f"{sum(r['wins'] > 0 for r in rs)} | {statistics.mean(rw):.4f} | {max(rw):.4f} |")
    return lines


def report(run, base, final):
    b, f = [r["eval_reward"] for r in base], [r["eval_reward"] for r in final]
    mb, mf = statistics.mean(b), statistics.mean(f)
    se = math.sqrt(statistics.variance(b) / len(b) + statistics.variance(f) / len(f))
    L = [f"# GRPO report: {run.name}", ""]
    cfg = run / "config.json"
    if cfg.exists():
        L += ["Configuration: `" + json.dumps(json.loads(cfg.read_text())) + "`", ""]
    L += ["## Training (training pool only; reward = share of rounds won, 0 for copies)", ""] + training_curve(run)
    L += ["", "## Held-out evaluation hill (never used for training or selection), fresh samples", "",
          "| model | samples | valid | copies | mean reward | best-of-n reward | share with reward > 0 |", "|---|---|---|---|---|---|---|"]
    for name, rows, rw in (("base", base, b), ("after GRPO", final, f)):
        L.append(f"| {name} | {len(rows)} | {sum(r['eval_valid'] for r in rows)} | {sum(r['eval_copy'] for r in rows)} | "
                 f"{statistics.mean(rw):.4f} | {max(rw):.4f} | {sum(x > 0 for x in rw) / len(rw):.2f} |")
    L += ["", f"Difference in mean reward: {mf - mb:+.4f} (95% CI {mf - mb - 1.96 * se:+.4f} to {mf - mb + 1.96 * se:+.4f}, "
          "Welch normal approximation)", "", "Mean reward by archetype asked:", "", "| archetype | base | after GRPO |", "|---|---|---|"]
    for a, _ in ARCHETYPES:
        rb = [r["eval_reward"] for r in base if r["arch"] == a]
        rf = [r["eval_reward"] for r in final if r["arch"] == a]
        if rb and rf:
            L.append(f"| {a} | {statistics.mean(rb):.4f} | {statistics.mean(rf):.4f} |")
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--adapter")
    ap.add_argument("--model")
    ap.add_argument("--n", type=int, default=64)
    ap.add_argument("--max-tokens", type=int)
    ap.add_argument("--seed", type=int, default=1000)
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    a = ap.parse_args()
    run = Path(a.run)
    cfg = json.loads((run / "config.json").read_text()) if (run / "config.json").exists() else {}
    model = a.model or cfg.get("model", "Qwen/Qwen2.5-Coder-7B-Instruct")
    max_tokens = a.max_tokens or cfg.get("max_completion", 768)
    s = sample(model, a.adapter or str(run / "final"), a.n, max_tokens, a.seed)
    base, final = score(s["base"], a.workers), score(s["final"], a.workers)
    write_jsonl(run / "base.eval.jsonl", base)
    write_jsonl(run / "final.eval.jsonl", final)
    text = report(run, base, final)
    (run / "REPORT.md").write_text(text)
    print(text)


if __name__ == "__main__":
    main()
