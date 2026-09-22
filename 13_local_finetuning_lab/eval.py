#!/usr/bin/env python3
"""Evaluate a fine-tuned adapter on held-out prompts."""
import argparse, json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--adapter", default="outputs/lora")
    parser.add_argument("--val-data", default="data/train_val.jsonl")
    parser.add_argument("--output", default="demo/eval.json")
    args = parser.parse_args()

    adapter_path = Path(args.adapter)
    if not adapter_path.exists():
        print(f"[skip] adapter not found: {adapter_path}")
        return

    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
        from peft import PeftModel
    except Exception as exc:
        print(f"[skip] heavy deps unavailable: {exc}")
        return

    val_items = [json.loads(line) for line in Path(args.val_data).read_text(encoding="utf-8").strip().splitlines()]
    print(f"[eval] {len(val_items)} validation items")
    # In a full implementation, generate and score with ROUGE/BLEU.
    results = {
        "adapter": str(adapter_path),
        "num_samples": len(val_items),
        "perplexity": None,
    }
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(results, indent=2, ensure_ascii=False))
    print(f"[eval] saved {args.output}")


if __name__ == "__main__":
    main()
