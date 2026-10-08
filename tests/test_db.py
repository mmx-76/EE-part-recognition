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
        self.assertEqual(found["rows"], db.centre_rows(sample_rows()))

    def test_saved_drawings_are_centred(self):
        new_id = db.add_connector(self.path, "Corner", 4, "plug", "other", sample_rows())
        rows = db.get_connector(self.path, new_id)["rows"]
        drawn_rows = [r for r, row in enumerate(rows) if set(row) != {"."}]
        drawn_cols = [c for row in rows for c, ch in enumerate(row) if ch != "."]
        self.assertAlmostEqual(min(drawn_rows), 31 - max(drawn_rows), delta=1)   # equal space above/below
        self.assertAlmostEqual(min(drawn_cols), 31 - max(drawn_cols), delta=1)   # equal space left/right
        self.assertEqual("".join(rows).count("P"), 4)                             # nothing lost or resized

    def test_centring_twice_changes_nothing(self):
        once = db.centre_rows(sample_rows())
        self.assertEqual(db.centre_rows(once), once)

    def test_old_uncentred_entries_are_centred_when_the_app_starts(self):
        with db.connect(self.path) as connection:   # simulate a row saved before centring existed
            connection.execute(
                "INSERT INTO connectors (name, pins, gender, industry, grid) VALUES (?,?,?,?,?)",
                ("Old", 4, "plug", "other", "\n".join(sample_rows())))
        db.init_db(self.path)
        old = db.list_connectors(self.path, include_rows=True)[0]
        self.assertEqual(old["rows"], db.centre_rows(sample_rows()))

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


class EditingTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.folder.name, "edit.db")
        db.init_db(self.path)

    def tearDown(self):
        self.folder.cleanup()

    def test_update_changes_everything_and_marks_checked(self):
        new_id = db.add_connector(self.path, "Draft", 4, "plug", "other", sample_rows("P"), reviewed=False)
        self.assertFalse(db.get_connector(self.path, new_id)["reviewed"])
        self.assertTrue(db.update_connector(self.path, new_id, "Fixed", 9, "socket", "computing", sample_rows("O")))
        found = db.get_connector(self.path, new_id)
        self.assertEqual((found["name"], found["pins"], found["gender"], found["industry"]),
                         ("Fixed", 9, "socket", "computing"))
        self.assertIn("OOOO", found["rows"][found["rows"].index(next(r for r in found["rows"] if "O" in r))])
        self.assertTrue(found["reviewed"])

    def test_update_of_missing_connector_returns_false(self):
        self.assertFalse(db.update_connector(self.path, 999, "X", 1, "plug", "other", sample_rows()))

    def test_names_must_be_unique_ignoring_case(self):
        first = db.add_connector(self.path, "USB-A", 4, "plug", "computing", sample_rows())
        with self.assertRaises(db.InvalidConnector):
            db.add_connector(self.path, "  usb-a ", 4, "plug", "computing", sample_rows())
        second = db.add_connector(self.path, "USB-B", 4, "plug", "computing", sample_rows())
        with self.assertRaises(db.InvalidConnector):
            db.update_connector(self.path, second, "usb-a", 4, "plug", "computing", sample_rows())
        # keeping your own name when editing is fine
        self.assertTrue(db.update_connector(self.path, first, "USB-A", 5, "plug", "computing", sample_rows()))

    def test_set_reviewed_toggles_the_flag(self):
        new_id = db.add_connector(self.path, "Draft", 4, "plug", "other", sample_rows(), reviewed=False)
        self.assertTrue(db.set_reviewed(self.path, new_id, True))
        self.assertTrue(db.get_connector(self.path, new_id)["reviewed"])
        self.assertTrue(db.set_reviewed(self.path, new_id, False))
        self.assertFalse(db.get_connector(self.path, new_id)["reviewed"])
        self.assertFalse(db.set_reviewed(self.path, 999, True))

    def test_old_database_without_the_flag_is_upgraded(self):
        import sqlite3
        import seed_data
        old_path = os.path.join(self.folder.name, "old.db")
        connection = sqlite3.connect(old_path)   # build a database exactly as it was before the flag
        connection.executescript("""CREATE TABLE connectors (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, pins INTEGER,
            gender TEXT NOT NULL, industry TEXT NOT NULL, grid TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);""")
        name, pins, gender, industry, rows = next(seed_data.starter_rows())
        edited = [row for row in rows]
        edited[0] = "P" + edited[0][1:]
        for n, r in ((name, rows), ("My own", sample_rows()), ("Edited starter", edited)):
            connection.execute("INSERT INTO connectors (name,pins,gender,industry,grid) VALUES (?,?,?,?,?)",
                               (n, 9, "plug", "other", "\n".join(r)))
        connection.commit(); connection.close()
        db.init_db(old_path)
        by_name = {c["name"]: c["reviewed"] for c in db.list_connectors(old_path)}
        self.assertFalse(by_name[name])          # untouched starter -> unchecked draft
        self.assertTrue(by_name["My own"])       # Max's own drawing -> counts as checked
        self.assertTrue(by_name["Edited starter"])  # not an exact starter any more -> left alone
        db.set_reviewed(old_path, next(c["id"] for c in db.list_connectors(old_path) if c["name"] == name), True)
        db.init_db(old_path)                     # restarting the app must not undo a tick
        self.assertTrue({c["name"]: c["reviewed"] for c in db.list_connectors(old_path)}[name])


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
