#!/usr/bin/env python3
"""Lint FINDINGS.md: every finding must carry its regime and its evidence.

Rule (imported from the determinism-layer postmortem, F-2/F-6 incident):
a finding cited outside the regime it was measured in is a bug. The cheap
mechanical guard is to make regime and evidence MANDATORY fields, so a
finding can never circulate without its regime attached.

Every `## F-*` entry in FINDINGS.md must contain:
  - a `- regime:` line (non-empty)
  - one or more `- source:` lines whose cited paths exist AND are tracked by
    git. A token is checked when it starts with results/, experiments/,
    tests/, docs/, src/, data/ or tools/ (separators normalised; wrapping
    parentheses, backticks, quotes and angle brackets dropped; a markdown
    link reduced to its target; one level of brace shorthand expanded:
    `a{,_r}.json` cites `a.json` and `a_r.json`). A bare file name (no "/",
    one of the suffixes in BARE_SUFFIXES) is resolved against the directory
    of the last prefixed file token before it, then against the repo root,
    so `results/real/x.json, x.json.state.jsonl` checks both files. A
    directory token passes when at least one tracked path sits beneath it
    (harvest directories keep only their metas tracked). Free text is
    allowed alongside; a citation in prose outside a `- source:` line is not
    read. Tracked means listed by `git ls-files` minus intent-to-add entries
    (`git add -N`), i.e. the index: a staged file counts. Existence alone
    was a blind spot: a registered run's state file is git-ignored until its
    own negation line lands in .gitignore, so a finding could cite evidence
    that never reached the repository (closed 2026-10-01; docs/SHARP_EDGES.md).
    When git cannot answer (not on PATH, not a checkout) the check falls back
    to existence and the OK line says "existence only"; under CI (the CI
    environment variable) that is a failure, not a fallback.

Exit code 0 on success, 1 with a report on failure. Run via `make lint`; CI
runs it on every push. Dated note 2026-10-18: "CI" is the public repository's
root workflow; this repository's own remote has Actions disabled while the
public cut is prepared (the push policy in ESPALIER_MEMORY.md's session rows),
so there the lint runs under `make lint` and `/preflight` only.

Dated note 2026-10-16 (lane C of the 2026-10-15 image audit, S5b-C-1): a
`- source:` bullet wrapped over several physical lines (continuation lines
indented, as FINDINGS.md wraps them) is read whole; before this the lint read
only the bullet's first line, so the paths on the continuation lines were never
checked. tests/test_lint_findings.py holds the wrapped case and its mutant.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

CHECKED_PREFIXES = ("results/", "experiments/", "tests/", "docs/", "src/", "data/", "tools/")
BARE_SUFFIXES = (".json", ".jsonl", ".npz", ".md", ".py", ".txt", ".toml", ".yml")
ASK_GIT = object()  # sentinel for lint_text(tracked=...): resolve the tracked set from git
_BRACE_COMMA = "\x00"  # stands in for a comma inside {a,b} while the line is split
_WRAPPERS = "()`'\"[]<>"
_MD_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")


def parse_entries(text: str) -> list[tuple[str, str]]:
    """Return (entry_id, entry_body) for every `## <ID> —/-` section."""
    entries: list[tuple[str, str]] = []
    matches = list(re.finditer(r"^## +(F-[\w.]+)\b.*$", text, flags=re.M))
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        entries.append((m.group(1), text[m.start() : end]))
    return entries


def _git_z(repo_root: Path, *args: str) -> list[str] | None:
    try:
        proc = subprocess.run(["git", *args, "-z"], cwd=repo_root, capture_output=True, check=False)
    except OSError:
        return None
    if proc.returncode != 0:
        return None
    return [p.decode("utf-8", "surrogateescape") for p in proc.stdout.split(b"\0") if p]


def git_tracked_paths(repo_root: Path) -> set[str] | None:
    """Repo-relative paths git tracks under ``repo_root`` (forward slashes),
    without intent-to-add entries, or ``None`` when git cannot answer (no git
    on PATH, not a checkout)."""
    listed = _git_z(repo_root, "ls-files")
    if listed is None:
        return None
    intent_to_add = _git_z(repo_root, "diff", "--name-only", "--diff-filter=A") or []
    return set(listed) - set(intent_to_add)


def _is_tracked(tok: str, tracked: set[str]) -> bool:
    """A file token is tracked when git lists it; a directory token when git
    lists at least one path beneath it."""
    rel = tok.rstrip("/")
    if rel in tracked:
        return True
    prefix = rel + "/"
    return any(p.startswith(prefix) for p in tracked)


def _case_twin(tok: str, tracked: set[str]) -> str | None:
    """The tracked path equal to ``tok`` up to letter case, if any (a
    case-insensitive filesystem lets such a token pass the existence check)."""
    low = tok.rstrip("/").lower()
    for p in tracked:
        if p.lower() == low:
            return p
    return None


def _normalise(tok: str) -> str:
    """Forward slashes, no doubled separators, no wrapping punctuation, no
    trailing `;`, `.` or `:`."""
    tok = tok.strip().rstrip(";.:").strip(_WRAPPERS).rstrip(";.:").replace("\\", "/")
    return re.sub(r"/{2,}", "/", tok)


def _expand_braces(tok: str) -> list[str]:
    """`{a,b}` shorthand; nested levels expand recursively."""
    m = re.search(r"\{([^{}]*)\}", tok)
    if not m:
        return [tok]
    head, tail = tok[: m.start()], tok[m.end():]
    out: list[str] = []
    for alt in m.group(1).split(","):
        out.extend(_expand_braces(head + alt + tail))
    return out


def source_paths(source_line: str, repo_root: Path) -> list[str]:
    """The repo-relative paths a `- source:` line cites: prefixed tokens with
    their brace expansions, and bare file names resolved against the directory
    of the last prefixed file token (then the repo root)."""
    paths: list[str] = []
    last_dir: str | None = None
    line = _MD_LINK.sub(r"\1", source_line)
    # a comma inside brace shorthand is part of the token, not a separator
    protected = re.sub(r"\{[^{}]*\}", lambda m: m.group(0).replace(",", _BRACE_COMMA), line)
    for raw in re.split(r"[,\s]+", protected):
        tok = _normalise(raw.replace(_BRACE_COMMA, ","))
        if not tok:
            continue
        if tok.startswith(CHECKED_PREFIXES):
            expanded = _expand_braces(tok)
            paths.extend(expanded)
            first = expanded[0]
            if first.endswith(BARE_SUFFIXES) and "/" in first:
                last_dir = first.rsplit("/", 1)[0]
            else:
                last_dir = first.rstrip("/")
        elif "/" not in tok and tok.endswith(BARE_SUFFIXES) and not tok.startswith("."):
            for name in _expand_braces(tok):
                if last_dir and (repo_root / last_dir / name).exists():
                    paths.append(f"{last_dir}/{name}")
                elif (repo_root / name).exists():
                    paths.append(name)
                elif last_dir:
                    paths.append(f"{last_dir}/{name}")  # reported as missing below
    return paths


_SOURCE_BULLET = re.compile(r"^- +source: *(\S.*(?:\n[ \t]+\S.*)*)", flags=re.M)


def source_lines(body: str) -> list[str]:
    """The `- source:` bullets of one entry, each joined into a single line. A bullet wrapped over
    several physical lines (the continuation lines indented, as FINDINGS.md wraps them) is one
    source line; before 2026-10-16 only the bullet's first line was read, so the paths on the
    continuation lines were never checked (image audit S5b-C-1). tests/test_lint_findings.py calls
    this function rather than re-typing the pattern."""
    return [" ".join(ln.strip() for ln in src.splitlines()) for src in _SOURCE_BULLET.findall(body)]


def lint_text(text: str, repo_root: Path, tracked: set[str] | None | object = ASK_GIT) -> list[str]:
    """Return the lint errors for ``text``. ``tracked`` is the set of
    git-tracked paths; ASK_GIT (the default) resolves it from git; ``None``
    means git could not answer and only existence is checked."""
    errors: list[str] = []
    entries = parse_entries(text)
    if tracked is ASK_GIT:
        tracked = git_tracked_paths(repo_root)
    for entry_id, body in entries:
        regime = re.search(r"^- +regime: *(\S.*)$", body, flags=re.M)
        if not regime:
            errors.append(f"{entry_id}: missing '- regime:' line (findings must carry their regime)")
        sources = source_lines(body)
        if not sources:
            errors.append(f"{entry_id}: missing '- source:' line (findings must carry evidence)")
            continue
        for source in sources:
            for tok in source_paths(source, repo_root):
                if not (repo_root / tok).exists():
                    errors.append(f"{entry_id}: source path does not exist: {tok}")
                elif tracked is not None and not _is_tracked(tok, tracked):
                    twin = _case_twin(tok, tracked)
                    if twin:
                        errors.append(
                            f"{entry_id}: source path case differs from the tracked path: {tok} (tracked as {twin})"
                        )
                    else:
                        errors.append(
                            f"{entry_id}: source path is not committed evidence "
                            f"(untracked or git-ignored): {tok}"
                        )
    return errors


def git_required() -> bool:
    """Under CI a lint that cannot ask git must fail, not degrade."""
    return bool(os.environ.get("CI"))


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    findings = repo_root / "FINDINGS.md"
    if not findings.exists():
        print("lint_findings: FINDINGS.md not found", file=sys.stderr)
        return 1
    text = findings.read_text(encoding="utf-8")
    tracked = git_tracked_paths(repo_root)
    if tracked is None and git_required():
        print("lint_findings: FAIL\n  - git cannot answer under CI; the tracked-evidence check is required here")
        return 1
    errors = lint_text(text, repo_root, tracked)
    if errors:
        print("lint_findings: FAIL")
        for e in errors:
            print(f"  - {e}")
        return 1
    n = len(parse_entries(text))
    if tracked is None:
        print(f"lint_findings: OK ({n} findings, all carry regime + evidence; existence only: git unavailable)")
    else:
        print(f"lint_findings: OK ({n} findings, all carry regime + tracked evidence)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
