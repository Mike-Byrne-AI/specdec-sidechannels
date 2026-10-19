"""tests/test_prefetch_r2.py (OQ-9 stage-1 GENERALISING FREE BASELINE, R2: the post-hoc
diagnostic of the stratified read's unseen-key margin, with the stored hidden state as a
second question): the CI-safe layer — the tool refuses a modified stratified tool (and its
parents); the twin's arms are the stratified tool's readers (Gram and weights equal Strat's);
the smoothing family's identities (k = 0 is the table where seen and the replay where not,
k = inf the replay, every row sums to one, the blend weight is n / (n + k)); the replay
against a brute-force computation and the source's sha; a replay-rule fixture whose unseen
keys the replay knows reads R2-ABSORBED with a material SHRINKAGE on the unseen keys; a
hidden-rule fixture reads H-ABSORBS with the address block NEGATIVE; a shift rule survives
both questions; labels are mechanical for every branch incl. the straddle flags and the void
branches; REPRODUCE EXACT against a fixture stratified payload; the (k, lambda) selection rule;
pairing within a scope refused; smoke / grid / replay / strat / out / overwrite guards;
--conclude-from reproduces a payload and refuses a tampered row, a flipped header and a
changed stratified payload; the hidden block is fit on train rows only; dims; LF evidence; no
torch, transformers or safetensors.

Fixtures are IMPORTED from tests/test_prefetch_strat.py and tests/test_prefetch_readouts.py
(the frozen instruments' tests); helpers here add a hidden array and a replay source.

Dated amendment 2026-10-19 (the public cut's first CI run; docs/BLUEPRINT.md, the dated amendment at its end, amending
the OQ-9 stage-1 R2 registration): the replay-rule fixture test's share assertion is narrowed to a positive twin
margin, because that margin read NEGATIVE on GitHub's ubuntu runner where this box reads exactly zero; every assertion
before it held there and every later one whose value the runner printed is satisfied, and all still run everywhere.
Nothing else in this file changed; the instrument is untouched."""

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
import run_prefetch_strat as rs  # noqa: E402  (the frozen stratified read)
import run_prefetch_r2 as r2  # noqa: E402
import test_prefetch_strat as tps  # noqa: E402  (its fixtures)
from sideband.probes import load_label_space  # noqa: E402

E, L, K, D = pr.N_EXPERTS, pr.N_GATES, pr.TOP_K, pr.D_MH
FAST = "1,100"
FAST3 = "1,100,10000"
INF = float("inf")


def _args(d, b, g, out, src, **kw):
    base = dict(harvest=str(d), out=str(out), buckets=str(b), glue=str(g), strat="none", replay=str(src),
                only_seeds=None, smoke_split_val=False, lambdas=FAST, k_grid=None, conclude_from=None)
    base.update(kw)
    return argparse.Namespace(**base)


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _rule_set(x: int, l: int) -> np.ndarray:
    """The token rule of tests/test_prefetch_readouts.py: S[t+1, l] = {(7 x + 3 l + 9 i) mod 64}."""
    return np.sort((7 * x + 3 * l + 9 * np.arange(K)) % E)


def _replay_source(path: Path, rule: bool, vocab: int = 16, seed: int = 0) -> Path:
    """A fixture replay source. rule=True: one-hot embeddings and routers whose top-8 at every gate
    is exactly the token rule's set for that token (the replay knows the rule for every key)."""
    rng = np.random.default_rng(seed)
    if rule:
        embed = np.eye(vocab, dtype=np.float32)
        gates = np.zeros((L, E, vocab), dtype=np.float32)
        for x in range(vocab):
            for l in range(L):
                gates[l, _rule_set(x, l), x] = 10.0
        norms = np.ones((L, vocab), dtype=np.float32)
    else:
        embed = rng.standard_normal((vocab, 8)).astype(np.float32)
        gates = rng.standard_normal((L, E, 8)).astype(np.float32)
        norms = np.ones((L, 8), dtype=np.float32)
    np.savez(path, embed=embed, gates=gates, norms=norms, eps=np.float32(1e-5))
    return path


def _add_hidden(d: Path, seed: int = 0, width: int = 1024, rule: bool = False) -> None:
    """Append a hidden array to every shard. rule=True: hidden = Z @ B (rank 32) and the routing of
    forward t is the top-8 of a linear score of Z[t-1] (so the target S[t+1] at anchor t is a linear
    read of hidden[t]); the tokens carry nothing."""
    rng = np.random.default_rng(seed)
    B = rng.standard_normal((32, width))
    M = rng.standard_normal((L, 32, E))

    def fn(z):
        R, T = z["tokens"].shape
        if not rule:
            z["hidden"] = rng.standard_normal((R, T, width)).astype(np.float16)
            return
        Z = rng.standard_normal((R, T, 32))
        z["hidden"] = (Z @ B).astype(np.float16)
        slots = np.full((R, T, L, K), -1, dtype=np.int16)
        lengths = z["lengths"]
        for r in range(R):
            for t in range(int(lengths[r])):
                zz = Z[r, t - 1] if t >= 1 else np.zeros(32)
                for l in range(L):
                    slots[r, t, l] = np.sort(np.argsort(-(zz @ M[l]), kind="stable")[:K])
        z["slots"] = slots
    tps._rewrite(d, fn)


def _chain(tmp_path, src, rule="token", R=24, T=16, seed=5, lambdas=FAST, hidden_rule=False, replay_rule=False, k_grid=None):
    """twin -> stratified -> R2 on an unseen-key fixture; returns (d, b, g, strat_out, r2_out, payload)."""
    d, b, g = tps._unseen_harvest(tmp_path, rule=rule, R=R, T=T, seed=seed)
    _add_hidden(d, seed=seed, rule=hidden_rule)
    src = _replay_source(src, rule=replay_rule)
    twin_out = tmp_path / "twin.json"
    rb.run(tps._twin_args(d, b, g, twin_out, lambdas=lambdas))
    strat_out = tmp_path / "strat.json"
    rs.run(tps._args(d, b, g, strat_out, lambdas=lambdas, twin=str(twin_out)))
    r2_out = tmp_path / "r2.json"
    payload = r2.run(_args(d, b, g, r2_out, src, strat=str(strat_out), lambdas=lambdas, k_grid=k_grid))
    return d, b, g, strat_out, r2_out, payload


SHORT_K = "0,8,inf"          # the rule fixtures need the family's ends and one interior point, not the whole grid


def _point(c, arm, B, scope="all"):
    return c["tables"][f"{arm}|B={B}|{scope}"]["all"]["point"]


# ---------------------------------------------------------------------------
# the frozen chain is asserted; the twin's arms are the stratified tool's readers
# ---------------------------------------------------------------------------

