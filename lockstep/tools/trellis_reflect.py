#!/usr/bin/env python3
"""Deterministic reflection checks for Trellis sessions."""

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

from tools.trellis_memory_lint import check_memory  # noqa: E402
from tools.trellis_pack_lint import lint_paths  # noqa: E402
from tools.trellis_paths import (  # noqa: E402
    TrellisPathError,
    active_task_packs,
    get_project_root,
    has_trellis_memory,
    is_source_layout,
    is_under,
    rel_posix,
)
from tools.trellis_refs import check_references  # noqa: E402

MD_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
TOOL_CMD_RE = re.compile(r"python\s+tools/([A-Za-z0-9_./-]+\.py)")
SOURCE_ONLY_MARKDOWN = {
    "BLUEPRINT.md",
    "CHANGELOG.md",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "README.md",
    "SECURITY.md",
}
SOURCE_ONLY_MARKDOWN_PREFIXES = {".github"}
TRELLIS_MARKDOWN_PREFIXES = {".claude", "task-packs", "trellis-docs"}


@dataclass(frozen=True)
class ReflectIssue:
    path: str
    code: str
    message: str


def _rel_parts(path: Path, project_root: Path) -> tuple[str, ...]:
    return path.relative_to(project_root).parts


def _in_reflection_scope(path: Path, project_root: Path, trellis_memory: bool, source_layout: bool) -> bool:
    rel = path.relative_to(project_root)
    rel_str = rel.as_posix()
    if path.name == "GODFILE.md":
        return False
    if rel.parts and rel.parts[0] == "memory":
        return trellis_memory
    if rel.parts and rel.parts[0] in TRELLIS_MARKDOWN_PREFIXES:
        return True
    if source_layout and rel_str in SOURCE_ONLY_MARKDOWN:
        return True
    if source_layout and rel.parts and rel.parts[0] in SOURCE_ONLY_MARKDOWN_PREFIXES:
        return True
    return False


def iter_markdown_files(project_root: Path) -> list[Path]:
    """Return Markdown files Trellis owns or, in source checkouts, publishes.

    Installed hosts may have arbitrary root docs with broken local links or
    non-UTF-8 content. Reflection should not fail the Trellis gate because of
    host-owned Markdown outside Trellis-owned directories.
    """
    skip_parts = {".git", ".pytest_cache", "__pycache__", ".venv"}
    project_root = project_root.resolve()
    trellis_memory = has_trellis_memory(project_root)
    source_layout = is_source_layout(project_root)
    files: list[Path] = []
    memory_root = project_root / "memory"
    for path in project_root.rglob("*.md"):
        try:
            parts = _rel_parts(path, project_root)
        except ValueError:
            continue
        if any(part in skip_parts for part in parts):
            continue
        if memory_root.exists() and is_under(path, memory_root) and not trellis_memory:
            continue
        if _in_reflection_scope(path, project_root, trellis_memory, source_layout):
            files.append(path)
    return sorted(files)


def is_external_link(target: str) -> bool:
    lower = target.lower()
    return lower.startswith(("http://", "https://", "mailto:", "#"))


def _read_markdown(path: Path, project_root: Path) -> tuple[str | None, ReflectIssue | None]:
    try:
        return path.read_text(encoding="utf-8"), None
    except UnicodeDecodeError as exc:
        return None, ReflectIssue(rel_posix(path, project_root), "unreadable-markdown", f"not valid UTF-8: {exc}")
    except OSError as exc:
        return None, ReflectIssue(rel_posix(path, project_root), "unreadable-markdown", f"could not read file: {exc}")


def check_markdown_links(project_root: Path) -> list[ReflectIssue]:
    issues: list[ReflectIssue] = []
    for path in iter_markdown_files(project_root):
        text, read_issue = _read_markdown(path, project_root)
        if read_issue is not None:
            issues.append(read_issue)
            continue
        assert text is not None
        for match in MD_LINK_RE.finditer(text):
            target = match.group(1).strip()
            if is_external_link(target) or target.startswith("sandbox:"):
                continue
            clean = target.split("#", 1)[0]
            if not clean:
                continue
            dest = (path.parent / clean).resolve()
            try:
                dest.relative_to(project_root.resolve())
            except ValueError:
                continue
            if not dest.exists():
                issues.append(ReflectIssue(rel_posix(path, project_root), "broken-link", f"missing local link target: {target}"))
    return issues


def check_command_tool_refs(project_root: Path) -> list[ReflectIssue]:
    issues: list[ReflectIssue] = []
    commands_dir = project_root / ".claude" / "commands"
    if not commands_dir.exists():
        return issues
    for path in sorted(commands_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        for match in TOOL_CMD_RE.finditer(text):
            rel_tool = "tools/" + match.group(1)
            if not (project_root / rel_tool).exists():
                issues.append(ReflectIssue(rel_posix(path, project_root), "missing-tool", f"command references missing {rel_tool}"))
    return issues


def reflect(project_root: Path) -> list[ReflectIssue]:
    issues: list[ReflectIssue] = []
    issues.extend(check_markdown_links(project_root))
    issues.extend(check_command_tool_refs(project_root))
    for ref_issue in check_references(project_root):
        issues.append(ReflectIssue(ref_issue.path, f"ref-{ref_issue.kind}", f"{ref_issue.ref}: {ref_issue.message}"))
    for memory_issue in check_memory(project_root):
        issues.append(ReflectIssue(memory_issue.path, f"memory-{memory_issue.code}", memory_issue.message))
    for pack_issue in lint_paths(active_task_packs(project_root), project_root):
        issues.append(ReflectIssue(pack_issue.path, f"pack-{pack_issue.code}", pack_issue.message))
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deterministic Trellis reflection checks")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--check", action="store_true", help="Alias for default fail-on-issues behavior")
    args = parser.parse_args()

    try:
        project_root = get_project_root(Path(__file__).resolve())
    except TrellisPathError as exc:
        print(f"[FAIL] reflect: {exc}", file=sys.stderr)
        return 1

    issues = reflect(project_root)
    payload = {"ok": not issues, "issues": [issue.__dict__ for issue in issues]}
    if args.json:
        print(json.dumps(payload, sort_keys=True))
        return 0 if not issues else 1
    if not issues:
        print("[OK] reflect: no deterministic issues found")
        return 0
    print(f"[FAIL] reflect: {len(issues)} issue(s)")
    for issue in issues:
        print(f"  {issue.path}: {issue.code} - {issue.message}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
