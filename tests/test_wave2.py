import tempfile
import unittest
from pathlib import Path

from _loader import load


class WaveTwoTests(unittest.TestCase):
    def test_08_contract_redacts_and_detects_breaking_change(self):
        module = load("08_dify_workflow_integration/workflow_contract.py")
        self.assertEqual("***REDACTED***", module.redact({"api_key": "secret"})["api_key"])
        diff = module.contract_diff({"inputs": {"query": {}}}, {"inputs": {"topic": {}}})
        self.assertTrue(diff["breaking"]); self.assertEqual(["query"], diff["removed_inputs"])

    def test_09_provenance_hashes_workflow_and_output(self):
        module = load("09_comfyui_image_gen/provenance.py")
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "image.png"; image.write_bytes(b"fake-png")
            record = module.generation_record({"seed": 42}, [image])
            self.assertEqual(64, len(record["workflow_sha256"])); self.assertEqual(8, record["images"][0]["bytes"])

    def test_10_repair_policy_blocks_dynamic_execution(self):
        module = load("10_openhands_code_agent/repair_policy.py")
        self.assertTrue(module.validate_candidate("x=1", "x=2")["valid"])
        self.assertFalse(module.validate_candidate("x=1", "eval('x')")["valid"])
        repair = load("10_openhands_code_agent/repair.py")
        diff = repair.generate_diff(Path("app.py"), "x = 1", "x = 2")
        self.assertIn("-x = 1", diff); self.assertIn("+x = 2", diff)

    def test_11_memory_export_delete_and_top_k(self):
        module = load("11_local_knowledge_os/knowledge_store.py")
        with tempfile.TemporaryDirectory() as tmp:
            store = module.KnowledgeStore(Path(tmp))
            first = store.add("Python project alpha", ["code"]); store.add("Python project beta", ["code"])
            self.assertEqual(1, len(store.query("Python project", top_k=1)))
            self.assertEqual(2, len(store.export()["episodes"]))
            self.assertTrue(store.delete(first)); self.assertFalse(store.delete(first))

    def test_12_wake_word_has_word_boundaries(self):
        module = load("12_local_voice_companion/wake_word.py")
        self.assertEqual("включи свет", module.extract_command("Компьютер, включи свет", "компьютер"))
        self.assertIsNone(module.extract_command("supercomputer", "computer"))

    def test_13_split_is_deterministic_and_leakage_safe(self):
        module = load("13_local_finetuning_lab/data_quality.py")
        items = [{"instruction": str(i), "output": str(i)} for i in range(10)]
        self.assertEqual(module.deterministic_split(items, .2, 7), module.deterministic_split(items, .2, 7))
        self.assertFalse(module.validate([items[0], items[0]])["valid"])

    def test_14_router_explains_privacy_rejections(self):
        module = load("14_local_model_router/decision.py")
        models = [{"name": "local", "type": "local", "avg_latency_ms": 500, "strengths": ["code"]},
                  {"name": "cloud", "type": "cloud", "avg_latency_ms": 100, "strengths": ["code"]}]
        result = module.choose(models, "code", private=True)
        self.assertEqual("local", result["model"]["name"]); self.assertEqual("cloud", result["rejected"][0]["model"])
        self.assertTrue(module.contains_sensitive_data("my password is hidden"))


if __name__ == "__main__":
    unittest.main()
