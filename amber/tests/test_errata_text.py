"""experiments/errata_text.py: placement is derived from the payload, insertions are append-only, lint lines exist, no raw pipes."""

import json
import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "experiments"))
import errata_text as ET  # noqa: E402

FINDINGS = "# Findings\n\n## F-1 — a\n- date: x\n- finding: y\n\n## F-2 — b\n- date: x\n- caveats: z\n\n## F-3 — c\n- date: x\n"


def test_insert_lines_is_append_only_and_bottom_up():
    lines = ["a", "b", "c", "d"]
    new = ET.insert_lines(lines, [(0, "A1"), (3, "D1"), (0, "A2"), (1, "B1")])
    assert len(new) == 8 and ET.is_subsequence(lines, new)
    assert new[0] == "a" and new[-1] == "D1" and new.index("b") > new.index("A1") and new.index("c") > new.index("B1")
    assert new[:3] == ["a", "A1", "A2"], "texts sharing an index keep their list order (an erratum line before a block on the last line)"
    assert not ET.is_subsequence(["a", "x"], new)


def test_finding_blocks_and_rows_by_finding():
    blocks = ET.finding_blocks(FINDINGS)
    assert [b[0] for b in blocks] == ["F-1", "F-2", "F-3"] and blocks[0][1:] == (2, 6) and blocks[2][2] == len(FINDINGS.split("\n"))
    payload = {"rows": {rid: {"where": []} for rid in ET.ROW_ORDER}}
    payload["rows"]["E2"]["where"] = ["FINDINGS.md:4"]          # inside F-1
    payload["rows"]["E3"]["where"] = ["FINDINGS.md:4", "README.md:3-4"]
    payload["rows"]["E11"]["where"] = ["FINDINGS.md:8"]         # inside F-2
    assert ET.rows_by_finding(payload, FINDINGS) == {"F-1": ["E2", "E3"], "F-2": ["E11"]}
    notes = ET.pointer_notes(payload, {})
    assert notes == {"README.md": {(3, 4): ["E3"]}}


def test_paragraph_end_and_note_styles():
    lines = ["**bold claim that", "continues here.**", "", "next para", "- bullet"]
    assert ET.paragraph_end(lines, 0) == 1 and ET.paragraph_end(lines, 3) == 3 and ET.paragraph_end(lines, 4) == 4
    T = {"E1": "one.", "E12": "twelve."}
    assert ET.note_line("README.md", "2026-10-10", ["E1", "E12"], T).startswith("> Erratum (2026-10-10; F-14 rows E1, E12): E1: one. E12: twelve.")
    assert ET.note_line("DECISIONS.md", "2026-10-10", ["E8b"], T | {"E8b": "ok."}).startswith("- erratum (2026-10-10; F-14 row E8b): ")
    assert ET.note_line("experiments/P7_PROTOCOL.md", "2026-10-10", ["E14"], {"E14": "gone."}) == "Withdrawn (2026-10-10; F-14 row E14): gone."


@pytest.mark.parametrize("payload, fid, rows", [("results/errata_recompute.json", "F-14", ET.ROW_ORDER[:16]),
                                                ("results/errata_recompute_2.json", "F-15", ["E15", "E16"]),
                                                ("results/errata_recompute_3.json", "F-16", ["E17", "E18", "E19"])])
