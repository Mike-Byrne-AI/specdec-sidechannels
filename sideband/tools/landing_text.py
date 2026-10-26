"""tools/landing_text.py: the landing-text kit. The mechanics that three scratch generators rewrote (the free-bigram
twin, 2026-10-01; the stratified coverage read, 2026-10-02; R2, 2026-10-03), kept once, so a landing writes only its
sentences and its anchors:

  - a PRIMARY / REPLICATION payload pair whose reading words come from the instrument's own rule (passed in, never
    re-implemented here: a typed "NOT-SHOWN / NOT-SHOWN" was wrong for a SIGNAL replication on 2026-10-03);
  - a NUMBER REGISTRY: every numeral a text carries is formatted through the pair, so `check` can trace each numeric
    token of a generated text, or of the worktree diff's added lines, back to a payload field;
  - PAIRED FRAGMENTS ("primary / replication"): a value that differs by side is emitted as one string and recorded, so a
    hand-typed pair shows up as a missing fragment (a wrong single word where both sides agree is not caught: the guard
    there is that the word is derived, never typed);
  - a BANNED-PHRASE assert over whitespace-collapsed, case-folded text (a wrapped line hides a phrase from a plain grep;
    the record writes labels in capitals);
  - an APPLIER (`Doc`) that edits a record file by exact anchors in the file's own line ending (LF or CRLF, detected;
    mixed refused; an `expect` that catches a `git checkout --` residue), inserts paragraphs by the BLANK-LINE rule
    (never a ")"-ending-line rule, which spliced a paragraph on 2026-10-03) and refuses it inside a tight list of
    bullets, numbered items or table rows (FINDINGS.md's finding blocks, where the "paragraph" is the whole block),
    matches wrapped phrases
    whitespace-tolerantly, and confines a replacement to a region looked up afresh on every call, so a phrase a frozen
    text also carries is never touched outside the region.

Standalone on purpose, like lint_findings.py: nothing here imports sideband, numpy or torch. A landing's generator and
applier stay per-landing scratch (their sentences and anchors are the landing's); they import this module by bare name
from tools/, as the instruments chain:

    sys.path.insert(0, str(ROOT / "tools")); import landing_text as lt
    import run_prefetch_readouts as pr
    P = lt.Pair(ROOT / "results/real/x_s3.json", ROOT / "results/real/x_s3_r.json", reading=pr._reading, floor=pr.MATERIAL)
    P.assert_registered(freeze="2fe5926", label="R2-FALLBACK-SURVIVES / H-ABSORBS")
    text = f"D_eq on the unseen keys {P.pair('gate_eq|B=16|fallback')} ({P.rdp('gate_eq|B=16|fallback')})"
    P.write(OUT, texts={"status_line.txt": text}, pointers={"readme": "..."}, banned=BANNED)   # LF texts + numbers.json
    doc = lt.Doc(ROOT, "FINDINGS.md", expect="lf")                       # refuses the CRLF a revert leaves behind
    doc.refuse_if_present("- status (2026-10-03;"); doc.append_line(text); doc.write(dry=DRY)
    doc = lt.Doc(ROOT, "docs/BLUEPRINT.md")                              # detected: CRLF
    doc.insert_after_paragraph("the paragraph's first words", lt.wrap(para, "  ")); doc.write()

Usage:
    python tools/landing_text.py check landing/numbers.json --files landing/status_line.txt landing/outcome.txt
    python tools/landing_text.py check landing/numbers.json --added FINDINGS.md docs/BLUEPRINT.md   # the diff's added lines
    python tools/landing_text.py eol                      # each tracked root / docs text file's line ending
    python tools/landing_text.py eol --expect lf FINDINGS.md README.md     # exit 1 on a mismatch
    python tools/landing_text.py eol --fix-lf FINDINGS.md README.md        # after a `git checkout --` on this box
`check` exits 1 on an unknown number, a missing pair or a banned phrase. `--files` paths are as given (no shell glob
under PowerShell: name each file); `--added` paths are repo-relative, read through `git diff HEAD -U0`, and a path git
does not track is refused, so stage a new file with `git add -N` first. Not checked, by design: integers from 2000 to
2099 (dates, but also 2048-sized dimension counts) and integers below 100 (gate indices, small counts); an ordinal or
a number glued to a letter (`1,024th`, `16B`) is not a numeric token.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Callable

SIDES = ("p", "r")                       # primary, replication
EOLS = {"lf": "\n", "crlf": "\r\n"}
EOL_NAMES = {"\n": "lf", "\r\n": "crlf"}
TEXT_SUFFIXES = (".md", ".toml", ".cff", ".txt", ".yml", ".yaml", ".cfg")
# a numeric token: optional sign, digits with thousands commas, an optional fraction and exponent; not preceded by a
# word character or a dot, not followed by a word character (so an ordinal or a unit glued on is no token: `1,024th`
# backtracks to `1`, which is below 100 and unchecked) and not followed by a dot that starts more digits (`1.2.3`); a
# sentence-final dot is allowed (`... was 0.0731.` is checked)
NUM_TOKEN = re.compile(r"(?<![\w.])[+-]?\d(?:\d|,(?=\d))*(?:\.\d+)?(?:e[+-]?\d+)?(?!\.?\d)(?!\w)")
UNCHECKED = re.compile(r"20\d\d|\d{1,2}")       # 2000..2099 (years, 2048-sized counts) and integers below 100
_SPAN = re.compile(r"`[^`\n]*`")
_HOLD = "\x00"
_ITEM = re.compile(r"(- |\d+[.)] |\|)")           # a tight list's items: bullets, numbered items, table rows


def squash(text: str) -> str:
    """Whitespace-collapsed text: what a wrapped phrase looks like to a grep that cannot see the wrap."""
    return " ".join(text.split())


def flex(phrase: str) -> str:
    """A regex that matches `phrase` across any whitespace, line breaks included."""
    return r"\s+".join(re.escape(w) for w in phrase.split())


def wrap(text: str, indent: str = "", width: int = 76, first_indent: str | None = None) -> str:
    """Wrap a paragraph the way the record's bullets are wrapped: no word broken, no hyphen break, and no backtick
    code span split across lines (its spaces are held while wrapping, so a long span may overrun the width)."""
    if _HOLD in text:
        raise SystemExit("wrap: the text carries a NUL byte, which wrap uses as its hold character; refusing")
    held = _SPAN.sub(lambda m: m.group(0).replace(" ", _HOLD), text)
    out = textwrap.fill(held, width=width, initial_indent=indent if first_indent is None else first_indent,
                        subsequent_indent=indent, break_long_words=False, break_on_hyphens=False)
    return out.replace(_HOLD, " ")


def assert_banned(texts: dict[str, str], banned: tuple[str, ...] | list[str]) -> None:
    """Refuse when any banned phrase occurs in any text, whitespace-collapsed and case-folded on both sides."""
    for name, text in texts.items():
        flat = squash(text).casefold()
        for bad in banned:
            if squash(bad).casefold() in flat:
                raise SystemExit(f"banned phrase in {name}: {bad!r}; refusing to write")


def fill_template(text: str, mapping: dict[str, str]) -> str:
    """Fill `__NAME__` placeholders; every key must be used and none may remain (dunders like __file__ are not placeholders)."""
    for key, value in mapping.items():
        if key not in text:
            raise SystemExit(f"placeholder {key} not in the template; refusing")
        text = text.replace(key, value)
    left = sorted(set(re.findall(r"__[A-Z][A-Z0-9_]*__", text)))
    if left:
        raise SystemExit(f"placeholders left unfilled: {left}; refusing")
    return text


def score(clauses: list[tuple]) -> tuple[int, list[str]]:
    """Score pinned prediction clauses: (name, value, lo, hi) holds when lo <= value <= hi; (name, bool) as given.
    Returns (held, lines) with each line `name -> value HELD|FAILED`; the verdict words are never typed."""
    out, held = [], 0
    for c in clauses:
        if len(c) == 4:
            name, v, lo, hi = c
            ok = lo <= v <= hi
            shown = f"{v:+.4f}" if abs(v) < 2 else f"{v:.4f}"
            out.append(f"{name} -> {shown} {'HELD' if ok else 'FAILED'}")
        elif len(c) == 2:
            name, ok = c
            out.append(f"{name} -> {'HELD' if ok else 'FAILED'}")
        else:
            raise SystemExit(f"a clause is a (name, value, lo, hi) or a (name, bool) tuple, got {c!r}; refusing")
        held += bool(ok)
    return held, out


class Pair:
    """A primary / replication payload pair with a number registry and the instrument's reading rule."""

    def __init__(self, primary: Path, replication: Path, reading: Callable[[dict], str], floor: float) -> None:
        self.paths = {"p": Path(primary), "r": Path(replication)}
        self.pl, self.lab, self.deltas, self.tables, self.prov = {}, {}, {}, {}, {}
        for s in SIDES:
            try:
                pl = json.loads(self.paths[s].read_text(encoding="utf-8"))
                self.lab[s] = pl["conclusion"]["labels"]
                self.deltas[s] = pl["conclusion"]["deltas"]
                self.tables[s] = pl["conclusion"].get("tables", {})
                self.prov[s] = pl["provenance"]
            except (OSError, ValueError, KeyError, TypeError) as e:
                raise SystemExit(f"{self.paths[s]}: not a payload with conclusion.labels, conclusion.deltas and provenance "
                                 f"({e!r}); refusing - regenerate it with the instrument's --conclude-from")
            self.pl[s] = pl
        self.reading_rule = reading
        self.floor = float(floor)
        self.nums: set[str] = set()
        self.pairs: list[str] = []

    # ---- provenance ----
    def assert_registered(self, freeze: str, label: str | None = None) -> None:
        """Both payloads are registered runs from the clean freeze commit; the label agrees with `label` when given."""
        if len(freeze) < 7 or not re.fullmatch(r"[0-9a-f]+", freeze):
            raise SystemExit(f"freeze {freeze!r} is not a commit prefix of at least seven hex characters; refusing")
        for s in SIDES:
            pv, name = self.prov[s], self.paths[s].name
            if pv.get("smoke") is not False:
                raise SystemExit(f"{name}: not a registered run (smoke={pv.get('smoke')!r}); refusing")
            if not str(pv.get("git_commit", "")).startswith(freeze):
                raise SystemExit(f"{name}: git_commit {pv.get('git_commit')!r} is not the freeze {freeze}; refusing")
            if pv.get("git_status_tracked") != []:
                raise SystemExit(f"{name}: tracked status not empty at the run ({pv.get('git_status_tracked')!r}); refusing")
            if label is not None and self.lab[s].get("label") != label:
                raise SystemExit(f"{name}: label {self.lab[s].get('label')!r}, expected {label!r}; refusing")

    # ---- numbers (every formatted value is registered) ----
    def f4(self, x: float, sign: bool = True) -> str:
        s = f"{x:+.4f}" if sign else f"{x:.4f}"
        self.nums.add(s.lstrip("+"))
        return s

    def num(self, x: float | int, fmt: str = "{:,}") -> str:
        s = fmt.format(x)
        self.nums.add(s.lstrip("+"))
        return s

    def ci(self, side: str, key: str) -> str:
        d = self.deltas[side][key]
        return f"{self.f4(d['delta'])} [{self.f4(d['lo'])}, {self.f4(d['hi'])}]"

    def pair(self, key: str) -> str:
        """`delta [lo, hi] / delta [lo, hi]`, primary / replication, recorded as a paired fragment."""
        s = f"{self.ci('p', key)} / {self.ci('r', key)}"
        self.pairs.append(s)
        return s

    def pp(self, a: float | int, b: float | int, fmt: str = "{:.4f}") -> str:
        """A primary / replication pair of scalars."""
        s = " / ".join(fmt.format(x) for x in (a, b))
        for x in (a, b):
            self.nums.add(fmt.format(x).lstrip("+"))
        self.pairs.append(s)
        return s

    def pt(self, key: str, path: tuple[str, ...] = ("all", "point"), fmt: str = "{:.4f}") -> str:
        """A table cell's value on both sides (`tables[key][path...]`), primary / replication."""
        vals = []
        for s in SIDES:
            v = self.tables[s][key]
            for p in path:
                v = v[p]
            vals.append(v)
        return self.pp(vals[0], vals[1], fmt)

    # ---- readings, from the rule ----
    def reading(self, side: str, key: str) -> str:
        return self.reading_rule(self.deltas[side][key])

    def rdp(self, key: str) -> str:
        """The reading word on both sides: one word when they agree, `A / B` (recorded as a pair) when they differ."""
        a, b = self.reading("p", key), self.reading("r", key)
        if a == b:
            return a
        s = f"{a} / {b}"
        self.pairs.append(s)
        return s

    def straddle(self, side: str, key: str) -> bool:
        d = self.deltas[side][key]
        return d["lo"] <= self.floor <= d["hi"]

    # ---- output ----
    def write(self, out_dir: Path, texts: dict[str, str], pointers: dict[str, str] | None = None,
              banned: tuple[str, ...] | list[str] = ()) -> Path:
        """Write the texts (LF), pointers.json and numbers.json (nums, pairs, banned) after the banned-phrase assert."""
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        pointers = dict(pointers or {})
        assert_banned({**texts, **{f"pointers[{k}]": v for k, v in pointers.items()}}, banned)
        for name, text in texts.items():
            (out_dir / name).write_text(text.rstrip("\n") + "\n", encoding="utf-8", newline="\n")
        if pointers:
            (out_dir / "pointers.json").write_text(json.dumps(pointers, indent=1), encoding="utf-8", newline="\n")
        reg = {"nums": sorted(self.nums), "pairs": list(dict.fromkeys(self.pairs)), "banned": list(banned)}
        path = out_dir / "numbers.json"
        path.write_text(json.dumps(reg, indent=1), encoding="utf-8", newline="\n")
        return path


