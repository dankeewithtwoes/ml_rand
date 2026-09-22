"""Behavioral tests for src/reliability.py (calibration report).

Covers the happy path, exact hand-computed metrics, bin-boundary edge cases,
and the failure modes the report must reject loudly instead of silently
producing a misleading number. Stdlib only: no torch required.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.reliability import calibration_report


class HappyPathTests(unittest.TestCase):
    def test_perfect_predictions_have_zero_error(self):
        # Mirrors the portfolio proof test test_01_calibration_perfect_predictions.
        report = calibration_report([0.0, 1.0], [0, 1], bins=2)
        self.assertEqual(0.0, report["brier_score"])
        self.assertEqual(0.0, report["expected_calibration_error"])

    def test_hand_computed_brier_and_ece(self):
        # probs=[0.5, 0.5], labels=[0, 1]:
        # brier = (0.25 + 0.25) / 2 = 0.25
        # one occupied bin [0.5, 1.0): confidence 0.5, accuracy 0.5 -> ECE = 0
        report = calibration_report([0.5, 0.5], [0, 1], bins=2)
        self.assertAlmostEqual(0.25, report["brier_score"])
        self.assertAlmostEqual(0.0, report["expected_calibration_error"])

    def test_confidently_wrong_predictions_score_badly(self):
        # The problem this project solves: high confidence, wrong answer.
        # brier = (0.95^2 + 0.95^2) / 2 = 0.9025; each bin is 0.95 off -> ECE = 0.95
        report = calibration_report([0.95, 0.05], [0, 1], bins=2)
        self.assertAlmostEqual(0.9025, report["brier_score"])
        self.assertAlmostEqual(0.95, report["expected_calibration_error"])

    def test_buckets_group_members_with_exact_counts(self):
        report = calibration_report([0.1, 0.2, 0.8], [0, 0, 1], bins=2)
        self.assertEqual(2, len(report["bins"]))
        low, high = report["bins"]
        self.assertEqual(2, low["count"])
        self.assertAlmostEqual(0.15, low["confidence"])
        self.assertAlmostEqual(0.0, low["accuracy"])
        self.assertEqual(1, high["count"])
        self.assertAlmostEqual(0.8, high["confidence"])
        self.assertAlmostEqual(1.0, high["accuracy"])

    def test_single_sample_is_accepted(self):
        report = calibration_report([0.3], [0], bins=10)
        self.assertAlmostEqual(0.09, report["brier_score"])
        self.assertEqual(1, len(report["bins"]))


class EdgeCaseTests(unittest.TestCase):
    def test_probability_exactly_one_lands_in_last_bin(self):
        # Regression guard: p == 1.0 must fall into the final bin even though
        # the bin is half-open [low, high). Without the boundary special case
        # the sample would silently vanish from every bucket.
        report = calibration_report([1.0], [1], bins=10)
        self.assertEqual(1, len(report["bins"]))
        self.assertEqual([0.9, 1.0], report["bins"][0]["range"])
        self.assertEqual(1, report["bins"][0]["count"])

    def test_empty_bins_are_skipped(self):
        report = calibration_report([0.05, 0.95], [0, 1], bins=10)
        self.assertEqual(2, len(report["bins"]))


class FailureModeTests(unittest.TestCase):
    def test_empty_input_rejected(self):
        with self.assertRaises(ValueError):
            calibration_report([], [])

    def test_mismatched_lengths_rejected(self):
        with self.assertRaises(ValueError):
            calibration_report([0.5, 0.6], [1])

    def test_probability_above_one_rejected(self):
        with self.assertRaises(ValueError):
            calibration_report([1.2], [1])

    def test_probability_below_zero_rejected(self):
        with self.assertRaises(ValueError):
            calibration_report([-0.1], [0])

    def test_non_binary_labels_rejected(self):
        with self.assertRaises(ValueError):
            calibration_report([0.5, 0.5], [0, 2])

    def test_zero_bins_rejected(self):
        with self.assertRaises(ValueError):
            calibration_report([0.5], [1], bins=0)


if __name__ == "__main__":
    unittest.main()
