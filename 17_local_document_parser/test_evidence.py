"""Behavioral tests for the evidence-tracing feature and the offline path.

Run from the project directory:
    python -m unittest test_evidence.py -v
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from evidence import attach_evidence, evidence_coverage
from rules import extract_fields


class EvidenceHappyPathTests(unittest.TestCase):
    def test_fields_are_grounded_with_exact_offsets(self):
        source = "Owner: Alice. Total: $42."
        result = attach_evidence({"total": "$42", "owner": "Alice"}, source)
        self.assertEqual(1.0, evidence_coverage(result))
        for field in result.values():
            self.assertTrue(field["grounded"])
            evidence = field["evidence"]
            self.assertEqual(source[evidence["start"]:evidence["end"]], evidence["quote"])
            self.assertEqual(str(field["value"]), evidence["quote"])

    def test_case_insensitive_match_preserves_original_quote(self):
        source = "BILL TO: Northwind Traders"
        result = attach_evidence({"bill to": "northwind traders"}, source)
        self.assertTrue(result["bill to"]["grounded"])
        self.assertEqual("Northwind Traders", result["bill to"]["evidence"]["quote"])

    def test_non_string_values_are_coerced(self):
        result = attach_evidence({"count": 42}, "items: 42 pcs")
        self.assertTrue(result["count"]["grounded"])
        self.assertEqual("42", result["count"]["evidence"]["quote"])


class EvidenceFailureModeTests(unittest.TestCase):
    def test_hallucinated_field_is_flagged_ungrounded(self):
        result = attach_evidence({"total": "$999"}, "Owner: Alice. Total: $42.")
        self.assertFalse(result["total"]["grounded"])
        self.assertIsNone(result["total"]["evidence"])
        self.assertEqual(0.0, evidence_coverage(result))

    def test_empty_source_flags_everything_ungrounded(self):
        result = attach_evidence({"total": "$42"}, "")
        self.assertFalse(result["total"]["grounded"])
        self.assertEqual(0.0, evidence_coverage(result))

    def test_empty_or_whitespace_value_is_never_grounded(self):
        # str.find("") returns 0, so empty needles must be rejected explicitly.
        result = attach_evidence({"a": "", "b": "   "}, "any source text")
        self.assertFalse(result["a"]["grounded"])
        self.assertFalse(result["b"]["grounded"])
        self.assertEqual(0.0, evidence_coverage(result))

    def test_empty_fields_yield_vacuous_full_coverage(self):
        self.assertEqual({}, attach_evidence({}, "any source"))
        self.assertEqual(1.0, evidence_coverage({}))


class RulesExtractionTests(unittest.TestCase):
    def test_extracts_key_value_lines(self):
        fields = extract_fields("Invoice date: 2026-07-01\nTotal due: $1,204.50\n")
        self.assertEqual({"invoice date": "2026-07-01", "total due": "$1,204.50"}, fields)

    def test_empty_text_yields_no_fields(self):
        self.assertEqual({}, extract_fields(""))

    def test_lines_without_colon_ignored_and_first_duplicate_wins(self):
        fields = extract_fields("just a heading\nTotal: $42\nTotal: $99\n")
        self.assertEqual({"total": "$42"}, fields)


class OfflineCliTests(unittest.TestCase):
    def test_parse_no_llm_produces_grounded_evidence(self):
        project = Path(__file__).resolve().parent
        with tempfile.TemporaryDirectory() as tmp:
            doc = Path(tmp) / "doc.txt"
            out = Path(tmp) / "out.json"
            doc.write_text("Total due: $42\nCurrency: USD\n", encoding="utf-8")
            run = subprocess.run(
                [sys.executable, str(project / "parse.py"), "--input", str(doc),
                 "--output", str(out), "--no-llm"],
                capture_output=True, text=True, cwd=project)
            self.assertEqual(0, run.returncode, run.stderr)
            result = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual("rules", result["structure"]["extractor"])
            self.assertEqual(1.0, result["evidence_coverage"])
            for field in result["evidence"].values():
                self.assertTrue(field["grounded"])
                evidence = field["evidence"]
                self.assertEqual(result["text"][evidence["start"]:evidence["end"]], evidence["quote"])


if __name__ == "__main__":
    unittest.main()
