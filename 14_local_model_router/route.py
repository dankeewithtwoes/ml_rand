#!/usr/bin/env python3
"""Route a prompt to the best model based on intent, privacy, cost and latency."""
import argparse, os
from pathlib import Path
from registry import ModelRegistry
from decision import choose, contains_sensitive_data


KEYWORD_RULES = {
    "private": ["password", "secret", "token", "ssn", "personal", "confidential"],
    "code": ["code", "function", "bug", "refactor", "python"],
    "legal": ["contract", "agreement", "clause", "law"],
    "creative": ["story", "poem", "write", "creative"],
}


def classify_intent(prompt: str) -> str:
    lower = prompt.lower()
    for intent, keywords in KEYWORD_RULES.items():
        if any(k in lower for k in keywords):
            return intent
    return "general"


def select_model(registry: ModelRegistry, prompt: str, private: bool) -> dict:
    intent = classify_intent(prompt)
    return choose(registry.list(), intent, private=private or contains_sensitive_data(prompt))["model"]


def call_model(model: dict, prompt: str) -> str:
    try:
        from openai import OpenAI
    except Exception as exc:
        return f"[skip] openai SDK unavailable: {exc}"
    api_key = os.getenv("OPENAI_API_KEY") if model["type"] == "cloud" else "ollama"
    base_url = model["url"]
    if model["type"] == "local" and not os.getenv("OPENAI_API_KEY"):
        api_key = "ollama"
    client = OpenAI(api_key=api_key or "ollama", base_url=base_url)
    model_name = model["name"] if model["type"] == "cloud" else model["name"]
    try:
        resp = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        return resp.choices[0].message.content
    except Exception as exc:
        return f"[skip] model call failed: {exc}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--private", action="store_true")
    parser.add_argument("--registry", default="demo/registry.json")
    args = parser.parse_args()

    reg = ModelRegistry(Path(args.registry))
    model = select_model(reg, args.prompt, args.private)
    print(f"[intent] {classify_intent(args.prompt)}")
    print(f"[router] -> {model['name']} ({model['type']})")
    answer = call_model(model, args.prompt)
    print(f"[answer] {answer}")


if __name__ == "__main__":
    main()
