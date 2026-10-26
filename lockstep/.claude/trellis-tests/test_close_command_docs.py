
from __future__ import annotations

import json


def test_close_command_exists_and_uses_lightweight_gate(repo_root):
    text = (repo_root / ".claude" / "commands" / "close.md").read_text(encoding="utf-8")
    assert "python tools/trellis_refs.py" in text
    assert "python tools/trellis_repair_gate.py" in text
    assert "python tools/trellis_extract_godfile.py" in text
    assert "task-packs/done/" in text


def test_settings_wires_statusline(repo_root):
    data = json.loads((repo_root / ".claude" / "settings.json").read_text(encoding="utf-8"))
    assert data["statusLine"]["type"] == "command"
    assert "tools/trellis_status.py" in data["statusLine"]["command"]
