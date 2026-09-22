#!/usr/bin/env python3
"""Ingest a note into the local knowledge store."""
import argparse
from pathlib import Path
from knowledge_store import KnowledgeStore


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--note", required=True, help="Text note to store")
    parser.add_argument("--tags", default="", help="Comma-separated tags")
    parser.add_argument("--store-dir", default="demo/knowledge")
    args = parser.parse_args()

    store = KnowledgeStore(Path(args.store_dir))
    tags = [t.strip() for t in args.tags.split(",") if t.strip()]
    eid = store.add(args.note, tags)
    print(f"[ingest] stored episode {eid} with tags {tags}")


if __name__ == "__main__":
    main()
