#!/usr/bin/env python3
"""Client that sends requests to the edge fleet orchestrator."""
import argparse, os
import requests


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:9090/v1/chat/completions")
    parser.add_argument("--prompt", default="Explain edge AI.")
    args = parser.parse_args()

    resp = requests.post(
        args.url,
        json={
            "model": os.getenv("OLLAMA_MODEL", "llama3.1"),
            "messages": [{"role": "user", "content": args.prompt}],
        },
        timeout=120,
    )
    print(resp.json().get("choices", [{}])[0].get("message", {}).get("content", ""))


if __name__ == "__main__":
    main()
