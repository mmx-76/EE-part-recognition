"""Helpers for drawing connector faces with code instead of by hand.

They do the same jobs as the shape and pin-pattern buttons in the drawing page.
Letters: . empty   H plastic housing   S metal shell   P pin   O socket   K key feature
"""
import math

SIZE = 32


class Canvas:
    """A blank 32 x 32 grid we can draw on with code."""

    def __init__(self):
        self.cells = [["."] * SIZE for _ in range(SIZE)]

    def put(self, row, col, letter):
        if 0 <= row < SIZE and 0 <= col < SIZE:
            self.cells[row][col] = letter

    def shape(self, name, top, left, height, width, letter, filled=False):
        """Same as dragging a shape box on the page. `name` is one of SHAPE_TESTS."""
        inside = SHAPE_TESTS[name]
        for r in range(height):
            for c in range(width):
                if not inside(r, c, height, width):
                    continue
                on_edge = not all(
                    0 <= rr < height and 0 <= cc < width and inside(rr, cc, height, width)
                    for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)))
                if filled or on_edge:
                    self.put(top + r, left + c, letter)

    def chamfer(self, top, left, height, width, corner, size, letter):
        """Cut a diagonal corner off a box (corner is 'tl', 'tr', 'bl' or 'br')."""
        for i in range(size + 1):
            for j in range(size + 1 - i):
                r = top + i if corner[0] == "t" else top + height - 1 - i
                c = left + j if corner[1] == "l" else left + width - 1 - j
                self.cells[r][c] = letter if i + j == size else "."

    def pins(self, kind, top, left, height, width, letter, count=1, rows=1):
        """Same as the pin-pattern buttons: kind is row, grid, ring or staggered."""
        for r, c in PATTERNS[kind](height, width, count, rows):
            self.put(top + r, left + c, letter)

    def blob(self, top, left, height, width, letter):
        """A solid block of one letter (a fat contact, a latch, a key)."""
        for r in range(top, top + height):
            for c in range(left, left + width):
                self.put(r, c, letter)

    def contact_at(self, row, col, size, letter):
        """A contact of size x size cells centred on (row, col)."""
        self.blob(row - size // 2, col - size // 2, size, size, letter)

    def rows(self):
        return ["".join(row) for row in self.cells]


def spread(count, length):
    if count == 1:
        return [round((length - 1) / 2)]
    return [round(i * (length - 1) / (count - 1)) for i in range(count)]


def _rounded(r, c, h, w):
    radius = max(1, min(4, min(h, w) // 3))
    near_v = r < radius or r >= h - radius
    near_h = c < radius or c >= w - radius
    if not (near_v and near_h):
        return True
    centre_r = radius - 0.5 if r < radius else h - radius - 0.5
    centre_c = radius - 0.5 if c < radius else w - radius - 0.5
    return (r - centre_r) ** 2 + (c - centre_c) ** 2 <= radius ** 2


def _trapezoid(r, c, h, w):
    max_inset = max(1, round(w * 0.15))
    inset = round(max_inset * (r / max(1, h - 1)))
    return inset <= c < w - inset


SHAPE_TESTS = {
    "rectangle": lambda r, c, h, w: True,
    "rounded": _rounded,
    "oval": lambda r, c, h, w: ((c + 0.5 - w / 2) / (w / 2)) ** 2 + ((r + 0.5 - h / 2) / (h / 2)) ** 2 <= 1,
    "trapezoid": _trapezoid,
    "dshape": lambda r, c, h, w: _trapezoid(r, c, h, w) and _rounded(r, c, h, w),
}


def _ring(h, w, n, rows):
    points = []
    for i in range(n):
        angle = 2 * math.pi * i / n
        points.append((round((h - 1) / 2 - (h - 1) / 2 * math.cos(angle)),
                       round((w - 1) / 2 + (w - 1) / 2 * math.sin(angle))))
    return points


def _staggered(h, w, n, rows):
    top_count, bottom_count = math.ceil(n / 2), n // 2
    top_cols = spread(top_count, w)
    points = [(0, c) for c in top_cols]
    for i in range(bottom_count):
        points.append((h - 1, round((top_cols[i] + top_cols[i + 1]) / 2)))
    return points


PATTERNS = {
    "row": lambda h, w, n, rows: [(round((h - 1) / 2), c) for c in spread(n, w)],
    "grid": lambda h, w, n, rows: [(r, c) for r in spread(rows, h) for c in spread(n, w)],
    "ring": _ring,
    "staggered": _staggered,
}


def female(rows):
    """The matching socket version: swap pins for sockets."""
    return [row.replace("P", "O") for row in rows]


def male(rows):
    return [row.replace("O", "P") for row in rows]


def polar(centre_row, centre_col, radius, degrees):
    """The cell `radius` cells from the centre, at an angle (0 = straight up, clockwise)."""
    angle = math.radians(degrees)
    return round(centre_row - radius * math.cos(angle)), round(centre_col + radius * math.sin(angle))
