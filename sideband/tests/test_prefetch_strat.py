"""tests/test_prefetch_strat.py (OQ-9 stage-1 STRATIFIED COVERAGE READ, the post-hoc
diagnostic of the free-bigram twin's coverage caveat): the CI-safe layer — the tool
refuses a modified twin (and its parent); the twin's arms are the twin's readers
(weights equal Bigram.fit's at the same lambda); every test position falls in exactly
one coverage stratum and the stratified rows sum to the twin's state rows (REPRODUCE
EXACT against a fixture twin payload; a tampered twin row is NEAR or INVALID by the
pinned rule); a routing rule driven by the forward's own output summaries is recovered
by pt_only and reads PT-ABSORBS (the index alignment: PT at the anchor, target S[t+1]);
labels are mechanical for every branch incl. the floor-straddle flag and the void
branches; pairing within a scope is refused; smoke / grid / twin / out / overwrite
guards; --conclude-from reproduces a payload, refuses a tampered row, a flipped header
and a changed twin; arm columns and dims; LF evidence; no torch.

Fixtures are IMPORTED from tests/test_prefetch_readouts.py (the frozen instrument's
tests); one helper here remaps train and val tokens so that four token ids appear only
in TEST rows (the unseen-key strata), and one re-rules a harvest by its mass16 argmax."""

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
sys.path.insert(0, str(ROOT / "tests"))
import run_prefetch_readouts as pr  # noqa: E402  (the frozen stage-1 instrument)
import run_prefetch_bigram as rb  # noqa: E402  (the frozen twin)
import run_prefetch_strat as rs  # noqa: E402
import test_prefetch_readouts as tpr  # noqa: E402  (its fixtures)
from sideband.probes import load_label_space  # noqa: E402

E, L, K = pr.N_EXPERTS, pr.N_GATES, pr.TOP_K
ONE = "100"
FAST = "1,100"
UNSEEN = (12, 13, 14, 15)          # token ids that appear only in TEST rows of the unseen-key fixtures


def _twin_args(d, b, g, out, **kw):
    base = dict(harvest=str(d), out=str(out), buckets=str(b), glue=str(g), committed="none",
                only_seeds=None, smoke_split_val=False, lambdas=ONE, conclude_from=None)
    base.update(kw)
    return argparse.Namespace(**base)


def _args(d, b, g, out, **kw):
    base = dict(harvest=str(d), out=str(out), buckets=str(b), glue=str(g), twin="none",
                only_seeds=None, smoke_split_val=False, lambdas=ONE, conclude_from=None)
    base.update(kw)
    return argparse.Namespace(**base)


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _rewrite(d: Path, fn) -> None:
    """Apply fn(z: dict) -> None to every shard's arrays in place and refresh the meta shas."""
    for npz in sorted(d.glob("*.npz")):
        z = dict(np.load(npz))
        fn(z)
        np.savez(npz, **z)
        mp = d / npz.name.replace(".npz", ".meta.json")
        meta = json.loads(mp.read_text())
        meta["npz_sha256"] = _sha(npz)
        mp.write_text(json.dumps(meta))


def _unseen_harvest(tmp_path, rule="token", R=24, T=16, seed=5):
    """A fixture harvest (vocab 16) whose TRAIN and VAL rows use token ids 0..11 only, so
    ids 12..15 are unseen keys that occur only in TEST rows (prompt_idx % 7 == 6): the
    four coverage strata are all populated on test. The routing rule is re-applied
    after the remap (rule 'token': S[t+1] a function of tokens[t]; 'random': none)."""
    d, b, g = tpr.make_fake_harvest(tmp_path, rule=rule, R=R, T=T, vocab=16, seed=seed)

    def remap(z):
        test = (z["prompt_idx"] % 7) == 6
        tok = z["tokens"].copy()
        tok[~test] = tok[~test] % 12
        z["tokens"] = tok.astype(np.int32)
        if rule == "token":
            z["slots"] = tpr._slots_token(z["tokens"], z["lengths"])

    _rewrite(d, remap)
    return d, b, g


def _pt_rule(d: Path) -> None:
    """Re-rule a harvest so that S[t, l] = {(4 j + l) mod 64 : j among the 8 largest of the 16
    coordinates of mass16[t-1]}: the TARGET S[t+1] at anchor t is a linear read of the summaries
    PT(t) (score expert 4 j + l by mass16[t, j]) and a function of nothing the tokens or S[t] hold
    (the fixture's masses are independent per position)."""
    def rule(z):
        tokens, lengths, m16 = z["tokens"], z["lengths"], z["mass16"].astype(np.float64)
        R, T = tokens.shape
        slots = np.full((R, T, L, K), -1, dtype=np.int16)
        for r in range(R):
            for t in range(int(lengths[r])):
                top = np.argsort(-m16[r, t - 1], kind="stable")[:K] if t >= 1 else np.arange(K)
                for l in range(L):
                    slots[r, t, l] = np.sort((4 * top + l) % E)
        z["slots"] = slots
    _rewrite(d, rule)


def _point(c, arm, B, scope="all"):
    return c["tables"][f"{arm}|B={B}|{scope}"]["all"]["point"]


# ---------------------------------------------------------------------------
# the frozen twin (and its parent) are asserted; the twin's arms are the twin's readers
# ---------------------------------------------------------------------------

