"""Load the starter connectors into the database.

Run it with:   py seed_db.py
It is safe to run again: connectors whose name already exists are skipped, so it never
creates duplicates and never overwrites changes you made in the app. (It only fills in a size
for an existing starter connector that has none, and applies renames of starter connectors.)
"""
import os

import db
import seed_data

DEFAULT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "connectors.db")


def load_starter_connectors(path):
    """Add any starter connector that is not already saved. Returns (added, skipped)."""
    db.init_db(path)
    for old_name, new_name in seed_data.RENAMED_STARTERS.items():
        db.rename_connector(path, old_name, new_name)
    existing = {connector["name"] for connector in db.list_connectors(path)}
    added = skipped = 0
    for name, pins, gender, industry, rows in seed_data.starter_rows():
        size = seed_data.STARTER_SIZES.get(name)
        if name in existing:
            db.fill_in_size_if_missing(path, name, size)
            skipped += 1
            continue
        db.add_connector(path, name, pins, gender, industry, rows, reviewed=False, size_mm=size)
        added += 1
    return added, skipped


if __name__ == "__main__":
    added, skipped = load_starter_connectors(DEFAULT_PATH)
    print("Added %d starter connectors (%d already there)." % (added, skipped))
