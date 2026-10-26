"""tests/test_prefetch_horizon.py — the horizon read at the R2 encoding (tools/run_prefetch_horizon.py;
the 2026-10-04 amendment to the R2 block of docs/BLUEPRINT.md): the frozen chain is asserted; at horizon 1
the tool IS R2 (its rows reproduce a fixture R2 run summed to the two unions, its identity cells equal
R2's); the horizon positions are the bigram positions with t + j inside the row; planted rules read the
stage labels they should (a shift rule survives at every horizon, a hidden carrier of the routing absorbs
it, a token rule decays to the floor beyond horizon 1); the labels are mechanical, incl. the straddle and
guard rules; the under-results guards, the R2 reference, the exact recompute and its refusals; nothing
imports torch. CPU fixtures only (the R2 test file's, with a 16-token vocabulary and 1024-wide hidden)."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))
import run_prefetch_readouts as pr  # noqa: E402  (the frozen stage-1 instrument)
import run_prefetch_bigram as rb  # noqa: E402  (the frozen twin)
import run_prefetch_strat as rs  # noqa: E402  (the frozen stratified read)
import run_prefetch_r2 as r2  # noqa: E402  (the frozen generalising free baseline)
import run_prefetch_horizon as hz  # noqa: E402
import test_prefetch_strat as tps  # noqa: E402  (its fixtures)
import test_prefetch_r2 as tpr  # noqa: E402  (its fixtures)
from sideband.probes import load_label_space  # noqa: E402

E, L, K, D = pr.N_EXPERTS, pr.N_GATES, pr.TOP_K, pr.D_MH
FAST = "1,100"
SHORT_K = "0,8,inf"
H123 = "1,2,3"
INF = float("inf")


def _args(d, b, g, out, src, **kw):
    base = dict(harvest=str(d), out=str(out), buckets=str(b), glue=str(g), r2="none", replay=str(src),
                only_seeds=None, smoke_split_val=False, lambdas=FAST, k_grid=SHORT_K, horizons=None, conclude_from=None)
    base.update(kw)
    return argparse.Namespace(**base)


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _hidden_of_slots(d: Path, seed: int = 0) -> None:
    """hidden[t] = multi-hot(S[t]) @ B (B a random 1024 x 1024 map): a linear carrier of the forward's own
    routing, so whatever S[t] predicts linearly, H(t) predicts too."""
    rng = np.random.default_rng(seed)
    B = rng.standard_normal((D, D))

    def fn(z):
        s = z["slots"].astype(np.int64)
        R, T = s.shape[:2]
        mh = np.zeros((R, T, L, E))
        idx = np.where(s >= 0)                                   # positions beyond a row's length hold -1
        mh[idx[0], idx[1], idx[2], s[idx]] = 1.0
        z["hidden"] = (mh.reshape(R, T, D) @ B).astype(np.float16)
    tps._rewrite(d, fn)


def _hidden_zero(d: Path) -> None:
    """hidden = 0 everywhere: an inert block (zero train variance, so H(t) = 0 and the H arms equal their partners)."""
    def fn(z):
        R, T = z["tokens"].shape
        z["hidden"] = np.zeros((R, T, D), dtype=np.float16)
    tps._rewrite(d, fn)


def _chain(tmp_path, src, rule="token", R=24, T=16, seed=5, lambdas=FAST, hidden="random", k_grid=SHORT_K, horizons=None):
    """twin -> stratified -> R2 -> horizon on an unseen-key fixture; hidden 'random' (tpr's), 'rule' (tpr's
    hidden rule), 'slots' (a linear carrier of S[t]) or 'zero' (inert); returns (d, b, g, r2_out, out, payload)."""
    d, b, g = tps._unseen_harvest(tmp_path, rule=rule, R=R, T=T, seed=seed)
    if hidden == "slots":
        tpr._add_hidden(d, seed=seed, rule=False)
        _hidden_of_slots(d, seed=seed)
    elif hidden == "zero":
        _hidden_zero(d)
    else:
        tpr._add_hidden(d, seed=seed, rule=(hidden == "rule"))
    src = tpr._replay_source(src, rule=False)
    twin_out = tmp_path / "twin.json"
    rb.run(tps._twin_args(d, b, g, twin_out, lambdas=lambdas))
    strat_out = tmp_path / "strat.json"
    rs.run(tps._args(d, b, g, strat_out, lambdas=lambdas, twin=str(twin_out)))
    r2_out = tmp_path / "r2.json"
    r2.run(tpr._args(d, b, g, r2_out, src, strat=str(strat_out), lambdas=lambdas, k_grid=k_grid))
    out = tmp_path / "horizon.json"
    payload = hz.run(_args(d, b, g, out, src, r2=str(r2_out), lambdas=lambdas, k_grid=k_grid, horizons=horizons))
    return d, b, g, r2_out, out, payload


def _point(c, arm, B, j, scope="all"):
    return c["tables"][f"{arm}|B={B}|j={j}|{scope}"]["all"]["point"]


# ---------------------------------------------------------------------------
# the frozen chain; the positions
# ---------------------------------------------------------------------------

def test_frozen_chain_is_asserted(tmp_path):
    assert hz.assert_frozen_r2() == hz.R2_INSTRUMENT_SHA256
    assert hz.r2.assert_frozen_strat() == r2.STRAT_INSTRUMENT_SHA256
    assert hz.rs.assert_frozen_twin() == rs.TWIN_INSTRUMENT_SHA256
    assert hz.rb.assert_frozen_instrument() == rb.FROZEN_INSTRUMENT_SHA256
    tampered = tmp_path / "run_prefetch_r2.py"
    tampered.write_bytes(Path(r2.__file__).read_bytes() + b"\n# touched\n")
    with pytest.raises(SystemExit, match="refusing"):
        hz.assert_frozen_r2(tampered)
    crlf = tmp_path / "crlf.py"
    crlf.write_bytes(Path(r2.__file__).read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
    assert hz.assert_frozen_r2(crlf) == hz.R2_INSTRUMENT_SHA256


def test_horizon_positions_are_the_bigram_positions_with_the_target_inside_the_row():
    rng = np.random.default_rng(3)
    T = 12
    lengths = rng.integers(2, T + 1, size=40).astype(np.int64)
    r1, a1 = hz.horizon_positions(lengths, 1, T)
    rb1, ab1 = rb.bigram_positions(lengths, T)
    assert np.array_equal(r1, rb1) and np.array_equal(a1, ab1)
    prev = set(zip(r1.tolist(), a1.tolist()))
    for j in (2, 3, 4):
        r, a = hz.horizon_positions(lengths, j, T)
        assert np.all(a >= 1) and np.all(a + j < lengths[r])
        cur = set(zip(r.tolist(), a.tolist()))
        assert cur <= prev and len(cur) < len(prev)
        # every qualifying anchor is present
        want = {(int(rr), int(t)) for rr in range(40) for t in range(1, T) if t + j < lengths[rr]}
        assert cur == want
        prev = cur


def test_horizon_tables_are_the_frozen_construction_with_the_target_moved(tmp_path):
    d, b, g = tps._unseen_harvest(tmp_path, rule="token", R=21, T=14, seed=2)
    tpr._add_hidden(d, seed=2)
    src = r2.load_replay_source(str(tpr._replay_source(tmp_path / "src.npz", rule=False)))
    data = pr.S3Data(d)
    lab, nc = load_label_space(b, g)
    h = hz.Horizon(data, lab, nc, r2.load_hidden(data), r2.replay_table(src, int(data.tokens.max()) + 1), lambdas=(1.0,), k_grid=(0.0, INF))
    h.fit_base()
    # at horizon 1 the moved-target construction IS the frozen one, array for array
    t1 = h.fit_tables_h(1)
    for name in h.TABLE_FIELDS:
        assert np.array_equal(t1[name], h.tables[1][name]), name
    # at horizon 2: counts of S[t+2]; 8 counts per gate per train position; keys a subset of horizon 1's
    t2 = h.fit_tables_h(2)
    rows, anchors = pr.restrict(*pr.positions_horizon(data.lengths, 2, data.T), h.masks["train"])
    assert t2["token_table"].sum() == rows.shape[0] * L * K < h.tables[1]["token_table"].sum()
    assert set(np.flatnonzero(t2["token_table"].sum(axis=(1, 2)))) <= set(np.flatnonzero(h.tables[1]["token_table"].sum(axis=(1, 2))))
    r_, a_ = rows[:5], anchors[:5]
    for i in range(5):
        tok = int(data.tokens[r_[i], a_[i]])
        for l in range(L):
            for e in data.slots[r_[i], a_[i] + 2, l]:
                assert t2["token_table"][tok, l, int(e)] >= 1
    assert np.allclose(t2["marginal_freq"].sum(axis=1), 1.0)
    rows_p, anchors_p = pr.restrict(*hz.horizon_positions(data.lengths, 2, data.T), h.masks["train"])
    assert t2["prev_table"].sum() == rows_p.shape[0] * L * K
    # an exact brute-force recount of TABLE_CUR^2 and TABLE_PREV^2 over the train positions
    brute_cur = np.zeros((h.vocab, L, E), dtype=np.int64)
    for r_i, a_i in zip(rows.tolist(), anchors.tolist()):
        for l in range(L):
            brute_cur[int(data.tokens[r_i, a_i]), l, data.slots[r_i, a_i + 2, l].astype(np.int64)] += 1
    assert np.array_equal(brute_cur, t2["token_table"])
    brute_prev = np.zeros((h.vocab, L, E), dtype=np.int64)
    for r_i, a_i in zip(rows_p.tolist(), anchors_p.tolist()):
        for l in range(L):
            brute_prev[int(data.tokens[r_i, a_i - 1]), l, data.slots[r_i, a_i + 2, l].astype(np.int64)] += 1
    assert np.array_equal(brute_prev, t2["prev_table"])
    # leave-one-prompt-out at a horizon-2 train row: the row's own prompt's contributions under the key are removed
    h.tables[2] = t2
    h.use_tables(2)
    for r_i, a_i in zip(rows[:4].tolist(), anchors[:4].tolist()):
        tok, pid = int(data.tokens[r_i, a_i]), int(data.prompt_idx[r_i])
        keep = np.array([(int(data.tokens[rr, aa]) == tok) and (int(data.prompt_idx[rr]) != pid) for rr, aa in zip(rows.tolist(), anchors.tolist())])
        cnt = np.zeros((L, E))
        for rr, aa in zip(rows[keep].tolist(), anchors[keep].tolist()):
            for l in range(L):
                cnt[l, data.slots[rr, aa + 2, l].astype(np.int64)] += 1
        tot = cnt.sum(axis=1, keepdims=True)
        want = np.where(tot > 0, cnt / np.maximum(tot, 1.0), t2["marginal_freq"]).reshape(D)
        got = h.table_vec(np.array([tok]), np.array([pid]))[0]
        assert np.allclose(got, want), (r_i, a_i)
    h.use_tables(1)
    for i in range(5):                                        # keyed on the PREVIOUS token, target two forwards on
        tokp = int(data.tokens[rows_p[i], anchors_p[i] - 1])
        for l in range(L):
            for e in data.slots[rows_p[i], anchors_p[i] + 2, l]:
                assert t2["prev_table"][tokp, l, int(e)] >= 1
    # use_tables swaps every attribute the twin's readers, the smoothed blocks and the strata read
    h.use_tables(2)
    for name in h.TABLE_FIELDS:
        assert getattr(h, name) is t2[name], name
    h.use_tables(1)
    for name in h.TABLE_FIELDS:
        assert getattr(h, name) is h.tables[1][name], name


# ---------------------------------------------------------------------------
# at horizon 1 the tool is R2: REPRODUCE EXACT, the identity, the re-selection; the exact recompute
# ---------------------------------------------------------------------------

def test_j1_reproduces_r2_and_the_identity_holds_and_conclude_from(tmp_path):
    d, b, g, r2_out, out, payload = _chain(tmp_path, tmp_path / "src.npz", rule="token", seed=5)
    rp = json.loads(r2_out.read_text(encoding="utf-8"))
    prov, lab, c = payload["provenance"], payload["conclusion"]["labels"], payload["conclusion"]
    assert prov["encoding_source"] == "r2" and prov["encoding_selected"] == rp["provenance"]["encoding_selected"]
    assert prov["constants"]["horizons"] == [1, 2, 3, 4] and lab["label_horizons"] == [2, 3, 4]
    sel1 = prov["selection"]["1"]
    assert sel1["k_selected"] == rp["provenance"]["k_selected"]
    for arm in r2.ARMS_TWIN + r2.ARMS_R2:
        assert sel1["lambda_selected"][arm] == rp["provenance"]["lambda_selected"][arm], arm
        assert sel1["lambda_source"][arm] == ("r2" if arm != "replay_zerofit" else None) and sel1["lambda_grid_edge"][arm] is None
    assert sel1["lambda_source"]["marginal"] == "val" and isinstance(sel1["lambda_grid_edge"]["marginal"], bool)
    assert set(sel1["arms"]) == set(hz.ARMS_J1) and len(hz.ARMS_J1) == 20
    # the same val data under the same rule re-selects what R2 selected
    re = sel1["reselect"]
    assert re["matches_r2"] is True and re["k"] == rp["provenance"]["k_selected"]
    for arm in hz.RESELECT_ARMS:
        assert re["lambda"][arm] == rp["provenance"]["lambda_selected"][arm], arm
    # the R2 record
    assert prov["r2"]["sha256"] == _sha(r2_out) and prov["r2"]["state_sha256"] == _sha(Path(str(r2_out) + ".state.jsonl"))
    assert "_rows" not in prov["r2"] and prov["r2"]["strat_path"] == rp["provenance"]["strat"]["path"]
    assert set(prov["r2"]["cells"]) == set(hz.IDENTITY_CELLS.values())
    # REPRODUCE EXACT against the R2 rows summed to the two unions; the identity on the four cells
    rep = lab["reproduce"]
    assert rep["status"] == "EXACT" and rep["ok"] is True and lab["reproduce_status"] == "EXACT" and lab["void"] is False
    r2_rows = pr.load_state(Path(str(r2_out) + ".state.jsonl"))[1]
    assert rep["n_compared"] == rep["n_r2_union_rows"] == len(hz._index_r2(r2_rows))
    assert rep["missing_here"] == rep["extra_here"] == rep["needed_mismatch_rows"] == rep["hits_mismatch_rows"] == 0
    assert lab["identity_matches_r2"] is True
    for mine, theirs in hz.IDENTITY_CELLS.items():
        assert c["deltas"][f"{mine}|B=16|j=1|all"] == rp["conclusion"]["deltas"][f"{theirs}|B=16|all"]
    # every R2 arm's horizon-1 table equals R2's pooled table (the unions sum to R2's strata)
    for arm in r2.ARMS_REQUIRED:
        for B in (8, 16, 32):
            assert c["tables"][f"{arm}|B={B}|j=1|all"]["all"] == rp["conclusion"]["tables"][f"{arm}|B={B}|all"]["all"], (arm, B)
    # horizons 2..4 carry the twelve arms with val-selected lambdas and their own k
    for j in ("2", "3", "4"):
        sj = prov["selection"][j]
        assert sj["arms"] == list(hz.arms_h(prov["encoding_selected"])) and sj["reselect"] is None
        assert all(sj["lambda_source"][a] == "val" for a in sj["arms"])
        assert set(sj["k_val_table"]) == {"0", "8", "inf"} and sj["val_table"]["free_r2"] == sj["k_val_table"][sj["k_selected"]]
        assert all(isinstance(sj["lambda_grid_edge"][a], bool) for a in sj["arms"])
    assert lab["k_of_horizon"] == {j: prov["selection"][j]["k_selected"] for j in ("1", "2", "3", "4")}
    # the state rows: scopes are the two unions only, every horizon, only test prompts, the header's record
    header, rows = pr.load_state(Path(str(out) + ".state.jsonl"))
    assert {r["scope"] for r in rows} <= set(hz.STATE_SCOPES) and {int(r["key"]) for r in rows} == {1, 2, 3, 4}
    assert {r["arm"] for r in rows if r["key"] == 1} == set(hz.ARMS_J1)
    assert {r["arm"] for r in rows if r["key"] == 3} == set(hz.arms_h(prov["encoding_selected"]))
    assert header["k_of_horizon"] == lab["k_of_horizon"] and header["r2"] == prov["r2"] and header["horizons"] == [1, 2, 3, 4]
    assert header["replay_source_sha256"] == prov["replay_source"]["sha256"]
    assert all(r["needed"] > 0 for r in rows) and len(rows) == payload["n_state_rows"]
    assert prov["frozen_r2"]["sha256_lf"] == hz.R2_INSTRUMENT_SHA256 and prov["frozen_strat"]["sha256_lf"] == r2.STRAT_INSTRUMENT_SHA256
    assert prov["n_positions"]["horizon1/bigram/train"] > prov["n_positions"]["horizon4/bigram/train"] > 0
    assert set(prov["elapsed_per_horizon_s"]) == {"1", "2", "3", "4"}
    # exact recompute incl. REPRODUCE re-derived from the R2 files on disk
    got = hz.conclude_from(out)
    assert got["labels"]["label"] == lab["label"] and got["labels"]["reproduce"]["status"] == "EXACT"
    for p in (out, Path(str(out) + ".state.jsonl"), tmp_path / "horizon.meta.json"):
        assert b"\r\n" not in p.read_bytes()


def test_horizon_one_takes_the_reference_selections_not_vals(tmp_path):
    """A doctored R2 reference (one arm's lambda moved off val's choice) must drive that arm's horizon-1 rows and
    flip the RESELECT flag, while the other arms' rows stay: the selections are TAKEN, not re-selected."""
    d, b, g, r2_out, out, payload = _chain(tmp_path, tmp_path / "src.npz", rule="token", R=21, T=14, seed=8, horizons="1,2")
    ref = hz.read_r2(r2_out)
    src = r2.load_replay_source(str(tmp_path / "src.npz"))
    data = pr.S3Data(d)
    lab, nc = load_label_space(b, g)
    hidden, replay = r2.load_hidden(data), r2.replay_table(src, int(data.tokens.max()) + 1)
    cur = float(ref["lambda_selected"]["h_only"])
    moved = 100.0 if cur != 100.0 else 1.0
    doctored = dict(ref, lambda_selected=dict(ref["lambda_selected"], h_only=moved))
    kw = dict(horizons=(1,), lambdas=(1.0, 100.0), k_grid=(0.0, 8.0, INF))
    ht = hz.Horizon(data, lab, nc, hidden, replay, r2ref=ref, **kw); ht.fit_base(); rt = ht.run_horizon(1)
    hd = hz.Horizon(data, lab, nc, hidden, replay, r2ref=doctored, **kw); hd.fit_base(); rd = hd.run_horizon(1)
    assert ht.sel[1]["reselect"]["matches_r2"] is True and hd.sel[1]["reselect"]["matches_r2"] is False
    assert ht.sel[1]["lambda_selected"]["h_only"] == cur and hd.sel[1]["lambda_selected"]["h_only"] == moved
    assert ht.sel[1]["reselect"]["lambda"] == hd.sel[1]["reselect"]["lambda"]          # val's re-selection is the same either way
    assert ht.sel[1]["lambda_source"]["h_only"] == "r2" and hd.sel[1]["lambda_grid_edge"]["h_only"] is None
    key = lambda r: (r["arm"], r["budget"], r["scope"], r["gate"], r["prompt_idx"])  # noqa: E731
    t_h = {key(r): (r["hits"], r["needed"]) for r in rt if r["arm"] == "h_only"}
    d_h = {key(r): (r["hits"], r["needed"]) for r in rd if r["arm"] == "h_only"}
    assert t_h.keys() == d_h.keys() and t_h != d_h                                       # the moved lambda moves h_only's rows
    for arm in ("history_tok", "free_r2", "free_h", "history_all_h", "marginal"):
        assert [(key(r), r["hits"]) for r in rt if r["arm"] == arm] == [(key(r), r["hits"]) for r in rd if r["arm"] == arm], arm


