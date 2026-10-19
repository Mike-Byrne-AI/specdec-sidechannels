#!/usr/bin/env python3
"""tools/evidence_pins.py — the absolute evidence-citation pins (2026-10-16, lane C of the
2026-10-15 image audit, item S6b-C-1).

tests/test_evidence_bytes.py's checks 1 to 5 are index- or HEAD-relative: a hand-edit of a cited
results file that is then COMMITTED passes all five (check 1 compares disk with the index, check 3
compares citation counts with HEAD's, and after the commit HEAD carries the edit). This tool lists
every 64-hex digest cited in a tracked text file that resolves to the bytes of some tracked file
(its disk bytes, or either line-ending twin of them), with the path(s) it resolves to, and writes
the list to tests/evidence_pins.json. Check 6 of the test recomputes the list from the tree and
requires the same digests resolving to the same paths: a cited file whose bytes changed no longer
resolves to the digest the record cites, so that digest drops out of the recomputation and the
test names it and the file, whatever HEAD says.

The pins file is the record of what resolved on the day it was written. A registered landing that
cites a new digest regenerates it (`python tools/evidence_pins.py --write`) and commits it beside
the landing; the test fails on an unlisted new resolution, so the regeneration is part of landing
(docs/TASK_RECIPES.md carries the step). `--write` refuses when a pinned digest no longer resolves
or resolves elsewhere, unless each such digest is named with `--accept <digest>`: a regeneration of
cited evidence is a registered act that names what it replaced, never a habit. The comparison is on
paths; the line-ending form each digest matched ("disk", "lf" or "crlf") is recorded for the reader
and not compared, because a checkout's line endings are checks 1 to 4's concern and a Linux clone
and a Windows checkout must agree here.

Scope, the same as check 4's except where noted: tracked files only (`git ls-files`, intent-to-add
entries included, since they have disk bytes; a tracked file missing from disk is skipped and its
digest then reads as unresolved); citers are tracked text files (TEXT_SUFFIXES, which adds `.cff`
to the test's list) except every file under the export tool's proof-receipt folder (check 5 holds
those), every file under the recovered critic folder (RECOVERED_PREFIXES, 2026-10-17: the reviewer's
recovered scripts and reports quote digests in whichever form the reviewer hashed, and the folder's
manifests quote its own files' digests; neither is a citation the record makes, so the test leaves the
folder out of checks 2 to 4 as well) and this tool's own pins file (it quotes every digest, and it IS a
citer for checks 2 to 4, so after a regeneration check 3 reads one citation short until the file is
rewritten). A digest that resolves to no tracked file (a gitignored raw's sha, a moments digest, a
registration document outside the tree) is not a pin. Nothing here imports torch; git runs through
subprocess.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PINS = ROOT / "tests" / "evidence_pins.json"
HEX64 = re.compile(rb"[0-9a-f]{64}")
TEXT_SUFFIXES = (".json", ".jsonl", ".md", ".py", ".txt", ".toml", ".yml", ".yaml", ".cff")
RECEIPT_PREFIXES = ("docs/public_cut/proofs/",)  # [withheld: docs/public_cut/ not in this repository; see WITHHELD.md]
RECOVERED_PREFIXES = ("docs/audits/critic-recovered/",)   # the same tuple as tests/test_evidence_bytes.py's
SELF = "tests/evidence_pins.json"


def tracked(root: Path) -> list[str]:
    out = subprocess.run(["git", "ls-files", "-z"], cwd=root, capture_output=True, check=True).stdout
    return [p.decode("utf-8", "surrogateescape") for p in out.split(b"\0") if p]


def is_text(path: str) -> bool:
    return path.endswith(TEXT_SUFFIXES)


def is_citer(path: str) -> bool:
    return is_text(path) and not path.startswith(RECEIPT_PREFIXES + RECOVERED_PREFIXES) and path != SELF


def forms(b: bytes) -> list[tuple[str, str]]:
    """(form, sha256) of ``b`` as it is ("disk"), LF-normalised ("lf") and CRLF-normalised
    ("crlf"), one entry per distinct digest; "disk" absorbs whichever twin equals it."""
    lf = b.replace(b"\r\n", b"\n")
    out: list[tuple[str, str]] = []
    seen: set[str] = set()
    for kind, x in (("disk", b), ("lf", lf), ("crlf", lf.replace(b"\n", b"\r\n"))):
        h = hashlib.sha256(x).hexdigest()
        if h not in seen:
            seen.add(h)
            out.append((kind, h))
    return out


def scan(root: Path) -> tuple[dict[str, dict], set[str]]:
    """(pins, cited): pins maps a digest to {"paths": [[path, form], ...] sorted} for every cited
    digest that resolves to a tracked file other than the citer; cited is the set of every 64-hex
    digest any citer quotes, resolved or not (so a lost pin can be told apart from a dropped
    citation)."""
    paths = tracked(root)
    index: dict[str, list[tuple[str, str]]] = {}
    blobs: dict[str, bytes] = {}
    for p in paths:
        fp = root / p
        if not fp.is_file():
            continue
        b = fp.read_bytes()
        if is_citer(p):
            blobs[p] = b
        for kind, h in forms(b):
            index.setdefault(h, []).append((p, kind))
    pins: dict[str, set[tuple[str, str]]] = {}
    cited: set[str] = set()
    for citer, b in blobs.items():
        for m in HEX64.finditer(b):
            h = m.group(0).decode()
            cited.add(h)
            for p, kind in index.get(h, ()):
                if p != citer:
                    pins.setdefault(h, set()).add((p, kind))
    return {h: {"paths": sorted([list(t) for t in s])} for h, s in sorted(pins.items())}, cited


def load_pins(path: Path = PINS) -> dict:
    return json.loads(path.read_bytes().decode("utf-8"))


def compare(pinned: dict[str, dict], now: dict[str, dict], cited: set[str]) -> dict[str, list]:
    """The four disagreements check 6 reports, each with its own remedy: `unresolved` (the digest is
    still cited and resolves to no tracked file: the cited bytes changed), `uncited` (no tracked text
    file quotes the digest any more: a citation was removed), `moved` (the digest resolves to other
    paths than pinned: a rename or a duplicate) and `new` (a resolution the pins file lacks)."""
    unresolved = [[h, pinned[h]["paths"]] for h in pinned if h not in now and h in cited]
    uncited = [[h, pinned[h]["paths"]] for h in pinned if h not in now and h not in cited]
    moved = [[h, pinned[h]["paths"], now[h]["paths"]] for h in pinned
             if h in now and [p for p, _ in pinned[h]["paths"]] != [p for p, _ in now[h]["paths"]]]
    new = [[h, now[h]["paths"]] for h in now if h not in pinned]
    return {"unresolved": unresolved, "uncited": uncited, "moved": moved, "new": new}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--write", action="store_true", help="rewrite tests/evidence_pins.json from the tree")
    ap.add_argument("--accept", action="append", default=[], metavar="DIGEST",
                    help="with --write: a pinned digest that may be dropped or moved (name each one)")
    args = ap.parse_args(argv)
    now, cited = scan(ROOT)
    n_paths = len({p for d in now.values() for p, _ in d["paths"]})
    print(f"evidence_pins: {len(now)} cited digests resolve to {n_paths} tracked files")
    diff = compare(load_pins()["pins"], now, cited) if PINS.exists() else None
    if diff is not None:
        for key, rows in diff.items():
            print(f"  {key}: {len(rows)}")
            for row in rows[:10]:
                print("   ", row)
    if args.write:
        if diff is not None:
            blocking = [row[0] for key in ("unresolved", "moved") for row in diff[key] if row[0] not in args.accept]
            if blocking:
                print(f"refusing --write: {len(blocking)} pinned digest(s) no longer resolve as pinned; "
                      "restore the bytes or re-cite through the registered landing, or name each with --accept")
                return 2
        payload = {"written": date.today().isoformat(), "n_digests": len(now), "n_files": n_paths, "pins": now}
        PINS.write_bytes((json.dumps(payload, indent=1, sort_keys=True) + "\n").encode("utf-8"))
        print(f"wrote {PINS.relative_to(ROOT)}")
        return 0
    if diff is None:
        print(f"no {PINS.relative_to(ROOT)}; run with --write")
        return 1
    return 0 if not any(diff.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
