#!/usr/bin/env python3
"""Lint Trellis task packs against the lightweight goldprint."""

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

from tools.trellis_paths import TrellisPathError, active_task_packs, get_project_root, rel_posix  # noqa: E402

REQUIRED_SECTIONS = [
    "goal",
    "why this matters",
    "out of scope",
    "files touched",
    "risk level",
    "dependencies",
    "proof gate",
    "sub-tasks",
    "final acceptance",
    "stop conditions",
]
HEADING_RE = re.compile(r"^#{2,6}\s+(.+?)\s*$", re.MULTILINE)
ACTIVE_TP_TITLE_RE = re.compile(r"^#\s+TP-[1-9]\d*(?=$|[\s_-])", re.MULTILINE)
EXAMPLE_TP_TITLE_RE = re.compile(r"^#\s+TP-(?:0|[1-9]\d*)(?=$|[\s_-])", re.MULTILINE)
COMMAND_HINT_RE = re.compile(r"\b(python|pytest|npm|make|git)\b")
BAD_PLACEHOLDER_RE = re.compile(r"\b(TBD|TODO|FIXME|<fill|<todo|placeholder)\b", re.IGNORECASE)


@dataclass(frozen=True)
class PackIssue:
    path: str
    code: str
    message: str


def normalize_heading(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def collect_sections(text: str) -> set[str]:
    return {normalize_heading(m.group(1)) for m in HEADING_RE.finditer(text)}


def section_body(text: str, heading: str) -> str:
    wanted = normalize_heading(heading)
    matches = list(HEADING_RE.finditer(text))
    for i, match in enumerate(matches):
        if normalize_heading(match.group(1)) != wanted:
            continue
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        return text[start:end].strip()
    return ""


def _is_example_pack(path: Path, root: Path) -> bool:
    try:
        rel = path.resolve().relative_to((root / "task-packs" / "examples").resolve())
    except ValueError:
        return False
    return len(rel.parts) >= 1


def lint_pack(path: Path, project_root: Path | None = None) -> list[PackIssue]:
    root = project_root or get_project_root(path)
    text = path.read_text(encoding="utf-8")
    rel = rel_posix(path, root)
    sections = collect_sections(text)
    issues: list[PackIssue] = []

    title_re = EXAMPLE_TP_TITLE_RE if _is_example_pack(path, root) else ACTIVE_TP_TITLE_RE
    if not title_re.search(text):
        issues.append(PackIssue(rel, "title", "active task pack title must start with '# TP-N' where N is 1 or higher; examples may use TP-0"))

    for section in REQUIRED_SECTIONS:
        if normalize_heading(section) not in sections:
            issues.append(PackIssue(rel, "missing-section", f"missing section: {section}"))

    files_body = section_body(text, "Files touched")
    if files_body and BAD_PLACEHOLDER_RE.search(files_body):
        issues.append(PackIssue(rel, "placeholder", "Files touched section contains a placeholder"))

    proof_body = section_body(text, "Proof gate")
    if proof_body and not COMMAND_HINT_RE.search(proof_body):
        issues.append(PackIssue(rel, "proof", "Proof gate should include at least one concrete command"))

    acceptance_body = section_body(text, "Final acceptance")
    if acceptance_body and BAD_PLACEHOLDER_RE.search(acceptance_body):
        issues.append(PackIssue(rel, "placeholder", "Final acceptance contains a placeholder"))

    return issues


def lint_paths(paths: list[Path], project_root: Path) -> list[PackIssue]:
    issues: list[PackIssue] = []
    for path in paths:
        if path.exists() and path.is_file():
            issues.extend(lint_pack(path, project_root=project_root))
        else:
            issues.append(PackIssue(str(path), "missing", "task pack does not exist"))
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint Trellis task packs")
    parser.add_argument("paths", nargs="*", help="Specific task packs to lint; default is active packs")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        project_root = get_project_root(Path(__file__).resolve())
    except TrellisPathError as exc:
        print(f"[FAIL] pack-lint: {exc}", file=sys.stderr)
        return 1

    paths = [Path(p).resolve() for p in args.paths] if args.paths else active_task_packs(project_root)
    issues = lint_paths(paths, project_root)
    payload = {"ok": not issues, "checked": [rel_posix(p, project_root) if p.exists() else str(p) for p in paths], "issues": [i.__dict__ for i in issues]}

    if args.json:
        print(json.dumps(payload, sort_keys=True))
        return 0 if not issues else 1

    if not paths:
        print("[OK] pack-lint: no active task packs")
        return 0
    if not issues:
        print(f"[OK] pack-lint: {len(paths)} pack(s) valid")
        return 0
    print(f"[FAIL] pack-lint: {len(issues)} issue(s)")
    for issue in issues:
        print(f"  {issue.path}: {issue.code} - {issue.message}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
