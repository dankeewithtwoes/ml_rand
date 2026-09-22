"""Tests for exact-size, fail-closed synthetic generation."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))

from generate_qa import GenerationError, generate_local, generate_to_file, parse_qa


class SyntheticGenerationTests(unittest.TestCase):
    def test_parser_accepts_only_complete_pairs(self):
        self.assertEqual(
            [{"instruction": "Question?", "output": "Answer."}],
            parse_qa("heading\n1. Q: Question? A: Answer.\nQ: missing answer"),
        )

    def test_exact_requested_count_is_written(self):
        calls = iter([
            "Q: One? A: First.\nQ: Two? A: Second.",
            "Q: Three? A: Third.",
        ])
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "dataset.jsonl"
            rows = generate_to_file(
                "support",
                3,
                2,
                output,
                max_attempts=2,
                generator=lambda _prompt: next(calls),
                progress=None,
            )
            self.assertEqual(3, len(rows))
            self.assertEqual(3, len(output.read_text(encoding="utf-8").splitlines()))

    def test_malformed_output_is_error_and_existing_file_is_untouched(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "dataset.jsonl"
            output.write_text("known-good\n", encoding="utf-8")
            with self.assertRaisesRegex(GenerationError, "output was not written"):
                generate_to_file(
                    "support",
                    1,
                    1,
                    output,
                    max_attempts=1,
                    generator=lambda _prompt: "not a QA record",
                    progress=None,
                )
            self.assertEqual("known-good\n", output.read_text(encoding="utf-8"))

    def test_duplicates_do_not_satisfy_requested_count(self):
        duplicate = "Q: Same? A: Same answer."
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaisesRegex(GenerationError, "1/2 valid unique rows"):
                generate_to_file(
                    "support",
                    2,
                    1,
                    Path(temp_dir) / "dataset.jsonl",
                    max_attempts=2,
                    generator=lambda _prompt: duplicate,
                    progress=None,
                )

    def test_missing_sdk_is_an_explicit_error(self):
        with patch.dict(sys.modules, {"openai": None}):
            with self.assertRaisesRegex(GenerationError, "openai package"):
                generate_local("generate")


if __name__ == "__main__":
    unittest.main()
