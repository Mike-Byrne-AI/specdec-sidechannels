#!/usr/bin/env python3
"""PreToolUse hook: block guarded source edits when the godfile is stale."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_HOOK_ROOT = str(Path(__file__).resolve().parents[2])
if _HOOK_ROOT not in sys.path:
    sys.path.insert(0, _HOOK_ROOT)

from tools.trellis_extract_godfile import godfile_freshness  # noqa: E402
from tools.trellis_paths import (  # noqa: E402
    TrellisPathError,
    get_project_root,
    resolve_tool_path,
)

GODFILE_BYPASS_MARKER = "GODFILE-BYPASS"
WRITE_TOOLS = {"Edit", "Write", "str_replace"}


def blocks_src_edit(data: dict, project_root: Path) -> tuple[bool, str]:
    tool_name = data.get("tool_name", "")
    if tool_name not in WRITE_TOOLS:
        return False, ""

    tool_input = data.get("tool_input", {})
    raw_file_path = tool_input.get("file_path") or tool_input.get("path") or ""
    if not raw_file_path:
        return False, ""

    target = resolve_tool_path(raw_file_path, project_root, data.get("cwd"))
    try:
        rel = target.relative_to(project_root)
    except ValueError:
        return False, ""

    rel_str = rel.as_posix()
    return rel_str.startswith("src/"), rel_str


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

    should_check, rel_str = blocks_src_edit(data, project_root)
    if not should_check:
        return 0

    tool_input = data.get("tool_input", {})
    if GODFILE_BYPASS_MARKER in json.dumps(tool_input, sort_keys=True):
        return 0

    freshness = godfile_freshness(project_root)
    if freshness.fresh:
        return 0

    if freshness.status == "missing":
        print(
            "BLOCK: .claude/GODFILE.md does not exist.\n"
            "Regenerate it before editing src/:\n"
            "  python tools/trellis_extract_godfile.py",
            file=sys.stderr,
        )
        return 2

    print(
        f"BLOCK: godfile is {freshness.status} before editing {rel_str}.\n"
        f"Reason: {freshness.reason}\n"
        "Regenerate it before editing src/:\n"
        "  python tools/trellis_extract_godfile.py",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
