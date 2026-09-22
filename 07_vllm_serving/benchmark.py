#!/usr/bin/env python3
"""Throughput benchmark for vLLM OpenAI-compatible endpoint."""
import argparse, asyncio, json, os, statistics, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from latency_stats import summarize


PROMPTS = [
    "Summarize the concept of retrieval-augmented generation.",
    "Write a one-sentence definition of machine learning.",
    "List three Python best practices.",
    "Explain why CI/CD improves software quality.",
    "What is the purpose of vector databases?",
]


def _call(base_url: str, api_key: str, model: str, prompt: str, max_tokens: int):
    from openai import OpenAI
    client = OpenAI(base_url=base_url, api_key=api_key)
    start = time.time()
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
    )
    latency = time.time() - start
    return {
        "latency_s": round(latency, 3),
        "prompt_tokens": resp.usage.prompt_tokens,
        "completion_tokens": resp.usage.completion_tokens,
        "total_tokens": resp.usage.total_tokens,
    }


def run_benchmark(base_url: str, api_key: str, model: str, concurrency: int, rounds: int, max_tokens: int):
    tasks = [(base_url, api_key, model, PROMPTS[i % len(PROMPTS)], max_tokens) for i in range(concurrency * rounds)]
    start = time.time()
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        results = list(pool.map(lambda a: _call(*a), tasks))
    total_s = time.time() - start
    latencies = [r["latency_s"] for r in results]
    latency = summarize(latencies)
    total_tokens = sum(r["total_tokens"] for r in results)
    return {
        "model": model,
        "concurrency": concurrency,
        "rounds": rounds,
        "max_tokens": max_tokens,
        "total_requests": len(results),
        "total_time_s": round(total_s, 2),
        "total_tokens": total_tokens,
        "throughput_tokens_per_sec": round(total_tokens / total_s, 2) if total_s else 0.0,
        "throughput_requests_per_sec": round(len(results) / total_s, 2) if total_s else 0.0,
        "latency_mean_s": round(statistics.mean(latencies), 3) if latencies else 0.0,
        "latency_p50_s": round(statistics.median(latencies), 3) if latencies else 0.0,
        "latency_p95_s": round(latency["p95"], 3),
        "latency_p99_s": round(latency["p99"], 3),
        "latencies_s": latencies,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8000/v1")
    parser.add_argument("--api-key", default=os.getenv("OPENAI_API_KEY", "dummy"))
    parser.add_argument("--model", default="Qwen/Qwen2.5-1.5B-Instruct")
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--rounds", type=int, default=5)
    parser.add_argument("--max-tokens", type=int, default=128)
    parser.add_argument("--output", default="demo/benchmark.json")
    args = parser.parse_args()

    try:
        import openai
    except Exception as exc:  # pragma: no cover - optional dep
        print(f"[skip] openai SDK unavailable: {exc}")
        return

    result = run_benchmark(args.base_url, args.api_key, args.model, args.concurrency, args.rounds, args.max_tokens)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"Throughput: {result['throughput_tokens_per_sec']} tok/s | "
          f"p50 latency: {result['latency_p50_s']}s | "
          f"Saved {args.output}")


if __name__ == "__main__":
    main()
