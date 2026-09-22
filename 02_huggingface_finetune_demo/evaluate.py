#!/usr/bin/env python3
"""Evaluate a fine-tuned LoRA model on the test split."""

import argparse
import json
from pathlib import Path

import numpy as np
from peft import PeftModel
from sklearn.metrics import accuracy_score, classification_report, f1_score
from transformers import AutoModelForSequenceClassification, AutoTokenizer


def load_jsonl(path: Path):
    texts, labels = [], []
    with path.open(encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line)
            prompt = f"### Instruction:\n{obj['instruction']}\n### Input:\n{obj['input']}\n### Response:\n"
            texts.append(prompt)
            labels.append(1 if obj["output"].lower() == "positive" else 0)
    return texts, np.array(labels)


def main(model_dir: Path, data_path: Path):
    tokenizer = AutoTokenizer.from_pretrained(model_dir)
    base_model = AutoModelForSequenceClassification.from_pretrained(
        "distilbert-base-uncased", num_labels=2
    )
    model = PeftModel.from_pretrained(base_model, model_dir)
    model.eval()

    texts, labels = load_jsonl(data_path)
    inputs = tokenizer(texts, return_tensors="pt", truncation=True, padding=True, max_length=128)

    with np.errstate(all="ignore"):
        logits = model(**inputs).logits
        preds = logits.argmax(dim=1).numpy()

    print(f"Accuracy: {accuracy_score(labels, preds):.4f}")
    print(f"F1: {f1_score(labels, preds):.4f}\n")
    print(classification_report(labels, preds, target_names=["negative", "positive"]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-dir", type=Path, default="demo/model/model")
    parser.add_argument("--data", type=Path, default="data.jsonl")
    args = parser.parse_args()
    main(args.model_dir, args.data)
