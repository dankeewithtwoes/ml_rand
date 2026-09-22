"""Tests for the real keyless search boundary (network calls are mocked)."""
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import URLError

sys.path.insert(0, str(Path(__file__).resolve().parent))

from web_search import WebSearchError, search_web


class _Response:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, _limit):
        return self.payload


class WebSearchTests(unittest.TestCase):
    @patch("web_search.urlopen")
    def test_returns_live_payload_values_and_provenance(self, mocked_open):
        mocked_open.return_value = _Response({
            "Heading": "Python",
            "AbstractText": "Python is a programming language.",
            "AbstractURL": "https://example.test/python",
            "Results": [],
            "RelatedTopics": [],
        })
        result = search_web("python language", max_results=2)
        self.assertEqual("Python", result["results"][0]["title"])
        self.assertEqual("https://example.test/python", result["results"][0]["url"])
        self.assertEqual("DuckDuckGo Instant Answer", result["provenance"]["provider"])
        request = mocked_open.call_args.args[0]
        self.assertIn("q=python+language", request.full_url)

    @patch("web_search.urlopen", side_effect=URLError("offline"))
    def test_network_failure_is_explicit(self, _mocked_open):
        with self.assertRaisesRegex(WebSearchError, "request failed"):
            search_web("python")

    @patch("web_search.urlopen")
    def test_empty_provider_result_is_not_fabricated(self, mocked_open):
        mocked_open.return_value = _Response({"Results": [], "RelatedTopics": []})
        with self.assertRaisesRegex(WebSearchError, "no instant-answer results"):
            search_web("unanswerable query")

    def test_invalid_input_is_rejected_before_network(self):
        with self.assertRaisesRegex(WebSearchError, "cannot be empty"):
            search_web("   ")


if __name__ == "__main__":
    unittest.main()
