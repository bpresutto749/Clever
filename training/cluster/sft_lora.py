#!/usr/bin/env python3
"""LoRA fine-tune on selected samples (TRL SFTTrainer; prompt-completion data, so the
loss is on the warrior only).
usage: sft_lora.py --model Qwen/Qwen2.5-Coder-7B-Instruct --data sft.jsonl --out adapters/round1"""
import argparse
import os
from datasets import load_dataset
from peft import LoraConfig
from trl import SFTConfig, SFTTrainer

ap = argparse.ArgumentParser()
ap.add_argument("--model", required=True)
ap.add_argument("--data", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--epochs", type=float, default=2)
ap.add_argument("--lr", type=float, default=1e-4)
a = ap.parse_args()
ds = load_dataset("json", data_files=a.data, split="train").remove_columns(["train_score"])
cfg = SFTConfig(output_dir=a.out, num_train_epochs=a.epochs, learning_rate=a.lr, per_device_train_batch_size=1,
                gradient_accumulation_steps=8, bf16=True, logging_steps=5, save_strategy="no",
                max_length=int(os.environ.get("SFT_MAX_LENGTH", 12288)), report_to=[], gradient_checkpointing=True)
# SFT_TARGETS=q_proj,k_proj,v_proj,o_proj limits the adapter to the attention projections.
targets = os.environ.get("SFT_TARGETS", "all-linear")
peft = LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05, target_modules=targets if targets == "all-linear" else targets.split(","), task_type="CAUSAL_LM")
model, tok = a.model, None
if os.environ.get("SFT_LOAD") == "gpu":
    # Large models: load the weights straight onto the GPU instead of through the host memory.
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    model = AutoModelForCausalLM.from_pretrained(a.model, dtype=torch.bfloat16, device_map={"": 0}, low_cpu_mem_usage=True)
    tok = AutoTokenizer.from_pretrained(a.model)
tr = SFTTrainer(model=model, processing_class=tok, args=cfg, train_dataset=ds, peft_config=peft)
tr.train()
tr.save_model(a.out)
print("saved adapter to", a.out)
