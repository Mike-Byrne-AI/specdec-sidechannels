#!/usr/bin/env python3
"""PreToolUse hook: require project-root memory files before src/ edits.

The hook accepts only reads of the actual project-root trellis-docs/trellis-findings.md and
trellis-docs/trellis-decisions.md. Matching basenames elsewhere do not satisfy the requirement.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_HOOK_ROOT = str(Path(__file__).resolve().parents[2])
if _HOOK_ROOT not in sys.path:
    sys.path.insert(0, _HOOK_ROOT)

from tools.trellis_paths import (  # noqa: E402
    TrellisPathError,
    get_project_root,
    path_key,
    resolve_tool_path,
)
from tools.trellis_session_state import read_session_reads  # noqa: E402

WRITE_TOOLS = {"Edit", "Write", "str_replace"}
REQUIRED_FILES = ("trellis-docs/trellis-findings.md", "trellis-docs/trellis-decisions.md")


def _src_edit_rel(data: dict, project_root: Path) -> str | None:
    if data.get("tool_name", "") not in WRITE_TOOLS:
        return None
    tool_input = data.get("tool_input", {})
    raw_file_path = tool_input.get("file_path") or tool_input.get("path") or ""
    if not raw_file_path:
        return None
    target = resolve_tool_path(raw_file_path, project_root, data.get("cwd"))
    try:
        rel = target.relative_to(project_root)
    except ValueError:
        return None
    rel_str = rel.as_posix()
    if rel_str.startswith("src/"):
        return rel_str
    return None


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    try:
        project_root = get_project_root(Path(__file__).resolve())
    except TrellisPathError as exc:
        print(f"BLOCK: could not determine Trellis project root: {exc}", file=sys.stderr)
        return 2

    rel_str = _src_edit_rel(data, project_root)
    if rel_str is None:
        return 0

    session_id = data.get("session_id", "default")
    observed_reads = read_session_reads(project_root, session_id)
    if observed_reads is None:
        print(
            f"BLOCK: cannot edit {rel_str} until context files have been read this session.\n"
            "Read trellis-docs/trellis-findings.md and trellis-docs/trellis-decisions.md from the project root before editing src/.",
            file=sys.stderr,
        )
        return 2

    required = {path_key(project_root / name): name for name in REQUIRED_FILES}
    observed = {path_key(path) for path in observed_reads}
    missing = [name for key, name in required.items() if key not in observed]
    if not missing:
        return 0

    print(
        f"BLOCK: cannot edit {rel_str} until context files have been read this session.\n"
        f"Missing root files: {missing}\n"
        "Read trellis-docs/trellis-findings.md and trellis-docs/trellis-decisions.md from the project root before editing src/.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
