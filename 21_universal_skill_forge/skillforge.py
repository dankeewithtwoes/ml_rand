#!/usr/bin/env python3
"""Skill Forge CLI: create, discover, validate, inspect, test, and run skills."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from skill import Skill, SkillError, discover_skills

TEMPLATE: dict[str, Any] = {
    "manifest.json": {"name": "{name}", "version": "0.1.0", "description": "Describe this skill."},
    "schema.json": {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {"query": {"type": "string", "minLength": 1}},
        "required": ["query"],
        "additionalProperties": False,
    },
    "handler.py": "def handle(args):\n    return {'result': f\"handled: {args['query']}\"}\n",
    "examples.json": [{"input": {"query": "hello"}, "expected": {"result": "handled: hello"}}],
}


def emit(payload: Any) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def create_skill(name: str, skills_dir: Path, force: bool = False) -> Path:
    skill_dir = skills_dir / name
    if skill_dir.exists() and any(skill_dir.iterdir()) and not force:
        raise SkillError(f"refusing to overwrite non-empty directory: {skill_dir} (use --force)")
    skill_dir.mkdir(parents=True, exist_ok=True)
    for filename, content in TEMPLATE.items():
        value = content if isinstance(content, str) else json.dumps(content, indent=2, ensure_ascii=False)
        (skill_dir / filename).write_text(value.replace("{name}", name), encoding="utf-8")
    Skill(skill_dir)
    return skill_dir


def load_examples(skill: Skill) -> list[dict[str, Any]]:
    path = skill.path / "examples.json"
    if not path.exists():
        raise SkillError(f"{skill.name} has no examples.json")
    try:
        examples = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SkillError(f"invalid examples.json for {skill.name}: {exc}") from exc
    if not isinstance(examples, list) or not examples:
        raise SkillError(f"examples.json for {skill.name} must be a non-empty array")
    return examples


def test_skill(skill: Skill) -> dict[str, Any]:
    cases = []
    for index, case in enumerate(load_examples(skill), start=1):
        if not isinstance(case, dict) or "input" not in case:
            raise SkillError(f"example #{index} must contain input")
        actual = skill.run(case["input"])
        expected = case.get("expected")
        cases.append({"case": index, "ok": expected is None or actual == expected, "actual": actual})
    return {"skill": skill.name, "passed": all(case["ok"] for case in cases), "cases": cases}


def doctor(skills_dir: Path) -> dict[str, Any]:
    try:
        skills = discover_skills(skills_dir)
        errors: list[str] = []
    except SkillError as exc:
        skills, errors = [], [str(exc)]
    return {
        "ok": not errors and bool(skills),
        "python": sys.version.split()[0],
        "skills_dir": str(skills_dir.resolve()),
        "skills": len(skills),
        "errors": errors,
    }


def parse_input(raw: str) -> dict[str, Any]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SkillError(f"--input must be valid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise SkillError("--input must be a JSON object")
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Provider-neutral, testable AI skill packages")
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("create"); create.add_argument("name"); create.add_argument("--skills-dir", default="skills"); create.add_argument("--force", action="store_true")
    listing = sub.add_parser("list"); listing.add_argument("--skills-dir", default="skills")
    inspect = sub.add_parser("inspect"); inspect.add_argument("skill_dir")
    test = sub.add_parser("test"); test.add_argument("skill_dir")
    run = sub.add_parser("run"); run.add_argument("skill_dir"); run.add_argument("--input", required=True)
    health = sub.add_parser("doctor"); health.add_argument("--skills-dir", default="skills")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "create": result = {"created": str(create_skill(args.name, Path(args.skills_dir), args.force))}
        elif args.command == "list": result = [skill.info.__dict__ for skill in discover_skills(args.skills_dir)]
        elif args.command == "inspect":
            skill = Skill(args.skill_dir); result = {"manifest": skill.manifest, "schema": skill.schema, "path": str(skill.path)}
        elif args.command == "test":
            result = test_skill(Skill(args.skill_dir))
            if not result["passed"]: emit(result); return 1
        elif args.command == "run":
            skill = Skill(args.skill_dir); result = {"skill": skill.name, "result": skill.run(parse_input(args.input))}
        else:
            result = doctor(Path(args.skills_dir))
            if not result["ok"]: emit(result); return 1
        emit(result); return 0
    except SkillError as exc:
        emit({"error": str(exc)}); return 2


if __name__ == "__main__":
    raise SystemExit(main())
