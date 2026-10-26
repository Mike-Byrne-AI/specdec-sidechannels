# TP-0_example

## Goal
Demonstrate the canonical Trellis task-pack format with a small hypothetical utility change.

## Why this matters
New contributors and agents need a complete reference that the strict linter accepts. This example is illustrative only and is never active work.

## Out of scope
- No real source-code change is required by this example.
- No new dependencies, network calls, or build-system changes.
- No changes outside the hypothetical `src/utils.py` and `tests/test_utils.py` files.

## Files touched
- `src/utils.py` - hypothetical `add_metadata()` helper.
- `tests/test_utils.py` - hypothetical regression tests.

## Risk level
Low. The example is inactive documentation under `task-packs/examples/` and is not executed as real work.

## Dependencies
- `trellis-docs/trellis-task-pack-goldprint.md` for the canonical section order.
- `tools/trellis_pack_lint.py` for validation behavior.

## Proof gate
```powershell
python -m pytest -q tests/test_utils.py
python tools/trellis_pack_lint.py task-packs/examples/TP-0_example.md
```

## Sub-tasks
1. Add `add_metadata(data: dict, meta: dict) -> dict` to `src/utils.py`, returning a shallow copy with metadata under `__meta__` without mutating inputs.
2. Add tests covering basic metadata merge, input immutability, merging existing `__meta__`, and empty metadata behavior.
3. Run the proof gate and keep the example inactive under `task-packs/examples/`.

## Final acceptance
- The hypothetical helper behavior is described precisely enough to implement.
- The hypothetical tests cover at least four observable behaviors.
- The pack contains every strict required section.
- The example remains under `task-packs/examples/` and is not treated as active work.

## Stop conditions
- Stop if this file is moved to the root active task-pack queue.
- Stop if making the example pass requires weakening active-pack validation.
- Stop if the example starts describing real work that should be a TP-1 or higher pack.