class Region:
    """A slice of a Doc between two unique markers, looked up afresh on every call (an edit elsewhere in the Doc
    moves the offsets); replacements never leave it."""

    def __init__(self, doc: "Doc", start: str, end: str) -> None:
        self.doc, self.start, self.end = doc, start, end
        self._bounds()

    def _bounds(self) -> tuple[int, int]:
        i = self.doc.once(self.start)
        j = self.doc.text.find(self.end, i)
        if j < 0:
            raise SystemExit(f"{self.doc.rel}: region end {self.end[:60]!r} not found after its start; refusing")
        return i, j + len(self.end)

    @property
    def text(self) -> str:
        i, j = self._bounds()
        return self.doc.text[i:j]

    def _put(self, new: str) -> None:
        i, j = self._bounds()
        self.doc.text = self.doc.text[:i] + new + self.doc.text[j:]

    def replace_once(self, old: str, new: str) -> None:
        n = self.text.count(old)
        if n != 1:
            raise SystemExit(f"{self.doc.rel}: {old[:60]!r} occurs {n} times in the region; refusing")
        self._put(self.text.replace(old, new))

    def flex_replace_once(self, old: str, new: str) -> None:
        pat = re.compile(flex(old))
        n = len(pat.findall(self.text))
        if n != 1:
            raise SystemExit(f"{self.doc.rel}: {old[:60]!r} matches {n} times in the region (whitespace-tolerant); refusing")
        self._put(pat.sub(lambda _: new, self.text, count=1))


