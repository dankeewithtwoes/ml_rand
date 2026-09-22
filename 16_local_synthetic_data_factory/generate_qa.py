#!/usr/bin/env python3
"""Generate an exact-size synthetic QA dataset with a local Ollama model."""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Callable


class GenerationError(RuntimeError):
    """Raised when a complete, valid dataset cannot be generated."""


QA_LINE = re.compile(
    r"^\s*(?:[-*]|\d+[.)])?\s*Q:\s*(?P<question>.+?)\s+A:\s*(?P<answer>.+?)\s*$",
    re.IGNORECASE,
)


def generate_local(prompt: str) -> str:
    """Call a real local OpenAI-compatible Ollama endpoint."""
    try:
        from openai import OpenAI
    except (ImportError, OSError) as exc:
        raise GenerationError(
            "local generation requires the openai package (pip install -r requirements.txt)"
        ) from exc
    model = os.getenv("OLLAMA_MODEL", "llama3.1")
    try:
        client = OpenAI(
            api_key="ollama",
            base_url=os.getenv("OPENAI_BASE_URL", "http://localhost:11434/v1"),
        )
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
        )
        content = response.choices[0].message.content
    except Exception as exc:
        raise GenerationError(f"local Ollama client/generation failed: {exc}") from exc
    if not isinstance(content, str) or not content.strip():
        raise GenerationError("local Ollama returned an empty generation")
    return content


def parse_qa(text: str) -> list[dict[str, str]]:
    """Parse non-empty ``Q: ... A: ...`` records, ignoring prose around them."""
    items: list[dict[str, str]] = []
    for line in text.splitlines():
        match = QA_LINE.match(line)
        if not match:
            continue
        question = match.group("question").strip()
        answer = match.group("answer").strip()
        if question and answer:
            items.append({"instruction": question, "output": answer})
    return items


def generate_dataset(
    topic: str,
    count: int,
    batch_size: int,
    *,
    max_attempts: int | None = None,
    generator: Callable[[str], str] = generate_local,
    progress: Callable[[str], None] | None = print,
) -> list[dict[str, str]]:
    """Generate exactly *count* unique records or raise without partial success."""
    topic = topic.strip()
    if not topic:
        raise GenerationError("schema topic cannot be empty")
    if count <= 0:
        raise GenerationError("count must be positive")
    if batch_size <= 0:
        raise GenerationError("batch size must be positive")
    minimum_batches = (count + batch_size - 1) // batch_size
    if max_attempts is None:
        max_attempts = minimum_batches * 3
    if max_attempts < minimum_batches:
        raise GenerationError(
            f"max attempts ({max_attempts}) cannot produce {count} rows with batch size {batch_size}"
        )

    generated: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for attempt in range(1, max_attempts + 1):
        needed = count - len(generated)
        if needed <= 0:
            break
        requested = min(batch_size, needed)
        prompt = (
            f"Generate exactly {requested} realistic Q&A pairs about {topic}. "
            "Put one pair per line and use exactly this format: Q: ... A: ... "
            "Do not add headings or commentary."
        )
        response = generator(prompt)
        parsed = parse_qa(response)
        accepted = 0
        for item in parsed:
            identity = (item["instruction"].casefold(), item["output"].casefold())
            if identity in seen:
                continue
            seen.add(identity)
            generated.append(item)
            accepted += 1
            if len(generated) == count:
                break
        if progress is not None:
            progress(
                f"[attempt {attempt}/{max_attempts}] accepted {accepted}; "
                f"total {len(generated)}/{count}"
            )

    if len(generated) != count:
        raise GenerationError(
            f"generation stopped with {len(generated)}/{count} valid unique rows after "
            f"{max_attempts} attempts; output was not written"
        )
    return generated


def write_jsonl_atomic(items: list[dict[str, str]], output: Path) -> None:
    """Replace *output* only after the complete JSONL has been serialized."""
    if not items:
        raise GenerationError("refusing to write an empty dataset")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            prefix=f".{output.name}.",
            suffix=".tmp",
            dir=output.parent,
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            for item in items:
                handle.write(json.dumps(item, ensure_ascii=False) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, output)
    except Exception as exc:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        if isinstance(exc, GenerationError):
            raise
        raise GenerationError(f"failed to write dataset atomically: {exc}") from exc


def generate_to_file(
    topic: str,
    count: int,
    batch_size: int,
    output: Path,
    *,
    max_attempts: int | None = None,
    generator: Callable[[str], str] = generate_local,
    progress: Callable[[str], None] | None = print,
) -> list[dict[str, str]]:
    items = generate_dataset(
        topic,
        count,
        batch_size,
        max_attempts=max_attempts,
        generator=generator,
        progress=progress,
    )
    write_jsonl_atomic(items, output)
    return items


def load_topic(schema_path: Path) -> str:
    if not schema_path.is_file():
        raise GenerationError(f"schema file does not exist: {schema_path}")
    try:
        import yaml
    except (ImportError, OSError) as exc:
        raise GenerationError("schema loading requires PyYAML") from exc
    try:
        schema = yaml.safe_load(schema_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise GenerationError(f"cannot read schema {schema_path}: {exc}") from exc
    if not isinstance(schema, dict) or not isinstance(schema.get("topic"), str):
        raise GenerationError("schema must be an object with a non-empty string 'topic'")
    topic = schema["topic"].strip()
    if not topic:
        raise GenerationError("schema topic cannot be empty")
    return topic


def main() -> int:
    parser = argparse.ArgumentParser(description="Fail-closed local synthetic QA generator")
    parser.add_argument("--schema", default="schemas/customer_support.yaml")
    parser.add_argument("--count", type=int, default=10)
    parser.add_argument("--output", default="data/synthetic.jsonl")
    parser.add_argument("--batch-size", type=int, default=5)
    parser.add_argument(
        "--max-attempts",
        type=int,
        default=0,
        help="0 chooses three times the minimum number of batches",
    )
    args = parser.parse_args()
    try:
        topic = load_topic(Path(args.schema))
        items = generate_to_file(
            topic,
            args.count,
            args.batch_size,
            Path(args.output),
            max_attempts=args.max_attempts or None,
        )
        print(f"[generate] saved exactly {len(items)} samples to {args.output}")
        return 0
    except GenerationError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
