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
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


class InvalidConnector(ValueError):
    """Raised when a connector's data is not acceptable."""


def connect(path):
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row  # lets us read columns by name
    return connection


def init_db(path):
    """Create the table if it doesn't exist yet. Safe to call every time the app starts."""
    with connect(path) as connection:
        connection.executescript(SCHEMA)


def validate_rows(rows):
    """Check a drawing is 32 rows of 32 valid letters and not completely empty."""
    if not isinstance(rows, list) or len(rows) != GRID_SIZE:
        raise InvalidConnector("The drawing must have %d rows." % GRID_SIZE)
    for row in rows:
        if not isinstance(row, str) or len(row) != GRID_SIZE or any(c not in CELL_CODES for c in row):
            raise InvalidConnector("Each drawing row must be %d valid letters." % GRID_SIZE)
    if all(c == "." for row in rows for c in row):
        raise InvalidConnector("The drawing is empty. Draw the connector first.")


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


def add_connector(path, name, pins, gender, industry, rows):
    """Save a connector and return its new id."""
    name, pins, gender, industry = validate(name, pins, gender, industry, rows)
    with connect(path) as connection:
        cursor = connection.execute(
            "INSERT INTO connectors (name, pins, gender, industry, grid) VALUES (?, ?, ?, ?, ?)",
            (name, pins, gender, industry, "\n".join(rows)),
        )
        return cursor.lastrowid


def _to_dict(row, include_rows):
    result = {"id": row["id"], "name": row["name"], "pins": row["pins"],
              "gender": row["gender"], "industry": row["industry"]}
    if include_rows:
        result["rows"] = row["grid"].split("\n")
    return result


def list_connectors(path):
    """Every connector, without the drawing (the list stays small and fast)."""
    with connect(path) as connection:
        rows = connection.execute("SELECT * FROM connectors ORDER BY name COLLATE NOCASE").fetchall()
    return [_to_dict(r, include_rows=False) for r in rows]


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
