from __future__ import annotations

import pytest

from tools.trellis_paths import is_source_layout

REQUIRED_PUBLIC_FILES = [
    "README.md",
    "LICENSE",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "CODE_OF_CONDUCT.md",
    "CHANGELOG.md",
    ".gitignore",
    ".github/workflows/ci.yml",
    ".github/ISSUE_TEMPLATE/bug_report.md",
    ".github/ISSUE_TEMPLATE/security_note.md",
    ".github/PULL_REQUEST_TEMPLATE.md",
]


def test_public_files_exist_in_source_checkout(repo_root):
    if not is_source_layout(repo_root):
        pytest.skip("public source-repository files are excluded from installed host projects")
    for relative in REQUIRED_PUBLIC_FILES:
        assert (repo_root / relative).exists(), relative


def test_readme_names_status_license_and_local_gates(repo_root):
    if not is_source_layout(repo_root):
        pytest.skip("README is source-only")
    readme = repo_root / "README.md"
    text = readme.read_text(encoding="utf-8")
    assert "public preview" in text.lower()
    assert "MIT" in text
    assert "python -m pytest -q" in text
    assert "pytest -q" in text
    assert "python tools/trellis_repair_gate.py" in text
    assert "python tools/trellis_oss_release_gate.py" in text
    assert "python tools/trellis_memory_lint.py" in text


def test_public_decisions_record_license_and_preview_status(repo_root):
    text = (repo_root / "trellis-docs" / "trellis-decisions.md").read_text(encoding="utf-8")
    assert "D-1 - Public preview license and status [imagined]" in text
    assert "MIT license" in text
