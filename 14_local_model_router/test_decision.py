#!/usr/bin/env python3
"""Behavioral tests for explainable constrained routing (decision.py).

Covers the happy path (strength match, privacy, budgets) and failure modes:
unsatisfiable constraints, empty registry, policy bypass by spoofed model name,
unknown intent fallback, and missing metadata fields.
"""
import tempfile
import unittest
from pathlib import Path

from decision import choose, contains_sensitive_data

MODELS = [
    {"name": "llama3.1", "type": "local", "cost_per_1k_tokens": 0.0, "avg_latency_ms": 800,
     "strengths": ["private", "general"]},
    {"name": "qwen-fast", "type": "local", "cost_per_1k_tokens": 0.0, "avg_latency_ms": 300,
     "strengths": ["fast", "code"]},
    {"name": "gpt-4o-mini", "type": "cloud", "cost_per_1k_tokens": 0.00015, "avg_latency_ms": 600,
     "strengths": ["reasoning"]},
]


def rejected_names(result):
    return [entry["model"] for entry in result["rejected"]]


class TestChooseHappyPath(unittest.TestCase):
    def test_strength_match_wins(self):
        result = choose(MODELS, "code")
        self.assertEqual("qwen-fast", result["model"]["name"])
        self.assertIn("matched model strength", result["reasons"])
        self.assertEqual([], result["rejected"])

    def test_private_prompt_rejects_cloud_with_reason(self):
        result = choose(MODELS, "reasoning", private=True)
        self.assertEqual("local", result["model"]["type"])
        self.assertIn("gpt-4o-mini", rejected_names(result))
        reasons = result["rejected"][0]["reasons"]
        self.assertIn("privacy requires local execution", reasons)

    def test_cost_budget_rejects_expensive_model(self):
        result = choose(MODELS, "reasoning", max_cost=0.0)
        self.assertEqual("local", result["model"]["type"])
        self.assertIn("gpt-4o-mini", rejected_names(result))
        self.assertIn("over cost budget", result["rejected"][0]["reasons"])

    def test_latency_budget_rejects_slow_models(self):
        result = choose(MODELS, "general", max_latency_ms=400)
        self.assertEqual("qwen-fast", result["model"]["name"])
        self.assertIn("llama3.1", rejected_names(result))
        self.assertIn("over latency budget", result["rejected"][0]["reasons"])

    def test_sensitive_prompt_forces_local_even_without_flag(self):
        # route.py auto-detects sensitive markers and applies the privacy policy.
        from registry import ModelRegistry
        from route import select_model
        with tempfile.TemporaryDirectory() as tmp:
            registry = ModelRegistry(Path(tmp) / "registry.json")  # seeds defaults
            model = select_model(registry, "here is my password for the db", private=False)
        self.assertEqual("local", model["type"])


class TestChooseFailureModes(unittest.TestCase):
    def test_no_model_satisfies_constraints_raises(self):
        cloud_only = [m for m in MODELS if m["type"] == "cloud"]
        with self.assertRaises(ValueError):
            choose(cloud_only, "reasoning", private=True)

    def test_empty_registry_raises(self):
        with self.assertRaises(ValueError):
            choose([], "general")

    def test_privacy_bypass_by_spoofed_name_fails(self):
        # A cloud model named like a local one must still be rejected:
        # the privacy policy is keyed on the declared type, not the name.
        spoofed = [{"name": "local-llama", "type": "cloud", "avg_latency_ms": 100,
                    "strengths": ["code"]}]
        with self.assertRaises(ValueError):
            choose(spoofed, "code", private=True)

    def test_unknown_intent_falls_back_to_tradeoff(self):
        result = choose(MODELS, "totally-unknown-intent")
        self.assertEqual(["best available trade-off"], result["reasons"])

    def test_missing_metadata_fields_do_not_crash(self):
        bare = [{"name": "bare-local", "type": "local"}]
        result = choose(bare, "code", private=True, max_cost=0.0)
        self.assertEqual("bare-local", result["model"]["name"])


class TestSensitiveDataDetection(unittest.TestCase):
    def test_markers_detected_case_insensitively(self):
        self.assertTrue(contains_sensitive_data("my PASSWORD is hidden"))
        self.assertTrue(contains_sensitive_data("the token leaked"))

    def test_clean_and_empty_prompts_pass(self):
        self.assertFalse(contains_sensitive_data("translate this contract"))
        self.assertFalse(contains_sensitive_data(""))


if __name__ == "__main__":
    unittest.main()
