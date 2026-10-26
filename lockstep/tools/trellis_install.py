#!/usr/bin/env python3
"""Install the Trellis harness into a target project directory.

Default behavior is host-friendly and merge-oriented: Trellis assets install
under `.claude/`, `tools/`, `trellis-docs/`, `memory/`, and `task-packs/`, while
root host files such as `CLAUDE.md`, `.gitignore`, and public repository metadata
are not copied. Existing target files are skipped by default. Use
`--overwrite-trellis` only when you intentionally want Trellis-managed collisions
replaced after a `.host-backup` copy is created.

Run `/trellis-bootstrap` after install to integrate root `CLAUDE.md` and
`.gitignore` with explicit permission.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent
if _PROJECT_ROOT.name == "tools":
    _PROJECT_ROOT = _PROJECT_ROOT.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from tools.trellis_install_surface import (  # noqa: E402
    iter_install_files,
    required_dirs,
)
from tools.trellis_paths import (  # noqa: E402
    TRELLIS_MEMORY_REL,
    first_symlink_in_path,
    has_trellis_memory,
    rel_or_name,
)


def _rel_is_under(rel: str, parent: str) -> bool:
    return rel == parent or rel.startswith(parent.rstrip("/") + "/")


def should_skip_memory_install(target: Path) -> bool:
    """Return True when target has a host-owned root memory directory.

    `memory/` is a deliberately generic name. To avoid silently mixing Trellis
    internal notes into a host project's own memory store, copy Trellis memory
    only when the path is absent or already carries the Trellis sentinel as a
    normal in-repo directory.
    """
    memory_dir = target / TRELLIS_MEMORY_REL
    if not memory_dir.exists():
        return False
    return not has_trellis_memory(target)


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def validate_target(source_root: Path, target: Path) -> str | None:
    source_root = source_root.resolve()
    target = target.resolve()
    if target == source_root:
        return "target must not be the Trellis source/template directory"
    if _is_relative_to(target, source_root):
        return "target must not be nested inside the Trellis source/template directory"
    return None


def next_backup_path(path: Path) -> Path:
    candidate = path.with_name(path.name + ".host-backup")
    if not candidate.exists():
        return candidate
    i = 1
    while True:
        numbered = path.with_name(path.name + f".host-backup-{i}")
        if not numbered.exists():
            return numbered
        i += 1


def backup_existing(dst: Path, dry_run: bool) -> Path | None:
    if not dst.exists():
        return None
    backup = next_backup_path(dst)
    if not dry_run:
        backup.parent.mkdir(parents=True, exist_ok=True)
        if dst.is_dir():
            shutil.copytree(dst, backup)
        else:
            shutil.copy2(dst, backup)
    return backup


def copy_file(src: Path, dst: Path, dry_run: bool) -> None:
    if dry_run:
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def install(
    source_root: Path,
    target: Path,
    force: bool = False,
    dry_run: bool = False,
    overwrite_trellis: bool | None = None,
) -> int:
    """Install Trellis into target.

    `force` is kept as a compatibility alias for `overwrite_trellis`; new code
    should pass `overwrite_trellis=True` for backup-and-overwrite behavior.
    """
    source_root = source_root.resolve()
    target = target.resolve()
    overwrite = bool(force if overwrite_trellis is None else overwrite_trellis)

    blocked = validate_target(source_root, target)
    if blocked:
        print(f"ERROR: {blocked}: {target}")
        return 1

    entries = iter_install_files(source_root)
    source_has_memory = has_trellis_memory(source_root)
    target_skips_memory = should_skip_memory_install(target)
    skip_memory = target_skips_memory or not source_has_memory
    if target_skips_memory:
        print("[SKIP] host-owned or unmarked memory/ path exists; internal memory files not installed")
    elif not source_has_memory:
        print("[SKIP] source has no Trellis memory sentinel; internal memory files not installed")

    if not dry_run:
        target.mkdir(parents=True, exist_ok=True)
        for dirname in required_dirs(source_root):
            if skip_memory and _rel_is_under(dirname, "memory"):
                continue
            dir_path = target / dirname
            link = first_symlink_in_path(dir_path, target)
            if link is not None:
                print(f"[SKIP] symlink path: {dirname} (via {rel_or_name(link, target)})")
                continue
            dir_path.mkdir(parents=True, exist_ok=True)

    copied = 0
    skipped = 0
    backed_up = 0
    for item in entries:
        if skip_memory and _rel_is_under(item.dest_rel, "memory"):
            print(f"[SKIP] host-owned memory/: {item.dest_rel}")
            skipped += 1
            continue
        dst = target / item.dest_rel
        link = first_symlink_in_path(dst, target)
        if link is not None:
            print(f"[SKIP] symlink path: {item.dest_rel} (via {rel_or_name(link, target)})")
            skipped += 1
            continue

        if dst.exists() and not overwrite:
            print(f"[SKIP] exists: {item.dest_rel}")
            skipped += 1
            continue
        if dst.exists() and overwrite:
            backup = backup_existing(dst, dry_run)
            if backup is not None:
                action = "would back up" if dry_run else "backed up"
                print(
                    f"[BACKUP] {action}: {item.dest_rel} -> "
                    f"{backup.relative_to(target).as_posix()}"
                )
                backed_up += 1
        action = "would copy" if dry_run else "copied"
        print(f"[OK] {action}: {item.dest_rel}")
        copy_file(item.source, dst, dry_run)
        copied += 1

    print(f"Summary: {copied} copied, {skipped} skipped, {backed_up} backed up")
    if not dry_run:
        print("Next steps:")
        print(f"  cd {target}")
        print("  python tools/trellis_bootstrap.py --yes")
        print("  python tools/trellis_check_env.py")
        print("  python tools/trellis_extract_godfile.py")
        print("  python tools/trellis_repair_gate.py")
        print(
            "Host docs were not renamed or overwritten. Run trellis_bootstrap.py "
            "to opt into root CLAUDE.md/.gitignore integration."
        )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Install Trellis into a target project")
    parser.add_argument("target", help="Target project directory")
    parser.add_argument(
        "--overwrite-trellis",
        action="store_true",
        help="Overwrite existing Trellis-managed collisions after creating .host-backup files",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Deprecated alias for --overwrite-trellis",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print actions without copying or creating directories")
    args = parser.parse_args()

    here = Path(__file__).resolve().parent
    source_root = here.parent if here.name == "tools" else here
    overwrite = args.overwrite_trellis or args.force
    if args.force and not args.overwrite_trellis:
        print("[WARN] --force is deprecated; use --overwrite-trellis for backup-and-overwrite installs.")
    return install(source_root, Path(args.target), dry_run=args.dry_run, overwrite_trellis=overwrite)


if __name__ == "__main__":
    sys.exit(main())
