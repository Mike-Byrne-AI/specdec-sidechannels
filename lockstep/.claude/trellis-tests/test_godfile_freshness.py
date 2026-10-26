from __future__ import annotations

import os
import time
from pathlib import Path

from conftest import run_hook
from tools.trellis_extract_godfile import build_godfile


def generate_godfile(repo_root: Path, project_root: Path) -> None:
    del repo_root
    out = project_root / ".claude" / "GODFILE.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build_godfile(project_root), encoding="utf-8")


def touch_newer(path: Path) -> None:
    now = time.time() + 5
    os.utime(path, (now, now))


def append_without_newer_mtime(path: Path, text: str) -> None:
    before = path.stat().st_mtime
    path.write_text(path.read_text(encoding="utf-8") + text, encoding="utf-8")
    os.utime(path, (before, before))


def src_edit_payload(project_root: Path) -> dict:
    return {
        "tool_name": "Edit",
        "session_id": "s1",
        "cwd": str(project_root),
        "tool_input": {
            "file_path": str(project_root / "src" / "main.py"),
            "old_string": "hello",
            "new_string": "hello world",
        },
    }


def test_fresh_godfile_permits_src_edit(repo_root, minimal_project):
    generate_godfile(repo_root, minimal_project)
    proc = run_hook(repo_root, minimal_project, "check_godfile_fresh.py", src_edit_payload(minimal_project))
    assert proc.returncode == 0, proc.stderr


def test_missing_godfile_blocks_src_edit(repo_root, minimal_project):
    proc = run_hook(repo_root, minimal_project, "check_godfile_fresh.py", src_edit_payload(minimal_project))
    assert proc.returncode == 2
    assert "GODFILE.md does not exist" in proc.stderr


def test_modified_core_sources_block_even_without_newer_mtime(repo_root, minimal_project):
    changes = {
        "trellis-docs/trellis-findings.md": "\n### F1 - changed finding\nObserved.\n",
        "trellis-docs/trellis-decisions.md": "\n## D-1 - changed decision [imagined]\nText.\n",
        "trellis-docs/trellis-runs.md": "\n| run_001 | ok |\n",
    }
    for relative, addition in changes.items():
        generate_godfile(repo_root, minimal_project)
        append_without_newer_mtime(minimal_project / relative, addition)
        proc = run_hook(repo_root, minimal_project, "check_godfile_fresh.py", src_edit_payload(minimal_project))
        assert proc.returncode == 2, relative


def test_new_active_task_pack_blocks(repo_root, minimal_project):
    generate_godfile(repo_root, minimal_project)
    active = minimal_project / "task-packs" / "TP-9_new.md"
    active.write_text("# new work\n", encoding="utf-8")
    proc = run_hook(repo_root, minimal_project, "check_godfile_fresh.py", src_edit_payload(minimal_project))
    assert proc.returncode == 2
    assert "TP-9_new.md" in proc.stderr


def test_modified_example_or_archived_pack_does_not_block(repo_root, minimal_project):
    generate_godfile(repo_root, minimal_project)
    example = minimal_project / "task-packs" / "examples" / "TP-0_example.md"
    archived = minimal_project / "task-packs" / "archive" / "TP-2_old.md"
    example.write_text("# example\n", encoding="utf-8")
    archived.write_text("# old\n", encoding="utf-8")
    append_without_newer_mtime(example, "changed example\n")
    append_without_newer_mtime(archived, "changed archive\n")
    proc = run_hook(repo_root, minimal_project, "check_godfile_fresh.py", src_edit_payload(minimal_project))
    assert proc.returncode == 0, proc.stderr
