# Expert iteration on a GPU cluster (vLLM + TRL)

The code behind `training/CLUSTER_RUNS.md`: the expert-iteration loop of
`training/run_expert_iteration.sh`, with the per-archetype protocol of `training/mlx`, run on
one large GPU with vLLM and TRL, for Qwen2.5-Coder 7B, 14B and 32B.

The files are kept as they ran on 14–15 November 2026. Nothing here changes the environment,
its reward or `arena/core.py`.

## Run

```bash
# from the repository root
python3 -m venv .venv && source .venv/bin/activate
pip install -r training/requirements-gpu.txt          # vLLM 0.11.0, TRL 0.24.0, PEFT 0.17.1
make -C pmars pmars CC="gcc -std=gnu89"
python3 -c "from huggingface_hub import snapshot_download; snapshot_download('Qwen/Qwen2.5-Coder-32B-Instruct')"

bash training/cluster/reproduce_32b.sh                 # 32B, 7 generations of 1020 samples, seed A
SEED_BASE=70000 bash training/cluster/reproduce_32b.sh # seed B
```

The report is written to
`training/cluster/runs/Qwen2.5-Coder-32B-Instruct-repro32-seed<SEED_BASE>/REPORT.md`.
The run is resumable: the same command skips every finished step.

Any other run of `training/CLUSTER_RUNS.md`:

```bash
env PROMPT_STYLE=arch MIN_SCORE=0 EVAL_N=120 SEED_BASE=40000 RUN_TAG=myrun \
    bash training/cluster/run_expert_iteration.sh Qwen/Qwen2.5-Coder-7B-Instruct 4 2040   # model, rounds, samples per round
```

## Files

| file | role |
|---|---|
| `reproduce_32b.sh` | one command for the 32B run |
| `run_expert_iteration.sh` | the loop: generate, score, select, fine-tune, evaluate, report |
| `generate.py` | sampling with vLLM |
| `score.py`, `common.py` | scoring with pMARS on the training pool or the hidden hill |
| `select_sft.py` | selection of the fine-tuning data |
| `sft_lora.py` | LoRA fine-tuning with TRL |
| `report.py` | `REPORT.md` |
| `arch_prompts.py` | the prompts, a byte-identical copy of `training/mlx/prompts.py` |
| `feedback.py` | sparring feedback turns |
| `search.py` | scripted constant search between rounds |

## Options (environment variables)

| variable | effect |
|---|---|
| `PROMPT_STYLE=arch` | per-archetype prompts and selection (`training/mlx` protocol) |
| `PROMPT_STYLE=examples` (default), `primer`, `docs` | one prompt: five example warriors; the strategy primer and Dwarf; the same plus the glossary |
| `MIN_SCORE` | selection floor on the training score (default 0.2510; 0 = none) |
| `FEEDBACK_TURNS=2` | draft, `battle`-style sparring table, new version; best draft on sparring kept |
| `SEARCH=1`, `SEARCH_MINUTES` | scripted constant search between rounds |
| `SEED_BASE`, `RUN_TAG`, `EVAL_N`, `MAX_KEEP` | sampling seeds, run folder name, evaluation samples per model, cap on kept samples |
| `SFT_LOAD=gpu` | load the weights straight onto the GPU for fine-tuning |
| `SFT_TARGETS` | LoRA target modules (default: all linear layers) |
| `ARENA_BATTLE_TIMEOUT` | seconds allowed per pMARS battle (default: the environment's 120) |

## Settings

| | |
|---|---|
| sampling | temperature 0.9, top-p 0.95, at most 900 new tokens |
| scoring for selection | training pool only (30 sparring + 60 training-hill warriors), 50 rounds each |
| selection | valid, not a near-copy of a published warrior, deduplicated; top 25% within each archetype, over all rounds so far |
| fine-tuning | LoRA r = 16, alpha 32, dropout 0.05, lr 1e-4, 2 epochs, batch 1 × accumulation 8; a fresh adapter each round |
| evaluation | hidden hill, 100 rounds per opponent, same sampling seed for base and final |
