"""Backups, export/import and feedback.  Run with:  py -m unittest discover tests"""
import datetime
import json
import os
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app as app_module  # noqa: E402
import db  # noqa: E402


def rows_with(letter, count, line=5):
    rows = ["." * 32 for _ in range(32)]
    rows[line] = (letter * count).ljust(32, ".")
    return rows


class TempDatabase(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.folder.name, "t.db")
        db.init_db(self.path)

    def tearDown(self):
        self.folder.cleanup()


class BackupTests(TempDatabase):
    def test_backup_is_made_once_a_day_and_is_a_real_copy(self):
        db.add_connector(self.path, "A", 2, "plug", "other", rows_with("P", 2))
        first = db.auto_backup(self.path)
        self.assertTrue(os.path.exists(first))
        self.assertIn(datetime.date.today().isoformat(), first)
        self.assertIsNone(db.auto_backup(self.path))   # second call the same day does nothing
        copy = sqlite3.connect(first)
        self.assertEqual(copy.execute("select name from connectors").fetchone()[0], "A")
        copy.close()

    def test_only_the_newest_backups_are_kept(self):
        folder = os.path.join(self.folder.name, "backups")
        os.makedirs(folder)
        for day in range(1, 21):
            open(os.path.join(folder, "connectors-2020-01-%02d.db" % day), "w").close()
        db.auto_backup(self.path, keep=5)
        left = sorted(os.listdir(folder))
        self.assertEqual(len(left), 5)
        self.assertIn("connectors-%s.db" % datetime.date.today().isoformat(), left)

    def test_no_database_no_backup(self):
        self.assertIsNone(db.auto_backup(os.path.join(self.folder.name, "missing.db")))


class ExportImportTests(TempDatabase):
    def fill(self):
        self.a = db.add_connector(self.path, "Alpha", 4, "plug", "computing", rows_with("P", 4), size_mm=12)
        db.add_connector(self.path, "Beta", None, "socket", "other", rows_with("O", 3), reviewed=False)
        db.add_feedback(self.path, "right", self.a, 2, 80, rows_with("P", 4), {"pins": 4})
        db.add_feedback(self.path, "not_found", None, None, None, rows_with("S", 6), {})

    def other_db(self):
        path = os.path.join(self.folder.name, "other.db")
        db.init_db(path)
        return path

    def test_round_trip_into_an_empty_database_loses_nothing(self):
        self.fill()
        exported = json.loads(json.dumps(db.export_all(self.path)))   # via real JSON text
        target = self.other_db()
        report = db.import_data(target, exported)
        self.assertEqual((report["added"], report["skipped"], report["feedback_added"]), (2, 0, 2))
        got = {c["name"]: c for c in db.list_connectors(target, include_rows=True)}
        self.assertEqual(got["Alpha"]["size_mm"], 12)
        self.assertEqual(got["Alpha"]["rows"], db.centre_rows(rows_with("P", 4)))
        self.assertFalse(got["Beta"]["reviewed"])
        self.assertIsNone(got["Beta"]["pins"])
        self.assertEqual(db.feedback_summary(target)["judged"], 2)
        self.assertEqual(db.list_feedback(target)[0]["connector_id"], got["Alpha"]["id"])

    def test_importing_twice_does_not_duplicate(self):
        self.fill()
        exported = db.export_all(self.path)
        target = self.other_db()
        db.import_data(target, exported)
        again = db.import_data(target, exported)
        self.assertEqual((again["added"], again["skipped"], again["feedback_added"]), (0, 2, 0))
        self.assertEqual(len(db.list_connectors(target)), 2)

    def test_same_name_is_kept_unless_replace_is_chosen(self):
        self.fill()
        exported = db.export_all(self.path)
        target = self.other_db()
        db.add_connector(target, "Alpha", 99, "plug", "other", rows_with("P", 9))
        db.import_data(target, exported)
        self.assertEqual(next(c for c in db.list_connectors(target) if c["name"] == "Alpha")["pins"], 99)
        report = db.import_data(target, exported, replace_same_name=True)
        self.assertEqual(report["replaced"], 2)   # Alpha and Beta both exist by now
        self.assertEqual(next(c for c in db.list_connectors(target) if c["name"] == "Alpha")["pins"], 4)

    def test_bad_entries_are_rejected_one_by_one(self):
        exported = {"format": db.EXPORT_FORMAT, "version": 1, "connectors": [
            {"name": "Good", "pins": 2, "gender": "plug", "industry": "other", "rows": rows_with("P", 2)},
            {"name": "Bad pins", "pins": -4, "gender": "plug", "industry": "other", "rows": rows_with("P", 2)},
            {"name": "Bad rows", "pins": 2, "gender": "plug", "industry": "other", "rows": ["x"]},
            "not even an object"], "feedback": []}
        report = db.import_data(self.path, exported)
        self.assertEqual(report["added"], 1)
        self.assertEqual(report["rejected_count"], 3)
        self.assertEqual([c["name"] for c in db.list_connectors(self.path)], ["Good"])

    def test_wrong_files_are_refused_with_a_clear_message(self):
        for bad in (None, [], {"format": "something else"}, {"format": db.EXPORT_FORMAT, "version": 7},
                    {"format": db.EXPORT_FORMAT, "version": 1, "connectors": "nope"}):
            with self.assertRaises(db.InvalidConnector):
                db.import_data(self.path, bad)


