"""Authoritative Trellis install-surface model.

This module is shared by the installer and bootstrap manifest so the files
copied into host projects and the files recorded as expected remain in sync.
Source-repository files such as README, LICENSE, CI, and pyproject metadata are
intentionally excluded from host installs.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from tools.trellis_paths import has_trellis_memory

EXCLUDE_NAMES = {
    "__pycache__",
    ".pytest_cache",
    ".git",
    ".mypy_cache",
    ".ruff_cache",
}
EXCLUDE_SUFFIXES = {".pyc", ".pyo"}

# Paths that are generated state, public-repository metadata, host-reserved root
# docs, or development-only files. They are never installed into host projects.
SOURCE_ONLY_RELATIVE = {
    ".claude/GODFILE.md",
    ".claude/.session-state",
    ".claude/logs",
    ".claude/.cache",
    ".claude/trellis_install_manifest.json",
    ".github",
    "BLUEPRINT.md",
    "CHANGELOG.md",
    "CLAUDE.md",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "DECISIONS.md",
    "FINDINGS.md",
    "HARNESS.md",
    "LICENSE",
    "README.md",
    "SECURITY.md",
    "docs",
    "outputs",
    "pyproject.toml",
    "requirements-dev.txt",
    "runs",
    "setup.sh",
    ".gitignore",
}

INSTALL_PREFIXES = {
    ".claude",
    "memory",
    "task-packs",
    "tests",
    "tools",
    "trellis-docs",
}
INSTALL_ROOT_FILES = {"install_trellis.py"}

HOST_RESERVED_PATHS = {
    "README.md",
    "CLAUDE.md",
    "FINDINGS.md",
    "DECISIONS.md",
    "HARNESS.md",
    "runs/RUNS.md",
    "docs/TASK_PACK_GOLDPRINT.md",
    "docs/TRELLIS_REPAIR_LEDGER.md",
    "docs/TRELLIS_WORKFLOW_BLUEPRINT.md",
    "task-packs/README.md",
    ".gitignore",
}

# Directories that should exist even when a release snapshot contains only a
# placeholder or no files beneath them. Memory directories are conditional in
# installed hosts because root `memory/` can be host-owned.
MEMORY_REQUIRED_DIRS = [
    "memory",
    "memory/task-pack-authoring",
    "memory/harness-maintenance",
    "memory/oss-release",
    "memory/session-continuity",
]

BASE_REQUIRED_DIRS = [
    "trellis-docs",
    "task-packs",
    "task-packs/examples",
    "task-packs/archive",
    "task-packs/completed",
    "task-packs/done",
    "tools",
    "tools/trellis_templates",
    ".claude/hooks",
    ".claude/commands",
    ".claude/skills",
    ".claude/agents",
    ".claude/rules",
    ".claude/blueprints",
    ".claude/trellis-tests",
]

# Compatibility constant for older imports. Call `required_dirs()` when the
# source root is known so memory dirs can honor the sentinel contract.
REQUIRED_DIRS = [*MEMORY_REQUIRED_DIRS, *BASE_REQUIRED_DIRS]

DESTINATION_MAP = {
    "install_trellis.py": "tools/trellis_install.py",
}

SELF_TEST_SOURCE_PREFIX = "tests/"
SELF_TEST_DEST_PREFIX = ".claude/trellis-tests/"


@dataclass(frozen=True)
class InstallFile:
    source: Path
    source_rel: str
    dest_rel: str


def rel_posix(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _is_under_rel(rel: str, parent: str) -> bool:
    return rel == parent or rel.startswith(parent.rstrip("/") + "/")


def should_copy(path: Path, root: Path) -> bool:
    if path.is_symlink():
        return False
    rel = rel_posix(path, root)
    if any(part in EXCLUDE_NAMES for part in path.parts):
        return False
    if path.suffix in EXCLUDE_SUFFIXES:
        return False
    if _is_under_rel(rel, "memory") and not has_trellis_memory(root):
        return False
    if any(_is_under_rel(rel, item) for item in SOURCE_ONLY_RELATIVE):
        return False
    if rel in HOST_RESERVED_PATHS:
        return False
    if rel in INSTALL_ROOT_FILES:
        return True
    return any(_is_under_rel(rel, prefix) for prefix in INSTALL_PREFIXES)


def destination_for(source_rel: str) -> str:
    if source_rel in DESTINATION_MAP:
        return DESTINATION_MAP[source_rel]
    if source_rel.startswith(SELF_TEST_SOURCE_PREFIX):
        return SELF_TEST_DEST_PREFIX + source_rel[len(SELF_TEST_SOURCE_PREFIX) :]
    return source_rel


def iter_install_files(source_root: Path) -> list[InstallFile]:
    source_root = source_root.resolve()
    files: list[InstallFile] = []
    for path in source_root.rglob("*"):
        if path.is_symlink() or not path.is_file():
            continue
        if not should_copy(path, source_root):
            continue
        source_rel = rel_posix(path, source_root)
        files.append(InstallFile(path, source_rel, destination_for(source_rel)))
    return sorted(files, key=lambda item: item.dest_rel)


def expected_installed_files(source_root: Path) -> list[str]:
    return [item.dest_rel for item in iter_install_files(source_root)]


def required_dirs(source_root: Path | None = None) -> list[str]:
    dirs = set(BASE_REQUIRED_DIRS)
    if source_root is None or has_trellis_memory(source_root):
        dirs.update(MEMORY_REQUIRED_DIRS)
    return sorted(dirs)


def expected_installed_dirs(source_root: Path | None = None) -> list[str]:
    dirs = set(required_dirs(source_root))
    if source_root is not None:
        for item in iter_install_files(source_root):
            parent = Path(item.dest_rel).parent.as_posix()
            while parent and parent != ".":
                dirs.add(parent)
                parent = Path(parent).parent.as_posix()
    return sorted(dirs)


def is_source_only(rel: str) -> bool:
    return any(_is_under_rel(rel, item) for item in SOURCE_ONLY_RELATIVE)
