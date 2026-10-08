# EE Part Recognition

Identify an electrical connector by drawing its mating face.

Electrical connectors come in a huge range of shapes, and they are often impossible to identify
by searching online. This app lets you sketch the face of a connector on a grid (housing, metal
shell, pins, sockets, keying features, empty space), add a few details such as pin count and
plug/socket, and then shows the closest matches from a database of known connectors, ranked by
similarity.

## Status

Milestone 1 is done and Milestone 2 has started: draw a connector (shapes, pin patterns, eraser), add what you know (pins, plug/socket, size, industry), and get a ranked, scored top matches from a database of 192 starter connectors (D-subs, Harting Han, RF coax, comms, fibre, heavy power and more) that you can correct and grow, with automatic daily backups. Advanced search lets you require, prefer or ignore each detail. Works with touch on a phone-sized screen. See [PROJECT_NOTES.md](PROJECT_NOTES.md) for the
scope, decisions, roadmap and next step.

## Planned tech

- Python + Flask (a small local web server)
- A browser page with a paintable grid canvas
- SQLite database of connectors (a single file, no server to install)

## Running it (Windows PowerShell)

```
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
py app.py
```

Load the starter connectors once (safe to repeat, never makes duplicates):

```
py seed_db.py
```

Then open http://127.0.0.1:5000. Run the tests with `py -m unittest discover tests`.
