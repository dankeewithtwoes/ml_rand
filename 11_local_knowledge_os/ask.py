#!/usr/bin/env python3
"""Ask a question over the local knowledge store."""
import argparse, os
from pathlib import Path
from knowledge_store import KnowledgeStore


def call_local_llm(prompt: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key or "ollama", base_url=base_url)
        if not api_key:
            client = OpenAI(api_key="ollama", base_url="http://localhost:11434/v1")
            model = os.getenv("OLLAMA_MODEL", "llama3.1")
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        return resp.choices[0].message.content
    except Exception as exc:
        print(f"[skip] LLM call failed: {exc}")
        return "[LLM unavailable]"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("question", nargs="+", help="Question")
    parser.add_argument("--store-dir", default="demo/knowledge")
    args = parser.parse_args()

    question = " ".join(args.question)
    store = KnowledgeStore(Path(args.store_dir))
    docs = store.query(question, top_k=5)
    context = "\n\n".join([f"- {d['content']}" for d in docs])
    prompt = (
        "You are a personal knowledge assistant. Answer based only on the context below.\n\n"
        f"Context:\n{context}\n\nQuestion: {question}\nAnswer:"
    )
    answer = call_local_llm(prompt)
    print(f"[ask] {answer}")


if __name__ == "__main__":
    main()
