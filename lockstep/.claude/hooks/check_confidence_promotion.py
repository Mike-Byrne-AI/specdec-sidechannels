#!/usr/bin/env python3
"""PreToolUse hook: block unaudited confidence promotions in trellis-docs/trellis-decisions.md."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

_HOOK_ROOT = str(Path(__file__).resolve().parents[2])
if _HOOK_ROOT not in sys.path:
    sys.path.insert(0, _HOOK_ROOT)

from tools.trellis_paths import TrellisPathError, decisions_path, get_project_root, resolve_tool_path  # noqa: E402

DECISION_HEADER_RE = re.compile(
    r"^##\s+(D-\d+)\s*[—-]\s*(.+?)\s+\[(verified|probable|imagined)\]\s*$",
    re.MULTILINE,
)
PROMOTION_ORDER = {"imagined": 0, "probable": 1, "verified": 2}
WRITE_TOOLS = {"Edit", "Write", "str_replace"}


def extract_confidence_map(text: str) -> dict[str, str]:
    return {m.group(1): m.group(3) for m in DECISION_HEADER_RE.finditer(text)}


def simulate_edit(current: str, tool_name: str, tool_input: dict) -> str | None:
    if tool_name == "str_replace":
        old_str = tool_input.get("old_str", "")
        new_str = tool_input.get("new_str", "")
        if not old_str or old_str not in current:
            return None
        return current.replace(old_str, new_str, 1)
    if tool_name == "Edit":
        old_str = tool_input.get("old_string", "") or tool_input.get("old_str", "")
        new_str = tool_input.get("new_string", "") or tool_input.get("new_str", "")
        if not old_str or old_str not in current:
            return None
        return current.replace(old_str, new_str, 1)
    if tool_name == "Write":
        return tool_input.get("file_text") or tool_input.get("content", "")
    return None


def delta_text(tool_input: dict) -> str:
    parts = []
    for field in ("new_string", "new_str", "file_text", "content", "text"):
        value = tool_input.get(field)
        if isinstance(value, str):
            parts.append(value)
    return "\n".join(parts)


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    tool_name = data.get("tool_name", "")
    if tool_name not in WRITE_TOOLS:
        return 0

    tool_input = data.get("tool_input", {})
    raw_file_path = tool_input.get("file_path") or tool_input.get("path") or ""
    if not raw_file_path:
        return 0

    try:
        project_root = get_project_root(Path(__file__).resolve())
    except TrellisPathError:
        return 0

    file_path = resolve_tool_path(raw_file_path, project_root, data.get("cwd"))
    if file_path != decisions_path(project_root):
        return 0
    if not file_path.exists():
        return 0

    try:
        current = file_path.read_text(encoding="utf-8")
    except OSError:
        return 0

    new_content = simulate_edit(current, tool_name, tool_input)
    if new_content is None:
        return 0

    old_map = extract_confidence_map(current)
    new_map = extract_confidence_map(new_content)

    violations: list[tuple[str, str, str]] = []
    for decision_id, new_confidence in new_map.items():
        old_confidence = old_map.get(decision_id)
        if old_confidence is None:
            continue
        if PROMOTION_ORDER.get(new_confidence, -1) > PROMOTION_ORDER.get(old_confidence, -1):
            violations.append((decision_id, old_confidence, new_confidence))

    if not violations:
        return 0

    changed_text = delta_text(tool_input)
    justifications = [
        "trellis_verify_finding.py" in changed_text or "verify_finding.py" in changed_text,
        bool(re.search(r"verified (by|in) run_\d+", changed_text)),
        "USER-CONFIRMED" in changed_text,
    ]
    if any(justifications):
        return 0

    msg = [
        "BLOCK: confidence promotion in trellis-docs/trellis-decisions.md without justification.",
        "",
        "Promotions detected:",
    ]
    for decision_id, old_confidence, new_confidence in violations:
        msg.append(f"  {decision_id}: [{old_confidence}] -> [{new_confidence}]")
    msg.extend(
        [
            "",
            "Confidence promotions require one of:",
            "  (a) a trellis_verify_finding.py citation in the same change",
            "  (b) a phrase like 'verified by run_NNN' in the same change",
            "  (c) the marker 'USER-CONFIRMED' from the user",
        ]
    )
    print("\n".join(msg), file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