def test_no_r2_path_reselects_what_r2_carried(tmp_path):
    d, b, g, r2_out, out, payload = _chain(tmp_path, tmp_path / "src.npz", rule="token", R=21, T=14, seed=8, horizons=H123)
    p2 = hz.run(_args(d, b, g, tmp_path / "horizon_nor2.json", tmp_path / "src.npz", r2="none", horizons=H123))
    prov, prov2 = payload["provenance"], p2["provenance"]
    assert prov2["encoding_source"] == "val" and prov2["r2"] is None and prov2["encoding_selected"] == prov["encoding_selected"]
    s1, s2 = prov["selection"]["1"], prov2["selection"]["1"]
    assert s2["k_selected"] == s1["k_selected"] and s2["reselect"] is None
    for arm in hz.ARMS_J1:
        assert s2["lambda_selected"][arm] == s1["lambda_selected"][arm], arm
        assert s2["lambda_source"][arm] == ("val" if arm != "replay_zerofit" else None)
    lab2 = p2["conclusion"]["labels"]
    assert lab2["reproduce"] is None and lab2["reproduce_ok"] is None and lab2["identity_matches_r2"] is None
    assert p2["conclusion"]["deltas"] == payload["conclusion"]["deltas"]
    assert lab2["label"] == payload["conclusion"]["labels"]["label"]
    hz.conclude_from(tmp_path / "horizon_nor2.json")


