"""All reading and writing of the connector database (a single SQLite file)."""
import sqlite3

GRID_SIZE = 32
CELL_CODES = ".HSPOK"  # empty, housing, shell, pin, socket, key
GENDERS = ["unknown", "plug", "socket"]
INDUSTRIES = ["unknown", "automotive", "audio_video", "computing", "networking",
              "industrial", "aerospace", "mains_power", "medical", "other"]

SCHEMA = """
CREATE TABLE IF NOT EXISTS connectors (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL,
    pins       INTEGER,               -- NULL means unknown
    gender     TEXT NOT NULL,         -- plug / socket / unknown
    industry   TEXT NOT NULL,
    grid       TEXT NOT NULL,         -- 32 lines of 32 letters, joined with newlines
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    reviewed   INTEGER NOT NULL DEFAULT 1, -- 0 = starter draft nobody has checked yet
    size_mm    REAL                        -- longest side of the mating face; NULL means unknown
);
"""


class InvalidConnector(ValueError):
    """Raised when a connector's data is not acceptable."""


def connect(path):
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row  # lets us read columns by name
    return connection


def centre_rows(rows):
    """Move a drawing (without resizing it) so it sits in the middle of the grid.

    Every saved connector goes through this, so thumbnails and loaded drawings are always
    centred, wherever on the canvas the original was drawn."""
    drawn = [(r, c) for r, row in enumerate(rows) for c, ch in enumerate(row) if ch != "."]
    if not drawn:
        return list(rows)
    top = min(r for r, _ in drawn)
    bottom = max(r for r, _ in drawn)
    left = min(c for _, c in drawn)
    right = max(c for _, c in drawn)
    move_down = (GRID_SIZE - (bottom - top + 1)) // 2 - top
    move_right = (GRID_SIZE - (right - left + 1)) // 2 - left
    result = [["."] * GRID_SIZE for _ in range(GRID_SIZE)]
    for r, c in drawn:
        result[r + move_down][c + move_right] = rows[r][c]
    return ["".join(row) for row in result]


def _columns(connection):
    return {row["name"] for row in connection.execute("PRAGMA table_info(connectors)")}


def init_db(path):
    """Create the table if it doesn't exist yet, and bring an older database up to date.

    Safe to call every time the app starts."""
    with connect(path) as connection:
        connection.executescript(SCHEMA)
        if "reviewed" not in _columns(connection):
            # Database made before the "checked" flag existed: add it, and mark every
            # starter connector that nobody has edited as an unchecked draft.
            connection.execute("ALTER TABLE connectors ADD COLUMN reviewed INTEGER NOT NULL DEFAULT 1")
            _flag_untouched_starters(connection)
        if "size_mm" not in _columns(connection):
            connection.execute("ALTER TABLE connectors ADD COLUMN size_mm REAL")
        for row in connection.execute("SELECT id, grid FROM connectors").fetchall():
            current = row["grid"].split("\n")
            centred = centre_rows(current)
            if centred != current:
                connection.execute("UPDATE connectors SET grid = ? WHERE id = ?",
                                   ("\n".join(centred), row["id"]))


def _flag_untouched_starters(connection):
    import seed_data  # imported here because seed_data is only needed for this one-off step
    untouched = {name: "\n".join(centre_rows(rows))
                 for name, _pins, _gender, _industry, rows in seed_data.starter_rows()}
    for old_name, new_name in seed_data.RENAMED_STARTERS.items():
        untouched[old_name] = untouched[new_name]
    for row in connection.execute("SELECT id, name, grid FROM connectors").fetchall():
        grid = "\n".join(centre_rows(row["grid"].split("\n")))
        if untouched.get(row["name"]) == grid:
            connection.execute("UPDATE connectors SET reviewed = 0 WHERE id = ?", (row["id"],))


def validate_rows(rows):
    """Check a drawing is 32 rows of 32 valid letters and not completely empty."""
    if not isinstance(rows, list) or len(rows) != GRID_SIZE:
        raise InvalidConnector("The drawing must have %d rows." % GRID_SIZE)
    for row in rows:
        if not isinstance(row, str) or len(row) != GRID_SIZE or any(c not in CELL_CODES for c in row):
            raise InvalidConnector("Each drawing row must be %d valid letters." % GRID_SIZE)
    if all(c == "." for row in rows for c in row):
        raise InvalidConnector("The drawing is empty. Draw the connector first.")


def validate_size(size_mm):
    if size_mm is not None:
        if isinstance(size_mm, bool) or not isinstance(size_mm, (int, float)) or not 0.5 <= size_mm <= 500:
            raise InvalidConnector("Size must be a number of millimetres from 0.5 to 500, or blank.")


