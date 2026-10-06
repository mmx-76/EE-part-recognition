# PROJECT_NOTES

Paste this file into a new chat (or let Claude read it from the repo) to pick up where we left off.

## Working agreement

- Owner (Max) decides features, looks, behaviour and priorities.
- Claude is technical lead and teacher: makes technical decisions, writes code, explains in plain
  English, one small step at a time, waits for confirmation before moving on.
- Commit after each working step. Push back on scope creep. Keep this file updated every session.
- Max: Windows PC, VS Code, Git, GitHub account, comfortable with Python (but loses track of 3D
  arrays, so keep data structures simple and well named). 3-6 hours/week.
- Max uses PowerShell in the VS Code terminal (not Command Prompt).

## Project summary

An app where a user paints a connector's mating face on a grid (housing, shell, pin, socket, key,
empty), enters details (pin count, plug/socket, later industry), and gets a ranked list of the
closest matches from a database of known connectors, with a similarity score.

## Scope

### MVP (version 1)
- Grid canvas (32x32) where you paint cells with a selected element type.
- Element types: housing, metal shell, pin, socket, key feature, empty.
- Details: pin count, plug or socket.
- Search button -> top 5 matches from the database, each with a similarity score.
- Database of about 20-30 common connectors, created by Claude from simple descriptions and
  corrected by Max.
- "Add to database" button so the database can grow.

### Not in MVP (later)
- Advanced search page (industry filter, weighting drawing vs details)
- Freehand drawing converted to a grid
- Photo upload / image matching
- Large-scale data import, user accounts, hosting online

## Decisions made (and why)

| Decision | Why |
|---|---|
| Drawing stored as a flat 32x32 grid, one label per cell | Searchable and comparable; raw pixels break when drawings shift or scale |
| Matching compares extracted features (outline, pin count/positions, keying), not pixels | Tolerates sloppy drawing |
| Grid painting (not freehand) for v1 | Simplest; maps directly to stored data |
| Starting database built by Claude (~20-30 connectors), grown via "Add" button | No clean free source exists; scraping is slow and legally grey |
| Python + Flask | Max already knows Python; Flask is the smallest web framework |
| SQLite | One file, nothing to install, plenty for this size |
| Shape stamps are shortcuts that paint cells (drag-to-size) | Stored data stays the same flat grid; full connector templates belong to the database, not the canvas |
| Plain HTML/JavaScript canvas, no front-end framework | Fewer moving parts for a beginner |

## Hard problems (raised early)

1. Storing drawings so they can be compared -> grid + extracted features (above).
2. Source of connector data -> hand-built seed set, then user-contributed.
3. Matching quality will need tuning against real examples; expect iteration.

## Roadmap

- Phase 0: Setup and scope (in progress)
- Milestone 1 (MVP): project skeleton -> paintable grid -> database + seed data -> feature
  extraction -> similarity search + ranked results -> add-to-database
- Milestone 2: advanced search (industry, weighting), better scoring, bigger database
- Milestone 3: freehand drawing, photo input, polish, possible online hosting

## Done

- GitHub repo created; cloned to Max's PC at `C:\Users\Max.Moir\EE-part-recognition`.
- Scope and MVP agreed (grid painting, seed database, similarity ranking).
- README.md and PROJECT_NOTES.md created.
- Python 3.13 works via `py`; venv `.venv` created; Flask installed; hello-world page ran.
- Paintable 32x32 grid page (templates/index.html) with 6 element types, drag painting,
  per-element cell counts, Clear button.
- Shape stamps (drag-to-size box): rectangle, rounded rectangle, circle/oval, D-shape,
  trapezoid, with a Filled/outline toggle. Buttons renamed "Plastic housing" / "Metal shell".

## Git notes

- Claude commits on branch `claude/connector-identification-app-dljcow`.
- Max's local clone is on `main` and has no commits yet.

## Next step

Max pulls the latest code (`git pull`), refreshes the page, tries the shape stamps and reports
what feels wrong or missing (e.g. D-shape orientation, extra shapes). Then:
1. Pin-pattern stamps (row of N, grid, ring of N) - if Max wants them.
2. Details form (pin count, plug/socket) beside the grid.
