"""OQ-18 amended instrument (tools/run_fullfree_coarse_amended.py): the frozen
instrument's sha is pinned; the grid adds only the fourth shuffled cell;
the reuse rule re-trains histogram-less shuffled rows; the amended rider
(leg 1 halts as registered, the raw leg 2 is reported and never halts, the
amended leg halts on a CI-clear material or above-band twin excess);
rider-v1 preservation; the amended conclusion refuses v1 payloads and
carries the reroute disclosure. No torch."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path, PureWindowsPath

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import run_fullfree_coarse as fz  # noqa: E402
import run_fullfree_coarse_amended as am  # noqa: E402
import run_oq18_rider_diag as rd  # noqa: E402


def test_frozen_instrument_sha_is_pinned_and_true_on_disk():
    assert am._sha(am.FROZEN_INSTRUMENT) == am.FROZEN_INSTRUMENT_SHA256
    am.assert_frozen_instrument()


@pytest.mark.parametrize("tag,n_trained", [("concept", 60), ("olmoe", 69)])
def test_grid_adds_only_the_twin_shuffled_cell(tag, n_trained):
    spaces = fz.registered_spaces(tag)
    frozen = fz.build_grid(spaces)
    amended = am.build_grid_amended(spaces)
    assert [c for c in frozen if not c[5]] == [c for c in amended if not c[5]]
    assert len([c for c in amended if not c[5]]) == n_trained
    for sp in spaces:
        sh = [c for c in amended if c[5] and c[0] == sp]
        assert sh == [(sp, 2, arm, "linear", 0, True) for arm in am.SHUFFLED_ARMS]
    assert len(amended) == len(frozen) + len(spaces)


def test_reuse_rule_retrains_histogram_less_shuffled_rows():
    done = {"x|SHUFFLED": {"test_acc": 0.5}, "y|SHUFFLED": {"test_acc": 0.5, "_hist": {}}, "z": {"test_acc": 0.4}}
    assert not am.reusable("x|SHUFFLED", done, True)
    assert am.reusable("y|SHUFFLED", done, True)
    assert am.reusable("z", done, False)
    assert not am.reusable("w", done, False)


def _cell(space, arm, per_prompt, n_classes, acc=None, with_hist=True):
    h = {}
    for p, (pred, y, wrap) in per_prompt.items():
        h.update(rd.histograms(np.asarray(pred), np.asarray(y), np.full(len(pred), p),
                               np.asarray(wrap, dtype=bool), n_classes))
    if acc is None:
        acc = float(np.mean(np.concatenate([np.asarray(v[0]) == np.asarray(v[1]) for v in per_prompt.values()])))
    c = {"cell": fz.cell_id(space, 2, arm, "linear", 0, True), "space": space, "offset": 2,
         "features": arm, "capacity": "linear", "seed": 0, "shuffled": True, "test_acc": acc,
         "best_epoch": 0, "majority_label": 0}
    if with_hist:
        c["_hist"] = h
    return c


def _prompts(n_classes=3, seed=0):
    rng = np.random.default_rng(seed)
    per = {}
    for p in range(30):
        y = rng.integers(0, n_classes, 60)
        wrap = np.zeros(60, dtype=bool)
        wrap[-4:] = True
        per[p] = (y, wrap)
    return per


def test_rider_check_amended_legs():
    sp = fz.registered_spaces("concept")[1]
    per = _prompts()
    const = {p: (np.zeros(60, dtype=int), y, w) for p, (y, w) in per.items()}
    rng = np.random.default_rng(3)
    informed = {p: (np.where(rng.random(60) < 0.6, y, rng.integers(0, 3, 60)), y, w) for p, (y, w) in per.items()}
    sa = _cell(sp, "a", const, 3, acc=0.40)
    assert am.rider_check_amended([], sp, 3) is None
    # leg 1 as registered: halts on a raw excess above the band
    sf_bad = _cell(sp, "fplus", const, 3, acc=0.42)
    with pytest.raises(SystemExit):
        am.rider_check_amended([sa, sf_bad], sp, 3, n_boot=50, expected_clusters=30)
    sf = _cell(sp, "fplus", const, 3, acc=0.39)
    out = am.rider_check_amended([sa, sf], sp, 3, n_boot=50, expected_clusters=30)
    assert out["leg1_pass"] and out["leg2_pass"] is None and out["pass"] is False
    # the registered raw leg 2 is REPORTED and never halts (raw excess +0.013 here)
    sb = _cell(sp, "fplus_b", const, 3, acc=0.403)
    out = am.rider_check_amended([sa, sf, sb], sp, 3, n_boot=50, expected_clusters=30)
    assert out["registered_leg2_raw"]["excess"] == pytest.approx(0.013)
    assert out["registered_leg2_raw"]["pass"] is False and out["leg2_pass"] is None
    # a twin with the same (constant) predictions: dE_br = 0 -> the amended leg passes
    sr = _cell(sp, "fplus_r", const, 3, acc=0.403)
    out = am.rider_check_amended([sa, sf, sb, sr], sp, 3, n_boot=50, expected_clusters=30)
    assert out["pass"] and out["leg2_pass"] and not out["amended_leg2"]["fails"]
    assert out["amended_leg2"]["d_E"] == pytest.approx(0.0)
    assert out["x_raw_seed0"] == pytest.approx(0.0) and out["x_raw_sentence"].endswith("would also have passed")
    assert set(out["E"]) == {"a", "fplus", "fplus_b", "fplus_r"}
    # an aligned block with real dependence over a constant twin: CI-clear and material -> halts
    sb_inf = _cell(sp, "fplus_b", informed, 3)
    with pytest.raises(SystemExit):
        am.rider_check_amended([sa, sf, sb_inf, sr], sp, 3, n_boot=50, expected_clusters=30)
    # a histogram-less (frozen-instrument) shuffled row is refused, never silently used
    sb_nohist = _cell(sp, "fplus_b", const, 3, acc=0.403, with_hist=False)
    with pytest.raises(SystemExit):
        am.rider_check_amended([sa, sf, sb_nohist, sr], sp, 3, n_boot=50, expected_clusters=30)
    # fplus_r without fplus_b is refused
    with pytest.raises(SystemExit):
        am.rider_check_amended([sa, sf, sr], sp, 3, n_boot=50, expected_clusters=30)


def test_preserve_v1(tmp_path):
    out = tmp_path / "fullfree_coarse_s3.json"
    assert am.preserve_v1(out) is None
    out.write_text(json.dumps({"registered": "OQ-18 COARSE-LABEL ... (frozen)", "provenance": {"instrument_sha256": "abc"}}))
    v1 = am.preserve_v1(out)
    assert v1 and v1["path"].endswith("fullfree_coarse_s3.rider_v1.json") and v1["frozen_instrument_sha256"] == "abc"
    assert not out.exists() and Path(v1["path"]).exists()
    # an amended payload is left in place for re-emission
    out.write_text(json.dumps({"registered": f"... {am.AMENDED_MARK} ..."}))
    assert am.preserve_v1(out) is None and out.exists()
    # a second frozen payload would need the v1 name again: refused
    out.write_text(json.dumps({"registered": "frozen again"}))
    with pytest.raises(SystemExit):
        am.preserve_v1(out)


def test_conclude_amended_refuses_v1_and_carries_the_disclosure(monkeypatch):
    v1 = {"registered": "OQ-18 COARSE-LABEL FULL-FREE RE-TEST REGISTRATION (frozen)"}
    with pytest.raises(SystemExit):
        am.conclude_amended(v1, v1)
    diag = {"branch": "AMENDABLE", "mechanism": "MARGINAL-DRIFT", "qualifiers": ["underpowered against x"],
            "x_raw_seed0": 0.004, "x_raw_sentence": "the registered statistic, twin-referenced, would also have passed"}
    sp = fz.registered_spaces("concept")[0]
    rider = {"pass": True, "leg1_pass": True, "leg2_pass": True}
    prov = {"git_status_tracked": list(am.LICENSED_DIRTY)}
    pp = {"registered": f"... {am.AMENDED_MARK} ...", "amendment": {"diagnostic": diag, "rider_v1_preserved": None},
          "per_space": {sp: {"rider": rider}}, "provenance": prov}
    rp = {"registered": f"... {am.AMENDED_MARK} ...", "amendment": {"diagnostic": diag, "rider_v1_preserved": {"path": "x"}},
          "per_space": {sp: {"rider": rider}}, "provenance": {"git_status_tracked": []}}
    monkeypatch.setattr(am.fz, "conclude", lambda p, r: {"spaces": {sp: {"label": "ABSORBED"}}, "rule": "frozen rule"})
    out = am.conclude_amended(pp, rp)
    assert out["spaces"][sp]["rider_amended"]["primary"] == rider
    d = out["amendment"]["disclosure"]
    assert d.startswith("read under the 2026-09-07 rider amendment")
    assert am.REROUTE_SENTENCE in d and "underpowered against x" in d and "+0.0040" in d
    assert am.DOMINANCE_SENTENCE in d and "S1 diagnostic X_raw at seed 0 +0.0040" in d
    assert d.index(am.REROUTE_SENTENCE) < d.index(am.DOMINANCE_SENTENCE) < d.index("S1 diagnostic X_raw")
    assert "\u2014" not in am.DOMINANCE_SENTENCE
    assert out["rule"].endswith("dependence-excess leg")
    # without the amendment block the payload is refused
    with pytest.raises(SystemExit):
        am.conclude_amended({"registered": f"{am.AMENDED_MARK}"}, rp)
    # an attestation beyond the licensed line is a violation: refused, never concluded
    bad = dict(pp)
    bad["provenance"] = {"git_status_tracked": list(am.LICENSED_DIRTY) + [" M docs/BLUEPRINT.md"]}
    with pytest.raises(SystemExit):
        am.conclude_amended(bad, rp)
    nop = dict(pp)
    nop["provenance"] = {}
    with pytest.raises(SystemExit):
        am.conclude_amended(nop, rp)


def test_guard_tolerates_exactly_the_licensed_line():
    am.guard_lines([], True)
    am.guard_lines(list(am.LICENSED_DIRTY), True)
    assert am.unlicensed_lines(list(am.LICENSED_DIRTY) + [""]) == []
    with pytest.raises(SystemExit):
        am.guard_lines([" M docs/BLUEPRINT.md"], True)
    with pytest.raises(SystemExit):
        am.guard_lines(list(am.LICENSED_DIRTY) + [" M results/real/fullfree_coarse_s3.json.state.jsonl"], True)
    with pytest.raises(SystemExit):
        am.guard_lines(["?? results/real/x.json", " D results/real/fullfree_coarse_s3.json"], True)
    with pytest.raises(SystemExit):
        am.guard_lines([], False)
    assert am.LICENSED_DIRTY == (" M results/real/fullfree_coarse_s1.json.state.jsonl",)


def test_load_diagnostic_requires_the_amendable_branch(tmp_path):
    p = tmp_path / "diag.json"
    with pytest.raises(SystemExit):
        am.load_diagnostic(p)
    p.write_text(json.dumps({"verdict": {"branch": "CONTENT-TRANSFER"}, "partial": False}))
    with pytest.raises(SystemExit):
        am.load_diagnostic(p)
    assert am.load_diagnostic(p, require_branch=None)["branch"] == "CONTENT-TRANSFER"
    p.write_text(json.dumps({"verdict": {"branch": "AMENDABLE", "mechanism": "MARGINAL-DRIFT"}, "partial": True}))
    with pytest.raises(SystemExit):
        am.load_diagnostic(p)
    p.write_text(json.dumps({"verdict": {"branch": "AMENDABLE", "mechanism": "MARGINAL-DRIFT"}, "partial": False}))
    assert am.load_diagnostic(p)["mechanism"] == "MARGINAL-DRIFT"


def test_parser_and_registered_out_refusals():
    ap = am.build_parser()
    a = ap.parse_args([])
    assert a.out == "results/real/fullfree_coarse_s1.json" and a.n_boot == rd.N_BOOT
    assert am.x_raw_sentence(0.01).endswith("would also have passed")
    assert am.x_raw_sentence(0.0101).endswith("would still have fired")


# ---------------------------------------------------------------------------
# The committed amended payloads (landed 2026-09-14) reproduce their own
# conclusion, resume plan, attestation and v1 preservation.
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
# docs/BLUEPRINT.md dated amendment bullet (RUNS): resumed_cells / retrained_shuffled_rows per payload
RESUME_PLAN = {"fullfree_coarse_s1.json": (30, 6), "fullfree_coarse_s1_r.json": (0, 0),
               "fullfree_coarse_s3.json": (69, 6), "fullfree_coarse_s3_r.json": (69, 6)}
# the labels read on 2026-09-14 through the amended --conclude-from (F-25); a changed payload flags here
LANDED_LABELS = {"L2_concept_k512": "ABSORBED", "L3_concept_groups_v1": "NOT-SHOWN",
                 "L2_olmoe_k512": "ABSORBED", "L3_olmoe_groups_v1": "SPLIT"}


@pytest.mark.parametrize("pair", [("fullfree_coarse_s1.json", "fullfree_coarse_s1_r.json"),
                                  ("fullfree_coarse_s3.json", "fullfree_coarse_s3_r.json")])
def test_committed_amended_payloads_reproduce_their_conclusion(pair):
    paths = [ROOT / "results" / "real" / n for n in pair]
    if not all(p.exists() for p in paths):
        pytest.skip("amended OQ-18 payloads not present")
    pp, rp = (json.loads(p.read_text(encoding="utf-8")) for p in paths)
    n_cells = 60 if "s1" in pair[0] else 69
    for name, d in zip(pair, (pp, rp)):
        assert am.AMENDED_MARK in d["registered"]
        assert d["partial"] is False and d["n_cells"] == n_cells
        assert (d["resumed_cells"], d["amendment"]["retrained_shuffled_rows"]) == RESUME_PLAN[name]
        prov = d["provenance"]
        assert prov["git_status_licensed"] is True
        assert not am.unlicensed_lines(list(prov["git_status_tracked"]))
        assert prov["licensed_dirty_lines"] == list(am.LICENSED_DIRTY)
        assert prov["instrument_sha256"] == prov["amended_instrument_sha256"]
        assert prov["frozen_instrument_sha256"] == am.FROZEN_INSTRUMENT_SHA256
        assert prov["arm_dims_total"]["fplus_b"] == prov["arm_dims_total"]["fplus_r"]
        assert d["twin"]["arm"] == fz.TWIN_ARM and d["twin"]["seed_base"] == fz.TWIN_SEED_BASE
        assert d["standardization"]["moments_sha_matches_committed_oq17"] is True
        assert d["amendment"]["diagnostic"]["mechanism"] == "TWIN-MATCHED"
        assert prov["git_commit"].startswith("3ec1064") and prov["git_commit"].endswith("-dirty")
        assert prov["diagnostic_payload_sha256"] == am._sha(ROOT / "results" / "real" / "oq18_rider_diag_s1.json")
        for sp, ps in d["per_space"].items():
            r = ps["rider"]
            assert r["pass"] and r["leg1_pass"] and r["leg2_pass"] and r["amended"] == am.AMENDED_MARK
            a = r["amended_leg2"]
            assert a["d_E"] == pytest.approx(r["E"]["fplus_b"] - r["E"]["fplus_r"])
            assert a["fails"] == ((a["d_E"] > r["band"]) or (a["ci95_d_E"][0] > 0 and a["d_E"] >= r["material"]))
            assert a["fails"] is False
            raw = r["registered_leg2_raw"]
            assert raw["excess"] == pytest.approx(r["shuffled_fplus_b"] - r["shuffled_fplus"])
            assert raw["pass"] == (raw["excess"] <= r["band"])
            assert ps["gate"]["fires"] == (ps["reader_valid"]["ok"] and fz.gate_fires(ps["gate"]["row"]))
            assert all(m["n_clusters"] == 30 and m["n_seeds"] == 3 for m in ps["d_fplus_b_vs_fplus_r"])
            assert ps["reader_valid"]["n_gate_probes"] == 12
        for g in d["twin"]["geometry"].values():
            assert all(gg["corrected_twin_same_prompt_frac"] == 0.0 for gg in g.values())
        v1 = d["amendment"]["rider_v1_preserved"]
        if "s3" in name:
            # the payload records the writing box's absolute path (backslashes); PureWindowsPath takes the last
            # component under either separator on every OS, where POSIX Path().name would keep the whole string
            v1_path = ROOT / "results" / "real" / PureWindowsPath(v1["path"]).name
            assert v1_path.name == name.replace(".json", ".rider_v1.json") and v1_path.exists()
            assert am._sha(v1_path) == v1["sha256"]
            v1p = json.loads(v1_path.read_text(encoding="utf-8"))
            assert am.AMENDED_MARK not in v1p["registered"] and "amendment" not in v1p
            assert v1p["provenance"]["instrument_sha256"] == am.FROZEN_INSTRUMENT_SHA256 == v1["frozen_instrument_sha256"]
            assert v1p["provenance"]["git_commit"].startswith("15c4e9c")
        else:
            assert v1 is None
    # the registered raw leg is above its band at exactly S1 L3 (the fire) and S1_r L2 (a fresh cell)
    above = sorted((n, sp) for n, d in zip(pair, (pp, rp)) for sp, ps in d["per_space"].items()
                   if not ps["rider"]["registered_leg2_raw"]["pass"])
    if "s1" in pair[0]:
        assert above == [("fullfree_coarse_s1.json", "L3_concept_groups_v1"), ("fullfree_coarse_s1_r.json", "L2_concept_k512")]
    else:
        assert above == []
    if "s1" in pair[0]:
        # the tracked S1 state file begins with the fired run's record, byte-identical to the sha the
        # diagnostic recorded (header + 36 rows); the amended resume only appended
        diag = json.loads((ROOT / "results" / "real" / "oq18_rider_diag_s1.json").read_text(encoding="utf-8"))
        state = (ROOT / "results" / "real" / "fullfree_coarse_s1.json.state.jsonl").read_bytes()
        head = b"".join(state.splitlines(keepends=True)[:37])
        assert hashlib.sha256(head).hexdigest() == diag["fired_rider"]["state_sha256"]
        assert len(state.splitlines()) == 37 + 8 + 30
    out = am.conclude_amended(pp, rp)
    assert out["amendment"]["disclosure"].startswith("read under the 2026-09-07 rider amendment")
    assert "twin-referenced" in out["rule"] and am.AMENDED_MARK in out["rule"]
    for sp, o in out["spaces"].items():
        assert o["label"] == LANDED_LABELS[sp]
        assert o["gate_fires"] == {"primary": pp["per_space"][sp]["gate"]["fires"],
                                   "replication": rp["per_space"][sp]["gate"]["fires"]}
        assert o["rider_amended"] == {"primary": pp["per_space"][sp]["rider"], "replication": rp["per_space"][sp]["rider"]}
    # the frozen instrument's own --conclude-from is never applied to these payloads (its label would lack the
    # disclosure); the amended conclude refuses the preserved v1 payloads
    if "s3" in pair[0]:
        v1p = json.loads((ROOT / "results" / "real" / "fullfree_coarse_s3.rider_v1.json").read_text(encoding="utf-8"))
        with pytest.raises(SystemExit):
            am.conclude_amended(v1p, rp)