class Doc:
    """One record file, read in its own line ending and written back in it; every edit refuses an ambiguous anchor."""

    def __init__(self, root: Path, rel: str, expect: str | None = None) -> None:
        self.root, self.rel = Path(root), rel
        self.path = self.root / rel
        b = self.path.read_bytes()
        n_crlf, n_lf = b.count(b"\r\n"), b.count(b"\n")
        if n_crlf and n_crlf != n_lf:
            raise SystemExit(f"{rel}: mixed line endings ({n_crlf} CRLF of {n_lf} line ends); refusing - normalise it "
                             f"first (`python tools/landing_text.py eol --fix-lf {rel}` for an LF file)")
        self.eol = "\r\n" if n_crlf else "\n"
        if expect is not None:
            if expect not in EOLS:
                raise SystemExit(f"{rel}: expect must be 'lf' or 'crlf', got {expect!r}; refusing")
            if EOLS[expect] != self.eol:
                raise SystemExit(f"{rel}: {EOL_NAMES[self.eol].upper()} line endings, expected {expect.upper()} (a `git checkout --` "
                                 f"on an autocrlf box re-materialises LF files as CRLF; `python tools/landing_text.py eol "
                                 f"--fix-lf {rel}` restores them); refusing")
        self.text = b.decode("utf-8").replace("\r\n", "\n")
        self._orig = self.text

    # ---- anchors ----
    def once(self, anchor: str) -> int:
        n = self.text.count(anchor)
        if n != 1:
            raise SystemExit(f"{self.rel}: anchor occurs {n} times: {anchor[:80]!r}; refusing")
        return self.text.index(anchor)

    def refuse_if_present(self, marker: str, what: str = "this landing's text") -> None:
        if marker in self.text:
            raise SystemExit(f"{self.rel}: already carries {what} ({marker[:60]!r}); refusing a second application")

    def replace_once(self, old: str, new: str) -> None:
        self.once(old)
        self.text = self.text.replace(old, new)

    def flex_replace_once(self, old: str, new: str) -> None:
        """Replace a phrase that textwrap may have split across lines; exactly one match or refuse."""
        pat = re.compile(flex(old))
        n = len(pat.findall(self.text))
        if n != 1:
            raise SystemExit(f"{self.rel}: {old[:60]!r} matches {n} times (whitespace-tolerant); refusing")
        self.text = pat.sub(lambda _: new, self.text, count=1)

    def region(self, start: str, end: str) -> Region:
        return Region(self, start, end)

    # ---- insertions ----
    def para_end(self, marker: str) -> int:
        """THE BLANK-LINE RULE: the index just after the newline that ends the paragraph containing `marker` (the
        paragraph ends at the next blank line; a paragraph that runs to EOF is refused, never guessed). A paragraph
        that is a tight list (more than one line starting as a bullet, a numbered item or a table row, as a FINDINGS.md
        finding block) is refused: use `insert_after_line` or `rewrap_bullet` there."""
        i = self.once(marker)
        j = self.text.find("\n\n", i)
        if j < 0:
            raise SystemExit(f"{self.rel}: the paragraph at {marker[:40]!r} is not followed by a blank line; refusing")
        k = self.text.rfind("\n\n", 0, i)
        start = 0 if k < 0 else k + 2
        items = sum(bool(_ITEM.match(ln)) for ln in self.text[start:j].split("\n"))
        if items > 1:
            raise SystemExit(f"{self.rel}: the paragraph at {marker[:40]!r} is a tight list of {items} items (bullets, numbered "
                             f"items or table rows), so the blank-line rule would land after the last one; use "
                             f"insert_after_line or rewrap_bullet; refusing")
        return j + 1

    def insert_after_paragraph(self, marker: str, block: str, new_paragraph: bool = False) -> None:
        """Insert `block` (already wrapped) right after the paragraph containing `marker`: as that paragraph's
        continuation lines, or as a paragraph of its own (`new_paragraph`), the blank line kept either way."""
        k = self.para_end(marker)
        ins = block.rstrip("\n") + "\n"
        if new_paragraph:
            ins = "\n" + ins
        self.text = self.text[:k] + ins + self.text[k:]

    def insert_after_line(self, marker: str, line: str) -> None:
        """Insert `line` after the unique line containing `marker`."""
        i = self.once(marker)
        if not self.text.endswith("\n"):
            self.text += "\n"
        k = self.text.find("\n", i) + 1
        self.text = self.text[:k] + line.rstrip("\n") + "\n" + self.text[k:]

    def append_line(self, line: str) -> None:
        if self.text and not self.text.endswith("\n"):
            self.text += "\n"
        self.text += line.rstrip("\n") + "\n"

    def rewrap_bullet(self, start: str, end: str, fn: Callable[[str], str], width: int = 76, indent: str = "  ") -> None:
        """Unwrap the bullet from `start` (its first words) up to `end` (exclusive, e.g. the next bullet's first words
        with its leading newline), apply `fn(flat) -> flat`, re-wrap with the record's bullet shape (first line flush,
        continuation lines indented). A span that crosses a blank line (more than one bullet) is refused."""
        i = self.once(start)
        j = self.text.find(end, i)
        if j < 0:
            raise SystemExit(f"{self.rel}: bullet end {end[:60]!r} not found after {start[:40]!r}; refusing")
        body = self.text[i:j]
        if "\n\n" in body.rstrip("\n"):
            raise SystemExit(f"{self.rel}: the span from {start[:40]!r} to {end[:40]!r} crosses a blank line (more than one "
                             f"bullet would be merged); narrow `end` to this bullet's last line; refusing")
        tail = body[len(body.rstrip("\n")):]                       # the newlines between the bullet and `end`, kept
        flat = " ".join(ln.strip() for ln in body.split("\n") if ln.strip())
        new = wrap(fn(flat), indent=indent, width=width, first_indent="")
        self.text = self.text[:i] + new + tail + self.text[j:]

    # ---- output ----
    @property
    def changed(self) -> bool:
        return self.text != self._orig

    def write(self, dry: bool = False) -> bool:
        """Write back in the file's own line ending (inserted text is normalised to LF first); returns whether
        anything changed. `dry` prints the plan only."""
        self.text = self.text.replace("\r\n", "\n")
        if not self.changed:
            print(f"{self.rel}: unchanged")
            return False
        b = self.text.replace("\n", self.eol).encode("utf-8")
        if dry:
            print(f"DRY {self.rel}: would write {len(b)} bytes ({EOL_NAMES[self.eol].upper()})")
            return True
        self.path.write_bytes(b)
        back = self.path.read_bytes()
        if back.count(b"\r\n") not in (0, back.count(b"\n")):
            raise SystemExit(f"{self.rel}: mixed line endings after the write; inspect before committing")
        print(f"{self.rel}: written ({EOL_NAMES[self.eol].upper()})")
        return True


