import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from compare_safety import safety_score_with_uncertainty
from safety_metrics import evaluate, wilson_interval


def record(success=None, response="model answer"):
    item = {"response": response}
    if success is not None:
        item["success"] = success
    return item


class EvaluateHappyPathTests(unittest.TestCase):
    def test_happy_path_mixed_results(self):
        report = evaluate([
            record(success=True, response="complied"),
            record(success=False, response="I'm sorry, I can't"),
            record(response="[error: Connection refused]"),
        ])
        self.assertEqual(2, report["evaluated"])
        self.assertEqual(1, report["excluded_errors"])
        self.assertAlmostEqual(0.5, report["attack_success_rate"])
        low, high = report["attack_success_ci95"]
        self.assertLessEqual(low, 0.5)
        self.assertLessEqual(0.5, high)
        self.assertGreaterEqual(low, 0.0)
        self.assertLessEqual(high, 1.0)

    def test_rate_counts_only_successful_attacks_over_valid(self):
        report = evaluate([record(success=True)] * 3 + [record(success=False)] * 7)
        self.assertEqual(10, report["evaluated"])
        self.assertAlmostEqual(0.3, report["attack_success_rate"])


class EvaluateFailureModeTests(unittest.TestCase):
    def test_empty_input_returns_zero_report_without_raising(self):
        report = evaluate([])
        self.assertEqual(0, report["evaluated"])
        self.assertEqual(0, report["excluded_errors"])
        self.assertEqual(0.0, report["attack_success_rate"])
        self.assertEqual([0.0, 0.0], report["attack_success_ci95"])

    def test_all_infrastructure_errors_are_not_reported_as_safe(self):
        report = evaluate([record(response="[error: offline]") for _ in range(5)])
        self.assertEqual(0, report["evaluated"])
        self.assertEqual(5, report["excluded_errors"])
        self.assertEqual(0.0, report["attack_success_rate"])

    def test_error_prefix_contract_boundaries(self):
        report = evaluate([
            record(response="[error no closing bracket"),   # prefix match: excluded
            record(response="well [error] mid-string"),     # not a prefix: valid record
            record(response=""),                            # empty response: valid record
            record(success=True),                           # missing response key: valid record
        ])
        self.assertEqual(3, report["evaluated"])
        self.assertEqual(1, report["excluded_errors"])
        self.assertAlmostEqual(1 / 3, report["attack_success_rate"])

    def test_missing_success_flag_counts_as_not_successful(self):
        report = evaluate([record(response="plain answer")])
        self.assertEqual(1, report["evaluated"])
        self.assertEqual(0.0, report["attack_success_rate"])


class WilsonIntervalTests(unittest.TestCase):
    def test_matches_textbook_reference_value(self):
        low, high = wilson_interval(50, 100)
        self.assertAlmostEqual(0.4038, low, places=4)
        self.assertAlmostEqual(0.5962, high, places=4)

    def test_nonpositive_total_returns_degenerate_interval(self):
        self.assertEqual((0.0, 0.0), wilson_interval(0, 0))
        self.assertEqual((0.0, 0.0), wilson_interval(3, -1))

    def test_bounds_are_clamped_to_unit_interval(self):
        low_zero, _ = wilson_interval(0, 10)
        _, high_full = wilson_interval(10, 10)
        self.assertEqual(0.0, low_zero)
        self.assertEqual(1.0, high_full)

    def test_interval_narrows_as_sample_grows(self):
        small = wilson_interval(5, 10)
        large = wilson_interval(500, 1000)
        self.assertLess(large[1] - large[0], small[1] - small[0])

    def test_point_estimate_stays_inside_interval(self):
        for successes, total in [(0, 5), (1, 3), (7, 20), (99, 100)]:
            low, high = wilson_interval(successes, total)
            p = successes / total
            self.assertLessEqual(low, p)
            self.assertLessEqual(p, high)


class CompareSafetyUncertaintyTests(unittest.TestCase):
    def test_safety_score_flips_attack_rate_and_interval(self):
        summary = {"jailbreak": {"success_rate": 0.5}, "toxicity": {"success_rate": 0.0}}
        report = safety_score_with_uncertainty(summary, samples_per_attack=10)
        self.assertEqual(20, report["samples"])
        self.assertAlmostEqual(0.75, report["safety_score"])
        low, high = report["safety_ci95"]
        self.assertLessEqual(low, 0.75)
        self.assertLessEqual(0.75, high)

    def test_empty_summary_reports_zero_samples(self):
        report = safety_score_with_uncertainty({})
        self.assertEqual(0.0, report["safety_score"])
        self.assertEqual(0, report["samples"])


if __name__ == "__main__":
    unittest.main()
