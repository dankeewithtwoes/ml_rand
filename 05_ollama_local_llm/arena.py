#!/usr/bin/env python3
"""Local LLM arena: run the same prompt through multiple Ollama models and compare."""

import argparse
import json
import sys
import time

import requests


BASE_URL = "http://localhost:11434"


def generate(model: str, prompt: str) -> dict:
    start = time.time()
    response = requests.post(
        f"{BASE_URL}/api/generate",
        json={"model": model, "prompt": prompt, "stream": False},
        timeout=300,
    )
    response.raise_for_status()
    elapsed = time.time() - start
    data = response.json()
    text = data.get("response", "").strip()
    eval_count = data.get("eval_count", 0)
    tokens_per_sec = eval_count / elapsed if elapsed > 0 else 0
    return {
        "model": model,
        "text": text,
        "latency_sec": round(elapsed, 2),
        "tokens": eval_count,
        "tokens_per_sec": round(tokens_per_sec, 2),
    }


def simple_judge(prompt: str, answer: str, judge_model: str) -> int:
    """Ask a judge model to score the answer 1-5."""
    judge_prompt = (
        f"Rate the following answer to the question on a scale of 1 to 5, "
        f"where 5 is excellent. Respond with only a number.\n\n"
        f"Question: {prompt}\nAnswer: {answer}\n\nRating:"
    )
    try:
        response = requests.post(
            f"{BASE_URL}/api/generate",
            json={"model": judge_model, "prompt": judge_prompt, "stream": False},
            timeout=120,
        )
        response.raise_for_status()
        text = response.json().get("response", "").strip()
        score = int("".join(c for c in text if c.isdigit())[:1])
        return max(1, min(5, score))
    except Exception as e:
        print(f"Judge failed: {e}", file=sys.stderr)
        return 0


def main(models: list[str], prompt: str, judge_model: str | None, output: str | None):
    print(f"Arena prompt: {prompt}\n")
    results = []
    for model in models:
        try:
            result = generate(model, prompt)
            results.append(result)
            print(f"[{model}] {result['latency_sec']}s | {result['tokens']} tokens | {result['tokens_per_sec']} tok/s")
        except requests.exceptions.RequestException as e:
            print(f"[{model}] ERROR: {e}")

    if judge_model:
        print(f"\nJudging with {judge_model}...")
        for r in results:
            r["judge_score"] = simple_judge(prompt, r["text"], judge_model)
            print(f"[{r['model']}] judge score: {r['judge_score']}/5")

    print("\n--- Results ---")
    for r in results:
        print(f"\nModel: {r['model']}")
        print(f"Latency: {r['latency_sec']}s | Tokens: {r['tokens']} | Speed: {r['tokens_per_sec']} tok/s")
        if "judge_score" in r:
            print(f"Judge score: {r['judge_score']}/5")
        print(f"Answer: {r['text'][:300]}{'...' if len(r['text']) > 300 else ''}")

    if output:
        with open(output, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\nSaved results to {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", default="llama3.1,phi3", help="Comma-separated model names")
    parser.add_argument("--prompt", default="Explain the concept of retrieval-augmented generation in two sentences.")
    parser.add_argument("--judge", default=None, help="Judge model, e.g. llama3.1")
    parser.add_argument("--output", default="demo/arena_results.json")
    args = parser.parse_args()
    try:
        main(args.models.split(","), args.prompt, args.judge, args.output)
    except requests.exceptions.ConnectionError:
        print("Error: cannot connect to Ollama. Run 'ollama serve' first.", file=sys.stderr)
        sys.exit(1)
