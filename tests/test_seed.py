"""Run with:  py -m unittest discover tests"""
import os
import random
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import db  # noqa: E402
import matching  # noqa: E402
import seed_data  # noqa: E402
import seed_db  # noqa: E402


class SeedDataTests(unittest.TestCase):
    def test_every_starter_connector_is_valid(self):
        for name, pins, gender, industry, rows in seed_data.starter_rows():
            db.validate(name, pins, gender, industry, rows)  # raises if anything is wrong

    def test_every_starter_connector_has_a_size(self):
        names = {name for name, *_ in seed_data.starter_rows()}
        self.assertEqual(names, set(seed_data.STARTER_SIZES))

    def test_audio_plugs_are_now_separated_by_size(self):
        self.assertEqual(seed_data.STARTER_SIZES["3.5 mm TRS audio plug (mini-jack)"], 3.5)
        self.assertEqual(seed_data.STARTER_SIZES["6.35 mm (1/4 inch) TRS audio plug"], 6.35)

    def test_names_are_unique(self):
        names = [name for name, *_ in seed_data.starter_rows()]
        self.assertEqual(len(names), len(set(names)))

    def test_plugs_and_sockets_use_the_matching_contact_letter(self):
        for name, pins, gender, industry, rows in seed_data.starter_rows():
            text = "".join(rows)
            if "centre" in name:
                continue  # barrel connectors: the centre contact is the opposite way round
            if gender == "plug":
                self.assertNotIn("O", text, name)
            if gender == "socket":
                self.assertNotIn("P", text, name)


class LoaderTests(unittest.TestCase):
    def test_older_database_gets_sizes_and_the_trs_rename(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "seed.db")
            db.init_db(path)
            rows = dict((n, r) for n, _p, _g, _i, r in seed_data.starter_rows())
            old = db.add_connector(path, "3.5 mm / 6.35 mm TRS audio plug", 3, "plug", "audio_video",
                                   rows["3.5 mm TRS audio plug (mini-jack)"], reviewed=False)
            seed_db.load_starter_connectors(path)
            found = db.get_connector(path, old)
            self.assertEqual(found["name"], "3.5 mm TRS audio plug (mini-jack)")   # renamed in place
            self.assertEqual(found["size_mm"], 3.5)                                # size filled in
            names = [c["name"] for c in db.list_connectors(path)]
            self.assertEqual(len(names), len(set(names)))
            self.assertIn("6.35 mm (1/4 inch) TRS audio plug", names)

    def test_loader_does_not_overwrite_a_size_you_set(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "seed.db")
            seed_db.load_starter_connectors(path)
            usb = next(c for c in db.list_connectors(path) if c["name"] == "USB-A plug")
            full = db.get_connector(path, usb["id"])
            db.update_connector(path, usb["id"], full["name"], full["pins"], full["gender"],
                                full["industry"], full["rows"], size_mm=99)
            seed_db.load_starter_connectors(path)
            self.assertEqual(db.get_connector(path, usb["id"])["size_mm"], 99)

    def test_starters_are_loaded_as_unchecked_drafts(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "seed.db")
            seed_db.load_starter_connectors(path)
            self.assertFalse(any(c["reviewed"] for c in db.list_connectors(path)))

    def test_loading_twice_does_not_duplicate(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "seed.db")
            first = seed_db.load_starter_connectors(path)
            second = seed_db.load_starter_connectors(path)
            self.assertEqual(first[1], 0)
            self.assertEqual(second[0], 0)
            self.assertEqual(len(db.list_connectors(path)), first[0])


def sloppy(rows, rng):
    """Redraw a connector badly, the way a person might: wobbly, shifted, with a few mistakes."""
    grid = [list(row) for row in rows]
    drawn = [(r, c) for r in range(32) for c in range(32) if grid[r][c] != "."]
    for r, c in drawn:
        roll = rng.random()
        if roll < 0.04:
            grid[r][c] = "."                      # forgot a cell
        elif roll < 0.12:
            letter = grid[r][c]                   # nudged one cell sideways
            grid[r][c] = "."
            rr, cc = r + rng.choice((-1, 0, 1)), c + rng.choice((-1, 0, 1))
            if 0 <= rr < 32 and 0 <= cc < 32:
                grid[rr][cc] = letter
    return ["".join(row) for row in grid]


