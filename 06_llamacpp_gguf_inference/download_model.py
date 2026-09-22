#!/usr/bin/env python3
"""Download a GGUF model from Hugging Face with cache."""
from pathlib import Path
import argparse, os, urllib.request

DEFAULT_MODELS = {
    "qwen2.5-1.5b-q4": "https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf",
    "qwen2.5-1.5b-q5": "https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q5_k_m.gguf",
    "qwen2.5-1.5b-q6": "https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q6_k_m.gguf",
}


def download(url: str, dest: Path):
    if dest.exists():
        print(f"[skip] {dest} already exists")
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"[download] {url} -> {dest}")
    urllib.request.urlretrieve(url, dest)
    return dest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="qwen2.5-1.5b-q4")
    parser.add_argument("--url")
    parser.add_argument("--cache-dir", default="models")
    args = parser.parse_args()

    url = args.url or DEFAULT_MODELS.get(args.model)
    if not url:
        raise ValueError(f"Unknown model {args.model}; use --url")
    name = Path(url).name
    dest = Path(args.cache_dir) / name
    download(url, dest)
    print(dest)


if __name__ == "__main__":
    main()
