from __future__ import annotations

import json

from conftest import run_hook
from tools.trellis_paths import path_key
from tools.trellis_session_state import read_session_reads, reads_state_file, record_session_read, session_state_root
from tools.trellis_status import build_status


def test_session_state_path_uses_safe_hash_and_stays_under_root(minimal_project):
    dangerous_ids = ["../escape", "..\\escape", "/absolute", "", "unicode-☃"]
    root = session_state_root(minimal_project).resolve()
    for session_id in dangerous_ids:
        path = reads_state_file(minimal_project, session_id).resolve()
        path.relative_to(root)
        assert ".." not in path.relative_to(root).as_posix()
        assert path.name == "reads.json"


def test_recorded_read_is_visible_to_context_hook_and_status(repo_root, minimal_project):
    session_id = "../not-a-path"
    record_session_read(minimal_project, session_id, path_key(minimal_project / "trellis-docs/trellis-findings.md"))
    record_session_read(minimal_project, session_id, path_key(minimal_project / "trellis-docs/trellis-decisions.md"))

    payload = {
        "tool_name": "Edit",
        "session_id": session_id,
        "cwd": str(minimal_project),
        "tool_input": {"file_path": "src/main.py", "old_string": "hello", "new_string": "hello world"},
    }
    proc = run_hook(repo_root, minimal_project, "check_context_loaded.py", payload)
    assert proc.returncode == 0, proc.stderr
    assert "ctx=loaded" in build_status(minimal_project, session_id)


def test_legacy_simple_session_fallback(minimal_project):
    state = minimal_project / ".claude" / ".session-state" / "s1" / "reads.json"
    state.parent.mkdir(parents=True, exist_ok=True)
    state.write_text(json.dumps(["x"]), encoding="utf-8")
    assert read_session_reads(minimal_project, "s1") == ["x"]
