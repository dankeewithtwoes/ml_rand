#!/usr/bin/env python3
"""Run inference with a fine-tuned LoRA model."""

import argparse
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForSequenceClassification, AutoTokenizer

LABEL_NAMES = ["negative", "positive"]


def main(model_dir: Path, text: str):
    tokenizer = AutoTokenizer.from_pretrained(model_dir)
    base_model = AutoModelForSequenceClassification.from_pretrained(
        "distilbert-base-uncased", num_labels=2
    )
    model = PeftModel.from_pretrained(base_model, model_dir)
    model.eval()

    prompt = f"### Instruction:\nClassify the sentiment of the following text.\n### Input:\n{text}\n### Response:\n"
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, padding=True, max_length=128)
    with torch.no_grad():
        logits = model(**inputs).logits
        probs = torch.softmax(logits, dim=1)
        pred = logits.argmax(dim=1).item()

    print(f"Text: {text}")
    print(f"Prediction: {LABEL_NAMES[pred]} (confidence {probs[0][pred].item():.4f})")
    print(f"Probabilities: {dict(zip(LABEL_NAMES, probs[0].tolist()))}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-dir", type=Path, default="demo/model/model")
    parser.add_argument("--text", default="This is the best thing I have ever bought!")
    args = parser.parse_args()
    main(args.model_dir, args.text)