def validate_pins_and_gender(pins, gender):
    if pins is not None:
        if not isinstance(pins, int) or isinstance(pins, bool) or not 1 <= pins <= 500:
            raise InvalidConnector("Pin count must be a whole number from 1 to 500, or blank.")
    if gender not in GENDERS:
        raise InvalidConnector("Unknown plug/socket value.")


def validate(name, pins, gender, industry, rows):
    """Return cleaned-up values, or raise InvalidConnector with a plain-English reason."""
    name = (name or "").strip()
    if not name:
        raise InvalidConnector("Please give the connector a name.")
    if len(name) > 100:
        raise InvalidConnector("The name is too long (100 characters max).")
    validate_pins_and_gender(pins, gender)
    if industry not in INDUSTRIES:
        raise InvalidConnector("Unknown industry value.")
    validate_rows(rows)
    return name, pins, gender, industry


def _check_name_is_free(connection, name, ignore_id=None):
    for row in connection.execute("SELECT id FROM connectors WHERE lower(name) = lower(?)", (name,)):
        if row["id"] != ignore_id:
            raise InvalidConnector(
                "A connector called '%s' already exists. Pick a different name, or load it and "
                "use 'Save changes'." % name)


def add_connector(path, name, pins, gender, industry, rows, reviewed=True, size_mm=None):
    """Save a new connector and return its id. Starter drafts are saved with reviewed=False."""
    name, pins, gender, industry = validate(name, pins, gender, industry, rows)
    validate_size(size_mm)
    with connect(path) as connection:
        _check_name_is_free(connection, name)
        cursor = connection.execute(
            "INSERT INTO connectors (name, pins, gender, industry, grid, reviewed, size_mm)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (name, pins, gender, industry, "\n".join(centre_rows(rows)), 1 if reviewed else 0, size_mm),
        )
        return cursor.lastrowid


def update_connector(path, connector_id, name, pins, gender, industry, rows, size_mm=None):
    """Replace a connector's name, details and drawing. Saving your own edit counts as having
    checked it. Returns False if there is no such connector."""
    name, pins, gender, industry = validate(name, pins, gender, industry, rows)
    validate_size(size_mm)
    with connect(path) as connection:
        if not connection.execute("SELECT 1 FROM connectors WHERE id = ?", (connector_id,)).fetchone():
            return False
        _check_name_is_free(connection, name, ignore_id=connector_id)
        connection.execute(
            "UPDATE connectors SET name = ?, pins = ?, gender = ?, industry = ?, grid = ?, reviewed = 1,"
            " size_mm = ? WHERE id = ?",
            (name, pins, gender, industry, "\n".join(centre_rows(rows)), size_mm, connector_id),
        )
        return True


def fill_in_size_if_missing(path, name, size_mm):
    """Used by the starter loader: give an existing connector a size only if it has none."""
    with connect(path) as connection:
        connection.execute("UPDATE connectors SET size_mm = ? WHERE name = ? AND size_mm IS NULL",
                           (size_mm, name))


def rename_connector(path, old_name, new_name):
    """Used by the starter loader when a starter connector is renamed. Does nothing if the old
    name is missing or the new name is taken."""
    with connect(path) as connection:
        taken = connection.execute("SELECT 1 FROM connectors WHERE lower(name) = lower(?)",
                                   (new_name,)).fetchone()
        if not taken:
            connection.execute("UPDATE connectors SET name = ? WHERE name = ?", (new_name, old_name))


def set_reviewed(path, connector_id, reviewed):
    """Tick or untick a connector as checked. Returns False if there is no such connector."""
    with connect(path) as connection:
        cursor = connection.execute("UPDATE connectors SET reviewed = ? WHERE id = ?",
                                    (1 if reviewed else 0, connector_id))
        return cursor.rowcount > 0


def _to_dict(row, include_rows):
    result = {"id": row["id"], "name": row["name"], "pins": row["pins"],
              "gender": row["gender"], "industry": row["industry"], "reviewed": bool(row["reviewed"]),
              "size_mm": row["size_mm"]}
    if include_rows:
        result["rows"] = row["grid"].split("\n")
    return result


def list_connectors(path, include_rows=False):
    """Every connector. By default without the drawing, so the list stays small and fast."""
    with connect(path) as connection:
        rows = connection.execute("SELECT * FROM connectors ORDER BY name COLLATE NOCASE").fetchall()
    return [_to_dict(r, include_rows=include_rows) for r in rows]


def get_connector(path, connector_id):
    """One connector including its drawing, or None if it doesn't exist."""
    with connect(path) as connection:
        row = connection.execute("SELECT * FROM connectors WHERE id = ?", (connector_id,)).fetchone()
    return _to_dict(row, include_rows=True) if row else None


def delete_connector(path, connector_id):
    """Delete a connector. Returns True if something was deleted."""
    with connect(path) as connection:
        cursor = connection.execute("DELETE FROM connectors WHERE id = ?", (connector_id,))
        return cursor.rowcount > 0
