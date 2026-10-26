from __future__ import annotations

import importlib.util
import io
import json
import os
import sys
import types
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import pytest

from tools.trellis_paths import get_project_root


@pytest.fixture
def repo_root() -> Path:
    return get_project_root(Path(__file__).resolve())


@pytest.fixture
def minimal_project(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    (root / ".claude" / ".session-state").mkdir(parents=True)
    (root / "trellis-docs").mkdir()
    (root / "task-packs" / "examples").mkdir(parents=True)
    (root / "task-packs" / "archive").mkdir()
    (root / "task-packs" / "completed").mkdir()
    (root / "task-packs" / "done").mkdir()
    (root / "src").mkdir()
    (root / ".claude" / "settings.json").write_text("{}\n", encoding="utf-8")
    (root / "tools" / "trellis_templates").mkdir(parents=True)
    (root / "tools" / "trellis_templates" / "CLAUDE.md.template").write_text("# Project\n", encoding="utf-8")
    (root / "tools" / "trellis_templates" / "gitignore.snippet").write_text(".claude/GODFILE.md\n", encoding="utf-8")
    (root / "trellis-docs" / "trellis-findings.md").write_text("# Findings\n", encoding="utf-8")
    (root / "trellis-docs" / "trellis-decisions.md").write_text("# Decisions\n", encoding="utf-8")
    (root / "trellis-docs" / "trellis-runs.md").write_text("# Runs\n", encoding="utf-8")
    (root / "src" / "main.py").write_text("print('hello')\n", encoding="utf-8")
    return root


def hook_env(repo_root: Path, project_root: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["TRELLIS_PROJECT_ROOT"] = str(project_root)
    env["PYTHONPATH"] = str(repo_root) + os.pathsep + env.get("PYTHONPATH", "")
    return env


def _load_hook_module(path: Path):
    module_name = f"_trellis_hook_test_{path.stem}_{id(path)}_{os.urandom(4).hex()}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_hook(repo_root: Path, project_root: Path, hook_name: str, payload: dict):
    hook_path = repo_root / ".claude" / "hooks" / hook_name
    old_env = os.environ.copy()
    old_stdin = sys.stdin
    stdout = io.StringIO()
    stderr = io.StringIO()
    try:
        os.environ["TRELLIS_PROJECT_ROOT"] = str(project_root)
        if str(repo_root) not in sys.path:
            sys.path.insert(0, str(repo_root))
        module = _load_hook_module(hook_path)
        sys.stdin = io.StringIO(json.dumps(payload))
        with redirect_stdout(stdout), redirect_stderr(stderr):
            returncode = module.main()
    finally:
        sys.stdin = old_stdin
        os.environ.clear()
        os.environ.update(old_env)
    return types.SimpleNamespace(returncode=returncode, stdout=stdout.getvalue(), stderr=stderr.getvalue())
