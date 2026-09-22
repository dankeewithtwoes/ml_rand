#!/usr/bin/env python3
"""Benchmark downstream classifier accuracy trained on synthetic data."""
import argparse, json, sys
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score


def load_dataset(path: Path):
    items = [json.loads(line) for line in path.read_text(encoding="utf-8").strip().splitlines()]
    texts = [i.get("instruction", "") + " " + i.get("output", "") for i in items]
    labels = [i.get("label", "") for i in items]
    return texts, labels


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", default="data/synthetic.jsonl")
    parser.add_argument("--test", default="data/real.jsonl")
    parser.add_argument("--output", default="demo/downstream_benchmark.json")
    args = parser.parse_args()

    train_path = Path(args.train)
    test_path = Path(args.test)
    if not train_path.exists() or not test_path.exists():
        print("[error] train and test files are required for the benchmark", file=sys.stderr)
        return 2

    X_train, y_train = load_dataset(train_path)
    X_test, y_test = load_dataset(test_path)

    model = Pipeline([
        ("tfidf", TfidfVectorizer()),
        ("clf", LogisticRegression(max_iter=1000)),
    ])
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    acc = accuracy_score(y_test, preds)

    report = {"downstream_accuracy": round(acc, 2), "train_size": len(y_train), "test_size": len(y_test)}
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"[benchmark] downstream accuracy={acc:.2f} -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
