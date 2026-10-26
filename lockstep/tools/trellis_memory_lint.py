#!/usr/bin/env python3
"""Lint Trellis internal memory for OSS-safe, low-footgun content.

The checker is intentionally conservative and dependency-free. It validates
only memory directories marked with `memory/.trellis-memory`; an unmarked root
`memory/` path is treated as host-owned and skipped.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from tools.trellis_paths import (  # noqa: E402
    TRELLIS_MEMORY_REL,
    TrellisPathError,
    get_project_root,
    has_trellis_memory,
    memory_dir,
    rel_posix,
)

TOPIC_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MAX_TOPIC_COUNT = 12
MAX_MARKDOWN_BYTES = 24_000
MAX_TOTAL_BYTES = 160_000
ALLOWED_ROOT_FILES = {".trellis-memory", "README.md"}
ALLOWED_SUFFIXES = {".md"}
BANNED_NAME_PARTS = {
    "cache",
    "credential",
    "credentials",
    "dump",
    "log",
    "logs",
    "private",
    "scratch",
    "secret",
    "secrets",
    "tmp",
    "transcript",
}
SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("private-key", re.compile(r"-----BEGIN (?:RSA |DSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("aws-access-key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("github-token", re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{30,}\b")),
    ("openai-style-key", re.compile(r"\bsk-[A-Za-z0-9]{20,}\b")),
    (
        "assigned-secret",
        re.compile(r"(?i)\b(?:api[_-]?key|password|secret|token)\s*[:=]\s*['\"]?[^\s'\"]{8,}"),
    ),
)


@dataclass(frozen=True)
class MemoryIssue:
    path: str
    code: str
    message: str


def _issue(path: Path, project_root: Path, code: str, message: str) -> MemoryIssue:
    try:
        rel = path.relative_to(project_root).as_posix()
    except ValueError:
        try:
            rel = rel_posix(path, project_root)
        except ValueError:
            rel = path.as_posix()
    return MemoryIssue(rel, code, message)


def _name_has_banned_part(path: Path) -> str | None:
    for part in path.parts:
        tokens = [token for token in re.split(r"[^A-Za-z0-9]+", part.lower()) if token]
        for token in tokens:
            if token in BANNED_NAME_PARTS:
                return token
    return None


def _read_utf8(path: Path) -> tuple[str | None, str | None]:
    try:
        return path.read_text(encoding="utf-8"), None
    except UnicodeDecodeError as exc:
        return None, f"not valid UTF-8: {exc}"
    except OSError as exc:
        return None, f"could not read file: {exc}"


def _check_secret_patterns(text: str) -> str | None:
    for label, pattern in SECRET_PATTERNS:
        if pattern.search(text):
            return label
    return None


def iter_memory_entries(project_root: Path) -> list[Path]:
    mem = memory_dir(project_root)
    if not mem.exists() or not mem.is_dir():
        return []
    return sorted(mem.rglob("*"))


def iter_memory_files(project_root: Path) -> list[Path]:
    return sorted(path for path in iter_memory_entries(project_root) if path.is_file() and not path.is_symlink())


def check_memory(project_root: Path) -> list[MemoryIssue]:
    """Return fatal Trellis memory issues for a marked memory directory.

    Unmarked `memory/` is skipped because Trellis considers it host-owned.
    """
    project_root = project_root.resolve()
    mem = memory_dir(project_root)
    if not mem.exists():
        return []

    sentinel = mem / ".trellis-memory"
    if sentinel.is_symlink():
        return [_issue(sentinel, project_root, "symlink", "memory sentinel must be a regular in-repo file, not a symlink")]
    if not has_trellis_memory(project_root):
        return []

    issues: list[MemoryIssue] = []
    root_readme = mem / "README.md"

    if not sentinel.is_file():
        issues.append(_issue(sentinel, project_root, "missing-sentinel", "Trellis memory must include memory/.trellis-memory"))
    if not root_readme.is_file():
        issues.append(_issue(root_readme, project_root, "missing-root-readme", "Trellis memory must include memory/README.md"))

    topics = sorted(path for path in mem.iterdir() if path.is_dir() and not path.is_symlink())
    if len(topics) > MAX_TOPIC_COUNT:
        issues.append(
            _issue(
                mem,
                project_root,
                "too-many-topics",
                f"memory has {len(topics)} topic folders; keep it low-cardinality (max {MAX_TOPIC_COUNT})",
            )
        )

    for entry in sorted(mem.iterdir()):
        if entry.is_symlink():
            issues.append(_issue(entry, project_root, "symlink", "memory entries must not be symlinks"))
            continue
        if entry.is_file() and entry.name not in ALLOWED_ROOT_FILES:
            issues.append(_issue(entry, project_root, "root-file", "root memory files are limited to .trellis-memory and README.md"))
        if entry.is_dir():
            if not TOPIC_RE.match(entry.name):
                issues.append(_issue(entry, project_root, "topic-name", "topic folder names must be lowercase kebab-case"))
            if not (entry / "README.md").is_file():
                issues.append(_issue(entry / "README.md", project_root, "missing-topic-readme", "each memory topic must have README.md"))

    for path in iter_memory_entries(project_root):
        if path.is_symlink() and path.parent != mem:
            issues.append(_issue(path, project_root, "symlink", "memory entries must not be symlinks"))

    total_bytes = 0
    for path in iter_memory_files(project_root):
        rel_to_memory = path.relative_to(mem)
        banned = _name_has_banned_part(rel_to_memory)
        if banned:
            issues.append(_issue(path, project_root, "banned-name", f"memory path contains unsafe scratch/private token: {banned}"))

        if path.name != ".trellis-memory" and path.suffix.lower() not in ALLOWED_SUFFIXES:
            issues.append(_issue(path, project_root, "file-type", "memory files must be Markdown, except the sentinel"))

        if len(rel_to_memory.parts) > 2:
            issues.append(_issue(path, project_root, "nested-file", "memory files must live at root or one topic folder deep"))

        try:
            size = path.stat().st_size
        except OSError as exc:
            issues.append(_issue(path, project_root, "stat", f"could not stat file: {exc}"))
            continue
        total_bytes += size
        if path.suffix.lower() == ".md" and size > MAX_MARKDOWN_BYTES:
            issues.append(_issue(path, project_root, "large-file", f"Markdown memory files must stay <= {MAX_MARKDOWN_BYTES} bytes"))

        text, error = _read_utf8(path)
        if error:
            issues.append(_issue(path, project_root, "utf8", error))
            continue
        assert text is not None
        secret_label = _check_secret_patterns(text)
        if secret_label:
            issues.append(_issue(path, project_root, "secret-pattern", f"content looks like a secret ({secret_label})"))

    if total_bytes > MAX_TOTAL_BYTES:
        issues.append(
            _issue(
                mem,
                project_root,
                "large-memory",
                f"memory directory is {total_bytes} bytes; keep it <= {MAX_TOTAL_BYTES} bytes",
            )
        )

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint Trellis internal memory")
    parser.add_argument("--json", action="store_true", help="Emit JSON only")
    args = parser.parse_args()

    try:
        project_root = get_project_root(Path(__file__).resolve())
    except TrellisPathError as exc:
        if args.json:
            print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
        else:
            print(f"[FAIL] memory: {exc}")
        return 1

    mem = project_root / TRELLIS_MEMORY_REL
    sentinel = mem / ".trellis-memory"
    skipped = mem.exists() and not has_trellis_memory(project_root) and not sentinel.is_symlink()
    issues = check_memory(project_root)
    payload = {"ok": not issues, "skipped_host_memory": skipped, "issues": [issue.__dict__ for issue in issues]}

    if args.json:
        print(json.dumps(payload, sort_keys=True))
        return 0 if not issues else 1

    if skipped:
        print("[SKIP] memory: root memory/ is unmarked; treating it as host-owned")
        return 0
    if not issues:
        print("[OK] memory: Trellis memory layout is clean")
        return 0

    print(f"[FAIL] memory: {len(issues)} issue(s)")
    for issue in issues:
        print(f"  {issue.path}: {issue.code} - {issue.message}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
