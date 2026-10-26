---
name: task-pack-format
description: Use when reading, writing, or executing a task pack in task-packs/. Covers the TP-N naming convention, canonical required sections, active versus inactive locations, and the discipline that Final acceptance is the completion contract.
---

# Task pack format

Task packs are executable contracts for Claude Code. One pack equals one focused unit of work, sized to roughly one session.

## File location and naming

```text
task-packs/TP-N_description_in_snake_case.md
```

- Root-level active packs use `TP-1` or higher.
- `TP-0` is reserved for examples under `task-packs/examples/`.
- Inactive packs live under `task-packs/examples/`, `task-packs/archive/`, `task-packs/completed/`, or `task-packs/done/`.

## Required sections

A well-formed pack has these sections, in this order:

1. **Goal** — one paragraph stating what the pack achieves.
2. **Why this matters** — empirical, architectural, or user-value motivation.
3. **Out of scope** — explicit boundaries and deferred adjacent work.
4. **Files touched** — concrete list of files created or modified.
5. **Risk level** — low, medium, or high with one sentence explaining why.
6. **Dependencies** — prior packs, findings, decisions, files, or `None`.
7. **Proof gate** — concrete commands to run for completion.
8. **Sub-tasks** — numbered implementation phases.
9. **Final acceptance** — observable criteria for declaring the pack done.
10. **Stop conditions** — cases that require stopping or asking before continuing.

Use the heading `Proof gate`, not the old `Verification` heading.

## Canonical skeleton

````markdown
# TP-N_short_name

## Goal
...

## Why this matters
...

## Out of scope
- ...

## Files touched
- `path` - reason.

## Risk level
Low. ...

## Dependencies
- None.

## Proof gate
```powershell
python -m pytest -q tests/test_specific.py
```

## Sub-tasks
1. ...

## Final acceptance
- ...

## Stop conditions
- ...
````

## Lifecycle

1. A pack lives in root `task-packs/` while active.
2. When all acceptance criteria pass, move it to `task-packs/done/` or `task-packs/completed/` and prepend a short completed status line.
3. If a pack is stalled, add `**Status**: BLOCKED <reason>` and leave it active.
4. Active task packs are godfile sources; examples and completed packs are not.

## Executor discipline

Read the full pack first, execute sub-tasks in order unless the pack says otherwise, run proof at each meaningful boundary, and treat Final acceptance as the contract. If changed files leave `Files touched`, proof fails, or a stop condition fires, stop and report the literal issue.
