#!/usr/bin/env python3
"""Benchmark document parser against ground-truth key-value fields."""
import argparse, json, sys
from pathlib import Path
from parse import extract_text


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ground-truth", default="gt")
    parser.add_argument("--predictions", default="parsed")
    parser.add_argument("--output", default="demo/parser_benchmark.json")
    args = parser.parse_args()

    gt_dir = Path(args.ground_truth)
    pred_dir = Path(args.predictions)
    if not gt_dir.exists() or not pred_dir.exists():
        print("[error] ground-truth and predictions directories are required", file=sys.stderr)
        return 2

    total = matches = 0
    for gt_file in gt_dir.glob("*.json"):
        pred_file = pred_dir / gt_file.name
        if not pred_file.exists():
            continue
        gt = json.loads(gt_file.read_text(encoding="utf-8"))
        pred = json.loads(pred_file.read_text(encoding="utf-8"))
        for key, val in gt.get("key_values", {}).items():
            total += 1
            if str(val).lower() in pred.get("text", "").lower():
                matches += 1

    accuracy = matches / total if total else 0.0
    report = {"field_accuracy": round(accuracy, 2), "fields_checked": total, "matches": matches}
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"[benchmark] field_accuracy={accuracy:.2f} -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
