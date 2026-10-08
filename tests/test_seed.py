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
        best = matching.search(self.path, ["".join(r) for r in rows], pins=42, gender="plug", limit=1)[0]
        self.assertLess(best["score"], 0.35)

    def test_outline_only_redraws_are_found(self):
        top1, top3 = self.accuracy(lambda rows, rng: outline_only(rows), "outline-only style")
        self.assertGreaterEqual(top3, 0.9)


if __name__ == "__main__":
    unittest.main()
