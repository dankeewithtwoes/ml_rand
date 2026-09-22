import unittest
from types import SimpleNamespace

from _loader import load


class WaveThreeTests(unittest.TestCase):
    def test_15_sarif_is_ci_compatible_and_stable(self):
        module = load("15_local_code_reviewer/reporting.py")
        issue = {"file": "app.py", "line": 3, "severity": "HIGH", "message": "danger"}
        report = module.to_sarif([issue])
        self.assertEqual("2.1.0", report["version"])
        self.assertEqual(module.fingerprint(issue), report["runs"][0]["results"][0]["ruleId"])

    def test_16_synthetic_quality_blocks_pii_and_duplicates(self):
        module = load("16_local_synthetic_data_factory/quality.py")
        row = {"instruction": "Email me", "output": "person@example.com"}
        report = module.audit([row, row])
        self.assertFalse(report["valid"]); self.assertEqual([1], report["duplicates"])
        self.assertEqual("email", report["pii"][0]["types"][0])

    def test_17_extracted_fields_include_source_evidence(self):
        module = load("17_local_document_parser/evidence.py")
        result = module.attach_evidence({"total": "$42", "owner": "Alice"}, "Owner: Alice. Total: $42.")
        self.assertEqual(1.0, module.evidence_coverage(result)); self.assertEqual("$42", result["total"]["evidence"]["quote"])

    def test_18_observability_redacts_instead_of_logging_content(self):
        module = load("18_local_ai_observability/policies.py")
        redacted, findings = module.redact("mail me at person@example.com")
        self.assertNotIn("person@example.com", redacted); self.assertEqual("EMAIL", findings[0]["type"])
        self.assertNotIn("mail me", module.trace_summary("mail me"))

    def test_19_circuit_breaker_and_weighted_load(self):
        module = load("19_local_edge_fleet/scheduler.py")
        state = module.FleetState(failure_threshold=2, cooldown_s=10)
        state.record("bad", False, now=0); state.record("bad", False, now=1)
        self.assertFalse(state.available("bad", now=2)); self.assertTrue(state.available("bad", now=12))
        node = module.choose_node([{"name": "a", "load": 0.8, "weight": 2}, {"name": "b", "load": 0.5, "weight": 1}], state, now=2)
        self.assertEqual("a", node["name"])

    def test_20_safety_metrics_report_uncertainty_and_errors(self):
        module = load("20_local_redteam_arena/safety_metrics.py")
        report = module.evaluate([{"success": True, "response": "bad"}, {"success": False, "response": "safe"}, {"response": "[error: offline]"}])
        self.assertEqual(2, report["evaluated"]); self.assertEqual(1, report["excluded_errors"])
        self.assertLess(report["attack_success_ci95"][0], report["attack_success_ci95"][1])

    def test_21_portability_contract_is_offline(self):
        module = load("21_universal_skill_forge/portability.py")
        skill = SimpleNamespace(name="calculator", schema={"type": "object", "properties": {}, "additionalProperties": False})
        report = module.contract_report(skill, ["ollama", "openai"])
        self.assertTrue(report["portable"]); self.assertTrue(all(report["providers"].values()))


if __name__ == "__main__":
    unittest.main()
