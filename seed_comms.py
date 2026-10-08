"""Communications and data connectors: telephone, Ethernet variants, fibre optic, ribbon and USB.

Approximate drawings, made from general knowledge. Check them against real parts.
Each entry: (name, pins, plug or socket, industry, size in mm or None if unsure, drawing function)
Fibre connectors: the centre contact (P) stands for the fibre end; "socket" means the female side.
"""
from drawing_tools import Canvas, female, polar, spread


def _modular_jack(width, height, contacts, shield=False):
    c = Canvas()
    o = 3 if shield else 0
    if shield:
        c.shape("rectangle", 0, 0, height + 6, width + 6, "S")
    c.shape("rectangle", o, o, height, width, "H")
    for x in spread(contacts, width - 6):
        c.put(o + 3, o + 3 + x, "O")
    c.blob(o + height - 3, o + width // 2 - 3, 3, 6, "K")      # the latch slot
    return c.rows()


def _modular_plug(width, height, contacts):
    c = Canvas()
    c.shape("rectangle", 0, 0, height, width, "H")
    for x in spread(contacts, width - 6):
        c.put(2, 3 + x, "P")
    c.blob(height - 2, width // 2 - 3, 2, 6, "K")              # the latch tab
    return c.rows()


def _ribbon(width, per_row, shape="rectangle"):
    """Centronics-style ribbon contacts: two rows inside a long metal shell."""
    c = Canvas()
    c.shape(shape, 0, 0, 8, width, "S")
    c.shape("rectangle", 2, 2, 4, width - 4, "H")
    for x in spread(per_row, width - 6):
        c.put(3, 3 + x, "P")
        c.put(5, 3 + x, "P")
    return c.rows()


def _round_m(d, contacts, key, pin_circle=True, shell_rings=2):
    """M8 / M12 style round connector: coupling ring, inner housing, contacts on a circle, a key."""
    c = Canvas()
    c.shape("oval", 0, 0, d, d, "S")
    if shell_rings == 2:
        c.shape("oval", 3, 3, d - 6, d - 6, "H")
    middle = d // 2
    radius = (d - 6) / 2 - 3 if shell_rings == 2 else d / 2 - 4
    for i in range(contacts):
        row, col = polar(middle, middle, radius, 360 * i / contacts + 360 / contacts / 2 * 0)
        c.put(row, col, "P")
    c.put(3 if shell_rings == 2 else 2, middle, key)
    c.put(3 if shell_rings == 2 else 2, middle - 1, key)
    return c.rows()


def _usb_mini():
    c = Canvas()
    c.shape("rectangle", 0, 0, 9, 14, "S")
    c.chamfer(0, 0, 9, 14, "bl", 2, "S")
    c.chamfer(0, 0, 9, 14, "br", 2, "S")
    for x in spread(5, 8):
        c.put(3, 3 + x, "P")
    return c.rows()


def _usb3_micro_b():
    c = Canvas()
    c.shape("rectangle", 0, 0, 7, 14, "S")
    c.chamfer(0, 0, 7, 14, "bl", 2, "S")
    c.shape("rectangle", 0, 13, 5, 11, "S")
    for x in spread(5, 8):
        c.put(2, 3 + x, "P")
    for x in spread(5, 6):
        c.put(2, 15 + x, "P")
    return c.rows()


def _usb3_a():
    c = Canvas()
    c.shape("rectangle", 0, 0, 10, 24, "S")
    c.shape("rectangle", 2, 2, 6, 20, "H", filled=True)
    for x in spread(4, 16):
        c.put(3, 4 + x, "P")
    for x in spread(5, 14):
        c.put(6, 5 + x, "P")
    return c.rows()


def _usb3_b():
    c = Canvas()
    c.shape("rectangle", 4, 0, 11, 15, "S")
    c.shape("rectangle", 0, 3, 5, 9, "S")
    for x in spread(4, 7):
        c.put(5, 4 + x, "P")
    for x in spread(5, 5):
        c.put(2, 5 + x, "P")
    return c.rows()


def _lightning():
    c = Canvas()
    c.shape("rounded", 0, 0, 7, 22, "S")
    for x in spread(8, 16):
        c.put(3, 3 + x, "P")
    return c.rows()


def _lc(duplex):
    c = Canvas()
    width = 26 if duplex else 14
    c.shape("rectangle", 0, 0, 14, width, "H")
    centres = (7, width - 8) if duplex else (width // 2,)
    for centre in centres:
        c.shape("oval", 4, centre - 3, 7, 7, "S")
        c.put(7, centre, "P")
    c.blob(12, width // 2 - 2, 2, 4, "K")   # latch
    return c.rows()


def _sc():
    c = Canvas()
    c.shape("rectangle", 0, 0, 15, 15, "H")
    c.shape("oval", 3, 3, 9, 9, "S")
    c.put(7, 7, "P")
    c.blob(0, 6, 2, 3, "K")
    return c.rows()


def _round_fibre(d, bayonet):
    c = Canvas()
    c.shape("oval", 2, 2, d, d, "S")
    c.shape("oval", 6, 6, d - 8, d - 8, "S")
    middle = 2 + d // 2
    c.put(middle, middle, "P")
    if bayonet:   # ST: bayonet lugs
        for r in (middle - 1, middle):
            c.put(r, 1, "K")
            c.put(r, 2 + d, "K")
    else:         # FC: key bump at the top
        c.blob(1, middle - 1, 2, 3, "K")
    return c.rows()


def _mpo(male):
    c = Canvas()
    c.shape("rectangle", 0, 0, 11, 28, "H")
    for x in spread(12, 18):
        c.put(5, 5 + x, "P")                                   # the 12 fibre ends
    for column in (2, 24):
        if male:
            c.blob(4, column, 3, 2, "S")                       # solid guide pins
        else:
            c.shape("rectangle", 3, column - 1, 5, 4, "S")     # hollow guide holes
    return c.rows()


CONNECTORS = [
    ("RJ11 (6P4C) telephone plug", 4, "plug", "networking", 9.7, lambda: _modular_plug(12, 10, 4)),
    ("RJ11 (6P4C) telephone jack", 4, "socket", "networking", 9.7, lambda: _modular_jack(14, 11, 4)),
    ("RJ12 (6P6C) plug", 6, "plug", "networking", 9.7, lambda: _modular_plug(12, 10, 6)),
    ("RJ12 (6P6C) jack", 6, "socket", "networking", 9.7, lambda: _modular_jack(14, 11, 6)),
    ("RJ45 (8P8C) jack, shielded", 8, "socket", "networking", None, lambda: _modular_jack(20, 14, 8, shield=True)),
    ("Telco 50 / RJ21 (Amphenol ribbon), male", 50, "plug", "networking", None, lambda: _ribbon(32, 25)),
    ("Telco 50 / RJ21 (Amphenol ribbon), female", 50, "socket", "networking", None, lambda: female(_ribbon(32, 25))),
    ("Centronics 36 (IEEE 1284-B), male", 36, "plug", "computing", None, lambda: _ribbon(28, 18)),
    ("Centronics 36 (IEEE 1284-B), female", 36, "socket", "computing", None, lambda: female(_ribbon(28, 18))),
    ("M12 4-pin D-coded (Ethernet), male", 4, "plug", "industrial", 15, lambda: _round_m(20, 4, "K")),
    ("M12 4-pin D-coded (Ethernet), female", 4, "socket", "industrial", 15, lambda: female(_round_m(20, 4, "K"))),
    ("M12 8-pin X-coded (10 Gb Ethernet), male", 8, "plug", "industrial", 15, lambda: _round_m(20, 8, "K")),
    ("M12 8-pin X-coded (10 Gb Ethernet), female", 8, "socket", "industrial", 15, lambda: female(_round_m(20, 8, "K"))),
    ("M8 4-pin, male", 4, "plug", "industrial", 11, lambda: _round_m(14, 4, "K", shell_rings=1)),
    ("M8 4-pin, female", 4, "socket", "industrial", 11, lambda: female(_round_m(14, 4, "K", shell_rings=1))),
    ("USB Mini-B plug", 5, "plug", "computing", None, _usb_mini),
    ("USB 3.0 Micro-B plug", 10, "plug", "computing", None, _usb3_micro_b),
    ("USB 3.0 Type-A plug", 9, "plug", "computing", 12, _usb3_a),
    ("USB 3.0 Type-B plug", 9, "plug", "computing", None, _usb3_b),
    ("Apple Lightning plug", 8, "plug", "computing", 7.7, _lightning),
    ("Fibre LC simplex", 1, "plug", "networking", None, lambda: _lc(False)),
    ("Fibre LC duplex", 2, "plug", "networking", None, lambda: _lc(True)),
    ("Fibre SC", 1, "plug", "networking", None, _sc),
    ("Fibre ST (bayonet)", 1, "plug", "networking", None, lambda: _round_fibre(15, True)),
    ("Fibre FC (threaded)", 1, "plug", "networking", None, lambda: _round_fibre(15, False)),
    ("Fibre MPO / MTP 12-fibre, male (guide pins)", 12, "plug", "networking", None, lambda: _mpo(True)),
    ("Fibre MPO / MTP 12-fibre, female (guide holes)", 12, "socket", "networking", None, lambda: _mpo(False)),
]
