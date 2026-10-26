from __future__ import annotations

import json
import sys
from io import StringIO

from tools import trellis_status
from tools.trellis_paths import path_key
from tools.trellis_status import build_status


def test_statusline_builds_compact_status(minimal_project):
    status = build_status(minimal_project)
    assert status.startswith("Trellis: ")
    assert "ctx=unknown" in status
    assert "packs=0" in status


def test_statusline_reports_loaded_context(minimal_project):
    session_id = "s1"
    state_dir = minimal_project / ".claude" / ".session-state" / session_id
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "reads.json").write_text(
        json.dumps([path_key(minimal_project / "trellis-docs/trellis-findings.md"), path_key(minimal_project / "trellis-docs/trellis-decisions.md")]),
        encoding="utf-8",
    )
    status = build_status(minimal_project, session_id)
    assert "ctx=loaded" in status


def test_statusline_main_uses_status_json_project_dir(repo_root, minimal_project, monkeypatch, capsys):
    del repo_root
    payload = {"workspace": {"project_dir": str(minimal_project)}, "session_id": "s1"}
    monkeypatch.setattr(sys, "stdin", StringIO(json.dumps(payload)))
    assert trellis_status.main() == 0
    out = capsys.readouterr().out
    assert out.startswith("Trellis: ")
