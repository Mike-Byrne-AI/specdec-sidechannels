from __future__ import annotations

import json
from pathlib import Path


def test_project_settings_exist_and_local_settings_are_optional(repo_root):
    settings = repo_root / ".claude" / "settings.json"
    assert settings.exists()
    assert not (repo_root / ".claude" / "settings.local.json").exists()
    assert ".claude/settings.local.json" in (repo_root / "tools" / "trellis_templates" / "gitignore.snippet").read_text(encoding="utf-8")


def test_settings_contain_permissions_and_hooks(repo_root):
    data = json.loads((repo_root / ".claude" / "settings.json").read_text(encoding="utf-8"))
    assert "permissions" in data
    assert "hooks" in data
    assert "PreToolUse" in data["hooks"]
    assert "PostToolUse" in data["hooks"]


def test_python_hooks_use_exec_form(repo_root):
    data = json.loads((repo_root / ".claude" / "settings.json").read_text(encoding="utf-8"))
    handlers = []
    for groups in data["hooks"].values():
        for group in groups:
            handlers.extend(group.get("hooks", []))
    python_handlers = [h for h in handlers if h.get("type") == "command" and h.get("command") == "python"]
    assert python_handlers
    for handler in python_handlers:
        assert "args" in handler
        assert len(handler["args"]) == 1
        assert handler["args"][0].startswith("${CLAUDE_PROJECT_DIR}/.claude/hooks/")


def test_shared_settings_do_not_allow_broad_python_c(repo_root):
    data = json.loads((repo_root / ".claude" / "settings.json").read_text(encoding="utf-8"))
    allow = data["permissions"].get("allow", [])
    assert "Bash(python -c:*)" not in allow


def test_shared_settings_do_not_allow_direct_root_claude_or_gitignore_edits(repo_root):
    data = json.loads((repo_root / ".claude" / "settings.json").read_text(encoding="utf-8"))
    allow = set(data["permissions"].get("allow", []))
    forbidden = {"Edit(CLAUDE.md)", "Write(CLAUDE.md)", "Edit(.gitignore)", "Write(.gitignore)"}
    assert forbidden.isdisjoint(allow)
    assert "Bash(python tools/trellis_bootstrap.py:*)" in allow


def test_shared_settings_do_not_auto_allow_memory_writes(repo_root):
    data = json.loads((repo_root / ".claude" / "settings.json").read_text(encoding="utf-8"))
    allow = set(data["permissions"].get("allow", []))
    forbidden = {"Edit(memory/**)", "Write(memory/**)"}
    assert forbidden.isdisjoint(allow)
    assert "Bash(python tools/trellis_memory_lint.py:*)" in allow


def test_shared_settings_do_not_auto_allow_shell_readers_staging_or_package_install(repo_root):
    data = json.loads((repo_root / ".claude" / "settings.json").read_text(encoding="utf-8"))
    allow = set(data["permissions"].get("allow", []))
    forbidden = {
        "Bash(cat:*)",
        "Bash(head:*)",
        "Bash(tail:*)",
        "Bash(grep:*)",
        "Bash(rg:*)",
        "Bash(find:*)",
        "Bash(git add:*)",
        "Bash(git show:*)",
        "Bash(pip install -r requirements.txt:*)",
    }
    assert forbidden.isdisjoint(allow)
