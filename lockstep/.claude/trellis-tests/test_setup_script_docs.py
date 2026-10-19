from __future__ import annotations

import pytest

from tools.trellis_paths import is_source_layout


def test_docs_prefer_portable_setup_invocation(repo_root):
    if not is_source_layout(repo_root):
        pytest.skip("README is source-only")
    docs = (repo_root / "README.md").read_text(encoding="utf-8") + "\n" + (repo_root / "trellis-docs" / "trellis-harness.md").read_text(encoding="utf-8")
    assert "bash setup.sh" in docs


def test_setup_script_uses_bash_and_python_installer(repo_root):
    if not is_source_layout(repo_root):
        pytest.skip("setup.sh is source-only")
    setup = repo_root / "setup.sh"
    text = setup.read_text(encoding="utf-8")
    assert text.startswith("#!/usr/bin/env bash")
    assert "install_trellis.py" in text