# ---------------------------------------------------------------------------
# planted rules read the stage labels they should
# ---------------------------------------------------------------------------

def test_shift_rule_with_an_inert_hidden_block_reads_lead_time_survives_and_conclude_writes_the_claim(tmp_path):
    d, b, g, r2_out, out, payload = _chain(tmp_path, tmp_path / "src.npz", rule="shift", seed=9, hidden="zero", horizons=H123)
    c, lab, prov = payload["conclusion"], payload["conclusion"]["labels"], payload["provenance"]
    assert lab["reproduce_status"] == "EXACT" and lab["identity_matches_r2"] is True
    assert prov["hidden"]["kept_variance_share"] is None                           # zero train variance: H(t) = 0
    for j in (1, 2, 3):
        assert _point(c, "history_bigram_r2", 16, j) > 0.95 and _point(c, "history_all_h", 16, j) > 0.95
        assert _point(c, "free_h", 16, j) < 0.6 and _point(c, "free_r2", 16, j) < 0.6
        assert _point(c, "free_h", 16, j) == _point(c, "free_r2", 16, j)        # an inert H adds nothing to its partner
    for j in ("2", "3"):
        hj = lab["horizons"][j]
        assert hj["q"] == "H-SURVIVES" and hj["d_eq_h_reading"] == "SIGNAL" and hj["d_add_h_reading"] == "SIGNAL"
        assert hj["reader_guard"] is False and hj["negative"] is False and hj["floor_straddle"] is False
    assert lab["stage"] == "LEAD-TIME-SURVIVES" and lab["first_horizon"] == 2 and lab["label"] == "LEAD-TIME-SURVIVES@2"
    assert lab["straddle_horizons"] == [] and lab["guard_horizons"] == []          # points above 0.95: the straddle branch cannot fire
    # under the test grid's TWO lambdas every selected lambda is a grid end, so run() withholds the claim by the FREE-ARM
    # EDGE RULE and says why; the claim text itself is checked through conclude() on the same rows with the edge flags cleared
    assert lab["free_h_edge_horizons"] == [2, 3] and lab["said_in_words"]["free_h_edge_horizons"] == [2, 3]
    assert lab["sentence"].startswith("the stage label reads LEAD-TIME-SURVIVES@2 by the rule while free_h's lambda sits at the grid's edge at horizon 2")
    assert lab["sentence"].endswith("no closing claim is written")
    ref = hz.read_r2(r2_out)
    rows = pr.load_state(Path(str(out) + ".state.jsonl"))[1]
    clean = hz.conclude(rows, lab["encoding"], lab["k_of_horizon"], ref["_rows"], ref["cells"], horizons=(1, 2, 3), free_h_edge={})["labels"]
    assert clean["label"] == "LEAD-TIME-SURVIVES@2" and clean["free_h_edge_horizons"] == [] and clean["reproduce_status"] == "EXACT"
    assert clean["sentence"] == hz.SENTENCE_STAGE["LEAD-TIME-SURVIVES"].replace("{J}", "2")     # no trailer: nothing to say beside it
    assert "stays struck and this cell does not reinstate it" in clean["sentence"]
    assert clean["horizons"]["3"]["sentence"].endswith("(the stage sentence governs; the motivation struck at horizon 1 stays struck)")
    assert lab["trend"]["d_add_h"]["1"]["delta"] > 0.3 and lab["trend"]["d_add_h"]["3"]["delta"] > 0.3
    got = hz.conclude_from(out)
    assert got["labels"]["label"] == lab["label"] and got["labels"]["sentence"] == lab["sentence"]


def test_shift_rule_with_a_noise_hidden_block_trips_the_guard_and_withholds_the_claim(tmp_path):
    """A 1024-wide noise block at a tiny train size degrades the free arm and the union (the smoke's shape): the
    per-horizon label stays H-SURVIVES by the rule, the guard fires, and the stage's closing claim is withheld."""
    d, b, g, r2_out, out, payload = _chain(tmp_path, tmp_path / "src.npz", rule="shift", seed=9, hidden="random", horizons=H123)
    c, lab = payload["conclusion"], payload["conclusion"]["labels"]
    assert lab["reproduce_status"] == "EXACT"
    for j in (2, 3):
        assert _point(c, "history_bigram_r2", 16, j) > 0.95 and _point(c, "free_r2", 16, j) < 0.6
        hj = lab["horizons"][str(j)]
        assert hj["q"] == "H-SURVIVES" and hj["d_eq_h_reading"] == "SIGNAL" and hj["d_add_h_reading"] == "SIGNAL"
        assert hj["reader_guard"] is True and (hj["free_h_gain"]["hi"] < 0 or hj["anchor"]["hi"] < 0)
        assert hj["sentence"].startswith("with the forward's final-norm state at the address block's width in the free arm, at horizon")
        assert "reads NEGATIVE" in hj["sentence"] or "read NEGATIVE" in hj["sentence"]
    assert lab["label"] == "LEAD-TIME-SURVIVES@2" and lab["guard_horizons"] == [2, 3]
    assert lab["sentence"].startswith("the stage label reads LEAD-TIME-SURVIVES@2 by the rule while the reader guard fired at horizon 2")
    assert lab["sentence"].endswith("no closing claim is written")
    assert hz.conclude_from(out)["labels"]["sentence"] == lab["sentence"]


