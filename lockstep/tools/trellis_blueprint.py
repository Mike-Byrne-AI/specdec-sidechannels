#!/usr/bin/env python3
"""Local cognitive blueprint storage for Trellis sessions.

Blueprints capture durable reasoning fragments that should survive context
compaction and session boundaries. They are local harness state, not a source of
truth that replaces trellis-docs/trellis-findings.md, trellis-docs/trellis-decisions.md, trellis-docs/trellis-runs.md, or task packs.
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from tools.trellis_paths import TrellisPathError, get_project_root, rel_posix  # noqa: E402

ALLOWED_KINDS = {
    "decision",
    "alternative_rejected",
    "pattern_discovered",
    "risk",
    "next_step",
    "stop_condition",
    "pack_result",
    "reflection",
    "context",
    "note",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def blueprint_dir(project_root: Path) -> Path:
    return project_root / ".claude" / "blueprints"


def active_path(project_root: Path) -> Path:
    return blueprint_dir(project_root) / "active.json"


def latest_path(project_root: Path) -> Path:
    return blueprint_dir(project_root) / "latest.json"


def new_blueprint_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return f"bp-{stamp}-{uuid.uuid4().hex[:6]}"


def read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def start_blueprint(project_root: Path, title: str = "Trellis session", reset: bool = False) -> dict[str, Any]:
    path = active_path(project_root)
    existing = read_json(path)
    if existing and not reset:
        return existing
    data = {
        "schema": 1,
        "id": new_blueprint_id(),
        "title": title,
        "status": "active",
        "started_at": utc_now(),
        "records": [],
    }
    write_json(path, data)
    return data


def require_active(project_root: Path, autostart: bool = True) -> dict[str, Any]:
    data = read_json(active_path(project_root))
    if data:
        return data
    if autostart:
        return start_blueprint(project_root)
    raise RuntimeError("no active blueprint")


def record_blueprint(project_root: Path, kind: str, description: str, autostart: bool = True) -> dict[str, Any]:
    if kind not in ALLOWED_KINDS:
        raise ValueError(f"unsupported blueprint kind: {kind}")
    if not description.strip():
        raise ValueError("description is required")
    data = require_active(project_root, autostart=autostart)
    record = {
        "kind": kind,
        "description": description.strip(),
        "created_at": utc_now(),
    }
    data.setdefault("records", []).append(record)
    data["updated_at"] = record["created_at"]
    write_json(active_path(project_root), data)
    return record


def finalized_blueprint_paths(project_root: Path) -> list[Path]:
    bp_dir = blueprint_dir(project_root)
    if not bp_dir.exists():
        return []
    return sorted(
        (p for p in bp_dir.glob("bp-*.json") if p.is_file()),
        key=lambda p: p.name,
    )


def summarize_blueprint(data: dict[str, Any]) -> dict[str, Any]:
    records = data.get("records", [])
    return {
        "id": data.get("id"),
        "title": data.get("title"),
        "status": data.get("status"),
        "started_at": data.get("started_at"),
        "finalized_at": data.get("finalized_at"),
        "record_count": len(records),
        "latest_records": records[-5:],
    }


def finalize_blueprint(project_root: Path) -> dict[str, Any] | None:
    path = active_path(project_root)
    data = read_json(path)
    if not data:
        return None
    data["status"] = "finalized"
    data["finalized_at"] = utc_now()
    out_path = blueprint_dir(project_root) / f"{data['id']}.json"
    write_json(out_path, data)
    write_json(latest_path(project_root), summarize_blueprint(data))
    path.unlink()
    return data


def load_blueprint_state(project_root: Path) -> dict[str, Any]:
    active = read_json(active_path(project_root))
    latest = read_json(latest_path(project_root))
    finalized = finalized_blueprint_paths(project_root)
    return {
        "active": summarize_blueprint(active) if active else None,
        "latest": latest,
        "finalized_count": len(finalized),
    }


def format_record(record: dict[str, Any]) -> str:
    return f"- {record.get('kind')}: {record.get('description')}"


def print_state(project_root: Path, json_only: bool = False) -> int:
    state = load_blueprint_state(project_root)
    if json_only:
        print(json.dumps(state, sort_keys=True))
        return 0
    active = state["active"]
    latest = state["latest"]
    if active:
        print(f"[OK] blueprint active: {active['id']} ({active['record_count']} records)")
        for record in active.get("latest_records", []):
            print(format_record(record))
    else:
        print("[WARN] blueprint active: none")
    if latest:
        print(f"[OK] latest finalized: {latest['id']} ({latest['record_count']} records)")
        for record in latest.get("latest_records", []):
            print(format_record(record))
    else:
        print("[WARN] latest finalized: none")
    return 0


def print_chain(project_root: Path, limit: int, json_only: bool = False) -> int:
    paths = finalized_blueprint_paths(project_root)[-limit:]
    items = []
    for path in paths:
        data = read_json(path) or {}
        items.append(summarize_blueprint(data))
    active = read_json(active_path(project_root))
    payload = {"finalized": items, "active": summarize_blueprint(active) if active else None}
    if json_only:
        print(json.dumps(payload, sort_keys=True))
        return 0
    if active:
        print(f"active: {active.get('id')} ({len(active.get('records', []))} records)")
    else:
        print("active: none")
    for item in items:
        print(f"finalized: {item.get('id')} ({item.get('record_count')} records)")
        for record in item.get("latest_records", []):
            print(f"  {format_record(record)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage Trellis cognitive blueprints")
    parser.add_argument("--root", help="Project root override")
    sub = parser.add_subparsers(dest="command", required=True)

    p_start = sub.add_parser("start", help="Start a blueprint session")
    p_start.add_argument("--title", default="Trellis session")
    p_start.add_argument("--reset", action="store_true", help="Replace an existing active blueprint")

    p_record = sub.add_parser("record", help="Record a durable reasoning fragment")
    p_record.add_argument("--kind", required=True, choices=sorted(ALLOWED_KINDS))
    p_record.add_argument("--description", required=True)
    p_record.add_argument("--no-autostart", action="store_true")

    sub.add_parser("finalize", help="Finalize the active blueprint")

    p_load = sub.add_parser("load", help="Show active/latest blueprint state")
    p_load.add_argument("--json", action="store_true")

    p_chain = sub.add_parser("chain", help="Show recent finalized blueprint chain")
    p_chain.add_argument("--limit", type=int, default=5)
    p_chain.add_argument("--json", action="store_true")

    p_status = sub.add_parser("status", help="Machine-readable blueprint status")
    p_status.add_argument("--json", action="store_true")

    args = parser.parse_args()
    try:
        project_root = Path(args.root).resolve() if args.root else get_project_root(Path(__file__).resolve())
    except TrellisPathError as exc:
        print(f"[FAIL] blueprint: {exc}", file=sys.stderr)
        return 1

    try:
        if args.command == "start":
            data = start_blueprint(project_root, title=args.title, reset=args.reset)
            print(f"[OK] blueprint active: {data['id']}")
            return 0
        if args.command == "record":
            record = record_blueprint(project_root, args.kind, args.description, autostart=not args.no_autostart)
            print(f"[OK] blueprint record: {record['kind']}")
            return 0
        if args.command == "finalize":
            data = finalize_blueprint(project_root)
            if not data:
                print("[WARN] blueprint: no active blueprint")
                return 0
            print(f"[OK] blueprint finalized: {data['id']}")
            return 0
        if args.command == "load":
            return print_state(project_root, json_only=args.json)
        if args.command == "chain":
            return print_chain(project_root, limit=args.limit, json_only=args.json)
        if args.command == "status":
            state = load_blueprint_state(project_root)
            if args.json:
                print(json.dumps(state, sort_keys=True))
            else:
                active = state["active"]
                latest = state["latest"]
                print(f"active={active['id'] if active else 'none'} latest={latest['id'] if latest else 'none'}")
            return 0
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"[FAIL] blueprint: {exc}", file=sys.stderr)
        return 1

    return 1


if __name__ == "__main__":
    sys.exit(main())
