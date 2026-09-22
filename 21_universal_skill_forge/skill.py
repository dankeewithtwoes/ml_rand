#!/usr/bin/env python3
"""Validated, discoverable skill packages for provider-neutral tool calling."""
from __future__ import annotations

import importlib.util
import json
import re
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any

from jsonschema import Draft202012Validator

NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_-]{1,63}$")
VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")


class SkillError(RuntimeError):
    """Base exception for invalid or broken skills."""


class SkillValidationError(SkillError):
    """Raised when a manifest, schema, or invocation is invalid."""


@dataclass(frozen=True)
class SkillInfo:
    name: str
    version: str
    description: str
    path: str


class Skill:
    """A trusted local package containing a manifest, schema, and handler."""

    REQUIRED_FILES = ("manifest.json", "schema.json", "handler.py")

    def __init__(self, path: Path | str):
        self.path = Path(path).resolve()
        self._ensure_package()
        self.manifest = self._read_json("manifest.json")
        self.schema = self._read_json("schema.json")
        self._validate_package()
        self.name = self.manifest["name"]
        self.version = self.manifest["version"]
        self.description = self.manifest["description"]
        self._handler: Any | None = None

    def _ensure_package(self) -> None:
        if not self.path.is_dir():
            raise SkillValidationError(f"skill directory does not exist: {self.path}")
        missing = [name for name in self.REQUIRED_FILES if not (self.path / name).is_file()]
        if missing:
            raise SkillValidationError(f"missing skill files: {', '.join(missing)}")

    def _read_json(self, filename: str) -> dict[str, Any]:
        try:
            value = json.loads((self.path / filename).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise SkillValidationError(f"invalid {filename}: {exc}") from exc
        if not isinstance(value, dict):
            raise SkillValidationError(f"{filename} must contain a JSON object")
        return value

    def _validate_package(self) -> None:
        missing = sorted({"name", "version", "description"} - self.manifest.keys())
        if missing:
            raise SkillValidationError(f"manifest missing: {', '.join(missing)}")
        if not NAME_PATTERN.fullmatch(str(self.manifest["name"])):
            raise SkillValidationError("name must be lowercase kebab/snake case (2-64 chars)")
        if not VERSION_PATTERN.fullmatch(str(self.manifest["version"])):
            raise SkillValidationError("version must use semantic versioning, e.g. 1.2.0")
        if not str(self.manifest["description"]).strip():
            raise SkillValidationError("description cannot be empty")
        try:
            Draft202012Validator.check_schema(self.schema)
        except Exception as exc:
            raise SkillValidationError(f"invalid JSON Schema: {exc}") from exc

    @property
    def info(self) -> SkillInfo:
        return SkillInfo(self.name, self.version, self.description, str(self.path))

    def validate_args(self, args: dict[str, Any]) -> None:
        errors = sorted(Draft202012Validator(self.schema).iter_errors(args), key=lambda e: list(e.path))
        if errors:
            raise SkillValidationError(
                f"invalid arguments for {self.name}: " + "; ".join(error.message for error in errors)
            )

    def _load_module(self) -> ModuleType:
        spec = importlib.util.spec_from_file_location(
            f"skillforge_{self.name}_{abs(hash(self.path))}", self.path / "handler.py"
        )
        if spec is None or spec.loader is None:
            raise SkillError(f"cannot load handler for {self.name}")
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except Exception as exc:
            raise SkillError(f"handler import failed for {self.name}: {exc}") from exc
        return module

    def run(self, args: dict[str, Any]) -> Any:
        self.validate_args(args)
        if self._handler is None:
            self._handler = getattr(self._load_module(), "handle", None)
        if not callable(self._handler):
            raise SkillError(f"handler.py for {self.name} must define handle(args)")
        try:
            return self._handler(args)
        except Exception as exc:
            raise SkillError(f"{self.name} failed: {exc}") from exc


def discover_skills(root: Path | str) -> list[Skill]:
    root = Path(root)
    if not root.is_dir():
        raise SkillValidationError(f"skills directory does not exist: {root}")
    skills = []
    for path in sorted((p for p in root.iterdir() if p.is_dir()), key=lambda p: p.name):
        if any((path / name).exists() for name in Skill.REQUIRED_FILES):
            skills.append(Skill(path))
    return skills
