#!/usr/bin/env python3
"""Run the Trellis OSS release-candidate gate.

The gate validates both the source checkout and a freshly installed host target
created in a temporary directory. It performs no network access and no remote
git operations.
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@dataclass(frozen=True)
class Step:
    label: str
    command: list[str]
    cwd: Path


@dataclass(frozen=True)
class StepResult:
    label: str
    ok: bool
    returncode: int
    output: str


def run_step(step: Step, *, timeout: int = 180) -> StepResult:
    print(f"[RUN] {step.label}: {' '.join(step.command)}", flush=True)
    env = os.environ.copy()
    env["PYTHONPATH"] = str(step.cwd) + os.pathsep + env.get("PYTHONPATH", "")
    if "pytest" in " ".join(step.command):
        env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"

    # Use DEVNULL rather than a pipe. Some test subprocesses can leave inherited
    # pipe file descriptors open after the immediate child exits, which makes
    # communicate() wait for EOF even though the command has effectively
    # finished. The release gate reports labels and exit codes; individual
    # commands can be rerun directly for detailed output.
    proc = subprocess.Popen(
        step.command,
        cwd=step.cwd,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
        start_new_session=(os.name != "nt"),
    )
    output = ""
    deadline = time.monotonic() + timeout
    next_notice = time.monotonic() + 2
    returncode: int | None = None
    while returncode is None:
        returncode = proc.poll()
        if returncode is not None:
            break
        now = time.monotonic()
        if now >= deadline:
            output = "[TIMEOUT] step exceeded timeout"
            print(output, flush=True)
            if os.name != "nt":
                os.killpg(proc.pid, signal.SIGTERM)
            else:
                proc.terminate()
            try:
                returncode = proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                if os.name != "nt":
                    os.killpg(proc.pid, signal.SIGKILL)
                else:
                    proc.kill()
                returncode = proc.wait()
            returncode = 124
            break
        if now >= next_notice:
            print(f"[WAIT] {step.label} still running", flush=True)
            next_notice = now + 2
        time.sleep(0.2)

    ok = returncode == 0
    print(f"[{'OK' if ok else 'FAIL'}] {step.label}", flush=True)
    return StepResult(step.label, ok, returncode, output)


def verify_manifest(project_root: Path) -> StepResult:
    label = "installed-manifest"
    path = project_root / ".claude" / "trellis_install_manifest.json"
    print(f"[RUN] {label}: verify {path.relative_to(project_root)}", flush=True)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        expected = payload.get("expected_files", [])
        missing = [rel for rel in expected if not (project_root / rel).exists()]
        recorded_missing = payload.get("missing_files", [])
    except (OSError, json.JSONDecodeError) as exc:
        output = f"manifest unreadable: {exc}"
        print(output)
        print(f"[FAIL] {label}")
        return StepResult(label, False, 1, output)
    if missing or recorded_missing:
        output = f"missing={missing}; recorded_missing={recorded_missing}"
        print(output)
        print(f"[FAIL] {label}")
        return StepResult(label, False, 1, output)
    output = f"{len(expected)} expected files present"
    print(output)
    print(f"[OK] {label}")
    return StepResult(label, True, 0, output)


def source_preflight_steps(project_root: Path) -> list[Step]:
    """Source checks that should run before exercising installer paths.

    Pytest and the source repair gate are run separately by CI before this
    release gate. This preflight keeps source integrity checks close to the
    installer smoke test without duplicating the full source test suite.
    """
    py = sys.executable
    return [
        Step("source-compile", [py, "-m", "compileall", "-q", "install_trellis.py", "tools", ".claude/hooks"], project_root),
        Step("source-inventory", [py, "tools/trellis_inventory.py", "--check"], project_root),
        Step("source-memory-lint", [py, "tools/trellis_memory_lint.py"], project_root),
        Step("source-pack-lint", [py, "tools/trellis_pack_lint.py"], project_root),
        Step("source-refs", [py, "tools/trellis_refs.py"], project_root),
        Step("source-reflect", [py, "tools/trellis_reflect.py", "--check"], project_root),
        Step("source-godfile-generate", [py, "tools/trellis_extract_godfile.py"], project_root),
        Step("source-godfile-check", [py, "tools/trellis_extract_godfile.py", "--check"], project_root),
    ]


def source_final_steps(project_root: Path) -> list[Step]:
    py = sys.executable
    return [
        Step("source-pytest-module", [py, "-m", "pytest", "-q"], project_root),
        Step("source-pytest-console", ["pytest", "-q"], project_root),
        Step("source-repair-gate", [py, "tools/trellis_repair_gate.py"], project_root),
    ]


def installed_steps(project_root: Path) -> list[Step]:
    py = sys.executable
    return [
        Step("installed-bootstrap", [py, "tools/trellis_bootstrap.py", "--yes"], project_root),
        Step("installed-repair-gate", [py, "tools/trellis_repair_gate.py"], project_root),
    ]


def run_release_gate(project_root: Path = PROJECT_ROOT, *, include_source_tests: bool = False) -> list[StepResult]:
    results: list[StepResult] = []
    for step in source_preflight_steps(project_root):
        results.append(run_step(step))
        if not results[-1].ok:
            return results

    with tempfile.TemporaryDirectory(prefix="trellis-oss-gate-") as tmp:
        tmp_root = Path(tmp)
        dry_target = tmp_root / "dry-run-host"
        install_target = tmp_root / "installed-host"
        py = sys.executable
        for step in [
            Step("installer-dry-run", [py, "install_trellis.py", str(dry_target), "--dry-run"], project_root),
            Step("fresh-install", [py, "install_trellis.py", str(install_target)], project_root),
        ]:
            results.append(run_step(step))
            if not results[-1].ok:
                return results
        if dry_target.exists():
            results.append(StepResult("installer-dry-run-no-write", False, 1, "dry-run target was created"))
            print("[FAIL] installer-dry-run-no-write: dry-run target was created")
            return results
        print("[OK] installer-dry-run-no-write: target was not created")
        results.append(StepResult("installer-dry-run-no-write", True, 0, "target was not created"))

        for step in installed_steps(install_target):
            results.append(run_step(step))
            if not results[-1].ok:
                return results
            if step.label == "installed-bootstrap":
                results.append(verify_manifest(install_target))
                if not results[-1].ok:
                    return results

    if include_source_tests:
        for step in source_final_steps(project_root):
            results.append(run_step(step))
            if not results[-1].ok:
                return results

    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Trellis OSS release-candidate gate")
    parser.add_argument("--json", action="store_true", help="Emit JSON summary after running")
    parser.add_argument(
        "--include-source-tests",
        action="store_true",
        help="Also run source pytest/repair checks inside this gate. CI normally runs them separately before this script.",
    )
    args = parser.parse_args()

    results = run_release_gate(PROJECT_ROOT, include_source_tests=args.include_source_tests)
    ok = all(result.ok for result in results)
    if args.json:
        print(json.dumps({"ok": ok, "steps": [result.__dict__ for result in results]}, sort_keys=True))
    if ok:
        print("[OK] Trellis OSS release gate passed")
        return 0
    print("[FAIL] Trellis OSS release gate failed")
    return 1


if __name__ == "__main__":
    sys.exit(main())
