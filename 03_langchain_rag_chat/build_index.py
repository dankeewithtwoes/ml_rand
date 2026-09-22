#!/usr/bin/env python3
"""Build (or rebuild) the hybrid RAG index from documents/."""
import argparse, shutil
from pathlib import Path
from rag_engine import HybridRAG


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--docs-dir", default="documents")
    parser.add_argument("--persist-dir", default="demo/chroma_db")
    parser.add_argument("--rebuild", action="store_true", help="Remove existing index before building")
    args = parser.parse_args()

    persist_dir = Path(args.persist_dir)
    if args.rebuild and persist_dir.exists():
        shutil.rmtree(persist_dir)

    rag = HybridRAG(docs_dir=Path(args.docs_dir), persist_dir=persist_dir)
    print(f"Index built/loaded from {args.docs_dir} into {persist_dir}")


if __name__ == "__main__":
    main()
