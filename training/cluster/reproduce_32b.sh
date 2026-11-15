#!/bin/bash
# Reproduces the best cluster result: Qwen2.5-Coder-32B-Instruct, per-archetype expert
# iteration, 7 generations of 1020 samples, one evaluation on the hidden hill at the end.
#   bash training/cluster/reproduce_32b.sh                      # seed A (reference: 0.011 -> 0.082)
#   SEED_BASE=70000 bash training/cluster/reproduce_32b.sh      # seed B (reference: 0.015 -> 0.059)
# Needs one large GPU (the reference runs used an H200, 141 GB) and the model in the Hugging
# Face cache. Resumable: rerun the same command after an interruption; finished steps are skipped.
set -euo pipefail
cd "$(dirname "$0")/../.."
export PROMPT_STYLE=arch          # the training/mlx protocol: one prompt per archetype
export MIN_SCORE=0                # no selection floor, as in training/mlx/pick.py
export EVAL_N=120                 # held-out samples per model (24 per archetype)
export SFT_LOAD=gpu               # load the 32B weights straight onto the GPU for fine-tuning
export SEED_BASE=${SEED_BASE:-40000}
export RUN_TAG=${RUN_TAG:-repro32-seed$SEED_BASE}
export ARENA_WORKERS=${ARENA_WORKERS:-$(nproc)}
export TOKENIZERS_PARALLELISM=false
[ -x pmars/pmars ] || make -C pmars pmars CC="gcc -std=gnu89" >/dev/null
bash training/cluster/run_expert_iteration.sh Qwen/Qwen2.5-Coder-32B-Instruct 6 1020
