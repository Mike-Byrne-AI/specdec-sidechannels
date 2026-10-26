"""tests/test_lint_findings.py: the findings lint reads a wrapped `- source:` bullet whole
(written 2026-10-16, lane C of the 2026-10-15 image audit, item S5b-C-1; no torch, no git needed
for the synthetic cases: lint_text takes the tracked set as an argument).

The image audit found that tools/lint_findings.py read only the first physical line of a
`- source:` bullet, so a path on a continuation line (FINDINGS.md wraps long bullets with
two-space indents) was never checked: renaming such a path to a nonexistent file still printed OK.
The cases here call the lint's own source_lines() and lint_text(), never a copy of its pattern (a
reviewer ran the first draft against the old lint and only one of four tests failed): a wrapped
bullet whose continuation paths exist and are tracked passes; the same bullet with a continuation
path renamed fails and names the path; a one-line bullet behaves as before; a pathless source still
passes (documented design, not changed here). The real-tree case runs the lint over FINDINGS.md
with git's tracked set, then renames a path that F-28 cites only on a continuation line and
requires the error.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import lint_findings as lf  # noqa: E402


def _tree(tmp_path: Path, *rel: str) -> set[str]:
    for r in rel:
        p = tmp_path / r
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("x\n", encoding="utf-8")
    return set(rel)


WRAPPED = (
    "## F-9 — a wrapped entry\n"
    "- regime: synthetic\n"
    "- source: results/real/a.json, results/real/a.json.state.jsonl\n"
    "  (PRIMARY), results/real/b.json,\n"
    "  tools/run_x.py (the instrument), tests/test_x.py;\n"
    "  docs/BLUEPRINT.md (the registration).\n"
    "- finding: something\n"
)
WRAPPED_FILES = ("results/real/a.json", "results/real/a.json.state.jsonl", "results/real/b.json",
                 "tools/run_x.py", "tests/test_x.py", "docs/BLUEPRINT.md")


def test_source_lines_joins_a_wrapped_bullet_into_one_line():
    body = lf.parse_entries(WRAPPED)[0][1]
    srcs = lf.source_lines(body)
    assert len(srcs) == 1 and "\n" not in srcs[0]
    assert srcs[0].startswith("results/real/a.json, results/real/a.json.state.jsonl (PRIMARY), results/real/b.json,")
    toks = lf.source_paths(srcs[0], ROOT)
    for want in ("tools/run_x.py", "tests/test_x.py", "docs/BLUEPRINT.md", "results/real/b.json"):
        assert want in toks
    # a bullet immediately followed by another bullet is not a continuation
    two = "## F-3 — two bullets\n- regime: r\n- source: results/a.json\n- finding: results/zz.json\n"
    assert lf.source_lines(lf.parse_entries(two)[0][1]) == ["results/a.json"]


def test_wrapped_source_bullet_passes_when_every_path_is_tracked(tmp_path):
    tracked = _tree(tmp_path, *WRAPPED_FILES)
    assert lf.lint_text(WRAPPED, tmp_path, tracked=tracked) == []


def test_renamed_continuation_path_is_reported(tmp_path):
    tracked = _tree(tmp_path, *WRAPPED_FILES)
    mutant = WRAPPED.replace("tests/test_x.py", "tests/test_gone.py")
    errors = lf.lint_text(mutant, tmp_path, tracked=tracked)
    assert errors and any("tests/test_gone.py" in e and "does not exist" in e for e in errors), errors
    # an untracked continuation path is reported too (exists on disk, not in the tracked set)
    (tmp_path / "tests" / "test_gone.py").write_text("x\n", encoding="utf-8")
    errors = lf.lint_text(mutant, tmp_path, tracked=tracked)
    assert any("tests/test_gone.py" in e and "not committed evidence" in e for e in errors), errors
    # the same rename on the LAST continuation line, the one the old regex never reached
    mutant = WRAPPED.replace("docs/BLUEPRINT.md", "docs/GONE.md")
    errors = lf.lint_text(mutant, tmp_path, tracked=tracked)
    assert any("docs/GONE.md" in e for e in errors), errors


def test_one_line_bullet_and_pathless_source_unchanged(tmp_path):
    tracked = _tree(tmp_path, "results/a.json")
    one = "## F-1 — one line\n- regime: r\n- source: results/a.json\n- finding: f\n"
    assert lf.lint_text(one, tmp_path, tracked=tracked) == []
    assert lf.lint_text(one.replace("a.json", "zz.json"), tmp_path, tracked=tracked) != []
    pathless = "## F-2 — prose source\n- regime: r\n- source: the critic's recompute of 2026-10-01\n- finding: f\n"
    assert lf.lint_text(pathless, tmp_path, tracked=tracked) == []   # documented design: free text passes


def test_real_findings_pass_and_a_continuation_path_rename_is_caught():
    text = (ROOT / "FINDINGS.md").read_text(encoding="utf-8")
    tracked = lf.git_tracked_paths(ROOT)
    if tracked is None:
        pytest.skip("git could not answer")
    assert lf.lint_text(text, ROOT, tracked=tracked) == []
    # F-28 cites its instrument on a continuation line of its source bullet only
    f28 = dict(lf.parse_entries(text))["F-28"]
    first_lines = [ln for ln in f28.splitlines() if ln.startswith("- source:")]
    assert first_lines and not any("tools/run_reader_lens.py" in ln for ln in first_lines)
    assert any("tools/run_reader_lens.py" in s for s in lf.source_lines(f28))
    mutant = text.replace("tools/run_reader_lens.py (the instrument", "tools/run_reader_gone.py (the instrument", 1)
    assert mutant != text
    errors = lf.lint_text(mutant, ROOT, tracked=tracked)
    assert any("F-28" in e and "tools/run_reader_gone.py" in e for e in errors), errors
