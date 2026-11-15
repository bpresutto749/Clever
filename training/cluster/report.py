#!/usr/bin/env python3
"""Summarise an expert-iteration run directory as markdown."""
import glob, math, statistics, sys
from pathlib import Path
from common import read_jsonl

d = Path(sys.argv[1])
print(f"# Expert iteration report: {d.name}\n")
print("| round | samples | valid | published copies | mean train score | best train score |")
print("|---|---|---|---|---|---|")
for p in sorted(d.glob("r*.train.jsonl"), key=lambda p: int(p.name[1:].split(".")[0])):
    rows = read_jsonl(p)
    sc = [r["train_score"] for r in rows]
    print(f"| {p.name.split('.')[0]} | {len(rows)} | {sum(r['train_valid'] for r in rows)} | {sum(r['train_copy'] for r in rows)} | "
          f"{statistics.mean(sc):.4f} | {max(sc):.4f} |")


def summ(name):
    p = d / f"{name}.eval.jsonl"
    if not p.exists():
        return None
    rw = [r["eval_reward"] for r in read_jsonl(p)]
    return rw


def by_arch(rows, key):
    out = {}
    for r in rows:
        if "arch" in r:
            out.setdefault(r["arch"], []).append(r[key])
    return out


tr = [(p.name.split(".")[0], by_arch(read_jsonl(p), "train_score"))
      for p in sorted(d.glob("r*.train.jsonl"), key=lambda p: int(p.name[1:].split(".")[0]))]
archs = sorted({a for _, t in tr for a in t})
if archs:
    print("\nMean / best training score by archetype prompt:\n")
    print("| round | " + " | ".join(archs) + " |")
    print("|---" * (len(archs) + 1) + "|")
    for name, t in tr:
        print(f"| {name} | " + " | ".join(f"{statistics.mean(t[a]):.3f} / {max(t[a]):.3f}" if a in t else "-" for a in archs) + " |")


b, f = summ("base"), summ("final")
if b and f:
    mb, mf = statistics.mean(b), statistics.mean(f)
    se = math.sqrt(statistics.variance(b) / len(b) + statistics.variance(f) / len(f))
    print("\nHeld-out evaluation hill (never used for training or selection), fresh samples:\n")
    print("| model | samples | mean reward | best-of-n reward | share with reward > 0 |")
    print("|---|---|---|---|---|")
    for n, r in (("base", b), ("after expert iteration", f)):
        print(f"| {n} | {len(r)} | {statistics.mean(r):.4f} | {max(r):.4f} | {sum(x > 0 for x in r) / len(r):.2f} |")
    print(f"\nDifference in mean reward: {mf - mb:+.4f} (95% CI {mf - mb - 1.96 * se:+.4f} to {mf - mb + 1.96 * se:+.4f}, Welch normal approximation)")
    eb, ef = by_arch(read_jsonl(d / "base.eval.jsonl"), "eval_reward"), by_arch(read_jsonl(d / "final.eval.jsonl"), "eval_reward")
    if eb and ef:
        print("\nBy archetype prompt (mean reward, base -> final):\n")
        for a in sorted(set(eb) & set(ef)):
            print(f"- {a}: {statistics.mean(eb[a]):.3f} -> {statistics.mean(ef[a]):.3f} (best {max(ef[a]):.3f}, n = {len(ef[a])})")

# Feedback turns (FEEDBACK_TURNS): does the sparring result help the model improve its own draft?
for name in ("base", "final"):
    p = d / f"{name}.eval.jsonl"
    rows = [r for r in read_jsonl(p) if "spar_by_turn" in r] if p.exists() else []
    if rows:
        k = len(rows[0]["spar_by_turn"])
        means = [statistics.mean((r["spar_by_turn"][j] or 0.0) for r in rows) for j in range(k)]
        kept = [sum(r["turn"] == j for r in rows) for j in range(k)]
        print(f"\nFeedback turns, {name} model ({len(rows)} samples): mean sparring score of draft 0.."
              f"{k - 1}: " + ", ".join(f"{m:.3f}" for m in means) + "; kept draft (best on sparring): "
              + ", ".join(f"draft {j}: {n}" for j, n in enumerate(kept)))
