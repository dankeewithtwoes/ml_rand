#!/usr/bin/env python3
"""Behavioral tests for latency_stats: happy path and failure modes.

Run from the project directory:  python -m unittest test_latency_stats -v
"""
import statistics
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from latency_stats import percentile, summarize


class TestNearestRankHappyPath(unittest.TestCase):
    def test_known_series_uses_nearest_rank(self):
        # ceil(0.99 * 5) = 5 -> the 5th ordered value, not an interpolation
        self.assertEqual(5, percentile([1, 2, 3, 4, 5], 0.99))
        self.assertEqual(4, summarize([1, 2, 3, 4])["p95"])

    def test_unsorted_input_is_ordered_first(self):
        self.assertEqual(0.5, percentile([0.5, 0.1, 0.3, 0.2, 0.4], 0.99))
        self.assertEqual(0.1, percentile([0.5, 0.1, 0.3, 0.2, 0.4], 0.01))

    def test_summarize_report_shape(self):
        report = summarize([0.2, 0.1, 0.4, 0.3])
        self.assertEqual(4, report["count"])
        self.assertAlmostEqual(0.25, report["mean"])
        self.assertEqual(0.4, report["max"])
        for key in ("p50", "p95", "p99"):
            self.assertIn(key, report)
        # every reported percentile is an actually observed value
        for key in ("p50", "p95", "p99"):
            self.assertIn(report[key], [0.1, 0.2, 0.3, 0.4])


class TestFailureModes(unittest.TestCase):
    def test_invalid_quantile_raises(self):
        for bad in (-0.1, 1.01, 2.0):
            with self.assertRaises(ValueError):
                percentile([1.0, 2.0], bad)

    def test_empty_input_returns_zero_sentinel(self):
        # documented contract: empty samples degrade to 0.0, never raise
        self.assertEqual(0.0, percentile([], 0.95))
        report = summarize([])
        self.assertEqual(0, report["count"])
        self.assertEqual(0.0, report["mean"])
        self.assertEqual(0.0, report["p99"])
        self.assertEqual(0.0, report["max"])

    def test_single_sample_boundary(self):
        for q in (0.0, 0.5, 0.95, 0.99, 1.0):
            self.assertEqual(7.5, percentile([7.5], q))
        # quantile 0 maps to the first rank, quantile 1 to the last
        self.assertEqual(1.0, percentile([1.0, 9.0], 0.0))
        self.assertEqual(9.0, percentile([1.0, 9.0], 1.0))

    def test_small_sample_tail_is_observed_value(self):
        # regression guard: interpolation reports values never observed and
        # under-reports the tail; nearest-rank must equal the observed max here
        sample = [0.412, 0.389, 0.401, 0.376, 0.455, 0.398,
                  0.421, 0.387, 0.512, 0.433, 0.968, 1.214]
        report = summarize(sample)
        self.assertEqual(1.214, report["p95"])
        self.assertEqual(1.214, report["p99"])
        interpolated_p99 = statistics.quantiles(sample, n=100, method="inclusive")[98]
        self.assertLess(interpolated_p99, report["p99"])


if __name__ == "__main__":
    unittest.main()