def test_hidden_carrier_of_the_routing_reads_lead_time_absorbed(tmp_path):
    d, b, g, r2_out, out, payload = _chain(tmp_path, tmp_path / "src.npz", rule="shift", seed=11, hidden="slots", horizons=H123)
    c, lab = payload["conclusion"], payload["conclusion"]["labels"]
    assert lab["reproduce_status"] == "EXACT"
    for j in (1, 2, 3):
        assert _point(c, "h_only", 16, j) > 0.95 and _point(c, "free_h", 16, j) > 0.95
        assert _point(c, "history_bigram_r2", 16, j) > 0.95 and _point(c, "history_all_h", 16, j) > 0.95
    for j in ("2", "3"):
        hj = lab["horizons"][j]
        assert hj["q"] == "H-ABSORBS" and hj["d_eq_h_reading"] != "SIGNAL" and hj["d_add_h_reading"] != "SIGNAL"
        assert abs(hj["d_eq_h"]["delta"]) < 0.05 and abs(hj["d_add_h"]["delta"]) < 0.05
        assert hj["reader_guard"] is False                              # free_h - free_r2 is large and positive
    assert lab["stage"] == "LEAD-TIME-ABSORBED" and lab["first_horizon"] is None and lab["label"] == "LEAD-TIME-ABSORBED"
    assert lab["straddle_horizons"] == [] and "not shown to add a material hit-rate margin over free information" in lab["sentence"]
    assert "PREFETCH-HEADROOM (which does not depend on this margin) stands" in lab["sentence"]
    assert lab["said_in_words"]["h_only_above_history_tok"]["2"] in (True, False)


def test_token_rule_decays_to_the_floor_beyond_horizon_one(tmp_path):
    d, b, g, r2_out, out, payload = _chain(tmp_path, tmp_path / "src.npz", rule="token", seed=6, horizons=H123)
    c, lab = payload["conclusion"], payload["conclusion"]["labels"]
    # horizon 1: the token rule is read by the table arms where the key is covered (the R2 fixture's shape)
    assert _point(c, "free_tok", 16, 1, "covered") > 0.9 and _point(c, "history_tok", 16, 1, "covered") > 0.9
    # horizons 2 and 3: S[t+j] is a function of tokens[t+j-1], unknown at t — every arm sits at the floor
    for j in (2, 3):
        floor = _point(c, "marginal", 16, j)
        for arm in hz.arms_h(lab["encoding"]):
            assert abs(_point(c, arm, 16, j) - floor) < 0.12, (arm, j)
        for arm in ("history_tok", "free_h", "history_all_h"):
            assert c["deltas"][f"{arm}-marginal|B=16|j={j}|all"]["delta"] < 0.12
    for j in ("2", "3"):
        assert lab["horizons"][j]["q"] == "H-ABSORBS"
    assert lab["stage"] == "LEAD-TIME-ABSORBED"
    assert set(lab["trend"]["abt"]) == {"1", "2", "3"} and lab["label_horizons"] == [2, 3]


# ---------------------------------------------------------------------------
# REPRODUCE is the pinned rule
# ---------------------------------------------------------------------------

def test_reproduce_check_is_the_pinned_rule():
    strata_of = {u: parts for u, parts in hz.UNIONS.items()}
    assert set(strata_of) == {"covered", "fallback"} and set(rs.UNIONS) >= set(strata_of)
    r2_rows = [{"arm": a, "budget": 16, "key": 1, "depth": None, "gate": g, "prompt_idx": p, "stratum": s, "hits": 10, "needed": 20}
               for a in ("history_tok", "free_tok") for g in range(L) for p in range(40) for u in strata_of for s in strata_of[u]]
    mine = [{"arm": a, "budget": 16, "key": 1, "depth": None, "gate": g, "prompt_idx": p, "scope": u,
             "hits": 10 * len(strata_of[u]), "needed": 20 * len(strata_of[u])}
            for a in ("history_tok", "free_tok") for g in range(L) for p in range(40) for u in strata_of]
    rep = hz.reproduce_check(mine, r2_rows)
    assert rep["status"] == "EXACT" and rep["ok"] and rep["n_r2_union_rows"] == 2 * L * 40 * 2 == rep["n_compared"]
    # 2,560 union rows: one +-1 hit mismatch is NEAR (cap 2), three are INVALID, a +-2 gap is INVALID, a needed mismatch is INVALID
    b1 = [dict(r) for r in mine]; b1[0]["hits"] += 1
    rep = hz.reproduce_check(b1, r2_rows)
    assert rep["status"] == "NEAR" and rep["ok"] is True and rep["hits_mismatch_rows"] == 1 and rep["max_abs_hits_gap"] == 1
    b2 = [dict(r) for r in mine]
    for i in range(3):
        b2[i]["hits"] += 1
    assert hz.reproduce_check(b2, r2_rows)["status"] == "INVALID"
    b3 = [dict(r) for r in mine]; b3[0]["hits"] += 2
    assert hz.reproduce_check(b3, r2_rows)["status"] == "INVALID"
    b4 = [dict(r) for r in mine]; b4[0]["needed"] += 1
    rep = hz.reproduce_check(b4, r2_rows)
    assert rep["needed_mismatch_rows"] == 1 and rep["status"] == "INVALID"
    # a missing or an extra row is INVALID; rows at other horizons, marginal rows and R2 rows of other arms are ignored
    assert hz.reproduce_check(mine[1:], r2_rows)["missing_here"] == 1 and hz.reproduce_check(mine[1:], r2_rows)["status"] == "INVALID"
    extra = mine + [dict(mine[0], prompt_idx=999)]
    assert hz.reproduce_check(extra, r2_rows)["extra_here"] == 1
    mixed = mine + [dict(r, key=2, hits=1) for r in mine[:10]] + [dict(r, arm="marginal", hits=1) for r in mine[:10]]
    r2_more = r2_rows + [dict(r, arm="pt_only", hits=2) for r in r2_rows[:10]]
    assert hz.reproduce_check(mixed, r2_more)["status"] == "EXACT"
    with pytest.raises(SystemExit, match="outside the six strata"):
        hz._index_r2([dict(r2_rows[0], stratum="elsewhere")])


# ---------------------------------------------------------------------------
# labels are mechanical
# ---------------------------------------------------------------------------

def _rows(rates: dict, per: int = 100, prompts=(0, 1), default: float = 0.80, horizons=(1, 2, 3, 4), encoding="prev_table"):
    """rates: {arm: {j: rate | (rate per prompt) | {scope: rate}}}; one row per (arm, horizon, scope, prompt, gate) at B = 16."""
    rows = []
    for j in horizons:
        arms = hz.ARMS_J1 if j == hz.REPRODUCE_HORIZON else hz.arms_h(encoding)
        for arm in arms:
            spec = rates.get(arm, {}).get(j, default)
            for scope in hz.STATE_SCOPES:
                rate = spec.get(scope, default) if isinstance(spec, dict) else spec
                for i, p in enumerate(prompts):
                    rp = rate[i] if isinstance(rate, (tuple, list)) else rate
                    for g in range(L):
                        rows.append({"arm": arm, "budget": 16, "key": j, "depth": None, "gate": g, "prompt_idx": p,
                                     "scope": scope, "hits": int(round(per * rp)), "needed": per})
    return rows


def _r2_of(rows):
    """R2-shaped rows (six strata) whose union sums are the horizon-1 rows: one stratum row per union."""
    first = {u: parts[0] for u, parts in hz.UNIONS.items()}
    return [{**{k: v for k, v in r.items() if k != "scope"}, "stratum": first[r["scope"]]}
            for r in rows if r["key"] == 1 and r["arm"] in r2.ARMS_REQUIRED]


def _flat(rate, horizons=(1, 2, 3, 4)):
    return {j: rate for j in horizons}


