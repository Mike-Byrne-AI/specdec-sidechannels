"""tests/test_evidence_bytes.py — committed evidence under results/ is stored byte
for byte as cited.

`.gitattributes` keeps results/** byte-exact (`-text`) because provenance records
cite the sha256 of a results file's bytes. Written 2026-10-01 after 84 tracked
results files were found LF in the index and CRLF on disk behind a clean
`git status` (a stale stat cache): a fresh clone reproduced the LF bytes and
broke every chain citing those files' CRLF shas. Scope on 2026-10-01: results/
only; the same class for sha-cited files under data/, tools/ and docs/ (twelve
files then, none with a `-text` attribute) was forward-ledger row EVID-1, closed
2026-10-03 by check 4 below: fifteen cited files pinned `-text` and stored as
they are on disk (six of them CRLF, the bytes their 99 citations name, of 186 in all).

Five checks, all over TRACKED files (a worktree may also hold gitignored smoke
payloads); checks 1 to 4 parse no provenance layout (a 64-hex search over every
tracked text file, so a citation under any key counts) and check 5 reads the
receipts' own fields:
  1. every tracked file under results/ hashes, unfiltered, to its index blob, so
     a checkout reproduces the bytes this tree cites (on a fresh checkout under
     `-text` this holds by construction; it guards long-lived worktrees);
     intent-to-add entries (`git add -N`, which git diff lists as added files)
     are left out of the comparison and named in any failure message;
  2. no tracked text file cites the sha256 of a results file's OTHER
     line-ending twin (the LF twin of a CRLF file, or the reverse): such a sha
     is a chain that broke when the bytes were converted;
  3. no results file is cited fewer times than at HEAD: the number of
     occurrences of a results file's current sha256 across the other tracked
     text files must be at least the number of occurrences of its HEAD sha256
     at HEAD, so a regenerated, edited, renamed or deleted cited file is named
     with both counts;
  4. every tracked file OUTSIDE results/ whose sha256 another tracked text file
     cites (its disk bytes, or either line-ending twin of them) carries the
     `-text` attribute in both the worktree's and the index's .gitattributes,
     is cited by its DISK bytes only, hashes on disk to its index blob, and is
     cited no fewer times than at HEAD. A citation of another line-ending form
     of the disk bytes is a STALE CHECKOUT when the index still holds the cited
     bytes (an autocrlf=true checkout that pulled a new `-text` line keeps its
     CRLF copy of an LF blob) and an unreproducible chain otherwise. The set is
     derived from the citations, so a new sha-cited instrument without its
     `.gitattributes` line goes red here once a payload cites its sha; a file
     pinned only by a 12-hex sha in prose (a freeze record) is listed by hand in
     HAND_PINNED and held to the attribute the same way. The export tool's proof
     receipts (the tracked `.json` files under FOLDED_CITERS) are not citers here,
     at HEAD or now: a receipt is the record of a past export, and check 5 holds
     it instead (dated 2026-10-14, call PC-4 of the public-cut decision batch; it
     supersedes the 2026-10-13 form, which kept the receipts as citers, so that an
     uncommitted edit to the tool or the allowlist went red on this check's
     HEAD-count, the file's new bytes being cited nowhere while HEAD's were cited
     by the receipt, until a receipt citing the new digest landed with the edit:
     the "receipt lock" of docs/PUBLIC_CUT_PLAN.md 12.7; the reasons no `-text`  # [withheld: docs/PUBLIC_CUT_PLAN.md not in this repository; see WITHHELD.md]
     line can pin those files stand there and in docs/SHARP_EDGES.md). A file a
     receipt cites that another tracked text file ALSO cites is back in this
     check, with the `-text` remedy the tool refuses for a withheld file, so a
     record never quotes a receipt's full digest;
  5. every tracked `.json` receipt under FOLDED_CITERS is, when HEAD holds it,
     byte-identical to HEAD's copy once CRLF is folded (a receipt is never
     edited); parses as JSON; names a 40-hex `source_commit` that is an ancestor
     of HEAD; and every 64-hex string under a key that names a sha256, at any
     depth, is the digest, as stored or with CRLF folded to LF (the fold the tool
     computes for itself on any checkout), of the file the key names at that
     commit (`tool_sha256` and `tool_sha256_at_proof` the tool, `allowlist_sha256`
     the allowlist) or, for a key this file does not know, of some file outside
     results/ there; and no receipt tracked at HEAD is missing from the tree or
     from disk. A digest that names bytes no commit holds (an uncommitted tool's,
     or the allowlist digest of a `--worktree-sources` export, which on this
     checkout is taken over CRLF worktree bytes) is refused: commit the sources,
     export from that commit, prove again. A receipt with no digest under a
     sha256 key, such as the 2026-10-12 worktree-sources receipt, binds nothing
     and passes; a string under such a key that is not 64 lowercase hex is
     refused, and a null binds nothing. The worktree and the index are not
     consulted for a receipt-cited file. What this form gives up, by that call: a
     committed edit to the tool or the allowlist no longer needs a receipt beside
     it, so the newest receipt may describe an older tool, and nothing here makes
     the next export's receipt follow. The guard is HEAD-relative, as check 3 is,
     and holds with no receipt at all (the public cut withholds docs/public_cut/,  # [withheld: docs/public_cut/ not in this repository; see WITHHELD.md]
     so it passes there with none, by design).
Remedy split: a file test 1 names that nothing cites may simply be committed
(churn); a cited one is restored with `git checkout -- <file>` or re-cited by
the registered landing that regenerated it. Check 4's messages each name their
own remedy: add and stage the `-text` line; for an untracked HAND_PINNED path,
update the list or `git add` the file; for a stale checkout restore the
index bytes to disk (`python tools/landing_text.py eol --fix-lf <file>` for an
LF-stored file), never renormalise; for an unreproducible chain restore the
cited bytes, never the citation; `git add --renormalize -- <path>` only when the
disk bytes are the cited bytes and the index differs; for a file cited fewer
times than at HEAD restore the bytes or re-cite through the registered landing,
never by editing the citation. Check 5's messages: a receipt that is gone or
missing on disk, that differs from HEAD's copy, that is not JSON, that names no
source commit or one that is not an ancestor of HEAD, that carries a sha256
string that is not 64 lowercase hex, or whose digest is not its file's at that
commit, is restored from history or, when it is new, re-made from an export of
committed sources; never edited. Nothing here imports torch; git
runs through subprocess.

Dated note 2026-10-16 (lane C of the 2026-10-15 image audit, item S6b-C-1): checks 1 to 5
are index- or HEAD-relative, so a hand-edit of a cited results file that is then committed
passes all five. Check 6, at the end of this file, is absolute: tests/evidence_pins.json
records every cited digest that resolved to a tracked file's bytes on the day it was written
(tools/evidence_pins.py --write), and the check recomputes the list from the tree and requires
the same digests resolving to the same files. A registered landing that cites a new digest
regenerates the file and commits it beside the landing; the check fails on an unlisted new
resolution, so the regeneration is part of landing."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HEX64 = re.compile(rb"[0-9a-f]{64}")
TEXT_SUFFIXES = (".json", ".jsonl", ".md", ".py", ".txt", ".toml", ".yml", ".yaml")
# anti-vacuity only: the per-file comparison with HEAD (test 3) is the detector.
# 556 citation occurrences across 68 cited files were counted on 2026-10-01.
MIN_CITATIONS = 100
# anti-vacuity only, for check 4: 186 citations of 15 files outside results/
# were counted on 2026-10-03.
MIN_OUTSIDE_CITATIONS = 50
# files a freeze record pins by a 12-hex sha in prose (outside the 64-hex scan), held to
# the `-text` attribute by hand: docs/BLUEPRINT.md's R2 freeze record pins this test file
# by its raw LF bytes (c9a8efa7cd5e, 2026-10-03); the horizon read's freeze record pins
# tests/test_prefetch_horizon.py the same way (2026-10-04), the seed-noise floor's
# freeze record pins tests/test_noise_floor.py (2026-10-04), and the reader-and-lens re-test's
# freeze record pins tests/test_reader_lens.py and the lens builder tools/build_balanced_groups.py
# (2026-10-05; the builder's sha is cited in the registration block), and the OQ-20 seed replay's
# freeze record pins tests/test_seed_replay.py (2026-10-09).
HAND_PINNED = ("tests/test_prefetch_r2.py", "tests/test_prefetch_horizon.py", "tests/test_noise_floor.py",
               "tests/test_reader_lens.py", "tools/build_balanced_groups.py", "tests/test_seed_replay.py",
               "tests/test_reader_s1.py")
# The export tool's proof receipts (tracked `.json` files under these prefixes) cite `tool_sha256` (the
# tool's bytes with CRLF folded to LF before hashing, `tool_digest()` in tools/export_public_cut.py)  # [withheld: tools/export_public_cut.py not in this repository; see WITHHELD.md]
# and `allowlist_sha256` (the blob of docs/public_cut/tone_allowlist.txt at the pinned commit when  # [withheld: docs/public_cut/ not in this repository; see WITHHELD.md]
# the export ran without --worktree-sources; a worktree-sources export hashes the worktree copy, CRLF
# on this checkout, which check 5 refuses when it folds to no blob at the source commit; a
# worktree-sources receipt that carries no digest binds nothing and passes). Both cited files are
# withheld from the public cut, and
# no `-text` line can pin them (2026-10-13: a literal line naming one is refused by the tool at
# export, a `*` glob breaks the real-tree frozen-set oracle of tests/test_export_public_cut.py, a `?`  # [withheld: tests/test_export_public_cut.py not in this repository; see WITHHELD.md]
# or bracket glob only hides the name from the mention guard; docs/SHARP_EDGES.md has the entry).
# 2026-10-15 (lane 2 of the batch): a literal line naming one is now DROPPED at export and listed in
# WITHHELD.md rather than refused, and the tool's frozen set is what `git check-attr` itself says over
# the tree's attribute files in a scratch repository; the real-tree oracle of
# tests/test_export_public_cut.py still reads literal lines only, so a glob pin still needs that oracle  # [withheld: tests/test_export_public_cut.py not in this repository; see WITHHELD.md]
# extended by hand. The route below stands either way.
# 2026-10-13 kept the receipts as citers of check 4, which made every uncommitted edit to the tool or
# the allowlist red on the HEAD-count until a fresh proof landed with it (docs/PUBLIC_CUT_PLAN.md  # [withheld: docs/PUBLIC_CUT_PLAN.md not in this repository; see WITHHELD.md]
# 12.7). Since 2026-10-14 (call PC-4 of the public-cut decision batch) receipts are never citers of
# check 4 and check 5 binds each receipt at the commit it names. A hand pin in HAND_PINNED brings the
# attribute back for its file as before; so does a second, non-receipt citer of a receipt-cited file.
FOLDED_CITERS = ("docs/public_cut/proofs/",)  # [withheld: docs/public_cut/ not in this repository; see WITHHELD.md]
# The recovered critic folder (2026-10-17, docs/PUBLIC_CUT_PLAN.md 14.2 item 3): the reviewer's own recompute  # [withheld: docs/PUBLIC_CUT_PLAN.md not in this repository; see WITHHELD.md]
# scripts and reports, copied from the author's scratch with their bytes pinned by the folder's manifests.
# They quote digests of results files and instruments in whichever line-ending form the reviewer hashed,
# and the manifests quote the folder's own digests; none of that is a citation the record makes, so every
# file under the folder (manifests included) is left out as a CITER of checks 2 to 4 and 6. Its files stay
# citation TARGETS like any tracked file. tools/evidence_pins.py keeps the same tuple
# (test_pins_tool_scope_matches_this_file); tests/test_critic_recovered.py holds the folder to its manifests.
RECOVERED_PREFIXES = ("docs/audits/critic-recovered/",)
# the receipt keys whose digest names a known file (check 5 binds them to that path at the source commit)
RECEIPT_PATH_KEYS = {"tool_sha256": "tools/export_public_cut.py", "tool_sha256_at_proof": "tools/export_public_cut.py",  # [withheld: tools/export_public_cut.py not in this repository; see WITHHELD.md]
                     "allowlist_sha256": "docs/public_cut/tone_allowlist.txt"}  # [withheld: docs/public_cut/ not in this repository; see WITHHELD.md]


def _git(*args: str, data: bytes | None = None) -> bytes:
    proc = subprocess.run(["git", *args], cwd=ROOT, input=data, capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args[:2])} failed: {proc.stderr.decode('utf-8', 'replace').strip()}")
    return proc.stdout


# "" when ROOT is the repository's top level; "<dir>/" when this tree is a subfolder of a larger
# checkout (the public specdec-sidechannels layout keeps it under sideband/). ls-files, ls-tree
# and check-attr speak in cwd-relative paths; an object name ("HEAD:<path>", ":<path>"),
# `hash-object --stdin-paths` and `diff --name-only` take or print top-level paths, so those get
# the prefix added or stripped (measured 2026-10-13 in the public cut's fresh clone, where both
# hash-object checks failed without it). Outside a git checkout (a tarball) the prefix is "" and
# the tests fail on their git calls as before.
try:
    PREFIX = _git("rev-parse", "--show-prefix").decode("utf-8").strip()
except RuntimeError:
    PREFIX = ""


def _z(out: bytes) -> list[str]:
    return [p for p in out.decode("utf-8", "surrogateescape").split("\0") if p]


def _tracked() -> list[str]:
    return _z(_git("ls-files", "-z"))


def _intent_to_add(prefix: str) -> set[str]:
    """Paths staged with `git add -N`: git diff lists them as added files (top-level
    paths, so the subfolder prefix is stripped)."""
    out = _z(_git("diff", "--name-only", "--diff-filter=A", "-z", "--", prefix))
    return {p[len(PREFIX):] if PREFIX and p.startswith(PREFIX) else p for p in out}


def _tracked_results_with_blobs() -> list[tuple[str, str]]:
    """(repo-relative path, index blob id) for every tracked file under results/."""
    rows: list[tuple[str, str]] = []
    for rec in _z(_git("ls-files", "-s", "-z", "--", "results")):
        meta, path = rec.split("\t", 1)
        rows.append((path, meta.split()[1]))
    return rows


def test_every_tracked_results_file_hashes_to_its_index_blob():
    rows = _tracked_results_with_blobs()
    assert rows, "no tracked files under results/"
    intent_to_add = sorted(_intent_to_add("results"))
    rows = [(p, blob) for p, blob in rows if p not in intent_to_add]
    paths = "\n".join(PREFIX + p for p, _ in rows) + "\n"
    # --no-filters hashes the bytes as they are on disk, ignoring attributes and
    # autocrlf: equality with the index blob is exactly "stored as checked out".
    disk = _git("hash-object", "--no-filters", "--stdin-paths", data=paths.encode("utf-8")).decode().split()
    assert len(disk) == len(rows)
    mismatched = [p for (p, blob), d in zip(rows, disk) if d != blob]
    assert mismatched == [], (
        f"{len(mismatched)} results files differ from their committed bytes "
        f"(line endings or content), e.g. {mismatched[:5]}; an uncited file may be committed as churn, "
        f"a cited one is restored with `git checkout -- <file>` or re-cited by its landing"
        + (f"; intent-to-add entries not compared: {intent_to_add}" if intent_to_add else "")
    )


def _twin(b: bytes) -> bytes:
    """The other line-ending version of ``b``: LF for a CRLF file, CRLF otherwise."""
    return b.replace(b"\r\n", b"\n") if b"\r\n" in b else b.replace(b"\n", b"\r\n")


def _is_text(path: str) -> bool:
    return path.endswith(TEXT_SUFFIXES)


def _is_citer(path: str) -> bool:
    """A tracked text file whose 64-hex digests count as citations: every text file except the
    recovered critic folder (RECOVERED_PREFIXES); check 4 also leaves out the receipts (_is_receipt)."""
    return _is_text(path) and not path.startswith(RECOVERED_PREFIXES)


def _citation_counts(read, paths: list[str]) -> dict[str, int]:
    """For every results/ path: how many times its sha256 (as ``read`` sees it)
    occurs in OTHER citing text files (as ``read`` sees them)."""
    actual: dict[bytes, str] = {}
    for p in paths:
        if p.startswith("results/"):
            actual[hashlib.sha256(read(p)).hexdigest().encode()] = p
    counts = {p: 0 for p in actual.values()}
    for p in paths:
        if not _is_citer(p):
            continue
        for m in HEX64.finditer(read(p)):
            q = actual.get(m.group(0))
            if q is not None and q != p:
                counts[q] += 1
    return counts


def test_no_tracked_file_cites_a_results_files_other_line_ending_twin():
    tracked = _tracked()
    actual: dict[bytes, str] = {}
    twin: dict[bytes, str] = {}
    for p in tracked:
        if not p.startswith("results/"):
            continue
        b = (ROOT / p).read_bytes()
        a = hashlib.sha256(b).hexdigest().encode()
        actual[a] = p
        t = hashlib.sha256(_twin(b)).hexdigest().encode()
        if t != a:
            twin[t] = p
    assert actual, "no tracked files under results/"
    cited = 0
    broken: list[tuple[str, str]] = []
    for p in tracked:
        if not _is_citer(p):
            continue
        for m in HEX64.finditer((ROOT / p).read_bytes()):
            h = m.group(0)
            if h in actual:
                if actual[h] != p:
                    cited += 1
            elif h in twin and twin[h] != p:
                broken.append((p, twin[h]))
    # the diagnosis first: a broken chain also lowers `cited`
    assert broken == [], (
        f"{len(broken)} citations name a results file's other line-ending twin "
        f"(citing file, cited file), e.g. {broken[:5]}; restore the cited file's bytes, never the citation"
    )
    assert cited >= MIN_CITATIONS, (
        f"{cited} < {MIN_CITATIONS} citations of tracked results files found: the scan or the tree changed"
    )


def _blob_reader(prefix: str, paths: list[str]) -> dict[str, bytes]:
    """``prefix`` + path -> bytes, one cat-file batch: ``"HEAD:"`` reads HEAD's versions,
    ``":"`` the index's (stage 0)."""
    specs = "\n".join(f"{prefix}{PREFIX}{p}" for p in paths) + "\n"
    out = _git("cat-file", "--batch", data=specs.encode("utf-8"))
    blobs: dict[str, bytes] = {}
    pos = 0
    for p in paths:
        nl = out.index(b"\n", pos)
        header = out[pos:nl].decode()
        if header.endswith(" missing"):
            pos = nl + 1
            continue
        size = int(header.rsplit(" ", 1)[1])
        blobs[p] = out[nl + 1 : nl + 1 + size]
        pos = nl + 1 + size + 1
    return blobs


