#!/usr/bin/env python3
"""User-owned local memory: SQLite metadata, optional vectors, export and deletion."""
import sqlite3
import time
from contextlib import closing
from pathlib import Path
from typing import List, Optional


class KnowledgeStore:
    def __init__(self, root: Path = Path("demo/knowledge")):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.db_path = root / "metadata.db"
        self.chroma_path = str(root / "chroma_db")
        self._init_sqlite()
        self._init_chroma()

    def _init_sqlite(self):
        with closing(sqlite3.connect(self.db_path)) as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS episodes (
                id INTEGER PRIMARY KEY, content TEXT NOT NULL, tags TEXT,
                created_at REAL, summary TEXT)""")
            conn.commit()

    def _init_chroma(self):
        try:
            import chromadb
            self.client = chromadb.PersistentClient(path=self.chroma_path)
            self.collection = self.client.get_or_create_collection("knowledge")
        except Exception as exc:  # optional dependency
            print(f"[warn] Chroma unavailable: {exc}")
            self.client = self.collection = None

    def add(self, content: str, tags: Optional[List[str]] = None):
        if not content.strip(): raise ValueError("memory content cannot be empty")
        tags, created = tags or [], time.time()
        with closing(sqlite3.connect(self.db_path)) as conn:
            cur = conn.execute("INSERT INTO episodes (content, tags, created_at) VALUES (?, ?, ?)",
                               (content, ",".join(tags), created))
            episode_id = cur.lastrowid
            conn.commit()
        if self.collection is not None:
            self.collection.add(documents=[content], metadatas=[{"tags": ",".join(tags), "created_at": created}], ids=[str(episode_id)])
        return episode_id

    def query(self, question: str, top_k: int = 5) -> List[dict]:
        if top_k < 1: raise ValueError("top_k must be positive")
        if self.collection is None: return self._keyword_search(question, top_k)
        results = self.collection.query(query_texts=[question], n_results=top_k)
        return [{"id": eid, "content": doc, "tags": meta.get("tags", ""),
                 "score": 1.0 - float(distance) if distance is not None else None}
                for doc, meta, eid, distance in zip(results["documents"][0], results["metadatas"][0],
                                                     results["ids"][0], results.get("distances", [[None] * top_k])[0])]

    def _keyword_search(self, question: str, top_k: int = 5) -> List[dict]:
        words = {word.lower().strip(".,!?;:") for word in question.split() if len(word) > 3}
        with closing(sqlite3.connect(self.db_path)) as conn:
            rows = conn.execute("SELECT id, content, tags FROM episodes ORDER BY created_at DESC LIMIT 500").fetchall()
        scored = []
        for eid, content, tags in rows:
            haystack = (content + " " + (tags or "")).lower()
            score = sum(word in haystack for word in words)
            if score: scored.append((score, int(eid), {"id": str(eid), "content": content, "tags": tags or "", "score": score}))
        scored.sort(key=lambda item: (-item[0], -item[1]))
        return [item[2] for item in scored[:top_k]]

    def delete(self, episode_id: int) -> bool:
        with closing(sqlite3.connect(self.db_path)) as conn:
            cur = conn.execute("DELETE FROM episodes WHERE id = ?", (episode_id,))
            conn.commit()
        if self.collection is not None: self.collection.delete(ids=[str(episode_id)])
        return cur.rowcount > 0

    def export(self) -> dict:
        return {"format": "knowledge-os-export", "version": 1, "episodes": self.all_episodes()}

    def summarize_old(self, days: int = 30):
        cutoff = time.time() - days * 86400
        with closing(sqlite3.connect(self.db_path)) as conn:
            rows = conn.execute("SELECT id, content, tags FROM episodes WHERE created_at < ? AND summary IS NULL", (cutoff,)).fetchall()
        if not rows: return []
        tags = sorted({tag for _, _, raw in rows for tag in (raw or "").split(",") if tag})
        summary = f"За последние {days} дней: {len(rows)} записей. Теги: {', '.join(tags)}."
        with closing(sqlite3.connect(self.db_path)) as conn:
            conn.execute("INSERT INTO episodes (content, tags, created_at, summary) VALUES (?, ?, ?, ?)",
                         (summary, "summary", time.time(), "1"))
            conn.commit()
        return [summary]

    def all_episodes(self) -> List[dict]:
        with closing(sqlite3.connect(self.db_path)) as conn:
            rows = conn.execute("SELECT id, content, tags, created_at FROM episodes ORDER BY created_at DESC").fetchall()
        return [{"id": row[0], "content": row[1], "tags": row[2], "created_at": row[3]} for row in rows]
