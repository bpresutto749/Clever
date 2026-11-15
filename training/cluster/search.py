#!/usr/bin/env python3
"""Search step of search-augmented expert iteration (optional, SEARCH=1).

Plain expert iteration only re-weights what the model already samples: the best score never
moves. This step adds exploration that the environment itself scores: take the best warriors
found so far, change one to three NUMBERS (never an opcode, a modifier or an addressing mode),
score the variant on the TRAINING pool exactly as score.py does (same copy gates), and keep it
if it beats its parent. The kept variants are written in the same format as scored samples, so
select_sft.py can pick them up as training data. The evaluation hill is never touched here.

usage: search.py scored.jsonl [more.jsonl ...] --out rN.search.jsonl --minutes 15 [--seeds 64] [--seed 0]
"""
import argparse, os, random, re, time
from pathlib import Path
from common import TRAIN_HILL, core, read_jsonl, score_many, write_jsonl

LINE = re.compile(r"^(START)?\s*([A-Z]{3}\.[A-Z]{1,2})\s+(\S)\s*(-?\d+),\s*(\S)\s*(-?\d+)")
MARGIN = 0.003          # a child must beat its parent by this much (50-round scores are noisy)


def listing(src):
    """[[op, modeA, a, modeB, b], ...] and the start index, from pMARS's own listing."""
    with core.Source(src) as s, core.Source(core._DUMMY) as d:
        if s.path is None:
            return None, 0
        p = core.run_pmars(["-r", str(core.ROUNDS), "-f", s.path, d.path], 60)
    ins, start, block = [], 0, 0
    for line in p.stdout.splitlines():
        if line.startswith("Program "):
            block += 1
            continue
        m = LINE.match(line) if block == 1 else None
        if m:
            if m.group(1):
                start = len(ins)
            ins.append([m.group(2), m.group(3), int(m.group(4)), m.group(5), int(m.group(6))])
    return (ins or None), start


def render(ins, start, name):
    body = "\n".join(f"        {op} {ma}{a}, {mb}{b}" for op, ma, a, mb, b in ins)
    return f";redcode-94\n;name {name}\n;assert CORESIZE==8000\n        org {start}\n{body}\n"


def mutate(ins, rng):
    out = [list(x) for x in ins]
    for _ in range(rng.choice([1, 1, 1, 2, 3])):
        i, f = rng.randrange(len(out)), rng.choice([2, 4])
        v, r = out[i][f], rng.random()
        if r < 0.4:
            v += rng.choice([-1, 1]) * rng.randint(1, 8)
        elif r < 0.7:
            v += rng.choice([-1, 1]) * rng.randint(9, 400)
        else:
            v = rng.randint(-3999, 4000)
        out[i][f] = (v + 4000) % 8000 - 4000
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inp", nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--minutes", type=float, default=15)
    ap.add_argument("--seeds", type=int, default=64)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--workers", type=int, default=int(os.environ.get("ARENA_WORKERS", 0)) or os.cpu_count())
    a = ap.parse_args()
    rng, t0 = random.Random(a.seed), time.time()
    rows = [r for p in a.inp if Path(p).exists() for r in read_jsonl(p) if r["train_valid"] and not r["train_copy"]]
    pop, seen = [], set()                      # pop: [score, ins, start, name]
    for r in sorted(rows, key=lambda r: -r["train_score"]):
        if len(pop) >= a.seeds:
            break
        ins, start = listing(r["source"])
        if not ins or tuple(map(tuple, ins)) in seen:
            continue
        seen.add(tuple(map(tuple, ins)))
        m = re.search(r"^;name[ \t]+(.+)$", r["source"], re.M)
        pop.append([r["train_score"], ins, start, re.sub(r"[^\w .-]", "", m.group(1)).strip()[:40] if m else "Warrior"])
    if not pop:
        write_jsonl(a.out, [])
        print("search: no valid original warrior to start from")
        return
    # re-score the starting points in rendered form so parent and child are measured the same way
    res = score_many([render(i, s, n) for _, i, s, n in pop], TRAIN_HILL, 50, a.workers)
    pop = [[x["score"], i, s, n] for x, (_, i, s, n) in zip(res, pop) if x["valid"] and not x["copy"]]
    best0, evals, kept, batch = max((p[0] for p in pop), default=0.0), len(res), [], max(2 * a.workers, 8)
    while pop and time.time() - t0 < a.minutes * 60:
        pop.sort(key=lambda p: -p[0])
        del pop[256:]
        parents = [pop[min(int(rng.expovariate(1 / 12)), len(pop) - 1)] for _ in range(batch)]
        kids = [mutate(p[1], rng) for p in parents]
        srcs = [render(k, p[2], p[3]) for k, p in zip(kids, parents)]
        res = score_many(srcs, TRAIN_HILL, 50, a.workers)
        evals += len(res)
        for x, k, p, src in zip(res, kids, parents, srcs):
            key = tuple(map(tuple, k))
            if x["valid"] and not x["copy"] and x["score"] >= p[0] + MARGIN and key not in seen:
                seen.add(key)
                pop.append([x["score"], k, p[2], p[3]])
                kept.append({"i": len(kept), "text": "```redcode\n" + src + "```", "source": src, "origin": "search",
                             "parent_score": p[0], "train_valid": True, "train_copy": False, "train_score": x["score"],
                             "train_len": x["len"], "train_published_sim": x["published_sim"]})
    write_jsonl(a.out, kept)
    best1 = max([best0] + [k["train_score"] for k in kept])
    print(f"search: {len(pop)} in population, {evals} evaluations in {(time.time() - t0) / 60:.1f} min, "
          f"{len(kept)} improved variants kept, best train score {best0:.4f} -> {best1:.4f}")


if __name__ == "__main__":
    main()
