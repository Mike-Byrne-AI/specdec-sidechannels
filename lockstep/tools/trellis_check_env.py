#!/usr/bin/env python3
"""Validate the local Trellis environment and installed harness layout.

Usage:
    python tools/trellis_check_env.py

The checker resolves the Trellis project root from this tool path or
`TRELLIS_PROJECT_ROOT`, so it reports the same layout when run from the project
root or a nested directory.
"""

from __future__ import annotations

import importlib
import os
import shutil
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from tools.trellis_paths import TrellisPathError, get_project_root  # noqa: E402

EXPECTED_FILES = [
    "tools/trellis_templates/CLAUDE.md.template",
    "tools/trellis_templates/gitignore.snippet",
    "trellis-docs/trellis-findings.md",
    "trellis-docs/trellis-decisions.md",
    "task-packs",
    ".claude/commands/trellis-bootstrap.md",
]

REQUIRED_PACKAGES = [
    ("pytest", "pytest"),
]

MIN_PYTHON = (3, 9)
PROJECT_USES_CUDA = False

if sys.stdout.isatty():
    OK = "\033[32m[OK]\033[0m"
    WARN = "\033[33m[WARN]\033[0m"
    FAIL = "\033[31m[FAIL]\033[0m"
else:
    OK, WARN, FAIL = "[OK]", "[WARN]", "[FAIL]"

CHECKS_PASSED = 0
CHECKS_FAILED = 0
WARNINGS = 0


def reset_counts() -> None:
    global CHECKS_PASSED, CHECKS_FAILED, WARNINGS
    CHECKS_PASSED = 0
    CHECKS_FAILED = 0
    WARNINGS = 0


def check(label: str, ok: bool, detail: str = "", fatal: bool = True) -> None:
    global CHECKS_PASSED, CHECKS_FAILED, WARNINGS
    if ok:
        print(f"  {OK}  {label}{(': ' + detail) if detail else ''}")
        CHECKS_PASSED += 1
    elif fatal:
        print(f"  {FAIL}  {label}{(': ' + detail) if detail else ''}")
        CHECKS_FAILED += 1
    else:
        print(f"  {WARN}  {label}{(': ' + detail) if detail else ''}")
        WARNINGS += 1


def run_check(project_root: Path, current_dir: Path) -> int:
    reset_counts()
    print("\nEnvironment check")
    print(f"Project root: {project_root}")
    print(f"Working dir: {current_dir}\n")

    print("Python")
    py_ok = sys.version_info >= MIN_PYTHON
    check(
        f"Python {sys.version_info.major}.{sys.version_info.minor}",
        py_ok,
        detail=("OK" if py_ok else f"need {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+"),
    )

    in_venv = (
        hasattr(sys, "real_prefix")
        or (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix)
        or os.environ.get("VIRTUAL_ENV") is not None
    )
    check(
        "Running inside a virtualenv",
        in_venv,
        detail=(sys.prefix if in_venv else "not in venv — packages may install to global Python"),
        fatal=False,
    )
    if not in_venv:
        print("    Hint: activate the project venv first. On Windows PowerShell:")
        print("      .\\.venv\\Scripts\\Activate.ps1")
        print("    On Linux/macOS:")
        print("      source .venv/bin/activate")
    print()

    if REQUIRED_PACKAGES:
        print("Required packages")
        for pkg, import_name in REQUIRED_PACKAGES:
            try:
                mod = importlib.import_module(import_name)
                version = getattr(mod, "__version__", "?")
                check(pkg, True, detail=f"version {version}")
            except ImportError as exc:
                check(pkg, False, detail=f"NOT installed ({exc})")
        print()

    if PROJECT_USES_CUDA:
        print("CUDA")
        try:
            import torch  # type: ignore

            cuda_available = torch.cuda.is_available()
            detail = (
                f"available, {torch.cuda.device_count()} device(s), {torch.cuda.get_device_name(0)}"
                if cuda_available
                else "not available (CPU only)"
            )
            check("CUDA", True, detail=detail, fatal=False)
        except ImportError:
            check("CUDA", True, detail="torch not installed, skipping", fatal=False)
        print()

    if EXPECTED_FILES:
        print("Project layout")
        for relative in EXPECTED_FILES:
            p = project_root / relative
            check(relative, p.exists(), detail=("present" if p.exists() else "MISSING"))
        print()

    print("Git")
    git_available = shutil.which("git") is not None
    check("git on PATH", git_available, fatal=False)
    if git_available:
        in_git_repo = (project_root / ".git").exists()
        status = "repo initialized" if in_git_repo else "not a git repo (OK for ad-hoc work)"
        print(f"  [OK]  git status: {status}")
        global CHECKS_PASSED
        CHECKS_PASSED += 1
    print()

    print("=" * 50)
    total = CHECKS_PASSED + CHECKS_FAILED + WARNINGS
    print(f"Summary: {CHECKS_PASSED}/{total} OK, {WARNINGS} warn, {CHECKS_FAILED} fail")

    if CHECKS_FAILED > 0:
        print("\nEnvironment has issues. Fix the [FAIL] items.")
        return 1
    if WARNINGS > 0:
        print("\nEnvironment is usable but has warnings.")
        return 0
    print("\nEnvironment is clean.")
    return 0


def main() -> int:
    try:
        project_root = get_project_root(Path(__file__).resolve())
    except TrellisPathError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return run_check(project_root, Path.cwd().resolve())


if __name__ == "__main__":
    sys.exit(main())