def _head_reader(paths: list[str]) -> dict[str, bytes]:
    """HEAD's versions of ``paths`` (one cat-file batch)."""
    return _blob_reader("HEAD:", paths)


def test_no_results_file_lost_citations_relative_to_head():
    head_paths = [p for p in _z(_git("ls-tree", "-r", "-z", "--name-only", "HEAD"))
                  if p.startswith("results/") or _is_text(p)]
    head_blobs = _head_reader(head_paths)
    head_counts = _citation_counts(lambda p: head_blobs.get(p, b""), [p for p in head_paths if p in head_blobs])
    now_paths = [p for p in _tracked() if p.startswith("results/") or _is_text(p)]
    now_counts = _citation_counts(lambda p: (ROOT / p).read_bytes(), now_paths)
    dropped = sorted((p, n, now_counts.get(p, 0)) for p, n in head_counts.items() if now_counts.get(p, 0) < n)
    assert dropped == [], (
        "results files cited fewer times than at HEAD (path, at HEAD, now): "
        f"{dropped[:8]}; the file's bytes changed, or it was renamed or deleted, or a citing file dropped it"
    )


def _index_blobs(paths: list[str]) -> dict[str, str]:
    """path -> index blob id for the given tracked paths (the whole index listed once,
    so no path reaches the command line as a pathspec)."""
    wanted = set(paths)
    blobs: dict[str, str] = {}
    for rec in _z(_git("ls-files", "-s", "-z")):
        meta, path = rec.split("\t", 1)
        if path in wanted:
            blobs[path] = meta.split()[1]
    return blobs