# ---- the check (the author's own copy of the critic's grep) ----
def unknown_numbers(text: str, nums: set[str]) -> list[str]:
    """Numeric tokens of `text` that no registered number explains, sign included (a sign-flipped value is unknown);
    integers 2000..2099 and below 100 are not checked (see the module docstring)."""
    bad = set()
    for t in NUM_TOKEN.findall(text):
        core = t.lstrip("+")
        if core in nums or UNCHECKED.fullmatch(core.lstrip("-")):
            continue
        bad.add(core)
    return sorted(bad)


def _git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace")


def _tracked(root: Path, rel: str) -> None:
    out = _git(root, "ls-files", "--error-unmatch", "--", rel)
    if out.returncode != 0:
        raise SystemExit(f"{rel}: not tracked by git (stage a new file with `git add -N {rel}`); refusing")


def added_lines(root: Path, rel: str) -> str:
    """The added lines of the worktree diff of `rel` against HEAD (unstaged and staged), joined with newlines; an
    untracked path is refused."""
    _tracked(root, rel)
    out = _git(root, "diff", "HEAD", "-U0", "--no-color", "--no-ext-diff", "--", rel)
    if out.returncode != 0:
        raise SystemExit(f"git diff failed for {rel}: {out.stderr.strip()}; refusing")
    added, in_hunk = [], False                 # the `+++ ` header sits before the first `@@`; an added line may start with `++`
    for ln in out.stdout.splitlines():
        if ln.startswith("@@"):
            in_hunk = True
        elif in_hunk and ln.startswith("+"):
            added.append(ln[1:])
    return "\n".join(added)


