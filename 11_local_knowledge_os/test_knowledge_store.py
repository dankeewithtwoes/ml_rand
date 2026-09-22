#!/usr/bin/env python3
"""Behavioral tests for the distinctive capability: search, export, permanent delete.

Runs fully offline against the SQLite keyword-search fallback (no chromadb,
no embeddings, no network). Style matches the portfolio root tests (unittest).
"""
import shutil
import tempfile
import unittest
from pathlib import Path

from knowledge_store import KnowledgeStore


class KnowledgeStoreLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="knowledge_os_test_")
        self.store = KnowledgeStore(Path(self.tmp))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    # --- happy path -------------------------------------------------------

    def test_add_query_export_delete_lifecycle(self):
        first = self.store.add("Meeting with Artem: AI router deadline Friday", ["work"])
        self.store.add("Pasta recipe: 200g pasta, 100g cheese, one egg", ["cooking"])
        self.store.add("Office address: Moscow, Lenina street 10", ["work"])

        self.store.add("Second meeting note: budget review moved to Monday", ["work"])

        hits = self.store.query("deadline meeting", top_k=2)
        self.assertEqual(2, len(hits))
        self.assertIn("deadline", hits[0]["content"])  # best match first

        exported = self.store.export()
        self.assertEqual("knowledge-os-export", exported["format"])
        self.assertEqual(4, len(exported["episodes"]))

        self.assertTrue(self.store.delete(first))
        remaining = self.store.export()["episodes"]
        self.assertEqual(3, len(remaining))
        self.assertNotIn(first, [episode["id"] for episode in remaining])

    def test_top_k_limits_results(self):
        for index in range(5):
            self.store.add(f"Python project note number {index}", ["code"])
        self.assertEqual(3, len(self.store.query("Python project", top_k=3)))
        self.assertEqual(1, len(self.store.query("Python project", top_k=1)))

    def test_deleted_episode_disappears_from_search(self):
        episode_id = self.store.add("Secret draft about vector databases", ["draft"])
        self.assertTrue(self.store.query("vector databases", top_k=5))
        self.store.delete(episode_id)
        hits = self.store.query("vector databases", top_k=5)
        self.assertEqual([], [h for h in hits if h["id"] == str(episode_id)])

    # --- failure modes ----------------------------------------------------

    def test_empty_or_blank_content_rejected(self):
        for bad in ("", "   ", "\n\t "):
            with self.assertRaises(ValueError):
                self.store.add(bad)
        self.assertEqual([], self.store.all_episodes())

    def test_top_k_must_be_positive(self):
        self.store.add("Some memory worth keeping", ["misc"])
        for bad_k in (0, -1, -100):
            with self.assertRaises(ValueError):
                self.store.query("memory", top_k=bad_k)

    def test_delete_is_idempotent_and_unknown_id_returns_false(self):
        episode_id = self.store.add("Temporary note", [])
        self.assertTrue(self.store.delete(episode_id))
        self.assertFalse(self.store.delete(episode_id))  # already gone
        self.assertFalse(self.store.delete(999999))      # never existed

    def test_empty_store_queries_and_exports_safely(self):
        self.assertEqual([], self.store.query("anything at all", top_k=5))
        exported = self.store.export()
        self.assertEqual([], exported["episodes"])
        self.assertEqual([], self.store.all_episodes())

    def test_query_without_matching_words_returns_empty(self):
        self.store.add("Grocery list: milk, bread, coffee", ["home"])
        self.assertEqual([], self.store.query("quantum entanglement", top_k=5))

    def test_top_k_larger_than_corpus_returns_only_what_matches(self):
        self.store.add("Single note about telescope setup", ["hobby"])
        hits = self.store.query("telescope", top_k=50)
        self.assertEqual(1, len(hits))


if __name__ == "__main__":
    unittest.main()
