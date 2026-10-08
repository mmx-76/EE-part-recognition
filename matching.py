"""Compare a drawing (plus details) against saved connectors and rank them.

How a drawing is compared, in plain English:
1. NORMALISE: crop the drawing to the area that was actually drawn, then scale it up to fill the
   32 x 32 grid. A connector drawn small in a corner can then match one drawn big in the middle.
2. SPLIT INTO LAYERS: "body" (housing or shell), "contacts" (pins or sockets), "key", and each
   element type on its own.
3. SCORE each layer with a tolerant match: every drawn cell earns full marks if the other drawing
   has the same cell, 0.7 if one cell away, 0.35 if two away, else 0 (see TOLERANCE). This forgives
   small wobbles and rounding. It is checked both ways round, so extra cells also cost points.
4. AVERAGE the layers using LAYER_WEIGHTS. Layers empty in both drawings are skipped.
5. CALIBRATE: unrelated drawings still share some accidental overlap (about 0.25), so anything at
   or below SHAPE_FLOOR counts as 0% and an exact copy as 100%.
6. Apply the details as GUARDS: if both sides know the pin count (or plug/socket) and they
   disagree, the score is multiplied down. Agreeing details never add points to a poor shape.

Everything tunable is in the constants below.
"""
import db

SIZE = db.GRID_SIZE

# (name, letters that belong to the layer, weight). Bigger weight = matters more.
LAYERS = [
    ("body",     "HS", 4.0),   # overall outline: plastic or metal
    ("contacts", "PO", 3.0),   # where the pins/sockets are
    ("key",      "K",  2.0),   # keying features
    ("housing",  "H",  1.0),   # exact element types, for tie-breaking
    ("shell",    "S",  1.0),
    ("pin",      "P",  1.0),
    ("socket",   "O",  1.0),
]

# Raw drawing similarity at or below this counts as "nothing in common" (measured: unrelated
# connector drawings score about 0.22 on average and rarely above 0.45).
SHAPE_FLOOR = 0.25

# How much the number of drawn contacts (pins/sockets) matters, as a weight like the layers.
CONTACT_COUNT_WEIGHT = 4.0

# Details only ever lower the score. These are the lowest multipliers (all details wrong).
PIN_COUNT_FLOOR = 0.2        # a hopelessly wrong pin count keeps only 20% of the shape score
GENDER_MISMATCH_FACTOR = 0.6  # plug vs socket mix-up keeps 60%

TOLERANCE = [1.0, 0.7, 0.35]  # credit for a cell that is 0, 1 or 2 cells from one in the other drawing


def normalise(rows):
    """Crop to the drawn area and stretch it (keeping its shape) to span the whole grid.

    Each drawn cell is moved to its scaled position, and gaps between neighbouring drawn cells
    are filled in. Strokes therefore stay one cell thick however big the drawing is, which
    matters because people draw outlines one cell wide at any size.

    Returns a list of 32 strings, or None if nothing was drawn."""
    drawn = [(r, c) for r, row in enumerate(rows) for c, ch in enumerate(row) if ch != "."]
    if not drawn:
        return None
    top = min(r for r, _ in drawn)
    bottom = max(r for r, _ in drawn)
    left = min(c for _, c in drawn)
    right = max(c for _, c in drawn)
    height, width = bottom - top + 1, right - left + 1
    longest = max(height, width)
    scale = (SIZE - 1) / (longest - 1) if longest > 1 else 1.0
    offset_row = (SIZE - 1 - round((height - 1) * scale)) // 2
    offset_col = (SIZE - 1 - round((width - 1) * scale)) // 2

    def new_row(r):
        return offset_row + round((r - top) * scale)

    def new_col(c):
        return offset_col + round((c - left) * scale)

    result = [["."] * SIZE for _ in range(SIZE)]
    for r in range(top, bottom + 1):
        for c in range(left, right + 1):
            letter = rows[r][c]
            if letter == ".":
                continue
            result[new_row(r)][new_col(c)] = letter
            # Join this cell to its right and lower neighbours across any gap the scaling left.
            if c < right and rows[r][c + 1] != ".":
                for gap in range(new_col(c) + 1, new_col(c + 1)):
                    result[new_row(r)][gap] = letter
            if r < bottom and rows[r + 1][c] != ".":
                for gap in range(new_row(r) + 1, new_row(r + 1)):
                    result[gap][new_col(c)] = letter
    return ["".join(line) for line in result]


def _dilate(mask):
    """Grow a 0/1-style mask by one cell in every direction (taking the biggest value nearby)."""
    wide = [[max(row[max(0, c - 1):c + 2]) for c in range(SIZE)] for row in mask]
    return [[max(wide[rr][c] for rr in range(max(0, r - 1), min(SIZE, r + 2)))
             for c in range(SIZE)] for r in range(SIZE)]


