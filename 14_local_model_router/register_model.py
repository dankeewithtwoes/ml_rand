#!/usr/bin/env python3
"""Register a model in the local zoo."""
import argparse
from pathlib import Path
from registry import ModelRegistry


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    parser.add_argument("--type", choices=["local", "cloud"], required=True)
    parser.add_argument("--url", required=True)
    parser.add_argument("--cost", type=float, default=0.0)
    parser.add_argument("--latency", type=int, default=500)
    parser.add_argument("--strengths", default="")
    parser.add_argument("--registry", default="demo/registry.json")
    args = parser.parse_args()

    reg = ModelRegistry(Path(args.registry))
    reg.add({
        "name": args.name,
        "type": args.type,
        "url": args.url,
        "cost_per_1k_tokens": args.cost,
        "avg_latency_ms": args.latency,
        "strengths": [s.strip() for s in args.strengths.split(",") if s.strip()],
    })
    print(f"[register] {args.name} ({args.type}) -> {args.url}")


if __name__ == "__main__":
    main()
