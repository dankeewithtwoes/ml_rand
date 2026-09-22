#!/usr/bin/env python3
"""Prepare and validate instruction-tuning dataset."""
import argparse, json
from pathlib import Path
from data_quality import deterministic_split, validate


def validate_format(items: list) -> bool:
    for item in items:
        if not isinstance(item, dict) or "instruction" not in item or "output" not in item:
            return False
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", default="data/train.jsonl")
    parser.add_argument("--split", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    lines = Path(args.input).read_text(encoding="utf-8").strip().splitlines()
    items = [json.loads(line) for line in lines]
    quality = validate(items)
    if not quality["valid"]:
        raise ValueError(f"Dataset quality check failed: {quality}")

    train, val = deterministic_split(items, args.split, args.seed)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in train), encoding="utf-8")
    val_path = out.with_stem(out.stem + "_val")
    val_path.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in val), encoding="utf-8")
    print(f"[prepare] train={len(train)} val={len(val)} -> {out}, {val_path}")


if __name__ == "__main__":
    main()
