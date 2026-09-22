import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from portability import contract_report
from skill import Skill

PROVIDERS = ["ollama", "openai"]


def fake_skill(name="calculator", schema=None):
    if schema is None:
        schema = {"type": "object", "properties": {}, "additionalProperties": False}
    return SimpleNamespace(name=name, schema=schema)


class PortabilityContractTests(unittest.TestCase):
    def test_happy_path_valid_skill_is_portable_for_both_providers(self):
        report = contract_report(fake_skill(), PROVIDERS)
        self.assertTrue(report["portable"])
        self.assertEqual({"ollama": True, "openai": True}, report["providers"])
        self.assertEqual([], report["errors"])

    def test_real_calculator_skill_passes_contract(self):
        report = contract_report(Skill(ROOT / "skills" / "calculator"), PROVIDERS)
        self.assertTrue(report["portable"])
        self.assertTrue(all(report["providers"].values()))

    def test_non_portable_tool_name_is_rejected(self):
        # The contract mirrors OpenAI's published function-name pattern ^[a-zA-Z0-9_-]{1,64}$.
        for bad_name in ("my tool", "bad!name", "x" * 65, "", "café"):
            with self.subTest(name=bad_name):
                report = contract_report(fake_skill(name=bad_name), PROVIDERS)
                self.assertFalse(report["portable"])
                self.assertIn("tool name is not provider portable", report["errors"])
                self.assertEqual({"ollama": False, "openai": False}, report["providers"])

    def test_mixed_case_name_matches_published_provider_pattern(self):
        report = contract_report(fake_skill(name="Calculator_2"), PROVIDERS)
        self.assertTrue(report["portable"])

    def test_non_object_schema_is_rejected(self):
        report = contract_report(fake_skill(schema={"type": "array", "items": {"type": "string"}}), PROVIDERS)
        self.assertFalse(report["portable"])
        self.assertIn("tool input schema must be an object", report["errors"])

    def test_unsupported_schema_keywords_are_listed(self):
        schema = {"type": "object", "properties": {}, "$defs": {}, "patternProperties": {"^x": {}}}
        report = contract_report(fake_skill(schema=schema), PROVIDERS)
        self.assertFalse(report["portable"])
        self.assertTrue(any("$defs" in error and "patternProperties" in error for error in report["errors"]))

    def test_empty_provider_list_is_a_valid_boundary(self):
        report = contract_report(fake_skill(), [])
        self.assertTrue(report["portable"])
        self.assertEqual({}, report["providers"])

    def test_multiple_violations_accumulate_in_one_report(self):
        report = contract_report(fake_skill(name="Bad Name", schema={"type": "string"}), PROVIDERS)
        self.assertFalse(report["portable"])
        self.assertGreaterEqual(len(report["errors"]), 2)


if __name__ == "__main__":
    unittest.main()
