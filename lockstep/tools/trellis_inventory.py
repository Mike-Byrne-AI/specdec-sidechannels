#!/usr/bin/env python3
"""Report Trellis harness inventory and check expected surface counts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from tools.trellis_paths import (  # noqa: E402
    active_task_packs,
    done_task_packs,
    example_task_packs,
    get_project_root,
    has_trellis_memory,
    is_source_layout,
    memory_dir,
)

EXPECTED_COUNTS = {
    "commands": 10,
    "skills": 5,
    "agents": 4,
    "hooks": 5,
    "rules": 5,
}
EXPECTED_SOURCE_MEMORY_TOPICS = 4


def count_files(root: Path, pattern: str) -> int:
    return len([p for p in root.glob(pattern) if p.is_file()])


def collect_inventory(project_root: Path) -> dict[str, int]:
    hooks = [
        p for p in (project_root / ".claude" / "hooks").glob("*.py")
        if p.is_file() and not p.name.startswith("__")
    ]
    mem = memory_dir(project_root)
    memory_topics = 0
    if has_trellis_memory(project_root):
        memory_topics = len([p for p in mem.iterdir() if p.is_dir() and not p.is_symlink()])
    return {
        "commands": count_files(project_root / ".claude" / "commands", "*.md"),
        "skills": count_files(project_root / ".claude" / "skills", "*/SKILL.md"),
        "agents": count_files(project_root / ".claude" / "agents", "*.md"),
        "hooks": len(hooks),
        "rules": count_files(project_root / ".claude" / "rules", "**/*.md"),
        "active_task_packs": len(active_task_packs(project_root)),
        "example_task_packs": len(example_task_packs(project_root)),
        "done_task_packs": len(done_task_packs(project_root)),
        "memory_topics": memory_topics,
    }


def inventory_mismatches(project_root: Path, inventory: dict[str, int]) -> list[str]:
    mismatches = []
    for key, expected in EXPECTED_COUNTS.items():
        actual = inventory.get(key)
        if actual != expected:
            mismatches.append(f"{key}: expected {expected}, got {actual}")

    mem = memory_dir(project_root)
    if has_trellis_memory(project_root):
        actual = inventory.get("memory_topics")
        if actual != EXPECTED_SOURCE_MEMORY_TOPICS:
            mismatches.append(f"memory_topics: expected {EXPECTED_SOURCE_MEMORY_TOPICS}, got {actual}")
    elif is_source_layout(project_root) and mem.exists():
        mismatches.append("memory: source checkout has memory/ but no valid regular memory/.trellis-memory sentinel")
    return mismatches


def main() -> int:
    parser = argparse.ArgumentParser(description="Print Trellis harness inventory")
    parser.add_argument("--json", action="store_true", help="Emit JSON only")
    parser.add_argument("--check", action="store_true", help="Exit nonzero on expected count mismatch")
    args = parser.parse_args()

    project_root = get_project_root(Path(__file__).resolve())
    inventory = collect_inventory(project_root)

    if args.json:
        print(json.dumps(inventory, sort_keys=True))
    else:
        print("Trellis inventory")
        for key in sorted(inventory):
            print(f"  {key}: {inventory[key]}")

    if args.check:
        mismatches = inventory_mismatches(project_root, inventory)
        if mismatches:
            print("Inventory check failed:", file=sys.stderr)
            for mismatch in mismatches:
                print(f"  {mismatch}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
