#!/usr/bin/env python3
"""Run a Dify Workflow app with version-tracked workflow JSON."""
import argparse, os, sys, json
import requests


def run_workflow(base_url: str, api_key: str, inputs: dict, user: str = "demo"):
    resp = requests.post(
        f"{base_url}/workflows/run",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"inputs": inputs, "response_mode": "blocking", "user": user},
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()
    print(json.dumps(data, indent=2, ensure_ascii=False))
    return data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=os.getenv("DIFY_BASE_URL", "http://localhost/v1"))
    parser.add_argument("--api-key", default=os.getenv("DIFY_API_KEY"))
    parser.add_argument("--input", action="append", default=[], help="key=value input")
    parser.add_argument("--workflow-file", default="workflow_api.json")
    args = parser.parse_args()

    if not args.api_key:
        print("Set DIFY_API_KEY or --api-key")
        sys.exit(1)

    inputs = {}
    for kv in args.input:
        k, v = kv.split("=", 1)
        inputs[k] = v

    run_workflow(args.base_url, args.api_key, inputs)


if __name__ == "__main__":
    main()
