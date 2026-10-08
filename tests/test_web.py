"""Run with:  py -m unittest discover tests"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app as app_module  # noqa: E402
import db  # noqa: E402


def rows_with(letter, count):
    rows = ["." * 32 for _ in range(32)]
    rows[5] = (letter * count).ljust(32, ".")
    return rows


class SearchRouteTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        path = os.path.join(self.folder.name, "web.db")
        app_module.app.config["DATABASE"] = path
        db.init_db(path)
        db.add_connector(path, "Pin row", 6, "plug", "other", rows_with("P", 6))
        db.add_connector(path, "Shell row", 6, "plug", "other", rows_with("S", 12))
        self.client = app_module.app.test_client()

    def tearDown(self):
        self.folder.cleanup()

    def search(self, rows, **details):
        return self.client.post("/api/search", json={"rows": rows, "details": details})

    def test_returns_ranked_matches_as_percentages(self):
        response = self.search(rows_with("P", 6), pins=6, gender="plug")
        self.assertEqual(response.status_code, 200)
        matches = response.get_json()
        self.assertEqual(matches[0]["name"], "Pin row")
        self.assertEqual(matches[0]["score"], 100)
        self.assertGreater(matches[0]["score"], matches[1]["score"])
        self.assertEqual(matches[0]["pins"], 6)       # the connector's own details
        self.assertEqual(len(matches[0]["rows"]), 32)  # so the page can draw a thumbnail

    def test_empty_drawing_is_a_400(self):
        response = self.search(["." * 32] * 32)
        self.assertEqual(response.status_code, 400)
        self.assertIn("empty", response.get_json()["error"])

    def test_malformed_input_is_a_400_not_a_crash(self):
        self.assertEqual(self.search(None).status_code, 400)
        self.assertEqual(self.search(rows_with("P", 3), pins="nine").status_code, 400)
        self.assertEqual(self.search(rows_with("P", 3), gender="banana").status_code, 400)

    def test_empty_database_gives_empty_list(self):
        for connector in db.list_connectors(app_module.app.config["DATABASE"]):
            db.delete_connector(app_module.app.config["DATABASE"], connector["id"])
        self.assertEqual(self.search(rows_with("P", 3)).get_json(), [])


if __name__ == "__main__":
    unittest.main()