def _attr_pass(stdin: bytes, *extra: str) -> dict[str, str]:
    fields = _z(_git("check-attr", "-z", "--stdin", *extra, "text", data=stdin))
    return {fields[i]: fields[i + 2] for i in range(0, len(fields) - 2, 3)}


def _text_attr(paths: list[str]) -> dict[str, str]:
    """path -> the `text` attribute as git resolves it: 'unset' only when BOTH the worktree's
    .gitattributes and the index's (`--cached`, what a fresh clone gets) carry the `-text`
    line; otherwise the first non-'unset' value ('unspecified' when no attribute names the
    path, 'set' or a value). Both are read because this repository commits with
    `git commit -- <paths>`, which takes the worktree copy, so an unstaged removal counts."""
    stdin = ("\0".join(paths) + "\0").encode("utf-8")
    worktree = _attr_pass(stdin)
    cached = _attr_pass(stdin, "--cached")
    return {p: (v if v != "unset" else cached.get(p, "unspecified")) for p, v in worktree.items()}


def _forms(b: bytes) -> list[tuple[str, bytes]]:
    """(kind, sha256) of ``b`` as it is ("disk"), LF-normalised ("lf") and CRLF-normalised
    ("crlf"), one entry per distinct form: "disk" absorbs whichever twin equals it, so "lf"
    survives for a CRLF file (or one with mixed endings) and "crlf" for an LF (or mixed) file."""
    lf = b.replace(b"\r\n", b"\n")
    out: list[tuple[str, bytes]] = []
    seen: set[bytes] = set()
    for kind, x in (("disk", b), ("lf", lf), ("crlf", lf.replace(b"\n", b"\r\n"))):
        h = hashlib.sha256(x).hexdigest().encode()
        if h not in seen:
            seen.add(h)
            out.append((kind, h))
    return out


