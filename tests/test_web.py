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


class EditRouteTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        path = os.path.join(self.folder.name, "edit.db")
        app_module.app.config["DATABASE"] = path
        db.init_db(path)
        self.client = app_module.app.test_client()
        self.body = {"name": "Draft", "details": {"pins": 6, "gender": "plug", "industry": "other"},
                     "rows": rows_with("P", 6)}
        self.id = self.client.post("/api/connectors", json=self.body).get_json()["id"]

    def tearDown(self):
        self.folder.cleanup()

    def test_put_updates_and_list_can_include_drawings(self):
        self.body["name"] = "Renamed"
        self.assertEqual(self.client.put("/api/connectors/%d" % self.id, json=self.body).status_code, 200)
        plain = self.client.get("/api/connectors").get_json()
        self.assertEqual(plain[0]["name"], "Renamed")
        self.assertNotIn("rows", plain[0])
        self.assertEqual(len(self.client.get("/api/connectors?rows=1").get_json()[0]["rows"]), 32)

    def test_put_errors(self):
        self.assertEqual(self.client.put("/api/connectors/999", json=self.body).status_code, 404)
        self.client.post("/api/connectors", json=dict(self.body, name="Other"))
        clash = self.client.put("/api/connectors/%d" % self.id, json=dict(self.body, name="other"))
        self.assertEqual(clash.status_code, 400)
        self.assertIn("already exists", clash.get_json()["error"])
        self.assertEqual(self.client.post("/api/connectors", json=self.body).status_code, 400)  # duplicate name

    def test_patch_reviewed(self):
        self.assertEqual(self.client.patch("/api/connectors/%d/reviewed" % self.id,
                                           json={"reviewed": False}).status_code, 200)
        self.assertFalse(self.client.get("/api/connectors").get_json()[0]["reviewed"])
        self.assertEqual(self.client.patch("/api/connectors/999/reviewed", json={}).status_code, 404)


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
