#!/usr/bin/env python3
"""Print a compact Trellis status line for Claude Code.

Reads optional Claude Code status JSON from stdin. Output is intentionally
cheap, dependency-free, and ASCII-only.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from tools.trellis_extract_godfile import godfile_freshness  # noqa: E402
from tools.trellis_paths import (  # noqa: E402
    TrellisPathError,
    active_task_packs,
    get_project_root,
    decisions_path,
    findings_path,
    path_key,
)
from tools.trellis_session_state import read_session_reads  # noqa: E402


def _read_stdin_json() -> dict:
    try:
        raw = sys.stdin.read()
    except OSError:
        return {}
    if not raw.strip():
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _project_root_from_status(data: dict) -> Path:
    workspace = data.get("workspace") if isinstance(data.get("workspace"), dict) else {}
    candidates = [
        workspace.get("project_dir"),
        workspace.get("current_dir"),
        data.get("cwd"),
        os.environ.get("TRELLIS_PROJECT_ROOT"),
        Path.cwd(),
    ]
    for candidate in candidates:
        if not candidate:
            continue
        try:
            return get_project_root(candidate)
        except (TrellisPathError, OSError):
            continue
    raise TrellisPathError("could not find Trellis project root")


def _godfile_status(project_root: Path) -> str:
    return godfile_freshness(project_root).status


def _context_status(project_root: Path, session_id: str | None) -> str:
    if not session_id:
        return "unknown"
    reads = read_session_reads(project_root, session_id)
    if reads is None:
        return "missing"
    observed = {str(item) for item in reads if isinstance(item, str)}
    required = {path_key(findings_path(project_root)), path_key(decisions_path(project_root))}
    return "loaded" if required.issubset(observed) else "missing"


def _git_status(project_root: Path) -> str:
    if not (project_root / ".git").exists():
        return "nogit"
    try:
        proc = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "unknown"
    if proc.returncode != 0:
        return "unknown"
    return "dirty" if proc.stdout.strip() else "clean"


def build_status(project_root: Path, session_id: str | None = None) -> str:
    packs = len(active_task_packs(project_root))
    ctx = _context_status(project_root, session_id)
    godfile = _godfile_status(project_root)
    git = _git_status(project_root)
    return f"Trellis: ctx={ctx} | godfile={godfile} | packs={packs} | git={git}"


def main() -> int:
    data = _read_stdin_json()
    session_id = data.get("session_id") if isinstance(data.get("session_id"), str) else None
    try:
        project_root = _project_root_from_status(data)
        print(build_status(project_root, session_id))
    except TrellisPathError:
        print("Trellis: unavailable")
    return 0


if __name__ == "__main__":
    sys.exit(main())