def test_generated_text_from_the_committed_payloads(payload, fid, rows):
    if not (REPO / payload).exists():
        pytest.skip(f"{payload} not written yet")
    P = json.loads((REPO / payload).read_text(encoding="utf-8"))
    try:
        T = ET.row_texts(P)
    except KeyError as e:
        import errata_lib as L
        pv = P["provenance"]
        if (pv.get("lib_sha256_lf") != L.sha256_lf(REPO / "experiments" / "errata_lib.py")
                or pv.get("script_sha256_lf") != L.sha256_lf(REPO / "experiments" / "errata_recompute.py")):
            pytest.xfail(f"{payload} was written by an older recompute (missing {e}); regenerate it on a clean tree")
        raise
    assert set(T) == set(P["rows"]) == set(rows) and ET.rows_present(P) == rows and all(T[r] for r in rows)
    block = ET.BLOCKS[fid](P, T)
    assert re.search(rf"^## {fid} — ", block, flags=re.M) and re.search(r"^- regime: \S", block, flags=re.M) and re.search(r"^- source: \S", block, flags=re.M)
    for tok in re.split(r"[,\s]+", re.search(r"^- source: *(.*)$", block, flags=re.M).group(1)):
        tok = tok.strip().rstrip(";.")
        if tok.startswith(("results/", "experiments/", "tests/", "docs/", "src/")):
            assert (REPO / tok).exists(), tok
    for rid in rows:
        r = P["rows"][rid]
        assert f"  - {rid} [{r['status']}" in block                      # qualifiers may follow the status inside the bracket
        if r.get("status_under_pinned_rule"):
            assert f"{r['status_under_pinned_rule']} under the pinned rule" in block
        if r.get("status_in_claim_regime"):
            assert f"{r['status_in_claim_regime']} in the claim's own regime" in block
        for site, s in (r.get("status_by_claim_site") or {}).items():
            assert f"{site} {s}" in block
        for arm, s in (r.get("status_by_arm") or {}).items():
            assert f"{arm} {s}" in block
    for text in [block, *T.values(), ET.readme_status_note(P, fid)]:
        assert not re.search(r"(?<!\\)\|", text), "unescaped pipe in generated markdown"
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", ET.date_of(P))
    assert fid in ET.readme_status_note(P, fid)


def test_first_payload_date_and_second_payload_batch():
    P1 = json.loads((REPO / "results" / "errata_recompute.json").read_text(encoding="utf-8"))
    P2 = json.loads((REPO / "results" / "errata_recompute_2.json").read_text(encoding="utf-8"))
    assert ET.date_of(P1) == "2026-10-10" and P2["provenance"]["batch"] == 2 and "E15" not in P1["rows"]


def test_status_bracket_and_note_fid():
    r = {"status": "CORRECTED", "status_by_arm": {"a1": "CORRECTED", "a8": "CONFIRMED"}, "status_in_claim_regime": "CONFIRMED"}
    assert ET.status_bracket(r) == "CORRECTED; CONFIRMED in the claim's own regime; by arm: a1 CORRECTED, a8 CONFIRMED"
    r = {"status": "CORRECTED", "status_by_class": {"A": "CORRECTED", "C": "CONFIRMED"}, "status_at_claim_scope": {"a1": "CONFIRMED"},
         "status_by_claim_site": {"X.md:1 (top-1)": "CONFIRMED"}}
    assert ET.status_bracket(r) == ("CORRECTED; by class over the decoded positions: A CORRECTED, C CONFIRMED; at the claims' own scope, slot 0: "
                                    "a1 CONFIRMED; by claim site: X.md:1 (top-1) CONFIRMED")
    assert ET.note_line("OPEN_QUESTIONS.md", "2026-10-11", ["E16"], {"E16": "t."}, "F-15") == "> Erratum (2026-10-11; F-15 row E16): E16: t."


def test_location_label_and_claim_site_counts():
    P = {"rows": {
        "E15": {"status": "CORRECTED", "value": {"pinned_rule_sites": ["FINDINGS.md:85"]},
                "status_by_claim_site": {"FINDINGS.md:72 (own regime)": "CONFIRMED", "FINDINGS.md:85 (class C)": "CONFIRMED", "docs/BLUEPRINT.md:57": "CONFIRMED"}},
        "E16": {"status": "CORRECTED", "value": {"pinned_rule_sites": ["FINDINGS.md:114", "OPEN_QUESTIONS.md:15"]},
                "status_by_claim_site": {"FINDINGS.md:55 (slot 0)": "CONFIRMED", "FINDINGS.md:114, OPEN_QUESTIONS.md:15 (depth)": "CORRECTED"}},
        "E7": {"status": "CONFIRMED", "value": {}}, "E2": {"status": "CORRECTED", "value": {}}}}
    assert ET.location_label(P, ["E15"], "FINDINGS.md", 72, 79) == "note"          # the sites there stand
    assert ET.location_label(P, ["E15"], "FINDINGS.md", 80, 87) == "erratum"       # the pinned rule's site
    assert ET.location_label(P, ["E15"], "docs/BLUEPRINT.md", 57, 57) == "note"
    assert ET.location_label(P, ["E16"], "FINDINGS.md", 50, 56) == "note" and ET.location_label(P, ["E16"], "FINDINGS.md", 102, 130) == "erratum"
    assert ET.location_label(P, ["E16"], "OPEN_QUESTIONS.md", 15, 16) == "erratum"
    assert ET.location_label(P, ["E7"], "FINDINGS.md", 1, 9) == "note" and ET.location_label(P, ["E2"], "FINDINGS.md", 1, 9) == "erratum"
    assert ET.site_tokens("FINDINGS.md:76 (F-10 item (1), A desyncs at theta 0: slot 0)") == [("FINDINGS.md", 76)]
    assert ET.claim_site_counts(P) == (5, 7)                                        # 3 + 2 sites, plus E7 (stands) and E2 (corrected) as one site each


