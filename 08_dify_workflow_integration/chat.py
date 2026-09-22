#!/usr/bin/env python3
"""Chat with a Dify Chatbot or Chatflow app."""
import argparse, os, sys
import requests


def chat(base_url: str, api_key: str, query: str, user: str = "demo"):
    resp = requests.post(
        f"{base_url}/chat-messages",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"inputs": {}, "query": query, "response_mode": "blocking", "user": user},
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    print(data.get("answer", ""))
    return data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=os.getenv("DIFY_BASE_URL", "http://localhost/v1"))
    parser.add_argument("--api-key", default=os.getenv("DIFY_API_KEY"))
    parser.add_argument("--query", default="Hello, what can you do?")
    args = parser.parse_args()

    if not args.api_key:
        print("Set DIFY_API_KEY or --api-key")
        sys.exit(1)

    chat(args.base_url, args.api_key, args.query)


if __name__ == "__main__":
    main()
