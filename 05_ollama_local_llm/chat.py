#!/usr/bin/env python3
"""Chat with a local model via Ollama API."""

import argparse
import sys

import requests


BASE_URL = "http://localhost:11434"


def generate(model: str, prompt: str, stream: bool = True):
    response = requests.post(
        f"{BASE_URL}/api/generate",
        json={"model": model, "prompt": prompt, "stream": stream},
        stream=stream,
    )
    response.raise_for_status()

    if stream:
        for line in response.iter_lines():
            if not line:
                continue
            data = line.decode("utf-8")
            import json

            payload = json.loads(data)
            print(payload.get("response", ""), end="", flush=True)
            if payload.get("done"):
                print()
                return
    else:
        print(response.json()["response"])


def chat(model: str, messages: list):
    response = requests.post(
        f"{BASE_URL}/api/chat",
        json={"model": model, "messages": messages, "stream": True},
        stream=True,
    )
    response.raise_for_status()

    full_reply = ""
    for line in response.iter_lines():
        if not line:
            continue
        import json

        payload = json.loads(line.decode("utf-8"))
        chunk = payload.get("message", {}).get("content", "")
        print(chunk, end="", flush=True)
        full_reply += chunk
        if payload.get("done"):
            print()
            return full_reply
    return full_reply


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="llama3.1")
    parser.add_argument("--prompt", default="Hello! What can you do?")
    parser.add_argument("--interactive", action="store_true")
    args = parser.parse_args()

    if args.interactive:
        messages = [{"role": "system", "content": "You are a helpful assistant."}]
        print("Interactive mode. Type 'exit' to quit.")
        while True:
            user_input = input("\nYou: ").strip()
            if user_input.lower() in ("exit", "quit"):
                break
            messages.append({"role": "user", "content": user_input})
            print("Model: ", end="")
            reply = chat(args.model, messages)
            messages.append({"role": "assistant", "content": reply})
    else:
        print(f"Model ({args.model}): ", end="")
        generate(args.model, args.prompt)


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("Error: cannot connect to Ollama. Run 'ollama serve' first.", file=sys.stderr)
        sys.exit(1)
