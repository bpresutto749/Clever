"""GRPO (training/grpo) on a Modal GPU: one H100 for the model, 16 CPU cores for pMARS.

    pip install modal && modal setup                                      # once
    modal run training/grpo/modal_app.py::smoke                           # 2 steps of the real run
    modal run --detach training/grpo/modal_app.py::train --run qwen7b-grpo --max-steps 150
    modal app logs corewar-grpo                                           # follow a detached run
    modal run training/grpo/modal_app.py::evaluate --run qwen7b-grpo     # hidden hill, once
    modal volume get corewar-grpo qwen7b-grpo training/grpo/runs/        # download the run

Runs live on the Modal volume `corewar-grpo` (samples.jsonl, checkpoints, final adapter,
REPORT.md). The model weights are cached on the volume `corewar-hf-cache`.
"""
import subprocess
import threading
from pathlib import Path

import modal

ROOT = Path(__file__).resolve().parents[2]
MODEL = "Qwen/Qwen2.5-Coder-7B-Instruct"

image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("gcc", "make", "libc6-dev")
    .pip_install("trl==1.17.1", "vllm==0.31.0", "peft", "datasets")
    .env({"HF_HOME": "/hf", "PYTHONUNBUFFERED": "1"})
    .add_local_dir(str(ROOT), remote_path="/repo", ignore=[
        "**/.git/**", "**/*.o", "pmars/pmars", "harbor/**", "runs/**", "media/**", "video/**",
        "jobs/**", "training/grpo/runs/**", "training/mlx/runs/**", "**/.venv*/**"])
)
runs = modal.Volume.from_name("corewar-grpo", create_if_missing=True)
hf = modal.Volume.from_name("corewar-hf-cache", create_if_missing=True)
app = modal.App("corewar-grpo", image=image)
GPU = dict(gpu="H100", cpu=16, memory=65536, volumes={"/out": runs, "/hf": hf})


def _run(cmd):
    """Build pMARS for Linux, then run cmd while committing the volumes every 5 minutes, so a
    detached run can be read (and resumed) before it ends."""
    subprocess.run(["make", "-B", "-C", "/repo/pmars", "pmars"], check=True, capture_output=True)
    stop = threading.Event()

    def commit_loop():
        while not stop.wait(300):
            runs.commit()

    t = threading.Thread(target=commit_loop, daemon=True)
    t.start()
    try:
        subprocess.run(cmd, check=True, cwd="/repo/training/grpo")
    finally:
        stop.set()
        runs.commit()
        hf.commit()


@app.function(timeout=8 * 3600, **GPU)
def train(run: str = "qwen7b-grpo", model: str = MODEL, max_steps: int = 150, lr: float = 1e-5,
          tie_weight: float = 0.0, extra: str = ""):
    import os
    os.environ["GRPO_TIE_WEIGHT"] = str(tie_weight)
    _run(["python", "train.py", "--model", model, "--out", f"/out/{run}", "--max-steps", str(max_steps),
          "--lr", str(lr), "--workers", "16", *extra.split()])


@app.function(timeout=3600, **GPU)
def smoke(model: str = MODEL):
    """Two steps of the real configuration: checks the whole loop, gives the time per step and
    the base model's reward distribution (the first two lines of the log)."""
    _run(["python", "train.py", "--model", model, "--out", "/out/smoke", "--max-steps", "2", "--save-steps", "1000",
          "--workers", "16"])


@app.function(timeout=2 * 3600, **GPU)
def evaluate(run: str = "qwen7b-grpo", n: int = 64, adapter: str = ""):
    _run(["python", "evaluate.py", "--run", f"/out/{run}", "--n", str(n), "--workers", "16",
          *(["--adapter", f"/out/{run}/{adapter}"] if adapter else [])])
    print(Path(f"/out/{run}/REPORT.md").read_text())