def test_labels_are_mechanical():
    kw = dict(n_boot=200, budgets=(16,))
    KH = {"1": "8", "2": "8", "3": "inf", "4": "0"}
    # A: ABSORBS at 2, SURVIVES at 3 and 4 -> LEAD-TIME-SURVIVES@3; no straddle, no guard
    a = {"history_bigram_r2": {1: 0.81, 2: 0.82, 3: 0.90, 4: 0.90}, "history_all_h": {1: 0.82, 2: 0.83, 3: 0.92, 4: 0.92},
         "free_h": {1: 0.80, 2: 0.80, 3: 0.80, 4: 0.80}, "free_r2": _flat(0.70)}
    rows = _rows(a)
    first = hz.conclude(rows, "prev_table", KH, _r2_of(rows), **kw)
    lab = first["labels"]
    assert lab["reproduce"]["status"] == "EXACT" and lab["reproduce_status"] == "EXACT" and lab["void"] is False
    assert lab["identity_matches_r2"] is None and lab["k_of_horizon"] == KH and lab["label_horizons"] == [2, 3, 4]
    assert lab["horizons"]["2"]["q"] == "H-ABSORBS" and lab["horizons"]["3"]["q"] == "H-SURVIVES" and lab["horizons"]["4"]["q"] == "H-SURVIVES"
    assert lab["stage"] == "LEAD-TIME-SURVIVES" and lab["first_horizon"] == 3 and lab["label"] == "LEAD-TIME-SURVIVES@3"
    assert abs(lab["horizons"]["3"]["d_eq_h"]["delta"] - 0.10) < 1e-9 and abs(lab["horizons"]["3"]["d_add_h"]["delta"] - 0.12) < 1e-9
    assert abs(lab["horizons"]["3"]["anchor"]["delta"] - 0.02) < 1e-9 and lab["horizons"]["3"]["inconsistent_cause"] is None
    assert lab["horizons"]["2"]["d_eq_h_reading"] == "NOT-SHOWN" and lab["horizons"]["2"]["sentence"].startswith("with the forward's final-norm state")
    assert "at horizon 2 no material margin" in lab["horizons"]["2"]["sentence"]
    assert lab["sentence"].startswith("at horizon 3 the address block adds a material margin") and "does not reinstate it" in lab["sentence"]
    assert "under the operator's words authorizing stage 2 in those words" in lab["sentence"]
    assert lab["straddle_horizons"] == [] and lab["guard_horizons"] == [] and lab["said_in_words"]["negative_horizons"] == []
    assert lab["free_h_edge_horizons"] == [] and lab["said_in_words"]["fallback_signal"] == ["d_eq_h|j=3", "d_add_h|j=3", "d_eq_h|j=4", "d_add_h|j=4"]
    assert set(lab["trend"]) == {"d_eq_h", "d_add_h", "anchor", "abt", "gate_eq_r2", "free_h-free_r2", "h_only-history"}
    assert abs(lab["trend"]["d_add_h"]["1"]["delta"] - 0.02) < 1e-9
    assert lab["scopes"]["3"]["all"]["positions"] == 50 and abs(lab["scopes"]["3"]["fallback"]["share"] - 0.5) < 1e-12
    assert first["tables"]["marginal|B=16|j=2|all"]["dims"] == 1 and first["tables"]["history_all_h|B=16|j=4|all"]["dims"] == 4097
    # the identity against the R2 cells: equal -> True; a moved cell -> INVALID, void, numbers kept
    cells = {theirs: first["deltas"][f"{mine}|B=16|j=1|all"] for mine, theirs in hz.IDENTITY_CELLS.items()}
    assert hz.conclude(rows, "prev_table", KH, _r2_of(rows), cells, **kw)["labels"]["identity_matches_r2"] is True
    moved = dict(cells); moved["d_add_h"] = dict(cells["d_add_h"], delta=cells["d_add_h"]["delta"] + 1e-6)
    void = hz.conclude(rows, "prev_table", KH, _r2_of(rows), moved, **kw)
    vl = void["labels"]
    assert vl["label"] == "REPRODUCE-INVALID" and vl["void"] is True and vl["identity_matches_r2"] is False
    for f_ in hz.READING_FIELDS:
        if f_ != "sentence":
            assert vl[f_] is None, f_
    assert vl["sentence"].startswith("this read's horizon-1 rows do not reproduce") and void["deltas"] == first["deltas"]
    # B: ABSORBED at every horizon, every delta CI-positive below the floor, no straddle: the closing sentence
    b = {"history_bigram_r2": _flat(0.82), "history_all_h": _flat(0.83), "free_h": _flat(0.80), "free_r2": _flat(0.70)}
    lab = hz.conclude(_rows(b), "prev_table", KH, None, **kw)["labels"]
    assert lab["label"] == "LEAD-TIME-ABSORBED" and lab["reproduce"] is None and lab["reproduce_ok"] is None
    assert all(lab["horizons"][j]["q"] == "H-ABSORBS" for j in ("2", "3", "4")) and lab["straddle_horizons"] == []
    assert lab["sentence"] == hz.SENTENCE_STAGE["LEAD-TIME-ABSORBED"] and "closes at this reader" in lab["sentence"]
    assert lab["horizons"]["4"]["d_eq_h"]["lo"] > 0 and lab["horizons"]["4"]["d_eq_h_reading"] == "NOT-SHOWN"
    # C: ABSORBED by the rule with a straddle at horizon 4 (per-prompt spread puts the floor inside the CI): no closing sentence
    c_ = dict(b, history_all_h={1: 0.83, 2: 0.83, 3: 0.83, 4: (0.82, 0.86)})
    lab = hz.conclude(_rows(c_), "prev_table", KH, None, **kw)["labels"]
    assert lab["stage"] == "LEAD-TIME-ABSORBED" and lab["horizons"]["4"]["d_add_h_reading"] == "NOT-SHOWN"
    assert lab["horizons"]["4"]["floor_straddle"] is True and lab["straddle_horizons"] == [4]
    assert lab["horizons"]["4"]["sentence"].startswith("with the forward's final-norm state") and "not settled at this power" in lab["horizons"]["4"]["sentence"]
    assert lab["sentence"].startswith("the stage label reads LEAD-TIME-ABSORBED by the rule while a CI95 straddles the +0.05 floor at horizon(s) 4")
    assert lab["sentence"].endswith("no closing claim is written") and "closes at this reader" not in lab["sentence"]
    # D: COMPLEMENTARY at 2 (only the union SIGNAL), ABSORBS after -> LEAD-TIME-COMPLEMENTARY@2
    d_ = dict(b, history_all_h={1: 0.83, 2: 0.90, 3: 0.83, 4: 0.83})
    lab = hz.conclude(_rows(d_), "prev_table", KH, None, **kw)["labels"]
    assert lab["label"] == "LEAD-TIME-COMPLEMENTARY@2" and lab["horizons"]["2"]["q"] == "H-COMPLEMENTARY"
    assert lab["sentence"].startswith("at horizon 2 no material margin") and "for the union reader only" in lab["sentence"]
    # E: only the equal-dims SIGNAL at 3 (the union not) -> INCONSISTENT with cause "reader" (anchor NEGATIVE)
    e_ = dict(b, history_bigram_r2={1: 0.82, 2: 0.82, 3: 0.95, 4: 0.82})
    lab = hz.conclude(_rows(e_), "prev_table", KH, None, **kw)["labels"]
    assert lab["horizons"]["3"]["q"] == "H-INCONSISTENT" and lab["horizons"]["3"]["inconsistent_cause"] == "reader"
    assert lab["horizons"]["3"]["reader_guard"] is True and lab["stage"] == "LEAD-TIME-INCONSISTENT" and lab["label"] == "LEAD-TIME-INCONSISTENT"
    assert lab["guard_horizons"] == [3] and lab["sentence"].endswith("the reader guard fired at horizon(s) 3, where no branch claim is written")
    assert lab["sentence"].startswith(hz.SENTENCE_STAGE["LEAD-TIME-INCONSISTENT"])
    assert lab["horizons"]["3"]["sentence"].startswith("with the forward's final-norm state at the address block's width in the free arm, at horizon 3 the dilution anchor")
    # D-edge: COMPLEMENTARY@2 with free_h's lambda at the grid's edge at horizon 2: the claim is withheld; at horizon 3 only, said in words
    lab = hz.conclude(_rows(d_), "prev_table", KH, None, free_h_edge={"2": True}, **kw)["labels"]
    assert lab["label"] == "LEAD-TIME-COMPLEMENTARY@2" and lab["free_h_edge_horizons"] == [2]
    assert lab["sentence"].startswith("the stage label reads LEAD-TIME-COMPLEMENTARY@2 by the rule while free_h's lambda sits at the grid's edge at horizon 2")
    lab = hz.conclude(_rows(d_), "prev_table", KH, None, free_h_edge={3: True}, **kw)["labels"]
    assert lab["free_h_edge_horizons"] == [3] and lab["sentence"].startswith("at horizon 2 no material margin")
    assert lab["sentence"].endswith("free_h's lambda sits at the grid's edge at horizon(s) 3 (the free arm is bounded by the grid there), said in words")
    lab = hz.conclude(_rows(b), "prev_table", KH, None, free_h_edge={"2": True, "4": True}, **kw)["labels"]   # under ABSORBED: words only
    assert lab["label"] == "LEAD-TIME-ABSORBED" and lab["free_h_edge_horizons"] == [2, 4] and lab["sentence"].startswith(hz.SENTENCE_STAGE["LEAD-TIME-ABSORBED"])
    assert lab["said_in_words"]["free_h_edge_horizons"] == [2, 4]
    # F: SURVIVES at 2 and 3 with the guard firing at 3 only (free_h below free_r2 there): the claim stands, the guard is said beside it
    f_ = {"history_bigram_r2": {1: 0.82, 2: 0.95, 3: 0.95, 4: 0.82}, "history_all_h": {1: 0.83, 2: 0.97, 3: 0.97, 4: 0.83},
          "free_h": {1: 0.80, 2: 0.80, 3: 0.60, 4: 0.80}, "free_r2": _flat(0.70)}
    lab = hz.conclude(_rows(f_), "prev_table", KH, None, **kw)["labels"]
    assert lab["label"] == "LEAD-TIME-SURVIVES@2" and lab["guard_horizons"] == [3] and lab["horizons"]["3"]["reader_guard"] is True
    assert "free_h - free_r2 reads NEGATIVE" in lab["horizons"]["3"]["sentence"] and lab["horizons"]["3"]["q"] == "H-SURVIVES"
    assert lab["sentence"].startswith("at horizon 2 the address block adds") and lab["sentence"].endswith("where no branch claim is written")
    # F': the guard at the FIRST horizon withholds the closing claim
    f2 = dict(f_, free_h={1: 0.80, 2: 0.60, 3: 0.80, 4: 0.80})
    lab = hz.conclude(_rows(f2), "prev_table", KH, None, **kw)["labels"]
    assert lab["label"] == "LEAD-TIME-SURVIVES@2" and lab["guard_horizons"] == [2]
    assert lab["sentence"].startswith("the stage label reads LEAD-TIME-SURVIVES@2 by the rule while the reader guard fired")
    # G: NEGATIVE readings carry their prefixes, each its own
    g_ = dict(b, free_h=_flat(0.90))
    lab = hz.conclude(_rows(g_), "prev_table", KH, None, **kw)["labels"]
    h2 = lab["horizons"]["2"]
    assert h2["d_eq_h_reading"] == "NEGATIVE" and h2["d_add_h_reading"] == "NEGATIVE" and h2["negative"] is True
    assert h2["sentence"].startswith(hz._NEG_EQ + hz._NEG_ADD) and lab["said_in_words"]["negative_horizons"] == [2, 3, 4]
    assert lab["stage"] == "LEAD-TIME-ABSORBED"
    # H: a straddle at the FIRST surviving horizon withholds the branch claim
    h_ = dict(b, history_bigram_r2={1: 0.82, 2: (0.82, 0.90), 3: 0.82, 4: 0.82}, history_all_h={1: 0.83, 2: (0.83, 0.91), 3: 0.83, 4: 0.83})
    lab = hz.conclude(_rows(h_), "prev_table", KH, None, **kw)["labels"]
    assert lab["label"] == "LEAD-TIME-SURVIVES@2" and lab["horizons"]["2"]["floor_straddle"] is True and lab["straddle_horizons"] == [2]
    assert abs(lab["horizons"]["2"]["d_eq_h"]["delta"] - 0.06) < 1e-9 and lab["horizons"]["2"]["d_eq_h_reading"] == "SIGNAL"
    assert lab["sentence"].startswith("the stage label reads LEAD-TIME-SURVIVES@2 by the rule while a CI95 straddles")
    assert "not settled at this power" in lab["horizons"]["2"]["sentence"]
    # I: a shorter horizon set labels on what it has; the REPRODUCE horizon alone has nothing to label (void, not ABSORBED)
    lab = hz.conclude(_rows(b, horizons=(1, 2)), "prev_table", {"1": "8", "2": "8"}, None, horizons=(1, 2), **kw)["labels"]
    assert lab["label_horizons"] == [2] and lab["label"] == "LEAD-TIME-ABSORBED"
    lab1 = hz.conclude(_rows(b, horizons=(1,)), "prev_table", {"1": "8"}, None, horizons=(1,), **kw)["labels"]
    assert lab1["label"] == "INCOMPLETE" and lab1["void"] is True and lab1["stage"] is None and lab1["label_horizons"] is None
    assert lab1["missing_label_cells"] == ["no label horizon beyond the REPRODUCE horizon"]
    # J: INCOMPLETE on a missing arm
    short = [r for r in _rows(b) if not (r["arm"] == "free_h" and r["key"] == 3)]
    lab = hz.conclude(short, "prev_table", KH, None, **kw)["labels"]
    assert lab["label"] == "INCOMPLETE" and lab["void"] is True and lab["missing_arms"] == {"3": ["free_h"]}
    assert lab["horizons"] is None and lab["stage"] is None
    with pytest.raises(SystemExit, match="unknown encoding"):
        hz.conclude(_rows(b), "nope", KH, None, **kw)


