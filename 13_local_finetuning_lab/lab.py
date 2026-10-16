#!/usr/bin/env python3
"""Local fine-tuning lab with auto-tune and resource tracking."""
import argparse, inspect, json, math, shutil, time
from pathlib import Path


def run_training(train_path: Path, val_path: Path, base_model: str, rank: int, lr: float, epochs: int, output_dir: str = "outputs/lora"):
    if rank <= 0 or epochs <= 0 or not math.isfinite(lr) or lr <= 0:
        raise ValueError("rank, epochs and learning rate must be positive")
    try:
        import torch
        from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer, DataCollatorForLanguageModeling
        from peft import LoraConfig, get_peft_model, TaskType
        from datasets import Dataset
    except Exception as exc:
        raise RuntimeError(f"Training dependencies unavailable: {exc}") from exc

    from data_quality import fingerprint, format_record, validate
    train_items = [json.loads(line) for line in train_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    val_items = [json.loads(line) for line in val_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not train_items or not val_items or not validate(train_items)["valid"] or not validate(val_items)["valid"]:
        raise ValueError("Training and validation data must be non-empty and valid")
    if {fingerprint(item) for item in train_items} & {fingerprint(item) for item in val_items}:
        raise ValueError("Training/validation overlap detected")

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

    def load_dataset(items):
        return Dataset.from_list([
            {
                "text": format_record(i),
            }
            for i in items
        ])

    train_ds = load_dataset(train_items)
    val_ds = load_dataset(val_items)

    def tokenize(examples):
        return tokenizer(examples["text"], truncation=True, padding="max_length", max_length=128)

    train_ds = train_ds.map(tokenize, batched=True, remove_columns=["text"])
    val_ds = val_ds.map(tokenize, batched=True, remove_columns=["text"])
    train_ds.set_format("torch")
    val_ds.set_format("torch")

    args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=epochs,
        per_device_train_batch_size=1,
        learning_rate=lr,
        logging_steps=1,
        **{("eval_strategy" if "eval_strategy" in inspect.signature(TrainingArguments).parameters else "evaluation_strategy"): "epoch"},
        save_strategy="no",
        report_to="none",
    )
    trainer = Trainer(model=model, args=args, train_dataset=train_ds, eval_dataset=val_ds,
                      data_collator=DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False))
    trainer.train()
    metrics = trainer.evaluate()
    val_loss = float(metrics["eval_loss"])
    if not math.isfinite(val_loss):
        raise ValueError("Evaluation returned a non-finite loss")
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    elapsed = time.time() - start
    peak_vram = torch.cuda.max_memory_allocated() / 1e9 if torch.cuda.is_available() else 0.0
    return {
        "val_loss": val_loss,
        "peak_vram_gb": round(peak_vram, 2),
        "training_time_s": round(elapsed, 2),
        "adapter_path": str(Path(output_dir).resolve()),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/train.jsonl")
    parser.add_argument("--base-model", default="Qwen/Qwen2.5-1.5B-Instruct")
    parser.add_argument("--auto-tune", action="store_true")
    parser.add_argument("--rank", type=int, default=8)
    parser.add_argument("--lr", type=float, default=2e-4)
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--output-dir", default="outputs/lora")
    args = parser.parse_args()

    train_path = Path(args.data)
    val_path = train_path.with_stem(train_path.stem + "_val")
    if not val_path.exists():
        raise FileNotFoundError(f"Validation split missing: {val_path}. Run prepare_data.py first.")

    if args.auto_tune:
        candidates = [(4, 5e-4), (8, 2e-4), (16, 1e-4)]
        best = None
        for rank, lr in candidates:
            print(f"[auto-tune] rank={rank} lr={lr}")
            trial_dir = str(Path(args.output_dir) / f"rank-{rank}-lr-{lr}")
            result = run_training(train_path, val_path, args.base_model, rank, lr, args.epochs, trial_dir)
            print(f"  {result}")
            if best is None or result["val_loss"] < best[0]:
                best = (result["val_loss"], rank, lr, result)
        print(f"[auto-tune] best rank={best[1]} lr={best[2]} -> {best[3]}")
        shutil.copytree(best[3]["adapter_path"], args.output_dir, dirs_exist_ok=True)
    else:
        result = run_training(train_path, val_path, args.base_model, args.rank, args.lr, args.epochs, args.output_dir)
        print(result)


if __name__ == "__main__":
    main()
