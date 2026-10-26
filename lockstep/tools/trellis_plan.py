#!/usr/bin/env python3
"""Small execution-plan tracker for Trellis command workflows."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from tools.trellis_paths import TrellisPathError, get_project_root  # noqa: E402

VALID_STATUSES = {"pending", "running", "passed", "failed", "blocked"}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def plan_path(project_root: Path) -> Path:
    return project_root / ".claude" / "trellis_plan.json"


def read_plan(project_root: Path) -> dict[str, Any] | None:
    path = plan_path(project_root)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def write_plan(project_root: Path, plan: dict[str, Any]) -> None:
    path = plan_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def split_steps(raw_steps: str) -> list[str]:
    steps = [part.strip() for part in raw_steps.split("|") if part.strip()]
    if not steps:
        raise ValueError("at least one step is required")
    return steps


def recompute_status(plan: dict[str, Any]) -> str:
    statuses = [step.get("status") for step in plan.get("steps", [])]
    if any(status == "failed" for status in statuses):
        return "failed"
    if any(status == "blocked" for status in statuses):
        return "blocked"
    if statuses and all(status == "passed" for status in statuses):
        return "complete"
    return "in_progress"


def create_plan(project_root: Path, task: str, raw_steps: str, force: bool = False) -> dict[str, Any]:
    if not task.strip():
        raise ValueError("task is required")
    existing = read_plan(project_root)
    if existing and existing.get("status") == "in_progress" and not force:
        raise RuntimeError("an in-progress execution plan already exists; use --force or /implement-task --resume")
    steps = [
        {"index": i, "title": title, "status": "pending", "notes": []}
        for i, title in enumerate(split_steps(raw_steps))
    ]
    now = utc_now()
    plan = {
        "schema": 1,
        "task": task.strip(),
        "status": "in_progress",
        "created_at": now,
        "updated_at": now,
        "steps": steps,
    }
    write_plan(project_root, plan)
    return plan


def mark_step(project_root: Path, index: int, status: str, note: str | None = None) -> dict[str, Any]:
    if index < 0:
        raise IndexError("step index must be non-negative")
    if status not in VALID_STATUSES:
        raise ValueError(f"invalid status: {status}")
    plan = read_plan(project_root)
    if not plan:
        raise RuntimeError("no execution plan exists")
    steps = plan.get("steps", [])
    if index >= len(steps):
        raise IndexError(f"step index out of range: {index}")
    step = steps[index]
    step["status"] = status
    if note:
        step.setdefault("notes", []).append({"at": utc_now(), "text": note})
    plan["updated_at"] = utc_now()
    plan["status"] = recompute_status(plan)
    write_plan(project_root, plan)
    return plan


def reset_plan(project_root: Path) -> bool:
    path = plan_path(project_root)
    if path.exists():
        path.unlink()
        return True
    return False


def next_step(plan: dict[str, Any]) -> dict[str, Any] | None:
    for status in ("running", "pending", "blocked"):
        for step in plan.get("steps", []):
            if step.get("status") == status:
                return step
    return None


def format_plan(plan: dict[str, Any]) -> str:
    lines = [f"task: {plan.get('task')}", f"status: {plan.get('status')}"]
    for step in plan.get("steps", []):
        lines.append(f"[{step.get('index')}] {step.get('status')}: {step.get('title')}")
        for note in step.get("notes", []):
            lines.append(f"    note: {note.get('text')}")
    nxt = next_step(plan)
    if nxt:
        lines.append(f"next: [{nxt.get('index')}] {nxt.get('title')}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage a Trellis execution plan")
    parser.add_argument("--root", help="Project root override")
    sub = parser.add_subparsers(dest="command", required=True)

    p_create = sub.add_parser("create", help="Create an execution plan")
    p_create.add_argument("--task", required=True)
    p_create.add_argument("--steps", required=True, help="Pipe-delimited step list")
    p_create.add_argument("--force", action="store_true")

    p_status = sub.add_parser("status", help="Show the current execution plan")
    p_status.add_argument("--json", action="store_true")

    p_mark = sub.add_parser("mark", help="Mark a step status")
    p_mark.add_argument("index", type=int)
    p_mark.add_argument("status", choices=sorted(VALID_STATUSES))
    p_mark.add_argument("--note")

    sub.add_parser("next", help="Show the next actionable step")
    sub.add_parser("reset", help="Delete the current execution plan")

    args = parser.parse_args()
    try:
        project_root = Path(args.root).resolve() if args.root else get_project_root(Path(__file__).resolve())
    except TrellisPathError as exc:
        print(f"[FAIL] plan: {exc}", file=sys.stderr)
        return 1

    try:
        if args.command == "create":
            plan = create_plan(project_root, args.task, args.steps, force=args.force)
            print(f"[OK] plan created: {len(plan['steps'])} step(s)")
            return 0
        if args.command == "status":
            plan = read_plan(project_root)
            if args.json:
                print(json.dumps(plan or {}, sort_keys=True))
            elif plan:
                print(format_plan(plan))
            else:
                print("[WARN] plan: none")
            return 0
        if args.command == "mark":
            plan = mark_step(project_root, args.index, args.status, note=args.note)
            print(f"[OK] step {args.index}: {args.status}; plan={plan['status']}")
            return 0
        if args.command == "next":
            plan = read_plan(project_root)
            nxt = next_step(plan) if plan else None
            if nxt:
                print(f"[{nxt['index']}] {nxt['status']}: {nxt['title']}")
            else:
                print("[OK] plan: no pending step")
            return 0
        if args.command == "reset":
            removed = reset_plan(project_root)
            print("[OK] plan reset" if removed else "[WARN] plan: none")
            return 0
    except (OSError, ValueError, RuntimeError, IndexError, json.JSONDecodeError) as exc:
        print(f"[FAIL] plan: {exc}", file=sys.stderr)
        return 1
    return 1


if __name__ == "__main__":
    sys.exit(main())