def test_pairing_is_refused_within_a_scope():
    rows = _rows({})
    bad = [dict(r) for r in rows]
    for r in bad:
        if r["arm"] == "free_h" and r["key"] == 2 and r["scope"] == "covered" and r["prompt_idx"] == 0 and r["gate"] == 0:
            r["needed"] += 1
    with pytest.raises(SystemExit, match="pairing violated"):
        hz.conclude(bad, "prev_table", {"1": "8", "2": "8", "3": "8", "4": "8"}, None, n_boot=50, budgets=(16,))
    with pytest.raises(SystemExit, match="only the two unions are stored"):
        hz.conclude([dict(rows[0], scope="all")], "prev_table", {"1": "8"}, None, n_boot=50, budgets=(16,))
    with pytest.raises(SystemExit, match="duplicate state row"):
        hz.conclude(rows + [dict(rows[0])], "prev_table", {"1": "8", "2": "8", "3": "8", "4": "8"}, None, n_boot=50, budgets=(16,))


# ---------------------------------------------------------------------------
# guards, the R2 reference, exact recompute and its refusals
# ---------------------------------------------------------------------------

def test_guards_under_results(tmp_path, monkeypatch):
    d, b, g = tps._unseen_harvest(tmp_path, rule="random", R=21, seed=12)
    tpr._add_hidden(d, seed=12)
    src = tpr._replay_source(tmp_path / "src.npz", rule=False)
    with pytest.raises(SystemExit, match="may not write under results/"):
        hz.run(_args(d, b, g, ROOT / "results" / "smoke" / "x.json", src, only_seeds="0"))
    with pytest.raises(SystemExit, match="lambda grid, k grid or horizon set"):
        hz.run(_args(d, b, g, ROOT / "results" / "smoke" / "y.json", src, lambdas=FAST, k_grid=None))
    with pytest.raises(SystemExit, match="lambda grid, k grid or horizon set"):
        hz.run(_args(d, b, g, ROOT / "results" / "smoke" / "y.json", src, lambdas=None, k_grid=None, horizons=H123))
    with pytest.raises(SystemExit, match="replay source must be the pinned checkpoint"):
        hz.run(_args(d, b, g, ROOT / "results" / "smoke" / "z.json", src, lambdas=None, k_grid=None))
    # horizons must be strictly increasing and start at the REPRODUCE horizon (smoke and test paths)
    with pytest.raises(SystemExit, match="start at 1"):
        hz.run(_args(d, b, g, tmp_path / "h.json", src, horizons="2,3"))
    with pytest.raises(SystemExit, match="start at 1"):
        hz.run(_args(d, b, g, tmp_path / "h.json", src, horizons="1,3,2"))
    monkeypatch.setattr(hz.pr, "_under_results", lambda p: True)        # results/ membership stubbed; nothing written there
    with pytest.raises(SystemExit, match="must be results/real/prefetch_horizon_s3.json"):
        hz.run(_args(d, b, g, tmp_path / "wrong_name.json", src, lambdas=None, k_grid=None, replay="hf"))
    out = tmp_path / "prefetch_horizon_s3.json"
    state = Path(str(out) + ".state.jsonl"); state.write_text("x")
    with pytest.raises(SystemExit, match="state.jsonl exists: a registered payload is never overwritten"):
        hz.run(_args(d, b, g, out, src, lambdas=None, k_grid=None, replay="hf"))
    state.unlink()
    monkeypatch.setattr(hz, "ROOT", tmp_path / "scratch_root")
    (tmp_path / "scratch_root" / "results" / "real").mkdir(parents=True)
    out = tmp_path / "scratch_root" / "results" / "real" / "prefetch_horizon_s3.json"
    with pytest.raises(SystemExit, match="r2 none is refused under results/"):
        hz.run(_args(d, b, g, out, src, lambdas=None, k_grid=None, replay="hf", r2="none"))
    with pytest.raises(SystemExit, match="must be the registered one for this harvest"):
        hz.run(_args(d, b, g, out, src, lambdas=None, k_grid=None, replay="hf", r2=str(tmp_path / "elsewhere.json")))
    with pytest.raises(SystemExit, match="not found"):
        hz.run(_args(d, b, g, out, src, lambdas=None, k_grid=None, replay="hf", r2=None))
    monkeypatch.undo()
    # the replay's eps and layer count, and the R2 payload's encoding, are checked under results/
    monkeypatch.setattr(hz.pr, "_under_results", lambda p: True)
    monkeypatch.setattr(hz, "ROOT", tmp_path / "scratch_root")
    r2_out = tmp_path / "scratch_root" / "results" / "real" / "prefetch_r2_s3.json"
    good = r2.load_replay_source(str(src))
    monkeypatch.setattr(hz.r2, "load_replay_source", lambda spec: dict(good, sha256=r2.REPLAY_SOURCE_SHA256, eps=1e-3))
    monkeypatch.setattr(hz, "r2_reference", lambda *a, **k: {"encoding": "prev_table"})
    with pytest.raises(SystemExit, match="eps must be 1e-5"):
        hz.run(_args(d, b, g, out, src, lambdas=None, k_grid=None, replay="hf", r2=str(r2_out)))
    monkeypatch.setattr(hz, "r2_reference", lambda *a, **k: {"encoding": "cur_table_at_prev"})
    with pytest.raises(SystemExit, match="encoding must be prev_table"):
        hz.run(_args(d, b, g, out, src, lambdas=None, k_grid=None, replay="hf", r2=str(r2_out)))
    monkeypatch.undo()
    assert hz.OUT_OF_HARVEST == {"harvest_moe": "prefetch_horizon_s3.json", "harvest_moe_r": "prefetch_horizon_s3_r.json"}
    assert hz.R2_OF_HARVEST == {"harvest_moe": "prefetch_r2_s3.json", "harvest_moe_r": "prefetch_r2_s3_r.json"}


