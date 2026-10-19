"""tests/test_landing_text.py — tools/landing_text.py (the landing-text kit), the CI-safe layer: readings come from
the rule passed in, every emitted number is registered and `check` traces numeric tokens back to it (sign included,
sentence-final dot included), a value that differs by side is a recorded pair, banned phrases are caught across a
line wrap and in any case, and the applier keeps each file's own line ending, refuses ambiguous anchors, a revert's
CRLF residue and a tight list (bullets, numbered items or table rows), inserts by the blank-line rule, re-looks a
region up after an edit above it, and reads the diff only through git-tracked paths. The last test is a positive
control on the committed R2 payloads (skips when absent); the git test skips without git. Fixture values are
synthetic: no four-decimal, exponent or comma-grouped value in this file occurs in FINDINGS.md, docs/BLUEPRINT.md,
OPEN_QUESTIONS.md, docs/FINDINGS_INDEX.md or README.md (checked 2026-10-03; the thresholds 0.05, 0.1 and the like
are the rule's, not a record's). No torch."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import landing_text as lt  # noqa: E402

FLOOR = 0.05


def _rule(d: dict, material: float = FLOOR) -> str:
    """The prefetch family's reading rule, copied here as the fixture's rule (the kit takes any rule)."""
    if d["lo"] > 0 and d["delta"] >= material:
        return "SIGNAL"
    if d["hi"] < 0:
        return "NEGATIVE"
    return "NOT-SHOWN"


def _payload(label: str, deltas: dict, point: float, commit: str = "abc1234def") -> dict:
    return {"conclusion": {"labels": {"label": label}, "deltas": deltas,
                           "tables": {"free|B=16|all": {"all": {"point": point}}}},
            "provenance": {"smoke": False, "git_commit": commit, "git_status_tracked": []}}


FB_PAIR = "+0.1234 [+0.1013, +0.1457] / +0.1111 [+0.0911, +0.1311]"       # the fixture's unseen-key pair, synthetic


def _pair(tmp_path: Path, **kw) -> lt.Pair:
    p = _payload("X", {"gate|B=16|all": {"delta": 0.0448, "lo": 0.0315, "hi": 0.0581},
                       "gate|B=16|fallback": {"delta": 0.1234, "lo": 0.1013, "hi": 0.1457}}, 0.7111)
    r = _payload("X", {"gate|B=16|all": {"delta": 0.0555, "lo": 0.0422, "hi": 0.0686},
                       "gate|B=16|fallback": {"delta": 0.1111, "lo": 0.0911, "hi": 0.1311}}, 0.7222)
    for k, v in kw.items():
        r["provenance"][k] = v
    (tmp_path / "p.json").write_text(json.dumps(p), encoding="utf-8")
    (tmp_path / "r.json").write_text(json.dumps(r), encoding="utf-8")
    return lt.Pair(tmp_path / "p.json", tmp_path / "r.json", reading=_rule, floor=FLOOR)


# ---- readings and pairs ----
def test_reading_words_come_from_the_rule_and_a_split_reading_is_a_recorded_pair(tmp_path):
    P = _pair(tmp_path)
    assert P.rdp("gate|B=16|fallback") == "SIGNAL" and "SIGNAL" not in P.pairs       # agreement: one word, not a pair
    assert P.rdp("gate|B=16|all") == "NOT-SHOWN / SIGNAL"                            # the 2026-10-03 shape, by the rule
    assert "NOT-SHOWN / SIGNAL" in P.pairs
    assert P.straddle("p", "gate|B=16|all") and not P.straddle("p", "gate|B=16|fallback")


def test_pair_pp_pt_register_every_number_and_the_fragment(tmp_path):
    P = _pair(tmp_path)
    s = P.pair("gate|B=16|fallback")
    assert s == FB_PAIR
    assert {"0.1234", "0.1013", "0.1457", "0.1111", "0.0911", "0.1311"} <= P.nums and s in P.pairs
    assert P.pt("free|B=16|all") == "0.7111 / 0.7222" and "0.7222" in P.nums
    assert P.pp(0.3131, 0.3232) == "0.3131 / 0.3232" and P.num(12345) == "12,345" and "12,345" in P.nums
    assert P.f4(-0.4321) == "-0.4321" and "-0.4321" in P.nums


def test_assert_registered_refuses_a_smoke_a_wrong_freeze_a_dirty_tree_a_wrong_label_and_a_short_freeze(tmp_path):
    _pair(tmp_path).assert_registered("abc1234", label="X")
    with pytest.raises(SystemExit, match="not a registered run"):
        _pair(tmp_path, smoke=True).assert_registered("abc1234")
    with pytest.raises(SystemExit, match="not the freeze"):
        _pair(tmp_path, git_commit="fff0000").assert_registered("abc1234")
    with pytest.raises(SystemExit, match="tracked status not empty"):
        _pair(tmp_path, git_status_tracked=["M FINDINGS.md"]).assert_registered("abc1234")
    with pytest.raises(SystemExit, match="label"):
        _pair(tmp_path).assert_registered("abc1234", label="Y")
    with pytest.raises(SystemExit, match="at least seven hex"):
        _pair(tmp_path).assert_registered("abc")


def test_pair_refuses_a_malformed_payload(tmp_path):
    (tmp_path / "bad.json").write_text('{"conclusion": {"labels": {}}}', encoding="utf-8")
    with pytest.raises(SystemExit, match="not a payload with conclusion.labels, conclusion.deltas and provenance"):
        lt.Pair(tmp_path / "bad.json", tmp_path / "bad.json", reading=_rule, floor=FLOOR)
    with pytest.raises(SystemExit, match="refusing"):
        lt.Pair(tmp_path / "absent.json", tmp_path / "absent.json", reading=_rule, floor=FLOOR)


def test_score_clauses_hold_or_fail_mechanically():
    held, lines = lt.score([("(1) in range", 0.1234, 0.05, 0.14), ("(2) out of range", 0.2, 0.0, 0.1), ("(3) flag", True), ("(4) flag", False)])
    assert held == 2 and lines[0].endswith("+0.1234 HELD") and lines[1].endswith("FAILED") and lines[2].endswith("HELD")
    with pytest.raises(SystemExit, match="clause"):
        lt.score([("bad", 1, 2)])


# ---- the number / pair / banned check ----
def test_check_flags_an_unknown_number_a_lost_pair_and_a_wrapped_banned_phrase_in_any_case(tmp_path):
    P = _pair(tmp_path)
    text = f"on the unseen keys {P.pair('gate|B=16|fallback')} ({P.rdp('gate|B=16|fallback')}); pooled {P.rdp('gate|B=16|all')} in 2026, gate 10"
    reg_path = P.write(tmp_path / "out", {"status.txt": text}, banned=("frobnicate the margin",))
    reg = json.loads(reg_path.read_text(encoding="utf-8"))
    assert reg["banned"] == ["frobnicate the margin"] and "NOT-SHOWN / SIGNAL" in reg["pairs"]
    assert lt.check_texts(reg, {"status.txt": text}) == []                                   # clean: years and 2-digit ints unchecked
    typed = text.replace("+0.1234", "+0.1235").replace("NOT-SHOWN / SIGNAL", "NOT-SHOWN / NOT-SHOWN")
    findings = lt.check_texts(reg, {"status.txt": typed})
    assert any("unknown numbers ['0.1235']" in f for f in findings) and any("NOT-SHOWN / SIGNAL" in f for f in findings)
    wrapped = text + "\nwe must never Frobnicate\n  THE margin here"
    assert any("banned phrase" in f for f in lt.check_texts(reg, {"status.txt": wrapped}))


def test_unknown_numbers_tokeniser_handles_ci_brackets_commas_exponents_signs_and_sentence_ends():
    nums = {"0.0271", "0.0518", "12,345", "8.3e-04", "-0.6543"}
    clean = "D [+0.0271, +0.0518]; 12,345 values; 8.3e-04 margin; -0.6543; 2026-10-03; gate 15; 99; 2048 dims; v1.2.3"
    assert lt.unknown_numbers(clean, nums) == []
    assert lt.unknown_numbers("1,357 values and 0.0282", nums) == ["0.0282", "1,357"]
    assert lt.unknown_numbers("the 1,357th eigenvalue and 16B", nums) == []            # an ordinal or a glued unit is no token
    assert lt.unknown_numbers("a flipped sign -0.0271 and +0.6543", nums) == ["-0.0271", "0.6543"]
    assert lt.unknown_numbers("the gate was 0.0738. Then 37,999 rows.", nums) == ["0.0738", "37,999"]


def test_write_refuses_a_banned_phrase_in_a_text_or_a_pointer_and_writes_lf(tmp_path):
    P = _pair(tmp_path)
    with pytest.raises(SystemExit, match="banned phrase in status.txt"):
        P.write(tmp_path / "o1", {"status.txt": "the whole\n  margin"}, banned=("the whole margin",))
    with pytest.raises(SystemExit, match=r"pointers\[readme\]"):
        P.write(tmp_path / "o2", {"status.txt": "fine"}, pointers={"readme": "The Whole Margin"}, banned=("the whole margin",))
    P.write(tmp_path / "o3", {"status.txt": "fine\n"}, pointers={"readme": "ok"})
    assert (tmp_path / "o3" / "status.txt").read_bytes() == b"fine\n" and (tmp_path / "o3" / "pointers.json").exists()


def test_fill_template_requires_every_key_and_leaves_no_placeholder():
    assert lt.fill_template("x __A__ __file__", {"__A__": "1"}) == "x 1 __file__"
    with pytest.raises(SystemExit, match="not in the template"):
        lt.fill_template("x", {"__A__": "1"})
    with pytest.raises(SystemExit, match="left unfilled"):
        lt.fill_template("x __A__ __B__", {"__A__": "1"})


# ---- the applier ----
def _doc(tmp_path: Path, text: str, eol: str, name: str = "doc.md") -> lt.Doc:
    (tmp_path / name).write_bytes(text.replace("\n", eol).encode("utf-8"))
    return lt.Doc(tmp_path, name)


BODY = "# T\n\n- first bullet (ends with a paren)\n  and continues here)\n  REPLICATION: more\n\n- second bullet\n\n## Next\n"
TIGHT = "## F-9\n\n- regime: synthetic\n- source: results/x.json\n- caveats: none\n\n## F-10\n"


def test_doc_keeps_each_files_own_line_ending_and_refuses_mixed_or_unexpected(tmp_path):
    d = _doc(tmp_path, BODY, "\r\n")
    assert d.eol == "\r\n" and "\r" not in d.text
    d.append_line("- tail")
    assert d.write() and (tmp_path / "doc.md").read_bytes().endswith(b"- tail\r\n") and b"\n\n" not in (tmp_path / "doc.md").read_bytes().replace(b"\r\n", b"")
    d2 = _doc(tmp_path, BODY, "\n", "lf.md")
    assert d2.eol == "\n" and lt.Doc(tmp_path, "lf.md", expect="lf").eol == "\n"
    with pytest.raises(SystemExit, match="LF line endings, expected CRLF"):
        lt.Doc(tmp_path, "lf.md", expect="crlf")
    with pytest.raises(SystemExit, match="expect must be"):
        lt.Doc(tmp_path, "lf.md", expect="cr")
    (tmp_path / "mixed.md").write_bytes(b"a\r\nb\nc\r\n")
    with pytest.raises(SystemExit, match="mixed line endings"):
        lt.Doc(tmp_path, "mixed.md")
    assert not d2.write() and not d2.changed                                              # unchanged: nothing written


def test_anchors_refuse_zero_or_many_and_refuse_a_second_application(tmp_path):
    d = _doc(tmp_path, BODY, "\n")
    with pytest.raises(SystemExit, match="occurs 2 times"):
        d.once("bullet")
    with pytest.raises(SystemExit, match="occurs 0 times"):
        d.replace_once("absent", "x")
    d.replace_once("second bullet", "second bullet (2026-10-03: landed)")
    with pytest.raises(SystemExit, match="already carries"):
        d.refuse_if_present("(2026-10-03: landed)")


def test_blank_line_rule_inserts_after_the_whole_paragraph_never_at_a_closing_paren(tmp_path):
    d = _doc(tmp_path, BODY, "\r\n")
    d.insert_after_paragraph("first bullet", lt.wrap("(2026-10-03: a dated pointer.)", "  "))
    lines = d.text.split("\n")
    assert lines[2:7] == ["- first bullet (ends with a paren)", "  and continues here)", "  REPLICATION: more",
                          "  (2026-10-03: a dated pointer.)", ""]                        # after REPLICATION, not after the ')'
    d.insert_after_paragraph("second bullet", "- third bullet", new_paragraph=True)
    assert "- second bullet\n\n- third bullet\n\n## Next" in d.text
    d.write()
    assert (tmp_path / "doc.md").read_bytes().count(b"\r\n") == d.text.count("\n")         # CRLF kept through the write
    with pytest.raises(SystemExit, match="not followed by a blank line"):
        _doc(tmp_path, "- only\n  paragraph\n", "\n", "eof.md").para_end("only")


def test_blank_line_rule_refuses_a_tight_list_where_insert_after_line_works(tmp_path):
    d = _doc(tmp_path, TIGHT, "\n")
    with pytest.raises(SystemExit, match="tight list of 3 items"):
        d.insert_after_paragraph("source: results/x.json", "  (2026-10-03: a pointer)")
    d.insert_after_line("source: results/x.json", "- status (2026-10-03: a dated line)")
    assert "- source: results/x.json\n- status (2026-10-03: a dated line)\n- caveats: none\n\n## F-10" in d.text
    single = _doc(tmp_path, "- one bullet\n  continued\n\n## H\n", "\n", "one.md")
    single.insert_after_paragraph("one bullet", "  (added)")
    assert single.text.startswith("- one bullet\n  continued\n  (added)\n\n## H")
    with pytest.raises(SystemExit, match="tight list of 3 items"):
        _doc(tmp_path, "1. first\n2. second\n3) third\n\n## H\n", "\n", "num.md").insert_after_paragraph("second", "x")
    with pytest.raises(SystemExit, match="tight list of 3 items"):
        _doc(tmp_path, "| a | b |\n|---|---|\n| 1 | 2 |\n\n## H\n", "\n", "tab.md").insert_after_paragraph("| 1 |", "x")


def test_insert_after_line_at_eof_with_and_without_a_trailing_newline(tmp_path):
    for eol in ("\n", "\r\n"):
        d = _doc(tmp_path, "x\nlast M", eol, "eof.md")
        d.insert_after_line("last M", "NEW")
        assert d.text == "x\nlast M\nNEW\n"
        d = _doc(tmp_path, "x\nlast M\n", eol, "eof2.md")
        d.insert_after_line("last M", "NEW")
        assert d.text == "x\nlast M\nNEW\n"
        d.write()
        assert (tmp_path / "eof2.md").read_bytes() == ("x\nlast M\nNEW\n".replace("\n", eol)).encode("utf-8")


def test_flex_replace_across_a_wrap(tmp_path):
    d = _doc(tmp_path, BODY, "\n")
    with pytest.raises(SystemExit, match="occurs 0 times"):
        d.replace_once("continues here) REPLICATION", "x")                                 # the plain match misses the wrap
    d.flex_replace_once("continues here) REPLICATION", "continues here) REPL.")
    assert "and continues here) REPL.: more" in d.text
    with pytest.raises(SystemExit, match="matches 0 times"):
        d.flex_replace_once("never there", "x")


def test_region_confines_a_shared_phrase_replacement_even_after_an_edit_above_it(tmp_path):
    text = "# T\n\n## A\n\nthe free tables are blind (registered)\n\n## B\n\nthe free tables are blind (mine)\n\n## C\n"
    d = _doc(tmp_path, text, "\n")
    with pytest.raises(SystemExit, match="occurs 2 times"):
        d.replace_once("the free tables are blind", "x")
    reg = d.region("## B", "## C")
    d.insert_after_line("# T", "an inserted line above the region, which moves every offset below it")
    reg.replace_once("the free tables are blind", "at least one free table is blind")
    assert d.text.count("the free tables are blind") == 1 and "(registered)" in d.text.split("## B")[0]
    assert "at least one free table is blind (mine)" in d.text and "blind (registered)" in d.text
    reg.flex_replace_once("free table is blind", "free table is BLIND")
    assert "at least one free table is BLIND (mine)" in d.text and d.text.count("BLIND") == 1
    with pytest.raises(SystemExit, match="not found after its start"):
        d.region("## C", "## Z")


def test_rewrap_bullet_unwraps_edits_and_rewraps_as_a_bullet_and_refuses_a_span_over_a_blank_line(tmp_path):
    d = _doc(tmp_path, BODY, "\r\n")
    d.rewrap_bullet("- first bullet", "\n\n- second bullet", lambda flat: flat.replace("REPLICATION: more", "REPLICATION: more, and a longer tail that forces a wrap " * 2), width=60)
    block = d.text.split("\n\n")[1].split("\n")
    assert block[0].startswith("- first bullet") and all(ln.startswith("  ") for ln in block[1:]) and all(len(ln) <= 60 for ln in block)
    assert "\n\n- second bullet" in d.text and d.text.endswith("## Next\n")
    with pytest.raises(SystemExit, match="crosses a blank line"):
        d.rewrap_bullet("- first bullet", "\n## Next", lambda flat: flat)


def test_wrap_keeps_a_backtick_code_span_on_one_line_and_refuses_a_nul():
    span = "`python tools/landing_text.py eol --fix-lf FINDINGS.md README.md`"
    out = lt.wrap(f"after a revert run {span} and then regenerate, re-apply and re-check every file", "  ", width=50)
    assert span in out and all(ln.count("`") % 2 == 0 for ln in out.split("\n")) and "\x00" not in out
    assert lt.wrap("plain `x y` text", width=80) == "plain `x y` text"
    with pytest.raises(SystemExit, match="NUL byte"):
        lt.wrap("a\x00b")


def test_wrap_never_breaks_a_word_or_a_hyphen():
    out = lt.wrap("D_eq +0.1234 [+0.1012, +0.1457] on the unseen-key positions of a very-long-hyphenated-token here", "  ", width=40)
    lines = out.split("\n")
    assert all(len(ln) <= 40 or " " not in ln.strip() for ln in lines)                   # over width only for one unbreakable token
    assert "very-long-hyphenated-token" in out.replace("\n  ", " ") and all(ln.startswith("  ") for ln in lines)


def test_write_normalises_crlf_in_inserted_text_and_dry_writes_nothing(tmp_path):
    d = _doc(tmp_path, BODY, "\r\n")
    d.append_line("a\r\nb")
    assert d.write(dry=True) and (tmp_path / "doc.md").read_bytes() == BODY.replace("\n", "\r\n").encode("utf-8")
    d.write()
    b = (tmp_path / "doc.md").read_bytes()
    assert b.endswith(b"a\r\nb\r\n") and b"\r\r" not in b and b.count(b"\r\n") == b.count(b"\n")


# ---- the CLI ----
def test_cli_check_on_files_and_eol_survey_fix_and_contradiction(tmp_path, capsys):
    P = _pair(tmp_path)
    text = f"the gate {P.pair('gate|B=16|fallback')}"
    reg = P.write(tmp_path / "out", {"t.txt": text})
    assert lt.main(["--root", str(tmp_path), "check", str(reg), "--files", str(tmp_path / "out" / "t.txt")]) == 0
    (tmp_path / "bad.txt").write_text(text.replace("0.1457", "0.1456"), encoding="utf-8")
    assert lt.main(["--root", str(tmp_path), "check", str(reg), "--files", str(tmp_path / "bad.txt")]) == 1
    assert "unknown numbers ['0.1456']" in capsys.readouterr().out
    with pytest.raises(SystemExit, match="give --files"):
        lt.main(["--root", str(tmp_path), "check", str(reg)])
    (tmp_path / "a.md").write_bytes(b"x\r\ny\r\n"); (tmp_path / "b.md").write_bytes(b"x\ny\n"); (tmp_path / "m.md").write_bytes(b"x\r\ny\n")
    assert lt.main(["--root", str(tmp_path), "eol", "a.md", "b.md"]) == 0
    assert lt.main(["--root", str(tmp_path), "eol", "m.md"]) == 1 and "m.md: MIXED" in capsys.readouterr().out
    assert lt.main(["--root", str(tmp_path), "eol", "--expect", "lf", "a.md", "b.md"]) == 1
    assert lt.main(["--root", str(tmp_path), "eol", "--fix-lf", "a.md", "m.md"]) == 0
    assert (tmp_path / "a.md").read_bytes() == b"x\ny\n" and (tmp_path / "m.md").read_bytes() == b"x\ny\n"
    assert "a.md: LF (was CRLF)" in capsys.readouterr().out
    with pytest.raises(SystemExit, match="explicit files"):
        lt.main(["--root", str(tmp_path), "eol", "--fix-lf"])
    with pytest.raises(SystemExit, match="contradicts"):
        lt.main(["--root", str(tmp_path), "eol", "--fix-lf", "--expect", "crlf", "a.md"])


@pytest.mark.skipif(shutil.which("git") is None, reason="git is not on PATH")
def test_added_lines_numstat_and_check_added_in_a_scratch_repo(tmp_path, capsys):
    repo = tmp_path / "repo"
    repo.mkdir()
    g = ["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", "-c", "core.autocrlf=false"]
    subprocess.run([*g, "init", "-q"], cwd=repo, check=True)
    (repo / "a.md").write_text("one\ntwo\n", encoding="utf-8", newline="\n")
    subprocess.run([*g, "add", "a.md"], cwd=repo, check=True)
    subprocess.run([*g, "commit", "-q", "-m", "init"], cwd=repo, check=True)
    (repo / "a.md").write_text("one\ntwo\n++ not a header line\nthe gate " + FB_PAIR + "\n", encoding="utf-8", newline="\n")
    assert lt.added_lines(repo, "a.md") == "++ not a header line\nthe gate " + FB_PAIR and lt.numstat(repo, "a.md") == (2, 0)
    P = _pair(tmp_path)
    reg = P.write(tmp_path / "out", {"t.txt": f"the gate {P.pair('gate|B=16|fallback')}"})
    assert lt.main(["--root", str(repo), "check", str(reg), "--added", "a.md"]) == 0 and "a.md: +2 -0" in capsys.readouterr().out
    (repo / "a.md").write_text("one\nthe gate " + FB_PAIR + " and 0.9876\n", encoding="utf-8", newline="\n")
    assert lt.main(["--root", str(repo), "check", str(reg), "--added", "a.md"]) == 1
    out = capsys.readouterr().out
    assert "not a pure insertion" in out and "unknown numbers ['0.9876']" in out
    (repo / "new.md").write_text("fresh 0.5555\n", encoding="utf-8", newline="\n")
    with pytest.raises(SystemExit, match="not tracked by git"):
        lt.added_lines(repo, "new.md")
    subprocess.run([*g, "add", "-N", "new.md"], cwd=repo, check=True)
    assert lt.added_lines(repo, "new.md") == "fresh 0.5555" and lt.numstat(repo, "new.md") == (1, 0)


# ---- positive control on committed evidence ----
R2 = ROOT / "results" / "real"
needs_r2 = pytest.mark.skipif(not (R2 / "prefetch_r2_s3.json").exists() or not (R2 / "prefetch_r2_s3_r.json").exists(),
                              reason="the committed R2 payloads are not present")


@needs_r2
def test_r2_payloads_through_the_kit_reproduce_the_landed_fragments():
    """The kit with the instrument's own rule reproduces, from the two committed R2 payloads, the unseen-key pair string
    and the pooled reading split that F-26's 2026-10-03 status line carries (FINDINGS.md): the pair verbatim, the split
    as the payloads' own label fields read it."""
    import run_prefetch_readouts as pr                                                   # numpy-only; the frozen stage-1 instrument
    P = lt.Pair(R2 / "prefetch_r2_s3.json", R2 / "prefetch_r2_s3_r.json", reading=pr._reading, floor=pr.MATERIAL)
    P.assert_registered("2fe5926", label="R2-FALLBACK-SURVIVES / H-ABSORBS")
    fb, al = P.pair("gate_eq_r2|B=16|fallback"), P.rdp("gate_eq_r2|B=16|all")
    assert P.rdp("gate_eq_r2|B=16|fallback") == "SIGNAL"
    assert al == f"{P.lab['p']['gate_eq_r2_all_reading']} / {P.lab['r']['gate_eq_r2_all_reading']}" == "NOT-SHOWN / SIGNAL"
    assert P.straddle("p", "gate_eq_r2|B=16|all") and not P.straddle("p", "gate_eq_r2|B=16|fallback")
    findings = (ROOT / "FINDINGS.md").read_bytes().replace(b"\r\n", b"\n").decode("utf-8")
    status = [ln for ln in findings.split("\n") if ln.startswith("- status (2026-10-03;")]
    assert status, "F-26's 2026-10-03 status line is missing from FINDINGS.md"
    assert any(fb in ln and al in ln for ln in status)
