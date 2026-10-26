# Trellis internal memory

`memory/` is Trellis-owned procedural memory. It keeps small, durable notes that help future sessions maintain the harness without bloating `CLAUDE.md`, task packs, or generated state.

## What belongs here

Use `memory/` for reusable operating knowledge that is not a finding, decision, run, or active task contract:

- task-pack authoring patterns that should shape future packs,
- harness-maintenance conventions that prevent drift,
- OSS-release safety notes that future contributors should remember,
- session-continuity routing between godfile, blueprint, and durable memory,
- short checklists that are stable across sessions.

## What does not belong here

Do not store secrets, credentials, private user data, raw Claude transcripts, hidden reasoning, chain-of-thought, generated outputs, large logs, temporary scratch notes, or project-specific application state.

Use the more specific Trellis surface instead:

- empirical observations with evidence -> `trellis-docs/trellis-findings.md`,
- architectural choices -> `trellis-docs/trellis-decisions.md`,
- experiment or verification run rows -> `trellis-docs/trellis-runs.md`,
- executable work contracts -> root-level `task-packs/TP-*.md`,
- short session continuity -> `.claude/blueprints/*.json` via `tools/trellis_blueprint.py`.

## Layout

Each topic gets a subfolder with a `README.md`. Keep entries short, reviewed, and written for future maintainers.

```text
memory/
  task-pack-authoring/   durable task-pack writing patterns
  harness-maintenance/   Trellis source maintenance conventions
  oss-release/           public-release safety notes
  session-continuity/    where durable vs session-local state belongs
```

## Validation

After changing Trellis memory, run:

```powershell
python tools/trellis_memory_lint.py
python tools/trellis_refs.py
python tools/trellis_reflect.py --check
```

`tools/trellis_memory_lint.py` validates only a memory directory marked with `memory/.trellis-memory`. An unmarked root `memory/` directory is host-owned and skipped by Trellis checks.

## Safety contract

- Treat this directory as public OSS content.
- Prefer stable procedures over session narrative.
- Link to source files instead of copying long content.
- Do not create ad hoc scratch files; use a task pack or blueprint record instead.
- Keep topic folders low-cardinality. Add a folder only when several future sessions will benefit.
- Preserve `memory/.trellis-memory` as a regular in-repo file; without it, or if it is a symlink, Trellis tools treat root `memory/` as host-owned or invalid.
