#!/usr/bin/env python3
"""Evaluate a fine-tuned adapter on held-out prompts."""
import argparse, json, math
from pathlib import Path
from data_quality import format_record, validate


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--adapter", default="outputs/lora")
    parser.add_argument("--val-data", default="data/train_val.jsonl")
    parser.add_argument("--output", default="demo/eval.json")
    args = parser.parse_args()

    adapter_path = Path(args.adapter)
    if not adapter_path.exists():
        raise FileNotFoundError(f"Adapter not found: {adapter_path}")

    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from peft import PeftModel, PeftConfig
    except Exception as exc:
        raise RuntimeError(f"Evaluation dependencies unavailable: {exc}") from exc

    val_items = [json.loads(line) for line in Path(args.val_data).read_text(encoding="utf-8").splitlines() if line.strip()]
    print(f"[eval] {len(val_items)} validation items")
    if not val_items or not validate(val_items)["valid"]:
        raise ValueError("Validation set must be non-empty and valid")
    config = PeftConfig.from_pretrained(str(adapter_path))
    tokenizer = AutoTokenizer.from_pretrained(str(adapter_path))
    base = AutoModelForCausalLM.from_pretrained(config.base_model_name_or_path)
    model = PeftModel.from_pretrained(base, str(adapter_path))
    model.eval()
    total_loss, total_tokens = 0.0, 0
    with torch.no_grad():
        for item in val_items:
            text = format_record(item)
            inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=128)
            labels = inputs["input_ids"].clone()
            labels[inputs["attention_mask"] == 0] = -100
            tokens = int((labels[:, 1:] != -100).sum().item())
            if not tokens:
                raise ValueError("Validation item has no target tokens")
            loss = float(model(**inputs, labels=labels).loss.item())
            total_loss += loss * tokens
            total_tokens += tokens
    average_loss = total_loss / total_tokens
    if not math.isfinite(average_loss):
        raise ValueError("Evaluation returned a non-finite loss")
    results = {
        "adapter": str(adapter_path),
        "num_samples": len(val_items),
        "evaluated_tokens": total_tokens,
        "loss": average_loss,
        "perplexity": math.exp(average_loss),
    }
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(results, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    print(f"[eval] saved {args.output}")


if __name__ == "__main__":
    main()
