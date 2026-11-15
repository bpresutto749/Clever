#!/usr/bin/env python3
"""Sample warriors from a (base or LoRA-tuned) model with vLLM.
usage: generate.py --model Qwen/Qwen2.5-Coder-7B-Instruct [--lora DIR] --n 256 --out samples.jsonl"""
import argparse
import os
from common import PROMPT_STYLE, ROOT, build_prompt, extract, write_jsonl


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--lora")
    ap.add_argument("--n", type=int, default=256)
    ap.add_argument("--temperature", type=float, default=0.9)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    from vllm import LLM, SamplingParams
    from vllm.lora.request import LoRARequest

    llm = LLM(model=a.model, enable_lora=bool(a.lora), max_lora_rank=64, max_model_len=int(os.environ.get("MAX_MODEL_LEN", 16384)), seed=a.seed)
    tok = llm.get_tokenizer()
    lora = LoRARequest("adapter", 1, a.lora) if a.lora else None
    if PROMPT_STYLE == "arch":
        # The colleague's training/mlx protocol: one prompt per archetype, the same number of samples
        # for each, and a reply that starts inside the code block (arch_prompts.py is his prompts.py).
        from arch_prompts import ARCHETYPES, PREFILL, assign, messages, source_of
        archs = assign(a.n)
        names = [n for n, _ in ARCHETYPES if n in archs]
        prompts = [tok.apply_chat_template(messages(n), tokenize=False, add_generation_prompt=True) + PREFILL for n in names]
        sps = [SamplingParams(n=archs.count(n), temperature=a.temperature, top_p=0.95, max_tokens=900,
                              seed=a.seed * 10000 + 2000 * k, stop=["```"]) for k, n in enumerate(names)]
        outs = llm.generate(prompts, sps, lora_request=lora)
        rows = [{"arch": n, "finish": o.finish_reason, "text": o.text, "source": source_of(o.text)}
                for n, out in zip(names, outs) for o in out.outputs]
        turns = int(os.environ.get("FEEDBACK_TURNS", 0))
        if turns:
            # Feedback turns (feedback.py): draft, sparring result, new version; keep the best draft on sparring.
            from feedback import feedback_text, spar_many
            workers = int(os.environ.get("ARENA_WORKERS", 0)) or os.cpu_count()
            dwarf = spar_many([(ROOT / "doc" / "example_dwarf.red").read_text()], workers=1)[0]["score"]
            convo = [messages(r["arch"]) for r in rows]                  # the conversation that led to the current draft
            drafts = [[{"source": r["source"], "prompt": c}] for r, c in zip(rows, convo)]
            for t in range(1, turns + 1):
                fbs = spar_many([d[-1]["source"] for d in drafts], workers=workers)
                for i, fb in enumerate(fbs):
                    drafts[i][-1]["spar"] = fb["score"]
                    convo[i] = convo[i] + [{"role": "assistant", "content": PREFILL + drafts[i][-1]["source"].rstrip() + "\n```"},
                                           {"role": "user", "content": feedback_text(fb, dwarf)}]
                prompts = [tok.apply_chat_template(c, tokenize=False, add_generation_prompt=True) + PREFILL for c in convo]
                sps = [SamplingParams(n=1, temperature=a.temperature, top_p=0.95, max_tokens=900,
                                      seed=a.seed * 10000 + 3000 * t + i, stop=["```"]) for i in range(len(prompts))]
                outs = llm.generate(prompts, sps, lora_request=lora)
                for i, out in enumerate(outs):
                    drafts[i].append({"source": source_of(out.outputs[0].text), "prompt": convo[i]})
                print(f"feedback turn {t}: sparring mean of the previous drafts "
                      f"{sum(fb['score'] or 0.0 for fb in fbs) / len(fbs):.4f}, valid {sum(fb['valid'] for fb in fbs)}/{len(fbs)}", flush=True)
            fbs = spar_many([d[-1]["source"] for d in drafts], workers=workers)
            print(f"last drafts: sparring mean {sum(fb['score'] or 0.0 for fb in fbs) / len(fbs):.4f}, valid {sum(fb['valid'] for fb in fbs)}/{len(fbs)}", flush=True)
            for r, d, fb in zip(rows, drafts, fbs):
                d[-1]["spar"] = fb["score"]
                best = max(range(len(d)), key=lambda j: (d[j]["spar"] if d[j]["spar"] is not None else -1.0, -j))
                r.update(source=d[best]["source"], turn=best, prompt_messages=d[best]["prompt"],
                         spar_by_turn=[x["spar"] for x in d], first_source=d[0]["source"])
        write_jsonl(a.out, [{"i": i, **r} for i, r in enumerate(rows)])
    else:
        prompt = tok.apply_chat_template([{"role": "user", "content": build_prompt()}], tokenize=False, add_generation_prompt=True)
        sp = SamplingParams(n=a.n, temperature=a.temperature, top_p=0.95, max_tokens=3000, seed=a.seed)
        out = llm.generate([prompt], sp, lora_request=lora)[0]
        write_jsonl(a.out, [{"i": i, "text": o.text, "source": extract(o.text)} for i, o in enumerate(out.outputs)])
    print("wrote", a.n, "samples to", a.out)


if __name__ == "__main__":
    main()
