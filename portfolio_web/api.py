from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

from .engine import catalog, run
from .storage import RunStore

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "portfolio_web" / "static"
DB_PATH = Path(os.getenv("PORTFOLIO_WORKBENCH_DB", str(ROOT / ".app-data" / "portfolio-workbench.sqlite3")))
store = RunStore(DB_PATH)
app = FastAPI(title="Portfolio Workbench", version="1.0.0")


class RunInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    payload: dict[str, Any]


class ReviewInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: str
    note: str = Field(default="", max_length=2000)


@app.get("/api/health")
def health():
    return {"ok": True, "projects": 21, "engine": "local-source-modules"}


@app.get("/api/catalog")
def get_catalog():
    return {"items": catalog()}


@app.post("/api/run/{project_id}")
def execute(project_id: int, body: RunInput):
    encoded_size = len(str(body.payload).encode("utf-8"))
    if encoded_size > 200_000:
        raise HTTPException(413, "Ввод превышает 200 KB")
    try:
        result = run(project_id, body.payload)
        return store.add(project_id, body.payload, result)
    except (KeyError, TypeError, ValueError, RuntimeError) as exc:
        raise HTTPException(422, str(exc)) from exc


@app.get("/api/history")
def history(limit: int = 100):
    return {"items": store.list(max(1, min(limit, 200)))}


@app.post("/api/history/{run_id}/review")
def review(run_id: str, body: ReviewInput):
    try:
        return store.review(run_id, body.status, body.note)
    except KeyError as exc:
        raise HTTPException(404, "Запуск не найден") from exc
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@app.delete("/api/history/{run_id}", status_code=204)
def delete(run_id: str):
    try:
        store.delete(run_id)
    except KeyError as exc:
        raise HTTPException(404, "Запуск не найден") from exc


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


app.mount("/static", StaticFiles(directory=STATIC), name="static")
