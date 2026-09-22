#!/usr/bin/env python3
"""Offline calibration demo: know when a classifier is confidently wrong.

Runs src/reliability.calibration_report on:

1. two synthetic edge cases (stdlib only, always available offline);
2. optionally, the validation probabilities of the trained two-moons model
   (requires torch, omegaconf, pyyaml and a checkpoint from train.py).

Usage:
    python examples/run_calibration_demo.py                      # stdlib only
    python examples/run_calibration_demo.py --model demo/model.pt

Writes a machine-readable report to examples/calibration_report.json.
"""
from __future__ import annotations

import argparse
import json
import platform
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.reliability import calibration_report

OUTPUT_PATH = Path(__file__).resolve().parent / "calibration_report.json"


def environment(torch_version: str | None) -> dict:
    return {
        "os": f"{platform.system()} {platform.release()}",
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python": platform.python_version(),
        "torch": torch_version or "not installed / not used",
        "gpu": "none (CPU-only run)",
    }


def synthetic_cases() -> dict:
    return {
        "perfect_predictions": {
            "description": "probabilities match labels exactly",
            "probabilities": [0.0, 1.0, 0.0, 1.0, 1.0, 0.0],
            "labels": [0, 1, 0, 1, 1, 0],
        },
        "confidently_wrong_predictions": {
            "description": "high confidence, wrong class: the failure this project detects",
            "probabilities": [0.95, 0.05, 0.9, 0.1],
            "labels": [0, 1, 0, 1],
        },
    }


def trained_model_case(model_path: Path, config_path: Path) -> dict:
    import torch
    from omegaconf import OmegaConf

    from src.data import get_datasets
    from src.model import TwoLayerNet
    from src.utils import set_seed

    cfg = OmegaConf.load(config_path)
    set_seed(cfg.seed)  # reproduces the exact train/validation permutation
    _, val_ds = get_datasets(cfg)
    X_val, y_val = val_ds.tensors

    model = TwoLayerNet(**cfg.model)
    model.load_state_dict(torch.load(model_path, map_location="cpu", weights_only=True))
    model.eval()
    with torch.no_grad():
        probabilities = torch.softmax(model(X_val), dim=1)[:, 1].tolist()

    labels = [int(v) for v in y_val.tolist()]
    accuracy = sum((p >= 0.5) == bool(y) for p, y in zip(probabilities, labels)) / len(labels)
    return {
        "description": f"trained two-moons model on its validation split ({len(labels)} samples)",
        "model_checkpoint": str(model_path),
        "validation_accuracy": round(accuracy, 6),
        "probabilities": probabilities,
        "labels": labels,
        "torch_version": torch.__version__,
    }


def summarize(case: dict, bins: int) -> dict:
    report = calibration_report(case["probabilities"], case["labels"], bins=bins)
    return {
        "description": case["description"],
        "samples": len(case["labels"]),
        "bins": bins,
        "brier_score": round(report["brier_score"], 6),
        "expected_calibration_error": round(report["expected_calibration_error"], 6),
        "buckets": [
            {
                "range": [round(b["range"][0], 2), round(b["range"][1], 2)],
                "count": b["count"],
                "confidence": round(b["confidence"], 6),
                "accuracy": round(b["accuracy"], 6),
            }
            for b in report["bins"]
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", help="optional checkpoint from train.py (requires torch)")
    parser.add_argument("--config", default=str(PROJECT_ROOT / "configs" / "config.yaml"))
    parser.add_argument("--bins", type=int, default=10)
    args = parser.parse_args()

    cases = synthetic_cases()
    torch_version = None
    trained = None
    if args.model:
        trained = trained_model_case(Path(args.model), Path(args.config))
        torch_version = trained.pop("torch_version")
        cases["trained_two_moons_model"] = trained

    results = {name: summarize(case, args.bins) for name, case in cases.items()}
    if trained is not None:
        results["trained_two_moons_model"]["validation_accuracy"] = trained["validation_accuracy"]
        results["trained_two_moons_model"]["model_checkpoint"] = trained["model_checkpoint"]

    document = {
        "artifact": "calibration report",
        "environment": environment(torch_version),
        "results": results,
    }
    OUTPUT_PATH.write_text(json.dumps(document, indent=2), encoding="utf-8")

    for name, result in results.items():
        line = (
            f"[{name}] n={result['samples']} "
            f"brier={result['brier_score']:.6f} ece={result['expected_calibration_error']:.6f}"
        )
        if "validation_accuracy" in result:
            line += f" val_acc={result['validation_accuracy']:.4f}"
        print(line)
    print(f"Report written to {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
