# TP-0_goldprint_multi_phase

## Goal
Add a new command plus its supporting local script and tests.

## Why this matters
Commands are useful only when their documented workflow, deterministic helper, and tests agree.

## Out of scope
- No command alias proliferation.
- No hook enforcement unless a later pack justifies it.
- No generated docs beyond the command file.

## Files touched
- `.claude/commands/example.md` - command protocol.
- `tools/example.py` - deterministic helper.
- `tests/test_example.py` - helper and docs tests.
- `tools/trellis_inventory.py` - expected command count if needed.

## Risk level
Medium. This changes the visible Claude Code surface.

## Dependencies
- Existing command style in `.claude/commands/pack.md`.
- Existing gate style in `tools/trellis_repair_gate.py`.

## Proof gate
```powershell
python -m pytest -q tests/test_example.py tests/test_trellis_inventory.py
python tools/trellis_inventory.py --check
python tools/trellis_repair_gate.py
```

## Sub-tasks
1. Add the deterministic helper and tests.
2. Add the command protocol.
3. Update inventory and docs.
4. Run targeted and full proof.

## Final acceptance
- The new command references a real script.
- The helper has tests for success and failure.
- Inventory counts match.
- The full local gate passes.

## Stop conditions
- Stop if the command needs another command to be renamed.
- Stop if the helper requires network, CI, database, or daemon behavior.
- Stop if the full local gate fails after targeted tests pass.
