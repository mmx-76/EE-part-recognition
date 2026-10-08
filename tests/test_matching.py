"""Run with:  py -m unittest discover tests"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import db  # noqa: E402
import matching  # noqa: E402


def blank():
    return [["."] * 32 for _ in range(32)]


def to_rows(grid):
    return ["".join(row) for row in grid]


def rectangle(grid, top, left, height, width, letter, filled=False):
    for r in range(top, top + height):
        for c in range(left, left + width):
            edge = r in (top, top + height - 1) or c in (left, left + width - 1)
            if filled or edge:
                grid[r][c] = letter


def d_sub_like(top=4, left=4, scale=1):
    """A shell with a row of pins: a stand-in for a D-sub."""
    grid = blank()
    rectangle(grid, top, left, 6 * scale, 14 * scale, "S")
    for i in range(5):
        grid[top + 2 * scale][left + (2 + 2 * i) * scale] = "P"
    return to_rows(grid)


def round_like():
    grid = blank()
    for r in range(32):
        for c in range(32):
            if 100 <= (r - 15.5) ** 2 + (c - 15.5) ** 2 <= 130:
                grid[r][c] = "S"
    grid[15][15] = grid[15][17] = grid[17][16] = "P"
    return to_rows(grid)


def prepared_score(a, b):
    return matching.drawing_score(matching.prepare(a), matching.prepare(b))


class NormaliseTests(unittest.TestCase):
    def test_empty_drawing_is_none(self):
        self.assertIsNone(matching.normalise(to_rows(blank())))

    def test_moving_a_drawing_changes_nothing(self):
        self.assertEqual(matching.normalise(d_sub_like(4, 4)), matching.normalise(d_sub_like(12, 9)))


class DrawingScoreTests(unittest.TestCase):
    def test_identical_is_perfect(self):
        self.assertAlmostEqual(prepared_score(d_sub_like(), d_sub_like()), 1.0)

    def test_moved_is_still_perfect(self):
        self.assertAlmostEqual(prepared_score(d_sub_like(2, 2), d_sub_like(15, 10)), 1.0)

    def test_scaled_up_is_very_similar(self):
        self.assertGreater(prepared_score(d_sub_like(), d_sub_like(2, 2, scale=2)), 0.7)

    def test_different_shape_scores_much_lower(self):
        self.assertLess(prepared_score(d_sub_like(), round_like()), 0.4)

    def test_one_cell_wobble_stays_high(self):
        wobbled = [list(row) for row in d_sub_like()]
        wobbled[6][7] = "."
        wobbled[6][8] = "P"
        self.assertGreater(prepared_score(d_sub_like(), to_rows(wobbled)), 0.85)


class CombineTests(unittest.TestCase):
    def test_unknown_details_are_ignored(self):
        result = matching.combine(0.8, None, "unknown", 9, "plug")
        self.assertAlmostEqual(result["score"], 0.8)
        self.assertIsNone(result["pins"])

    def test_matching_details_lift_the_score(self):
        with_details = matching.combine(0.8, 9, "plug", 9, "plug")["score"]
        self.assertGreater(with_details, 0.8)

    def test_wrong_details_lower_the_score(self):
        self.assertLess(matching.combine(0.8, 9, "plug", 25, "socket")["score"], 0.8)

    def test_close_pin_counts_beat_far_ones(self):
        close = matching.combine(0.8, 9, "unknown", 10, "unknown")["score"]
        far = matching.combine(0.8, 9, "unknown", 25, "unknown")["score"]
        self.assertGreater(close, far)


class SearchTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.folder.name, "t.db")
        db.init_db(self.path)
        db.add_connector(self.path, "D-like", 5, "plug", "computing", d_sub_like())
        db.add_connector(self.path, "Round-like", 3, "plug", "audio_video", round_like())

    def tearDown(self):
        self.folder.cleanup()

    def test_best_match_comes_first(self):
        results = matching.search(self.path, d_sub_like(10, 10), pins=5, gender="plug")
        self.assertEqual([r["name"] for r in results], ["D-like", "Round-like"])
        self.assertGreater(results[0]["score"], 0.95)

    def test_limit(self):
        self.assertEqual(len(matching.search(self.path, d_sub_like(), limit=1)), 1)

    def test_empty_query_is_rejected(self):
        with self.assertRaises(db.InvalidConnector):
            matching.search(self.path, to_rows(blank()))


if __name__ == "__main__":
    unittest.main()
