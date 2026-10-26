"""Shared path and source-discovery helpers for Trellis.

Keep all generated-state truth here so the extractor and hooks agree about
which files matter. Functions are intentionally small and dependency-free.
"""

from __future__ import annotations

import os
from pathlib import Path

TRELLIS_DOCS_DIR = "trellis-docs"
TRELLIS_FINDINGS_REL = "trellis-docs/trellis-findings.md"
TRELLIS_DECISIONS_REL = "trellis-docs/trellis-decisions.md"
TRELLIS_RUNS_REL = "trellis-docs/trellis-runs.md"
TRELLIS_HARNESS_REL = "trellis-docs/trellis-harness.md"
TRELLIS_MEMORY_REL = "memory"
TRELLIS_MEMORY_SENTINEL_REL = "memory/.trellis-memory"

ROOT_MARKERS = (".claude/settings.json", TRELLIS_FINDINGS_REL, TRELLIS_DECISIONS_REL)
SOURCE_LAYOUT_MARKERS = (
    "install_trellis.py",
    "BLUEPRINT.md",
    "CHANGELOG.md",
    "pyproject.toml",
    "requirements-dev.txt",
    "tests/conftest.py",
    "tests/test_public_project_surface.py",
)


def has_root_markers(root: str | Path) -> bool:
    candidate = Path(root).resolve()
    return all((candidate / marker).exists() for marker in ROOT_MARKERS)


def is_source_layout(project_root: str | Path) -> bool:
    """Return True for the Trellis source checkout, not an installed host.

    Installed hosts receive `install_trellis.py`, and many real projects already
    have a root `tests/conftest.py`. Source detection therefore also requires
    several source-only release files that the installer intentionally excludes.
    """
    root = Path(project_root).resolve()
    return has_root_markers(root) and all((root / marker).exists() for marker in SOURCE_LAYOUT_MARKERS)


ACTIVE_PACK_PREFIX = "TP-"
ACTIVE_PACK_SUFFIX = ".md"
EXCLUDED_PACK_DIRS = {"examples", "archive", "archives", "completed", "done"}
EXCLUDED_PACK_NAME_PARTS = {"example", "template", "archived", "completed"}


class TrellisPathError(RuntimeError):
    """Raised when the Trellis project root or source paths cannot be resolved."""


def _candidate_start(start: str | Path | None) -> Path:
    if start is None:
        return Path.cwd().resolve()
    p = Path(start).resolve()
    if p.is_file():
        return p.parent
    return p


def get_project_root(start: str | Path | None = None) -> Path:
    """Return the Trellis project root.

    `TRELLIS_PROJECT_ROOT` is honored first to make hook and script tests easy.
    Otherwise the function walks upward from `start` until it finds the Trellis
    markers. Trellis markers intentionally live under `trellis-docs/` and
    `.claude/` so host project docs can keep their original names.
    """
    env_root = os.environ.get("TRELLIS_PROJECT_ROOT")
    if env_root:
        root = Path(env_root).resolve()
        if not root.exists():
            raise TrellisPathError(f"TRELLIS_PROJECT_ROOT does not exist: {root}")
        if has_root_markers(root):
            return root
        raise TrellisPathError(f"TRELLIS_PROJECT_ROOT is not a Trellis project root: {root}")

    current = _candidate_start(start)
    candidates = [current, *current.parents]
    for candidate in candidates:
        if has_root_markers(candidate):
            return candidate
    raise TrellisPathError(f"could not find Trellis project root from {current}")


def trellis_docs_dir(project_root: str | Path) -> Path:
    return Path(project_root).resolve() / TRELLIS_DOCS_DIR


def findings_path(project_root: str | Path) -> Path:
    return Path(project_root).resolve() / TRELLIS_FINDINGS_REL


def decisions_path(project_root: str | Path) -> Path:
    return Path(project_root).resolve() / TRELLIS_DECISIONS_REL


def runs_path(project_root: str | Path) -> Path:
    return Path(project_root).resolve() / TRELLIS_RUNS_REL


def memory_dir(project_root: str | Path) -> Path:
    return Path(project_root).resolve() / TRELLIS_MEMORY_REL


def memory_sentinel_path(project_root: str | Path) -> Path:
    return Path(project_root).resolve() / TRELLIS_MEMORY_SENTINEL_REL


def has_trellis_memory(project_root: str | Path) -> bool:
    """Return True only when root `memory/` is marked as Trellis-owned.

    A plain root `memory/` directory is a common host-project name. Trellis
    treats it as host-owned unless the sentinel file is present. Symlinks are
    not treated as Trellis memory so tools do not accidentally follow a generic
    host path outside the repository boundary.
    """
    root = Path(project_root).resolve()
    mem = root / TRELLIS_MEMORY_REL
    sentinel = root / TRELLIS_MEMORY_SENTINEL_REL
    return (
        mem.exists()
        and mem.is_dir()
        and not mem.is_symlink()
        and sentinel.is_file()
        and not sentinel.is_symlink()
    )


