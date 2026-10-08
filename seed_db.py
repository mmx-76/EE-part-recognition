"""Load the starter connectors into the database.

Run it with:   py seed_db.py
It is safe to run again: connectors whose name already exists are skipped, so it never
creates duplicates and never overwrites changes you made in the app.
"""
import os

import db
import seed_data

DEFAULT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "connectors.db")


def load_starter_connectors(path):
    """Add any starter connector that is not already saved. Returns (added, skipped)."""
    db.init_db(path)
    existing = {connector["name"] for connector in db.list_connectors(path)}
    added = skipped = 0
    for name, pins, gender, industry, rows in seed_data.starter_rows():
        if name in existing:
            skipped += 1
            continue
        db.add_connector(path, name, pins, gender, industry, rows, reviewed=False)
        added += 1
    return added, skipped


if __name__ == "__main__":
    added, skipped = load_starter_connectors(DEFAULT_PATH)
    print("Added %d starter connectors (%d already there)." % (added, skipped))
