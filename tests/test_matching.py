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


def info(pins=None, gender="unknown", size=None, industry="unknown"):
    return {"pins": pins, "gender": gender, "size_mm": size, "industry": industry}


NOTHING = info()


class CombineTests(unittest.TestCase):
    def test_unrelated_drawings_score_near_zero(self):
        self.assertEqual(matching.combine(0.25, NOTHING, NOTHING)["score"], 0.0)
        self.assertLess(matching.combine(0.40, NOTHING, NOTHING)["score"], 0.25)

    def test_identical_drawings_score_one(self):
        self.assertAlmostEqual(matching.combine(1.0, NOTHING, NOTHING)["score"], 1.0)

    def test_unknown_details_change_nothing(self):
        plain = matching.combine(0.8, NOTHING, info(9, "plug", 12, "computing"))
        self.assertAlmostEqual(plain["score"], matching.calibrate(0.8))
        self.assertIsNone(plain["pin_score"])

    def test_agreeing_details_do_not_inflate_a_poor_shape(self):
        shape_only = matching.combine(0.4, NOTHING, info(9, "plug", 12, "computing"))["score"]
        with_details = matching.combine(0.4, info(9, "plug", 12, "computing"),
                                        info(9, "plug", 12, "computing"))["score"]
        self.assertAlmostEqual(with_details, shape_only)

    def test_wrong_details_lower_the_score(self):
        same = info(9, "plug", 12, "computing")
        right = matching.combine(0.8, same, same)["score"]
        for wrong in (info(25, "plug", 12, "computing"), info(9, "socket", 12, "computing"),
                      info(9, "plug", 30, "computing"), info(9, "plug", 12, "automotive")):
            self.assertLess(matching.combine(0.8, same, wrong)["score"], right, wrong)

    def test_close_pin_counts_beat_far_ones(self):
        close = matching.combine(0.8, info(9), info(10))["score"]
        far = matching.combine(0.8, info(9), info(25))["score"]
        self.assertGreater(close, far)

    def test_42_pins_against_24_pins_is_a_poor_match(self):
        self.assertLess(matching.combine(0.8, info(42), info(24))["score"], 0.35)

    def test_sizes_within_15_percent_count_as_the_same(self):
        self.assertEqual(matching.size_score(12, 13.5), 1.0)
        self.assertEqual(matching.size_score(3.5, 6.35), matching.size_score(6.35, 3.5))
        self.assertLess(matching.size_score(3.5, 6.35), 0.4)   # mini-jack vs quarter-inch jack
        self.assertEqual(matching.size_score(5, 50), 0.0)

    def test_same_looking_connectors_are_separated_by_size(self):
        small = matching.combine(0.95, info(size=3.5), info(size=3.5))["score"]
        big = matching.combine(0.95, info(size=3.5), info(size=6.35))["score"]
        self.assertGreater(small - big, 0.3)

    def test_other_and_unknown_industry_never_count_against(self):
        base = matching.combine(0.8, NOTHING, NOTHING)["score"]
        for query, other in (("other", "computing"), ("computing", "other"), ("unknown", "computing")):
            self.assertAlmostEqual(matching.combine(0.8, info(industry=query), info(industry=other))["score"], base)

    def test_modes_ignore_prefer_require(self):
        query, other = info(9, "plug"), info(25, "socket")
        prefer = matching.combine(0.8, query, other)
        ignore = matching.combine(0.8, query, other, {"pins": "ignore", "gender": "ignore"})
        require = matching.combine(0.8, query, other, {"pins": "require"})
        self.assertAlmostEqual(ignore["score"], matching.calibrate(0.8))
        self.assertIsNone(ignore["pin_score"])
        self.assertFalse(prefer["excluded"])
        self.assertTrue(require["excluded"])
        self.assertFalse(matching.combine(0.8, info(9), info(9), {"pins": "require"})["excluded"])
        self.assertFalse(matching.combine(0.8, info(9), info(None), {"pins": "require"})["excluded"])  # unknown: benefit of the doubt


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
        results = matching.search(self.path, d_sub_like(10, 10), {"pins": 5, "gender": "plug"})
        self.assertEqual([r["name"] for r in results], ["D-like", "Round-like"])
        self.assertGreater(results[0]["score"], 0.95)
        self.assertLess(results[1]["score"], 0.3)  # a round connector is not a D-sub

    def test_connector_details_are_not_overwritten_by_scores(self):
        best = matching.search(self.path, d_sub_like(), {"pins": 5, "gender": "plug"})[0]
        self.assertEqual((best["pins"], best["gender"]), (5, "plug"))
        self.assertIn("pin_score", best)

    def test_require_drops_connectors_that_disagree(self):
        results = matching.search(self.path, d_sub_like(), {"pins": 3}, {"pins": "require"})
        self.assertEqual([r["name"] for r in results], ["Round-like"])

    def test_only_checked_leaves_out_drafts(self):
        db.add_connector(self.path, "Draft", 5, "plug", "other", d_sub_like(), reviewed=False)
        names = [r["name"] for r in matching.search(self.path, d_sub_like(), only_checked=True)]
        self.assertNotIn("Draft", names)
        self.assertIn("Draft", [r["name"] for r in matching.search(self.path, d_sub_like())])

    def test_limit(self):
        self.assertEqual(len(matching.search(self.path, d_sub_like(), limit=1)), 1)

    def test_empty_query_is_rejected(self):
        with self.assertRaises(db.InvalidConnector):
            matching.search(self.path, to_rows(blank()))


if __name__ == "__main__":
    unittest.main()
