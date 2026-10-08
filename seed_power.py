"""Heavy power, industrial power and mains connectors.

Approximate drawings, made from general knowledge. The faces of the big industrial connectors
(IEC 60309, NEMA locking, Socapex, powerCON) are especially rough: check them against real parts.
Sizes are ballpark figures, and None where I wasn't confident.
Each entry: (name, pins, plug, socket or unknown, industry, size in mm or None, drawing function)
Males/plugs have pins (P); females/sockets have sockets (O).
"""
from drawing_tools import Canvas, female, polar, spread

POWER = "mains_power"


def _carrier(c, blob_size, contacts_xy, width, height, divider=True, chamfers=()):
    c.shape("rectangle", 0, 0, height, width, "H")
    if divider:
        c.blob(1, width // 2, height - 2, 1, "H")
    for corner in chamfers:
        c.chamfer(0, 0, height, width, corner, 2, "H")
    for row, col in contacts_xy:
        c.contact_at(row, col, blob_size, "P")


def _anderson(blob_size, width, height):
    """Genderless two-pole Anderson housing: two cavities side by side, each with a contact."""
    c = Canvas()
    _carrier(c, blob_size, [(height // 2, width // 4), (height // 2, 3 * width // 4)], width, height)
    return c.rows()


def _xt(width, height, blob_size):
    c = Canvas()
    _carrier(c, blob_size, [(height // 2, width // 4 + 1), (height // 2, 3 * width // 4 - 1)],
             width, height, divider=False, chamfers=("tl", "tr"))
    return c.rows()


def _deans():
    c = Canvas()
    c.shape("rectangle", 0, 0, 9, 12, "H")
    c.chamfer(0, 0, 9, 12, "tr", 2, "H")
    c.blob(2, 3, 5, 1, "P")
    c.blob(2, 8, 5, 1, "P")
    return c.rows()


def _camlok(centre):
    c = Canvas()
    c.shape("oval", 2, 2, 19, 19, "S")
    c.shape("oval", 5, 5, 13, 13, "H")
    c.blob(9, 9, 5, 5, centre)
    c.blob(1, 11, 2, 2, "K")
    c.blob(21, 11, 2, 2, "K")
    return c.rows()


def _dinse(centre):
    c = Canvas()
    c.shape("oval", 0, 0, 15, 15, "S")
    c.blob(4, 4, 7, 7, centre)
    return c.rows()


def _cee(n, d, blob):
    """IEC 60309 industrial round plug/socket: contacts on a circle, earth at 6 o'clock, a key."""
    c = Canvas()
    o = 2
    middle = o + d // 2
    c.shape("oval", o, o, d, d, "S")
    c.shape("oval", o + 3, o + 3, d - 6, d - 6, "H")
    radius = (d - 6) / 2 - 4
    for i in range(n):
        row, col = polar(middle, middle, radius, 180 + 360 * i / n)
        c.contact_at(row, col, blob + 1 if i == 0 else blob, "P")   # i = 0 is the earth contact
    c.blob(o + d, middle - 1, 2, 3, "K")                              # the key at 6 o'clock
    return c.rows()


def _nema_locking(blade_angles, ground_angle, d=21):
    """NEMA locking plug (L5-30P and friends): round face, curved blades, a ground contact."""
    c = Canvas()
    o = 2
    middle = o + d // 2
    c.shape("oval", o, o, d, d, "H")
    radius = d / 2 - 4
    for angle in blade_angles:
        for step in (-20, -10, 0, 10, 20):
            row, col = polar(middle, middle, radius, angle + step)
            c.put(row, col, "P")
    row, col = polar(middle, middle, radius - 1, ground_angle)
    c.contact_at(row, col, 2, "P")
    return c.rows()


def _nema_14_50():
    c = Canvas()
    c.shape("rounded", 0, 0, 20, 20, "H")
    c.blob(3, 4, 6, 2, "P")
    c.blob(3, 14, 6, 2, "P")
    c.blob(11, 9, 5, 2, "P")
    c.contact_at(16, 10, 2, "P")
    return c.rows()


def _iec_inlet(width, height, blade_w, blade_h):
    """C14/C20-style inlet: a chamfered rectangle with earth at the top and L/N below."""
    c = Canvas()
    c.shape("rectangle", 0, 0, height, width, "H")
    c.chamfer(0, 0, height, width, "tl", 4, "H")
    c.chamfer(0, 0, height, width, "tr", 4, "H")
    c.blob(3, width // 2 - blade_w // 2, blade_h, blade_w, "P")
    c.blob(height - 2 - blade_h, 4, blade_h, blade_w, "P")
    c.blob(height - 2 - blade_h, width - 4 - blade_w, blade_h, blade_w, "P")
    return c.rows()


def _iec_c6():
    c = Canvas()
    c.shape("oval", 0, 0, 18, 20, "H")
    c.blob(3, 9, 4, 2, "P")
    c.blob(10, 4, 4, 2, "P")
    c.blob(10, 14, 4, 2, "P")
    return c.rows()


def _iec_c8():
    c = Canvas()
    c.shape("oval", 0, 0, 11, 13, "H")
    c.shape("oval", 0, 11, 11, 13, "H")
    c.blob(3, 5, 5, 1, "P")
    c.blob(3, 18, 5, 1, "P")
    return c.rows()


def _schuko():
    c = Canvas()
    c.shape("oval", 0, 0, 21, 21, "H")
    c.contact_at(10, 5, 2, "P")
    c.contact_at(10, 15, 2, "P")
    c.blob(0, 8, 1, 5, "P")      # earth clips top and bottom
    c.blob(20, 8, 1, 5, "P")
    return c.rows()


def _europlug():
    c = Canvas()
    c.shape("rounded", 0, 0, 11, 19, "H")
    c.contact_at(5, 4, 2, "P")
    c.contact_at(5, 14, 2, "P")
    return c.rows()


def _uk_plug():
    c = Canvas()
    c.shape("rounded", 0, 0, 19, 17, "H")
    c.blob(3, 7, 5, 3, "P")      # earth
    c.blob(11, 3, 3, 5, "P")     # neutral
    c.blob(11, 10, 3, 5, "P")    # live
    return c.rows()


def _au_plug():
    c = Canvas()
    c.shape("rounded", 0, 0, 17, 17, "H")
    for i in range(5):
        c.put(3 + i, 4 + i, "P")       # two angled blades in a V
        c.put(3 + i, 12 - i, "P")
    c.blob(11, 8, 4, 1, "P")           # earth
    return c.rows()


def _powercon(letter):
    c = Canvas()
    c.shape("oval", 2, 2, 19, 19, "S")
    c.shape("oval", 5, 5, 13, 13, "H")
    for angle in (0, 120, 240):
        row, col = polar(11, 11, 4, angle)
        c.contact_at(row, col, 2, letter)
    c.blob(1, 10, 2, 3, "K")
    c.blob(21, 10, 2, 3, "K")
    return c.rows()


def _socapex(letter):
    c = Canvas()
    c.shape("oval", 0, 0, 27, 27, "S")
    c.shape("oval", 3, 3, 21, 21, "H")
    c.put(13, 13, letter)
    for i in range(6):
        row, col = polar(13, 13, 4, 60 * i)
        c.put(row, col, letter)
    for i in range(12):
        row, col = polar(13, 13, 8, 30 * i + 15)
        c.put(row, col, letter)
    c.blob(1, 12, 2, 3, "K")
    return c.rows()


def _speakon(letter):
    c = Canvas()
    c.shape("oval", 0, 0, 21, 21, "S")
    c.shape("oval", 3, 3, 15, 15, "H")
    for angle in (45, 135, 225, 315):
        row, col = polar(10, 10, 4, angle)
        c.contact_at(row, col, 2, letter)
    c.blob(1, 4, 2, 2, "K")
    c.blob(1, 15, 2, 2, "K")
    return c.rows()


CONNECTORS = [
    ("Anderson SB50 (genderless)", 2, "unknown", POWER, None, lambda: _anderson(3, 22, 12)),
    ("Anderson SB120 (genderless)", 2, "unknown", POWER, None, lambda: _anderson(4, 28, 14)),
    ("Anderson SB175 (genderless)", 2, "unknown", POWER, None, lambda: _anderson(5, 32, 16)),
    ("Anderson Powerpole PP45 (genderless)", 2, "unknown", POWER, None, lambda: _anderson(2, 18, 9)),
    ("XT30, male", 2, "plug", POWER, 10, lambda: _xt(10, 6, 2)),
    ("XT30, female", 2, "socket", POWER, 10, lambda: female(_xt(10, 6, 2))),
    ("XT60, male", 2, "plug", POWER, 15.5, lambda: _xt(16, 9, 3)),
    ("XT60, female", 2, "socket", POWER, 15.5, lambda: female(_xt(16, 9, 3))),
    ("XT90, male", 2, "plug", POWER, 24, lambda: _xt(24, 11, 4)),
    ("XT90, female", 2, "socket", POWER, 24, lambda: female(_xt(24, 11, 4))),
    ("Deans T-plug, male", 2, "plug", POWER, None, _deans),
    ("Deans T-plug, female", 2, "socket", POWER, None, lambda: female(_deans())),
    ("Cam-Lok single pole, male", 1, "plug", "industrial", None, lambda: _camlok("P")),
    ("Cam-Lok single pole, female", 1, "socket", "industrial", None, lambda: _camlok("O")),
    ("Dinse welding connector, male", 1, "plug", "industrial", None, lambda: _dinse("P")),
    ("Dinse welding connector, female", 1, "socket", "industrial", None, lambda: _dinse("O")),
]

for _name, _n, _d, _blob, _size in [
        ("IEC 60309 16 A 2P+E (3 pin)", 3, 25, 1, 52), ("IEC 60309 16 A 3P+E (4 pin)", 4, 25, 1, 52),
        ("IEC 60309 16 A 3P+N+E (5 pin)", 5, 25, 1, 52), ("IEC 60309 32 A 3P+E (4 pin)", 4, 25, 2, 62),
        ("IEC 60309 32 A 3P+N+E (5 pin)", 5, 25, 2, 62), ("IEC 60309 63 A 3P+N+E (5 pin)", 5, 27, 3, 84),
        ("IEC 60309 125 A 3P+N+E (5 pin)", 5, 27, 4, 108)]:
    CONNECTORS.append(("%s, plug" % _name, _n, "plug", "industrial", _size,
                       lambda n=_n, d=_d, b=_blob: _cee(n, d, b)))
    CONNECTORS.append(("%s, socket" % _name, _n, "socket", "industrial", _size,
                       lambda n=_n, d=_d, b=_blob: female(_cee(n, d, b))))

CONNECTORS += [
    ("NEMA L5-30P locking plug", 3, "plug", POWER, None, lambda: _nema_locking((60, 300), 180)),
    ("NEMA L6-30P locking plug", 3, "plug", POWER, None, lambda: _nema_locking((90, 270), 180)),
    ("NEMA L14-30P locking plug", 4, "plug", POWER, None, lambda: _nema_locking((45, 315, 135), 225)),
    ("NEMA L21-30P locking plug", 5, "plug", POWER, None, lambda: _nema_locking((0, 72, 144, 216), 288)),
    ("NEMA 14-50P plug (RV / EV)", 4, "plug", POWER, None, _nema_14_50),
    ("IEC C20 inlet (16 A, male)", 3, "plug", POWER, None, lambda: _iec_inlet(26, 15, 2, 5)),
    ("IEC C19 outlet (16 A, female)", 3, "socket", POWER, None, lambda: female(_iec_inlet(26, 15, 2, 5))),
    ("IEC C6 inlet (cloverleaf, male)", 3, "plug", POWER, None, _iec_c6),
    ("IEC C5 outlet (cloverleaf, female)", 3, "socket", POWER, None, lambda: female(_iec_c6())),
    ("IEC C8 inlet (figure-8, male)", 2, "plug", POWER, None, _iec_c8),
    ("IEC C7 outlet (figure-8, female)", 2, "socket", POWER, None, lambda: female(_iec_c8())),
    ("Schuko CEE 7/4 plug", 3, "plug", POWER, None, _schuko),
    ("Europlug CEE 7/16", 2, "plug", POWER, None, _europlug),
    ("UK BS 1363 plug", 3, "plug", POWER, None, _uk_plug),
    ("Australia / NZ AS 3112 plug", 3, "plug", POWER, None, _au_plug),
    ("Neutrik powerCON (3 pole), plug", 3, "plug", "audio_video", None, lambda: _powercon("P")),
    ("Neutrik powerCON (3 pole), socket", 3, "socket", "audio_video", None, lambda: _powercon("O")),
    ("Socapex 19-pin lighting multicore, male", 19, "plug", "audio_video", None, lambda: _socapex("P")),
    ("Socapex 19-pin lighting multicore, female", 19, "socket", "audio_video", None, lambda: _socapex("O")),
    ("Neutrik speakON 4 pole, plug", 4, "plug", "audio_video", None, lambda: _speakon("P")),
    ("Neutrik speakON 4 pole, socket", 4, "socket", "audio_video", None, lambda: _speakon("O")),
]