def _layer(rows, letters):
    """Return (tolerance map, list of the layer's cells). The map says, for every grid cell,
    how much credit a cell of the OTHER drawing earns by landing there."""
    solid = [[1.0 if ch in letters else 0.0 for ch in row] for row in rows]
    cells = [(r, c) for r in range(SIZE) for c in range(SIZE) if solid[r][c]]
    if not cells:
        return None, cells
    grown_once = _dilate(solid)
    grown_twice = _dilate(grown_once)
    credit = [[max(TOLERANCE[0] * solid[r][c], TOLERANCE[1] * grown_once[r][c],
                   TOLERANCE[2] * grown_twice[r][c]) for c in range(SIZE)] for r in range(SIZE)]
    return credit, cells


def prepare(rows):
    """Do the slow part once per drawing: normalise and build every layer."""
    normal = normalise(rows)
    if normal is None:
        return None
    prepared = {name: _layer(normal, letters) for name, letters, _ in LAYERS}
    prepared["contact_total"] = sum(row.count("P") + row.count("O") for row in rows)
    return prepared


def _coverage(cells, credit):
    """Average credit that `cells` earn from the other drawing's tolerance map."""
    if not cells:
        return 0.0
    if credit is None:
        return 0.0
    return sum(credit[r][c] for r, c in cells) / len(cells)


def drawing_score(prepared_a, prepared_b):
    """0..1 similarity of two prepared drawings."""
    total, weight_sum = 0.0, 0.0
    for name, _letters, weight in LAYERS:
        credit_a, cells_a = prepared_a[name]
        credit_b, cells_b = prepared_b[name]
        if not cells_a and not cells_b:
            continue  # layer absent from both: says nothing either way
        similarity = (_coverage(cells_a, credit_b) + _coverage(cells_b, credit_a)) / 2
        total += weight * similarity
        weight_sum += weight
    contacts_a, contacts_b = prepared_a["contact_total"], prepared_b["contact_total"]
    if contacts_a or contacts_b:  # 42 drawn pins is not a match for a 24 pin connector
        total += CONTACT_COUNT_WEIGHT * (min(contacts_a, contacts_b) / max(contacts_a, contacts_b)) ** 2
        weight_sum += CONTACT_COUNT_WEIGHT
    return total / weight_sum if weight_sum else 0.0


def calibrate(raw):
    """Stretch raw similarity so 'nothing in common' reads 0 and 'identical' reads 1."""
    return max(0.0, (raw - SHAPE_FLOOR) / (1.0 - SHAPE_FLOOR))


def pin_count_score(a, b):
    """1.0 for the same count; falls away quickly (42 pins vs 24 pins scores about 0.33)."""
    return (min(a, b) / max(a, b)) ** 2


def combine(raw_drawing, query_pins, query_gender, other_pins, other_gender):
    """Turn the raw drawing similarity and the details into the final score and its breakdown."""
    shape = calibrate(raw_drawing)
    score = shape
    pin_part = gender_part = None
    if query_pins is not None and other_pins is not None:
        pin_part = pin_count_score(query_pins, other_pins)
        score *= PIN_COUNT_FLOOR + (1 - PIN_COUNT_FLOOR) * pin_part
    if query_gender != "unknown" and other_gender != "unknown":
        gender_part = 1.0 if query_gender == other_gender else 0.0
        score *= 1.0 if gender_part else GENDER_MISMATCH_FACTOR
    return {"score": score, "drawing_score": shape, "pin_score": pin_part,
            "gender_score": gender_part}


_prepared_cache = {}  # drawing (as a tuple of rows) -> prepared layers; saves redoing the maths


def _prepare_cached(rows):
    key = tuple(rows)
    if key not in _prepared_cache:
        if len(_prepared_cache) > 5000:  # never let it grow without limit
            _prepared_cache.clear()
        _prepared_cache[key] = prepare(rows)
    return _prepared_cache[key]


def search(path, rows, pins=None, gender="unknown", limit=5):
    """Rank every saved connector against the query. Best match first."""
    query = prepare(rows)
    if query is None:
        raise db.InvalidConnector("The drawing is empty. Draw the connector first.")
    results = []
    for full in db.list_connectors(path, include_rows=True):
        candidate = _prepare_cached(full["rows"])
        if candidate is None:
            continue
        breakdown = combine(drawing_score(query, candidate), pins, gender,
                            full["pins"], full["gender"])
        full.update(breakdown)
        results.append(full)
    results.sort(key=lambda item: item["score"], reverse=True)
    return results[:limit]
