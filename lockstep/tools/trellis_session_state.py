"""Safe session-state paths for Trellis hooks and status line."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

SESSION_STATE_REL = ".claude/.session-state"
_READS_FILE = "reads.json"
_SAFE_LEGACY_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


def session_key(session_id: str | None) -> str:
    raw = session_id if isinstance(session_id, str) and session_id else "default"
    digest = hashlib.sha256(raw.encode("utf-8", errors="surrogatepass")).hexdigest()[:20]
    return f"session-{digest}"


def session_state_root(project_root: Path) -> Path:
    return project_root / SESSION_STATE_REL


def reads_state_file(project_root: Path, session_id: str | None) -> Path:
    root = session_state_root(project_root).resolve()
    path = root / session_key(session_id) / _READS_FILE
    resolved = path.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:  # Defensive; session_key should make this impossible.
        raise ValueError("session state path escaped Trellis state directory") from exc
    return path


def legacy_reads_state_file(project_root: Path, session_id: str | None) -> Path | None:
    raw = session_id if isinstance(session_id, str) and session_id else "default"
    if raw in {".", ".."} or not _SAFE_LEGACY_RE.match(raw):
        return None
    return project_root / SESSION_STATE_REL / raw / _READS_FILE


def _load_reads(path: Path) -> list[str] | None:
    try:
        if not path.exists():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(payload, list):
        return None
    return [str(item) for item in payload if isinstance(item, str)]


def read_session_reads(project_root: Path, session_id: str | None, *, legacy_fallback: bool = True) -> list[str] | None:
    reads = _load_reads(reads_state_file(project_root, session_id))
    if reads is not None:
        return reads
    if legacy_fallback:
        legacy = legacy_reads_state_file(project_root, session_id)
        if legacy is not None:
            return _load_reads(legacy)
    return None


def write_session_reads(project_root: Path, session_id: str | None, reads: list[str]) -> Path:
    path = reads_state_file(project_root, session_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    unique: list[str] = []
    for item in reads:
        if item not in unique:
            unique.append(item)
    path.write_text(json.dumps(unique, indent=2), encoding="utf-8")
    return path


def record_session_read(project_root: Path, session_id: str | None, normalized_path: str) -> Path:
    reads = read_session_reads(project_root, session_id, legacy_fallback=False)
    if not isinstance(reads, list):
        reads = []
    if normalized_path not in reads:
        reads.append(normalized_path)
    return write_session_reads(project_root, session_id, reads)
