#!/usr/bin/env python3
"""PostToolUse hook: remind on source changes that cite finding IDs.

This hook is informational. It inspects the actual text being written across
normal Claude Code Edit, Write, and str_replace payload shapes.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

_HOOK_ROOT = str(Path(__file__).resolve().parents[2])
if _HOOK_ROOT not in sys.path:
    sys.path.insert(0, _HOOK_ROOT)

from tools.trellis_paths import TrellisPathError, get_project_root, resolve_tool_path  # noqa: E402

WRITE_TOOLS = {"Edit", "Write", "str_replace"}
DIRECT_TEXT_FIELDS = ("new_string", "new_str", "content", "file_text", "text")
NESTED_TEXT_FIELDS = ("edits", "replacements", "changes")
FINDING_RE = re.compile(r"(?<![A-Za-z0-9_])F[1-9]\d*(?![A-Za-z0-9_-])")


def extract_candidate_text(payload: dict) -> str:
    """Collect candidate changed text from known shallow payload fields."""
    parts: list[str] = []
    for field in DIRECT_TEXT_FIELDS:
        value = payload.get(field)
        if isinstance(value, str):
            parts.append(value)
    for field in NESTED_TEXT_FIELDS:
        value = payload.get(field)
        if not isinstance(value, list):
            continue
        for item in value:
            if not isinstance(item, dict):
                continue
            for direct_field in DIRECT_TEXT_FIELDS:
                nested = item.get(direct_field)
                if isinstance(nested, str):
                    parts.append(nested)
    return "\n".join(parts)


def in_scope(file_path: str, project_root: Path, cwd: str | None) -> bool:
    if not file_path:
        return False
    target = resolve_tool_path(file_path, project_root, cwd)
    suffix = target.suffix.lower()
    if suffix not in {".py", ".md", ".txt"}:
        return False
    try:
        rel = target.relative_to(project_root)
    except ValueError:
        return False
    parts = set(rel.parts)
    rel_str = rel.as_posix()
    return bool(parts & {"src", "tools", "tests"}) or rel_str in {"trellis-docs/trellis-decisions.md", "trellis-docs/trellis-findings.md"}


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    if data.get("tool_name", "") not in WRITE_TOOLS:
        return 0

    tool_input = data.get("tool_input", {})
    if not isinstance(tool_input, dict):
        return 0

    delta_text = extract_candidate_text(tool_input)
    findings = sorted(set(FINDING_RE.findall(delta_text)))
    if not findings:
        return 0

    try:
        project_root = get_project_root(Path(__file__).resolve())
    except TrellisPathError:
        return 0

    file_path = tool_input.get("file_path") or tool_input.get("path") or ""
    if not in_scope(str(file_path), project_root, data.get("cwd")):
        return 0

    candidates = sorted((project_root / "outputs").glob("run_*/checkpoint.pt"))
    if candidates:
        checkpoint = max(candidates, key=lambda p: p.stat().st_mtime).relative_to(project_root)
    else:
        checkpoint = Path("outputs/run_NNN/checkpoint.pt")

    msg = [
        f"REMINDER: change to {file_path} cites finding(s): {findings}",
        "",
        "If this code asserts the finding still holds, verify it now:",
    ]
    for finding in findings:
        msg.append(f"  python tools/trellis_verify_finding.py {finding} --checkpoint {checkpoint}")
    msg.extend(
        [
            "",
            "If verify returns CONTRADICTS, append a new finding that documents",
            "the invalidation before treating this change as done.",
        ]
    )
    print("\n".join(msg), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
