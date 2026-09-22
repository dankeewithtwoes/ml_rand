#!/usr/bin/env python3
"""Pull a model using the Ollama API."""

import argparse
import json

import requests


BASE_URL = "http://localhost:11434"


def pull(model: str):
    response = requests.post(
        f"{BASE_URL}/api/pull",
        json={"name": model, "stream": True},
        stream=True,
    )
    response.raise_for_status()

    for line in response.iter_lines():
        if not line:
            continue
        payload = json.loads(line.decode("utf-8"))
        status = payload.get("status", "")
        completed = payload.get("completed")
        total = payload.get("total")
        if completed and total:
            pct = completed / total * 100
            print(f"\r{status}: {pct:.1f}%", end="", flush=True)
        else:
            print(f"\r{status}", end="", flush=True)
    print("\nDone.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="llama3.1")
    args = parser.parse_args()
    pull(args.model)
