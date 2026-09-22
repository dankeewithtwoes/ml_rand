import importlib
import os
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient


class PortfolioWebTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        os.environ["PORTFOLIO_WORKBENCH_DB"] = str(Path(cls.temp.name) / "runs.sqlite3")
        api = importlib.import_module("portfolio_web.api")
        cls.client = TestClient(api.app)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_catalog_has_exactly_21_unique_projects(self):
        response = self.client.get("/api/catalog")
        self.assertEqual(200, response.status_code)
        items = response.json()["items"]
        self.assertEqual(21, len(items))
        self.assertEqual(list(range(1, 22)), [item["id"] for item in items])

    def test_every_sample_executes_its_real_source_module(self):
        items = self.client.get("/api/catalog").json()["items"]
        for item in items:
            with self.subTest(project=item["id"]):
                response = self.client.post(f"/api/run/{item['id']}", json={"payload": item["sample"]})
                self.assertEqual(200, response.status_code, response.text)
                self.assertTrue(response.json()["result"] is not None)

    def test_history_review_and_delete_roundtrip(self):
        item = self.client.get("/api/catalog").json()["items"][3]
        run = self.client.post(f"/api/run/{item['id']}", json={"payload": item["sample"]}).json()
        reviewed = self.client.post(f"/api/history/{run['id']}/review", json={"status": "approved", "note": "checked"})
        self.assertEqual("approved", reviewed.json()["review_status"])
        self.assertTrue(any(entry["id"] == run["id"] for entry in self.client.get("/api/history").json()["items"]))
        self.assertEqual(204, self.client.delete(f"/api/history/{run['id']}").status_code)

    def test_static_ui_is_served(self):
        page = self.client.get("/")
        self.assertEqual(200, page.status_code)
        self.assertIn("21 инструментарий", page.text)


if __name__ == "__main__":
    unittest.main()