def test_r2_reference_reading(tmp_path):
    d, b, g, r2_out, out, payload = _chain(tmp_path, tmp_path / "src.npz", rule="random", R=21, T=14, seed=13, horizons="1,2")
    ref = hz.read_r2(r2_out)
    rp = json.loads(r2_out.read_text(encoding="utf-8"))
    assert ref["encoding"] == rp["provenance"]["encoding_selected"] and ref["k_selected"] == rp["provenance"]["k_selected"]
    assert set(ref["lambda_selected"]) == set(r2.ARMS_REQUIRED) and ref["lambda_selected"]["replay_zerofit"] is None
    assert ref["n_state_rows"] == rp["n_state_rows"] == len(ref["_rows"]) and ref["sha256"] == _sha(r2_out)
    assert ref["replay_source_sha256"] == rp["provenance"]["replay_source"]["sha256"]
    assert set(ref["cells"]) == {"d_eq_h", "d_add_h", "history_all_h-history_bigram_r2", "free_h-free_r2"}
    # the reference resolves from the harvest name only under the repo's results/, else explicitly or not at all
    assert hz.r2_reference(d, "none", smoke=False, out_under_results=False) is None
    assert hz.r2_reference(d, None, smoke=True, out_under_results=False) is None
    assert hz.r2_reference(d, str(r2_out), smoke=False, out_under_results=False)["sha256"] == ref["sha256"]
    with pytest.raises(SystemExit, match="not found"):
        hz.r2_reference(d, str(tmp_path / "missing.json"), smoke=False, out_under_results=False)
    # refusals: not an R2 payload; another instrument; a smoke; no state file
    other = tmp_path / "other.json"
    other.write_text(json.dumps({"registered": "something else"}), encoding="utf-8")
    with pytest.raises(SystemExit, match="not a generalising free baseline"):
        hz.read_r2(other)
    p2 = json.loads(json.dumps(rp)); p2["provenance"]["instrument_sha256"] = "0" * 64
    other.write_text(json.dumps(p2), encoding="utf-8")
    with pytest.raises(SystemExit, match="not written by the frozen R2 tool"):
        hz.read_r2(other)
    p3 = json.loads(json.dumps(rp)); p3["provenance"]["smoke"] = True
    other.write_text(json.dumps(p3), encoding="utf-8")
    with pytest.raises(SystemExit, match="smoke payload"):
        hz.read_r2(other)
    other.write_text(json.dumps(rp), encoding="utf-8")
    with pytest.raises(SystemExit, match="state file .* not found"):
        hz.read_r2(other)
    # a reference read on other shards is refused by run()
    o = tmp_path / "o"
    o.mkdir()
    d2, _, _ = tps._unseen_harvest(o, rule="random", R=21, T=14, seed=14)
    with pytest.raises(SystemExit, match="different harvest shards"):
        hz.run(_args(d2, b, g, tmp_path / "x.json", tmp_path / "src.npz", r2=str(r2_out), horizons="1,2"))


