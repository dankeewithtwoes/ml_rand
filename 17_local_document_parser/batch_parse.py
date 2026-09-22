#!/usr/bin/env python3
"""Batch parse a directory of PDFs."""
import argparse, json, time
from pathlib import Path
from parse import DocumentReadError, read_document, structure_with_llm


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--no-llm", action="store_true")
    parser.add_argument("--ocr-language", default="rus+eng")
    parser.add_argument("--ocr-dpi", type=int, default=200)
    args = parser.parse_args()

    in_dir = Path(args.input_dir)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    start = time.time()
    count = 0
    for pdf_path in sorted(in_dir.glob("*.pdf")):
        try:
            text, extraction = read_document(
                pdf_path,
                ocr_language=args.ocr_language,
                ocr_dpi=args.ocr_dpi,
            )
        except DocumentReadError as exc:
            raise SystemExit(f"[error] {pdf_path}: {exc}") from exc
        result = {
            "source": str(pdf_path),
            "pages": len(extraction),
            "extraction": extraction,
            "text": text,
        }
        if not args.no_llm:
            result["structure"] = structure_with_llm(text)
        out = out_dir / (pdf_path.stem + ".json")
        out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        count += 1
        print(f"  parsed {pdf_path.name}")

    elapsed = time.time() - start
    print(f"[batch] {count} docs in {elapsed:.1f}s ({count/elapsed:.1f} docs/s)")


if __name__ == "__main__":
    main()
