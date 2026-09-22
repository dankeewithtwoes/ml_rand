#!/usr/bin/env python3
"""Simple GGUF inference with llama.cpp (optional dependency)."""
from pathlib import Path
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, help="Path to .gguf file")
    parser.add_argument("--prompt", default="Explain quantization in LLMs.")
    parser.add_argument("--max-tokens", type=int, default=256)
    args = parser.parse_args()

    model_path = Path(args.model)
    if not model_path.exists():
        print(f"Model not found: {model_path}")
        raise SystemExit(1)

    try:
        from llama_cpp import Llama
    except Exception as exc:  # pragma: no cover - optional heavy dep
        print(f"[skip] llama-cpp-python unavailable: {exc}")
        print(f"Would generate answer for: {args.prompt}")
        return

    llm = Llama(str(model_path), n_ctx=2048, verbose=False)
    out = llm(args.prompt, max_tokens=args.max_tokens, stop=["User:", "\n\n"])
    print(out["choices"][0]["text"].strip())


if __name__ == "__main__":
    main()
