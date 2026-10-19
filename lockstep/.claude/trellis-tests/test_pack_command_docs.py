from __future__ import annotations


def test_pack_command_is_powershell_safe_and_handles_missing_tests(repo_root):
    text = (repo_root / ".claude" / "commands" / "pack.md").read_text(encoding="utf-8")
    assert "python -m pytest -q" in text
    assert "no tests/ directory yet" in text
    assert "tail -3" not in text
    assert "task-packs/examples/" in text
