#!/usr/bin/env python3
"""docs/audits/critic-recovered/recover.py: the recovered critic folder (the public-cut plan,
section 14.2 item 3, 2026-10-17). This file is frozen in the export; the withheld paths it names
are mention-exempt in the export tool's spec.

The sideband critic's recompute scripts and reports of the harness era (2026-10-01 to 2026-10-16)
survived only in the author's per-session scratch under the box's Temp folder. On 2026-10-16 an
archive was made outside Temp and outside the repository (README.md names it), with a sha256
manifest, by this rule, recovered from the archive itself on 2026-10-17 (the rule rebuilds it
exactly): the files sitting DIRECTLY inside a folder whose name starts with ``critic``, with the
suffix .py, .txt, .json or .md, nothing nested below such a folder and nothing of another suffix.
What that rule left in Temp (nested round folders, logs, dispatch briefs, two reports named critic*
outside such folders) was copied to a second archive on 2026-10-17 and is not in this folder
(README.md, "What the archive's rule left behind"). This script copies the first archive into the
folder beside it, so the record carries what the reviewer ran, and writes the two manifests that
pin every byte.

What it does, in order:

1. Verifies the archive: every file the archive's MANIFEST.json lists is present with the listed
   sha256 and size, and nothing else is there. The archive is read as bytes; nothing in it runs.
2. Lays the files out flat: ``<date>-<session8>/<subpath>``, where the date is the UTC day of the
   session's earliest file, session8 the first eight characters of the session's transcript id and
   subpath the archive path with its ``<session>/scratchpad/`` prefix removed.
3. Scrubs home paths: the user's name after ``Users`` or ``home`` plus a run of path separators
   (backslashes in any number, so JSON-escaped paths too, or slashes) or a hyphen (the harness's
   project-folder slug), when no word character follows the name, becomes ``<user>``, any letter
   case. The name is read from the archive manifest's ``source_root``; it does not appear in this
   file. Nothing else in any file changes; a file that carries no such path is copied byte for byte,
   line endings included. A second, independent search for the name in those positions must then
   find nothing, and the bare name's remaining occurrences are counted and printed (the public
   author name in a copied test fixture is the expected residue).
4. Attributes a lane to every file from its session and its archive mtime: each session has one or
   more windows, each closed by one lane commit's author time (LANES below; the first commit listed
   in a window is the closing one, the others are the lane's other commits); a file falls in the
   first window whose cutoff is after its mtime. A file past every window is an error, not a guess.
5. Lists, without copying, the one file that is a derived index rather than a report or a script
   (NOT_COPIED: 14,915,488 bytes of number-to-path lookups that ``pool.py`` beside it rebuilds from
   the committed payloads). Its archive sha256, size and would-be path are recorded.
6. Writes MANIFEST.json (the rows the public cut exports, plus the withheld sessions and files by
   name and count with no digests, and exported-only totals beside the full ones) and
   MANIFEST_WITHHELD.json (the rows the public cut withholds: the critic rounds of the five
   public-cut lanes, which review the withheld export tool, its test and the plan and quote their
   text, digests and placeholders; one copy of docs/REPORT.md carrying the placeholders the export
   fills; and one diff of the withheld idea file). Every row records the archive path, session,
   lane, commits, mtime, both sizes, both digests (archive bytes and committed bytes), the
   substitution count, the line-ending form and the export status. The split keeps every digest of
   a withheld file out of the public manifest.

Run::

    python -I docs/audits/critic-recovered/recover.py --source <the archive folder> --date 2026-10-17
    python -I docs/audits/critic-recovered/recover.py --source <the archive folder> --date 2026-10-17 --check

``--check`` rebuilds everything in memory and compares it with the folder on disk, writing nothing;
a file on disk that the build would not write (beside README.md, gen_readme.py and this script) is
reported too, and write mode refuses to proceed over one. The output is deterministic given the
archive and ``--date``. tests/test_critic_recovered.py holds the folder to its manifests without the
archive; the folder is pinned ``-text`` in .gitattributes, its session folders are left out of ruff,
all of it is left out of the evidence-bytes citer scans, and it is frozen in the public cut.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
USER_TOKEN = "<user>"
SCRATCH_PREFIX = "scratchpad/"
OWN_FILES = ("MANIFEST.json", "MANIFEST_WITHHELD.json", "README.md", "recover.py", "gen_readme.py")

# Session transcript id -> lane windows, each (cutoff, lane, commits). The cutoff is the author time
# of the FIRST commit listed, as `git log --date=iso-strict` prints it (local offset kept; compared
# as instants); the commits after it are the lane's other commits, before or after the window. A
# file whose archive mtime is before the cutoff takes the window. Windows are chronological.
LANES: dict[str, list[tuple[str, str, str]]] = {
    "64064aa4-b9c8-45b6-9f59-46838015656c": [
        ("2026-10-01T08:06:31-04:00", "harness initialisation: results bytes stored as checked out and as cited", "ab12cbd, d614666"),
    ],
    "4f289fb0-652a-439c-a5cf-abf830e63352": [
        ("2026-10-01T13:34:00-04:00", "free-bigram twin of F-26's margin: registration rounds", "d55e62f, 6eaabf4"),
    ],
    "12e6097a-8666-465a-b5a3-e76024a56cff": [
        ("2026-10-02T18:45:54-04:00", "R1 stratified coverage read: registration rounds", "fea2431"),
        ("2026-10-02T19:47:18-04:00", "R1 stratified coverage read: landing rounds", "09e846b"),
    ],
    "38e3cfca-4ea6-4df8-ad3b-d4716d1f4b4a": [
        ("2026-10-02T22:11:28-04:00", "derived ledgers levelled after the stratified read", "b35a202"),
    ],
    "bd3df22e-cbe2-4aa0-9fa2-1f8c060c993b": [
        ("2026-10-03T04:59:08-04:00", "R2 generalising free baseline: registration round", "2fe5926"),
        ("2026-10-03T17:49:26-04:00", "R2 generalising free baseline: landing rounds", "2f13134"),
    ],
    "58dc4aea-78c6-4f4b-bdbd-daf075114c98": [
        ("2026-10-03T20:47:32-04:00", "landing-text kit: the diff-mode read over the record files", "cf4eccf"),
    ],
    "d880d7a7-5b03-4222-a6bf-23f7b5705b02": [
        ("2026-10-04T01:16:35-04:00", "EVID-1: sha-cited files outside results/ stored as cited", "0eb73d9"),
    ],
    "ae76f7e0-b675-4f4b-8fcc-ef4ee8f05d7c": [
        ("2026-10-04T06:01:45-04:00", "horizon read at the R2 encoding: registration round", "b41d3f3"),
    ],
    "fdeffb05-309a-409b-9a03-d56ff41b9815": [
        ("2026-10-05T00:11:19-04:00", "seed-noise floor readouts (F-27): landing rounds", "73d8dc2, 906edfd"),
        ("2026-10-05T02:49:49-04:00", "reader-and-lens re-test at S3: registration rounds", "b128fda"),
        ("2026-10-05T07:41:55-04:00", "reader-and-lens stage LENS (F-28): landing rounds", "9bbe905"),
        ("2026-10-05T14:42:42-04:00", "reader-and-lens stage READERS: landing rounds", "34078d1"),
        ("2026-10-09T17:06:31-04:00", "reader-and-lens stage READERS-LONG: landing rounds", "7f0af3e"),
    ],
    "4efb2604-196f-4619-a6f7-dea2fa75cc20": [
        ("2026-10-09T21:13:57-04:00", "OQ-20 seed replay of the verdict legs: registration rounds", "b6d3701, 9163706"),
    ],
    "b10c3ea1-ddef-43f8-a561-0b70da6c8f93": [
        ("2026-10-13T08:58:10-04:00", "public cut: the export tool, commit A", "3e7b744"),
    ],
    "46731adb-36bf-4335-804f-ca396f161653": [
        ("2026-10-13T23:29:08-04:00", "public cut: commit B, the pinned export and its proof", "977ff11"),
    ],
    "a8adf32c-e575-46a3-99cc-cb0de01adb55": [
        ("2026-10-14T08:18:25-04:00", "public cut: the front-doors lane", "d481935"),
    ],
    "c8cb4ef4-c63c-4089-a24d-8367ad2fda94": [
        ("2026-10-15T01:15:38-04:00", "public cut: decision batch lane 1, the gates", "51ceb9c"),
    ],
    "9dfaf64d-4621-4bfa-959a-dc14aeaa3790": [
        ("2026-10-15T14:14:34-04:00", "public cut: decision batch lane 2, the tool, the allowlist and the record", "5c264b0"),
    ],
    "4a635c95-32cd-4b83-b700-20e9fecdfde7": [
        ("2026-10-16T00:39:36-04:00", "image audit lane A: CI portability", "c41f9f1"),
    ],
}

# Sessions whose rounds the public cut withholds as a block, with the reason WITHHELD.md prints.
WITHHELD_SESSIONS: dict[str, str] = {
    s: "critic rounds of the public-cut lane (" + LANES[s][0][1].split(": ", 1)[1] + ", " + LANES[s][0][2]
       + "): they review the withheld export tool, its test and the plan, quoting their text, digests "
       "and placeholders, and go with them (plan 12; 14.2 item 3)"
    for s in ("b10c3ea1-ddef-43f8-a561-0b70da6c8f93", "46731adb-36bf-4335-804f-ca396f161653",
              "a8adf32c-e575-46a3-99cc-cb0de01adb55", "c8cb4ef4-c63c-4089-a24d-8367ad2fda94",
              "9dfaf64d-4621-4bfa-959a-dc14aeaa3790")
}
# Single files the public cut withholds, by archive path.
WITHHELD_FILES: dict[str, str] = {
    "58dc4aea-78c6-4f4b-bdbd-daf075114c98/scratchpad/critic/REPORT.md":
        "the critic's copy of docs/REPORT.md as of 2026-10-03, carrying the placeholders the export fills in the tracked file",
    "12e6097a-8666-465a-b5a3-e76024a56cff/scratchpad/strat/critic5/diff_ptrs.txt":
        "a diff hunk of the withheld idea file read by the R1 landing's fifth round; its lines go with the file they come from (plan section 3)",
}
# Archive files listed but not copied, by archive path.
NOT_COPIED: dict[str, str] = {
    "12e6097a-8666-465a-b5a3-e76024a56cff/scratchpad/strat/critic6/pool.json":
        "a derived index (every formatted number of the R1 payloads mapped to the JSON paths holding it), "
        "14,915,488 bytes, rebuilt by pool.py beside it from the committed payloads; not a report or a script",
}


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def eol_kind(b: bytes) -> str:
    crlf = b.count(b"\r\n")
    lf = b.count(b"\n") - crlf
    if crlf and lf:
        return "mixed"
    if crlf:
        return "crlf"
    if lf:
        return "lf"
    return "none"


def utc_day(iso: str) -> str:
    return datetime.fromisoformat(iso).astimezone(timezone.utc).date().isoformat()


def user_of(source_root: str) -> str:
    m = re.search(r"Users[\\/]+([^\\/]+)", source_root, re.I)
    if not m:
        raise SystemExit("the archive manifest's source_root names no Users/<name> segment: " + source_root)
    return m.group(1)


def scrub_pattern(user: str) -> re.Pattern[bytes]:
    """``Users`` + a run of separators (backslashes or slashes) or the hyphen of the harness's project slug, or
    ``home`` + a run of separators, then the name with no word character after it; any case."""
    return re.compile(rb"(users(?:[\\/]+|-)|home[\\/]+)" + re.escape(user.encode("utf-8")) + rb"(?![A-Za-z0-9_])", re.I)


def survival_pattern(user: str) -> re.Pattern[bytes]:
    """An independent second look for the name in a home-path position, written apart from the scrub."""
    return re.compile(rb"(?:users[\\/-]+|home[\\/]+)" + re.escape(user.encode("utf-8")) + rb"(?:[^A-Za-z0-9_]|$)", re.I)


def scrub(b: bytes, pat: re.Pattern[bytes]) -> tuple[bytes, int]:
    return pat.subn(rb"\1" + USER_TOKEN.encode("utf-8"), b)


def scrub_text(s: str, pat: re.Pattern[bytes]) -> str:
    return scrub(s.encode("utf-8"), pat)[0].decode("utf-8")


def lane_of(session: str, mtime: str) -> tuple[str, str]:
    t = datetime.fromisoformat(mtime)
    for cutoff, lane, commits in LANES[session]:
        if t < datetime.fromisoformat(cutoff):
            return lane, commits
    raise SystemExit(f"{session}: a file at {mtime} falls past every lane window; extend LANES")


def load_archive(source: Path) -> tuple[dict, str, list[str]]:
    """The archive manifest, its own sha256, and the list of files on disk (archive-relative, posix)."""
    mp = source / "MANIFEST.json"
    raw = mp.read_bytes()
    man = json.loads(raw.decode("utf-8"))
    on_disk = sorted(p.relative_to(source).as_posix() for p in source.rglob("*") if p.is_file() and p != mp)
    listed = sorted(f["path"] for f in man["files"])
    if on_disk != listed or len(listed) != man["n_files"]:
        extra = sorted(set(on_disk) - set(listed))
        missing = sorted(set(listed) - set(on_disk))
        raise SystemExit(f"archive and manifest disagree: {len(extra)} unlisted, {len(missing)} missing; "
                         f"e.g. {extra[:3]} / {missing[:3]}")
    for f in man["files"]:
        b = (source / f["path"]).read_bytes()
        if sha256(b) != f["sha256"] or len(b) != f["bytes"]:
            raise SystemExit("archive file differs from its manifest entry: " + f["path"])
    return man, sha256(raw), on_disk


def build(source: Path, date: str) -> tuple[dict[str, bytes], dict, dict, dict]:
    """(files to write: committed path -> bytes, MANIFEST.json object, MANIFEST_WITHHELD.json object,
    the bare name's remaining occurrences by committed path)."""
    man, man_sha, _ = load_archive(source)
    user = user_of(man["source_root"])
    pat, alive = scrub_pattern(user), survival_pattern(user)
    bare = re.compile(rb"(?<![A-Za-z0-9_])" + re.escape(user.encode("utf-8")) + rb"(?![A-Za-z0-9_])", re.I)
    first_day: dict[str, str] = {}
    for f in man["files"]:
        s = f["path"].split("/", 1)[0]
        d = utc_day(f["mtime"])
        first_day[s] = min(first_day.get(s, d), d)
    unknown = sorted(set(first_day) - set(LANES))
    if unknown:
        raise SystemExit("sessions without a lane window: " + ", ".join(unknown))
    out: dict[str, bytes] = {}
    rows: list[dict] = []
    not_copied: list[dict] = []
    bare_left: dict[str, int] = {}
    for f in sorted(man["files"], key=lambda x: x["path"]):
        session, rest = f["path"].split("/", 1)
        if not rest.startswith(SCRATCH_PREFIX):
            raise SystemExit("archive path outside scratchpad/: " + f["path"])
        lane, commits = lane_of(session, f["mtime"])
        path = f"{first_day[session]}-{session[:8]}/{rest[len(SCRATCH_PREFIX):]}"
        base = {"source_path": f["path"], "session": session, "lane": lane, "commits": commits,
                "mtime": f["mtime"], "bytes_source": f["bytes"], "sha256_source": f["sha256"]}
        if f["path"] in NOT_COPIED:
            not_copied.append({"path": path, **base, "why": NOT_COPIED[f["path"]]})
            continue
        b, n = scrub((source / f["path"]).read_bytes(), pat)
        if alive.search(b):
            raise SystemExit("a home path survived the scrub in " + f["path"])
        left = len(bare.findall(b))
        if left:
            bare_left[path] = left
        out[path] = b
        withheld = session in WITHHELD_SESSIONS or f["path"] in WITHHELD_FILES
        rows.append({"path": path, **base, "bytes": len(b), "sha256": sha256(b), "substitutions": n,
                     "eol": eol_kind(b), "export": "withheld" if withheld else "exported"})
    exported = [r for r in rows if r["export"] == "exported"]
    withheld_rows = [r for r in rows if r["export"] == "withheld"]
    # the public manifest names every withheld file (path and whether it is empty, never a digest or a
    # size), so the README's word index and its table render from MANIFEST.json alone in the public clone
    withheld_summary = [
        {"dir": f"{first_day[s]}-{s[:8]}", "session": s, "lane": LANES[s][0][1], "commits": LANES[s][0][2],
         "n_files": sum(1 for r in withheld_rows if r["session"] == s), "reason": why,
         "files": [{"path": r["path"], "empty": r["bytes"] == 0} for r in withheld_rows if r["session"] == s]}
        for s, why in WITHHELD_SESSIONS.items()
    ] + [
        {"path": next(r["path"] for r in rows if r["source_path"] == sp), "session": sp.split("/", 1)[0],
         "n_files": 1, "reason": why,
         "files": [{"path": r["path"], "empty": r["bytes"] == 0} for r in withheld_rows if r["source_path"] == sp]}
        for sp, why in WITHHELD_FILES.items()
    ]
    counts = {"archive": man["n_files"], "copied": len(rows), "exported": len(exported),
              "withheld": len(withheld_rows), "not_copied": len(not_copied),
              "scrubbed_files": sum(1 for r in rows if r["substitutions"]),
              "substitutions": sum(r["substitutions"] for r in rows),
              "scrubbed_files_exported": sum(1 for r in exported if r["substitutions"]),
              "substitutions_exported": sum(r["substitutions"] for r in exported),
              "bare_name_occurrences_left": sum(bare_left.values()),
              "bare_name_files_left": len(bare_left)}
    header = {
        "recovered_on": date,
        "archive": {"name": source.name, "copied": man["copied"], "source_root": scrub_text(man["source_root"], pat),
                    "n_files": man["n_files"], "manifest_sha256": man_sha,
                    "rule": "the files directly inside a folder whose name starts with critic, with the suffix .py, "
                            ".txt, .json or .md; nothing nested below such a folder, nothing of another suffix "
                            "(recovered from the archive on 2026-10-17; it rebuilds the archive exactly)"},
        "user_token": USER_TOKEN,
        "layout": "<UTC day of the session's earliest file>-<first 8 of the session id>/<archive path minus "
                  "'<session>/scratchpad/'>",
        "scrub": "the user's name after 'Users' or 'home' plus a run of path separators or a hyphen, with no word "
                 "character after it, any case, replaced by the user token; nothing else changed; line endings kept",
        "lane_rule": "the first window of the file's session whose cutoff (the author time of the first commit the "
                     "window lists) is after the file's archive mtime (recover.py LANES)",
        "counts": counts,
        "sessions": [{"dir": f"{first_day[s]}-{s[:8]}", "session": s, "n_files": sum(1 for r in rows if r["session"] == s),
                      "substitutions": sum(r["substitutions"] for r in rows if r["session"] == s),
                      "windows": [{"before": c, "lane": lane, "commits": cm, "cutoff_commit": cm.split(",")[0].strip(),
                                   "n_files": sum(1 for r in rows if r["session"] == s and (r["lane"], r["commits"]) == (lane, cm))}
                                  for c, lane, cm in LANES[s]]}
                     for s in sorted(LANES, key=lambda s: first_day[s])],
    }
    public = {**header, "withheld": withheld_summary, "not_copied": not_copied,
              "files_note": "the exported rows; the withheld rows, digests included, are in MANIFEST_WITHHELD.json, "
                            "which the public cut withholds with them",
              "files": exported}
    withheld_doc = {**header, "files_note": "the rows the public cut withholds; MANIFEST.json lists them by session and count",
                    "files": withheld_rows}
    return out, public, withheld_doc, bare_left


def dumps(obj: dict) -> bytes:
    return (json.dumps(obj, indent=1, ensure_ascii=True) + "\n").encode("utf-8")


def on_disk_files(out_dir: Path) -> set[str]:
    return {p.relative_to(out_dir).as_posix() for p in out_dir.rglob("*")
            if p.is_file() and "__pycache__" not in p.parts}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--source", required=True, help="the dated archive folder (its MANIFEST.json beside its files)")
    ap.add_argument("--date", required=True, help="the recovery date written into the manifests (YYYY-MM-DD)")
    ap.add_argument("--out", default=str(HERE), help="the folder to write (default: this script's folder)")
    ap.add_argument("--check", action="store_true", help="rebuild in memory and compare with --out; write nothing")
    a = ap.parse_args(argv)
    source, out_dir = Path(a.source), Path(a.out)
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", a.date):
        raise SystemExit("--date must be YYYY-MM-DD")
    files, public, withheld, bare_left = build(source, a.date)
    files = {**files, "MANIFEST.json": dumps(public), "MANIFEST_WITHHELD.json": dumps(withheld)}
    stale = sorted(on_disk_files(out_dir) - set(files) - set(OWN_FILES)) if out_dir.exists() else []
    changed: list[str] = []
    for rel, b in files.items():
        p = out_dir / rel
        if not p.exists() or p.read_bytes() != b:
            changed.append(rel)
    c = public["counts"]
    verb = "would change" if a.check else "wrote"
    if stale:
        print(f"{len(stale)} file(s) under {out_dir} that this build would not write:", *stale[:10], sep="\n  ")
        if not a.check:
            print("refusing to write over them; remove them first")
            return 1
    if not a.check:
        for rel in changed:
            p = out_dir / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(files[rel])
    print(f"archive {source.name}: {c['archive']} files; copied {c['copied']} ({c['exported']} exported, "
          f"{c['withheld']} withheld), {c['not_copied']} listed and not copied; {c['scrubbed_files']} files scrubbed, "
          f"{c['substitutions']} substitutions ({c['scrubbed_files_exported']} files, {c['substitutions_exported']} in "
          f"the exported rows); the bare name left in {c['bare_name_files_left']} file(s), {c['bare_name_occurrences_left']} "
          f"occurrence(s): {', '.join(sorted(bare_left)) or 'none'}; {verb} {len(changed)} of {len(files)} files under {out_dir}")
    if a.check and (changed or stale):
        if changed:
            print("differs:", *changed[:10], sep="\n  ")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