def outline_only(rows):
    """Redraw the way most people do: housing and shell as outlines, not filled blocks."""
    grid = [list(row) for row in rows]
    out = [list(row) for row in rows]
    for r in range(32):
        for c in range(32):
            if grid[r][c] in "HS":
                neighbours = [grid[rr][cc] if 0 <= rr < 32 and 0 <= cc < 32 else "."
                              for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))]
                if all(n in "HS" for n in neighbours):
                    out[r][c] = "."
    return ["".join(row) for row in out]


class RealisticSearchQualityTests(unittest.TestCase):
    """Does the right connector come back when the drawing is imperfect?

    This is the test that matters most for the whole app. If it starts failing after a change
    to matching.py, the change made searching worse."""

    @classmethod
    def setUpClass(cls):
        cls.folder = tempfile.TemporaryDirectory()
        cls.path = os.path.join(cls.folder.name, "quality.db")
        seed_db.load_starter_connectors(cls.path)
        cls.connectors = db.list_connectors(cls.path)

    @classmethod
    def tearDownClass(cls):
        cls.folder.cleanup()

    def rank_of(self, name, rows):
        results = matching.search(self.path, rows, limit=len(self.connectors))
        return [r["name"] for r in results].index(name) + 1

    def accuracy(self, redraw, label):
        rng = random.Random(1234)
        ranks = []
        for name, _pins, _gender, _industry, rows in seed_data.starter_rows():
            ranks.append(self.rank_of(name, redraw(rows, rng)))
        top1 = sum(r == 1 for r in ranks) / len(ranks)
        top3 = sum(r <= 3 for r in ranks) / len(ranks)
        print("\n%-28s right answer first: %3d%%   in top 3: %3d%%" % (label, top1 * 100, top3 * 100))
        return top1, top3

    def test_exact_copies_come_back_first(self):
        top1, _ = self.accuracy(lambda rows, rng: rows, "exact copy")
        self.assertGreaterEqual(top1, 0.9)  # a few near-twins (plug/socket) can tie

    def test_sloppy_redraws_are_found(self):
        top1, top3 = self.accuracy(sloppy, "sloppy redraw")
        self.assertGreaterEqual(top3, 0.9)

    def test_size_separates_look_alike_connectors(self):
        rows = {name: r for name, _p, _g, _i, r in seed_data.starter_rows()}
        for name, look_alike in (("3.5 mm TRS audio plug (mini-jack)", "6.35 mm (1/4 inch) TRS audio plug"),
                                 ("6.35 mm (1/4 inch) TRS audio plug", "3.5 mm TRS audio plug (mini-jack)"),
                                 ("RCA (phono) plug", "DC barrel jack (centre-pin type)"),
                                 ("DC barrel jack (centre-pin type)", "RCA (phono) plug")):
            results = matching.search(self.path, rows[name], {"size_mm": seed_data.STARTER_SIZES[name]}, limit=34)
            by_name = {r["name"]: r["score"] for r in results}
            self.assertEqual(results[0]["name"], name)
            self.assertGreater(by_name[name] - by_name[look_alike], 0.25, name)

    def test_with_the_size_known_exact_copies_are_always_first(self):
        misses = []
        for name, _p, _g, _i, rows in seed_data.starter_rows():
            best = matching.search(self.path, rows, {"size_mm": seed_data.STARTER_SIZES[name]}, limit=1)[0]
            if best["name"] != name:
                misses.append((name, best["name"]))
        print("\nexact copy + size known:     right answer first: %3d%%" % (100 - 100 * len(misses) // 35))
        self.assertEqual(misses, [])

    def test_meaningless_drawings_get_low_scores(self):
        rng = random.Random(7)
        noise = [["."] * 32 for _ in range(32)]
        for _ in range(120):
            noise[rng.randrange(32)][rng.randrange(32)] = rng.choice("HSPOK")
        best = matching.search(self.path, ["".join(row) for row in noise], limit=1)[0]
        self.assertLess(best["score"], 0.2)

    def test_a_42_pin_drawing_is_not_a_confident_match_for_anything(self):
        rows = [["."] * 32 for _ in range(32)]
        for col in range(3, 24):
            rows[6][col] = rows[12][col] = "P"
        for col in range(2, 26):
            rows[3][col] = rows[15][col] = "S"
        for r in range(3, 16):
            rows[r][2] = rows[r][25] = "S"
        best = matching.search(self.path, ["".join(r) for r in rows], {"pins": 42, "gender": "plug"}, limit=1)[0]
        self.assertLess(best["score"], 0.35)

    def test_outline_only_redraws_are_found(self):
        top1, top3 = self.accuracy(lambda rows, rng: outline_only(rows), "outline-only style")
        self.assertGreaterEqual(top3, 0.9)


if __name__ == "__main__":
    unittest.main()