class FeedbackTests(TempDatabase):
    def test_summary_counts(self):
        a = db.add_connector(self.path, "A", 2, "plug", "other", rows_with("P", 2))
        rows = rows_with("P", 2)
        for rank in (1, 1, 3, 7):
            db.add_feedback(self.path, "right", a, rank, 90, rows, {})
        db.add_feedback(self.path, "not_found", None, None, None, rows, {})
        self.assertEqual(db.feedback_summary(self.path),
                         {"judged": 5, "first": 2, "top3": 3, "later": 1, "not_found": 1})

    def test_bad_feedback_is_rejected(self):
        a = db.add_connector(self.path, "A", 2, "plug", "other", rows_with("P", 2))
        good = rows_with("P", 2)
        for args in (("maybe", a, 1, 50, good, {}), ("right", None, 1, 50, good, {}),
                     ("right", 999, 1, 50, good, {}), ("right", a, 0, 50, good, {}),
                     ("right", a, 1, 150, good, {}), ("right", a, 1, 50, ["x"], {}),
                     ("right", a, 1, 50, [".." * 16] * 32, {}), ("not_found", None, None, None, good, "text")):
            with self.assertRaises(db.InvalidConnector, msg=str(args[:4])):
                db.add_feedback(self.path, *args)


class RouteTests(TempDatabase):
    def setUp(self):
        super().setUp()
        app_module.app.config["DATABASE"] = self.path
        self.client = app_module.app.test_client()
        self.body = {"name": "Alpha", "details": {"pins": 4, "gender": "plug", "industry": "other", "size_mm": 9},
                     "rows": rows_with("P", 4)}
        self.id = self.client.post("/api/connectors", json=self.body).get_json()["id"]

    def test_export_downloads_a_json_file_and_import_reads_it_back(self):
        response = self.client.get("/api/export")
        self.assertIn("attachment; filename=connector-database-", response.headers["Content-Disposition"])
        text = response.get_data(as_text=True)
        self.assertEqual(json.loads(text)["connectors"][0]["name"], "Alpha")
        db.delete_connector(self.path, self.id)
        report = self.client.post("/api/import", json={"data": json.loads(text)}).get_json()
        self.assertEqual(report["added"], 1)

    def test_import_of_rubbish_is_a_400(self):
        self.assertEqual(self.client.post("/api/import", json={"data": {"hello": 1}}).status_code, 400)
        self.assertEqual(self.client.post("/api/import", json={}).status_code, 400)

    def test_feedback_routes(self):
        good = {"outcome": "right", "connector_id": self.id, "rank": 1, "score": 88,
                "rows": rows_with("P", 4), "details": {"pins": 4}}
        self.assertEqual(self.client.post("/api/feedback", json=good).status_code, 201)
        self.assertEqual(self.client.post("/api/feedback", json=dict(good, rank=0)).status_code, 400)
        summary = self.client.get("/api/feedback/summary").get_json()
        self.assertEqual((summary["judged"], summary["first"]), (1, 1))


if __name__ == "__main__":
    unittest.main()
