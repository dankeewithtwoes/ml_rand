"""Tests for scanned-PDF OCR routing and fail-closed behavior."""
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))

from parse import DocumentReadError, _extract_pdf_pages


class Page:
    def __init__(self, text):
        self.text = text
        self.rendered = False

    def get_text(self):
        return self.text

    def get_pixmap(self, **_kwargs):
        self.rendered = True
        return object()


class OcrRoutingTests(unittest.TestCase):
    def setUp(self):
        self.fitz = SimpleNamespace(Matrix=lambda x, y: (x, y))

    def test_scanned_page_is_rendered_and_sent_to_local_ocr(self):
        scanned = Page("")
        with patch("parse._ocr_pixmap", return_value="Invoice total: 42") as ocr:
            text, provenance = _extract_pdf_pages(
                [scanned], self.fitz, ocr_language="eng", ocr_dpi=200
            )
        self.assertTrue(scanned.rendered)
        ocr.assert_called_once()
        self.assertEqual("Invoice total: 42", text)
        self.assertEqual("tesseract_ocr", provenance[0]["method"])
        self.assertEqual("eng", provenance[0]["ocr_language"])

    def test_embedded_text_does_not_run_ocr(self):
        with patch("parse._ocr_pixmap") as ocr:
            text, provenance = _extract_pdf_pages(
                [Page("native text")], self.fitz, ocr_language="eng", ocr_dpi=200
            )
        ocr.assert_not_called()
        self.assertEqual("native text", text)
        self.assertEqual("embedded_text", provenance[0]["method"])

    def test_ocr_engine_failure_is_explicit_not_empty_text(self):
        with patch("parse._ocr_pixmap", side_effect=DocumentReadError("Tesseract missing")):
            with self.assertRaisesRegex(DocumentReadError, "Tesseract missing"):
                _extract_pdf_pages(
                    [Page("")], self.fitz, ocr_language="rus+eng", ocr_dpi=200
                )

    def test_empty_ocr_result_is_rejected(self):
        with patch("parse._ocr_pixmap", return_value=""):
            with self.assertRaisesRegex(DocumentReadError, "no text was found"):
                _extract_pdf_pages(
                    [Page("")], self.fitz, ocr_language="eng", ocr_dpi=200
                )


if __name__ == "__main__":
    unittest.main()
