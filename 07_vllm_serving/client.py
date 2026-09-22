#!/usr/bin/env python3
"""Minimal OpenAI-compatible client for the vLLM server."""
import argparse, os
from openai import OpenAI


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8000/v1")
    parser.add_argument("--api-key", default=os.getenv("OPENAI_API_KEY", "dummy"))
    parser.add_argument("--model", default="Qwen/Qwen2.5-1.5B-Instruct")
    parser.add_argument("--prompt", default="List three benefits of unit testing.")
    parser.add_argument("--max-tokens", type=int, default=128)
    args = parser.parse_args()

    client = OpenAI(base_url=args.base_url, api_key=args.api_key)
    resp = client.chat.completions.create(
        model=args.model,
        messages=[{"role": "user", "content": args.prompt}],
        max_tokens=args.max_tokens,
    )
    print(resp.choices[0].message.content)
    print(f"prompt_tokens={resp.usage.prompt_tokens} completion_tokens={resp.usage.completion_tokens}")


if __name__ == "__main__":
    main()