def test_conclude_from_refusals(tmp_path, monkeypatch):
    d, b, g, r2_out, out, payload = _chain(tmp_path, tmp_path / "src.npz", rule="token", R=21, T=14, seed=6, horizons=H123)
    hz.conclude_from(out)                                                 # clean
    state = Path(str(out) + ".state.jsonl")
    lines = state.read_text(encoding="utf-8").splitlines()
    header = json.loads(lines[0])

    def write_header(h):
        state.write_text("\n".join([json.dumps(h)] + lines[1:]) + "\n", encoding="utf-8")

    def write_payload(p):
        out.write_text(json.dumps(p), encoding="utf-8")

    kk = dict(header["k_of_horizon"]); kk["2"] = "0" if kk["2"] != "0" else "8"
    write_header(dict(header, k_of_horizon=kk))
    with pytest.raises(SystemExit, match="k per horizon differs"):
        hz.conclude_from(out)
    lam = json.loads(json.dumps(header["lambda_selected"])); lam["2"]["h_only"] = 12345.0
    write_header(dict(header, lambda_selected=lam))
    with pytest.raises(SystemExit, match="lambdas differ from the payload's"):
        hz.conclude_from(out)
    rr = dict(header["r2"]); rr["sha256"] = "0" * 64
    write_header(dict(header, r2=rr))
    with pytest.raises(SystemExit, match="R2 reference differs"):
        hz.conclude_from(out)
    write_header(dict(header, replay_source_sha256="0" * 64))
    with pytest.raises(SystemExit, match="replay source sha differs"):
        hz.conclude_from(out)
    write_header(dict(header, smoke=True))
    with pytest.raises(SystemExit, match="registration or smoke flag differs"):
        hz.conclude_from(out)
    write_header(dict(header, horizons=[1, 2]))
    with pytest.raises(SystemExit, match="horizons differ"):
        hz.conclude_from(out)
    write_header(header)
    # a flipped grid-edge flag at horizon 2 is refused: it is re-derived from the selected k / lambda
    p4 = json.loads(json.dumps(payload)); p4["provenance"]["selection"]["2"]["k_grid_edge"] = not p4["provenance"]["selection"]["2"]["k_grid_edge"]
    write_payload(p4)
    with pytest.raises(SystemExit, match="k grid-edge flag at horizon 2"):
        hz.conclude_from(out)
    p4 = json.loads(json.dumps(payload)); s = p4["provenance"]["selection"]["3"]; s["lambda_grid_edge"]["h_only"] = not s["lambda_grid_edge"]["h_only"]
    write_payload(p4)
    with pytest.raises(SystemExit, match="grid-edge flag for h_only at horizon 3"):
        hz.conclude_from(out)
    # a CONSISTENT flip of k at horizon 2 in header and payload is refused: the k table re-selects it
    p2 = json.loads(json.dumps(payload))
    s2 = p2["provenance"]["selection"]["2"]
    other_k = [x for x in p2["provenance"]["constants"]["k_grid"] if x != s2["k_selected"]][0]
    s2["k_selected"] = other_k
    kk = dict(header["k_of_horizon"]); kk["2"] = other_k
    write_header(dict(header, k_of_horizon=kk)); write_payload(p2)
    with pytest.raises(SystemExit, match="at horizon 2 is not the pair its k table selects"):
        hz.conclude_from(out)
    # a CONSISTENT flip of an arm's lambda at horizon 3 is refused by its val table
    p3 = json.loads(json.dumps(payload))
    s3 = p3["provenance"]["selection"]["3"]
    cur = s3["lambda_selected"]["history_all_h"]
    other = [float(x) for x in p3["provenance"]["constants"]["lambdas"] if float(x) != cur][0]
    s3["lambda_selected"]["history_all_h"] = other
    s3["lambda_grid_edge"]["history_all_h"] = bool(other in (float(p3["provenance"]["constants"]["lambdas"][0]), float(p3["provenance"]["constants"]["lambdas"][-1])))
    lam = json.loads(json.dumps(header["lambda_selected"])); lam["3"]["history_all_h"] = other
    write_header(dict(header, lambda_selected=lam)); write_payload(p3)
    with pytest.raises(SystemExit, match="lambda for history_all_h at horizon 3 is not the one its val table selects"):
        hz.conclude_from(out)
    # the horizon-1 selections must be the R2 payload's; the re-selection flag must be what the tables imply
    p5 = json.loads(json.dumps(payload))
    s1 = p5["provenance"]["selection"]["1"]
    cur = s1["lambda_selected"]["h_only"]
    other = [float(x) for x in p5["provenance"]["constants"]["lambdas"] if float(x) != cur][0]
    s1["lambda_selected"]["h_only"] = other
    lam = json.loads(json.dumps(header["lambda_selected"])); lam["1"]["h_only"] = other
    write_header(dict(header, lambda_selected=lam)); write_payload(p5)
    with pytest.raises(SystemExit, match="horizon-1 lambda for h_only is not the R2 payload's"):
        hz.conclude_from(out)
    p6 = json.loads(json.dumps(payload)); p6["provenance"]["selection"]["1"]["reselect"]["matches_r2"] = not p6["provenance"]["selection"]["1"]["reselect"]["matches_r2"]
    write_header(header); write_payload(p6)
    with pytest.raises(SystemExit, match="re-selection flag"):
        hz.conclude_from(out)
    # the arm list, the lambda sources and the taken k's grid-edge flag are pinned too
    p7 = json.loads(json.dumps(payload)); p7["provenance"]["selection"]["2"]["arms"].remove("h_only")
    write_payload(p7)
    with pytest.raises(SystemExit, match="arm list at horizon 2"):
        hz.conclude_from(out)
    p8 = json.loads(json.dumps(payload)); p8["provenance"]["selection"]["2"]["lambda_source"]["h_only"] = "r2"
    write_payload(p8)
    with pytest.raises(SystemExit, match="lambda sources at horizon 2"):
        hz.conclude_from(out)
    p9 = json.loads(json.dumps(payload)); p9["provenance"]["selection"]["1"]["k_grid_edge"] = not p9["provenance"]["selection"]["1"]["k_grid_edge"]
    write_payload(p9)
    with pytest.raises(SystemExit, match="horizon-1 k grid-edge flag"):
        hz.conclude_from(out)
    p10 = json.loads(json.dumps(payload)); p10["provenance"]["selection"]["1"]["lambda_grid_edge"]["h_only"] = True
    write_payload(p10)
    with pytest.raises(SystemExit, match="grid-edge flag for h_only is not null"):
        hz.conclude_from(out)
    # a mutated state row is a RECOMPUTE MISMATCH; a changed R2 file on disk is refused by its sha
    write_payload(payload)
    row = json.loads(lines[-1]); row["hits"] = row["hits"] + 1 if row["hits"] < row["needed"] else row["hits"] - 1
    state.write_text("\n".join(lines[:-1] + [json.dumps(row)]) + "\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="RECOMPUTE MISMATCH"):
        hz.conclude_from(out)
    state.write_text("\n".join(lines) + "\n", encoding="utf-8")
    hz.conclude_from(out)
    r2_state = Path(str(r2_out) + ".state.jsonl")
    keep = r2_state.read_bytes()
    r2_state.write_bytes(keep + b"\n")
    with pytest.raises(SystemExit, match="is not the one this run read"):
        hz.conclude_from(out)
    r2_state.write_bytes(keep)
    r2_out.rename(tmp_path / "moved.json")
    with pytest.raises(SystemExit, match="is not present; REPRODUCE cannot be recomputed"):
        hz.conclude_from(out)
    (tmp_path / "moved.json").rename(r2_out)
    hz.conclude_from(out)
    # under results/ a payload must be a registered run (stubbed membership; the files stay in tmp_path)
    monkeypatch.setattr(hz.pr, "_under_results", lambda p: True)
    with pytest.raises(SystemExit, match="must carry the registered lambda grid, k grid and horizons"):
        hz.conclude_from(out)
    monkeypatch.undo()
    hz.conclude_from(out)


# ---------------------------------------------------------------------------
# constants, dims, the no-torch rule
# ---------------------------------------------------------------------------

def test_arm_dims_and_constants():
    enc = "prev_table"
    assert hz.arms_h(enc) == ("marginal", "history", "free_tok", "history_tok", "free_bigram_b", "history_bigram_b", "free_r2",
                              "history_tok_r2", "history_bigram_r2", "h_only", "free_h", "history_all_h")
    assert hz.arms_h("cur_table_at_prev")[4:6] == ("free_bigram_a", "history_bigram_a")
    assert hz.ARMS_J1 == r2.ARMS_REQUIRED + ("marginal",) and len(hz.ARMS_J1) == 20
    assert hz.arm_dims("marginal", enc) == 1 and hz.arm_dims("free_h", enc) == 3073 and hz.arm_dims("history_all_h", enc) == 4097
    assert hz.ARM_BLOCKS_H["marginal"] == ("bias",) and all(hz.ARM_BLOCKS_H[a] == r2.ARM_BLOCKS_R2[a] for a in r2.ARM_BLOCKS_R2)
    assert hz.HORIZONS == (1, 2, 3, 4) and hz.LABEL_HORIZONS == (2, 3, 4) and hz.REPRODUCE_HORIZON == 1
    assert hz.STATE_SCOPES == ("covered", "fallback") and hz.SCOPES == ("covered", "fallback", "all")
    assert hz.IDENTITY_CELLS == {"d_eq_h": "d_eq_h", "d_add_h": "d_add_h", "anchor": "history_all_h-history_bigram_r2",
                                 "free_h-free_r2": "free_h-free_r2"}
    assert hz.RESELECT_ARMS == r2.ARMS_RIDGE_R2 and hz.LAMBDAS == r2.LAMBDAS and hz.K_GRID == r2.K_GRID
    assert set(hz.SENTENCE_STAGE) == {"LEAD-TIME-ABSORBED", "LEAD-TIME-SURVIVES", "LEAD-TIME-COMPLEMENTARY", "LEAD-TIME-INCONSISTENT"}
    for q in ("H-SURVIVES", "H-COMPLEMENTARY", "H-ABSORBS", "H-INCONSISTENT"):
        for s in (False, True):
            assert "j = 2" in hz.sentence_horizon(q, s, 2)
    with pytest.raises(SystemExit, match="unknown horizon label"):
        hz.sentence_horizon("nope", False, 2)
    assert hz.REGISTERED.startswith("OQ-9 STAGE-1 HORIZON READ REGISTRATION")
    assert hz.R2_INSTRUMENT_SHA256 == "eaf671fdb9d637624c012b5555a06d1a7ff82072d09829c1d31c3aa492231a84"


def test_select_k_and_pooled_all_read_the_union_scopes():
    h = hz.Horizon.__new__(hz.Horizon)
    h.k_grid, h.lambdas = r2.K_GRID, (1.0, 10.0)
    h.val_table, h.lambda_selected, h.grid_edge = {}, {}, {}

    def grid(values):
        return {(k, lam, 16, "fallback"): (np.array([[int(100 * v)] * L]), np.array([[100] * L])) for (k, lam), v in values.items()}

    flat = {(k, lam): 0.5 for k in r2.K_GRID for lam in (1.0, 10.0)}
    h.select_k(grid(flat))
    assert h.k_selected == 0.0 and h.lambda_selected["free_r2"] == 1.0 and h.k_grid_edge is True
    best = dict(flat); best[(32.0, 10.0)] = 0.9
    h.select_k(grid(best))
    assert h.k_selected == 32.0 and h.lambda_selected["free_r2"] == 10.0 and h.k_grid_edge is False
    assert h.val_table["free_r2"] == h.k_val_table["32"]
    val = {("h_only", 16, 1.0, "covered"): (np.array([[60] * L]), np.array([[100] * L])),
           ("h_only", 16, 1.0, "fallback"): (np.array([[20] * L]), np.array([[100] * L]))}
    assert abs(hz.Horizon._pooled_all(val, "h_only", 1.0) - 0.4) < 1e-12
    # a stratum-named key (the R2 shape) is not read by the union rule
    assert np.isnan(hz.Horizon._pooled_all({("h_only", 16, 1.0, "covered_5p"): val[("h_only", 16, 1.0, "covered")]}, "h_only", 1.0))


def test_tool_imports_no_torch_transformers_or_safetensors():
    src = Path(hz.__file__).read_text(encoding="utf-8")
    for name in ("import torch", "import transformers", "import safetensors", "from safetensors", "from transformers"):
        assert name not in src
    code = ("import sys; sys.path.insert(0, r'%s'); import run_prefetch_horizon; "
            "print([m in sys.modules for m in ('torch', 'transformers', 'safetensors')])" % str(ROOT / "tools"))
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)
    assert out.stdout.strip() == "[False, False, False]"
