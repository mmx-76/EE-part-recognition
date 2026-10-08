"""More D-sub connectors and Harting Han industrial inserts.

Approximate drawings, made from general knowledge. Check them against real parts.
Each entry: (name, pins, plug or socket, industry, size in mm or None if unsure, drawing function)
Males have pins (P); females have sockets (O).
"""
from drawing_tools import SHAPE_TESTS, Canvas, female, spread


def _dsub(width, height, counts):
    """A D-shaped shell with evenly spread rows of contacts, kept clear of the slanted sides."""
    c = Canvas()
    c.shape("dshape", 0, 0, height, width, "S")
    inner = height - 4
    for i, count in enumerate(counts):
        row = 2 + (round(i * (inner - 1) / (len(counts) - 1)) if len(counts) > 1 else inner // 2)
        inside = [col for col in range(width) if SHAPE_TESTS["dshape"](row, col, height, width)]
        first, last = inside[0] + 2, inside[-1] - 2   # stay clear of the slanted shell sides
        for x in spread(count, last - first + 1):
            c.put(row, first + x, "P")
    return c.rows()


def _micro_d(width, counts):
    """Micro-D: a slim rectangular shell (bottom corners cut) with two rows of fine-pitch contacts."""
    c = Canvas()
    c.shape("rectangle", 0, 0, 8, width, "S")
    c.chamfer(0, 0, 8, width, "bl", 2, "S")
    c.chamfer(0, 0, 8, width, "br", 2, "S")
    for i, count in enumerate(counts):
        for x in spread(count, width - 6):
            c.put(2 + i * 3, 3 + x, "P")
    return c.rows()


def _han(rows, width, extra_height=0, contact=1, pe_blob=2):
    """A rectangular Han insert: rows of contacts (list of counts) plus the PE (earth) contact."""
    height = 5 + 4 * len(rows) + extra_height
    c = Canvas()
    c.shape("rectangle", 0, 0, height, width, "H")
    usable = width - 3 - (pe_blob + 6)   # leave a clear gap before the earth contact
    for i, count in enumerate(rows):
        row = 3 + i * 4
        for column in spread(count, usable):
            c.contact_at(row, 3 + column, contact, "P")
    c.contact_at(height // 2, width - 4, pe_blob, "P")      # the PE (protective earth) contact
    return c.rows()


_DSUBS = [  # name, shell width (cells), height, contact rows, pins, size mm
    ("DA-15", 27, 9, [8, 7], 15, 25),
    ("DC-37", 32, 7, [19, 18], 37, 55),
    ("DD-50", 32, 9, [17, 16, 17], 50, 53),
    ("HD-26 (high density 3-row)", 27, 9, [9, 9, 8], 26, 25),
    ("HD-44 (high density 3-row)", 31, 9, [15, 15, 14], 44, 38),
    ("HD-62 (high density 3-row)", 32, 9, [21, 21, 20], 62, 55),
]

_MICRO_D = [("Micro-D 9", 16, [5, 4], 9), ("Micro-D 15", 22, [8, 7], 15),
            ("Micro-D 25", 30, [13, 12], 25), ("Micro-D 51", 32, [26, 25], 51)]

# Harting Han inserts: name, contact rows, width, contacts incl. earth, contact size
_HAN = [
    ("Han 3 A (3 contacts + PE)", [3], 18, 4, 1),
    ("Han 6 B (6 contacts + PE)", [3, 3], 19, 7, 1),
    ("Han 10 B (10 contacts + PE)", [5, 5], 27, 11, 1),
    ("Han 16 B (16 contacts + PE)", [8, 8], 32, 17, 1),
    ("Han 24 B (24 contacts + PE)", [8, 8, 8], 32, 25, 1),
    ("Han 7 D (7 contacts + PE)", [4, 3], 15, 8, 1),
    ("Han 8 D (8 contacts + PE)", [4, 4], 15, 9, 1),
    ("Han 15 D (15 contacts + PE)", [8, 7], 23, 16, 1),
    ("Han 6 E (6 contacts + PE)", [3, 3], 21, 7, 2),
    ("Han 10 E (10 contacts + PE)", [5, 5], 29, 11, 2),
    ("Han 16 E (16 contacts + PE)", [8, 8], 32, 17, 2),
    ("Han 24 E (24 contacts + PE)", [8, 8, 8], 32, 25, 2),
]

CONNECTORS = []


def _add(name, pins, industry, size, build):
    CONNECTORS.append(("%s, male" % name, pins, "plug", industry, size, build))
    CONNECTORS.append(("%s, female" % name, pins, "socket", industry, size, lambda b=build: female(b())))


for _name, _w, _h, _counts, _pins, _size in _DSUBS:
    _add("D-sub " + _name, _pins, "computing" if "HD" in _name else "industrial", _size,
         lambda w=_w, h=_h, n=_counts: _dsub(w, h, n))
for _name, _w, _counts, _pins in _MICRO_D:
    _add(_name + " (MIL-DTL-83513)", _pins, "aerospace", None, lambda w=_w, n=_counts: _micro_d(w, n))
for _name, _rows, _w, _pins, _contact in _HAN:
    _add("Harting " + _name, _pins, "industrial", None,
         lambda r=_rows, w=_w, k=_contact: _han(r, w, contact=k, pe_blob=2 if k == 1 else 3))
