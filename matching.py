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
6. Apply the details as GUARDS: if both sides know the pin count, plug/socket, size or industry
   and they disagree, the score is multiplied down. Agreeing details never add points to a poor
   shape. The advanced search can ignore a detail, or require it (dropping connectors that
   disagree).

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
SIZE_FLOOR = 0.3             # a hopelessly wrong size keeps 30%
INDUSTRY_MISMATCH_FACTOR = 0.85  # industries are fuzzy, so this is only a gentle nudge

# Sizes are measured by eye or ruler, so be forgiving: within about 15% counts as the same size,
# and below 40% of the other size counts as completely different.
SIZE_SAME_RATIO = 0.85
SIZE_DIFFERENT_RATIO = 0.4

# "other" and "unknown" say nothing useful about the industry, so they never count for or against.
NEUTRAL_INDUSTRIES = ("unknown", "other")

# How strictly each detail is applied (the advanced search lets the user change these):
#   ignore  - don't use it at all      prefer - lower the score when it disagrees (the default)
#   require - drop connectors whose known value disagrees (unknown values are given the benefit of the doubt)
MODES = ("ignore", "prefer", "require")
DETAILS = ("pins", "gender", "size", "industry")

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


def size_score(a, b):
    """1.0 when sizes agree to within about 15%, falling to 0.0 when one is under 40% of the other."""
    ratio = min(a, b) / max(a, b)
    return min(1.0, max(0.0, (ratio - SIZE_DIFFERENT_RATIO) / (SIZE_SAME_RATIO - SIZE_DIFFERENT_RATIO)))


def combine(raw_drawing, query, other, modes=None):
    """Turn the raw drawing similarity and the details into the final score and its breakdown.

    `query` and `other` are dicts with pins, gender, size_mm and industry (None / "unknown" when
    not known). `modes` says how strictly to apply each detail (see MODES)."""
    modes = dict({name: "prefer" for name in DETAILS}, **(modes or {}))
    shape = calibrate(raw_drawing)
    score = shape
    excluded = False
    parts = {"pins": None, "gender": None, "size": None, "industry": None}

    if modes["pins"] != "ignore" and query.get("pins") is not None and other.get("pins") is not None:
        parts["pins"] = pin_count_score(query["pins"], other["pins"])
        excluded |= modes["pins"] == "require" and query["pins"] != other["pins"]
        score *= PIN_COUNT_FLOOR + (1 - PIN_COUNT_FLOOR) * parts["pins"]

    if modes["gender"] != "ignore" and "unknown" not in (query.get("gender"), other.get("gender")):
        parts["gender"] = 1.0 if query["gender"] == other["gender"] else 0.0
        excluded |= modes["gender"] == "require" and parts["gender"] == 0.0
        score *= 1.0 if parts["gender"] else GENDER_MISMATCH_FACTOR

    if modes["size"] != "ignore" and query.get("size_mm") is not None and other.get("size_mm") is not None:
        parts["size"] = size_score(query["size_mm"], other["size_mm"])
        ratio = min(query["size_mm"], other["size_mm"]) / max(query["size_mm"], other["size_mm"])
        excluded |= modes["size"] == "require" and ratio < SIZE_SAME_RATIO
        score *= SIZE_FLOOR + (1 - SIZE_FLOOR) * parts["size"]

    if (modes["industry"] != "ignore" and query.get("industry") not in NEUTRAL_INDUSTRIES
            and other.get("industry") not in NEUTRAL_INDUSTRIES):
        parts["industry"] = 1.0 if query["industry"] == other["industry"] else 0.0
        excluded |= modes["industry"] == "require" and parts["industry"] == 0.0
        score *= 1.0 if parts["industry"] else INDUSTRY_MISMATCH_FACTOR

    return {"score": score, "drawing_score": shape, "pin_score": parts["pins"],
            "gender_score": parts["gender"], "size_score": parts["size"],
            "industry_score": parts["industry"], "excluded": excluded}


_prepared_cache = {}  # drawing (as a tuple of rows) -> prepared layers; saves redoing the maths


def _prepare_cached(rows):
    key = tuple(rows)
    if key not in _prepared_cache:
        if len(_prepared_cache) > 5000:  # never let it grow without limit
            _prepared_cache.clear()
        _prepared_cache[key] = prepare(rows)
    return _prepared_cache[key]


def warm_cache(path):
    """Prepare every saved drawing now, so the first search after the app starts is as fast as the rest."""
    for connector in db.list_connectors(path, include_rows=True):
        _prepare_cached(connector["rows"])


def search(path, rows, details=None, modes=None, limit=5, only_checked=False):
    """Rank saved connectors against the query. Best match first.

    details: what the user knows (pins, gender, size_mm, industry); modes: how strictly to apply
    each (see MODES); only_checked: leave out unchecked starter drafts."""
    query = prepare(rows)
    if query is None:
        raise db.InvalidConnector("The drawing is empty. Draw the connector first.")
    details = dict({"pins": None, "gender": "unknown", "size_mm": None, "industry": "unknown"},
                   **(details or {}))
    results = []
    for full in db.list_connectors(path, include_rows=True):
        if only_checked and not full["reviewed"]:
            continue
        candidate = _prepare_cached(full["rows"])
        if candidate is None:
            continue
        breakdown = combine(drawing_score(query, candidate), details, full, modes)
        if breakdown.pop("excluded"):
            continue
        full.update(breakdown)
        results.append(full)
    results.sort(key=lambda item: item["score"], reverse=True)
    return results[:limit]
