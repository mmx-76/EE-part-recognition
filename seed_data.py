"""The starter connectors, drawn with code instead of by hand.

IMPORTANT: these are simplified, approximate drawings of real connector faces, made without
the manufacturers' drawings in front of me. Treat them as a first draft: load one in the app,
correct it, and save it again (or delete it) if it doesn't match the real thing.

The helpers below do the same jobs as the shape and pin-pattern buttons in the drawing page.
Letters: . empty   H plastic housing   S metal shell   P pin   O socket   K key feature
"""
from drawing_tools import Canvas, PATTERNS, SHAPE_TESTS, female, male, spread  # noqa: F401


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


# The families added later live in their own files; they join the same list here.
import seed_comms  # noqa: E402
import seed_dsub_harting  # noqa: E402
import seed_power  # noqa: E402
import seed_rf  # noqa: E402

for _module in (seed_dsub_harting, seed_rf, seed_comms, seed_power):
    for _name, _pins, _gender, _industry, _size, _build in _module.CONNECTORS:
        STARTER_CONNECTORS.append((_name, _pins, _gender, _industry, _build))
        if _size is not None:
            STARTER_SIZES[_name] = _size


def starter_rows():
    """Yield (name, pins, gender, industry, rows) for every starter connector."""
    for name, pins, gender, industry, build in STARTER_CONNECTORS:
        yield name, pins, gender, industry, build()