def _is_receipt(path: str) -> bool:
    return path.startswith(FOLDED_CITERS) and path.endswith(".json")


def _outside_citation_counts(read, paths: list[str]) -> dict[str, dict[str, int]]:
    """For every path outside results/ (as ``read`` sees it): how many times each
    line-ending form of its sha256 occurs in OTHER citing text files (as ``read`` sees
    them), the receipts under FOLDED_CITERS left out as citers (check 5 holds
    them) and the recovered critic folder too (RECOVERED_PREFIXES); only cited paths are keys."""
    forms: dict[bytes, list[tuple[str, str]]] = {}
    for p in paths:
        if not p.startswith("results/"):
            for kind, h in _forms(read(p)):
                forms.setdefault(h, []).append((p, kind))
    counts: dict[str, dict[str, int]] = {}
    for p in paths:
        if not _is_citer(p) or _is_receipt(p):
            continue
        for m in HEX64.finditer(read(p)):
            for q, kind in forms.get(m.group(0), ()):
                if q != p:
                    counts.setdefault(q, {}).setdefault(kind, 0)
                    counts[q][kind] += 1
    return counts


def _lf_sha(b: bytes) -> bytes:
    return hashlib.sha256(b.replace(b"\r\n", b"\n")).hexdigest().encode()