def test_frozen_twin_sha_is_asserted(tmp_path):
    assert rs.assert_frozen_twin() == rs.TWIN_INSTRUMENT_SHA256
    assert rs.rb.assert_frozen_instrument() == rb.FROZEN_INSTRUMENT_SHA256
    tampered = tmp_path / "run_prefetch_bigram.py"
    tampered.write_bytes(Path(rb.__file__).read_bytes() + b"\n# touched\n")
    with pytest.raises(SystemExit, match="refusing"):
        rs.assert_frozen_twin(tampered)
    # a CRLF copy of the twin's bytes still passes (the sha is LF-normalised)
    crlf = tmp_path / "crlf.py"
    crlf.write_bytes(Path(rb.__file__).read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
    assert rs.assert_frozen_twin(crlf) == rs.TWIN_INSTRUMENT_SHA256


def test_twin_arm_weights_equal_the_twins_at_the_same_lambda(tmp_path):
    d, b, g = _unseen_harvest(tmp_path, rule="token", R=21, T=14, seed=2)
    data = pr.S3Data(d)
    lab, nc = load_label_space(b, g)
    bb = rb.Bigram(data, lab, nc, lambdas=(1.0, 100.0))
    bb.fit()
    st = rs.Strat(data, lab, nc, twin=None, lambdas=(1.0, 100.0))
    st.fit()
    # the twin's Gram and targets, accumulated by the same statements on the same chunks
    assert np.array_equal(st.G, bb.G) and np.array_equal(st.C, bb.C)
    for arm in rs.ARMS_TWIN:
        for lam in (1.0, 100.0):
            assert np.array_equal(st.W[(arm, lam)], bb.W[(arm, lam)]), (arm, lam)
    # the full Gram carries the twin's as its leading block, the PT cross terms beside it
    assert np.array_equal(st.G_full[:rb.D_X, :rb.D_X], bb.G)
    assert st.G_full.shape == (rs.D_X, rs.D_X) and st.C_full.shape == (rs.D_X, rb.D)
    assert np.allclose(st.G_full, st.G_full.T)


def test_pt_vec_is_the_stored_summaries_at_the_anchor(tmp_path):
    d, b, g = _unseen_harvest(tmp_path, rule="random", R=21, T=14, seed=3)
    data = pr.S3Data(d)
    lab, nc = load_label_space(b, g)
    st = rs.Strat(data, lab, nc, lambdas=(1.0,))
    rows, anchors = pr.restrict(*rb.bigram_positions(data.lengths, data.T), st.masks["test"])
    P = st.pt_vec(rows, anchors)
    assert P.shape == (rows.shape[0], rs.D_PT)
    assert np.array_equal(P[:, :16], data.mass16[rows, anchors])
    assert np.array_equal(P[:, 16:80], data.mass64[rows, anchors])
    assert np.allclose(P[:, 80], data.entropy[rows, anchors] / np.log(lab.shape[0]))
    assert abs(st.ent_scale - np.log(lab.shape[0])) < 1e-12
    # the design is the twin's with PT after the bias (the tables are needed for the twin's blocks)
    st.fit_tables()
    X, Y = st.design_pt(rows[:5], anchors[:5])
    Xt, Yt = st.design(rows[:5], anchors[:5])
    assert np.array_equal(X[:, :rb.D_X], Xt) and np.array_equal(Y, Yt)
    assert np.array_equal(X[:, rs.PT_COLS], P[:5]) and np.all(X[:, rs.BIAS_COL] == 1.0)


# ---------------------------------------------------------------------------
# strata, REPRODUCE against a fixture twin payload, the identity check
# ---------------------------------------------------------------------------

def test_strata_partition_and_reproduce_exact_against_a_fixture_twin(tmp_path):
    d, b, g = _unseen_harvest(tmp_path, rule="token", R=24, T=16, seed=5)
    twin_out = tmp_path / "twin.json"
    tp = rb.run(_twin_args(d, b, g, twin_out, lambdas=FAST))
    out = tmp_path / "strat.json"
    payload = rs.run(_args(d, b, g, out, lambdas=FAST, twin=str(twin_out)))
    prov, lab = payload["provenance"], payload["conclusion"]["labels"]
    # the twin's encoding and lambdas were taken verbatim
    assert prov["encoding_source"] == "twin" and prov["encoding_selected"] == tp["provenance"]["encoding_selected"]
    for arm in rs.ARMS_TWIN:
        assert prov["lambda_selected"][arm] == tp["provenance"]["lambda_selected"][arm]
        assert prov["lambda_source"][arm] == "twin" and prov["lambda_grid_edge"][arm] is None
    for arm in rs.ARMS_PT:
        assert prov["lambda_source"][arm] == "val" and isinstance(prov["lambda_grid_edge"][arm], bool)
    assert prov["twin"]["sha256"] == _sha(twin_out) and prov["twin"]["state_sha256"] == _sha(Path(str(twin_out) + ".state.jsonl"))
    assert "_rows" not in prov["twin"]
    # REPRODUCE: exact, every twin row compared, and the pooled D_eq is the twin's to the bit
    rep = lab["reproduce"]
    assert rep["status"] == "EXACT" and rep["ok"] is True and lab["reproduce_status"] == "EXACT"
    assert rep["n_compared"] == rep["n_twin_rows"] == tp["n_state_rows"]
    assert rep["missing_in_strat"] == rep["extra_in_strat"] == rep["needed_mismatch_rows"] == rep["hits_mismatch_rows"] == 0
    assert lab["all_gate_eq_matches_twin"] is True
    assert payload["conclusion"]["deltas"]["gate_eq|B=16|all"] == tp["conclusion"]["deltas"]["gate_eq|B=16"]
    # the six strata partition the test positions; the covered union and the three unseen-key strata are populated
    sc = prov["strata_counts"]["test"]
    assert sum(sc[s]["n"] for s in rs.STRATA) == sc["n"] == prov["n_positions"]["bigram/test"]
    assert sc["covered"]["n"] > 0 and all(sc[s]["n"] > 0 for s in rs.UNIONS["fallback"])
    assert sc["covered"]["n"] == sum(sc[s]["n"] for s in rs.UNIONS["covered"]) and sc["all"]["n"] == sc["n"]
    assert abs(sum(sc[s]["share"] for s in rs.STRATA) - 1.0) < 1e-9
    scopes = lab["scopes"]
    assert scopes["all"]["positions"] == sc["n"] and abs(scopes["all"]["share"] - 1.0) < 1e-12
    assert scopes["fallback"]["positions"] == sum(sc[s]["n"] for s in rs.UNIONS["fallback"])
    assert scopes["covered"]["positions"] + scopes["fallback"]["positions"] == scopes["all"]["positions"]
    assert prov["blas"]["cpu_count"] == rs.os.cpu_count() and "blas" in prov["blas"]
    # an independent sum over strata of the state rows reproduces the twin's rows
    _, rows = pr.load_state(Path(str(out) + ".state.jsonl"))
    _, trows = pr.load_state(Path(str(twin_out) + ".state.jsonl"))
    mine = {}
    for r in rows:
        if r["arm"] in rs.ARMS_TWIN:
            k = (r["arm"], r["budget"], r["gate"], r["prompt_idx"])
            h, n = mine.get(k, (0, 0)); mine[k] = (h + r["hits"], n + r["needed"])
    assert mine == {(r["arm"], r["budget"], r["gate"], r["prompt_idx"]): (r["hits"], r["needed"]) for r in trows}
    # every seen token of this fixture occurs five or more times in train, so the two sparse covered strata are empty
    present = {r["stratum"] for r in rows}
    assert present <= set(rs.STRATA) and present >= {"covered_5p", "cur_unseen", "prev_unseen", "both_unseen"}
    assert {r["arm"] for r in rows} == set(rs.ARMS_REQUIRED)
    # labels are read (no label cell missing), and the token rule puts the free arms at the top on covered keys
    assert lab["label"] not in ("INCOMPLETE", "REPRODUCE-INVALID") and " / " in lab["label"] and lab["void"] is False
    assert lab["q1"] in ("COVERED-MATERIAL", "FALLBACK-LOCATED", "UNLOCATED")
    assert lab["q2"] in ("PT-SURVIVES", "PT-COMPLEMENTARY", "PT-ABSORBS", "PT-INCONSISTENT")
    c = payload["conclusion"]
    assert _point(c, "free_tok", 16, "covered") > 0.95 and _point(c, "free_tok", 16, "cur_unseen") < 0.6
    # exact recompute, incl. REPRODUCE re-derived from the twin's state file on disk
    got = rs.conclude_from(out)
    assert got["labels"]["label"] == lab["label"] and got["labels"]["reproduce"]["status"] == "EXACT"
    # evidence files are LF on every platform
    for p in (out, Path(str(out) + ".state.jsonl"), tmp_path / "strat.meta.json"):
        assert b"\r\n" not in p.read_bytes()


def test_strata_masks_split_covered_keys_by_the_smaller_occurrence_count(tmp_path):
    """The six strata on synthetic tables: token k carries k train occurrences (128 k counts) in BOTH tables;
    a position's stratum follows the smaller of its two keys' counts, zero meaning unseen."""
    d, b, g = _unseen_harvest(tmp_path, rule="random", R=21, T=14, seed=15)
    data = pr.S3Data(d)
    lab, nc = load_label_space(b, g)
    st = rs.Strat(data, lab, nc, lambdas=(1.0,))
    st.fit_tables()
    V = st.vocab
    occ = np.arange(V, dtype=np.int64)
    table = np.zeros((V, L, E), np.int64)
    table[:, :, :K] = occ[:, None, None]                 # sum over (gate, expert) = 16 x 8 x k = 128 k
    st.token_table, st.prev_table = table.copy(), table.copy()
    assert np.array_equal(st.token_table.sum(axis=(1, 2)), rs.COUNTS_PER_OCCURRENCE * occ)
    cases = [((1, 1), "covered_1"), ((1, 5), "covered_1"), ((9, 1), "covered_1"), ((2, 9), "covered_2_4"),
             ((4, 4), "covered_2_4"), ((5, 5), "covered_5p"), ((9, 6), "covered_5p"), ((0, 3), "cur_unseen"),
             ((3, 0), "prev_unseen"), ((0, 0), "both_unseen")]
    rows = np.arange(len(cases)); anchors = np.full(len(cases), 2)       # distinct rows, anchor t = 2, key t - 1 = 1
    for i, ((cur, prev), _) in enumerate(cases):
        data.tokens[i, 2], data.tokens[i, 1] = cur, prev
    masks = st.strata_masks(rows, anchors)
    assert set(masks) == set(rs.STRATA)
    for i, (_, want) in enumerate(cases):
        got = [s for s in rs.STRATA if masks[s][i]]
        assert got == [want], (cases[i], got)
    assert np.array_equal(sum(masks[s].astype(int) for s in rs.STRATA), np.ones(len(cases), int))   # a partition
    # asymmetric tables: token k has V - 1 - k occurrences in TABLE_PREV, so a cur / prev swap would misfile these
    st.prev_table = np.zeros((V, L, E), np.int64)
    st.prev_table[:, :, :K] = occ[::-1][:, None, None]
    asym = [((9, 1), "covered_5p"),                      # min(9, 14) = 9; swapped it would read min(1, 6) = 1
            ((1, 9), "covered_1"),                       # min(1, 6) = 1; swapped min(9, 14) = 9
            ((3, V - 1), "prev_unseen"),                 # the last token has 0 previous-table occurrences
            ((V - 1, 3), "covered_5p")]                  # min(15, 12) = 12
    for i, ((cur, prev), _) in enumerate(asym):
        data.tokens[i, 2], data.tokens[i, 1] = cur, prev
    masks = st.strata_masks(np.arange(len(asym)), np.full(len(asym), 2))
    for i, (_, want) in enumerate(asym):
        assert [s for s in rs.STRATA if masks[s][i]] == [want], (asym[i],)


def test_no_twin_path_reselects_what_the_twin_selected(tmp_path):
    d, b, g = _unseen_harvest(tmp_path, rule="token", R=21, T=14, seed=8)
    tp = rb.run(_twin_args(d, b, g, tmp_path / "twin.json", lambdas=FAST))
    payload = rs.run(_args(d, b, g, tmp_path / "strat.json", lambdas=FAST))
    prov = payload["provenance"]
    assert prov["encoding_source"] == "val" and prov["twin"] is None
    assert prov["encoding_selected"] == tp["provenance"]["encoding_selected"]
    for arm in rs.ARMS_TWIN:
        assert prov["lambda_selected"][arm] == tp["provenance"]["lambda_selected"][arm]
        assert prov["val_table"][arm] == tp["provenance"]["val_table"][arm]
        assert prov["lambda_source"][arm] == "val"
    lab = payload["conclusion"]["labels"]
    assert lab["reproduce"] is None and lab["reproduce_ok"] is None and lab["all_gate_eq_matches_twin"] is None
    assert payload["conclusion"]["deltas"]["gate_eq|B=16|all"] == tp["conclusion"]["deltas"]["gate_eq|B=16"]


def test_reproduce_check_is_the_pinned_rule():
    S = len(rs.STRATA)                                             # six strata, 100 trials each per (gate, prompt)
    twin = [{"arm": "history_tok", "budget": 16, "key": 1, "depth": None, "gate": g, "prompt_idx": p, "hits": 300, "needed": 100 * S}
            for g in range(L) for p in (0, 1)] + \
           [{"arm": "free_tok", "budget": 16, "key": 1, "depth": None, "gate": g, "prompt_idx": p, "hits": 280, "needed": 100 * S}
            for g in range(L) for p in (0, 1)]
    rows = []
    for r in twin:
        for i, s in enumerate(rs.STRATA):
            rows.append(dict(r, stratum=s, hits=r["hits"] // S + (0 if i else r["hits"] % S), needed=100))
    rep = rs.reproduce_check(rows, twin)
    assert rep["status"] == "EXACT" and rep["ok"] and rep["n_twin_rows"] == 64 and rep["n_compared"] == 64
    # one hit off on one row: within the NEAR cap (0.1% of 64 rows is 0 rows, so NEAR needs a bigger twin)
    r2 = [dict(r) for r in rows]; r2[0]["hits"] += 1
    rep = rs.reproduce_check(r2, twin)
    assert rep["hits_mismatch_rows"] == 1 and rep["max_abs_hits_gap"] == 1 and rep["status"] == "INVALID"
    # with 2,000 twin rows one +-1 hit mismatch is NEAR, two hits off on one row is INVALID, a needed mismatch is INVALID
    big_twin = [dict(twin[0], prompt_idx=p) for p in range(2000)]
    big_rows = [dict(t, stratum=s, hits=50, needed=100) for t in big_twin for s in rs.STRATA]
    assert rs.reproduce_check(big_rows, big_twin)["status"] == "EXACT"
    b2 = [dict(r) for r in big_rows]; b2[0]["hits"] -= 1
    rep = rs.reproduce_check(b2, big_twin)
    assert rep["status"] == "NEAR" and rep["ok"] is True and rep["hits_mismatch_rows"] == 1
    b3 = [dict(r) for r in big_rows]; b3[0]["hits"] -= 2
    assert rs.reproduce_check(b3, big_twin)["status"] == "INVALID"
    b4 = [dict(r) for r in big_rows]; b4[0]["hits"] -= 1; b4[S]["hits"] += 1; b4[2 * S]["hits"] -= 1   # three twin rows
    assert rs.reproduce_check(b4, big_twin)["status"] == "INVALID"          # 3 rows > 0.1% of 2,000
    b6 = [dict(r) for r in big_rows]; b6[0]["hits"] -= 1; b6[1]["hits"] += 1                       # one twin row, net 0
    assert rs.reproduce_check(b6, big_twin)["status"] == "EXACT"            # the check is on the summed rows
    b5 = [dict(r) for r in big_rows]; b5[0]["needed"] += 1
    rep = rs.reproduce_check(b5, big_twin)
    assert rep["needed_mismatch_rows"] == 1 and rep["status"] == "INVALID"
    # a twin row with no stratified counterpart, or an extra one, is INVALID
    assert rs.reproduce_check(big_rows[S:], big_twin)["missing_in_strat"] == 1
    assert rs.reproduce_check(big_rows[S:], big_twin)["status"] == "INVALID"
    extra = big_rows + [dict(big_rows[0], gate=15, prompt_idx=99999)]
    assert rs.reproduce_check(extra, big_twin)["extra_in_strat"] == 1
    # PT arms are not part of the check
    pt = big_rows + [dict(r, arm="pt_only", hits=10) for r in big_rows]
    assert rs.reproduce_check(pt, big_twin)["status"] == "EXACT"


# ---------------------------------------------------------------------------
# a p_t-driven rule: pt_only recovers it, the free bigram does not, PT-ABSORBS
# ---------------------------------------------------------------------------

def test_pt_rule_is_recovered_by_pt_only_and_reads_pt_absorbs(tmp_path):
    d, b, g = _unseen_harvest(tmp_path, rule="random", R=24, T=14, seed=7)
    _pt_rule(d)
    payload = rs.run(_args(d, b, g, tmp_path / "pt.json", lambdas=FAST))
    c, lab = payload["conclusion"], payload["conclusion"]["labels"]
    # B = 8 is the discriminating budget: each gate's eight targets sit among sixteen candidate experts (4 j + l), so
    # at B = 16 every reader that ranks the candidates first reads 1.0 by construction
    # a 17-weight ridge on a few hundred rows ranks the top-8 of sixteen uniforms imperfectly near the 8th / 9th
    # order statistics (0.85 measured against a 0.49 chance floor), so the bar is 0.8, not 0.95
    assert _point(c, "pt_only", 8) > 0.8                       # PT(t) IS the target S[t+1]
    assert _point(c, "free_tok", 8) < 0.65                     # tokens say nothing (8 of 16 candidates: 0.5)
    assert _point(c, lab["free_bigram_arm"], 8) < 0.65
    assert _point(c, "history", 8) < 0.65                      # S[t] = f(mass16[t-1]) says nothing about S[t+1]
    assert _point(c, "free_bigram_pt", 8) > 0.8 and _point(c, "history_tok_pt", 8) > 0.8
    assert _point(c, "pt_only", 8) - _point(c, "free_tok", 8) > 0.3
    assert pr._reading(c["deltas"]["d_pt|B=8|all"]) == "NEGATIVE"
    assert pr._reading(c["deltas"]["pt_gain|B=8|all"]) == "SIGNAL"
    assert pr._reading(c["deltas"]["pt_only-free_tok|B=8|all"]) == "SIGNAL"
    assert lab["d_eq_pt_all_reading"] != "SIGNAL" and lab["q2"] == "PT-ABSORBS"   # the label budget: saturated, no margin
    assert lab["label"].endswith("PT-ABSORBS")
    assert "no material margin" in lab["sentence"] and "output-distribution summaries" in lab["sentence"]


def test_token_rule_locates_no_margin_on_covered_keys(tmp_path):
    """Under the token rule the free table IS the target where the key is seen, and where it is
    unseen neither the free tables (at the marginal) nor the address block (S[t] = f(tokens[t-1]),
    silent about S[t+1] = f(tokens[t])) carry it: no covered margin, random summaries add nothing."""
    d, b, g = _unseen_harvest(tmp_path, rule="token", R=24, T=16, seed=11)
    payload = rs.run(_args(d, b, g, tmp_path / "tok.json", lambdas=FAST))
    c, lab = payload["conclusion"], payload["conclusion"]["labels"]
    assert _point(c, "free_tok", 16, "covered") > 0.95 and _point(c, "history_tok", 16, "covered") > 0.95
    assert _point(c, "free_tok", 16, "cur_unseen") < 0.6
    assert lab["gate_eq_covered_reading"] != "SIGNAL"
    assert lab["q1"] in ("FALLBACK-LOCATED", "UNLOCATED")
    assert abs(c["deltas"]["pt_gain|B=16|all"]["delta"]) < 0.05        # random summaries add nothing material
    assert lab["d_eq_pt_all_reading"] != "SIGNAL" and lab["d_add_pt_all_reading"] != "SIGNAL" and lab["q2"] == "PT-ABSORBS"


def test_shift_rule_reads_covered_material_and_pt_survives(tmp_path):
    """The address-only rule (S[t+1] a shift of S[t]; tokens and summaries independent of it): the
    address block carries the target on covered and unseen keys alike, and random summaries cannot
    absorb it — COVERED-MATERIAL / PT-SURVIVES, with D_eq SIGNAL in every populated scope."""
    d, b, g = _unseen_harvest(tmp_path, rule="shift", R=24, T=16, seed=9)
    payload = rs.run(_args(d, b, g, tmp_path / "shift.json", lambdas=FAST))
    c, lab = payload["conclusion"], payload["conclusion"]["labels"]
    assert _point(c, "history", 16) > 0.95 and _point(c, "free_tok", 16) < 0.5
    assert _point(c, lab["free_bigram_arm"], 16) < 0.5 and _point(c, "free_bigram_pt", 16) < 0.5
    assert lab["q1"] == "COVERED-MATERIAL" and lab["q2"] == "PT-SURVIVES"
    assert lab["label"] == "COVERED-MATERIAL / PT-SURVIVES"
    assert all(v == "SIGNAL" for v in lab["gate_eq_readings"].values())
    assert lab["d_eq_pt_all_reading"] == "SIGNAL" and lab["d_add_pt_all_reading"] == "SIGNAL"
    assert lab["covered_floor_straddle"] is False and lab["d_eq_pt_floor_straddle"] is False
    assert lab["sentence"].startswith("the coverage caveat on the free-bigram twin is retired")
    assert "the twin's verdict stands at this encoding of p_t" in lab["sentence"]


# ---------------------------------------------------------------------------
# labels are mechanical
# ---------------------------------------------------------------------------

def _rows(rates: dict, per: int = 100, prompts=(0, 1), default: float = 0.80):
    """rates: {arm: {stratum: rate}} (missing arms / strata take the default); one row per
    (arm, stratum, prompt, gate) at budget 16 with `per` trials."""
    rows = []
    for arm in rs.ARMS_REQUIRED:
        for s in rs.STRATA:
            rate = rates.get(arm, {}).get(s, default)
            for p in prompts:
                for g in range(L):
                    rows.append({"arm": arm, "budget": 16, "key": 1, "depth": None, "gate": g, "prompt_idx": p,
                                 "stratum": s, "hits": int(round(per * rate)), "needed": per})
    return rows


def _twin_of(rows: list[dict]) -> list[dict]:
    """The twin rows a stratified row set reproduces: the twin arms summed over the strata."""
    acc = {}
    for r in rows:
        if r["arm"] not in rs.ARMS_TWIN:
            continue
        k = (r["arm"], r["budget"], r["gate"], r["prompt_idx"])
        h, n = acc.get(k, (0, 0)); acc[k] = (h + r["hits"], n + r["needed"])
    return [{"arm": a, "budget": B, "key": 1, "depth": None, "gate": g, "prompt_idx": p, "hits": h, "needed": n}
            for (a, B, g, p), (h, n) in acc.items()]


COVERED_S = rs.UNIONS["covered"]
UNSEEN_S = rs.UNIONS["fallback"]


def _split(cov: float, unseen: float) -> dict:
    """A per-stratum rate dict: one rate on the three covered strata, another on the three unseen."""
    return {**{s: cov for s in COVERED_S}, **{s: unseen for s in UNSEEN_S}}


def _flat(rate: float) -> dict:
    return {s: rate for s in rs.STRATA}


def test_labels_are_mechanical():
    kw = dict(n_boot=200, budgets=(16,))
    # A: COVERED-MATERIAL / PT-SURVIVES (every other arm at the 0.80 default, so free_bigram_pt is 0.80 on all)
    a = {"history_tok": _split(0.92, 0.95), "free_bigram_b": _split(0.85, 0.70),
         "history_tok_pt": _flat(0.88), "history_bigram_pt": _flat(0.90)}
    rows = _rows(a)
    lab = rs.conclude(rows, "prev_table", _twin_of(rows), **kw)["labels"]
    assert lab["reproduce"]["status"] == "EXACT" and lab["reproduce_status"] == "EXACT" and lab["void"] is False
    assert lab["label"] == "COVERED-MATERIAL / PT-SURVIVES" and lab["q1"] == "COVERED-MATERIAL" and lab["q2"] == "PT-SURVIVES"
    assert abs(lab["gate_eq_covered"]["delta"] - 0.07) < 1e-9 and lab["gate_eq_covered_reading"] == "SIGNAL"
    assert abs(lab["gate_eq_fallback"]["delta"] - 0.25) < 1e-9
    assert abs(lab["d_eq_pt_all"]["delta"] - 0.08) < 1e-9 and abs(lab["d_add_pt_all"]["delta"] - 0.10) < 1e-9
    assert abs(lab["pt_dilution_anchor"]["delta"] - 0.02) < 1e-9 and lab["pt_inconsistent_cause"] is None
    assert abs(lab["d_pt_all"]["delta"] - ((3 * 0.92 + 3 * 0.95) / 6 - 0.80)) < 1e-9     # the asymmetric read, reported
    assert lab["sentence"].startswith("the coverage caveat on the free-bigram twin is retired")
    assert "the twin's verdict stands at this encoding of p_t" in lab["sentence"]
    assert "(B = 16, j = 1)" in lab["sentence"] and lab["sentence"].count("at this reader") == 2
    assert abs(lab["scopes"]["covered"]["share"] - 0.5) < 1e-12 and abs(lab["scopes"]["fallback"]["share"] - 0.5) < 1e-12
    assert lab["scopes"]["all"]["positions"] == 150            # 6 strata x 2 prompts x 16 gates x 100 trials / (16 x 8)
    assert lab["scopes"]["covered"]["prompts_with_positions"] == 2
    # the other encoding flips which free arm the deltas read
    lab2 = rs.conclude(rows, "cur_table_at_prev", _twin_of(rows), **kw)["labels"]
    assert lab2["free_bigram_arm"] == "free_bigram_a" and abs(lab2["gate_eq_covered"]["delta"] - 0.12) < 1e-9
    # B: FALLBACK-LOCATED / PT-ABSORBS (covered D_eq +0.03 is CI-positive below the floor: NOT-SHOWN, in the frozen words)
    b = {"history_tok": _split(0.90, 0.95), "free_bigram_b": _split(0.87, 0.70),
         "history_tok_pt": _flat(0.82), "history_bigram_pt": _flat(0.83)}
    rows = _rows(b)
    lab = rs.conclude(rows, "prev_table", _twin_of(rows), **kw)["labels"]
    assert lab["label"] == "FALLBACK-LOCATED / PT-ABSORBS"
    assert lab["gate_eq_covered_reading"] == "NOT-SHOWN" and lab["gate_eq_covered"]["lo"] > 0
    assert lab["gate_eq_fallback_reading"] == "SIGNAL"
    assert lab["d_eq_pt_all_reading"] == "NOT-SHOWN" and lab["d_add_pt_all_reading"] == "NOT-SHOWN"
    assert lab["sentence"].startswith("the material part of the surviving pooled margin is located on the positions with at least one unseen key")
    assert "no material margin (at or above +0.05)" in lab["sentence"]
    assert "no better" not in lab["sentence"] and "reproduced" not in lab["sentence"] and "accounted" not in lab["sentence"]
    assert "any informative block" not in lab["sentence"] and "coverage effect" not in lab["sentence"]
    # C: UNLOCATED (neither scope SIGNAL) / PT-COMPLEMENTARY (only the union adds)
    c = {"history_tok": _flat(0.90), "free_bigram_b": _flat(0.87), "history_tok_pt": _flat(0.82), "history_bigram_pt": _flat(0.90)}
    rows = _rows(c)
    lab = rs.conclude(rows, "prev_table", _twin_of(rows), **kw)["labels"]
    assert lab["q1"] == "UNLOCATED" and lab["q2"] == "PT-COMPLEMENTARY" and lab["label"] == "UNLOCATED / PT-COMPLEMENTARY"
    assert lab["sentence"].startswith("this split does not locate the surviving margin")
    assert "while the address stream adds a material margin over the free bigram plus the summaries" in lab["sentence"]
    # D: a NEGATIVE covered D_eq is "not SIGNAL", routes by the fallback reading, and is said in words
    d = {"history_tok": _split(0.80, 0.95), "free_bigram_b": _split(0.90, 0.70)}
    rows = _rows(d)
    lab = rs.conclude(rows, "prev_table", _twin_of(rows), **kw)["labels"]
    assert lab["gate_eq_covered_reading"] == "NEGATIVE" and lab["covered_negative"] is True and lab["q1"] == "FALLBACK-LOCATED"
    assert lab["sentence"].startswith("the address block reads below the equal-dims free bigram block")
    # E: PT-INCONSISTENT with the two pinned causes: the anchor CI-clear negative ("reader") or not ("floor straddle")
    e = {"history_tok_pt": _flat(0.88), "history_bigram_pt": _flat(0.84)}
    rows = _rows(e)
    lab = rs.conclude(rows, "prev_table", _twin_of(rows), **kw)["labels"]
    assert lab["q2"] == "PT-INCONSISTENT" and lab["pt_inconsistent_cause"] == "reader" and lab["pt_dilution_anchor"]["hi"] < 0
    assert "no sentence on the twin's verdict is written" in lab["sentence"]
    rows = _rows({"history_tok_pt": _flat(0.88), "history_bigram_pt": _flat(0.80)}, prompts=(0,)) + \
        _rows({"history_tok_pt": _flat(0.86), "history_bigram_pt": _flat(0.87)}, prompts=(1,))
    lab = rs.conclude(rows, "prev_table", _twin_of(rows), **kw)["labels"]
    assert lab["d_eq_pt_all_reading"] == "SIGNAL" and lab["d_add_pt_all_reading"] == "NOT-SHOWN"
    assert lab["q2"] == "PT-INCONSISTENT" and lab["pt_inconsistent_cause"] == "floor straddle"
    # floor straddles: per-prompt covered deltas 0.07 / 0.03 and equal-dims PT deltas 0.07 / 0.03 -> both CIs contain +0.05,
    # the readings follow the rule and the sentences claim "not settled at this power"
    rows = _rows(a, prompts=(0,)) + _rows({"history_tok": _split(0.88, 0.95), "free_bigram_b": _split(0.85, 0.70),
                                           "history_tok_pt": _flat(0.83), "history_bigram_pt": _flat(0.90)}, prompts=(1,))
    lab = rs.conclude(rows, "prev_table", _twin_of(rows), **kw)["labels"]
    assert abs(lab["gate_eq_covered"]["delta"] - 0.05) < 1e-9 and lab["covered_floor_straddle"] is True
    assert lab["q1"] == "COVERED-MATERIAL" and "the coverage caveat is not retired at this power" in lab["sentence"]
    assert lab["d_eq_pt_floor_straddle"] is True and lab["q2_floor_straddle"] is True and lab["q2"] == "PT-SURVIVES"
    assert "the twin's verdict with p_t is not settled at this power" in lab["sentence"]
    assert "retired at this encoding" not in lab["sentence"] and "the twin's verdict stands" not in lab["sentence"]
    assert lab["d_add_pt_floor_straddle"] is False and lab["fallback_floor_straddle"] is False
    # a straddle on the UNION reading alone also selects the "not settled" variant (the PT-ABSORBS strike needs both CIs
    # clear of the floor), and a straddle on the Q1 branch reading is said in words
    rows = _rows({"history_tok": _split(0.92, 0.95), "free_bigram_b": _split(0.85, 0.80), "history_tok_pt": _flat(0.90),
                  "history_bigram_pt": _flat(0.83)}, prompts=(0,)) + \
        _rows({"history_tok": _split(0.92, 0.85), "free_bigram_b": _split(0.85, 0.80), "history_tok_pt": _flat(0.90),
               "history_bigram_pt": _flat(0.87)}, prompts=(1,))
    lab = rs.conclude(rows, "prev_table", _twin_of(rows), **kw)["labels"]
    assert lab["d_eq_pt_floor_straddle"] is False and lab["d_add_pt_floor_straddle"] is True and lab["q2_floor_straddle"] is True
    assert lab["q2"] == "PT-SURVIVES" and "both Q2 readings are SIGNAL by the rule while at least one CI95 straddles" in lab["sentence"]
    assert lab["q1"] == "COVERED-MATERIAL" and lab["covered_floor_straddle"] is False
    assert abs(lab["gate_eq_fallback"]["delta"] - 0.10) < 1e-9 and lab["fallback_floor_straddle"] is True
    assert "the unseen-key reading's CI95 straddles the +0.05 floor" in lab["sentence"]
    # PT-ABSORBS with the union reading straddling: the sentence claims nothing (no stage-2 strike wording)
    rows = _rows({"history_tok_pt": _flat(0.84), "history_bigram_pt": _flat(0.82)}, prompts=(0,)) + \
        _rows({"history_tok_pt": _flat(0.84), "history_bigram_pt": _flat(0.87)}, prompts=(1,))
    lab = rs.conclude(rows, "prev_table", _twin_of(rows), **kw)["labels"]
    assert abs(lab["d_add_pt_all"]["delta"] - 0.045) < 1e-9 and lab["d_add_pt_all_reading"] == "NOT-SHOWN"
    assert lab["q2"] == "PT-ABSORBS" and lab["d_add_pt_floor_straddle"] is True and lab["q2_floor_straddle"] is True
    assert "neither Q2 reading is SIGNAL by the rule while at least one CI95 straddles" in lab["sentence"]
    assert "none of the address stream over the free bigram plus the summaries" not in lab["sentence"]
    # no twin (smoke / test): REPRODUCE not applicable, never INVALID
    rows = _rows(a)
    lab = rs.conclude(rows, "prev_table", None, **kw)["labels"]
    assert lab["reproduce"] is None and lab["reproduce_ok"] is None and lab["label"] == "COVERED-MATERIAL / PT-SURVIVES"
    # REPRODUCE-INVALID: the twin rows differ in needed; the payload is void and carries numbers only
    twin = _twin_of(rows); twin[0] = dict(twin[0], needed=twin[0]["needed"] + 1)
    out = rs.conclude(rows, "prev_table", twin, **kw)
    lab = out["labels"]
    assert lab["reproduce_status"] == "INVALID" and lab["label"] == "REPRODUCE-INVALID" and lab["void"] is True
    assert lab["q1"] is None and lab["q2"] is None and lab["gate_eq_covered_reading"] is None and lab["d_eq_pt_readings"] is None
    assert lab["covered_negative"] is None and lab["pt_inconsistent_cause"] is None
    assert lab["gate_eq_covered"]["delta"] is not None and "gate_eq|B=16|covered" in out["deltas"]
    assert lab["sentence"].startswith("the stratified rows do not reproduce")
    # the identity check against the twin's committed D_eq: EXACT rows whose pooled D_eq is not the twin's are void too
    ide = rs.conclude(rows, "prev_table", _twin_of(rows), **kw)["deltas"]["gate_eq|B=16|all"]
    ok = rs.conclude(rows, "prev_table", _twin_of(rows), twin_gate_eq=ide, **kw)["labels"]
    assert ok["all_gate_eq_matches_twin"] is True and ok["reproduce_status"] == "EXACT"
    off = rs.conclude(rows, "prev_table", _twin_of(rows), twin_gate_eq=dict(ide, delta=ide["delta"] + 1e-6), **kw)["labels"]
    assert off["all_gate_eq_matches_twin"] is False and off["reproduce"]["status"] == "EXACT"
    assert off["reproduce_status"] == "INVALID" and off["label"] == "REPRODUCE-INVALID" and off["void"] is True
    # INCOMPLETE: a missing registered arm, or a missing label cell (no fallback positions at all)
    lab = rs.conclude([r for r in rows if r["arm"] != "pt_only"], "prev_table", None, **kw)["labels"]
    assert lab["label"] == "INCOMPLETE" and lab["missing_arms"] == ["pt_only"] and lab["q1"] is None and lab["void"] is True
    lab = rs.conclude([r for r in rows if r["stratum"] in COVERED_S], "prev_table", None, **kw)["labels"]
    assert lab["label"] == "INCOMPLETE" and lab["missing_label_cells"] == ["gate_eq|B=16|fallback"]
    with pytest.raises(SystemExit, match="unknown encoding"):
        rs.conclude(rows, "trigram", None, **kw)
    with pytest.raises(SystemExit, match="unknown stratum"):
        rs.conclude([dict(rows[0], stratum="covered")] + rows[1:], "prev_table", None, **kw)   # a union is not a stratum


def test_pairing_is_refused_within_a_scope():
    rows = _rows({})
    bad = [r for r in rows if not (r["arm"] == "history_all" and r["prompt_idx"] == 1 and r["stratum"] == "both_unseen")]
    with pytest.raises(SystemExit, match="pairing violated: history_all"):
        rs.conclude(bad, "prev_table", None, n_boot=50, budgets=(16,))
    bad2 = [dict(r, needed=(r["needed"] + 1 if r["arm"] == "pt_only" and r["stratum"] == "covered_5p" else r["needed"]))
            for r in rows]
    with pytest.raises(SystemExit, match="pairing violated: pt_only"):
        rs.conclude(bad2, "prev_table", None, n_boot=50, budgets=(16,))


# ---------------------------------------------------------------------------
# guards, the twin reference, exact recompute and its refusals
# ---------------------------------------------------------------------------

def test_guards_under_results(tmp_path, monkeypatch):
    d, b, g = _unseen_harvest(tmp_path, rule="random", R=21, seed=12)
    with pytest.raises(SystemExit, match="may not write under results/"):
        rs.run(_args(d, b, g, ROOT / "results" / "smoke" / "x.json", only_seeds="0"))
    with pytest.raises(SystemExit, match="lambda grid"):
        rs.run(_args(d, b, g, ROOT / "results" / "smoke" / "y.json", lambdas=FAST))
    monkeypatch.setattr(rs.pr, "_under_results", lambda p: True)        # results/ membership stubbed; nothing written there
    with pytest.raises(SystemExit, match="must be results/real/prefetch_strat_s3.json"):
        rs.run(_args(d, b, g, tmp_path / "wrong_name.json", lambdas=None))
    out = tmp_path / "prefetch_strat_s3.json"
    state = Path(str(out) + ".state.jsonl"); state.write_text("x")
    with pytest.raises(SystemExit, match="state.jsonl exists: a registered payload is never overwritten"):
        rs.run(_args(d, b, g, out, lambdas=None))
    state.unlink()
    meta = tmp_path / "prefetch_strat_s3.meta.json"; meta.write_text("x")
    with pytest.raises(SystemExit, match="meta.json exists: a registered payload is never overwritten"):
        rs.run(_args(d, b, g, out, lambdas=None))
    meta.unlink()
    # --twin none is refused under results/; the twin must be the registered one for the harvest there
    monkeypatch.setattr(rs, "ROOT", tmp_path / "scratch_root")
    (tmp_path / "scratch_root" / "results" / "real").mkdir(parents=True)
    out = tmp_path / "scratch_root" / "results" / "real" / "prefetch_strat_s3.json"
    with pytest.raises(SystemExit, match="twin none is refused under results/"):
        rs.run(_args(d, b, g, out, lambdas=None, twin="none"))
    with pytest.raises(SystemExit, match="must be the registered one for this harvest"):
        rs.run(_args(d, b, g, out, lambdas=None, twin=str(tmp_path / "elsewhere.json")))
    with pytest.raises(SystemExit, match="not found"):
        rs.run(_args(d, b, g, out, lambdas=None, twin=None))
    monkeypatch.undo()
    assert rs.OUT_OF_HARVEST == {"harvest_moe": "prefetch_strat_s3.json", "harvest_moe_r": "prefetch_strat_s3_r.json"}
    assert rs.TWIN_OF_HARVEST == {"harvest_moe": "prefetch_bigram_s3.json", "harvest_moe_r": "prefetch_bigram_s3_r.json"}


def test_twin_reference_reading(tmp_path):
    d, b, g = _unseen_harvest(tmp_path, rule="random", R=21, seed=13)
    other = tmp_path / "other.json"; other.write_text(json.dumps({"registered": "x"}))
    with pytest.raises(SystemExit, match="not a free-bigram twin payload"):
        rs.read_twin(other)
    # a twin payload not written by the frozen twin (its attested sha differs) is refused before its rows are read
    forged = tmp_path / "forged.json"
    forged.write_text(json.dumps({"registered": rb.REGISTERED, "provenance": {"instrument_sha256": "0" * 64}, "n_state_rows": 0}))
    with pytest.raises(SystemExit, match="not written by the frozen twin"):
        rs.read_twin(forged)
    twin_out = tmp_path / "twin.json"
    tp = rb.run(_twin_args(d, b, g, twin_out))
    tw = rs.read_twin(twin_out)
    assert tw["encoding"] == tp["provenance"]["encoding_selected"] and tw["n_state_rows"] == tp["n_state_rows"]
    assert tw["gate_eq"] == tp["conclusion"]["deltas"]["gate_eq|B=16"] and len(tw["_rows"]) == tp["n_state_rows"]
    assert tw["sha256"] == _sha(twin_out) and "\\" not in tw["path"]
    # outside results/: an explicit missing twin is refused, an unknown harvest without --twin reads none, a smoke never reads one
    with pytest.raises(SystemExit, match="not found"):
        rs.twin_reference(d, str(tmp_path / "nope.json"), smoke=False, out_under_results=False)
    assert rs.twin_reference(tmp_path / "harvest_other", None, smoke=False, out_under_results=False) is None
    with pytest.raises(SystemExit, match="no committed twin payload is known"):
        rs.twin_reference(tmp_path / "harvest_other", None, smoke=False, out_under_results=True)
    assert rs.twin_reference(d, str(twin_out), smoke=True, out_under_results=False) is None
    # a twin read on other shards than this run opens is refused
    (tmp_path / "second").mkdir()
    d2, b2, g2 = _unseen_harvest(tmp_path / "second", rule="random", R=21, seed=14)
    with pytest.raises(SystemExit, match="different harvest shards"):
        rs.run(_args(d2, b2, g2, tmp_path / "mismatch.json", twin=str(twin_out)))
    # a twin whose state file is missing is refused
    Path(str(twin_out) + ".state.jsonl").unlink()
    with pytest.raises(SystemExit, match="twin state file"):
        rs.read_twin(twin_out)


def test_conclude_from_refusals(tmp_path):
    d, b, g = _unseen_harvest(tmp_path, rule="token", R=21, T=14, seed=6)
    twin_out = tmp_path / "twin.json"
    rb.run(_twin_args(d, b, g, twin_out, lambdas=FAST))
    out = tmp_path / "strat.json"
    payload = rs.run(_args(d, b, g, out, lambdas=FAST, twin=str(twin_out)))
    rs.conclude_from(out)                                                 # clean
    state = Path(str(out) + ".state.jsonl")
    lines = state.read_text(encoding="utf-8").splitlines()
    header = json.loads(lines[0])

    def write_header(h):
        state.write_text("\n".join([json.dumps(h)] + lines[1:]) + "\n", encoding="utf-8")

    # (1) the header's encoding flipped alone
    write_header(dict(header, encoding=rb.other_encoding(header["encoding"])))
    with pytest.raises(SystemExit, match="encoding differs from the payload's"):
        rs.conclude_from(out)
    # (2) a lambda flipped in the header alone
    lam = dict(header["lambda_selected"]); lam["pt_only"] = 12345.0
    write_header(dict(header, lambda_selected=lam))
    with pytest.raises(SystemExit, match="lambdas differ from the payload's"):
        rs.conclude_from(out)
    # (3) a twin reference changed in the header alone
    tw = dict(header["twin"]); tw["sha256"] = "0" * 64
    write_header(dict(header, twin=tw))
    with pytest.raises(SystemExit, match="twin reference differs"):
        rs.conclude_from(out)
    # (4) a CONSISTENT flip of a PT lambda in header and payload is refused: the val table re-selects it
    write_header(header)
    p2 = json.loads(out.read_text(encoding="utf-8"))
    other_lam = [x for x in p2["provenance"]["constants"]["lambdas"] if x != p2["provenance"]["lambda_selected"]["pt_only"]][0]
    p2["provenance"]["lambda_selected"]["pt_only"] = other_lam
    h2 = dict(header); h2["lambda_selected"] = dict(p2["provenance"]["lambda_selected"])
    write_header(h2); out.write_text(json.dumps(p2), encoding="utf-8")
    with pytest.raises(SystemExit, match="not the one its val table selects"):
        rs.conclude_from(out)
    write_header(header); out.write_text(json.dumps(payload), encoding="utf-8")
    # (5) a tampered stratified row
    row = json.loads(lines[1]); row["hits"] = max(0, row["hits"] - 1)
    state.write_text("\n".join([lines[0], json.dumps(row)] + lines[2:]) + "\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="RECOMPUTE MISMATCH"):
        rs.conclude_from(out)
    write_header(header)
    # (5b) a twin record that header and payload agree on but that differs from the twin on disk beyond the shas
    tw5 = dict(header["twin"]); tw5["git_commit"] = "deadbeef"
    p5 = json.loads(out.read_text(encoding="utf-8")); p5["provenance"]["twin"] = tw5
    write_header(dict(header, twin=tw5)); out.write_text(json.dumps(p5), encoding="utf-8")
    with pytest.raises(SystemExit, match="beyond the shas"):
        rs.conclude_from(out)
    write_header(header); out.write_text(json.dumps(payload), encoding="utf-8")
    # (6) the twin's state file on disk changed: refused by sha before any recompute
    tstate = Path(str(twin_out) + ".state.jsonl")
    tb = tstate.read_bytes(); tstate.write_bytes(tb + b"\n")
    with pytest.raises(SystemExit, match="is not the one this run read"):
        rs.conclude_from(out)
    tstate.write_bytes(tb)
    rs.conclude_from(out)
    # (7) the twin payload absent: REPRODUCE cannot be recomputed, so the recompute refuses
    twin_out.rename(tmp_path / "moved.json")
    with pytest.raises(SystemExit, match="REPRODUCE cannot be recomputed"):
        rs.conclude_from(out)
    # (8) a non-strat payload
    with pytest.raises(SystemExit, match="not a stratified coverage read payload"):
        rs.conclude_from(tmp_path / "moved.json")


def test_arm_cols_and_dims():
    for enc in rb.ENCODINGS:
        assert rs.arm_dims("pt_only", enc) == 82 and rs.arm_dims("free_bigram_pt", enc) == rs.arm_dims("history_tok_pt", enc) == 2130
        assert rs.arm_dims("history_bigram_pt", enc) == 3154
        for arm in rs.ARMS_TWIN:
            assert np.array_equal(rs.arm_cols(arm, enc), rb.arm_cols(arm))
        cols = rs.arm_cols("free_bigram_pt", enc)
        prev = rb.BLOCKS["prev_" + rb.ENC_SUFFIX[enc]]
        assert np.array_equal(cols, np.r_[np.arange(*rb.BLOCKS["cur"]), np.arange(*prev), rs.BIAS_COL, rs.PT_COLS])
    assert rs.D_X == rb.D_X + rs.D_PT == 4178 and rs.BIAS_COL == 4096 and rs.PT_COLS[0] == 4097 and rs.PT_COLS[-1] == 4177
    assert np.array_equal(rs.arm_cols("pt_only", "prev_table"), np.r_[rs.BIAS_COL, rs.PT_COLS])
    assert np.array_equal(rs.arm_cols("history_tok_pt", "prev_table")[:-rs.D_PT - 1], np.arange(0, 2 * rb.D))
    with pytest.raises(SystemExit, match="unknown encoding"):
        rs.arm_cols("pt_only", "trigram")
    assert rs.STRATA == ("covered_1", "covered_2_4", "covered_5p", "cur_unseen", "prev_unseen", "both_unseen")
    assert rs.UNIONS["covered"] == ("covered_1", "covered_2_4", "covered_5p")
    assert rs.UNIONS["fallback"] == ("cur_unseen", "prev_unseen", "both_unseen") and rs.UNIONS["all"] == rs.STRATA
    assert rs.COUNTS_PER_OCCURRENCE == L * K == 128
    assert rs.LABEL_CELLS == ("gate_eq|B=16|covered", "gate_eq|B=16|fallback", "d_eq_pt|B=16|all", "d_add_pt|B=16|all")
    assert rs.ARMS_REQUIRED == rb.ARMS_REQUIRED + ("pt_only", "free_bigram_pt", "history_tok_pt", "history_bigram_pt")


def test_tool_imports_no_torch():
    code = ("import sys; sys.path.insert(0, r'%s'); import run_prefetch_strat; "
            "print('torch' in sys.modules)" % str(ROOT / "tools"))
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)
    assert out.stdout.strip() == "False"
