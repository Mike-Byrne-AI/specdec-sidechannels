from __future__ import annotations

import json


def test_docs_state_permissions_are_not_a_sandbox(repo_root):
    relatives = ["trellis-docs/trellis-harness.md", "tools/trellis_templates/CLAUDE.md.template"]
    if (repo_root / "BLUEPRINT.md").exists():
        relatives.append("BLUEPRINT.md")
    for relative in relatives:
        text = (repo_root / relative).read_text(encoding="utf-8").lower()
        assert "not a sandbox" in text, relative


def test_shared_settings_no_known_dangerous_allow_patterns(repo_root):
    data = json.loads((repo_root / ".claude" / "settings.json").read_text(encoding="utf-8"))
    allow = data["permissions"].get("allow", [])
    forbidden = {"Bash(rm -rf:*)", "Bash(git push:*)", "Bash(git reset --hard:*)", "Bash(curl:*)", "Bash(wget:*)"}
    assert forbidden.isdisjoint(set(allow))


def test_docs_route_root_integration_through_bootstrap(repo_root):
    harness = (repo_root / "trellis-docs" / "trellis-harness.md").read_text(encoding="utf-8")
    template = (repo_root / "tools" / "trellis_templates" / "CLAUDE.md.template").read_text(encoding="utf-8")
    assert "tools/trellis_bootstrap.py" in harness
    assert "Shared `.claude/settings.json` does not directly allow" in harness
    assert "root `memory/**`" in harness
    assert "root `CLAUDE.md` and `.gitignore` behind `tools/trellis_bootstrap.py`" in template
