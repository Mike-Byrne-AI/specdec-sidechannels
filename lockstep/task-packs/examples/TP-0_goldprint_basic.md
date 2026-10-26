# TP-0_goldprint_basic

## Goal
Add one small deterministic checker to the harness.

## Why this matters
Small local checkers are the safest Trellis extension shape because they are testable, cross-platform, and easy to explain.

## Out of scope
- No new agent.
- No new remote service.
- No broad refactor.

## Files touched
- `tools/example_checker.py` - new checker script.
- `tests/test_example_checker.py` - regression tests.
- `README.md` - one-line command reference.

## Risk level
Low. The change is additive and local.

## Dependencies
- `tools/trellis_paths.py` for project-root detection.

## Proof gate
```powershell
python -m pytest -q tests/test_example_checker.py
python tools/example_checker.py
```

## Sub-tasks
1. Add the checker script and unit tests.
2. Wire the checker into docs.
3. Run the proof gate.

## Final acceptance
- The checker exits 0 on a healthy repo.
- The regression test fails on the intended broken case.
- The README command is accurate.

## Stop conditions
- Stop if the checker needs network access.
- Stop if the proof gate requires a project-specific dependency not already installed.
- Stop if files outside Files touched must change.
