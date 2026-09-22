#!/usr/bin/env python3
"""Compress old episodic memories into summary records."""
import argparse
from pathlib import Path
from knowledge_store import KnowledgeStore


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--store-dir", default="demo/knowledge")
    args = parser.parse_args()

    store = KnowledgeStore(Path(args.store_dir))
    summaries = store.summarize_old(days=args.days)
    if summaries:
        print(f"[compress] created {len(summaries)} summary record(s)")
        for s in summaries:
            print(f"  {s}")
    else:
        print("[compress] nothing to compress")


if __name__ == "__main__":
    main()
