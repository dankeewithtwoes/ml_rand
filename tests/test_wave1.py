import tempfile
import unittest
from pathlib import Path

from _loader import load


class WaveOneTests(unittest.TestCase):
    def test_01_calibration_perfect_predictions(self):
        module = load("01_pytorch_classifier_demo/src/reliability.py")
        report = module.calibration_report([0.0, 1.0], [0, 1], bins=2)
        self.assertEqual(0.0, report["brier_score"])
        self.assertEqual(0.0, report["expected_calibration_error"])

    def test_02_dataset_duplicates_and_leakage(self):
        module = load("02_huggingface_finetune_demo/data_audit.py")
        row = {"instruction": "hello", "output": "world"}
        self.assertEqual(1, module.audit_records([row, row])["duplicates"])
        self.assertEqual([0], module.leakage_between([row], [row])["validation_rows"])

    def test_03_grounding_flags_unsupported_claim(self):
        module = load("03_langchain_rag_chat/grounding.py")
        report = module.sentence_grounding("Paris is in France. Penguins fly to Mars.", ["Paris is the capital of France."])
        self.assertTrue(report["sentences"][0]["grounded"])
        self.assertFalse(report["sentences"][1]["grounded"])

    def test_04_agent_math_rejects_python(self):
        module = load("04_llamaindex_agent/safe_math.py")
        self.assertEqual(14, module.evaluate("2 + 3 * 4"))
        with self.assertRaises(ValueError): module.evaluate("__import__('os').getcwd()")

    def test_05_arena_ranking_explains_tradeoff(self):
        module = load("05_ollama_local_llm/arena_scoring.py")
        ranked = module.rank_results([
            {"model": "fast", "tokens_per_sec": 100, "judge_score": 3},
            {"model": "smart", "tokens_per_sec": 50, "judge_score": 5},
        ])
        self.assertEqual("smart", ranked[0]["model"])
        self.assertIn("quality", ranked[0]["score_components"])

    def test_06_model_checksum(self):
        module = load("06_llamacpp_gguf_inference/model_integrity.py")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "model.gguf"; path.write_bytes(b"gguf-test")
            digest = module.sha256_file(path)
            self.assertTrue(module.verify_file(path, digest, minimum_bytes=4)["valid"])
            self.assertFalse(module.verify_file(path, "0" * 64)["valid"])

    def test_07_percentile_uses_nearest_rank(self):
        module = load("07_vllm_serving/latency_stats.py")
        self.assertEqual(5, module.percentile([1, 2, 3, 4, 5], 0.99))
        self.assertEqual(4, module.summarize([1, 2, 3, 4])["p95"])


if __name__ == "__main__":
    unittest.main()