def test_every_cited_file_outside_results_is_stored_and_checked_out_as_cited():
    tracked = _tracked()
    now = _outside_citation_counts(lambda p: (ROOT / p).read_bytes(), tracked)
    total = sum(sum(c.values()) for c in now.values())
    assert total >= MIN_OUTSIDE_CITATIONS, (
        f"{total} < {MIN_OUTSIDE_CITATIONS} citations of tracked files outside results/ found: "
        "the scan or the tree changed"
    )
    paths = sorted(now)
    missing_hand_pins = sorted(set(HAND_PINNED) - set(tracked))
    assert missing_hand_pins == [], (
        f"HAND_PINNED names untracked paths {missing_hand_pins} (renamed, deleted or not yet added); update the list or `git add` the file"
    )
    pinned_by_hand = [p for p in HAND_PINNED if p not in now]
    attrs = _text_attr(paths + pinned_by_hand)
    not_pinned = [p for p in paths + pinned_by_hand if attrs.get(p) != "unset"]
    assert not_pinned == [], (
        f"{len(not_pinned)} sha-cited files outside results/ (HAND_PINNED included) lack the `-text` attribute "
        f"(a checkout's core.autocrlf then decides their bytes): {not_pinned}; add `<path> -text` to "
        ".gitattributes and stage it (both the worktree's copy and the index's, what a clone gets, are read)"
    )
    # under `-text` a checkout writes the index blob, so only a citation of the DISK bytes reproduces. A
    # citation of another line-ending form of them is a STALE CHECKOUT when the index still holds the cited
    # bytes (an autocrlf=true checkout that pulled a new `-text` line keeps its CRLF copy of an LF blob and
    # `git status` stays clean), else a chain no checkout reproduces. The two have opposite remedies.
    intent_to_add = _intent_to_add(".") & set(paths)  # `git add -N`: no index blob to compare yet
    off_form = [(p, kind, n) for p in paths if p not in intent_to_add for kind, n in now[p].items() if kind != "disk"]
    stale: list[tuple[str, str, int]] = []
    unreproducible: list[tuple[str, str, int]] = []
    if off_form:
        index_bytes = _blob_reader(":", sorted({p for p, _, _ in off_form}))
        for p, kind, n in off_form:
            cited = dict(_forms((ROOT / p).read_bytes()))[kind]
            index_sha = hashlib.sha256(index_bytes.get(p, b"")).hexdigest().encode()
            (stale if index_sha == cited else unreproducible).append((p, kind, n))
    assert stale == [], (
        f"stale checkout: the index holds the cited bytes but the worktree holds another line ending "
        f"(path, form cited, count): {stale}; restore the index bytes to disk (`python tools/landing_text.py "
        "eol --fix-lf <file>` for an LF-stored file, or delete the file and `git checkout -- <file>`), never "
        "`git add --renormalize`, which would store the stale bytes"
    )
    assert unreproducible == [], (
        f"citations name a line-ending form no checkout reproduces (path, form, count): {unreproducible}; "
        "restore the cited file's bytes, never the citation"
    )
    # every cited file is now cited by its disk bytes: the index must hold those bytes too
    compared = [p for p in paths if p not in intent_to_add]
    blobs = _index_blobs(compared)
    stdin = "\n".join(PREFIX + p for p in compared) + "\n"
    on_disk = _git("hash-object", "--no-filters", "--stdin-paths", data=stdin.encode("utf-8")).decode().split()
    assert len(on_disk) == len(compared)
    mismatched = [p for p, d in zip(compared, on_disk) if d != blobs[p]]
    assert mismatched == [], (
        f"{len(mismatched)} sha-cited files outside results/ are cited by their disk bytes but stored "
        f"differently (line endings or content): {mismatched}; store the cited bytes (`git add --renormalize -- "
        f"<file>` under `-text`), never re-cite"
        + (f"; intent-to-add entries not compared: {sorted(intent_to_add)}" if intent_to_add else "")
    )
    # a cited file whose bytes changed is cited by none of its forms any more and so leaves `now`
    # unseen by the checks above: as test 3 does for results/, compare the counts with HEAD's
    head_paths = [p for p in _z(_git("ls-tree", "-r", "-z", "--name-only", "HEAD"))
                  if not p.startswith("results/") or _is_text(p)]
    head_blobs = _head_reader(head_paths)
    head = _outside_citation_counts(lambda p: head_blobs.get(p, b""), [p for p in head_paths if p in head_blobs])
    dropped = sorted((p, sum(n.values()), sum(now.get(p, {}).values()))
                     for p, n in head.items() if sum(now.get(p, {}).values()) < sum(n.values()))
    assert dropped == [], (
        "files outside results/ cited fewer times than at HEAD (path, at HEAD, now): "
        f"{dropped[:8]}; the file's bytes changed, or it was renamed or deleted, or a citing file dropped it; "
        "restore the bytes or re-cite through the registered landing, never by editing the citation"
    )


