#!/usr/bin/env python3
"""Pin large gitignored evidence by content: write or check a sha256 manifest.

The top-256 logit dumps under results/p2 and results/p2_llama32 (~1 GB each)
stay local; the repo commits this manifest instead, so a later recompute can
prove it read the same bytes the findings did. Output is sha256sum-compatible
(`<hex>  <path>` per line, LF, sorted by path, paths relative to the repo
root with forward slashes).

  python tools/sha256_manifest.py write --out results/p2_dumps.sha256 results/p2 results/p2_llama32
  python tools/sha256_manifest.py check results/p2_dumps.sha256

`check` exits 1 and names every missing or mismatched file.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def sha256_file(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def manifest_lines(dirs: list[Path], root: Path) -> list[str]:
    files = sorted(p for d in dirs for p in d.rglob("*") if p.is_file())
    return [f"{sha256_file(p)}  {p.relative_to(root).as_posix()}" for p in files]


def parse_manifest(text: str) -> list[tuple[str, str]]:
    rows = []
    for line in text.splitlines():
        if not line.strip():
            continue
        digest, sep, rel = line.partition("  ")
        if not sep or len(digest) != 64:
            raise ValueError(f"malformed manifest line: {line!r}")
        rows.append((digest, rel))
    return rows


def check(manifest: Path, root: Path) -> list[str]:
    problems = []
    for digest, rel in parse_manifest(manifest.read_text(encoding="utf-8")):
        p = root / rel
        if not p.is_file():
            problems.append(f"MISSING  {rel}")
        elif sha256_file(p) != digest:
            problems.append(f"MISMATCH {rel}")
    return problems


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, default=REPO_ROOT, help="paths are written relative to this")
    sub = ap.add_subparsers(dest="cmd", required=True)
    w = sub.add_parser("write")
    w.add_argument("--out", type=Path, required=True)
    w.add_argument("dirs", nargs="+", type=Path)
    c = sub.add_parser("check")
    c.add_argument("manifest", type=Path)
    a = ap.parse_args(argv)
    root = a.root.resolve()
    if a.cmd == "write":
        lines = manifest_lines([d.resolve() for d in a.dirs], root)
        a.out.write_bytes(("\n".join(lines) + "\n").encode("utf-8"))
        print(f"wrote {len(lines)} entries to {a.out}")
        return 0
    problems = check(a.manifest, root)
    for p in problems:
        print(p)
    print("manifest: OK" if not problems else f"manifest: FAIL ({len(problems)} problems)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
