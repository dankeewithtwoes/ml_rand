#!/usr/bin/env python3
"""Compare different GGUF quantization levels for speed and quality."""
from pathlib import Path
import argparse, json, time


def bench(model_path: Path, prompt: str, max_tokens: int):
    try:
        from llama_cpp import Llama
    except Exception as exc:  # pragma: no cover - optional heavy dep
        print(f"[skip] llama-cpp-python unavailable: {exc}")
        return None

    start = time.time()
    llm = Llama(str(model_path), n_ctx=2048, verbose=False)
    load_s = time.time() - start

    start = time.time()
    out = llm(prompt, max_tokens=max_tokens, stop=["User:", "\n\n"])
    gen_s = time.time() - start
    text = out["choices"][0]["text"].strip()
    tokens = out["usage"]["completion_tokens"]
    return {
        "model": model_path.name,
        "load_time_s": round(load_s, 2),
        "generation_time_s": round(gen_s, 2),
        "tokens": tokens,
        "tokens_per_sec": round(tokens / gen_s, 2) if gen_s else 0.0,
        "response": text[:300],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--models-dir", default="models")
    parser.add_argument("--max-tokens", type=int, default=128)
    parser.add_argument("--output", default="demo/benchmark_quant.json")
    args = parser.parse_args()

    prompt = "What is retrieval-augmented generation and why does it reduce hallucinations?"
    results = []
    for path in sorted(Path(args.models_dir).glob("*.gguf")):
        print(f"[bench] {path.name}")
        res = bench(path, prompt, args.max_tokens)
        if res:
            results.append(res)
            print(f"  tokens/sec={res['tokens_per_sec']} load={res['load_time_s']}s gen={res['generation_time_s']}s")

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(results, indent=2, ensure_ascii=False))
    print(f"Saved {args.output}")


if __name__ == "__main__":
    main()
