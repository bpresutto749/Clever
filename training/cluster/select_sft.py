#!/usr/bin/env python3
"""Keep the best valid, original, de-duplicated samples as SFT data (expert iteration).
usage: select_sft.py scored.jsonl [more.jsonl ...] --top 0.25 --out sft.jsonl"""
import argparse
import math
from collections import defaultdict
from common import PROMPT_STYLE, build_prompt, read_jsonl, write_jsonl, core

ap = argparse.ArgumentParser()
ap.add_argument("inp", nargs="+")
ap.add_argument("--top", type=float, default=0.25)
ap.add_argument("--min-score", type=float, default=0.0)
ap.add_argument("--max", type=int, default=0, help="keep at most this many (0 = no limit)")
ap.add_argument("--out", required=True)
a = ap.parse_args()
rows = [r for p in a.inp for r in read_jsonl(p) if r["train_valid"] and not r["train_copy"]]
seen, uniq = set(), []
for r in sorted(rows, key=lambda r: -r["train_score"]):
    key = tuple(core.assemble(r["source"])[0])
    if key in seen:
        continue
    seen.add(key); uniq.append(r)
if PROMPT_STYLE == "arch":
    # The colleague's training/mlx/pick.py: the top fraction OF EACH ARCHETYPE, so that the run
    # cannot collapse onto the cheapest strategy. --min-score and --max (shared equally) still apply.
    from arch_prompts import messages
    by_arch = defaultdict(list)
    for r in uniq:
        if r["train_score"] > 0:
            by_arch[r.get("arch", "free")].append(r)
    keep = []
    for arch, rs in sorted(by_arch.items()):
        k = max(1, math.ceil(len(rs) * a.top))
        if a.max:
            k = min(k, max(1, a.max // len(by_arch)))
        ks = [r for r in rs[:k] if r["train_score"] >= a.min_score]
        keep += ks
        print(f"  {arch:10s} {len(rs):5d} unique originals, kept {len(ks)}" + (f", scores {ks[0]['train_score']:.3f} .. {ks[-1]['train_score']:.3f}" if ks else ""))
    # with FEEDBACK_TURNS, the prompt is the conversation (drafts and sparring results) that led to the kept warrior
    write_jsonl(a.out, [{"prompt": r.get("prompt_messages") or messages(r.get("arch", "free")),
                         "completion": [{"role": "assistant", "content": "```redcode\n" + r["source"].rstrip() + "\n```"}],
                         "train_score": r["train_score"]} for r in keep])
    print(f"{len(rows)} valid originals, {len(uniq)} unique, kept {len(keep)}" if keep else "nothing kept")
else:
    k = max(1, int(len(uniq) * a.top))
    keep = [r for r in uniq[:k] if r["train_score"] >= a.min_score]
    if a.max:
        keep = keep[:a.max]
    prompt = build_prompt()
    # prompt-completion format: TRL trains on the completion (the warrior) only
    write_jsonl(a.out, [{"prompt": [{"role": "user", "content": prompt}],
                         "completion": [{"role": "assistant", "content": "```redcode\n" + r["source"] + "```"}],
                         "train_score": r["train_score"]} for r in keep])
    print(f"{len(rows)} valid originals, {len(uniq)} unique, kept {len(keep)} (min score {keep[-1]['train_score']:.3f})" if keep else "nothing kept")