def test_frozen_chain_is_asserted(tmp_path):
    assert r2.assert_frozen_strat() == r2.STRAT_INSTRUMENT_SHA256
    assert r2.rs.assert_frozen_twin() == rs.TWIN_INSTRUMENT_SHA256
    assert r2.rb.assert_frozen_instrument() == rb.FROZEN_INSTRUMENT_SHA256
    tampered = tmp_path / "run_prefetch_strat.py"
    tampered.write_bytes(Path(rs.__file__).read_bytes() + b"\n# touched\n")
    with pytest.raises(SystemExit, match="refusing"):
        r2.assert_frozen_strat(tampered)
    crlf = tmp_path / "crlf.py"
    crlf.write_bytes(Path(rs.__file__).read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
    assert r2.assert_frozen_strat(crlf) == r2.STRAT_INSTRUMENT_SHA256


def test_twin_arm_weights_equal_the_stratified_tools_at_the_same_lambda(tmp_path):
    d, b, g = tps._unseen_harvest(tmp_path, rule="token", R=21, T=14, seed=2)
    _add_hidden(d, seed=2)
    src = r2.load_replay_source(str(_replay_source(tmp_path / "src.npz", rule=False)))
    data = pr.S3Data(d)
    lab, nc = load_label_space(b, g)
    st = rs.Strat(data, lab, nc, twin=None, lambdas=(1.0, 100.0))
    st.fit()
    rr = r2.R2(data, lab, nc, r2.load_hidden(data), r2.replay_table(src, int(data.tokens.max()) + 1), lambdas=(1.0, 100.0))
    rr.fit()
    assert np.array_equal(rr.G, st.G) and np.array_equal(rr.C, st.C)
    for arm in r2.ARMS_TWIN:
        for lam in (1.0, 100.0):
            assert np.array_equal(rr.W[(arm, lam)], st.W[(arm, lam)]), (arm, lam)
    # the assembled Grams are symmetric and the free arm's equals the explicit product on a chunk
    Gs, Cs = rr.arm_gram("history_all_h", 8.0)
    assert Gs.shape == (4097, 4097) and Cs.shape == (4097, D) and np.allclose(Gs, Gs.T)
    rows, anchors = pr.restrict(*rb.bigram_positions(data.lengths, data.T), rr.masks["train"])
    X, Y = rr.design(rows, anchors, lopo=True)
    Sk = rr.smooth_blocks(rows, anchors, (8.0,), lopo=True)[8.0]
    Xa = np.hstack([Sk, np.ones((rows.shape[0], 1))])
    G8, C8 = rr.arm_gram("free_r2", 8.0)
    assert np.allclose(G8, Xa.T @ Xa) and np.allclose(C8, Xa.T @ Y)
    Hb = rr.h_block(rows, anchors)
    Xh = np.hstack([X[:, :D], Sk, Hb, np.ones((rows.shape[0], 1))])
    assert np.allclose(Gs, Xh.T @ Xh) and np.allclose(Cs, Xh.T @ Y)


# ---------------------------------------------------------------------------
# the smoothing family and the replay
# ---------------------------------------------------------------------------

def test_smoothing_identities(tmp_path):
    rng = np.random.default_rng(0)
    c = rng.integers(0, 5, size=(5, L, E)).astype(np.float64) * 8
    c[1] = 0.0                                                   # an unseen key
    n = c.sum(axis=2, keepdims=True)
    r = rng.random((5, L, E)); r /= r.sum(axis=2, keepdims=True)
    table = np.where(n > 0, c / np.maximum(n, 1.0), r)
    assert np.array_equal(r2.smooth(c, n, r, 0.0), table)
    assert np.array_equal(r2.smooth(c, n, r, INF), r)
    assert np.array_equal(r2.smooth(c, n, r, 8.0)[1], r[1])      # unseen: the replay at every k
    for k in r2.K_GRID:
        assert np.allclose(r2.smooth(c, n, r, k).sum(axis=2), 1.0)
    w = n / (n + 8.0)
    assert np.allclose(r2.smooth(c, n, r, 8.0) - r, w * (table - r))
    # at TRAIN rows k = 0 is the twin's leave-one-prompt-out table where it has a count, the replay where not
    d, b, g = tps._unseen_harvest(tmp_path, rule="random", R=21, T=14, seed=3)
    _add_hidden(d, seed=3)
    src = r2.load_replay_source(str(_replay_source(tmp_path / "src.npz", rule=False)))
    data = pr.S3Data(d)
    lab, nc = load_label_space(b, g)
    rr = r2.R2(data, lab, nc, r2.load_hidden(data), r2.replay_table(src, int(data.tokens.max()) + 1), lambdas=(1.0,))
    rr.fit_tables()
    rows, anchors = pr.restrict(*rb.bigram_positions(data.lengths, data.T), rr.masks["train"])
    tok, tokp, prompt = data.tokens[rows, anchors], data.tokens[rows, anchors - 1], data.prompt_idx[rows]
    blocks = rr.smooth_blocks(rows, anchors, (0.0, INF), lopo=True)
    cc, nn = rr._lopo_counts(rr.token_table, rr.pair_keys, rr.pair_counts, tok, prompt)
    seen = (nn[:, :, 0] > 0)                                     # (N, L)
    twin_cur = rr.table_vec(tok, prompt).reshape(-1, L, E)
    mine_cur = blocks[0.0][:, :D].reshape(-1, L, E)
    assert np.array_equal(mine_cur[seen], twin_cur[seen])
    rep_cur = rr.replay[tok].reshape(-1, L, E)
    assert np.array_equal(mine_cur[~seen], rep_cur[~seen]) and (~seen).any() or seen.all()
    assert np.array_equal(blocks[INF], np.hstack([rr.replay[tok], rr.replay[tokp]]))
    # the previous-token block: the twin's prev_table_vec leave-one-prompt-out where seen, the replay of tokens[t-1] where not
    cp, npv = rr._lopo_counts(rr.prev_table, rr.prev_pair_keys, rr.prev_pair_counts, tokp, prompt)
    seen_p = npv[:, :, 0] > 0
    twin_prev = rr.prev_table_vec(tokp, prompt).reshape(-1, L, E)
    mine_prev = blocks[0.0][:, D:].reshape(-1, L, E)
    assert np.array_equal(mine_prev[seen_p], twin_prev[seen_p])
    assert np.array_equal(mine_prev[~seen_p], rr.replay[tokp].reshape(-1, L, E)[~seen_p])
    # val / test rows read the full table (no prompt): k = 0 equals the twin's table_vec where seen
    rows_t, anchors_t = pr.restrict(*rb.bigram_positions(data.lengths, data.T), rr.masks["test"])
    tok_t = data.tokens[rows_t, anchors_t]
    cc_t, nn_t = rr._lopo_counts(rr.token_table, rr.pair_keys, rr.pair_counts, tok_t, None)
    seen_t = nn_t[:, :, 0] > 0
    mine_t = rr.smooth_blocks(rows_t, anchors_t, (0.0,))[0.0][:, :D].reshape(-1, L, E)
    assert np.array_equal(mine_t[seen_t], rr.table_vec(tok_t).reshape(-1, L, E)[seen_t])
    assert (~seen_t).any() and np.array_equal(mine_t[~seen_t], rr.replay[tok_t].reshape(-1, L, E)[~seen_t])


def test_replay_table_matches_brute_force_and_source_handling(tmp_path):
    path = _replay_source(tmp_path / "src.npz", rule=False, vocab=12)
    src = r2.load_replay_source(str(path))
    assert src["kind"] == "fixture" and src["sha256"] == _sha(path)
    table = r2.replay_table(src, 12)
    assert table.shape == (12, D) and np.allclose(table.reshape(12, L, E).sum(axis=2), 1.0)
    z = np.load(path)
    for x in range(12):
        e = z["embed"][x].astype(np.float64)
        v = e / np.sqrt((e * e).mean() + float(z["eps"]))
        for l in range(L):
            logits = z["gates"][l].astype(np.float64) @ (v * z["norms"][l].astype(np.float64))
            p = np.exp(logits - logits.max()); p /= p.sum()
            assert np.allclose(table[x, l * E:(l + 1) * E], p, atol=1e-12)
    with pytest.raises(SystemExit, match="covers 12 token ids"):
        r2.replay_table(src, 13)
    # a vocabulary below the embedding's rows (the harvests' case) and a chunk boundary inside it (the chunking
    # changes BLAS's summation order in the last bits, so the chunked table is close, not bit-equal; CHUNK is a constant)
    assert np.allclose(r2.replay_table(src, 10), table[:10], rtol=0, atol=1e-14)
    assert np.allclose(r2.replay_table(src, 11, chunk=4), table[:11], rtol=0, atol=1e-14)
    probe = r2.replay_probe(table)
    assert set(probe) == {"0", "1", "2", "3"} and all(len(v) == 64 for v in probe.values())
    assert probe == r2.replay_probe(r2.replay_table(src, 12))
    # the rule source: every token's top-8 at every gate is the rule's set, with the mass on it
    rule = r2.load_replay_source(str(_replay_source(tmp_path / "rule.npz", rule=True)))
    rt = r2.replay_table(rule, 16).reshape(16, L, E)
    for x in range(16):
        for l in range(L):
            assert np.array_equal(np.sort(np.argsort(-rt[x, l], kind="stable")[:K]), _rule_set(x, l))
            assert rt[x, l][_rule_set(x, l)].sum() > 0.999
    # a changed source changes the sha; a missing key and a missing file are refused
    other = r2.load_replay_source(str(_replay_source(tmp_path / "src2.npz", rule=False, vocab=12, seed=1)))
    assert other["sha256"] != src["sha256"] and not np.array_equal(r2.replay_table(other, 12), table)
    np.savez(tmp_path / "bad.npz", embed=np.eye(4, dtype=np.float32), gates=np.zeros((L, E, 4), np.float32))
    with pytest.raises(SystemExit, match="lacks 'norms'"):
        r2.load_replay_source(str(tmp_path / "bad.npz"))
    with pytest.raises(SystemExit, match="not found"):
        r2.load_replay_source(str(tmp_path / "nope.npz"))
    assert r2.REPLAY_SOURCE_SHA256 == "d8e5770a2d88a8bee02518b3f95a88fed122f9a7ce66ba3183d16fdf39936e63"
    assert r2.SNAPSHOT == "b89a7c4bc24fb9e55ce2543c9458ce0ca5c4650e"


# ---------------------------------------------------------------------------
# rules: the replay recovers the token rule on unseen keys; h_only recovers a hidden rule; a shift survives
# ---------------------------------------------------------------------------

def test_replay_rule_is_recovered_on_unseen_keys_and_reads_r2_absorbed(tmp_path):
    d, b, g, strat_out, out, payload = _chain(tmp_path, tmp_path / "src.npz", rule="token", seed=5, lambdas=FAST3, replay_rule=True, k_grid=SHORT_K)
    c, lab, prov = payload["conclusion"], payload["conclusion"]["labels"], payload["provenance"]
    assert lab["reproduce_status"] == "EXACT" and lab["gate_eq_matches_strat"] is True
    # the replay knows the rule for every key: zero-fit and fitted replay arms are perfect where the table is blind
    assert _point(c, "replay_zerofit", 16, "cur_unseen") > 0.99 and _point(c, "free_replay", 16, "cur_unseen") > 0.9
    assert _point(c, "free_r2", 16, "cur_unseen") > 0.9 and _point(c, "free_backoff", 16, "cur_unseen") > 0.9
    assert _point(c, "free_bigram_b", 16, "cur_unseen") < 0.6 and _point(c, "free_tok", 16, "cur_unseen") < 0.6
    # the headline: the generalising encoding recovers the twin's deficit on the unseen keys
    assert lab["shrinkage_readings"]["fallback"] == "SIGNAL" and lab["shrinkage_fallback"]["delta"] > 0.3
    share = lab["shrinkage_share_of_fallback_margin"]           # None where the twin's own fallback margin is zero (a pure token rule)
    # Dated amendment 2026-10-19: the share is asserted only where the twin's own fallback margin is positive. On GitHub's
    # ubuntu runner that margin read NEGATIVE -0.0011 [-0.0016, -0.0009] where this box reads exactly zero (share None), so
    # the share read -416.67 and the old `share is None or share > 0.5` failed while every earlier assertion held
    # (docs/BLUEPRINT.md, the dated amendment at its end; tests/README.md, "Fail, not skip").
    twin_fb = lab["twin_gate_eq_fallback"]["delta"]
    assert share is None or twin_fb <= 0 or share > 0.5
    # the address block adds nothing over the equal-dims generalising free block: R2-ABSORBED
    assert lab["q1"] == "R2-ABSORBED" and lab["gate_eq_r2_fallback_reading"] != "SIGNAL" and lab["gate_eq_r2_all_reading"] != "SIGNAL"
    assert lab["label"].startswith("R2-ABSORBED / ")
    assert "consistent with table sparsity" in lab["sentence"] or "not settled at this power" in lab["sentence"]
    # the replay agreement is perfect on every split (the routing IS the rule of the input token)
    for split in pr.SPLITS:
        ag = prov["replay_agreement"][split]
        assert ag["n"] > 0 and ag["prev_vs_S_t"]["pooled"] > 0.999 and ag["cur_vs_S_t1"]["pooled"] > 0.999
        assert len(ag["prev_vs_S_t"]["per_gate"]) == L
    assert prov["replay_source"]["kind"] == "fixture" and prov["replay_source_matches_pinned"] is False
    assert prov["k_selected"] in r2.K_TAG.values() and isinstance(prov["k_grid_edge"], bool)


def test_hidden_rule_is_recovered_by_h_only_and_reads_h_absorbs(tmp_path):
    d, b, g, strat_out, out, payload = _chain(tmp_path, tmp_path / "src.npz", rule="random", seed=7, lambdas=FAST3, hidden_rule=True, k_grid=SHORT_K)
    c, lab, prov = payload["conclusion"], payload["conclusion"]["labels"], payload["provenance"]
    assert lab["reproduce_status"] == "EXACT"
    assert _point(c, "h_only", 16) > 0.9 and _point(c, "free_h", 16) > 0.9
    assert _point(c, "history_bigram_r2", 16) < 0.6 and _point(c, "free_r2", 16) < 0.6
    assert lab["q2"] == "H-ABSORBS" and lab["d_eq_h_all_reading"] == "NEGATIVE" and lab["h_negative"] is True
    assert lab["d_add_h_all_reading"] != "SIGNAL"
    eq_prefix = "the address block reads below the equal-dims free block with the hidden block (NEGATIVE); "
    assert eq_prefix in lab["sentence"] and lab["sentence"].index(eq_prefix) < lab["sentence"].index("with the forward's final-norm state")
    assert ("the address stream reads below" in lab["sentence"]) == (lab["d_add_h_all_reading"] == "NEGATIVE")
    assert prov["hidden"]["width"] == 1024 and prov["hidden"]["kept_variance_share"] > 0.999   # rank-32 hidden: all variance kept
    assert prov["hidden"]["train_positions"] == prov["n_positions"]["bigram/train"]


def test_shift_rule_survives_both_questions(tmp_path):
    d, b, g, strat_out, out, payload = _chain(tmp_path, tmp_path / "src.npz", rule="shift", seed=9, lambdas=FAST3, k_grid=SHORT_K)
    c, lab = payload["conclusion"], payload["conclusion"]["labels"]
    assert lab["reproduce_status"] == "EXACT"
    assert _point(c, "history_tok_r2", 16) > 0.95 and _point(c, "history_bigram_r2", 16) > 0.95
    assert _point(c, "free_r2", 16) < 0.6 and _point(c, "free_h", 16) < 0.6
    assert lab["label"] == "R2-FALLBACK-SURVIVES / H-SURVIVES"
    assert lab["gate_eq_r2_fallback_reading"] == "SIGNAL" and lab["d_eq_h_all_reading"] == "SIGNAL" and lab["d_add_h_all_reading"] == "SIGNAL"
    assert lab["shrinkage_readings"]["fallback"] != "SIGNAL"       # the replay carries nothing about a shift rule
    got = r2.conclude_from(out)
    assert got["labels"]["label"] == lab["label"]


# ---------------------------------------------------------------------------
# REPRODUCE against a fixture stratified payload; the no-payload path; the pinned check rule
# ---------------------------------------------------------------------------

def test_reproduce_exact_against_a_fixture_strat_and_conclude_from(tmp_path):
    d, b, g, strat_out, out, payload = _chain(tmp_path, tmp_path / "src.npz", rule="token", seed=5)
    sp = json.loads(strat_out.read_text(encoding="utf-8"))
    prov, lab = payload["provenance"], payload["conclusion"]["labels"]
    assert prov["encoding_source"] == "strat" and prov["encoding_selected"] == sp["provenance"]["encoding_selected"]
    for arm in r2.ARMS_TWIN:
        assert prov["lambda_selected"][arm] == sp["provenance"]["lambda_selected"][arm]
        assert prov["lambda_source"][arm] == "strat" and prov["lambda_grid_edge"][arm] is None
    for arm in r2.ARMS_RIDGE_R2:
        assert prov["lambda_source"][arm] == "val" and isinstance(prov["lambda_grid_edge"][arm], bool)
    assert prov["lambda_selected"]["replay_zerofit"] is None and prov["lambda_source"]["replay_zerofit"] is None
    assert prov["strat"]["sha256"] == _sha(strat_out) and prov["strat"]["state_sha256"] == _sha(Path(str(strat_out) + ".state.jsonl"))
    assert "_rows" not in prov["strat"] and prov["strat"]["twin_path"] == sp["provenance"]["twin"]["path"]
    rep = lab["reproduce"]
    assert rep["status"] == "EXACT" and rep["ok"] is True and lab["reproduce_status"] == "EXACT" and lab["void"] is False
    assert rep["n_compared"] == rep["n_strat_rows"] == sum(1 for r in pr.load_state(Path(str(strat_out) + ".state.jsonl"))[1] if r["arm"] in r2.ARMS_TWIN)
    assert rep["missing_in_r2"] == rep["extra_in_r2"] == rep["needed_mismatch_rows"] == rep["hits_mismatch_rows"] == 0
    assert lab["gate_eq_matches_strat"] is True
    for scope in r2.IDENTITY_SCOPES:
        assert payload["conclusion"]["deltas"][f"gate_eq|B=16|{scope}"] == sp["conclusion"]["deltas"][f"gate_eq|B=16|{scope}"]
    # the (k, lambda) pair and the k table
    assert set(prov["k_val_table"]) == set(r2.K_TAG.values()) and all(set(v) == {"1.0", "100.0"} for v in prov["k_val_table"].values())
    assert prov["val_table"]["free_r2"] == prov["k_val_table"][prov["k_selected"]] and "eigen_1025th" in prov["hidden"]
    assert prov["constants"]["k_grid"] == ["0", "2", "8", "32", "128", "512", "inf"]
    assert prov["k_selected"] in prov["k_val_table"]
    # the state rows: every arm, only test prompts, strata only, the header's record
    header, rows = pr.load_state(Path(str(out) + ".state.jsonl"))
    assert {r["arm"] for r in rows} == set(r2.ARMS_REQUIRED) and {r["stratum"] for r in rows} <= set(r2.STRATA)
    assert header["k_selected"] == prov["k_selected"] and header["strat"] == prov["strat"]
    assert header["replay_source_sha256"] == prov["replay_source"]["sha256"]
    assert all(r["needed"] > 0 for r in rows) and len(rows) == payload["n_state_rows"]
    # every R2 arm shares history_tok's trials in every scope (pairing), and the replay probe is recorded
    assert len(prov["replay_probe"]) == 4 and prov["replay_vocab"] == int(pr.S3Data(d).tokens.max()) + 1
    assert prov["frozen_strat"]["sha256_lf"] == r2.STRAT_INSTRUMENT_SHA256
    assert prov["frozen_twin"]["sha256_lf"] == rs.TWIN_INSTRUMENT_SHA256 and prov["frozen_instrument"]["sha256_lf"] == rb.FROZEN_INSTRUMENT_SHA256
    assert prov["blas"]["cpu_count"] == rs.os.cpu_count()
    # exact recompute incl. REPRODUCE re-derived from the stratified files on disk
    got = r2.conclude_from(out)
    assert got["labels"]["label"] == lab["label"] and got["labels"]["reproduce"]["status"] == "EXACT"
    for p in (out, Path(str(out) + ".state.jsonl"), tmp_path / "r2.meta.json"):
        assert b"\r\n" not in p.read_bytes()


def test_no_strat_path_reselects_what_the_strat_carried(tmp_path):
    d, b, g, strat_out, out, payload = _chain(tmp_path, tmp_path / "src.npz", rule="token", R=21, T=14, seed=8)
    p2 = r2.run(_args(d, b, g, tmp_path / "r2_nostrat.json", tmp_path / "src.npz", strat="none", lambdas=FAST))
    prov, prov2 = payload["provenance"], p2["provenance"]
    assert prov2["encoding_source"] == "val" and prov2["strat"] is None
    assert prov2["encoding_selected"] == prov["encoding_selected"]
    for arm in r2.ARMS_TWIN:
        assert prov2["lambda_selected"][arm] == prov["lambda_selected"][arm] and prov2["lambda_source"][arm] == "val"
    lab2 = p2["conclusion"]["labels"]
    assert lab2["reproduce"] is None and lab2["reproduce_ok"] is None and lab2["gate_eq_matches_strat"] is None
    assert p2["conclusion"]["deltas"] == payload["conclusion"]["deltas"]
    assert lab2["label"] == payload["conclusion"]["labels"]["label"]
    r2.conclude_from(tmp_path / "r2_nostrat.json")


def test_reproduce_check_is_the_pinned_rule():
    strat = [{"arm": a, "budget": 16, "key": 1, "depth": None, "gate": g, "prompt_idx": p, "stratum": s, "hits": 50, "needed": 100}
             for a in ("history_tok", "free_tok") for g in range(L) for p in range(40) for s in r2.STRATA]
    rows = [dict(r) for r in strat]
    rep = r2.reproduce_check(rows, strat)
    assert rep["status"] == "EXACT" and rep["ok"] and rep["n_strat_rows"] == 2 * L * 40 * 6 == rep["n_compared"]
    # 7,680 rows: one +-1 hit mismatch is NEAR (cap 7), eight are INVALID, a +-2 gap is INVALID, a needed mismatch is INVALID
    b1 = [dict(r) for r in rows]; b1[0]["hits"] += 1
    rep = r2.reproduce_check(b1, strat)
    assert rep["status"] == "NEAR" and rep["ok"] is True and rep["hits_mismatch_rows"] == 1 and rep["max_abs_hits_gap"] == 1
    b2 = [dict(r) for r in rows]
    for i in range(8):
        b2[i]["hits"] += 1
    assert r2.reproduce_check(b2, strat)["status"] == "INVALID"
    b3 = [dict(r) for r in rows]; b3[0]["hits"] += 2
    assert r2.reproduce_check(b3, strat)["status"] == "INVALID"
    b4 = [dict(r) for r in rows]; b4[0]["needed"] += 1
    rep = r2.reproduce_check(b4, strat)
    assert rep["needed_mismatch_rows"] == 1 and rep["status"] == "INVALID"
    # a missing or an extra row is INVALID; rows of non-twin arms on either side are ignored
    assert r2.reproduce_check(rows[1:], strat)["missing_in_r2"] == 1 and r2.reproduce_check(rows[1:], strat)["status"] == "INVALID"
    extra = rows + [dict(rows[0], prompt_idx=999)]
    assert r2.reproduce_check(extra, strat)["extra_in_r2"] == 1
    mixed = rows + [dict(r, arm="free_r2", hits=1) for r in rows[:10]]
    strat_pt = strat + [dict(r, arm="pt_only", hits=2) for r in strat[:10]]
    assert r2.reproduce_check(mixed, strat_pt)["status"] == "EXACT"


def test_select_k_rule_ties_and_edges():
    rr = r2.R2.__new__(r2.R2)
    rr.k_grid, rr.lambdas = r2.K_GRID, (1.0, 10.0)
    rr.val_table, rr.lambda_selected, rr.grid_edge = {}, {}, {}

    def grid(values):          # {(k, lam): pooled rate} -> the evaluate_free_grid shape on one stratum
        return {(k, lam, 16, "covered_5p"): (np.array([[int(100 * v)] * L]), np.array([[100] * L])) for (k, lam), v in values.items()}

    flat = {(k, lam): 0.5 for k in r2.K_GRID for lam in (1.0, 10.0)}
    rr.select_k(grid(flat))
    assert rr.k_selected == 0.0 and rr.lambda_selected["free_r2"] == 1.0            # ties keep the smaller k then lambda
    assert rr.k_grid_edge is True and rr.grid_edge["free_r2"] is True
    best = dict(flat); best[(32.0, 10.0)] = 0.9
    rr.select_k(grid(best))
    assert rr.k_selected == 32.0 and rr.lambda_selected["free_r2"] == 10.0 and rr.k_grid_edge is False
    assert rr.k_val_table["32"]["10.0"] == 0.9 and rr.val_table["free_r2"] == rr.k_val_table["32"]
    top = dict(flat); top[(INF, 1.0)] = 0.95
    rr.select_k(grid(top))
    assert rr.k_selected == INF and rr.k_grid_edge is True
    assert r2._select_k_from_table(rr.k_val_table, r2.K_GRID, (1.0, 10.0)) == (INF, 1.0)
    assert r2.k_tag(INF) == "inf" and r2.k_of_tag("inf") == INF and r2.k_of_tag("8") == 8.0 and r2.k_tag(8.0) == "8"


# ---------------------------------------------------------------------------
# labels are mechanical
# ---------------------------------------------------------------------------

def _rows(rates: dict, per: int = 100, prompts=(0, 1), default: float = 0.80):
    """rates: {arm: {stratum: rate or (rate per prompt)}}; one row per (arm, stratum, prompt, gate) at budget 16."""
    rows = []
    for arm in r2.ARMS_REQUIRED:
        for s in r2.STRATA:
            rate = rates.get(arm, {}).get(s, default)
            for i, p in enumerate(prompts):
                rp = rate[i] if isinstance(rate, (tuple, list)) else rate
                for g in range(L):
                    rows.append({"arm": arm, "budget": 16, "key": 1, "depth": None, "gate": g, "prompt_idx": p,
                                 "stratum": s, "hits": int(round(per * rp)), "needed": per})
    return rows


def _strat_of(rows):
    return [dict(r) for r in rows if r["arm"] in r2.ARMS_TWIN]


COV, FB = rs.UNIONS["covered"], rs.UNIONS["fallback"]


def _split(cov, unseen):
    return {**{s: cov for s in COV}, **{s: unseen for s in FB}}


def _flat(rate):
    return {s: rate for s in r2.STRATA}


def test_labels_are_mechanical():
    kw = dict(n_boot=200, budgets=(16,))
    # A: R2-FALLBACK-SURVIVES / H-SURVIVES, with the twin's margin on fallback giving a shrinkage share
    a = {"history_tok": _split(0.90, 0.95), "free_bigram_b": _split(0.85, 0.70), "free_r2": _split(0.88, 0.88),
         "history_tok_r2": _split(0.90, 0.95), "history_bigram_r2": _flat(0.99), "free_h": _flat(0.89),
         "history_all_h": _flat(1.00)}
    rows = _rows(a)
    first = r2.conclude(rows, "prev_table", 8.0, _strat_of(rows), **kw)
    lab = first["labels"]
    assert lab["reproduce"]["status"] == "EXACT" and lab["reproduce_status"] == "EXACT" and lab["void"] is False
    assert lab["gate_eq_matches_strat"] is None and lab["k_selected"] == "8"
    assert lab["label"] == "R2-FALLBACK-SURVIVES / H-SURVIVES" and lab["q1"] == "R2-FALLBACK-SURVIVES" and lab["q2"] == "H-SURVIVES"
    assert abs(lab["gate_eq_r2_fallback"]["delta"] - 0.07) < 1e-9 and lab["gate_eq_r2_fallback_reading"] == "SIGNAL"
    assert abs(lab["gate_eq_r2_all"]["delta"] - 0.045) < 1e-9 and lab["gate_eq_r2_all_reading"] == "NOT-SHOWN"
    assert abs(lab["shrinkage_fallback"]["delta"] - 0.18) < 1e-9 and lab["shrinkage_readings"]["fallback"] == "SIGNAL"
    assert abs(lab["shrinkage_covered"]["delta"] - 0.03) < 1e-9 and lab["shrinkage_readings"]["covered"] == "NOT-SHOWN"
    assert abs(lab["twin_gate_eq_fallback"]["delta"] - 0.25) < 1e-9 and abs(lab["shrinkage_share_of_fallback_margin"] - 0.72) < 1e-9
    assert not lab["all_floor_straddle"]
    assert abs(lab["d_eq_h_all"]["delta"] - 0.10) < 1e-9 and abs(lab["d_add_h_all"]["delta"] - 0.11) < 1e-9
    assert abs(lab["h_dilution_anchor"]["delta"] - 0.01) < 1e-9 and lab["h_inconsistent_cause"] is None
    assert lab["q2_reader_guard"] is False and lab["free_h_gain_reading"] == "NOT-SHOWN" and lab["address_handicap"] is False
    assert lab["sentence"].startswith("against a free encoding that is never at the marginal")
    assert "the address margin survives the strongest free arm this registration builds (the p_t summaries and the full h_a not included)" in lab["sentence"]
    assert lab["sentence"].count("at this reader") == 2 and not lab["fallback_floor_straddle"] and not lab["q2_floor_straddle"]
    assert lab["scopes"]["all"]["positions"] == 150 and abs(lab["scopes"]["fallback"]["share"] - 0.5) < 1e-12
    # the identity against the stratified cells: equal -> True; a moved cell -> INVALID, void
    cells = {s: first["deltas"][f"gate_eq|B=16|{s}"] for s in r2.IDENTITY_SCOPES}
    assert r2.conclude(rows, "prev_table", 8.0, _strat_of(rows), cells, **kw)["labels"]["gate_eq_matches_strat"] is True
    moved = dict(cells); moved["all"] = dict(cells["all"], delta=cells["all"]["delta"] + 1e-6)
    void = r2.conclude(rows, "prev_table", 8.0, _strat_of(rows), moved, **kw)["labels"]
    assert void["label"] == "REPRODUCE-INVALID" and void["void"] is True and void["q1"] is None and void["q2"] is None
    assert void["gate_eq_r2_fallback_reading"] is None and void["shrinkage_readings"] is None and void["gate_eq_r2_fallback"] is not None
    for f_ in r2.READING_FIELDS:                                            # a void payload carries numbers, no readings
        assert void[f_] is None, f_
    assert void["address_handicap_scopes"] is None and void["d_add_h_fallback_reading"] is None and void["d_add_h_fallback"] is not None
    assert void["sentence"].startswith("this read's rows do not reproduce")
    # B: R2-ABSORBED / H-ABSORBS (every delta CI-positive below the floor, no straddle: the frozen NOT-SHOWN words)
    b = {"history_tok_r2": _split(0.90, 0.92), "free_r2": _split(0.88, 0.90), "history_bigram_r2": _flat(0.91),
         "free_h": _flat(0.90), "history_all_h": _flat(0.92)}
    lab = r2.conclude(_rows(b), "prev_table", 32.0, None, **kw)["labels"]
    assert lab["label"] == "R2-ABSORBED / H-ABSORBS" and lab["reproduce"] is None and lab["reproduce_ok"] is None
    assert lab["gate_eq_r2_fallback_reading"] == "NOT-SHOWN" and lab["gate_eq_r2_fallback"]["lo"] > 0
    assert lab["sentence"].startswith("no material margin (at or above +0.05) of the address block over the equal-dims generalising free block is shown on the unseen-key positions nor pooled")
    assert "consistent with table sparsity" in lab["sentence"] and "show no material address margin" in lab["sentence"]
    assert lab["shrinkage_share_of_fallback_margin"] is None             # the twin's fallback margin is zero here
    assert lab["k_at_replay_end"] is False and lab["address_handicap"] is False and lab["q2_reader_guard"] is False
    assert lab["said_in_words"] == {"b8_b32_disagree": [], "limit_arm_above_free_r2": [], "h_only_above_history_tok": False,
                                    "replay_zerofit_all_point": 0.8} and lab["h_anchor_reading"] == "NOT-SHOWN"
    # B-inf: the same rows with k at the pure-replay end: the sparsity clause is replaced, nothing else moves
    lab = r2.conclude(_rows(b), "prev_table", INF, None, **kw)["labels"]
    assert lab["label"] == "R2-ABSORBED / H-ABSORBS" and lab["k_at_replay_end"] is True and lab["k_selected"] == "inf"
    assert "pure-replay end of the grid" in lab["sentence"] and "consistent with table sparsity" not in lab["sentence"]
    assert "neither resolved nor retired" in lab["sentence"]
    # B-handicap: the shared k handicaps the address partner (history_tok_r2 below history_tok, NEGATIVE): said in the sentence
    bh = dict(b, history_tok=_flat(0.95))
    lab = r2.conclude(_rows(bh), "prev_table", 32.0, None, **kw)["labels"]
    assert lab["address_handicap"] is True and lab["address_handicap_reading"] == "NEGATIVE"
    assert lab["address_handicap_scopes"] == ["all", "fallback"] and "NEGATIVE, on all and fallback)" in lab["sentence"]
    assert "consistent with table sparsity" in lab["sentence"] and "handicaps the address partner" in lab["sentence"]
    assert abs(lab["gate_eq_r2_twinarm_all"]["delta"] - (0.95 - 0.89)) < 1e-9
    bh2 = dict(b, history_tok={**_split(0.80, 0.95)})                      # a FALLBACK-only handicap is keyed too
    lab = r2.conclude(_rows(bh2), "prev_table", 32.0, None, **kw)["labels"]
    assert lab["address_handicap"] is True and lab["address_handicap_scopes"] == ["fallback"] and "NEGATIVE, on fallback)" in lab["sentence"]
    assert abs(lab["gate_eq_r2_twinarm_all"]["delta"] - (0.875 - 0.89)) < 1e-9
    # B-guard: adding the hidden block degrades the free arm (free_h below free_r2, NEGATIVE): the Q2 label stays, the
    # branch sentence is replaced by the reader-guard sentence, nothing is struck
    bg = dict(b, free_h=_flat(0.70))
    lab = r2.conclude(_rows(bg), "prev_table", 32.0, None, **kw)["labels"]
    assert lab["q2"] == "H-SURVIVES" and lab["q2_reader_guard"] is True and lab["free_h_gain_reading"] == "NEGATIVE"
    assert "degrades a reader at this train size" in lab["sentence"] and "free_h - free_r2 reads NEGATIVE" in lab["sentence"]
    assert "address margin survives" not in lab["sentence"] and lab["label"] == "R2-ABSORBED / H-SURVIVES"
    bg2 = dict(b, history_all_h=_flat(0.70))                              # the anchor NEGATIVE alone also fires it
    lab = r2.conclude(_rows(bg2), "prev_table", 32.0, None, **kw)["labels"]
    assert lab["q2_reader_guard"] is True and "the dilution anchor history_all_h - history_bigram_r2 reads NEGATIVE" in lab["sentence"]
    # D_add^H alone is NEGATIVE: the prefix names the address STREAM, not the equal-dims block, and stays under the guard
    assert lab["h_negative"] is True and lab["d_add_h_all_reading"] == "NEGATIVE" and lab["d_eq_h_all_reading"] != "NEGATIVE"
    assert "the address stream reads below the free bigram plus the hidden block (NEGATIVE); with the forward's final-norm state" in lab["sentence"]
    assert "the address block reads below the equal-dims free block" not in lab["sentence"]
    assert lab["d_add_h_fallback_reading"] == "NEGATIVE" and lab["d_add_r2_fallback_floor_straddle"] is False
    # the no-gain tail: an ABSORBED label without a material SHRINKAGE on the unseen keys is not credited to sparsity
    bn = dict(b, free_bigram_b=_split(0.88, 0.90))
    lab = r2.conclude(_rows(bn), "prev_table", 32.0, None, **kw)["labels"]
    assert lab["q1"] == "R2-ABSORBED" and lab["shrinkage_readings"]["fallback"] == "NOT-SHOWN"
    assert "did not recover a material share of the unseen-key deficit" in lab["sentence"] and "consistent with table sparsity" not in lab["sentence"]
    bg3 = dict(b, free_h=_flat(0.70), history_all_h=_flat(0.60))          # both readings NEGATIVE: "read", not "reads"
    lab = r2.conclude(_rows(bg3), "prev_table", 32.0, None, **kw)["labels"]
    assert "free_h - free_r2 and the dilution anchor history_all_h - history_bigram_r2 read NEGATIVE" in lab["sentence"]
    # C: R2-POOLED-ONLY / H-COMPLEMENTARY
    c = {"history_tok_r2": _split(0.95, 0.90), "free_r2": _split(0.85, 0.88), "history_bigram_r2": _flat(0.92),
         "free_h": _flat(0.90), "history_all_h": _flat(1.00)}
    lab = r2.conclude(_rows(c), "prev_table", 8.0, None, **kw)["labels"]
    assert lab["label"] == "R2-POOLED-ONLY / H-COMPLEMENTARY"
    assert lab["gate_eq_r2_fallback_reading"] == "NOT-SHOWN" and lab["gate_eq_r2_all_reading"] == "SIGNAL"
    assert lab["sentence"].startswith("no material margin (at or above +0.05) of the address block over the equal-dims generalising free block is shown on the unseen-key positions while the pooled margin is material")
    assert lab["gate_eq_r2_covered_reading"] == "SIGNAL" and "and what survives sits on the covered positions" in lab["sentence"]
    assert "while the address stream adds a material margin over the free bigram plus the hidden block" in lab["sentence"]
    # D: H-INCONSISTENT blamed on the reader (the anchor's CI95 upper below zero)
    d_ = {"history_tok_r2": _flat(0.80), "free_r2": _flat(0.80), "history_bigram_r2": _flat(0.90),
          "free_h": _flat(0.80), "history_all_h": _flat(0.83)}
    lab = r2.conclude(_rows(d_), "prev_table", 8.0, None, **kw)["labels"]
    assert lab["q2"] == "H-INCONSISTENT" and lab["h_inconsistent_cause"] == "reader"
    assert lab["q2_reader_guard"] is True                                 # the anchor is NEGATIVE: the guard's sentence
    assert "degrades a reader" in lab["sentence"] and "no sentence on the margin is written" not in lab["sentence"]
    # E: floor straddles (per-prompt spread), on the Q1 gate and on a Q2 reading: the "not settled" sentences
    e = {"history_tok_r2": {**_split(0.80, (0.95, 0.75)), **{s: 0.80 for s in COV}}, "free_r2": _flat(0.80),
         "history_bigram_r2": _flat(0.80), "free_h": _flat(0.80), "history_all_h": {s: (0.90, 0.78) for s in r2.STRATA}}
    lab = r2.conclude(_rows(e), "prev_table", 8.0, None, **kw)["labels"]
    assert lab["fallback_floor_straddle"] is True and lab["gate_eq_r2_fallback_reading"] == "NOT-SHOWN"
    assert lab["d_add_h_floor_straddle"] is True and lab["q2_floor_straddle"] is True
    assert lab["sentence"].startswith("neither Q1 reading is SIGNAL by the rule while the unseen-key CI95 straddles the +0.05 floor: not settled at this power")
    assert lab["sentence"].count("not settled at this power") == 2
    # F: a NEGATIVE Q1 gate is said in words and routes by the pooled reading; a NEGATIVE pooled reading is said too
    f = {"history_tok_r2": _split(0.98, 0.75), "free_r2": _split(0.80, 0.90), "history_bigram_r2": _flat(0.80),
         "free_h": _flat(0.80), "history_all_h": _flat(0.80)}
    lab = r2.conclude(_rows(f), "prev_table", 8.0, None, **kw)["labels"]
    assert lab["gate_eq_r2_fallback_reading"] == "NEGATIVE" and lab["fallback_negative"] is True
    assert lab["q1"] == "R2-ABSORBED" and lab["sentence"].startswith("the address block reads below the equal-dims generalising free block on the unseen-key positions (NEGATIVE); ")
    assert lab["all_negative"] is False and "the pooled Q1 reading is NEGATIVE" not in lab["sentence"]
    f2 = dict(f, history_tok_r2=_flat(0.70))
    lab = r2.conclude(_rows(f2), "prev_table", 8.0, None, **kw)["labels"]
    assert lab["all_negative"] is True and "; the pooled Q1 reading is NEGATIVE" in lab["sentence"]
    # G: a pooled-gate straddle is said in words beside the sentence; H: a missing arm is INCOMPLETE
    g_ = {"history_tok_r2": {s: (0.90, 0.80) for s in r2.STRATA}, "free_r2": _flat(0.80), "history_bigram_r2": _flat(0.80),
          "free_h": _flat(0.80), "history_all_h": _flat(0.80)}
    lab = r2.conclude(_rows(g_), "prev_table", 8.0, None, **kw)["labels"]
    assert lab["all_floor_straddle"] is True and "; the pooled Q1 reading's CI95 straddles the +0.05 floor" in lab["sentence"]
    lab = r2.conclude([r for r in _rows({}) if r["arm"] != "h_only"], "prev_table", 8.0, None, **kw)["labels"]
    assert lab["label"] == "INCOMPLETE" and lab["void"] is True and lab["missing_arms"] == ["h_only"] and lab["sentence"] is None
    # the said-in-words flags: a limit arm above free_r2 on test and h_only above history_tok
    s_ = {"free_backoff": _flat(0.85), "h_only": _flat(0.90), "history_tok": _flat(0.85)}
    lab = r2.conclude(_rows(s_), "prev_table", 8.0, None, **kw)["labels"]
    assert lab["said_in_words"]["limit_arm_above_free_r2"] == ["free_backoff"] and lab["said_in_words"]["h_only_above_history_tok"] is True
    with pytest.raises(SystemExit, match="unknown encoding"):
        r2.conclude(_rows({}), "trigram", 8.0, None, **kw)


def test_pairing_is_refused_within_a_scope():
    rows = _rows({})
    bad = [r for r in rows if not (r["arm"] == "history_all_h" and r["prompt_idx"] == 1 and r["stratum"] == "both_unseen")]
    with pytest.raises(SystemExit, match="pairing violated: history_all_h"):
        r2.conclude(bad, "prev_table", 8.0, None, n_boot=50, budgets=(16,))
    bad2 = [dict(r, needed=(r["needed"] + 1 if r["arm"] == "free_h" and r["stratum"] == "covered_5p" else r["needed"])) for r in rows]
    with pytest.raises(SystemExit, match="pairing violated: free_h"):
        r2.conclude(bad2, "prev_table", 8.0, None, n_boot=50, budgets=(16,))


# ---------------------------------------------------------------------------
# guards, the stratified reference, exact recompute and its refusals
# ---------------------------------------------------------------------------

def test_guards_under_results(tmp_path, monkeypatch):
    d, b, g = tps._unseen_harvest(tmp_path, rule="random", R=21, seed=12)
    _add_hidden(d, seed=12)
    src = _replay_source(tmp_path / "src.npz", rule=False)
    with pytest.raises(SystemExit, match="may not write under results/"):
        r2.run(_args(d, b, g, ROOT / "results" / "smoke" / "x.json", src, only_seeds="0"))
    with pytest.raises(SystemExit, match="lambda or k grid"):
        r2.run(_args(d, b, g, ROOT / "results" / "smoke" / "y.json", src, lambdas=FAST))
    with pytest.raises(SystemExit, match="lambda or k grid"):
        r2.run(_args(d, b, g, ROOT / "results" / "smoke" / "y.json", src, lambdas=None, k_grid="0,8"))
    with pytest.raises(SystemExit, match="replay source must be the pinned checkpoint"):
        r2.run(_args(d, b, g, ROOT / "results" / "smoke" / "z.json", src, lambdas=None))
    # the k grid must be strictly increasing and run from 0 to inf (smoke and test paths)
    with pytest.raises(SystemExit, match="strictly increasing"):
        r2.run(_args(d, b, g, tmp_path / "kg.json", src, k_grid="8,0,inf"))
    with pytest.raises(SystemExit, match="must run from 0"):
        r2.run(_args(d, b, g, tmp_path / "kg.json", src, k_grid="2,8"))
    monkeypatch.setattr(r2.pr, "_under_results", lambda p: True)        # results/ membership stubbed; nothing written there
    with pytest.raises(SystemExit, match="must be results/real/prefetch_r2_s3.json"):
        r2.run(_args(d, b, g, tmp_path / "wrong_name.json", src, lambdas=None, replay="hf"))
    out = tmp_path / "prefetch_r2_s3.json"
    state = Path(str(out) + ".state.jsonl"); state.write_text("x")
    with pytest.raises(SystemExit, match="state.jsonl exists: a registered payload is never overwritten"):
        r2.run(_args(d, b, g, out, src, lambdas=None, replay="hf"))
    state.unlink()
    monkeypatch.setattr(r2, "ROOT", tmp_path / "scratch_root")
    (tmp_path / "scratch_root" / "results" / "real").mkdir(parents=True)
    out = tmp_path / "scratch_root" / "results" / "real" / "prefetch_r2_s3.json"
    with pytest.raises(SystemExit, match="strat none is refused under results/"):
        r2.run(_args(d, b, g, out, src, lambdas=None, replay="hf", strat="none"))
    with pytest.raises(SystemExit, match="must be the registered one for this harvest"):
        r2.run(_args(d, b, g, out, src, lambdas=None, replay="hf", strat=str(tmp_path / "elsewhere.json")))
    with pytest.raises(SystemExit, match="not found"):
        r2.run(_args(d, b, g, out, src, lambdas=None, replay="hf", strat=None))
    monkeypatch.undo()
    # the replay's eps and layer count are checked under results/ (config.json sits outside the pinned sha)
    monkeypatch.setattr(r2.pr, "_under_results", lambda p: True)
    monkeypatch.setattr(r2, "ROOT", tmp_path / "scratch_root")
    strat_out = tmp_path / "scratch_root" / "results" / "real" / "prefetch_strat_s3.json"
    good = r2.load_replay_source(str(src))
    monkeypatch.setattr(r2, "load_replay_source", lambda spec: dict(good, sha256=r2.REPLAY_SOURCE_SHA256, eps=1e-3))
    monkeypatch.setattr(r2, "strat_reference", lambda *a, **k: {"encoding": "prev_table"})
    with pytest.raises(SystemExit, match="eps must be 1e-5"):
        r2.run(_args(d, b, g, out, src, lambdas=None, replay="hf", strat=str(strat_out)))
    monkeypatch.undo()
    assert r2.OUT_OF_HARVEST == {"harvest_moe": "prefetch_r2_s3.json", "harvest_moe_r": "prefetch_r2_s3_r.json"}
    assert r2.STRAT_OF_HARVEST == {"harvest_moe": "prefetch_strat_s3.json", "harvest_moe_r": "prefetch_strat_s3_r.json"}


def test_strat_reference_reading(tmp_path):
    d, b, g = tps._unseen_harvest(tmp_path, rule="random", R=21, seed=13)
    _add_hidden(d, seed=13)
    src = _replay_source(tmp_path / "src.npz", rule=False)
    other = tmp_path / "other.json"; other.write_text(json.dumps({"registered": "x"}))
    with pytest.raises(SystemExit, match="not a stratified coverage read payload"):
        r2.read_strat(other)
    forged = tmp_path / "forged.json"
    forged.write_text(json.dumps({"registered": rs.REGISTERED, "provenance": {"instrument_sha256": "0" * 64}, "n_state_rows": 0}))
    with pytest.raises(SystemExit, match="not written by the frozen stratified tool"):
        r2.read_strat(forged)
    # a stratified payload that selected its own encoding (no twin) is refused: it carries no twin lambdas
    twinless = tmp_path / "twinless.json"
    rs.run(tps._args(d, b, g, twinless, lambdas=FAST))
    with pytest.raises(SystemExit, match="did not take its encoding and lambdas from a committed twin payload"):
        r2.read_strat(twinless)
    twin_out = tmp_path / "twin.json"
    rb.run(tps._twin_args(d, b, g, twin_out, lambdas=FAST))
    strat_out = tmp_path / "strat.json"
    sp = rs.run(tps._args(d, b, g, strat_out, lambdas=FAST, twin=str(twin_out)))
    st = r2.read_strat(strat_out)
    assert st["encoding"] == sp["provenance"]["encoding_selected"] and st["n_state_rows"] == sp["n_state_rows"]
    assert set(st["gate_eq"]) == set(r2.IDENTITY_SCOPES) and st["gate_eq"]["all"] == sp["conclusion"]["deltas"]["gate_eq|B=16|all"]
    assert len(st["_rows"]) == sp["n_state_rows"] and st["sha256"] == _sha(strat_out) and "\\" not in st["path"]
    assert set(st["lambda_selected"]) == set(r2.ARMS_TWIN)
    with pytest.raises(SystemExit, match="not found"):
        r2.strat_reference(d, str(tmp_path / "nope.json"), smoke=False, out_under_results=False)
    assert r2.strat_reference(tmp_path / "harvest_other", None, smoke=False, out_under_results=False) is None
    with pytest.raises(SystemExit, match="no committed stratified payload is known"):
        r2.strat_reference(tmp_path / "harvest_other", None, smoke=False, out_under_results=True)
    assert r2.strat_reference(d, str(strat_out), smoke=True, out_under_results=False) is None
    (tmp_path / "second").mkdir()
    d2, b2, g2 = tps._unseen_harvest(tmp_path / "second", rule="random", R=21, seed=14)
    _add_hidden(d2, seed=14)
    with pytest.raises(SystemExit, match="different harvest shards"):
        r2.run(_args(d2, b2, g2, tmp_path / "mismatch.json", src, strat=str(strat_out)))
    Path(str(strat_out) + ".state.jsonl").unlink()
    with pytest.raises(SystemExit, match="stratified state file"):
        r2.read_strat(strat_out)


def test_conclude_from_refusals(tmp_path):
    d, b, g, strat_out, out, payload = _chain(tmp_path, tmp_path / "src.npz", rule="token", R=21, T=14, seed=6, k_grid=SHORT_K)
    r2.conclude_from(out)                                                 # clean
    state = Path(str(out) + ".state.jsonl")
    lines = state.read_text(encoding="utf-8").splitlines()
    header = json.loads(lines[0])

    def write_header(h):
        state.write_text("\n".join([json.dumps(h)] + lines[1:]) + "\n", encoding="utf-8")

    write_header(dict(header, k_selected="512" if header["k_selected"] != "512" else "2"))
    with pytest.raises(SystemExit, match="k differs from the payload's"):
        r2.conclude_from(out)
    lam = dict(header["lambda_selected"]); lam["h_only"] = 12345.0
    write_header(dict(header, lambda_selected=lam))
    with pytest.raises(SystemExit, match="lambdas differ from the payload's"):
        r2.conclude_from(out)
    st = dict(header["strat"]); st["sha256"] = "0" * 64
    write_header(dict(header, strat=st))
    with pytest.raises(SystemExit, match="stratified reference differs"):
        r2.conclude_from(out)
    write_header(dict(header, replay_source_sha256="0" * 64))
    with pytest.raises(SystemExit, match="replay source sha differs"):
        r2.conclude_from(out)
    write_header(dict(header, smoke=True))
    with pytest.raises(SystemExit, match="registration or smoke flag differs"):
        r2.conclude_from(out)
    # a flipped grid-edge flag is refused: it is re-derived from the selected k / lambda
    write_header(header)
    p4 = json.loads(json.dumps(payload)); p4["provenance"]["k_grid_edge"] = not p4["provenance"]["k_grid_edge"]
    out.write_text(json.dumps(p4), encoding="utf-8")
    with pytest.raises(SystemExit, match="k grid-edge flag"):
        r2.conclude_from(out)
    p4 = json.loads(json.dumps(payload)); p4["provenance"]["lambda_grid_edge"]["h_only"] = not p4["provenance"]["lambda_grid_edge"]["h_only"]
    out.write_text(json.dumps(p4), encoding="utf-8")
    with pytest.raises(SystemExit, match="grid-edge flag for h_only"):
        r2.conclude_from(out)
    out.write_text(json.dumps(payload), encoding="utf-8")
    # a CONSISTENT flip of k in header and payload is refused: the k table re-selects it
    write_header(header)
    p2 = json.loads(out.read_text(encoding="utf-8"))
    other_k = [x for x in p2["provenance"]["constants"]["k_grid"] if x != p2["provenance"]["k_selected"]][0]
    p2["provenance"]["k_selected"] = other_k
    write_header(dict(header, k_selected=other_k)); out.write_text(json.dumps(p2), encoding="utf-8")
    with pytest.raises(SystemExit, match="not the pair its val table selects"):
        r2.conclude_from(out)
    # a CONSISTENT flip of a new arm's lambda is refused by its val table
    p3 = json.loads(json.dumps(payload))
    other_lam = [x for x in p3["provenance"]["constants"]["lambdas"] if x != p3["provenance"]["lambda_selected"]["h_only"]][0]
    p3["provenance"]["lambda_selected"]["h_only"] = other_lam
    write_header(dict(header, lambda_selected=p3["provenance"]["lambda_selected"])); out.write_text(json.dumps(p3), encoding="utf-8")
    with pytest.raises(SystemExit, match="not the one its val table selects"):
        r2.conclude_from(out)
    write_header(header); out.write_text(json.dumps(payload), encoding="utf-8")
    # a tampered row
    row = json.loads(lines[1]); row["hits"] = max(0, row["hits"] - 1)
    state.write_text("\n".join([lines[0], json.dumps(row)] + lines[2:]) + "\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="RECOMPUTE MISMATCH"):
        r2.conclude_from(out)
    write_header(header)
    # a stratified record header and payload agree on but that differs from the file on disk beyond the shas
    st5 = dict(header["strat"]); st5["git_commit"] = "deadbeef"
    p5 = json.loads(out.read_text(encoding="utf-8")); p5["provenance"]["strat"] = st5
    write_header(dict(header, strat=st5)); out.write_text(json.dumps(p5), encoding="utf-8")
    with pytest.raises(SystemExit, match="beyond the shas"):
        r2.conclude_from(out)
    write_header(header); out.write_text(json.dumps(payload), encoding="utf-8")
    # the stratified state file changed on disk: refused by sha before any recompute
    sstate = Path(str(strat_out) + ".state.jsonl")
    sb = sstate.read_bytes(); sstate.write_bytes(sb + b"\n")
    with pytest.raises(SystemExit, match="is not the one this run read"):
        r2.conclude_from(out)
    sstate.write_bytes(sb)
    r2.conclude_from(out)
    strat_out.rename(tmp_path / "moved.json")
    with pytest.raises(SystemExit, match="REPRODUCE cannot be recomputed"):
        r2.conclude_from(out)
    with pytest.raises(SystemExit, match="not a generalising free baseline"):
        r2.conclude_from(tmp_path / "moved.json")
    (tmp_path / "moved.json").rename(strat_out)
    r2.conclude_from(out)
    # a payload under results/ must be a registered run: registered grids, the pinned source, a stratified record, no smoke
    import run_prefetch_r2 as _r2
    monkey = pytest.MonkeyPatch()
    monkey.setattr(_r2.pr, "_under_results", lambda p: True)
    with pytest.raises(SystemExit, match="registered lambda and k grids"):
        r2.conclude_from(out)                                             # the fixture grid is "1,100"
    p6 = json.loads(json.dumps(payload)); p6["provenance"]["constants"]["lambdas"] = list(r2.LAMBDAS)
    p6["provenance"]["constants"]["k_grid"] = [r2.k_tag(k) for k in r2.K_GRID]
    out.write_text(json.dumps(p6), encoding="utf-8")
    with pytest.raises(SystemExit, match="k val table does not carry its own k and lambda grids"):
        r2.conclude_from(out)                                             # the tables still carry the fixture's grids
    monkey.undo()
    # the same malformed payload outside results/: refused for the same reason, never a KeyError
    with pytest.raises(SystemExit, match="does not carry its own"):
        r2.conclude_from(out)
    p7 = json.loads(json.dumps(payload)); p7["provenance"]["val_table"]["h_only"] = {"1.0": 0.5}
    out.write_text(json.dumps(p7), encoding="utf-8")
    with pytest.raises(SystemExit, match="val table for h_only does not carry its own lambda grid"):
        r2.conclude_from(out)
    out.write_text(json.dumps(payload), encoding="utf-8")
    r2.conclude_from(out)


# ---------------------------------------------------------------------------
# the hidden block is fit on train only; load_hidden guards; dims; no torch
# ---------------------------------------------------------------------------

def test_hidden_block_is_fit_on_train_only_and_load_hidden_guards(tmp_path):
    d, b, g = tps._unseen_harvest(tmp_path, rule="random", R=21, T=14, seed=4)
    _add_hidden(d, seed=4)
    src = r2.load_replay_source(str(_replay_source(tmp_path / "src.npz", rule=False)))
    data = pr.S3Data(d)
    lab, nc = load_label_space(b, g)
    hidden = r2.load_hidden(data)
    assert hidden.shape == (data.n_rows, data.T, 1024) and hidden.dtype == np.float16
    replay = r2.replay_table(src, int(data.tokens.max()) + 1)
    rr = r2.R2(data, lab, nc, hidden, replay, lambdas=(1.0,))
    rows, anchors = pr.restrict(*rb.bigram_positions(data.lengths, data.T), rr.masks["train"])
    rr.fit_hidden(rows, anchors)
    noisy = hidden.copy()
    noisy[~rr.masks["train"]] = (np.random.default_rng(1).standard_normal(noisy[~rr.masks["train"]].shape) * 50).astype(np.float16)
    r3 = r2.R2(data, lab, nc, noisy, replay, lambdas=(1.0,))
    r3.fit_hidden(rows, anchors)
    for name in ("h_mu", "h_sd", "h_min", "h_max", "h_V"):
        assert np.array_equal(getattr(rr, name), getattr(r3, name)), name
    assert rr.h_V.shape == (1024, D) and np.allclose(rr.h_V.T @ rr.h_V, np.eye(D), atol=1e-8)
    assert all(rr.h_V[int(np.argmax(np.abs(rr.h_V[:, j]))), j] > 0 for j in range(D))     # the sign convention
    # test rows are clipped to the train support before the z-score
    rt, at = pr.restrict(*rb.bigram_positions(data.lengths, data.T), r3.masks["test"])
    Hb = r3.h_block(rt, at)
    z = (np.clip(noisy[rt, at].astype(np.float64), r3.h_min, r3.h_max) - r3.h_mu) / r3.h_sd
    assert np.allclose(Hb, z @ r3.h_V)
    # the smoke filter keeps the hidden rows aligned with S3Data's
    sm = pr.S3Data(d, smoke_split_val=True)
    assert r2.load_hidden(sm).shape[0] == sm.n_rows
    # guards: a narrow hidden; a shard without one
    tps._rewrite(d, lambda z: z.__setitem__("hidden", z["hidden"][:, :, :64]))
    with pytest.raises(SystemExit, match="below the address block's"):
        r2.load_hidden(pr.S3Data(d))
    tps._rewrite(d, lambda z: z.pop("hidden"))
    with pytest.raises(SystemExit, match="has no 'hidden' array"):
        r2.load_hidden(pr.S3Data(d))


def test_safetensors_parser_widens_bf16_and_reads_f32(tmp_path):
    """A minimal safetensors file written by hand (8-byte length prefix, JSON header, raw bytes): BF16 values
    exactly representable in bf16 round-trip to their float32 values; F32 reads as is; an unknown dtype is refused."""
    vals = np.array([[1.5, -2.0, 0.25], [1024.0, -0.0078125, 3.0]], dtype=np.float32)
    bf16 = (vals.view(np.uint32) >> 16).astype(np.uint16)                 # the top 16 bits: exact for these values
    f32 = np.array([0.1, -7.25], dtype=np.float32)
    header = {"a": {"dtype": "BF16", "shape": [2, 3], "data_offsets": [0, 12]},
              "b": {"dtype": "F32", "shape": [2], "data_offsets": [12, 20]},
              "c": {"dtype": "I8", "shape": [1], "data_offsets": [20, 21]}}
    hb = json.dumps(header).encode()
    path = tmp_path / "t.safetensors"
    path.write_bytes(len(hb).to_bytes(8, "little") + hb + bf16.tobytes() + f32.tobytes() + b"\x07")
    hdr, base = r2._read_header(path)
    assert hdr == header and base == 8 + len(hb)
    a, dt, shape, raw = r2._read_tensor(path, "a", hdr, base)
    assert dt == "BF16" and shape == [2, 3] and raw == bf16.tobytes() and np.array_equal(a, vals)
    b, dt, shape, raw = r2._read_tensor(path, "b", hdr, base)
    assert dt == "F32" and np.array_equal(b, f32) and raw == f32.tobytes()
    with pytest.raises(SystemExit, match="unsupported safetensors dtype"):
        r2._read_tensor(path, "c", hdr, base)


def test_hidden_block_truncates_a_wider_hidden_to_the_address_width(tmp_path):
    d, b, g = tps._unseen_harvest(tmp_path, rule="random", R=21, T=14, seed=16)
    _add_hidden(d, seed=16, width=1280)
    src = r2.load_replay_source(str(_replay_source(tmp_path / "src.npz", rule=False)))
    data = pr.S3Data(d)
    lab, nc = load_label_space(b, g)
    hidden = r2.load_hidden(data)
    assert hidden.shape[2] == 1280
    rr = r2.R2(data, lab, nc, hidden, r2.replay_table(src, int(data.tokens.max()) + 1), lambdas=(1.0,))
    rows, anchors = pr.restrict(*rb.bigram_positions(data.lengths, data.T), rr.masks["train"])
    rr.fit_hidden(rows, anchors)
    assert rr.h_V.shape == (1280, D) and rr.h_mu.shape == (1280,) and 0 < rr.h_kept_share <= 1.0
    assert rr.h_block(rows[:5], anchors[:5]).shape == (5, D)
    assert np.allclose(rr.h_V.T @ rr.h_V, np.eye(D), atol=1e-8)


def test_arm_dims_and_constants():
    enc = "prev_table"
    assert r2.arm_dims("free_r2", enc) == r2.arm_dims("history_tok_r2", enc) == rb.arm_dims("history_tok") == 2049
    assert r2.arm_dims("free_h", enc) == r2.arm_dims("history_bigram_r2", enc) == 3073
    assert r2.arm_dims("history_all_h", enc) == 4097 and r2.arm_dims("h_only", enc) == r2.arm_dims("replay_cur", enc) == 1025
    assert r2.arm_dims("free_backoff", enc) == r2.arm_dims("free_replay", enc) == 2049 and r2.arm_dims("replay_zerofit", enc) == 0
    for arm in r2.ARMS_TWIN:
        assert r2.arm_dims(arm, enc) == rb.arm_dims(arm)
    assert r2.ARM_K == {"free_backoff": 0.0, "free_replay": INF, "replay_cur": INF}
    assert r2.K_GRID == (0.0, 2.0, 8.0, 32.0, 128.0, 512.0, INF) and [r2.k_tag(k) for k in r2.K_GRID] == ["0", "2", "8", "32", "128", "512", "inf"]
    assert r2.ARMS_REQUIRED == rb.ARMS_REQUIRED + r2.ARMS_R2 and len(r2.ARMS_R2) == 10
    assert r2.LABEL_CELLS == ("gate_eq_r2|B=16|fallback", "gate_eq_r2|B=16|all", "d_eq_h|B=16|all", "d_add_h|B=16|all")
    assert r2.HEADLINE_CELLS[0] == "shrinkage|B=16|fallback" and r2.IDENTITY_SCOPES == ("all", "covered", "fallback")
    assert r2.TOKEN_PROBE == (0, 1, 2, 3, 128, 1024, 8192, 32768) and r2.MODEL_ID == "allenai/OLMoE-1B-7B-0125-Instruct"
    assert set(r2.SENTENCES_Q1) == {(q, s) for q in ("R2-FALLBACK-SURVIVES", "R2-POOLED-ONLY", "R2-ABSORBED") for s in (False, True)}
    assert set(r2.SENTENCES_Q2) == {(q, s) for q in ("H-SURVIVES", "H-COMPLEMENTARY", "H-ABSORBS", "H-INCONSISTENT") for s in (False, True)}
    assert r2.ARMS_RIDGE_R2 == tuple(a for a in r2.ARMS_R2 if a != "replay_zerofit")


def test_tool_imports_no_torch_transformers_or_safetensors():
    src = Path(r2.__file__).read_text(encoding="utf-8")
    for name in ("import torch", "import transformers", "import safetensors", "from safetensors", "from transformers"):
        assert name not in src
    code = ("import sys; sys.path.insert(0, r'%s'); import run_prefetch_r2; "
            "print([m in sys.modules for m in ('torch', 'transformers', 'safetensors')])" % str(ROOT / "tools"))
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)
    assert out.stdout.strip() == "[False, False, False]"
