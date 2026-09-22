#!/usr/bin/env python3
"""Export/import Dify workflow DSL for version control."""
import argparse, json, os, sys
from pathlib import Path
import requests


def fetch_workflow(base_url: str, api_key: str, export_format: str = "dsl"):
    url = f"{base_url}/workflows/export" if export_format == "dsl" else f"{base_url}/workflows/export?format=yml"
    resp = requests.get(url, headers={"Authorization": f"Bearer {api_key}"}, timeout=30)
    resp.raise_for_status()
    return resp.text


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=os.getenv("DIFY_BASE_URL", "http://localhost/v1"))
    parser.add_argument("--api-key", default=os.getenv("DIFY_API_KEY"))
    parser.add_argument("--output", default="workflow_api.json")
    parser.add_argument("--import-file")
    args = parser.parse_args()

    if not args.api_key:
        print("Set DIFY_API_KEY or --api-key")
        sys.exit(1)

    if args.import_file:
        data = Path(args.import_file).read_text(encoding="utf-8")
        resp = requests.post(
            f"{args.base_url}/workflows/import",
            headers={"Authorization": f"Bearer {args.api_key}", "Content-Type": "application/json"},
            data=data,
            timeout=60,
        )
        resp.raise_for_status()
        print("[import] ok")
    else:
        dsl = fetch_workflow(args.base_url, args.api_key)
        Path(args.output).write_text(dsl, encoding="utf-8")
        print(f"[export] saved {args.output}")


if __name__ == "__main__":
    main()
