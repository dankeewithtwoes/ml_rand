#!/usr/bin/env python3
"""Chat with a hybrid RAG engine (BM25 + dense + reranker)."""

import argparse
from pathlib import Path

from rag_engine import HybridRAG


def main(question: str, docs_dir: Path, persist_dir: Path):
    rag = HybridRAG(docs_dir, persist_dir)
    result = rag.ask(question)
    print(f"\nQ: {question}\n")
    print(f"A: {result['result']}\n")
    print("Sources (after reranking):")
    for doc in result["source_documents"]:
        print(f"  - {doc.metadata.get('source', 'unknown')}: {doc.page_content[:120]}...")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("question", default="What are the benefits of the products?", nargs="?")
    parser.add_argument("--docs-dir", type=Path, default="documents")
    parser.add_argument("--persist-dir", type=Path, default="demo/chroma_db")
    args = parser.parse_args()
    main(args.question, args.docs_dir, args.persist_dir)
