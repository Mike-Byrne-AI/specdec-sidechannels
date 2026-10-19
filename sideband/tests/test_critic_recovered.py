"""tests/test_critic_recovered.py: the recovered critic folder (docs/audits/critic-recovered/, 2026-10-17,
the public-cut plan section 14.2 item 3) is held to its manifests.

The folder is a copy of a selection of the reviewer's own scratch of the harness era; recover.py beside it
carries the provenance, the archive's rule, the layout, the scrub and the lane rule, and writes the two
manifests; gen_readme.py writes the README from them. MANIFEST.json lists the rows the public cut exports;
MANIFEST_WITHHELD.json, which the public cut withholds with the files it lists, holds the rest. These tests
read whichever manifests are present, so they hold in the private tree and in the public clone alike (the
public layout keeps the tree under a prefix; git's cwd-relative and top-level-relative conventions are both
handled), and they fail rather than skip: a row whose file is missing, whose bytes moved, whose index blob
differs from its disk bytes, or whose `text` attribute git does not leave unset is a defect of the landing,
as is a home path the scrub missed. Disk bytes alone prove nothing on an autocrlf checkout (a `-text`
checkout writes the index blob; docs/SHARP_EDGES.md, 2026-10-09), so the index is compared too. Every count
comes from the manifests; the one literal is the archive's 309. Nothing here imports torch; git runs through
subprocess; the folder is listed through git, so an ignored cache beside it is not a stray file.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REC = "docs/audits/critic-recovered/"
FOLDER = ROOT / REC
ARCHIVE_FILES = 309   # the 2026-10-16 archive's file count, the plan's figure (section 14.2 item 3)
USER_TOKEN = "<user>"
OWN_FILES = {"MANIFEST.json", "MANIFEST_WITHHELD.json", "README.md", "recover.py", "gen_readme.py"}
# `Users` + a run of separators (backslashes or slashes, so JSON-escaped paths too) or the hyphen of the harness's
# project slug, or `home` + a run of separators, then a segment. Measured at the landing (2026-10-17), the folder holds
# only the token, the fixture names of the export tool's own test as copied in the withheld lane-2 session (Jane,
# Someone, Pat, A, bob, me, y, a@b, in both cases), `x` in the critic's own smoke paths of 2026-10-01, and `<name>` from
# the tool copy's and recover.py's prose; the operator's name is none of them, and a new segment fails here until it is
# understood.
USER_SEGMENT = re.compile(rb"(?:users(?:[\\/]+|-)|home[\\/]+)([^\\/\-\s\"'`|)\];,.]+)", re.I)
ALLOWED_SEGMENTS = {USER_TOKEN, "x", "y", "<name>", "a@b", "bob", "me", "Jane", "jane", "Someone", "someone", "A", "Pat"}


def _git(*args: str, data: bytes | None = None, check: bool = True) -> bytes:
    proc = subprocess.run(["git", *args], cwd=ROOT, input=data, capture_output=True)
    if check:
        assert proc.returncode == 0, proc.stderr.decode("utf-8", "replace")
    return proc.stdout if proc.returncode == 0 else b""


try:
    PREFIX = _git("rev-parse", "--show-prefix").decode("utf-8").strip()
except AssertionError:
    PREFIX = ""


def _manifests() -> tuple[dict, dict | None]:
    public = json.loads((FOLDER / "MANIFEST.json").read_text(encoding="utf-8"))
    wp = FOLDER / "MANIFEST_WITHHELD.json"
    withheld = json.loads(wp.read_text(encoding="utf-8")) if wp.exists() else None
    return public, withheld


def _rows() -> list[dict]:
    public, withheld = _manifests()
    return public["files"] + (withheld["files"] if withheld else [])


def _folder_files() -> list[str]:
    """Every tracked or untracked, non-ignored file under the folder (cwd-relative from git, so the public
    layout's prefix is not in the way), relative to the folder."""
    out = _git("ls-files", "-z", "-co", "--exclude-standard", "--", REC.rstrip("/")).decode("utf-8", "surrogateescape")
    return sorted(p[len(REC):] for p in out.split("\0") if p.startswith(REC))


def test_manifests_agree_with_each_other_and_with_the_archive_count():
    public, withheld = _manifests()
    c = public["counts"]
    assert c["archive"] == ARCHIVE_FILES
    assert c["copied"] + c["not_copied"] == c["archive"]
    assert c["exported"] + c["withheld"] == c["copied"]
    assert len(public["files"]) == c["exported"] and all(r["export"] == "exported" for r in public["files"])
    assert sum(w["n_files"] for w in public["withheld"]) == c["withheld"] and all(w["reason"] for w in public["withheld"])
    assert len(public["not_copied"]) == c["not_copied"]
    for n in public["not_copied"]:
        assert n["why"] and n["sha256_source"] and n["bytes_source"] > 0
        assert not (FOLDER / n["path"]).exists(), n["path"]   # the path the copy would have had
    assert public["user_token"] == USER_TOKEN and public["archive"]["n_files"] == ARCHIVE_FILES
    assert c["scrubbed_files_exported"] == sum(1 for r in public["files"] if r["substitutions"])
    assert c["substitutions_exported"] == sum(r["substitutions"] for r in public["files"])
    # the withheld rows: present in the private tree, absent (with their files) from the public clone
    dirs = [w["dir"] for w in public["withheld"] if "dir" in w]
    files = [w["path"] for w in public["withheld"] if "path" in w]
    assert dirs and files and all((FOLDER / d).exists() == (withheld is not None) for d in dirs + files), (dirs, files)
    if withheld is not None:
        assert len(withheld["files"]) == c["withheld"] and all(r["export"] == "withheld" for r in withheld["files"])
        assert {k: v for k, v in withheld.items() if k not in ("files", "files_note")} == \
               {k: v for k, v in public.items() if k not in ("files", "files_note", "withheld", "not_copied")}
        per_dir = {d: sum(1 for r in withheld["files"] if r["path"].startswith(d + "/")) for d in dirs}
        assert per_dir == {w["dir"]: w["n_files"] for w in public["withheld"] if "dir" in w}
        assert set(files) <= {r["path"] for r in withheld["files"]}
        assert c["scrubbed_files"] == sum(1 for r in _rows() if r["substitutions"])
        assert c["substitutions"] == sum(r["substitutions"] for r in _rows())
        # no public digest is a withheld digest (the manifests were split for exactly this)
        wd = {r["sha256"] for r in withheld["files"]} | {r["sha256_source"] for r in withheld["files"]}
        pub_text = (FOLDER / "MANIFEST.json").read_text(encoding="utf-8")
        assert not (set(re.findall(r"[0-9a-f]{64}", pub_text)) & wd)


def test_every_row_is_on_disk_with_its_bytes_and_the_index_holds_the_same():
    rows = _rows()
    assert rows
    missing = [r["path"] for r in rows if not (FOLDER / r["path"]).is_file()]
    assert missing == [], f"{len(missing)} manifest rows have no file, e.g. {missing[:5]}"
    moved = [r["path"] for r in rows
             if hashlib.sha256((FOLDER / r["path"]).read_bytes()).hexdigest() != r["sha256"]
             or (FOLDER / r["path"]).stat().st_size != r["bytes"]]
    assert moved == [], f"{len(moved)} files differ from their manifest row (bytes or size), e.g. {moved[:5]}; restore the bytes, never the row"
    # the index: every file tracked, and stored as it is on disk (intent-to-add entries have no blob to compare yet)
    index: dict[str, str] = {}
    for rec in _git("ls-files", "-s", "-z", "--", REC.rstrip("/")).decode("utf-8", "surrogateescape").split("\0"):
        if rec:
            meta, path = rec.split("\t", 1)
            index[path] = meta.split()[1]
    untracked = [r["path"] for r in rows if REC + r["path"] not in index]
    assert untracked == [], f"{len(untracked)} recovered files are not in the index: git add them, e.g. {untracked[:5]}"
    ita = {p for p in _git("diff", "--name-only", "--diff-filter=A", "-z", "--", REC.rstrip("/")).decode().split("\0") if p}
    compared = [r["path"] for r in rows if PREFIX + REC + r["path"] not in ita]
    stdin = "\n".join(PREFIX + REC + p for p in compared) + "\n"
    on_disk = _git("hash-object", "--no-filters", "--stdin-paths", data=stdin.encode("utf-8")).decode().split()
    assert len(on_disk) == len(compared)
    mismatched = [p for p, d in zip(compared, on_disk) if d != index[REC + p]]
    assert mismatched == [], f"{len(mismatched)} recovered files are stored differently from their disk bytes: {mismatched[:5]}"
    # and nothing under the folder that no manifest lists, beside the folder's own five files
    extra = sorted(set(_folder_files()) - {r["path"] for r in rows} - OWN_FILES)
    assert extra == [], extra
    assert OWN_FILES - {"MANIFEST_WITHHELD.json"} <= set(_folder_files())


def test_git_leaves_the_text_attribute_unset_on_every_file():
    files = _folder_files()
    out = _git("check-attr", "--stdin", "-z", "text", data="\0".join(REC + f for f in files).encode("utf-8") + b"\0")
    parts = out.decode("utf-8", "surrogateescape").split("\0")
    attrs = {parts[i]: parts[i + 2] for i in range(0, len(parts) - 2, 3)}
    not_unset = sorted(p for p in (REC + f for f in files) if attrs.get(p) != "unset")
    assert not_unset == [], f"{len(not_unset)} files under the folder lack `-text` (a checkout's autocrlf then decides their bytes): {not_unset[:5]}"


def test_no_home_path_user_segment_survived_the_scrub():
    seen: dict[str, list[str]] = {}
    for f in _folder_files():
        for m in USER_SEGMENT.finditer((FOLDER / f).read_bytes()):
            seen.setdefault(m.group(1).decode("utf-8", "replace"), []).append(f)
    assert USER_TOKEN in seen, "the scrub token appears nowhere: the folder was not written by recover.py"
    stray = {s: fs[:3] for s, fs in seen.items() if s not in ALLOWED_SEGMENTS}
    assert stray == {}, stray
    rows = _rows()
    scrubbed_without_token = [r["path"] for r in rows if r["substitutions"] and USER_TOKEN.encode() not in (FOLDER / r["path"]).read_bytes()]
    assert scrubbed_without_token == []


def test_the_folder_readme_agrees_with_the_manifests():
    """README.md is written by gen_readme.py from the manifests, so it must regenerate byte for byte (a clone
    without the sibling archives reads their counts back from the README itself), and its table and counts are
    checked here independently of the generator."""
    public, withheld = _manifests()
    proc = subprocess.run([sys.executable, "-I", str(FOLDER / "gen_readme.py"), "--check"], cwd=ROOT, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    text = (FOLDER / "README.md").read_text(encoding="utf-8")
    assert "\r" not in text
    c = public["counts"]
    rows = _rows()
    assert f"{c['withheld']} of the {c['copied']} copied files are withheld" in text
    assert f"{c['scrubbed_files']} files carry {c['substitutions']} substitutions" in text
    table = {}
    for line in text.splitlines():
        if line.startswith("| `20"):
            cells = [x.strip() for x in line.strip("|").split("|")]
            table[cells[0].split("`")[1]] = (int(cells[2]), int(cells[3]), "withheld from the public cut" in cells[0],
                                             [int(n) for n in re.findall(r"\[(\d+)\]", cells[4])])
    expect = {s["dir"]: (s["n_files"], s["substitutions"], s["dir"] in {w.get("dir") for w in public["withheld"]},
                         [w["n_files"] for w in s["windows"]]) for s in public["sessions"]}
    assert table == expect, {k: (table.get(k), expect.get(k)) for k in set(table) | set(expect) if table.get(k) != expect.get(k)}
    # the per-session counts the table shows are the rows' (all rows in the private tree, at least the exported
    # rows' share in the public clone), and every withheld file the public manifest names is a withheld row
    for s in public["sessions"]:
        got = sum(r["substitutions"] for r in rows if r["session"] == s["session"])
        assert got == s["substitutions"] if withheld is not None else got <= s["substitutions"], s["dir"]
    named = {f["path"]: f["empty"] for w in public["withheld"] for f in w["files"]}
    assert len(named) == public["counts"]["withheld"]
    if withheld is not None:
        assert named == {r["path"]: r["bytes"] == 0 for r in withheld["files"]}
    for n in public["not_copied"]:
        assert n["source_path"] in text and n["sha256_source"] in text and n["path"] in text


def test_every_row_carries_its_lane_by_the_manifests_own_windows_and_git_agrees_where_it_can():
    public, _ = _manifests()
    windows = {s["session"]: s for s in public["sessions"]}
    for s in windows.values():
        assert sum(w["n_files"] for w in s["windows"]) == s["n_files"]
    for r in _rows():
        s = windows[r["session"]]
        assert r["path"].startswith(s["dir"] + "/") and r["source_path"].startswith(r["session"] + "/scratchpad/")
        t = datetime.fromisoformat(r["mtime"])
        first = next((w for w in s["windows"] if t < datetime.fromisoformat(w["before"])), None)
        assert first is not None and (first["lane"], first["commits"]) == (r["lane"], r["commits"]), r["path"]
        assert r["sha256_source"] and r["sha256"] and r["eol"] in ("lf", "crlf", "mixed", "none")
        assert (r["sha256_source"] == r["sha256"]) == (r["substitutions"] == 0), r["path"]
    # the cutoffs are the closing commits' author times: checked against git where the commits resolve (the
    # private tree), and required to resolve all together or not at all (a public clone's fresh history)
    cutoffs = [(w["cutoff_commit"], w["before"]) for s in windows.values() for w in s["windows"]]
    assert all(w["commits"].split(",")[0].strip() == w["cutoff_commit"] for s in windows.values() for w in s["windows"])
    resolved = {sha: _git("log", "-1", "--format=%aI", sha, check=False).decode().strip() for sha, _ in cutoffs}
    found = {sha: t for sha, t in resolved.items() if t}
    assert not found or len(found) == len(resolved), sorted(set(resolved) - set(found))
    wrong = [(sha, before, found[sha]) for sha, before in cutoffs if sha in found
             and datetime.fromisoformat(found[sha]) != datetime.fromisoformat(before)]
    assert wrong == [], wrong
