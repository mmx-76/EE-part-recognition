"""The starter connectors, drawn with code instead of by hand.

IMPORTANT: these are simplified, approximate drawings of real connector faces, made without
the manufacturers' drawings in front of me. Treat them as a first draft: load one in the app,
correct it, and save it again (or delete it) if it doesn't match the real thing.

The helpers below do the same jobs as the shape and pin-pattern buttons in the drawing page.
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


# ---------------------------------------------------------------- the connectors

def d_sub(width, height, pin_layout, pin_count, **layout):
    c = Canvas()
    c.shape("dshape", 0, 0, height, width, "S")
    c.pins(pin_layout, 2, 3, height - 4, width - 6, "P", pin_count, **layout)
    return c.rows()


def usb_a():
    c = Canvas()
    c.shape("rectangle", 0, 0, 9, 24, "S")
    c.shape("rectangle", 2, 2, 5, 20, "H", filled=True)
    c.pins("row", 4, 4, 1, 16, "P", 4)
    return c.rows()


def usb_b():
    c = Canvas()
    c.shape("rectangle", 0, 0, 14, 14, "S")
    c.chamfer(0, 0, 14, 14, "tl", 3, "S")
    c.chamfer(0, 0, 14, 14, "tr", 3, "S")
    c.pins("grid", 4, 3, 6, 8, "P", 2, rows=2)
    return c.rows()


def usb_c():
    c = Canvas()
    c.shape("rounded", 0, 0, 10, 26, "S")
    c.pins("row", 2, 3, 1, 20, "P", 12)
    c.pins("row", 7, 3, 1, 20, "P", 12)
    return c.rows()


def usb_c_receptacle():
    c = Canvas()
    c.shape("rounded", 0, 0, 10, 26, "S")
    c.shape("rectangle", 4, 3, 2, 20, "H", filled=True)
    c.pins("row", 3, 3, 1, 20, "O", 12)
    c.pins("row", 6, 3, 1, 20, "O", 12)
    return c.rows()


def micro_usb():
    c = Canvas()
    c.shape("rectangle", 0, 0, 7, 16, "S")
    c.chamfer(0, 0, 7, 16, "bl", 2, "S")
    c.chamfer(0, 0, 7, 16, "br", 2, "S")
    c.pins("row", 2, 3, 1, 10, "P", 5)
    return c.rows()


def hdmi():
    c = Canvas()
    c.shape("rectangle", 0, 0, 9, 28, "S")
    c.chamfer(0, 0, 9, 28, "bl", 2, "S")
    c.chamfer(0, 0, 9, 28, "br", 2, "S")
    c.pins("staggered", 2, 3, 5, 22, "P", 19)
    return c.rows()


def displayport():
    c = Canvas()
    c.shape("rectangle", 0, 0, 9, 26, "S")
    c.chamfer(0, 0, 9, 26, "tr", 3, "S")
    c.pins("row", 2, 3, 1, 20, "P", 10)
    c.pins("row", 6, 3, 1, 20, "P", 10)
    return c.rows()


def rj45_plug():
    c = Canvas()
    c.shape("rectangle", 0, 0, 12, 18, "H")
    c.pins("row", 2, 3, 1, 12, "P", 8)
    c.shape("rectangle", 10, 6, 2, 6, "K", filled=True)
    return c.rows()


def rj45_jack():
    c = Canvas()
    c.shape("rectangle", 0, 0, 14, 20, "H")
    c.pins("row", 3, 3, 1, 14, "O", 8)
    c.shape("rectangle", 11, 7, 3, 6, "K", filled=True)
    return c.rows()


def circle_with_centre(diameter, centre_letter, rings=("S",), extra=None):
    """Concentric round connector: outer ring(s) and a centre contact."""
    c = Canvas()
    size = diameter
    for i, letter in enumerate(rings):
        inset = i * 3
        c.shape("oval", inset, inset, size - 2 * inset, size - 2 * inset, letter)
    c.put(size // 2, size // 2, centre_letter)
    if size % 2 == 0:
        c.put(size // 2 - 1, size // 2 - 1, centre_letter)
        c.put(size // 2 - 1, size // 2, centre_letter)
        c.put(size // 2, size // 2 - 1, centre_letter)
    if extra:
        extra(c)
    return c.rows()


def bnc_male():
    def bayonet_pins(c):
        for r in (7, 8):
            c.put(r, 0, "K")
            c.put(r, 16, "K")
    return circle_with_centre(17, "P", ("S", "H"), extra=bayonet_pins)


def xlr_male():
    c = Canvas()
    c.shape("oval", 0, 0, 20, 20, "S")
    c.pins("grid", 5, 5, 10, 10, "P", 2, rows=1)
    c.put(14, 10, "P")
    c.put(14, 9, "P")
    c.put(2, 9, "K")
    c.put(2, 10, "K")
    return c.rows()


def din5():
    c = Canvas()
    c.shape("oval", 0, 0, 21, 21, "S")
    for r, col in ((8, 3), (5, 6), (4, 10), (5, 14), (8, 17)):
        c.put(r, col, "P")
    c.put(18, 10, "K")
    c.put(18, 9, "K")
    return c.rows()


def mini_din6():
    c = Canvas()
    c.shape("oval", 0, 0, 15, 15, "S")
    c.pins("ring", 3, 3, 9, 9, "P", 6)
    c.put(1, 7, "K")
    c.put(2, 7, "K")
    return c.rows()


def m12_male():
    c = Canvas()
    c.shape("oval", 0, 0, 20, 20, "S")
    c.shape("oval", 3, 3, 14, 14, "H")
    c.pins("ring", 6, 6, 8, 8, "P", 4)
    c.put(4, 9, "K")
    c.put(4, 10, "K")
    return c.rows()


def header_2x5():
    c = Canvas()
    c.shape("rectangle", 0, 0, 9, 17, "H")
    c.pins("grid", 2, 3, 5, 11, "P", 5, rows=2)
    c.shape("rectangle", 0, 7, 1, 3, "K", filled=True)
    return c.rows()


def molex_4_peripheral_female():
    c = Canvas()
    c.shape("rectangle", 0, 0, 8, 22, "H")
    c.chamfer(0, 0, 8, 22, "tl", 2, "H")
    c.chamfer(0, 0, 8, 22, "tr", 2, "H")
    c.pins("row", 3, 3, 2, 16, "O", 4)
    return c.rows()


def sata_data():
    c = Canvas()
    c.shape("rectangle", 0, 0, 8, 24, "H")
    c.chamfer(0, 0, 8, 24, "tr", 3, "H")
    c.pins("row", 4, 3, 1, 18, "P", 7)
    c.shape("rectangle", 1, 2, 2, 6, "K", filled=True)
    return c.rows()


def obd2_female():
    c = Canvas()
    c.shape("trapezoid", 0, 0, 10, 28, "S")
    c.pins("row", 2, 3, 1, 22, "O", 8)
    c.pins("row", 7, 4, 1, 20, "O", 8)
    c.shape("rectangle", 4, 6, 1, 16, "K", filled=True)
    return c.rows()


def iec_c14():
    c = Canvas()
    c.shape("rectangle", 0, 0, 14, 20, "H")
    c.chamfer(0, 0, 14, 20, "tl", 4, "H")
    c.chamfer(0, 0, 14, 20, "tr", 4, "H")
    for r in range(3, 7):
        c.put(r, 9, "P")
        c.put(r, 10, "P")
    for r in range(8, 12):
        for col in (4, 15):
            c.put(r, col, "P")
    return c.rows()


def nema_5_15p():
    c = Canvas()
    c.shape("rounded", 0, 0, 18, 18, "H")
    for r in range(3, 8):
        c.put(r, 5, "P")
        c.put(r, 12, "P")
    c.put(12, 8, "P")
    c.put(12, 9, "P")
    c.put(13, 8, "P")
    c.put(13, 9, "P")
    return c.rows()


def _barrel_plug():
    return circle_with_centre(15, "O", ("S",))


def _barrel_jack():
    return circle_with_centre(15, "P", ("S",))


def _trs_plug():
    return circle_with_centre(13, "P", ("S", "H"))


def _rca_plug():
    return circle_with_centre(15, "P", ("S",))


def _rca_jack():
    return circle_with_centre(15, "O", ("S",))


def xlr_female():
    c = Canvas()
    c.shape("oval", 0, 0, 20, 20, "S")
    c.shape("oval", 2, 2, 16, 16, "H", filled=True)
    c.put(5, 6, "O"); c.put(5, 13, "O"); c.put(13, 9, "O"); c.put(13, 10, "O")
    c.put(2, 9, "K"); c.put(2, 10, "K")
    return c.rows()


def _m12_female():
    return female(m12_male())


# name, pins, plug or socket, industry, drawing
STARTER_CONNECTORS = [
    ("DE-9 (DB-9) serial, male",        9,  "plug",   "computing",   lambda: d_sub(19, 9, "staggered", 9)),
    ("DE-9 (DB-9) serial, female",      9,  "socket", "computing",   lambda: female(d_sub(19, 9, "staggered", 9))),
    ("DB-25 parallel/serial, male",     25, "plug",   "computing",   lambda: d_sub(31, 9, "staggered", 25)),
    ("DB-25 parallel/serial, female",   25, "socket", "computing",   lambda: female(d_sub(31, 9, "staggered", 25))),
    ("HD-15 VGA, female (on the PC)",   15, "socket", "audio_video", lambda: female(d_sub(19, 11, "grid", 5, rows=3))),
    ("HD-15 VGA, male (on the cable)",  15, "plug",   "audio_video", lambda: d_sub(19, 11, "grid", 5, rows=3)),
    ("USB-A plug",                      4,  "plug",   "computing",   usb_a),
    ("USB-A receptacle (port)",         4,  "socket", "computing",   lambda: female(usb_a())),
    ("USB-B plug",                      4,  "plug",   "computing",   usb_b),
    ("USB-C plug",                      24, "plug",   "computing",   usb_c),
    ("USB-C receptacle (port)",         24, "socket", "computing",   usb_c_receptacle),
    ("Micro-USB B plug",                5,  "plug",   "computing",   micro_usb),
    ("HDMI Type A plug",                19, "plug",   "audio_video", hdmi),
    ("DisplayPort plug",                20, "plug",   "audio_video", displayport),
    ("RJ45 (8P8C) plug",                8,  "plug",   "networking",  rj45_plug),
    ("RJ45 (8P8C) jack",                8,  "socket", "networking",  rj45_jack),
    ("DC barrel plug (centre-hole type)", 2, "plug",  "mains_power", _barrel_plug),
    ("DC barrel jack (centre-pin type)",  2, "socket", "mains_power", _barrel_jack),
    ("3.5 mm TRS audio plug (mini-jack)", 3, "plug",  "audio_video", _trs_plug),
    ("6.35 mm (1/4 inch) TRS audio plug", 3, "plug",  "audio_video", _trs_plug),
    ("RCA (phono) plug",                2,  "plug",   "audio_video", _rca_plug),
    ("BNC plug (male)",                 1,  "plug",   "audio_video", bnc_male),
    ("XLR 3-pin, male",                 3,  "plug",   "audio_video", xlr_male),
    ("XLR 3-pin, female",               3,  "socket", "audio_video", xlr_female),
    ("DIN 5-pin 180 degree (MIDI) plug", 5, "plug",   "audio_video", din5),
    ("Mini-DIN 6-pin (PS/2) plug",      6,  "plug",   "computing",   mini_din6),
    ("M12 4-pin A-coded, male",         4,  "plug",   "industrial",  m12_male),
    ("M12 4-pin A-coded, female",       4,  "socket", "industrial",  _m12_female),
    ("2x5 pin header (shrouded, IDC)",  10, "plug",   "computing",   header_2x5),
    ("Molex 4-pin peripheral, female",  4,  "socket", "computing",   molex_4_peripheral_female),
    ("SATA data plug",                  7,  "plug",   "computing",   sata_data),
    ("OBD-II (J1962) female socket",    16, "socket", "automotive",  obd2_female),
    ("IEC C14 inlet (male)",            3,  "plug",   "mains_power", iec_c14),
    ("IEC C13 outlet (female)",         3,  "socket", "mains_power", lambda: female(iec_c14())),
    ("NEMA 5-15P plug (North American mains)", 3, "plug", "mains_power", nema_5_15p),
]


# Approximate size of each mating face (longest side, in millimetres), from general knowledge.
# They are rough: the search treats sizes within about 15% as the same.
STARTER_SIZES = {
    "DE-9 (DB-9) serial, male": 17, "DE-9 (DB-9) serial, female": 17,
    "DB-25 parallel/serial, male": 38, "DB-25 parallel/serial, female": 38,
    "HD-15 VGA, female (on the PC)": 17, "HD-15 VGA, male (on the cable)": 17,
    "USB-A plug": 12, "USB-A receptacle (port)": 12, "USB-B plug": 8.5,
    "USB-C plug": 8.3, "USB-C receptacle (port)": 8.3, "Micro-USB B plug": 6.9,
    "HDMI Type A plug": 14, "DisplayPort plug": 17,
    "RJ45 (8P8C) plug": 12, "RJ45 (8P8C) jack": 12,
    "DC barrel plug (centre-hole type)": 5.5, "DC barrel jack (centre-pin type)": 5.5,
    "3.5 mm TRS audio plug (mini-jack)": 3.5, "6.35 mm (1/4 inch) TRS audio plug": 6.35,
    "RCA (phono) plug": 8.5, "BNC plug (male)": 10,
    "XLR 3-pin, male": 20, "XLR 3-pin, female": 20,
    "DIN 5-pin 180 degree (MIDI) plug": 13, "Mini-DIN 6-pin (PS/2) plug": 9.5,
    "M12 4-pin A-coded, male": 15, "M12 4-pin A-coded, female": 15,
    "2x5 pin header (shrouded, IDC)": 23, "Molex 4-pin peripheral, female": 19,
    "SATA data plug": 14, "OBD-II (J1962) female socket": 38,
    "IEC C14 inlet (male)": 28, "IEC C13 outlet (female)": 28,
    "NEMA 5-15P plug (North American mains)": 40,
}

# Starter connectors that were renamed in a later version: old name -> new name.
RENAMED_STARTERS = {"3.5 mm / 6.35 mm TRS audio plug": "3.5 mm TRS audio plug (mini-jack)"}


def starter_rows():
    """Yield (name, pins, gender, industry, rows) for every starter connector."""
    for name, pins, gender, industry, build in STARTER_CONNECTORS:
        yield name, pins, gender, industry, build()
