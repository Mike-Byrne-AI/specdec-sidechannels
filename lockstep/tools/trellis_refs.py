#!/usr/bin/env python3
"""Check Trellis stable-reference integrity.

Validates that F<N>, D-<N>, and TP-<N> references point to known project
memory entries or task packs. This is a deterministic drift check, not a
semantic verifier.
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
    TrellisPathError,
    active_task_packs,
    decisions_path,
    findings_path,
    get_project_root,
    has_trellis_memory,
    rel_posix,
    runs_path,
)

FINDING_HEADER_RE = re.compile(r"^#{2,3}\s+(F[1-9]\d*)\b", re.MULTILINE)
DECISION_HEADER_RE = re.compile(r"^##\s+(D-[1-9]\d*)\s*[—-]\s*(.+?)\s+\[(verified|probable|imagined)\]\s*$", re.MULTILINE)
DECISION_ANY_HEADER_RE = re.compile(r"^##\s+(D-[1-9]\d*)\b.*$", re.MULTILINE)
FINDING_REF_RE = re.compile(r"(?<![A-Za-z0-9_])F[1-9]\d*(?![A-Za-z0-9_-])")
DECISION_REF_RE = re.compile(r"(?<![A-Za-z0-9_])D-[1-9]\d*(?![A-Za-z0-9_-])")
TASK_REF_RE = re.compile(r"(?<![A-Za-z0-9_])TP-[1-9]\d*(?![A-Za-z0-9_-])")
FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)

TEXT_SOURCE_SUFFIXES = {
    ".c", ".cc", ".cfg", ".cpp", ".cs", ".css", ".go", ".h", ".hpp",
    ".html", ".ini", ".java", ".js", ".json", ".jsx", ".kt", ".m",
    ".md", ".py", ".rb", ".rs", ".sh", ".sql", ".toml", ".ts", ".tsx",
    ".txt", ".xml", ".yaml", ".yml",
}
MAX_EXTENSIONLESS_TEXT_BYTES = 1_000_000


@dataclass(frozen=True)
class RefIssue:
    path: str
    kind: str
    ref: str
    message: str


def _read(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _looks_binary(data: bytes) -> bool:
    return b"\x00" in data


def _should_try_source_text(path: Path) -> bool:
    if path.suffix.lower() in TEXT_SOURCE_SUFFIXES:
        return True
    if path.suffix == "":
        try:
            return path.stat().st_size <= MAX_EXTENSIONLESS_TEXT_BYTES
        except OSError:
            return False
    return False


def _read_source_text(path: Path) -> str | None:
    if not _should_try_source_text(path):
        return None
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if _looks_binary(data):
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def strip_ignored_blocks(text: str) -> str:
    text = FENCE_RE.sub("", text)
    text = HTML_COMMENT_RE.sub("", text)
    return text


def collect_finding_ids(project_root: Path) -> set[str]:
    return set(FINDING_HEADER_RE.findall(_read(findings_path(project_root))))


def collect_decision_ids(project_root: Path) -> set[str]:
    return {m.group(1) for m in DECISION_HEADER_RE.finditer(_read(decisions_path(project_root)))}


def collect_task_pack_ids(project_root: Path) -> set[str]:
    task_root = project_root / "task-packs"
    if not task_root.exists():
        return set()
    ids: set[str] = set()
    for path in task_root.rglob("TP-*.md"):
        if any(part == "examples" for part in path.relative_to(task_root).parts):
            continue
        m = re.match(r"^(TP-[1-9]\d*)", path.name)
        if m:
            ids.add(m.group(1))
    return ids


def iter_reference_files(project_root: Path) -> list[Path]:
    files = [
        findings_path(project_root),
        decisions_path(project_root),
        runs_path(project_root),
    ]
    memory_root = project_root / "memory"
    if has_trellis_memory(project_root):
        files.extend(path for path in memory_root.rglob("*.md") if path.is_file())
    task_root = project_root / "task-packs"
    if task_root.exists():
        for path in task_root.rglob("*.md"):
            rel_parts = path.relative_to(task_root).parts
            if rel_parts and rel_parts[0] == "examples":
                continue
            files.append(path)
    src_root = project_root / "src"
    if src_root.exists():
        files.extend(p for p in src_root.rglob("*") if p.is_file())
    return sorted({p.resolve() for p in files if p.exists()})


def decision_confidence_issues(project_root: Path) -> list[RefIssue]:
    path = decisions_path(project_root)
    text = _read(path)
    valid = {m.group(1) for m in DECISION_HEADER_RE.finditer(text)}
    issues: list[RefIssue] = []
    for m in DECISION_ANY_HEADER_RE.finditer(text):
        decision_id = m.group(1)
        if decision_id not in valid:
            issues.append(
                RefIssue(
                    rel_posix(path, project_root),
                    "decision",
                    decision_id,
                    "decision header is missing a valid confidence marker: [verified], [probable], or [imagined]",
                )
            )
    return issues


def check_references(project_root: Path) -> list[RefIssue]:
    finding_ids = collect_finding_ids(project_root)
    decision_ids = collect_decision_ids(project_root)
    task_ids = collect_task_pack_ids(project_root)
    issues = decision_confidence_issues(project_root)

    src_root = project_root / "src"
    for path in iter_reference_files(project_root):
        if src_root.exists():
            try:
                path.relative_to(src_root)
                is_host_source = True
            except ValueError:
                is_host_source = False
        else:
            is_host_source = False
        raw_text = _read_source_text(path) if is_host_source else _read(path)
        if raw_text is None:
            continue
        text = strip_ignored_blocks(raw_text)
        rel = rel_posix(path, project_root)
        for ref in sorted(set(FINDING_REF_RE.findall(text))):
            if ref not in finding_ids:
                issues.append(RefIssue(rel, "finding", ref, "missing finding header in trellis-docs/trellis-findings.md"))
        for ref in sorted(set(DECISION_REF_RE.findall(text))):
            if ref not in decision_ids:
                issues.append(RefIssue(rel, "decision", ref, "missing valid decision header in trellis-docs/trellis-decisions.md"))
        for ref in sorted(set(TASK_REF_RE.findall(text))):
            if ref not in task_ids:
                issues.append(RefIssue(rel, "task-pack", ref, "missing task pack file outside examples"))
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Trellis stable-reference integrity")
    parser.add_argument("--json", action="store_true", help="Emit JSON only")
    args = parser.parse_args()

    try:
        project_root = get_project_root(Path(__file__).resolve())
    except TrellisPathError as exc:
        if args.json:
            print(json.dumps({"ok": False, "error": str(exc)}))
        else:
            print(f"[FAIL] refs: {exc}")
        return 1

    issues = check_references(project_root)
    if args.json:
        print(json.dumps({"ok": not issues, "issues": [issue.__dict__ for issue in issues]}, sort_keys=True))
        return 0 if not issues else 1

    if not issues:
        print("[OK] refs: all stable references resolve")
        return 0

    print(f"[FAIL] refs: {len(issues)} issue(s)")
    for issue in issues:
        print(f"  {issue.path}: {issue.ref} ({issue.kind}) - {issue.message}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
