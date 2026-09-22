#!/usr/bin/env python3
"""End-to-end offline demo of the distinctive capability:
search, export, and permanently delete local memory.

Runs against a throwaway store in a temp directory. No network, no API keys,
no optional vector dependencies required (SQLite keyword fallback).
"""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from knowledge_store import KnowledgeStore


def main():
    tmp = tempfile.TemporaryDirectory(prefix="knowledge_os_demo_")
    store = KnowledgeStore(Path(tmp.name))

    print("== 1. Ingest personal memories ==")
    notes = [
        ("Meeting with Artem: AI router deadline is Friday", ["work", "meetings"]),
        ("Pasta recipe: 200g pasta, 100g cheese, one egg", ["cooking"]),
        ("Office address: Moscow, Lenina street 10", ["work"]),
        ("Book idea: local-first AI memory as a second brain", ["ideas"]),
    ]
    ids = [store.add(content, tags) for content, tags in notes]
    for episode_id, (content, tags) in zip(ids, notes):
        print(f"  stored #{episode_id}: {content[:60]} (tags={tags})")

    print("\n== 2. Search (top_k=2) ==")
    for question in ("when is the deadline", "how to cook pasta"):
        hits = store.query(question, top_k=2)
        print(f"  Q: {question!r}")
        for hit in hits:
            print(f"    -> #{hit['id']} score={hit['score']}: {hit['content'][:60]}")

    print("\n== 3. Export full memory to portable JSON ==")
    exported = store.export()
    out_path = Path(__file__).parent / "export_before_delete.json"
    out_path.write_text(json.dumps(exported, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  format={exported['format']} version={exported['version']} "
          f"episodes={len(exported['episodes'])} -> {out_path.name}")

    print("\n== 4. Permanently delete one memory ==")
    target = ids[0]
    print(f"  delete(#{target}) -> {store.delete(target)}")
    print(f"  delete(#{target}) again -> {store.delete(target)} (idempotent, already gone)")
    remaining = store.export()["episodes"]
    print(f"  episodes after delete: {len(remaining)} (was {len(notes)})")
    assert all(episode["id"] != target for episode in remaining)
    assert not any(hit["id"] == str(target) for hit in store.query("deadline", top_k=5))
    print("  verified: deleted episode absent from export AND from search results")

    tmp.cleanup()
    print("\nDemo store was temporary; nothing persists on disk except the JSON export above.")


if __name__ == "__main__":
    main()