HEX64_STR = re.compile(r"[0-9a-f]{64}")
_BLOB_DIGESTS: dict[str, tuple[str, str]] = {}   # blob id -> (sha256 as stored, sha256 LF-folded), kept across commits


def _is_ancestor(commit: str) -> bool:
    try:
        _git("merge-base", "--is-ancestor", commit, "HEAD")
    except RuntimeError:
        return False
    return True


def _receipt_digests(rec) -> list[tuple[str, str]]:
    """(key, value) for every string value under a key that names a sha256, at any depth; free
    text such as a stage's tail is never read as a citation, and a value that is not 64 lowercase
    hex is reported by the caller (a null is skipped: it binds nothing)."""
    out: list[tuple[str, str]] = []

    def walk(o, key: str) -> None:
        if isinstance(o, dict):
            for k, v in o.items():
                walk(v, k)
        elif isinstance(o, list):
            for v in o:
                walk(v, key)
        elif isinstance(o, str) and "sha256" in key.lower():
            out.append((key, o))

    walk(rec, "")
    return out


def _blob_digests_at(commit: str) -> dict[str, list[str]]:
    """sha256 -> paths for every blob tracked at ``commit`` outside results/, each blob as stored
    and with CRLF folded to LF (one entry when the two agree); digests are cached by blob id, so a
    second receipt naming another commit hashes only the blobs that differ."""
    entries: list[tuple[str, str]] = []
    for rec in _z(_git("ls-tree", "-r", "-z", commit)):
        meta, path = rec.split("\t", 1)
        _mode, kind, blob = meta.split()
        if kind == "blob" and not path.startswith("results/"):
            entries.append((blob, path))
    missing = sorted({b for b, _ in entries if b not in _BLOB_DIGESTS})
    if missing:
        out = _git("cat-file", "--batch", data=("\n".join(missing) + "\n").encode("utf-8"))
        pos = 0
        for b in missing:
            nl = out.index(b"\n", pos)
            size = int(out[pos:nl].decode().rsplit(" ", 1)[1])
            data = out[nl + 1 : nl + 1 + size]
            pos = nl + 1 + size + 1
            _BLOB_DIGESTS[b] = (hashlib.sha256(data).hexdigest(), hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest())
    digests: dict[str, list[str]] = {}
    for b, path in entries:
        for h in set(_BLOB_DIGESTS[b]):
            digests.setdefault(h, []).append(path)
    return digests


