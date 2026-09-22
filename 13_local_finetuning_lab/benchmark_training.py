#!/usr/bin/env python3
"""Benchmark training throughput and memory for a small model."""
import argparse, time
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-model", default="Qwen/Qwen2.5-1.5B-Instruct")
    parser.add_argument("--steps", type=int, default=10)
    args = parser.parse_args()

    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except Exception as exc:
        print(f"[skip] heavy deps unavailable: {exc}")
        return

    start = time.time()
    model = AutoModelForCausalLM.from_pretrained(args.base_model)
    tokenizer = AutoTokenizer.from_pretrained(args.base_model)
    load_time = time.time() - start

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = model.to(device)
    sample = "This is a benchmark sentence for training throughput."
    inputs = tokenizer(sample, return_tensors="pt").to(device)

    start = time.time()
    for _ in range(args.steps):
        outputs = model(**inputs, labels=inputs["input_ids"])
        loss = outputs.loss
        loss.backward()
    elapsed = time.time() - start
    tokens = inputs["input_ids"].shape[1] * args.steps
    peak_vram = torch.cuda.max_memory_allocated() / 1e9 if torch.cuda.is_available() else 0.0

    print(f"load_time={load_time:.2f}s device={device}")
    print(f"steps={args.steps} tokens={tokens} elapsed={elapsed:.2f}s throughput={tokens/elapsed:.2f} tok/s")
    print(f"peak_vram={peak_vram:.2f}GB")


if __name__ == "__main__":
    main()