def numstat(root: Path, rel: str) -> tuple[int, int]:
    """(added, deleted) line counts of the worktree diff of `rel` against HEAD; a binary diff is refused."""
    _tracked(root, rel)
    out = _git(root, "diff", "HEAD", "--numstat", "--", rel)
    if out.returncode != 0:
        raise SystemExit(f"git diff --numstat failed for {rel}: {out.stderr.strip()}; refusing")
    line = out.stdout.strip().splitlines()
    if not line:
        return 0, 0
    a, d = line[0].split("\t")[:2]
    if a == "-" or d == "-":
        raise SystemExit(f"{rel}: git reports a binary diff; refusing")
    return int(a), int(d)


def check_texts(registry: dict, texts: dict[str, str]) -> list[str]:
    """Findings over `texts` (name -> text): unknown numbers per text, banned phrases per text (whitespace-collapsed,
    case-folded), and pairs missing from the union of all texts. Empty means clean."""
    nums, pairs, banned = set(registry.get("nums", [])), registry.get("pairs", []), registry.get("banned", [])
    findings = []
    for name, text in texts.items():
        bad = unknown_numbers(text, nums)
        if bad:
            findings.append(f"{name}: unknown numbers {bad}")
        flat = squash(text).casefold()
        for phrase in banned:
            if squash(phrase).casefold() in flat:
                findings.append(f"{name}: banned phrase {phrase!r}")
    union = squash("\n".join(texts.values()))
    missing = [p for p in pairs if squash(p) not in union]
    if missing:
        findings.append(f"pairs missing from every checked text: {missing}")
    return findings


