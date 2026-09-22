from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path


class RunStore:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        with closing(self._connect()) as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("""CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY, project_id INTEGER NOT NULL, created_at TEXT NOT NULL,
                input_json TEXT NOT NULL, result_json TEXT NOT NULL,
                review_status TEXT NOT NULL DEFAULT 'pending', review_note TEXT NOT NULL DEFAULT ''
            )""")
            db.commit()

    def _connect(self):
        return sqlite3.connect(self.path, timeout=10)

    def add(self, project_id: int, payload: dict, result: dict) -> dict:
        run_id, created = str(uuid.uuid4()), datetime.now(timezone.utc).isoformat()
        with closing(self._connect()) as db:
            db.execute("INSERT INTO runs VALUES (?, ?, ?, ?, ?, 'pending', '')", (run_id, project_id, created, json.dumps(payload, ensure_ascii=False), json.dumps(result, ensure_ascii=False)))
            db.commit()
        return self.get(run_id)

    def get(self, run_id: str) -> dict:
        with closing(self._connect()) as db:
            row = db.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
        if not row:
            raise KeyError(run_id)
        return self._row(row)

    def list(self, limit: int = 100) -> list[dict]:
        with closing(self._connect()) as db:
            rows = db.execute("SELECT * FROM runs ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [self._row(row) for row in rows]

    def review(self, run_id: str, status: str, note: str) -> dict:
        if status not in {"approved", "needs_changes", "rejected", "pending"}:
            raise ValueError("Недопустимый статус review")
        with closing(self._connect()) as db:
            changed = db.execute("UPDATE runs SET review_status = ?, review_note = ? WHERE id = ?", (status, note[:2000], run_id)).rowcount
            db.commit()
        if not changed:
            raise KeyError(run_id)
        return self.get(run_id)

    def delete(self, run_id: str) -> None:
        with closing(self._connect()) as db:
            changed = db.execute("DELETE FROM runs WHERE id = ?", (run_id,)).rowcount
            db.commit()
        if not changed:
            raise KeyError(run_id)

    @staticmethod
    def _row(row: tuple) -> dict:
        return {"id": row[0], "project_id": row[1], "created_at": row[2], "input": json.loads(row[3]), "result": json.loads(row[4]), "review_status": row[5], "review_note": row[6]}
