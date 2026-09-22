#!/usr/bin/env python3
"""Example client that calls the guard proxy instead of the LLM directly."""
import argparse, os
from openai import OpenAI


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--proxy", default="http://localhost:11435/v1")
    parser.add_argument("--prompt", default="Hello, what is the weather?")
    parser.add_argument("--model", default=os.getenv("OLLAMA_MODEL", "llama3.1"))
    args = parser.parse_args()

    client = OpenAI(api_key="ollama", base_url=args.proxy)
    try:
        resp = client.chat.completions.create(
            model=args.model,
            messages=[{"role": "user", "content": args.prompt}],
        )
        print(resp.choices[0].message.content)
    except Exception as exc:
        print(f"[client] request blocked or failed: {exc}")


if __name__ == "__main__":
    main()
