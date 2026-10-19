#!/usr/bin/env python3
"""PreToolUse hook for Read: record normalized paths read this session."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_HOOK_ROOT = str(Path(__file__).resolve().parents[2])
if _HOOK_ROOT not in sys.path:
    sys.path.insert(0, _HOOK_ROOT)

from tools.trellis_paths import TrellisPathError, get_project_root, path_key, resolve_tool_path  # noqa: E402
from tools.trellis_session_state import record_session_read  # noqa: E402


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    if data.get("tool_name") != "Read":
        return 0

    raw_file_path = data.get("tool_input", {}).get("file_path", "")
    if not raw_file_path:
        return 0

    try:
        project_root = get_project_root(Path(__file__).resolve())
    except TrellisPathError:
        return 0

    session_id = data.get("session_id", "default")

    try:
        norm = path_key(resolve_tool_path(raw_file_path, project_root, data.get("cwd")))
        record_session_read(project_root, session_id, norm)
    except (ValueError, OSError):
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