def cmd_check(args: argparse.Namespace) -> int:
    registry = json.loads(Path(args.numbers).read_text(encoding="utf-8"))
    root = Path(args.root).resolve()
    texts: dict[str, str] = {}
    for f in args.files or []:
        texts[f] = Path(f).read_text(encoding="utf-8")
    for rel in args.added or []:
        texts[f"{rel} (added lines)"] = added_lines(root, rel)
        a, d = numstat(root, rel)
        print(f"{rel}: +{a} -{d}" + ("" if d == 0 else "  (not a pure insertion: lines removed or re-wrapped)"))
    if not texts:
        raise SystemExit("check: give --files and/or --added; refusing to report on nothing")
    findings = check_texts(registry, texts)
    for line in findings:
        print("FINDING", line)
    print(f"check: {len(texts)} text(s), {len(registry.get('nums', []))} registered numbers, "
          f"{len(registry.get('pairs', []))} pairs, {len(findings)} finding(s)")
    return 1 if findings else 0


def eol_of(path: Path) -> str:
    b = path.read_bytes()
    n_crlf, n_lf = b.count(b"\r\n"), b.count(b"\n")
    if n_lf == 0:
        return "NONE"
    if n_crlf == 0:
        return "LF"
    return "CRLF" if n_crlf == n_lf else "MIXED"