def test_score_predictions_labels_sources():
    P = {"rows": {"E15": {"status": "CORRECTED", "prediction": {"a": 77, "b": 170, "c": 1.5, "d": 1.5, "e": 4.4}, "value": {"a": 76.6, "b": 170.4, "c": 1.49, "d": 1.44, "e": 4.44,
                          "prediction_sources": {"a": "the critic (x)", "b": "this protocol (y)", "e": "the review harvest (z)"}}},
                  "E19": {"status": "CONFIRMED", "prediction": {}, "value": {"prediction_note": "not scored: identical by construction"}}}}
    assert ET.score_predictions(P) == {"E15": ["a hit (critic)", "b hit (protocol)", "c hit", "d miss", "e hit (harvest)"],
                                       "E19": ["not scored: identical by construction"]}            # scored at the prediction's precision
    r = {"status": "CONFIRMED", "status_by_count": "CONFIRMED", "post_hoc": "rule after values", "status_out_of_sample": "CONFIRMED"}
    assert ET.status_bracket(r) == "CONFIRMED; CONFIRMED by beyond-count; post hoc: rule after values; CONFIRMED out of sample (the other binnings)"


def test_plan_edits_merges_notes_sharing_an_insertion_point(monkeypatch):
    P = {"provenance": {"written_unix": 0, "inputs": {}}, "summary": {"E18": "CORRECTED"},
         "rows": {"E18": {"status": "CORRECTED", "claim": "c", "where": ["README.md:2", "README.md:3"], "value": {"pinned_rule_sites": []},
                          "status_by_claim_site": {"README.md:2 (a)": "CONFIRMED", "README.md:3 (b)": "CORRECTED"}}}}
    files = {"FINDINGS.md": "# F\n\n## F-1 — a\n- date: x\n", "README.md": "# R\n\n## Status\n\nline two\nline three\n\nnext\n"}
    monkeypatch.setattr(ET, "read_lf", lambda path: (files[path.name], b"\n"))
    monkeypatch.setattr(ET, "row_texts", lambda P: {"E18": "text."})
    monkeypatch.setitem(ET.BLOCKS, "F-16", lambda P, T: "## F-16 — t\n- date: x\n- regime: r\n- source: s\n")
    notes = [t for i, t in ET.plan_edits(P, "F-16")["README.md"] if t.startswith(">") and "F-16 row" in t]
    assert len(notes) == 1 and notes[0].startswith("> Erratum (")                  # one note for the paragraph, erratum because one site is corrected


def test_merge_locations_joins_touching_ranges_only():
    locs = {(16, 16): ["E16"], (15, 15): ["E16"], (30, 31): ["E7"], (3, 4): ["E1", "E12"], (5, 5): ["E12", "E3"]}
    assert ET.merge_locations(locs) == {(3, 5): ["E1", "E12", "E3"], (15, 16): ["E16"], (30, 31): ["E7"]}
    payload = {"rows": {"E16": {"where": ["OPEN_QUESTIONS.md:16", "OPEN_QUESTIONS.md:15", "README.md:50"]}}}
    assert ET.pointer_notes(payload, {}) == {"OPEN_QUESTIONS.md": {(15, 16): ["E16"]}, "README.md": {(50, 50): ["E16"]}}


def test_status_note_goes_after_existing_notes():
    assert ET.status_note_index(["# T", "## Status", "", "text"]) == 2
    assert ET.status_note_index(["# T", "## Status", "", "> first note", "> second note", "text"]) == 4


@pytest.mark.parametrize("payload, fid", [("results/errata_recompute.json", "F-14"), ("results/errata_recompute_2.json", "F-15")])
def test_plan_edits_refuses_a_second_run(monkeypatch, payload, fid):
    P = json.loads((REPO / payload).read_text(encoding="utf-8"))
    monkeypatch.setattr(ET, "read_lf", lambda path: (f"## {fid} — already\n- date: x\n", b"\n"))
    with pytest.raises(ValueError, match="already exists"):
        ET.plan_edits(P, fid)
