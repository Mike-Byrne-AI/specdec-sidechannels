# Task pack goldprint

A Trellis task pack is an executable contract. It should be short enough to use in one work session and precise enough that `/implement-pack` can turn it into a phase plan.

## Required shape

```markdown
# TP-N_short_name

## Goal
One sentence describing the user-visible outcome.

## Why this matters
One paragraph explaining the value and what breaks without it.

## Out of scope
Bullets naming adjacent work that must not be done in this pack.

## Files touched
- `path/to/file.py` - why it changes
- `tests/test_file.py` - proof for the change

## Risk level
Low | Medium | High, with one sentence explaining why.

## Dependencies
- Existing file, decision, finding, or prior TP dependency
- `None` if there are no dependencies

## Proof gate
```powershell
python -m pytest -q tests/test_specific.py
python tools/trellis_refs.py
```

## Sub-tasks
1. First phase with expected files and proof.
2. Second phase with expected files and proof.

## Final acceptance
- Concrete observable acceptance item.
- Every command in Proof gate passes.
- No active task-pack or reference drift remains.

## Stop conditions
- Stop if targeted proof fails.
- Stop if changed files leave Files touched scope.
- Stop if acceptance cannot be verified.
```

## Good pack rules

- State the exact files expected to change.
- Give one targeted proof command whenever possible.
- Name what is out of scope.
- Use `STOP`, `OPERATOR REQUIRED`, `DO NOT AUTO-EXECUTE`, or `MANUAL STEP` only when the pack truly requires human intervention.
- Keep examples under `task-packs/examples/` so they are never active work.

## Lint command

```powershell
python tools/trellis_pack_lint.py task-packs/TP-N_short_name.md
```

The linter checks required sections, concrete proof commands, and placeholder leakage.
