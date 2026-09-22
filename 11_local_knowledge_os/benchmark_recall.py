#!/usr/bin/env python3
"""Benchmark recall@k on a small synthetic personal knowledge dataset."""
import shutil
from pathlib import Path
from knowledge_store import KnowledgeStore


FACTS = [
    ("Моя машина — Toyota Camry 2020, номер А123БВ777.", "какая у меня машина", []),
    ("Встреча с Артёмом: обсудили AI-роутер, дедлайн пятница.", "когда дедлайн по проекту с Артёмом", []),
    ("Рецепт пасты: 200г макарон, 100г сыра, яйцо.", "из чего паста", []),
    ("Адрес офиса: Москва, ул. Ленина, 10.", "где офис", []),
]


def main():
    store_dir = Path("demo/knowledge_benchmark")
    if store_dir.exists():
        shutil.rmtree(store_dir)
    store = KnowledgeStore(store_dir)
    for content, _, tags in FACTS:
        store.add(content, tags)

    correct = 0
    k = 3
    for content, question, _ in FACTS:
        results = store.query(question, top_k=k)
        found = any(content in r["content"] for r in results)
        if found:
            correct += 1
        print(f"  {question[:40]:40} -> {'FOUND' if found else 'MISS'}")

    recall = correct / len(FACTS)
    print(f"\n[benchmark] recall@{k}: {recall:.2f}")


if __name__ == "__main__":
    main()
