#!/usr/bin/env python3
"""Lint FINDINGS.md: every finding must carry its regime and its evidence.

Rule (imported from the determinism-layer postmortem, F-2/F-6 incident):
a finding cited outside the regime it was measured in is a bug. The cheap
mechanical guard is to make regime and evidence MANDATORY fields, so a
finding can never circulate without its regime attached.

Every `## F-*` entry in FINDINGS.md must contain:
  - a `- regime:` line (non-empty)
  - a `- source:` line whose repo-relative paths exist (results/, experiments/,
    tests/, docs/ prefixes are checked; free text is allowed alongside)

Exit code 0 on success, 1 with a report on failure. Run via `make lint`; CI
runs it on every push.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

CHECKED_PREFIXES = ("results/", "experiments/", "tests/", "docs/", "src/")


def parse_entries(text: str) -> list[tuple[str, str]]:
    """Return (entry_id, entry_body) for every `## <ID> —/-` section."""
    entries: list[tuple[str, str]] = []
    matches = list(re.finditer(r"^## +(F-[\w.]+)\b.*$", text, flags=re.M))
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        entries.append((m.group(1), text[m.start() : end]))
    return entries


def lint_text(text: str, repo_root: Path) -> list[str]:
    errors: list[str] = []
    entries = parse_entries(text)
    for entry_id, body in entries:
        regime = re.search(r"^- +regime: *(\S.*)$", body, flags=re.M)
        if not regime:
            errors.append(f"{entry_id}: missing '- regime:' line (findings must carry their regime)")
        source = re.search(r"^- +source: *(\S.*)$", body, flags=re.M)
        if not source:
            errors.append(f"{entry_id}: missing '- source:' line (findings must carry evidence)")
        else:
            for tokenised in re.split(r"[,\s]+", source.group(1)):
                tok = tokenised.strip().rstrip(";.")
                if tok.startswith(CHECKED_PREFIXES) and not (repo_root / tok).exists():
                    errors.append(f"{entry_id}: source path does not exist: {tok}")
    return errors


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    findings = repo_root / "FINDINGS.md"
    if not findings.exists():
        print("lint_findings: FINDINGS.md not found", file=sys.stderr)
        return 1
    errors = lint_text(findings.read_text(), repo_root)
    if errors:
        print("lint_findings: FAIL")
        for e in errors:
            print(f"  - {e}")
        return 1
    n = len(parse_entries(findings.read_text()))
    print(f"lint_findings: OK ({n} findings, all carry regime + evidence)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
