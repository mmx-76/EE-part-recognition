"""Run with:  py -m unittest discover tests"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app as app_module  # noqa: E402
import db  # noqa: E402


def sample_rows(letter="P"):
    rows = ["." * 32 for _ in range(32)]
    rows[0] = letter * 4 + "." * 28
    return rows


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.folder.name, "test.db")
        db.init_db(self.path)

    def tearDown(self):
        self.folder.cleanup()

    def test_add_then_get_round_trip(self):
        new_id = db.add_connector(self.path, "DE-9", 9, "plug", "computing", sample_rows())
        found = db.get_connector(self.path, new_id)
        self.assertEqual(found["name"], "DE-9")
        self.assertEqual(found["pins"], 9)
        self.assertEqual(found["rows"], sample_rows())

    def test_unknown_pin_count_is_stored_as_none(self):
        new_id = db.add_connector(self.path, "Mystery", None, "unknown", "unknown", sample_rows())
        self.assertIsNone(db.get_connector(self.path, new_id)["pins"])

    def test_list_is_sorted_and_has_no_drawing(self):
        db.add_connector(self.path, "b-conn", 2, "plug", "other", sample_rows())
        db.add_connector(self.path, "A-conn", 2, "plug", "other", sample_rows())
        names = [c["name"] for c in db.list_connectors(self.path)]
        self.assertEqual(names, ["A-conn", "b-conn"])
        self.assertNotIn("rows", db.list_connectors(self.path)[0])

    def test_delete(self):
        new_id = db.add_connector(self.path, "Temp", 2, "plug", "other", sample_rows())
        self.assertTrue(db.delete_connector(self.path, new_id))
        self.assertIsNone(db.get_connector(self.path, new_id))
        self.assertFalse(db.delete_connector(self.path, new_id))

    def test_bad_data_is_rejected(self):
        good = sample_rows()
        cases = [
            ("", 9, "plug", "other", good),                          # no name
            ("x", 0, "plug", "other", good),                         # pins out of range
            ("x", 9, "banana", "other", good),                       # bad gender
            ("x", 9, "plug", "space", good),                         # bad industry
            ("x", 9, "plug", "other", good[:-1]),                    # wrong row count
            ("x", 9, "plug", "other", ["Z" * 32] * 32),              # bad letters
            ("x", 9, "plug", "other", ["." * 32] * 32),              # empty drawing
        ]
        for case in cases:
            with self.assertRaises(db.InvalidConnector, msg=str(case[:4])):
                db.add_connector(self.path, *case)


class WebTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        app_module.app.config["DATABASE"] = os.path.join(self.folder.name, "web.db")
        db.init_db(app_module.app.config["DATABASE"])
        self.client = app_module.app.test_client()

    def tearDown(self):
        self.folder.cleanup()

    def test_save_list_load_delete(self):
        body = {"name": "XLR3", "details": {"pins": 3, "gender": "plug", "industry": "audio_video"},
                "rows": sample_rows()}
        response = self.client.post("/api/connectors", json=body)
        self.assertEqual(response.status_code, 201)
        new_id = response.get_json()["id"]
        self.assertEqual(len(self.client.get("/api/connectors").get_json()), 1)
        self.assertEqual(self.client.get("/api/connectors/%d" % new_id).get_json()["name"], "XLR3")
        self.assertEqual(self.client.delete("/api/connectors/%d" % new_id).status_code, 200)
        self.assertEqual(self.client.get("/api/connectors/%d" % new_id).status_code, 404)

    def test_bad_save_gives_400_with_message(self):
        response = self.client.post("/api/connectors", json={"name": "", "rows": sample_rows()})
        self.assertEqual(response.status_code, 400)
        self.assertIn("name", response.get_json()["error"].lower())


if __name__ == "__main__":
    unittest.main()
