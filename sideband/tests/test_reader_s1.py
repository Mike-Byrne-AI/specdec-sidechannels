"""tests/test_reader_s1.py — the S1 word instrument tools/run_reader_s1.py (docs/BLUEPRINT.md, "S1 READER RE-TEST
REGISTRATION", 2026-10-16): the word rules on every branch over frozen pair labels, the conclude flow on fake s1
payloads through the frozen verify_payload, every refusal (the reader set, the launch commit, the stage binding,
the same harvest, a stored number that differs, the registered-out rules), the pairing block, and the assertion,
at import and again before any conclusion, that the frozen reader-lens instrument is the one this file was
written against. No torch, no harvest; the fakes are tests/test_reader_lens.py's. Written before any
reader-variant cell at S1 trained."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests"))                      # the fixtures' module, whatever pytest's import mode
import run_reader_lens as rl  # noqa: E402
import run_reader_s1 as rs  # noqa: E402
from test_reader_lens import NPZ, NPZ_R, NULL_D, _payload, _readouts  # noqa: E402  (its fixtures)

S1 = rl.SPACE_L1["concept"]
READERS = ("RN", "RT", "RL")


def _lab(primary: dict, replication: dict | None = None) -> dict:
    return rl.pair_label(primary, replication if replication is not None else primary, (rl.GATE_OFFSET,), stronger_word=True)


FIRE = _readouts(S1)                                            # D fires, Mt upper >= 0, Mn_r upper >= 0, Mt below the floor
NULL = _readouts(S1, **NULL_D)                                  # ABSORBED
NOT_SHOWN = _readouts(S1, d=(0.002, -0.001, 0.006))             # no fire, an upper at the floor or above
MT_FIRE = _readouts(S1, mt=(0.006, 0.002, 0.01))                # D fires AND Mt fires the triple rule
NEG_TWIN = _readouts(S1, mnr=(-0.004, -0.007, -0.001))          # D fires with Mn_r's upper below 0
INVALID = _readouts(S1, ok=False)


# ---------------------------------------------------------------------------
# the pinned word rules, every branch, over the FROZEN pair labels
# ---------------------------------------------------------------------------

def test_the_fake_labels_read_as_the_frozen_rules_say():
    assert _lab(NULL)["label"] == rl.LABEL_ABSORBED
    assert _lab(NOT_SHOWN)["label"] == rl.LABEL_NOT_SHOWN
    assert _lab(FIRE, NULL)["label"] == rl.LABEL_SPLIT
    v = _lab(FIRE)
    assert v["label"] == rl.LABEL_STRONGER and v["licence"] == "full" and not rl.reopen_eligible(v)
    w = _lab(MT_FIRE)
    assert w["label"] == rl.LABEL_STRONGER and w["licence"] == "full" and rl.reopen_eligible(w)
    x = _lab(FIRE, NEG_TWIN)
    assert x["label"] == rl.LABEL_STRONGER and x["licence"] == "equal-dims-only" and not rl.reopen_eligible(x)
    assert _lab(INVALID)["label"] == rl.LABEL_READER_INVALID


def test_s1_word_every_branch_and_the_precedence():
    key = {r: f"{r}|{S1}" for r in READERS}
    all_null = {key[r]: _lab(NULL) for r in READERS}
    w = rs.s1_word(all_null)
    assert w["word"] == rs.WORD_NOT_OVERTURNED and w["narrowed_cells"] == sorted(key.values()) and w["not_narrowed_cells"] == []
    assert not w["provisional"] and w["reader_matched_rider_rule"] is None and w["void_cells"] == [] and not w["over_valid_cells_only"]
    mixed = {key["RN"]: _lab(NULL), key["RT"]: _lab(NOT_SHOWN), key["RL"]: _lab(NULL)}
    w = rs.s1_word(mixed)
    assert w["word"] == rs.WORD_NOT_OVERTURNED and w["not_narrowed_cells"] == [key["RT"]] and w["narrowed_cells"] == [key["RL"], key["RN"]]
    w = rs.s1_word({key["RN"]: _lab(FIRE, NULL), key["RT"]: _lab(NULL), key["RL"]: _lab(NOT_SHOWN)})
    assert w["word"] == rs.WORD_UNSETTLED and w["split"] == [key["RN"]]
    w = rs.s1_word({key["RN"]: _lab(FIRE), key["RT"]: _lab(FIRE, NULL), key["RL"]: _lab(NULL)})
    assert w["word"] == rs.WORD_ISOLATED and list(w["survives_stronger"]) == [key["RN"]]
    assert w["survives_stronger"][key["RN"]]["licence"] == "full" and w["reopened"] == [] and not w["provisional"]
    w = rs.s1_word({key["RN"]: _lab(FIRE, NEG_TWIN), key["RT"]: _lab(NULL), key["RL"]: _lab(NULL)})
    assert w["word"] == rs.WORD_ISOLATED and w["survives_stronger"][key["RN"]]["licence"] == "equal-dims-only"
    assert "twin" in w["survives_stronger"][key["RN"]]["licence_reason"]
    w = rs.s1_word({key["RN"]: _lab(MT_FIRE), key["RT"]: _lab(FIRE, NULL), key["RL"]: _lab(FIRE)})
    assert w["word"] == rs.WORD_REOPENED and w["reopened"] == [key["RN"]] and w["provisional"]
    assert "reader-matched rider" in w["reader_matched_rider_rule"] and "S1 harvests" in w["reader_matched_rider_rule"]
    assert sorted(w["survives_stronger"]) == [key["RL"], key["RN"]] and w["split"] == [key["RT"]]
    assert w["per_source"].startswith("S1") and "does not move" in w["per_source"]
    w = rs.s1_word({key["RN"]: _lab(INVALID), key["RT"]: _lab(NULL), key["RL"]: _lab(FIRE, NULL)})
    assert w["word"] == rs.WORD_UNSETTLED and w["void_cells"] == [key["RN"]] and w["over_valid_cells_only"]
    w = rs.s1_word({key[r]: _lab(INVALID) for r in READERS})
    assert w["word"] == rs.WORD_INCOMPLETE and w["void_cells"] == sorted(key.values())
    assert rs.s1_word({key["RN"]: _lab(NULL)})["word"] == rs.WORD_NOT_OVERTURNED          # one reader is a valid board
    assert rs.s1_word({})["word"] == rs.WORD_INCOMPLETE
    assert set(rs.WORDS) == {rs.WORD_INCOMPLETE, rs.WORD_REOPENED, rs.WORD_ISOLATED, rs.WORD_UNSETTLED, rs.WORD_NOT_OVERTURNED}
    for word in rs.WORDS:
        assert word.endswith("-AT-S1") and word.startswith("K-2-")


def test_s1_word_refuses_a_foreign_space_and_an_unknown_label():
    with pytest.raises(SystemExit, match="not the S1 gate space"):
        rs.s1_word({f"RN|{rl.SPACE_L1['olmoe']}": _lab(NULL)})
    bad = dict(_lab(NULL))
    bad["label"] = "SURVIVES-FULL-FREE-ISH"
    with pytest.raises(SystemExit, match="unknown label"):
        rs.s1_word({f"RN|{S1}": bad})


# ---------------------------------------------------------------------------
# the frozen-instrument assertion
# ---------------------------------------------------------------------------

def test_the_frozen_reader_lens_sha_is_the_attested_one_and_asserted_at_import_and_at_conclude(monkeypatch):
    on_disk = hashlib.sha256(Path(rl.__file__).read_bytes()).hexdigest()
    assert rs.FROZEN_READER_LENS_SHA256 == on_disk
    import test_reader_lens_readers_long_landing as landed
    assert rs.FROZEN_READER_LENS_SHA256 == landed.INSTRUMENT_SHA256
    assert rs.FROZEN_CHAIN_AT_IMPORT["reader_lens_sha256"] == on_disk           # asserted when the module was imported
    chain = rs.assert_frozen_reader_lens()
    assert chain["reader_lens_sha256"] == on_disk and chain["amended_sha256"] == rl.AMENDED_INSTRUMENT_SHA256
    monkeypatch.setattr(rs, "FROZEN_READER_LENS_SHA256", "0" * 64)
    with pytest.raises(SystemExit, match="refusing"):
        rs.assert_frozen_reader_lens()
    with pytest.raises(SystemExit, match="refusing"):
        rs.conclude(Path("x.json"), Path("y.json"))


def test_a_wrong_frozen_sha_refuses_the_import_itself():
    # the module's source with its pinned digest altered, executed as a module in a fresh interpreter: the
    # module-level assertion fails closed before anything else is defined
    src = (ROOT / "tools" / "run_reader_s1.py").read_text(encoding="utf-8")
    assert src.count(rs.FROZEN_READER_LENS_SHA256) == 1
    bad = src.replace(rs.FROZEN_READER_LENS_SHA256, "0" * 64)
    code = ("import sys; sys.path.insert(0, 'tools'); sys.path.insert(0, 'src'); "
            "exec(compile(sys.stdin.read(), 'tools/run_reader_s1.py', 'exec'), {'__name__': 'altered', '__file__': 'tools/run_reader_s1.py'})")
    r = subprocess.run([sys.executable, "-c", code], input=bad, capture_output=True, text=True, cwd=ROOT, timeout=120)
    assert r.returncode != 0 and "refusing" in (r.stderr + r.stdout)
    r2 = subprocess.run([sys.executable, "-c", code], input=src, capture_output=True, text=True, cwd=ROOT, timeout=120)
    assert r2.returncode == 0, r2.stderr[-500:]


# ---------------------------------------------------------------------------
# conclude on fake s1 payloads through the FROZEN verify_payload
# ---------------------------------------------------------------------------

def _s1_pair(tmp_path, per_rs, readers=READERS, npz_r=NPZ_R, **over):
    p = _payload(tmp_path, "readers_s1.json", "s1", NPZ, per_rs, tag="concept", readers_list=readers, **over)
    r = _payload(tmp_path, "readers_s1_r.json", "s1", npz_r, per_rs, tag="concept", readers_list=readers, **over)
    return p, r


def _fake_recompute(monkeypatch, tmp_path):
    monkeypatch.setattr(rl, "PAYLOAD_ROOT", tmp_path)
    monkeypatch.setattr(rl, "recompute_readouts", lambda p, cells, data_root=rl.REAL: p["per_reader_space"])


def test_conclude_issues_the_word_from_the_frozen_labels(tmp_path, monkeypatch):
    _fake_recompute(monkeypatch, tmp_path)
    per_rs = {f"RN|{S1}": NULL, f"RT|{S1}": NOT_SHOWN, f"RL|{S1}": NULL}
    p, r = _s1_pair(tmp_path, per_rs)
    out = rs.conclude(p, r, data_root=tmp_path)
    assert out["word"]["word"] == rs.WORD_NOT_OVERTURNED and out["readers"] == list(READERS) and out["space"] == S1
    assert out["labels"][f"RN|{S1}"]["label"] == rl.LABEL_ABSORBED and out["labels"][f"RT|{S1}"]["label"] == rl.LABEL_NOT_SHOWN
    assert out["inputs"]["primary"]["n_rows"] == 36 and out["inputs"]["replication"]["n_rows"] == 36
    assert out["inputs"]["primary"]["payload_sha256"] == hashlib.sha256(p.read_bytes()).hexdigest()
    assert out["inputs"]["replication"]["state_sha256"] == hashlib.sha256((tmp_path / "readers_s1_r.json.state.jsonl").read_bytes()).hexdigest()
    assert out["inputs"]["primary"]["harvest"].endswith("harvest_shadow") and out["inputs"]["replication"]["harvest"].endswith("harvest_shadow_r")
    assert out["materiality_floor"] == rl.MATERIALITY and out["frozen_chain"]["reader_lens_sha256"] == rs.FROZEN_READER_LENS_SHA256
    assert set(out["diagnostics"]) == set(out["labels"])
    assert out["diagnostics"][f"RN|{S1}"]["reader_valid"] == {"primary": {"ok": True}, "replication": {"ok": True}}   # the full frozen dicts
    assert out["diagnostics"][f"RN|{S1}"]["best_epochs"] == {"primary": {"fplus": [1, 1, 1]}, "replication": {"fplus": [1, 1, 1]}}
    assert out["inputs"]["data_root"] == str(tmp_path.resolve())
    # the pairing block: descriptive, never a refusal; on fakes the committed twin payload is absent and the RN / RT
    # fresh (a) rows (identical fakes) read identical except runtime
    pr = out["pairing"]["primary"]
    assert pr["committed_twin_payload"] == "fullfree_s1_twin.json" and pr["perm_sha256_committed"] is None
    assert pr["twin_perm_sha256_equal_to_committed"] is False
    assert sorted(pr["rn_rt_fresh_a_rows"]) == ["0", "1", "2"] and pr["rn_rt_fresh_a_rows_all_identical"] is True
    assert out["pairing"]["replication"]["committed_twin_payload"] == "fullfree_s1_r_twin.json"
    # the frozen tool's own conclude-from on the same pair yields the same labels and no word
    frozen = rl.conclude_from(p, r, data_root=tmp_path)
    assert {k: v["label"] for k, v in frozen["labels"].items()} == {k: v["label"] for k, v in out["labels"].items()}
    assert "k2" not in frozen and "note" in frozen
    # a reopen-grade board
    (tmp_path / "re").mkdir(exist_ok=True)
    p2, r2 = _s1_pair(tmp_path / "re", {f"RN|{S1}": MT_FIRE, f"RT|{S1}": NULL, f"RL|{S1}": NULL})
    monkeypatch.setattr(rl, "PAYLOAD_ROOT", tmp_path / "re")
    out2 = rs.conclude(p2, r2, data_root=tmp_path / "re")
    assert out2["word"]["word"] == rs.WORD_REOPENED and out2["word"]["reopened"] == [f"RN|{S1}"] and out2["word"]["provisional"]


def test_conclude_refusals(tmp_path, monkeypatch):
    _fake_recompute(monkeypatch, tmp_path)
    per_rs = {f"RN|{S1}": NULL, f"RT|{S1}": NULL, f"RL|{S1}": NULL}
    p, r = _s1_pair(tmp_path, per_rs)
    # a readers payload where an s1 payload is required (the frozen stage binding), never read as S1
    s3 = {f"RN|{rl.SPACE_L1['olmoe']}": NULL}
    rd = _payload(tmp_path, "readers_s3.json", "readers", NPZ, {**s3, f"RN|{rl.SPACE_L3_LOP}": NULL, f"RN|{rl.SPACE_L3_BAL}": NULL,
                                                                 f"RT|{rl.SPACE_L1['olmoe']}": NULL, f"RT|{rl.SPACE_L3_LOP}": NULL,
                                                                 f"RT|{rl.SPACE_L3_BAL}": NULL})
    with pytest.raises(SystemExit, match="where a s1 payload is required"):
        rs.conclude(rd, r, data_root=tmp_path)
    # the same harvest twice is not a pair
    p_same, r_same = _s1_pair(tmp_path, per_rs, npz_r=NPZ)
    with pytest.raises(SystemExit, match="SAME harvest"):
        rs.conclude(p_same, r_same, data_root=tmp_path)
    # the reader set is pinned: exactly RN, RT, RL in that order, on both payloads (the frozen verify_payload takes
    # an s1 payload's readers from the payload itself, so a mis-launched pair must be refused HERE)
    p3, _ = _s1_pair(tmp_path, per_rs)
    r3 = _payload(tmp_path, "readers_s1_r.json", "s1", NPZ_R, {f"RN|{S1}": NULL, f"RT|{S1}": NULL}, tag="concept", readers_list=("RN", "RT"))
    with pytest.raises(SystemExit, match="replication payload names readers"):
        rs.conclude(p3, r3, data_root=tmp_path)
    one = {f"RN|{S1}": MT_FIRE}
    p_one, r_one = _s1_pair(tmp_path, one, readers=("RN",))
    with pytest.raises(SystemExit, match="primary payload names readers"):
        rs.conclude(p_one, r_one, data_root=tmp_path)
    with_r0 = {f"R0|{S1}": MT_FIRE, f"RN|{S1}": NULL, f"RT|{S1}": NULL, f"RL|{S1}": NULL}
    p_r0, r_r0 = _s1_pair(tmp_path, with_r0, readers=("R0", "RN", "RT", "RL"))
    with pytest.raises(SystemExit, match="R0 is not re-run"):              # never a REOPENED word from the registered reader
        rs.conclude(p_r0, r_r0, data_root=tmp_path)
    p_ord, r_ord = _s1_pair(tmp_path, per_rs, readers=("RT", "RN", "RL"))
    with pytest.raises(SystemExit, match="in that order"):
        rs.conclude(p_ord, r_ord, data_root=tmp_path)
    # one registration, one launch HEAD: payloads from different commits are refused
    p5, _ = _s1_pair(tmp_path, per_rs)
    r5 = _payload(tmp_path, "readers_s1_r.json", "s1", NPZ_R, per_rs, tag="concept", readers_list=READERS, head="h2")
    with pytest.raises(SystemExit, match="different commits"):
        rs.conclude(p5, r5, data_root=tmp_path)


def test_a_stored_number_that_differs_from_the_state_file_is_refused_by_the_frozen_recompute(tmp_path, monkeypatch):
    # the frozen recompute_readouts stays REAL here; its inputs are stubbed so the re-derived readouts differ from the
    # payload's stored ones, and the frozen refusal fires on the s1 path (tests/test_reader_lens.py's pattern)
    monkeypatch.setattr(rl, "PAYLOAD_ROOT", tmp_path)
    monkeypatch.setattr(rl, "load_phase3_cells", lambda *a, **k: [])
    monkeypatch.setattr(rl, "readouts_for", lambda *a, **k: {"tampered": True})
    per_rs = {f"RN|{S1}": NULL, f"RT|{S1}": NULL, f"RL|{S1}": NULL}
    p, r = _s1_pair(tmp_path, per_rs)
    with pytest.raises(SystemExit, match="does not reproduce"):
        rs.conclude(p, r, data_root=tmp_path)


def test_write_word_registered_out_rules_and_the_scratch_write(tmp_path, monkeypatch):
    _fake_recompute(monkeypatch, tmp_path)
    per_rs = {f"RN|{S1}": NULL, f"RT|{S1}": NULL, f"RL|{S1}": NULL}
    p, r = _s1_pair(tmp_path, per_rs)
    out = rs.conclude(p, r, data_root=tmp_path)
    # outside results/: a scratch write, registered false, LF bytes, the provenance block
    scratch = rs.write_word(tmp_path / "word.json", out)
    raw = scratch.read_bytes()
    assert b"\r\n" not in raw and raw.endswith(b"\n")
    d = json.loads(raw.decode("utf-8"))
    assert d["registered"] is False and d["word"]["word"] == rs.WORD_NOT_OVERTURNED
    assert d["provenance"]["instrument_sha256"] == hashlib.sha256(Path(rs.__file__).read_bytes()).hexdigest()
    assert d["provenance"]["reader_lens_sha256"] == rs.FROZEN_READER_LENS_SHA256 and d["provenance"]["out"] == "word.json"
    assert {"git_commit", "git_status_tracked", "numpy_version", "python_version", "platform"} <= set(d["provenance"])
    # the registered name (under a FAKE results/real; the real tree is never written by a test): a dirty tracked tree
    # refuses, an untracked instrument refuses, a foreign data root refuses, a clean tree writes once, a second write refuses
    fake_real = tmp_path / "results" / "real"
    fake_real.mkdir(parents=True)
    monkeypatch.setattr(rs, "REAL", fake_real)
    monkeypatch.setattr(rl, "REAL", fake_real)
    target = fake_real / rs.REGISTERED_OUT
    monkeypatch.setattr(rs, "_git", lambda strict: ("h" * 40, [" M docs/BLUEPRINT.md"]))
    with pytest.raises(SystemExit, match="not clean"):
        rs.write_word(target, out)
    assert not target.exists()
    monkeypatch.setattr(rs, "_git", lambda strict: ("h" * 40, []))
    monkeypatch.setattr(rs, "_tool_tracked", lambda: False)
    with pytest.raises(SystemExit, match="not git-tracked"):
        rs.write_word(target, out)
    monkeypatch.setattr(rs, "_tool_tracked", lambda: True)
    with pytest.raises(SystemExit, match="committed companions"):      # out["inputs"]["data_root"] is tmp_path, not the fake REAL
        rs.write_word(target, out)
    assert not target.exists()
    out["inputs"]["data_root"] = str(fake_real.resolve())
    written = rs.write_word(target, out)
    d = json.loads(written.read_text(encoding="utf-8"))
    assert d["registered"] is True and d["provenance"]["git_commit"] == "h" * 40 and d["provenance"]["git_status_tracked"] == []
    with pytest.raises(SystemExit, match="written once"):
        rs.write_word(target, out)
    with pytest.raises(SystemExit, match="may not be written under results/"):
        rs.write_word(fake_real / "other.json", out)


def test_main_runs_the_cli_end_to_end_on_fakes(tmp_path, monkeypatch, capsys):
    _fake_recompute(monkeypatch, tmp_path)
    per_rs = {f"RN|{S1}": NULL, f"RT|{S1}": NOT_SHOWN, f"RL|{S1}": NULL}
    p, r = _s1_pair(tmp_path, per_rs)
    out = tmp_path / "word.json"
    monkeypatch.setattr(sys, "argv", ["run_reader_s1.py", "--conclude", str(p), str(r), "--out", str(out), "--data-root", str(tmp_path)])
    rs.main()
    printed = json.loads(capsys.readouterr().out)
    assert printed["word"] == rs.WORD_NOT_OVERTURNED and printed["labels"][f"RT|{S1}"] == [rl.LABEL_NOT_SHOWN, None]
    assert out.exists() and json.loads(out.read_text(encoding="utf-8"))["word"]["word"] == rs.WORD_NOT_OVERTURNED
    parser = rs.build_parser()
    assert "readers_s1_word.json" in parser.format_help()
