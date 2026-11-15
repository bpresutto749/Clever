#!/bin/bash
# Expert iteration on the TRAINING hill only; the evaluation hill is touched once, at the end.
# usage: bash training/run_expert_iteration.sh [MODEL] [ROUNDS] [N]
# Resumable: a step whose output already exists is skipped (preemptable clusters requeue the job).
set -euo pipefail
cd "$(dirname "$0")"
MODEL=${1:-Qwen/Qwen2.5-Coder-7B-Instruct}
ROUNDS=${2:-3}
N=${3:-256}
MIN_SCORE=${MIN_SCORE:-0.2510}     # training-pool score of the best trivial warrior (common.TRAIN_FLOOR)
OUT=runs/$(basename "$MODEL")${RUN_TAG:+-$RUN_TAG}
mkdir -p "$OUT"
todo() { [ ! -s "$1" ]; }          # true if the step's output file is missing or empty
LORA=""
for r in $(seq 0 "$ROUNDS"); do
  todo "$OUT/r$r.samples.jsonl" && python3 generate.py --model "$MODEL" ${LORA:+--lora "$LORA"} --n "$N" --seed "$((r + ${SEED_BASE:-0}))" --out "$OUT/r$r.samples.jsonl"
  todo "$OUT/r$r.train.jsonl" && python3 score.py "$OUT/r$r.samples.jsonl" "$OUT/r$r.train.jsonl" --hill train | tee "$OUT/r$r.train.log"
  [ "$r" = "$ROUNDS" ] && break
  # rounds 0..r only, and an empty selection is a result too: a resumed job must not redo it with later rounds
  SCORED=(); for i in $(seq 0 "$r"); do SCORED+=("$OUT/r$i.train.jsonl"); [ -e "$OUT/r$i.search.jsonl" ] && SCORED+=("$OUT/r$i.search.jsonl"); done
  if [ "${SEARCH:-0}" = 1 ]; then
    # search-augmented variant: mutate the numbers of the best warriors so far, scored on the training pool only
    [ -e "$OUT/r$r.search.jsonl" ] || python3 search.py "${SCORED[@]}" --out "$OUT/r$r.search.jsonl" --minutes "${SEARCH_MINUTES:-15}" --seed "$((r + ${SEED_BASE:-0}))" | tee "$OUT/r$r.search.log"
    SCORED+=("$OUT/r$r.search.jsonl")
  fi
  [ -e "$OUT/r$r.sft.jsonl" ] || python3 select_sft.py "${SCORED[@]}" --top 0.25 --min-score "$MIN_SCORE" ${MAX_KEEP:+--max "$MAX_KEEP"} --out "$OUT/r$r.sft.jsonl"
  if [ -s "$OUT/r$r.sft.jsonl" ]; then
    todo "$OUT/adapter_r$((r+1))/adapter_config.json" && python3 sft_lora.py --model "$MODEL" --data "$OUT/r$r.sft.jsonl" --out "$OUT/adapter_r$((r+1))"
    LORA="$OUT/adapter_r$((r+1))"
  else
    echo "round $r: no sample beats the trivial floor ($MIN_SCORE); no fine-tuning this round"
  fi
done
# Held-out evaluation: base model (round 0 samples) vs final adapter, fresh samples, evaluation hill.
todo "$OUT/base.eval.samples.jsonl" && python3 generate.py --model "$MODEL" --n "${EVAL_N:-64}" --seed "$((1000 + ${SEED_BASE:-0}))" --out "$OUT/base.eval.samples.jsonl"
todo "$OUT/base.eval.jsonl" && python3 score.py "$OUT/base.eval.samples.jsonl" "$OUT/base.eval.jsonl" --hill eval --rounds 100 | tee "$OUT/base.eval.log"
todo "$OUT/final.eval.samples.jsonl" && python3 generate.py --model "$MODEL" ${LORA:+--lora "$LORA"} --n "${EVAL_N:-64}" --seed "$((1000 + ${SEED_BASE:-0}))" --out "$OUT/final.eval.samples.jsonl"
todo "$OUT/final.eval.jsonl" && python3 score.py "$OUT/final.eval.samples.jsonl" "$OUT/final.eval.jsonl" --hill eval --rounds 100 | tee "$OUT/final.eval.log"
python3 report.py "$OUT" > "$OUT/REPORT.md"
cat "$OUT/REPORT.md"
