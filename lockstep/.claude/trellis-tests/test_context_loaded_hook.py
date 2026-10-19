from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from conftest import run_hook
from tools.trellis_paths import path_key


def write_reads(project_root: Path, session_id: str, reads: list[Path | str]) -> None:
    state_dir = project_root / ".claude" / ".session-state" / session_id
    state_dir.mkdir(parents=True, exist_ok=True)
    state_file = state_dir / "reads.json"
    state_file.write_text(json.dumps([path_key(p) for p in reads]), encoding="utf-8")


def edit_payload(project_root: Path, file_path: str | Path, session_id: str = "s1") -> dict:
    return {
        "tool_name": "Edit",
        "session_id": session_id,
        "cwd": str(project_root),
        "tool_input": {
            "file_path": str(file_path),
            "old_string": "hello",
            "new_string": "hello world",
        },
    }


def test_exact_root_context_files_allow_src_edit(repo_root, minimal_project):
    write_reads(minimal_project, "s1", [minimal_project / "trellis-docs/trellis-findings.md", minimal_project / "trellis-docs/trellis-decisions.md"])
    proc = run_hook(repo_root, minimal_project, "check_context_loaded.py", edit_payload(minimal_project, "src/main.py"))
    assert proc.returncode == 0, proc.stderr


def test_missing_findings_blocks(repo_root, minimal_project):
    write_reads(minimal_project, "s1", [minimal_project / "trellis-docs/trellis-decisions.md"])
    proc = run_hook(repo_root, minimal_project, "check_context_loaded.py", edit_payload(minimal_project, "src/main.py"))
    assert proc.returncode == 2
    assert "trellis-docs/trellis-findings.md" in proc.stderr


def test_missing_decisions_blocks(repo_root, minimal_project):
    write_reads(minimal_project, "s1", [minimal_project / "trellis-docs/trellis-findings.md"])
    proc = run_hook(repo_root, minimal_project, "check_context_loaded.py", edit_payload(minimal_project, "src/main.py"))
    assert proc.returncode == 2
    assert "trellis-docs/trellis-decisions.md" in proc.stderr


def test_matching_basenames_elsewhere_do_not_satisfy_requirement(repo_root, minimal_project, tmp_path):
    other = tmp_path / "other"
    other.mkdir()
    (other / "trellis-docs").mkdir()
    fake_findings = other / "trellis-docs/trellis-findings.md"
    fake_decisions = other / "trellis-docs/trellis-decisions.md"
    fake_findings.write_text("fake", encoding="utf-8")
    fake_decisions.write_text("fake", encoding="utf-8")
    write_reads(minimal_project, "s1", [fake_findings, fake_decisions])

    proc = run_hook(repo_root, minimal_project, "check_context_loaded.py", edit_payload(minimal_project, "src/main.py"))
    assert proc.returncode == 2


def test_relative_and_absolute_paths_work_when_real(repo_root, minimal_project):
    write_reads(minimal_project, "s1", [minimal_project / "trellis-docs/trellis-findings.md", minimal_project / "trellis-docs/trellis-decisions.md"])
    rel_proc = run_hook(repo_root, minimal_project, "check_context_loaded.py", edit_payload(minimal_project, "src/main.py"))
    abs_proc = run_hook(repo_root, minimal_project, "check_context_loaded.py", edit_payload(minimal_project, minimal_project / "src" / "main.py"))
    assert rel_proc.returncode == 0, rel_proc.stderr
    assert abs_proc.returncode == 0, abs_proc.stderr


def test_non_src_edit_is_not_blocked(repo_root, minimal_project):
    proc = run_hook(repo_root, minimal_project, "check_context_loaded.py", edit_payload(minimal_project, "README.md"))
    assert proc.returncode == 0, proc.stderr


def test_hook_imports_helpers_from_hook_root_not_env_shadow(repo_root, minimal_project):
    shadow_tools = minimal_project / "tools"
    shadow_tools.mkdir(exist_ok=True)
    (shadow_tools / "trellis_paths.py").write_text("raise RuntimeError('shadowed helper imported')\n", encoding="utf-8")
    write_reads(minimal_project, "s1", [minimal_project / "trellis-docs/trellis-findings.md", minimal_project / "trellis-docs/trellis-decisions.md"])

    env = os.environ.copy()
    env["TRELLIS_PROJECT_ROOT"] = str(minimal_project)
    env["PYTHONPATH"] = str(repo_root) + os.pathsep + env.get("PYTHONPATH", "")
    proc = subprocess.run(
        [sys.executable, str(repo_root / ".claude" / "hooks" / "check_context_loaded.py")],
        cwd=minimal_project,
        env=env,
        input=json.dumps(edit_payload(minimal_project, "src/main.py")),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=20,
    )

    assert proc.returncode == 0, proc.stderr
