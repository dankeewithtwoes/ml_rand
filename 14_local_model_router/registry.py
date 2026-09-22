#!/usr/bin/env python3
"""Model registry with metadata for local/cloud models."""
import json
from pathlib import Path
from typing import List, Optional


DEFAULT_REGISTRY = {
    "models": [
        {
            "name": "llama3.1",
            "type": "local",
            "url": "http://localhost:11434/v1",
            "cost_per_1k_tokens": 0.0,
            "avg_latency_ms": 800,
            "strengths": ["private", "general", "cheap"],
        },
        {
            "name": "qwen2.5-1.5b",
            "type": "local",
            "url": "http://localhost:8000/v1",
            "cost_per_1k_tokens": 0.0,
            "avg_latency_ms": 300,
            "strengths": ["fast", "coding", "private"],
        },
        {
            "name": "gpt-4o-mini",
            "type": "cloud",
            "url": "https://api.openai.com/v1",
            "cost_per_1k_tokens": 0.00015,
            "avg_latency_ms": 600,
            "strengths": ["reasoning", "instruction"],
        },
    ]
}


class ModelRegistry:
    def __init__(self, path: Path = Path("demo/registry.json")):
        self.path = path
        if not self.path.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.save(DEFAULT_REGISTRY)
        self.data = json.loads(self.path.read_text(encoding="utf-8"))

    def save(self, data: dict):
        self.path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def list(self) -> List[dict]:
        return self.data.get("models", [])

    def get(self, name: str) -> Optional[dict]:
        for m in self.list():
            if m["name"] == name:
                return m
        return None

    def add(self, model: dict):
        self.data["models"] = [m for m in self.list() if m["name"] != model["name"]]
        self.data["models"].append(model)
        self.save(self.data)

    def local_models(self) -> List[dict]:
        return [m for m in self.list() if m["type"] == "local"]
