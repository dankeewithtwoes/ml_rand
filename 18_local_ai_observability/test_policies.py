"""Behavioral tests for the distinctive feature: privacy-preserving traces.

The guardrail pipeline must redact PII and record only content-free trace
summaries (length + SHA-256), so raw private prompts never reach the log.
"""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from policies import redact, trace_summary


class TestRedactHappyPath(unittest.TestCase):
    def test_email_phone_and_api_key_are_redacted(self):
        text = "mail person@example.com or call +1 (555) 123-4567, key sk-abcdefghijklmnop"
        redacted, findings = redact(text)
        self.assertNotIn("person@example.com", redacted)
        self.assertNotIn("123-4567", redacted)
        self.assertNotIn("sk-abcdefghijklmnop", redacted)
        self.assertEqual({"EMAIL", "PHONE", "API_KEY"}, {f["type"] for f in findings})

    def test_finding_offsets_match_original_text(self):
        text = "contact bob@example.org please"
        _, findings = redact(text)
        self.assertEqual(1, len(findings))
        start, end = findings[0]["start"], findings[0]["end"]
        self.assertEqual("bob@example.org", text[start:end])

    def test_trace_summary_is_content_free(self):
        prompt = "my email is person@example.com"
        trace = trace_summary(prompt)
        self.assertEqual({"characters", "sha256"}, set(trace))
        self.assertEqual(len(prompt), trace["characters"])
        self.assertEqual(hashlib.sha256(prompt.encode()).hexdigest(), trace["sha256"])
        self.assertNotIn("person@example.com", json.dumps(trace))


class TestRedactFailureModes(unittest.TestCase):
    def test_empty_input_produces_no_findings(self):
        redacted, findings = redact("")
        self.assertEqual("", redacted)
        self.assertEqual([], findings)
        self.assertEqual(0, trace_summary("")["characters"])

    def test_non_string_input_fails_loudly(self):
        with self.assertRaises(TypeError):
            redact(None)
        with self.assertRaises(TypeError):
            trace_summary(None)

    def test_api_key_boundary_length(self):
        long_enough, findings = redact("token sk-" + "a" * 12)
        self.assertEqual(1, len(findings))
        self.assertNotIn("sk-" + "a" * 12, long_enough)
        too_short, findings = redact("token sk-" + "a" * 11)
        self.assertEqual([], findings)
        self.assertIn("sk-" + "a" * 11, too_short)

    def test_safe_text_passes_unchanged(self):
        text = "What is the capital of France?"
        redacted, findings = redact(text)
        self.assertEqual(text, redacted)
        self.assertEqual([], findings)


class TestProxyLogNeverStoresRawPrompt(unittest.TestCase):
    """Policy-bypass resistance: whatever the prompt contains, the JSONL log
    entry must carry only the content-free trace summary."""

    def test_log_call_stores_no_prompt_content(self):
        import guard_proxy

        secret = "person@example.com"
        req_body = {"model": "mock", "messages": [{"role": "user", "content": f"mail {secret}"}]}
        checks = {"pii": [{"type": "EMAIL", "start": 5, "end": 24}], "toxicity": False, "injection": False}
        with tempfile.TemporaryDirectory() as tmp:
            guard_proxy.LOG_FILE = Path(tmp) / "guard_logs.jsonl"
            guard_proxy.log_call(req_body, {}, checks, 0.123)
            raw_line = guard_proxy.LOG_FILE.read_text(encoding="utf-8").strip()

        self.assertNotIn(secret, raw_line)
        self.assertNotIn("mail ", raw_line)
        entry = json.loads(raw_line)
        self.assertEqual({"characters", "sha256"}, set(entry["prompt"]))
        self.assertEqual("mock", entry["model"])
        self.assertEqual(0.123, entry["latency_s"])


if __name__ == "__main__":
    unittest.main()
