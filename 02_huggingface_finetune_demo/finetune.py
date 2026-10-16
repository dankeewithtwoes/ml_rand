#!/usr/bin/env python3
"""Parameter-efficient instruction tuning with LoRA on a tiny sentiment dataset."""

import argparse
import json
import inspect
from pathlib import Path

import numpy as np
from datasets import Dataset
from peft import LoraConfig, get_peft_model, TaskType
from sklearn.metrics import accuracy_score, f1_score
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    DataCollatorWithPadding,
    Trainer,
    TrainingArguments,
)


MODEL_NAME = "distilbert-base-uncased"
LABEL_NAMES = ["negative", "positive"]


def load_jsonl(path: Path) -> Dataset:
    texts, labels = [], []
    with path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            obj = json.loads(line)
            label = str(obj.get("output", "")).strip().lower()
            if label not in LABEL_NAMES:
                raise ValueError(f"Unknown sentiment label: {label!r}")
            prompt = f"### Instruction:\n{obj['instruction']}\n### Input:\n{obj['input']}\n### Response:\n"
            texts.append(prompt)
            labels.append(LABEL_NAMES.index(label))
    if len(texts) < 2:
        raise ValueError("At least two classification examples are required")
    return Dataset.from_dict({"text": texts, "label": labels})


def tokenize_function(examples, tokenizer, max_length: int):
    return tokenizer(examples["text"], truncation=True, padding="max_length", max_length=max_length)


def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=1)
    return {
        "accuracy": accuracy_score(labels, preds),
        "f1": f1_score(labels, preds, average="binary"),
    }


def main(data_path: Path, output_dir: Path, epochs: int, batch_size: int, lora_rank: int, model_name: str = MODEL_NAME):
    if epochs <= 0 or batch_size <= 0 or lora_rank <= 0:
        raise ValueError("epochs, batch size and LoRA rank must be positive")
    output_dir.mkdir(parents=True, exist_ok=True)

    dataset = load_jsonl(data_path)
    dataset = dataset.train_test_split(test_size=0.2, seed=42)
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    def tok(x):
        return tokenize_function(x, tokenizer, max_length=128)

    tokenized = dataset.map(tok, batched=True, remove_columns=["text"])

    model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=2)

    peft_config = LoraConfig(
        task_type=TaskType.SEQ_CLS,
        r=lora_rank,
        lora_alpha=lora_rank * 2,
        lora_dropout=0.1,
        bias="none",
        target_modules=["q_lin", "v_lin"],
    )
    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()

    training_args = TrainingArguments(
        output_dir=str(output_dir / "checkpoints"),
        num_train_epochs=epochs,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        **{("eval_strategy" if "eval_strategy" in inspect.signature(TrainingArguments).parameters else "evaluation_strategy"): "epoch"},
        save_strategy="epoch",
        logging_steps=5,
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        seed=42,
        report_to="none",
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized["train"],
        eval_dataset=tokenized["test"],
        **{("processing_class" if "processing_class" in inspect.signature(Trainer).parameters else "tokenizer"): tokenizer},
        data_collator=DataCollatorWithPadding(tokenizer),
        compute_metrics=compute_metrics,
    )

    trainer.train()

    model.save_pretrained(output_dir / "model")
    tokenizer.save_pretrained(output_dir / "model")
    print(f"LoRA model saved to {output_dir / 'model'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default="data.jsonl")
    parser.add_argument("--output-dir", type=Path, default="demo/model")
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--lora-rank", type=int, default=8)
    parser.add_argument("--model-name", default=MODEL_NAME)
    args = parser.parse_args()
    main(args.data, args.output_dir, args.epochs, args.batch_size, args.lora_rank, args.model_name)
