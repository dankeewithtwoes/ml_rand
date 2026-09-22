"""Behavioral tests for sentence-level grounding (offline, stdlib only)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from grounding import sentence_grounding


class SentenceGroundingTests(unittest.TestCase):
    # --- happy path -----------------------------------------------------

    def test_flags_supported_and_unsupported_sentences(self):
        report = sentence_grounding(
            "Paris is in France. Penguins fly to Mars.",
            ["Paris is the capital of France."],
        )
        self.assertTrue(report["sentences"][0]["grounded"])
        self.assertFalse(report["sentences"][1]["grounded"])
        self.assertEqual(0.5, report["grounded_sentence_ratio"])

    def test_case_and_punctuation_are_normalized(self):
        report = sentence_grounding("PARIS, France!", ["paris france"])
        self.assertTrue(report["sentences"][0]["grounded"])
        self.assertEqual(1.0, report["sentences"][0]["coverage"])

    def test_ratio_is_mean_of_sentence_flags(self):
        report = sentence_grounding(
            "Cats are mammals. Dogs are mammals. Rocks fly daily.",
            ["Cats are mammals.", "Dogs are mammals."],
        )
        self.assertEqual(3, len(report["sentences"]))
        self.assertAlmostEqual(2 / 3, report["grounded_sentence_ratio"])

    # --- failure modes --------------------------------------------------

    def test_empty_answer_returns_zero_ratio(self):
        report = sentence_grounding("", ["any evidence"])
        self.assertEqual([], report["sentences"])
        self.assertEqual(0.0, report["grounded_sentence_ratio"])

    def test_empty_contexts_flags_every_sentence(self):
        report = sentence_grounding("Paris is in France.", [])
        self.assertFalse(report["sentences"][0]["grounded"])
        self.assertEqual(0.0, report["sentences"][0]["coverage"])
        self.assertEqual(0.0, report["grounded_sentence_ratio"])

    def test_non_string_answer_rejected(self):
        with self.assertRaises(TypeError):
            sentence_grounding(None, ["evidence"])

    def test_bare_string_contexts_rejected(self):
        # a single string would silently iterate over characters
        with self.assertRaises(TypeError):
            sentence_grounding("Some answer.", "Paris is in France.")

    def test_non_string_context_element_rejected(self):
        with self.assertRaises(TypeError):
            sentence_grounding("Some answer.", ["valid", 42])

    def test_threshold_out_of_range_rejected(self):
        with self.assertRaises(ValueError):
            sentence_grounding("Some answer.", ["evidence"], threshold=1.5)

    # --- boundary cases -------------------------------------------------

    def test_coverage_exactly_at_threshold_is_grounded(self):
        report = sentence_grounding("paris unknown", ["paris"], threshold=0.5)
        self.assertEqual(0.5, report["sentences"][0]["coverage"])
        self.assertTrue(report["sentences"][0]["grounded"])

    def test_strict_threshold_flags_partial_coverage(self):
        answer, contexts = "Paris is a city in France.", ["Paris France"]
        self.assertTrue(sentence_grounding(answer, contexts, threshold=0.35)["sentences"][0]["grounded"])
        strict = sentence_grounding(answer, contexts, threshold=1.0)
        self.assertAlmostEqual(2 / 3, strict["sentences"][0]["coverage"])
        self.assertFalse(strict["sentences"][0]["grounded"])

    def test_termless_sentence_counts_as_neutral(self):
        report = sentence_grounding("OK.", ["unrelated evidence"])
        self.assertEqual(1.0, report["sentences"][0]["coverage"])
        self.assertTrue(report["sentences"][0]["grounded"])


if __name__ == "__main__":
    unittest.main()
