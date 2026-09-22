#!/usr/bin/env python3
"""Parse text PDFs and scanned PDFs with local OCR and evidence tracing."""
from __future__ import annotations

import argparse
import json
import sys
from io import BytesIO
from pathlib import Path
from typing import Any

from evidence import attach_evidence, evidence_coverage
from rules import extract_fields


class DocumentReadError(RuntimeError):
    """Raised when a document cannot be read without fabricating text."""


def _ocr_pixmap(pixmap: Any, language: str) -> str:
    """Run the installed local Tesseract engine on a PyMuPDF pixmap."""
    try:
        from PIL import Image
        import pytesseract
    except (ImportError, OSError) as exc:
        raise DocumentReadError(
            "scanned-page OCR requires Pillow and pytesseract; install requirements.txt"
        ) from exc
    try:
        with Image.open(BytesIO(pixmap.tobytes("png"))) as image:
            text = pytesseract.image_to_string(image, lang=language)
    except Exception as exc:
        raise DocumentReadError(
            "local Tesseract OCR failed; install the Tesseract executable and "
            f"language data for '{language}': {exc}"
        ) from exc
    return text.strip()


def _extract_pdf_pages(
    document: Any,
    fitz_module: Any,
    *,
    ocr_language: str,
    ocr_dpi: int,
) -> tuple[str, list[dict[str, Any]]]:
    if ocr_dpi < 72 or ocr_dpi > 600:
        raise DocumentReadError("OCR DPI must be between 72 and 600")
    if not ocr_language.strip():
        raise DocumentReadError("OCR language cannot be empty")

    parts: list[str] = []
    provenance: list[dict[str, Any]] = []
    scale = ocr_dpi / 72.0
    for page_number, page in enumerate(document, start=1):
        try:
            embedded = page.get_text().strip()
        except Exception as exc:
            raise DocumentReadError(f"cannot extract PDF page {page_number}: {exc}") from exc
        if embedded:
            text = embedded
            method = "embedded_text"
        else:
            try:
                pixmap = page.get_pixmap(
                    matrix=fitz_module.Matrix(scale, scale), alpha=False
                )
            except Exception as exc:
                raise DocumentReadError(
                    f"cannot render scanned PDF page {page_number}: {exc}"
                ) from exc
            text = _ocr_pixmap(pixmap, ocr_language)
            method = "tesseract_ocr"
        parts.append(text)
        provenance.append({
            "page": page_number,
            "method": method,
            "characters": len(text),
            **({"ocr_language": ocr_language, "ocr_dpi": ocr_dpi} if method == "tesseract_ocr" else {}),
        })

    if not provenance:
        raise DocumentReadError("PDF has no pages")
    text = "\f".join(parts)
    if not text.strip("\f\n\r\t "):
        raise DocumentReadError("no text was found in the PDF after local OCR")
    return text, provenance


def extract_pdf(
    pdf_path: Path,
    *,
    ocr_language: str = "rus+eng",
    ocr_dpi: int = 200,
) -> tuple[str, list[dict[str, Any]]]:
    try:
        import fitz  # PyMuPDF
    except (ImportError, OSError) as exc:
        raise DocumentReadError(
            "PDF input requires PyMuPDF (pip install -r requirements.txt)"
        ) from exc
    try:
        document = fitz.open(str(pdf_path))
    except Exception as exc:
        raise DocumentReadError(f"cannot open PDF {pdf_path}: {exc}") from exc
    try:
        return _extract_pdf_pages(
            document,
            fitz,
            ocr_language=ocr_language,
            ocr_dpi=ocr_dpi,
        )
    finally:
        close = getattr(document, "close", None)
        if callable(close):
            close()


def extract_text(
    pdf_path: Path,
    *,
    ocr_language: str = "rus+eng",
    ocr_dpi: int = 200,
) -> str:
    """Compatibility wrapper returning PDF text while preserving explicit errors."""
    text, _provenance = extract_pdf(
        pdf_path, ocr_language=ocr_language, ocr_dpi=ocr_dpi
    )
    return text


def read_document(
    path: Path,
    *,
    ocr_language: str = "rus+eng",
    ocr_dpi: int = 200,
) -> tuple[str, list[dict[str, Any]]]:
    """Read plain text or extract PDF pages, returning per-page provenance."""
    if not path.is_file():
        raise DocumentReadError(f"input file does not exist: {path}")
    if path.suffix.lower() in (".txt", ".md"):
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise DocumentReadError(f"cannot read text document {path}: {exc}") from exc
        if not text.strip():
            raise DocumentReadError("text document is empty")
        return text, [{"page": 1, "method": "plain_text", "characters": len(text)}]
    if path.suffix.lower() != ".pdf":
        raise DocumentReadError("supported input types are .pdf, .txt, and .md")
    return extract_pdf(path, ocr_language=ocr_language, ocr_dpi=ocr_dpi)


def read_input(path: Path) -> str:
    """Backward-compatible text-only result for existing callers."""
    text, _provenance = read_document(path)
    return text


def structure_with_llm(text: str) -> dict:
    import os
    try:
        from openai import OpenAI
    except Exception as exc:
        return {"error": f"openai SDK unavailable: {exc}"}
    client = OpenAI(api_key="ollama", base_url=os.getenv("OPENAI_BASE_URL", "http://localhost:11434/v1"))
    model = os.getenv("OLLAMA_MODEL", "llama3.1")
    prompt = (
        "Extract key-value pairs, tables and headings from the document below. "
        "Return valid JSON with keys: title, headings, key_values, tables.\n\n" + text[:3000]
    )
    try:
        resp = client.chat.completions.create(model=model, messages=[{"role": "user", "content": prompt}], temperature=0.2)
        content = resp.choices[0].message.content
        if "```json" in content:
            content = content.split("```json", 1)[1]
        if "```" in content:
            content = content.split("```", 1)[0]
        return json.loads(content)
    except Exception as exc:
        return {"error": str(exc), "raw": content if 'content' in locals() else ""}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--no-llm", action="store_true")
    parser.add_argument("--ocr-language", default="rus+eng")
    parser.add_argument("--ocr-dpi", type=int, default=200)
    args = parser.parse_args()

    source = Path(args.input)
    try:
        text, extraction = read_document(
            source,
            ocr_language=args.ocr_language,
            ocr_dpi=args.ocr_dpi,
        )
    except DocumentReadError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 2
    result = {
        "source": str(source),
        "pages": len(extraction),
        "extraction": extraction,
        "text": text,
    }
    if args.no_llm:
        key_values = extract_fields(text)
        result["structure"] = {"extractor": "rules", "key_values": key_values}
        result["evidence"] = attach_evidence(key_values, text)
        result["evidence_coverage"] = evidence_coverage(result["evidence"])
    else:
        result["structure"] = structure_with_llm(text)
        key_values = result["structure"].get("key_values", {}) if isinstance(result["structure"], dict) else {}
        if isinstance(key_values, dict):
            result["evidence"] = attach_evidence(key_values, text)
            result["evidence_coverage"] = evidence_coverage(result["evidence"])

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.suffix.lower() == ".json":
        out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    else:
        out.write_text(text, encoding="utf-8")
    print(f"[parse] {len(extraction)} pages -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