def tracked_text_files(root: Path) -> list[str]:
    out = _git(root, "ls-files", "--", ".", "docs")
    if out.returncode != 0:
        raise SystemExit(f"git ls-files failed: {out.stderr.strip()}; refusing")
    rels = [ln for ln in out.stdout.splitlines() if ln.endswith(TEXT_SUFFIXES)]
    return [r for r in rels if r.count("/") == 0 or r.startswith("docs/")]


def cmd_eol(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    if args.fix_lf and not args.files:
        raise SystemExit("eol --fix-lf wants explicit files; refusing to rewrite the tracked set")
    if args.fix_lf and args.expect == "crlf":
        raise SystemExit("eol --fix-lf with --expect crlf contradicts itself; refusing")
    rels = args.files or tracked_text_files(root)
    bad = 0
    for rel in rels:
        p = root / rel
        if not p.exists():
            print(f"{rel}: missing")
            bad += 1
            continue
        kind = eol_of(p)
        note = ""
        if args.fix_lf and kind in ("CRLF", "MIXED"):
            p.write_bytes(p.read_bytes().replace(b"\r\n", b"\n"))
            note = f" (was {kind})"
            kind = eol_of(p)
        if args.expect and kind != args.expect.upper():
            note += f"  MISMATCH (expected {args.expect.upper()})"
            bad += 1
        if kind == "MIXED":
            bad += 1
        print(f"{rel}: {kind}{note}")
    return 1 if bad else 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="landing-text kit: number / pair / banned-phrase check and line-ending survey")
    ap.add_argument("--root", default=str(Path(__file__).resolve().parent.parent), help="repository root")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check", help="check generated texts or the diff's added lines against numbers.json")
    c.add_argument("numbers", help="the numbers.json a Pair.write() produced")
    c.add_argument("--files", nargs="*", help="generated text files (paths as given; no shell glob under PowerShell)")
    c.add_argument("--added", nargs="*", help="repo-relative tracked files whose added lines (git diff HEAD -U0) are checked")
    c.set_defaults(fn=cmd_check)
    e = sub.add_parser("eol", help="report each file's line ending; tracked root and docs/ text files when none given")
    e.add_argument("files", nargs="*", help="repo-relative files")
    e.add_argument("--expect", choices=("lf", "crlf"), help="exit 1 when a file differs")
    e.add_argument("--fix-lf", action="store_true", help="rewrite CRLF as LF in the given files")
    e.set_defaults(fn=cmd_eol)
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
