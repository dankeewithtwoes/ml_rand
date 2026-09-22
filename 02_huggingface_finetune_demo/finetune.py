#!/usr/bin/env python3
"""Parameter-efficient instruction tuning with LoRA on a tiny sentiment dataset."""

import argparse
import json
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
            obj = json.loads(line)
            prompt = f"### Instruction:\n{obj['instruction']}\n### Input:\n{obj['input']}\n### Response:\n"
            texts.append(prompt)
            labels.append(1 if obj["output"].lower() == "positive" else 0)
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


def main(data_path: Path, output_dir: Path, epochs: int, batch_size: int, lora_rank: int):
    output_dir.mkdir(parents=True, exist_ok=True)

    dataset = load_jsonl(data_path)
    dataset = dataset.train_test_split(test_size=0.2, seed=42)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    def tok(x):
        return tokenize_function(x, tokenizer, max_length=128)

    tokenized = dataset.map(tok, batched=True, remove_columns=["text"])

    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=2)

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
        evaluation_strategy="epoch",
        save_strategy="epoch",
        logging_steps=5,
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        seed=42,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized["train"],
        eval_dataset=tokenized["test"],
        tokenizer=tokenizer,
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
    args = parser.parse_args()
    main(args.data, args.output_dir, args.epochs, args.batch_size, args.lora_rank)
