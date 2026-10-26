#!/usr/bin/env python3
"""Bootstrap Trellis into host-owned root files with explicit permission.

This script intentionally touches only two host-owned root files, and only after
operator approval or --yes:

- CLAUDE.md: create, prepend, or update a fenced Trellis orientation block.
- .gitignore: merge Trellis ignore patterns without duplicating lines.

It may also write .claude/trellis_install_manifest.json with approval. It never
deletes or moves files; legacy cleanup is advisory only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from tools.trellis_install_surface import expected_installed_files  # noqa: E402
from tools.trellis_paths import (  # noqa: E402
    TrellisPathError,
    first_symlink_in_path,
    get_project_root,
    rel_or_name,
    rel_posix,
)

FENCE_START = "<!-- BEGIN TRELLIS BOOTSTRAP -->"
FENCE_END = "<!-- END TRELLIS BOOTSTRAP -->"
MANIFEST_REL = ".claude/trellis_install_manifest.json"
TEMPLATE_REL = "tools/trellis_templates/CLAUDE.md.template"
GITIGNORE_SNIPPET_REL = "tools/trellis_templates/gitignore.snippet"

# Kept as a compatibility name for older tests/imports; build_manifest derives
# the current list from tools.trellis_install_surface.
EXPECTED_INSTALL_PATHS: list[str] = []


CLEANUP_CANDIDATES = [
    "trellis-docs/trellis-claude.md",
    "trellis-docs/trellis-readme.md",
    "trellis-docs/trellis-project-readme-template.md",
    "trellis-docs/trellis-gitignore-snippet.txt",
    "trellis-docs/trellis-workflow-blueprint.md",
    "trellis-docs/trellis-repair-ledger.md",
]


def _task_pack_history_candidates(root: Path) -> list[str]:
    out: list[str] = []
    for dirname in ("task-packs/done", "task-packs/completed"):
        path = root / dirname
        if path.exists():
            out.extend(rel_posix(p, root) for p in sorted(path.glob("TP-*.md")) if p.is_file())
    return out


def read_required_template(root: Path, relative: str) -> str:
    path = root / relative
    if not path.exists():
        raise FileNotFoundError(f"required template missing: {relative}")
    return path.read_text(encoding="utf-8")


def fenced_block(template_text: str) -> str:
    text = template_text.strip("\n")
    return f"{FENCE_START}\n{text}\n{FENCE_END}\n"


def integrate_claude(existing: str | None, template_text: str) -> tuple[str, str]:
    """Return (new_text, action) for CLAUDE.md."""
    block = fenced_block(template_text)
    if existing is None or existing == "":
        return block, "create"

    start = existing.find(FENCE_START)
    end = existing.find(FENCE_END)
    if start != -1 and end != -1 and end > start:
        end_index = end + len(FENCE_END)
        replacement = block.rstrip("\n")
        new_text = existing[:start] + replacement + existing[end_index:]
        if not new_text.endswith("\n"):
            new_text += "\n"
        return new_text, "update"

    separator = "\n" if existing.startswith("\n") else "\n\n"
    return block + separator + existing, "prepend"


def normalize_gitignore_lines(text: str) -> list[str]:
    return [line.rstrip() for line in text.splitlines()]


def merge_gitignore(existing: str | None, snippet_text: str) -> tuple[str, bool]:
    existing_text = existing or ""
    existing_lines = normalize_gitignore_lines(existing_text)
    existing_nonempty = {line for line in existing_lines if line.strip()}
    snippet_lines = normalize_gitignore_lines(snippet_text)

    missing = [line for line in snippet_lines if not line.strip() or line not in existing_nonempty]
    # Preserve blank lines in the snippet only when there is at least one real line missing.
    if not any(line.strip() and line not in existing_nonempty for line in snippet_lines):
        return existing_text, False

    addition_lines = []
    for line in snippet_lines:
        if not line.strip():
            if addition_lines and addition_lines[-1] != "":
                addition_lines.append("")
            continue
        if line not in existing_nonempty:
            addition_lines.append(line)

    if not existing_text:
        merged = "\n".join(addition_lines).rstrip() + "\n"
    else:
        base = existing_text.rstrip("\n")
        merged = base + "\n\n" + "\n".join(addition_lines).rstrip() + "\n"
    return merged, True


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def skip_symlink_write(path: Path, root: Path, label: str) -> bool:
    link = first_symlink_in_path(path, root)
    if link is None:
        return False
    print(f"[SKIP] {label}: symlink path {rel_or_name(path, root)} (via {rel_or_name(link, root)})")
    return True


def cleanup_candidates_present(root: Path) -> list[str]:
    candidates = list(CLEANUP_CANDIDATES)
    candidates.extend(_task_pack_history_candidates(root))
    return [rel for rel in candidates if (root / rel).exists()]


def build_manifest(root: Path, template_text: str, gitignore_snippet: str) -> dict:
    expected = expected_installed_files(root)
    missing = [rel for rel in expected if not (root / rel).exists()]
    return {
        "schema": "trellis-install-manifest/v1",
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "expected_files": expected,
        "missing_files": missing,
        "cleanup_candidates_present": cleanup_candidates_present(root),
        "templates": {
            TEMPLATE_REL: sha256_text(template_text),
            GITIGNORE_SNIPPET_REL: sha256_text(gitignore_snippet),
        },
        "host_touched_with_permission": ["CLAUDE.md", ".gitignore"],
    }


def comparable_manifest(manifest: dict) -> dict:
    """Drop timestamps for idempotency comparison."""
    clone = json.loads(json.dumps(manifest, sort_keys=True))
    clone.pop("generated_at_utc", None)
    return clone


def load_manifest(path: Path) -> dict | None:
    try:
        if not path.exists():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


@dataclass
class BootstrapOptions:
    yes: bool = False
    dry_run: bool = False
    check: bool = False


def confirm(label: str, opts: BootstrapOptions) -> bool:
    if opts.check:
        print(f"[CHECK] would ask before {label}")
        return False
    if opts.yes:
        print(f"[YES] {label}")
        return True
    answer = input(f"Apply {label}? Type yes to continue: ").strip().lower()
    return answer == "yes"


def write_text_if_allowed(root: Path, path: Path, text: str, label: str, opts: BootstrapOptions) -> bool:
    if skip_symlink_write(path, root, label):
        return False
    if not confirm(label, opts):
        print(f"[SKIP] {label}")
        return False
    if opts.dry_run:
        print(f"[DRY-RUN] would write {rel_or_name(path, root)}")
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(f"[OK] wrote {rel_or_name(path, root)}")
    return True


def phase_claude(root: Path, template_text: str, opts: BootstrapOptions) -> bool:
    path = root / "CLAUDE.md"
    if skip_symlink_write(path, root, "integrate root CLAUDE.md"):
        return False
    existing = path.read_text(encoding="utf-8") if path.exists() else None
    new_text, action = integrate_claude(existing, template_text)
    if existing == new_text:
        print("CLAUDE.md already integrated")
        return False
    label = f"{action} root CLAUDE.md Trellis fenced block"
    return write_text_if_allowed(root, path, new_text, label, opts)


def phase_gitignore(root: Path, snippet_text: str, opts: BootstrapOptions) -> bool:
    path = root / ".gitignore"
    if skip_symlink_write(path, root, "merge Trellis .gitignore snippet"):
        return False
    existing = path.read_text(encoding="utf-8") if path.exists() else None
    new_text, changed = merge_gitignore(existing, snippet_text)
    if not changed:
        print("gitignore already merged")
        return False
    return write_text_if_allowed(root, path, new_text, "merge Trellis .gitignore snippet", opts)


def phase_manifest(root: Path, template_text: str, gitignore_snippet: str, opts: BootstrapOptions) -> bool:
    path = root / MANIFEST_REL
    if skip_symlink_write(path, root, "write Trellis install manifest"):
        return False
    manifest = build_manifest(root, template_text, gitignore_snippet)
    existing = load_manifest(path)
    if existing is not None and comparable_manifest(existing) == comparable_manifest(manifest):
        print("install manifest already current")
        return False
    text = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    return write_text_if_allowed(root, path, text, "write Trellis install manifest", opts)


def phase_cleanup(root: Path) -> list[str]:
    present = cleanup_candidates_present(root)
    print("Cleanup advisory:")
    if not present:
        print("  none")
        return []
    for rel in present:
        print(f"  manual review/delete candidate: {rel}")
    print("  Trellis did not delete or move these files.")
    return present


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bootstrap Trellis root CLAUDE.md and .gitignore safely")
    parser.add_argument("--yes", action="store_true", help="Apply required mutations without interactive prompts")
    parser.add_argument("--dry-run", action="store_true", help="Print intended mutations without writing")
    parser.add_argument("--check", action="store_true", help="Report needed mutations without writing or prompting")
    args = parser.parse_args(argv)
    opts = BootstrapOptions(yes=args.yes, dry_run=args.dry_run, check=args.check)

    try:
        root = get_project_root(Path(__file__).resolve())
        template_text = read_required_template(root, TEMPLATE_REL)
        gitignore_snippet = read_required_template(root, GITIGNORE_SNIPPET_REL)
    except (TrellisPathError, FileNotFoundError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"Trellis bootstrap root: {root}")
    changed = False
    changed = phase_claude(root, template_text, opts) or changed
    changed = phase_gitignore(root, gitignore_snippet, opts) or changed
    changed = phase_manifest(root, template_text, gitignore_snippet, opts) or changed
    phase_cleanup(root)

    if opts.check:
        return 0
    if changed:
        print("Bootstrap complete. Run: python tools/trellis_repair_gate.py")
    else:
        print("Bootstrap complete. No mutations applied.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