def path_key(path: str | Path) -> str:
    """Return a stable absolute comparison key for paths.

    On Windows this normalizes case. On other platforms it is a no-op beyond
    absolute resolution.
    """
    return os.path.normcase(str(Path(path).resolve()))


def resolve_tool_path(raw_path: str | Path, project_root: Path, cwd: str | Path | None = None) -> Path:
    """Resolve a Claude Code tool path against the hook cwd or project root."""
    p = Path(raw_path)
    if p.is_absolute():
        return p.resolve()
    base = Path(cwd).resolve() if cwd else project_root.resolve()
    return (base / p).resolve()


def is_under(path: str | Path, parent: str | Path) -> bool:
    try:
        Path(path).resolve().relative_to(Path(parent).resolve())
        return True
    except ValueError:
        return False


def rel_posix(path: str | Path, root: str | Path) -> str:
    return Path(path).resolve().relative_to(Path(root).resolve()).as_posix()


def first_symlink_in_path(path: str | Path, root: str | Path) -> Path | None:
    """Return the first symlink at or below root in path, without resolving path."""
    root_path = Path(root).resolve()
    path_obj = Path(path)
    if not path_obj.is_absolute():
        path_obj = root_path / path_obj
    try:
        rel = path_obj.relative_to(root_path)
    except ValueError:
        return path_obj
    current = root_path
    for part in rel.parts:
        current = current / part
        if current.is_symlink():
            return current
    return None


def rel_or_name(path: str | Path, root: str | Path) -> str:
    root_path = Path(root).resolve()
    path_obj = Path(path)
    if not path_obj.is_absolute():
        path_obj = root_path / path_obj
    try:
        return path_obj.relative_to(root_path).as_posix()
    except ValueError:
        return path_obj.name


def is_active_task_pack(path: str | Path, project_root: str | Path) -> bool:
    """Return True only for executable top-level task-pack files."""
    root = Path(project_root).resolve()
    task_packs_dir = root / "task-packs"
    p = Path(path).resolve()

    if not p.is_file():
        return False
    try:
        rel = p.relative_to(task_packs_dir)
    except ValueError:
        return False

    # Active packs are top-level only. Nested examples/archive/completed are out.
    if len(rel.parts) != 1:
        if rel.parts and rel.parts[0].lower() in EXCLUDED_PACK_DIRS:
            return False
        return False

    name = p.name
    name_lower = name.lower()
    if not (name.startswith(ACTIVE_PACK_PREFIX) and name.endswith(ACTIVE_PACK_SUFFIX)):
        return False
    if any(part in name_lower for part in EXCLUDED_PACK_NAME_PARTS):
        return False
    return True


def active_task_packs(project_root: str | Path) -> list[Path]:
    """Return active top-level task packs sorted by filename."""
    root = Path(project_root).resolve()
    task_packs_dir = root / "task-packs"
    if not task_packs_dir.exists():
        return []
    return sorted(
        (p for p in task_packs_dir.iterdir() if is_active_task_pack(p, root)),
        key=lambda p: p.name,
    )


def example_task_packs(project_root: str | Path) -> list[Path]:
    root = Path(project_root).resolve()
    examples_dir = root / "task-packs" / "examples"
    if not examples_dir.exists():
        return []
    return sorted(examples_dir.glob("*.md"), key=lambda p: p.name)


def done_task_packs(project_root: str | Path) -> list[Path]:
    root = Path(project_root).resolve()
    out: list[Path] = []
    for dirname in ("done", "completed"):
        d = root / "task-packs" / dirname
        if d.exists():
            out.extend(p for p in d.glob("*.md") if p.is_file())
    return sorted(out, key=lambda p: (p.parent.name, p.name))


def godfile_sources(project_root: str | Path) -> list[Path]:
    """Return all source files summarized by .claude/GODFILE.md."""
    root = Path(project_root).resolve()
    sources = [
        findings_path(root),
        decisions_path(root),
        runs_path(root),
    ]
    sources.extend(active_task_packs(root))
    return [p for p in sources if p.exists()]


def newest_source_newer_than(target: Path, sources: list[Path]) -> list[Path]:
    """Return sources newer than target. Missing/unreadable sources are callers' concern."""
    target_mtime = target.stat().st_mtime
    return [p for p in sources if p.stat().st_mtime > target_mtime]
