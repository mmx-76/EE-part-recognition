# EE Part Recognition

Identify an electrical connector by drawing its mating face.

Electrical connectors come in a huge range of shapes, and they are often impossible to identify
by searching online. This app lets you sketch the face of a connector on a grid (housing, metal
shell, pins, sockets, keying features, empty space), add a few details such as pin count and
plug/socket, and then shows the closest matches from a database of known connectors, ranked by
similarity.

## Status

Phase 0 (setup and scope). No app code yet. See [PROJECT_NOTES.md](PROJECT_NOTES.md) for the
scope, decisions, roadmap and next step.

## Planned tech

- Python + Flask (a small local web server)
- A browser page with a paintable grid canvas
- SQLite database of connectors (a single file, no server to install)

## Running it

Not runnable yet. Instructions will be added once the first version exists.
