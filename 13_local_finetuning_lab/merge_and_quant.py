#!/usr/bin/env python3
"""Merge LoRA adapter with base model and export to GGUF."""
import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--adapter", default="outputs/lora")
    parser.add_argument("--base-model", default="Qwen/Qwen2.5-1.5B-Instruct")
    parser.add_argument("--quant", default="q4_k_m")
    parser.add_argument("--output-dir", default="outputs")
    args = parser.parse_args()

    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from peft import PeftModel
    except Exception as exc:
        print(f"[skip] heavy deps unavailable: {exc}")
        return

    adapter_path = Path(args.adapter)
    if not adapter_path.exists():
        print(f"[skip] adapter not found: {adapter_path}")
        return

    out_dir = Path(args.output_dir) / "merged"
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"[merge] loading base model {args.base_model}")
    base = AutoModelForCausalLM.from_pretrained(args.base_model)
    model = PeftModel.from_pretrained(base, str(adapter_path))
    merged = model.merge_and_unload()
    merged.save_pretrained(out_dir)
    AutoTokenizer.from_pretrained(args.base_model).save_pretrained(out_dir)
    print(f"[merge] saved merged model to {out_dir}")
    print(f"[quant] to quantize run: llama.cpp/convert.py {out_dir} && ./quantize ... {args.quant}")


if __name__ == "__main__":
    main()
