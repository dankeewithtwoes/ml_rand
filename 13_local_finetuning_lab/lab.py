#!/usr/bin/env python3
"""Local fine-tuning lab with auto-tune and resource tracking."""
import argparse, json, time
from pathlib import Path


def run_training(train_path: Path, val_path: Path, base_model: str, rank: int, lr: float, epochs: int):
    try:
        import torch
        from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer
        from peft import LoraConfig, get_peft_model, TaskType
        from datasets import Dataset
    except Exception as exc:
        print(f"[skip] heavy deps unavailable: {exc}")
        return {"val_loss": 0.0, "peak_vram_gb": 0.0, "training_time_s": 0.0}

    start = time.time()
    tokenizer = AutoTokenizer.from_pretrained(base_model)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        base_model,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        device_map="auto" if torch.cuda.is_available() else None,
    )
    lora_config = LoraConfig(
        r=rank,
        lora_alpha=rank * 2,
        target_modules=["q_proj", "v_proj"],
        task_type=TaskType.CAUSAL_LM,
    )
    model = get_peft_model(model, lora_config)

    def load_dataset(path: Path):
        items = [json.loads(line) for line in path.read_text(encoding="utf-8").strip().splitlines()]
        return Dataset.from_list([
            {
                "text": f"### Instruction:\n{i['instruction']}\n\n### Response:\n{i['output']}",
            }
            for i in items
        ])

    train_ds = load_dataset(train_path)
    val_ds = load_dataset(val_path)

    def tokenize(examples):
        return tokenizer(examples["text"], truncation=True, padding="max_length", max_length=128)

    train_ds = train_ds.map(tokenize, batched=True)
    val_ds = val_ds.map(tokenize, batched=True)
    train_ds.set_format("torch")
    val_ds.set_format("torch")

    args = TrainingArguments(
        output_dir="outputs/lora",
        num_train_epochs=epochs,
        per_device_train_batch_size=1,
        learning_rate=lr,
        logging_steps=1,
        evaluation_strategy="epoch",
        save_strategy="no",
    )
    trainer = Trainer(model=model, args=args, train_dataset=train_ds, eval_dataset=val_ds)
    trainer.train()
    metrics = trainer.evaluate()
    elapsed = time.time() - start
    peak_vram = torch.cuda.max_memory_allocated() / 1e9 if torch.cuda.is_available() else 0.0
    return {
        "val_loss": metrics.get("eval_loss", 0.0),
        "peak_vram_gb": round(peak_vram, 2),
        "training_time_s": round(elapsed, 2),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/train.jsonl")
    parser.add_argument("--base-model", default="Qwen/Qwen2.5-1.5B-Instruct")
    parser.add_argument("--auto-tune", action="store_true")
    parser.add_argument("--rank", type=int, default=8)
    parser.add_argument("--lr", type=float, default=2e-4)
    parser.add_argument("--epochs", type=int, default=1)
    args = parser.parse_args()

    train_path = Path(args.data)
    val_path = train_path.with_stem(train_path.stem + "_val")
    if not val_path.exists():
        print("[warn] validation file not found, using train file")
        val_path = train_path

    if args.auto_tune:
        candidates = [(4, 5e-4), (8, 2e-4), (16, 1e-4)]
        best = None
        for rank, lr in candidates:
            print(f"[auto-tune] rank={rank} lr={lr}")
            result = run_training(train_path, val_path, args.base_model, rank, lr, args.epochs)
            print(f"  {result}")
            if best is None or result["val_loss"] < best[0]:
                best = (result["val_loss"], rank, lr, result)
        print(f"[auto-tune] best rank={best[1]} lr={best[2]} -> {best[3]}")
    else:
        result = run_training(train_path, val_path, args.base_model, args.rank, args.lr, args.epochs)
        print(result)


if __name__ == "__main__":
    main()
