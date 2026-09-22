#!/usr/bin/env python3
"""Evaluate the RAG pipeline with RAGAS-style metrics.

RAGAS itself pulls heavy LLM-as-a-judge dependencies, so this script implements
lightweight rule-based proxies that correlate with the real metrics:
- context_precision: keyword overlap between question and retrieved chunks
- answer_relevancy: embedding similarity between question and answer
- faithfulness: overlap between answer and retrieved context
"""

import argparse
import json
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from rag_engine import HybridRAG


EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def token_overlap(text_a: str, text_b: str) -> float:
    tokens_a = set(text_a.lower().split())
    tokens_b = set(text_b.lower().split())
    if not tokens_a or not tokens_b:
        return 0.0
    return len(tokens_a & tokens_b) / len(tokens_a)


def semantic_similarity(model: SentenceTransformer, a: str, b: str) -> float:
    embeddings = model.encode([a, b])
    return float(cosine_similarity([embeddings[0]], [embeddings[1]])[0][0])


def evaluate(rag: HybridRAG, questions: list, model: SentenceTransformer):
    results = []
    for q in questions:
        response = rag.ask(q)
        answer = response["result"]
        context = " ".join([d.page_content for d in response["source_documents"]])

        ctx_precision = token_overlap(q, context)
        answer_relevancy = semantic_similarity(model, q, answer)
        faithfulness = token_overlap(answer, context)

        results.append({
            "question": q,
            "answer": answer,
            "context_precision": round(ctx_precision, 4),
            "answer_relevancy": round(answer_relevancy, 4),
            "faithfulness": round(faithfulness, 4),
        })

    for key in ["context_precision", "answer_relevancy", "faithfulness"]:
        values = [r[key] for r in results]
        print(f"{key}: mean={np.mean(values):.4f}, min={np.min(values):.4f}, max={np.max(values):.4f}")

    out = Path("demo/eval_results.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    print(f"\nDetailed results saved to {out}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--docs-dir", type=Path, default="documents")
    parser.add_argument("--persist-dir", type=Path, default="demo/chroma_db")
    args = parser.parse_args()

    questions = [
        "What are the benefits of Product A?",
        "How does Product B use AI?",
        "Which product is for enterprise customers?",
    ]

    rag = HybridRAG(args.docs_dir, args.persist_dir)
    model = SentenceTransformer(EMBEDDING_MODEL)
    evaluate(rag, questions, model)