def test_every_proof_receipt_resolves_at_its_own_source_commit():
    # check 5 (2026-10-14; call PC-4 of the public-cut decision batch chose the binding at the source
    # commit, and this lane's two reviews added the never-edited clause, the ancestor test, the
    # key-and-path binding and the rule on bytes no commit holds): a receipt binds the files it cites
    # at the commit it names, not at HEAD, so an edit to the tool or the allowlist never reds this
    # file; a receipt HEAD holds is never edited; a new one's digests must name committed bytes.
    tracked = _tracked()
    receipts = sorted(p for p in tracked if _is_receipt(p))
    head_receipts = sorted(p for p in _z(_git("ls-tree", "-r", "-z", "--name-only", "HEAD")) if _is_receipt(p))
    gone = sorted(p for p in head_receipts if p not in receipts or not (ROOT / p).is_file())
    assert gone == [], (
        f"proof receipts tracked at HEAD are gone from the tree: {gone}; a receipt is committed evidence, "
        "restore it from history"
    )
    head_blobs = _head_reader(head_receipts)
    problems: list[tuple[str, str]] = []
    for r in receipts:
        raw = (ROOT / r).read_bytes()
        at_head = r in head_blobs
        if at_head and _lf_sha(raw) != _lf_sha(head_blobs[r]):
            problems.append((r, "differs from HEAD's copy once CRLF is folded; a receipt is never edited, restore it "
                                "from history"))
            continue
        try:
            rec = json.loads(raw)
        except ValueError as e:
            problems.append((r, f"not JSON: {e}; restore the receipt from history, or re-make it with the tool's "
                                "`prove`"))
            continue
        commit = rec.get("source_commit") if isinstance(rec, dict) else None
        if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40}", commit):
            problems.append((r, "names no 40-hex source_commit; restore the receipt from history, or re-make it with "
                                "the tool's `prove`"))
            continue
        if not _is_ancestor(commit):
            problems.append((r, f"source_commit {commit[:12]} is not an ancestor of HEAD (an amended, rewritten or "
                                "dangling snapshot commit, or a shallow clone); restore the receipt from history, or "
                                "export from a commit HEAD descends from and prove again"))
            continue
        cited = _receipt_digests(rec)
        digests = _blob_digests_at(commit) if any(HEX64_STR.fullmatch(h) for _, h in cited) else {}
        for key, h in cited:
            if not HEX64_STR.fullmatch(h):
                problems.append((r, f"{key} {h[:24]!r} is not a 64-character lowercase hex digest; the tool writes "
                                    "hexdigest() strings, restore the receipt or re-make it with `prove`"))
                continue
            want = RECEIPT_PATH_KEYS.get(key)
            paths = digests.get(h, [])
            if (want in paths) if want else bool(paths):
                continue
            if at_head:
                remedy = "restore the receipt from history, never edit it"
            elif paths:   # a blob there, at another path than the key names (the critic's read of lane 1, 2026-10-15)
                remedy = ("the digest is a blob at the source commit, but at " + ", ".join(paths) + ", not at the path the "
                          "key names (a key pointing at the wrong file, or a wrong source_commit): re-make the receipt with `prove`")
            else:
                where = "the path the key names" if want else "any path outside results/"   # a key naming no path
                remedy = ("the digest names no blob at " + where + " at the source commit (an uncommitted tool's "
                          "digest, an allowlist digest taken over a worktree copy, or a wrong source_commit): commit the "
                          "sources, export from that commit, prove again")
            problems.append((r, f"{key} {h[:12]} is not the sha256, stored or LF-folded, of "
                                f"{want or 'any file outside results/'} at its source commit {commit[:12]}; {remedy}"))
    assert problems == [], (
        f"proof receipts that do not resolve at their own source commit (receipt, problem): {problems}"
    )


