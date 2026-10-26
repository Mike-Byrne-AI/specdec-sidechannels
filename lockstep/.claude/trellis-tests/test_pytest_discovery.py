from __future__ import annotations

import pytest


def test_pyproject_configures_pytest_import_path(repo_root):
    pyproject = repo_root / "pyproject.toml"
    if not pyproject.exists():
        pytest.skip("source-only pytest configuration is not installed into host projects")
    text = pyproject.read_text(encoding="utf-8")
    assert '[tool.pytest.ini_options]' in text
    assert 'pythonpath = ["."]' in text
    assert ('testpaths = ["tests"]' in text
            or 'testpaths = ["tests_project"]' in text)
