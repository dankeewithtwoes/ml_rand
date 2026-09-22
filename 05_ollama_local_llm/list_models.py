#!/usr/bin/env python3
"""List locally available Ollama models."""

import requests


BASE_URL = "http://localhost:11434"


def main():
    response = requests.get(f"{BASE_URL}/api/tags")
    response.raise_for_status()
    models = response.json().get("models", [])
    if not models:
        print("No models found. Pull one with: python pull_model.py --model <name>")
        return
    print("Available models:")
    for m in models:
        print(f"  - {m.get('name')} (size: {m.get('size', 0) / 1e9:.2f} GB)")


if __name__ == "__main__":
    main()