# ---- check 6: absolute pins (2026-10-16, lane C of the 2026-10-15 image audit, S6b-C-1) ----
# tools/evidence_pins.py lists every cited digest that resolves to a tracked file; the list in
# tests/evidence_pins.json is compared with a fresh scan, not with HEAD or the index. On 2026-10-16
# the scan found 152 cited digests resolving to 153 tracked files (`python tools/evidence_pins.py`
# prints the count; the audit's own figure, 781 of 978 values, counted by another method and is not
# comparable); the rest of the cited digests name gitignored raws, moments and documents outside the
# tree. The floor below is anti-vacuity only. Paths are compared; the line-ending form each digest
# matched is recorded in the file and not compared, so a Linux clone and this box agree. The pins
# file is a citer for checks 2 to 4 (it quotes every digest) and not for this check, so after a
# legitimate regeneration of cited evidence check 3 reads one citation short until `--write` runs.
MIN_PINNED_DIGESTS = 100


def _pins_tool():
    import sys as _sys
    _sys.path.insert(0, str(ROOT / "tools"))
    import evidence_pins as ev
    return ev


def test_pins_tool_scope_matches_this_file():
    """The tool keeps its own copies of this file's scope constants; they must agree (the tool's text
    suffixes add `.cff`, which this file does not scan, for CITATION.cff's digests)."""
    ev = _pins_tool()
    assert ev.RECEIPT_PREFIXES == FOLDED_CITERS
    assert ev.RECOVERED_PREFIXES == RECOVERED_PREFIXES
    assert set(ev.TEXT_SUFFIXES) == set(TEXT_SUFFIXES) | {".cff"}
    assert ev.SELF == "tests/evidence_pins.json"


def test_every_cited_digest_still_resolves_to_the_pinned_file():
    ev = _pins_tool()
    pins_path = ROOT / "tests" / "evidence_pins.json"
    assert pins_path.exists(), "tests/evidence_pins.json is missing: python tools/evidence_pins.py --write"
    pinned = ev.load_pins(pins_path)["pins"]
    assert len(pinned) >= MIN_PINNED_DIGESTS, f"{len(pinned)} pinned digests < {MIN_PINNED_DIGESTS}: the scan or the tree changed"
    now, cited = ev.scan(ROOT)
    diff = ev.compare(pinned, now, cited)
    remedies = {
        "unresolved": "the cited bytes changed, whatever HEAD holds: restore the bytes, or re-cite through the "
                      "registered landing and then `python tools/evidence_pins.py --write --accept <digest>`; never edit the pin",
        "uncited": "a citation was removed: `python tools/evidence_pins.py --write --accept <digest>` if that was the landing's intent",
        "moved": "the digest resolves to other paths than pinned (a rename or a duplicate): `--write --accept <digest>` once understood",
        "new": "a new citation: `python tools/evidence_pins.py --write`, then commit tests/evidence_pins.json with the landing",
    }
    report = {k: (len(v), v[:4], remedies[k]) for k, v in diff.items() if v}
    assert report == {}, report
