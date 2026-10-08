"""RF coaxial connectors.

Approximate drawings, made from general knowledge. At this level of detail many RF families look
alike (a ring with a centre contact); they are separated mainly by size, the coupling style
(nut, bayonet, snap-on) and the centre contact (pin or socket). Check them against real parts.

Naming: "male" = the centre contact is a pin, "female" = the centre contact is a socket.
Each entry: (name, pins, plug or socket, industry, size in mm or None if unsure, drawing function)
"""
from drawing_tools import Canvas

D = 17          # diameter of the drawn ring, in cells
ORIGIN = 2      # leaves room outside the ring for bayonet lugs


def _coax(style, centre, blob=1):
    """A concentric RF connector face. styles: hex (hex coupling nut), thread (round nut),
    bayonet (BNC-style lugs), snap (snap-on / push-on), micro (tiny snap-on)."""
    c = Canvas()
    o, middle = ORIGIN, ORIGIN + D // 2
    c.shape("rounded" if style == "hex" else "oval", o, o, D, D, "S")
    if style in ("hex", "thread"):
        c.shape("oval", o + 2, o + 2, D - 4, D - 4, "S")
        c.shape("oval", o + 5, o + 5, D - 10, D - 10, "H")
    elif style == "bayonet":
        c.shape("oval", o + 3, o + 3, D - 6, D - 6, "H")
        for row in (middle - 1, middle):
            c.put(row, o - 1, "K")
            c.put(row, o + D, "K")
    elif style == "snap":
        c.shape("oval", o + 4, o + 4, D - 8, D - 8, "H")
    c.contact_at(middle, middle, blob, centre)
    return c.rows()


def _fakra(centre):
    """FAKRA: a keyed rectangular plastic body around a small coax connector."""
    c = Canvas()
    c.shape("rounded", 2, 2, 16, 18, "H")
    c.shape("oval", 5, 5, 10, 12, "S")
    c.blob(2, 4, 3, 4, "K")          # the colour-coded key
    c.contact_at(10, 11, 1, centre)
    return c.rows()


# name, style, blob size, size mm, industry
_FAMILIES = [
    ("SMA", "hex", 1, 6.4, "rf_microwave"),
    ("TNC", "thread", 1, 11, "rf_microwave"),
    ("N-type", "thread", 3, 20, "rf_microwave"),
    ("7/16 DIN", "thread", 3, 29, "rf_microwave"),
    ("4.3-10", "thread", 3, None, "rf_microwave"),
    ("2.92 mm (K)", "hex", 1, 6.4, "rf_microwave"),
    ("3.5 mm precision", "hex", 1, 6.4, "rf_microwave"),
    ("F-type", "thread", 1, 11, "audio_video"),
    ("UHF (PL-259 / SO-239)", "thread", 3, 17, "rf_microwave"),
    ("SMB", "snap", 1, None, "rf_microwave"),
    ("SMC", "thread", 1, None, "rf_microwave"),
    ("MCX", "snap", 1, None, "rf_microwave"),
    ("MMCX", "micro", 1, None, "rf_microwave"),
    ("QMA", "snap", 1, None, "rf_microwave"),
]

CONNECTORS = []
for _name, _style, _blob, _size, _industry in _FAMILIES:
    CONNECTORS.append(("RF %s, centre pin (male)" % _name, 1, "plug", _industry, _size,
                       lambda s=_style, b=_blob: _coax(s, "P", b)))
    CONNECTORS.append(("RF %s, centre socket (female)" % _name, 1, "socket", _industry, _size,
                       lambda s=_style, b=_blob: _coax(s, "O", b)))

CONNECTORS += [
    ("RF BNC, centre socket (female)", 1, "socket", "rf_microwave", 10, lambda: _coax("bayonet", "O")),
    ("RF RP-SMA, centre socket in the nut (reverse polarity male)", 1, "plug", "networking", 6.4,
     lambda: _coax("hex", "O")),
    ("RF RP-SMA, centre pin in the thread (reverse polarity female)", 1, "socket", "networking", 6.4,
     lambda: _coax("thread", "P")),
    ("RF U.FL / IPEX, cable plug (centre socket)", 1, "plug", "networking", None, lambda: _coax("micro", "O")),
    ("RF U.FL / IPEX, board receptacle (centre pin)", 1, "socket", "networking", None, lambda: _coax("micro", "P")),
    ("RF FAKRA, centre pin", 1, "plug", "automotive", 14, lambda: _fakra("P")),
    ("RF FAKRA, centre socket", 1, "socket", "automotive", 14, lambda: _fakra("O")),
]
