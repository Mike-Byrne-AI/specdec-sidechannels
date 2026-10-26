#!/usr/bin/env python3
"""Run the local Trellis repair/release verification gate."""

from __future__ import annotations

import argparse
import compileall
import contextlib
import importlib
import io
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.trellis_paths import is_source_layout  # noqa: E402

COMMANDS = [
    ("compile", [sys.executable, "-m", "compileall", "-q", "tools", ".claude/hooks"]),
    ("tests", [sys.executable, "-m", "pytest", "-q"]),
    ("inventory", [sys.executable, "tools/trellis_inventory.py", "--check"]),
    ("memory-lint", [sys.executable, "tools/trellis_memory_lint.py"]),
    ("pack-lint", [sys.executable, "tools/trellis_pack_lint.py"]),
    ("refs", [sys.executable, "tools/trellis_refs.py"]),
    ("reflect", [sys.executable, "tools/trellis_reflect.py", "--check"]),
    ("godfile-generate", [sys.executable, "tools/trellis_extract_godfile.py"]),
    ("godfile-check", [sys.executable, "tools/trellis_extract_godfile.py", "--check"]),
    ("env", [sys.executable, "tools/trellis_check_env.py"]),
]

IN_PROCESS = {
    "inventory": ("tools.trellis_inventory", ["trellis_inventory.py", "--check"]),
    "memory-lint": ("tools.trellis_memory_lint", ["trellis_memory_lint.py"]),
    "pack-lint": ("tools.trellis_pack_lint", ["trellis_pack_lint.py"]),
    "refs": ("tools.trellis_refs", ["trellis_refs.py"]),
    "reflect": ("tools.trellis_reflect", ["trellis_reflect.py", "--check"]),
    "godfile-generate": ("tools.trellis_extract_godfile", ["trellis_extract_godfile.py"]),
    "godfile-check": ("tools.trellis_extract_godfile", ["trellis_extract_godfile.py", "--check"]),
    "env": ("tools.trellis_check_env", ["trellis_check_env.py"]),
}

INCLUDE_HOST_TESTS = False


def _print_output(text: str | None) -> None:
    if text:
        print(text, end="" if text.endswith("\n") else "\n", flush=True)


def trellis_test_paths(project_root: Path, include_host_tests: bool = False) -> list[str]:
    if is_source_layout(project_root):
        return ["tests"]
    installed = project_root / ".claude" / "trellis-tests"
    paths: list[str] = []
    if installed.exists():
        paths.append(".claude/trellis-tests")
    if include_host_tests and (project_root / "tests").exists():
        paths.append("tests")
    return paths


def pytest_command(project_root: Path, include_host_tests: bool = False) -> list[str]:
    paths = trellis_test_paths(project_root, include_host_tests=include_host_tests)
    return [sys.executable, "-m", "pytest", "-q", *paths]


def run_compile() -> bool:
    ok_tools = compileall.compile_dir(PROJECT_ROOT / "tools", quiet=1)
    ok_hooks = compileall.compile_dir(PROJECT_ROOT / ".claude" / "hooks", quiet=1)
    return bool(ok_tools and ok_hooks)


def run_pytest(command: list[str]) -> bool:
    env = os.environ.copy()
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    env["PYTHONPATH"] = str(PROJECT_ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    if len(command) <= 4:
        command = pytest_command(PROJECT_ROOT, include_host_tests=INCLUDE_HOST_TESTS)
    if len(command) <= 4:
        print("[WARN] tests: no Trellis self-tests found", flush=True)
        return True
    try:
        # Use DEVNULL rather than a pipe. Some self-tests spawn subprocesses,
        # and inherited pipe descriptors can keep communicate() waiting for EOF
        # after the immediate pytest child exits. The gate prints labels and
        # pass/fail status; rerun pytest directly for detailed test output.
        proc = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            text=True,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
            timeout=120,
        )
    except subprocess.TimeoutExpired as exc:
        _print_output(exc.stdout)
        print("[FAIL] tests: timed out", flush=True)
        return False
    _print_output(proc.stdout)
    return proc.returncode == 0


def run_module_main(module_name: str, argv: list[str]) -> bool:
    old_argv = sys.argv[:]
    old_cwd = Path.cwd()
    stdout = io.StringIO()
    stderr = io.StringIO()
    try:
        os.chdir(PROJECT_ROOT)
        sys.argv = argv[:]
        module = importlib.import_module(module_name)
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            try:
                result = module.main()
            except SystemExit as exc:
                result = exc.code
    finally:
        sys.argv = old_argv
        os.chdir(old_cwd)
    _print_output(stdout.getvalue())
    _print_output(stderr.getvalue())
    return int(result or 0) == 0


def run_command(label: str, command: list[str]) -> bool:
    if label == "tests":
        command = pytest_command(PROJECT_ROOT, include_host_tests=INCLUDE_HOST_TESTS)
    print(f"[RUN] {label}: {' '.join(command)}", flush=True)

    if label == "compile":
        ok = run_compile()
    elif label == "tests":
        ok = run_pytest(command)
    elif label in IN_PROCESS:
        module_name, argv = IN_PROCESS[label]
        ok = run_module_main(module_name, argv)
    else:
        proc = subprocess.run(command, cwd=PROJECT_ROOT, text=True)
        ok = proc.returncode == 0

    if ok:
        print(f"[OK] {label}", flush=True)
        return True
    print(f"[FAIL] {label}", flush=True)
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Trellis verification gate")
    parser.add_argument("--list", action="store_true", help="List checks without running them")
    parser.add_argument("--include-host-tests", action="store_true", help="Also run host root tests/ in installed layout")
    args = parser.parse_args()

    global INCLUDE_HOST_TESTS
    INCLUDE_HOST_TESTS = args.include_host_tests

    if args.list:
        for label, command in COMMANDS:
            if label == "tests":
                command = pytest_command(PROJECT_ROOT, include_host_tests=INCLUDE_HOST_TESTS)
            print(f"{label}: {' '.join(command)}")
        return 0

    ok = True
    for label, command in COMMANDS:
        ok = run_command(label, command) and ok
    if ok:
        print("[OK] Trellis repair gate passed", flush=True)
        return 0
    print("[FAIL] Trellis repair gate failed", flush=True)
    return 1


if __name__ == "__main__":
    sys.exit(main())
