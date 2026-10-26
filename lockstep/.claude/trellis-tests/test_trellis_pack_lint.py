from __future__ import annotations

from tools.trellis_pack_lint import lint_pack

GOOD_PACK = """# TP-1_good_pack

## Goal
Ship a small change.

## Why this matters
It makes the harness safer.

## Out of scope
- No broad refactor.

## Files touched
- `tools/x.py` - helper.
- `tests/test_x.py` - proof.

## Risk level
Low. Additive only.

## Dependencies
- None.

## Proof gate
```powershell
python -m pytest -q tests/test_x.py
```

## Sub-tasks
1. Add helper.
2. Add tests.

## Final acceptance
- Tests pass.

## Stop conditions
- Stop if tests fail.
"""


def test_good_pack_passes_lint(minimal_project):
    path = minimal_project / "task-packs" / "TP-1_good.md"
    path.write_text(GOOD_PACK, encoding="utf-8")
    assert lint_pack(path, minimal_project) == []


def test_missing_required_section_fails(minimal_project):
    path = minimal_project / "task-packs" / "TP-2_bad.md"
    path.write_text("# TP-2_bad\n\n## Goal\nDo it.\n", encoding="utf-8")
    issues = lint_pack(path, minimal_project)
    assert any(issue.code == "missing-section" for issue in issues)


def test_placeholder_and_missing_proof_command_fail(minimal_project):
    text = GOOD_PACK.replace("- `tools/x.py` - helper.", "- TBD")
    text = text.replace("python -m pytest -q tests/test_x.py", "verify manually")
    path = minimal_project / "task-packs" / "TP-3_placeholder.md"
    path.write_text(text, encoding="utf-8")
    issues = lint_pack(path, minimal_project)
    assert any(issue.code == "placeholder" for issue in issues)
    assert any(issue.code == "proof" for issue in issues)


def test_root_tp0_fails_but_example_tp0_passes(minimal_project):
    root_tp0 = minimal_project / "task-packs" / "TP-0_bad.md"
    example_tp0 = minimal_project / "task-packs" / "examples" / "TP-0_good.md"
    root_tp0.write_text(GOOD_PACK.replace("# TP-1_good_pack", "# TP-0_bad"), encoding="utf-8")
    example_tp0.write_text(GOOD_PACK.replace("# TP-1_good_pack", "# TP-0_good"), encoding="utf-8")

    assert any(issue.code == "title" for issue in lint_pack(root_tp0, minimal_project))
    assert lint_pack(example_tp0, minimal_project) == []
