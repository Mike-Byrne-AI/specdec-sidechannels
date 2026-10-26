"""tests/test_prefetch_readouts.py (OQ-9 stage-1 prefetch readouts): the
CI-safe layer — the recency policy matches a brute-force walk and budget 8 is
self-reuse; the ridge readers recover deterministic routing rules exactly
(a cross-token shift rule for the address-only arms, a token-driven rule for
the free-token / draft arms and the intra-forward slices) while the policy
and fixed baselines stay below; independent random routing leaves every
learned arm at chance (no leak); the top-B tie-break is by ascending expert
id; the lambda tie rule and grid-edge flag; FREE_PREV reads a-1 only with
TRAIN moments; the full CLI path on a fake sha-bound harvest + label space;
--conclude-from reproduces the payload and refuses a tampered row; a smoke
may not write under results/; labels are mechanical and INCOMPLETE on a
missing cell; pairing violations are refused; layout guards; no torch."""

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
import run_prefetch_readouts as pr  # noqa: E402

E, L, K = pr.N_EXPERTS, pr.N_GATES, pr.TOP_K
FAST_GRID = "1,100"


# ---------------------------------------------------------------------------
# fake harvests
# ---------------------------------------------------------------------------

def _slots_shift(rng, R, T, lengths):
    """S[t, 0] = (base + t) mod 64, S[t, l] = (S[t, 0] + l) mod 64: the next
    position's routing is a permutation of this one's (address-only arms
    recover it); no token dependence."""
    slots = np.full((R, T, L, K), -1, dtype=np.int16)
    for r in range(R):
        base = rng.choice(E, size=K, replace=False)
        for t in range(int(lengths[r])):
            for l in range(L):
                slots[r, t, l] = np.sort((base + t + l) % E)
    return slots


def _slots_token(tokens, lengths):
    """S[t, l] = {(7 * tokens[t-1] + 3 l + 9 i) mod 64 : i < 8}: the routing of
    forward t is a function of its INPUT token (tokens[t-1]); gate l is gate
    0 shifted by 3 l. tokens[-1] := 0."""
    R, T = tokens.shape
    slots = np.full((R, T, L, K), -1, dtype=np.int16)
    for r in range(R):
        for t in range(int(lengths[r])):
            tin = int(tokens[r, t - 1]) if t >= 1 else 0
            for l in range(L):
                slots[r, t, l] = np.sort((7 * tin + 3 * l + 9 * np.arange(K)) % E)
    return slots


def _slots_random(rng, R, T, lengths):
    slots = np.full((R, T, L, K), -1, dtype=np.int16)
    for r in range(R):
        for t in range(int(lengths[r])):
            for l in range(L):
                slots[r, t, l] = np.sort(rng.choice(E, size=K, replace=False))
    return slots


def make_fake_harvest(tmp_path: Path, rule="shift", n_shards=2, R=21, T=14, vocab=20, seed=0):
    rng = np.random.default_rng(seed)
    d = tmp_path / "harvest_moe"
    d.mkdir()
    for s in range(n_shards):
        lengths = rng.integers(6, T + 1, size=R).astype(np.int32)
        tokens = rng.integers(0, vocab, size=(R, T)).astype(np.int32)
        if rule == "shift":
            slots = _slots_shift(rng, R, T, lengths)
        elif rule == "token":
            slots = _slots_token(tokens, lengths)
        else:
            slots = _slots_random(rng, R, T, lengths)
        npz = d / f"moe_s{s}.npz"
        np.savez(npz, tokens=tokens, lengths=lengths, prompt_idx=np.arange(R, dtype=np.int32),
                 slots=slots, mass16=rng.random((R, T, 16)).astype(np.float16),
                 mass64=rng.random((R, T, 64)).astype(np.float16),
                 entropy=rng.random((R, T)).astype(np.float32))
        meta = {"npz_file": npz.name, "npz_sha256": hashlib.sha256(npz.read_bytes()).hexdigest(),
                "seed": s, "n_experts": E}
        (d / f"moe_s{s}.meta.json").write_text(json.dumps(meta))
    bucket_of = {str(t): int(t % 4) for t in range(vocab)}
    bpath = tmp_path / "buckets.json"
    bpath.write_text(json.dumps({"n_tokens": vocab, "bucket_of_token": bucket_of, "k": 4}))
    gpath = tmp_path / "glue.json"
    gpath.write_text(json.dumps({"glue_bucket_ids": [0], "k": 4,
                                 "buckets_sha256": hashlib.sha256(bpath.read_bytes()).hexdigest()}))
    return d, bpath, gpath


def _args(d, b, g, out, **kw):
    base = dict(harvest=str(d), out=str(out), buckets=str(b), glue=str(g), only_seeds=None,
                smoke_split_val=False, lambdas=FAST_GRID, conclude_from=None)
    base.update(kw)
    return argparse.Namespace(**base)


def _point(c, arm, B, key, depth=None):
    return c["tables"][f"{arm}|B={B}|key={key}|depth={depth}"]["all"]["point"]


# ---------------------------------------------------------------------------
# recency and top-B
# ---------------------------------------------------------------------------

def _brute_recency(slots_row, length, B, j):
    hits = np.zeros(L, np.int64); needed = np.zeros(L, np.int64)
    for l in range(L):
        recent: list[int] = []
        for t in range(length):
            block = sorted(slots_row[t, l].tolist())
            recent = block + [e for e in recent if e not in block]     # most recent first, asc id within a position
            if t + j < length:
                resident = set(recent[:B])
                hits[l] += sum(int(e) in resident for e in slots_row[t + j, l])
                needed[l] += K
    return hits, needed


def test_recency_matches_bruteforce_and_budget8_is_self_reuse():
    rng = np.random.default_rng(5)
    R, T = 4, 9
    lengths = np.array([9, 5, 7, 9])
    slots = _slots_random(rng, R, T, lengths)
    hits, needed = pr.recency_hits(slots, lengths, budgets=(8, 16), horizons=(1, 2))
    for r in range(R):
        for B in (8, 16):
            for j in (1, 2):
                h, n = _brute_recency(slots[r], int(lengths[r]), B, j)
                np.testing.assert_array_equal(hits[(B, j)][r], h)
                np.testing.assert_array_equal(needed[j][r], n)
    for r in range(R):
        for j in (1, 2):
            want = np.zeros(L, np.int64)
            for t in range(int(lengths[r]) - j):
                for l in range(L):
                    want[l] += len(set(slots[r, t, l].tolist()) & set(slots[r, t + j, l].tolist()))
            np.testing.assert_array_equal(hits[(8, j)][r], want)


def test_topb_tie_break_is_ascending_expert_id():
    sc = np.zeros((1, L, E))
    sc[0, 3, [5, 40, 12]] = 1.0
    assert pr.topb_order(sc, 2)[0, 3].tolist() == [5, 12]
    assert pr.topb_order(np.zeros((1, L, E)), 8)[0, 0].tolist() == list(range(8))
    counts = np.zeros((L, E)); counts[2, [9, 1]] = 3
    assert pr.resident_from_counts(counts, 3)[2].tolist() == [1, 9, 0]


# ---------------------------------------------------------------------------
# rules recovered, no leak
# ---------------------------------------------------------------------------

def test_shift_rule_is_recovered_by_the_address_arms(tmp_path):
    d, b, g = make_fake_harvest(tmp_path, rule="shift")
    out = tmp_path / "shift.json"
    c = pr.run(_args(d, b, g, out))["conclusion"]
    assert _point(c, "history", 8, 1) == 1.0
    assert _point(c, "history_tok", 8, 1) == 1.0
    for k in (1, 2, 4):
        assert _point(c, "intra", 8, k) == 1.0
    assert _point(c, "recency", 8, 1) < 1.0
    assert _point(c, "marginal", 8, 1) < 1.0
    assert _point(c, "marginal_all", 8, 0) < 1.0
    assert c["labels"]["history"] == "SIGNAL" and not c["labels"]["missing_arms"]
    assert c["labels"]["stage"] in ("PREFETCH-HEADROOM", "PREFETCH-NOT-SHOWN", "CACHE-SUFFICIENT")


def test_token_rule_is_recovered_by_the_free_and_draft_arms(tmp_path):
    d, b, g = make_fake_harvest(tmp_path, rule="token", vocab=12)
    out = tmp_path / "token.json"
    payload = pr.run(_args(d, b, g, out))
    c = payload["conclusion"]
    # S[t+1] is a function of tokens[t]: the free arms are exact, address-only is not
    assert _point(c, "free_table", 8, 1) == 1.0
    assert _point(c, "free_tok", 8, 1) == 1.0
    assert _point(c, "history_tok", 8, 1) == 1.0
    assert _point(c, "history", 8, 1) < 0.9
    # S[t+2] is a function of tokens[t+1] (the perfect draft): the draft arms are exact, the free arms are not
    assert _point(c, "draft_free", 8, 2) == 1.0
    assert _point(c, "draft_full", 8, 2) == 1.0
    assert _point(c, "history_tok", 8, 2) < 0.9
    # gate l is gate 0 shifted: intra recovers it at every lead
    for k in (1, 2, 4):
        assert _point(c, "intra", 8, k) == 1.0
    # no j >= 3 arm reads beyond tokens[t]: free_tok at j = 3 / 4 sits near chance (0.125)
    for j in (3, 4):
        assert _point(c, "free_tok", 8, j) < 0.3
    assert c["labels"]["draft"] == "SIGNAL"
    assert c["labels"]["address_beyond_token"] in ("NOT-SHOWN", "NEGATIVE")   # the token carries everything here
    assert c["labels"]["sideband_sentence"]
    prov = payload["provenance"]
    assert set(prov["harvest_npz_sha256"]) == {"moe_s0.npz", "moe_s1.npz"}
    assert prov["smoke"] is False and prov["n_test_prompts"] == 3
    assert prov["constants"]["lambdas"] == [1.0, 100.0]
    # state file reproduces the payload; a tampered row is refused
    got = pr.conclude_from(out)
    assert json.dumps(got, sort_keys=True) == json.dumps(c, sort_keys=True)
    sp = Path(str(out) + ".state.jsonl")
    lines = sp.read_text().splitlines()
    row = json.loads(lines[5]); row["hits"] = max(0, row["hits"] - 1); lines[5] = json.dumps(row)
    sp.write_text("\n".join(lines) + "\n")
    with pytest.raises(SystemExit, match="RECOMPUTE MISMATCH"):
        pr.conclude_from(out)


def test_independent_random_routing_leaves_every_learned_arm_at_chance(tmp_path):
    d, b, g = make_fake_harvest(tmp_path, rule="random", R=28, T=16, seed=11)
    out = tmp_path / "random.json"
    c = pr.run(_args(d, b, g, out, lambdas="100"))["conclusion"]
    chance = K / E
    for arm, key in (("history", 1), ("free_tok", 1), ("history_tok", 1), ("free_table", 1),
                     ("draft_free", 2), ("draft_full", 2), ("intra", 1), ("intra", 4)):
        p = _point(c, arm, 8, key)
        assert abs(p - chance) < 0.05, (arm, key, p)
    for o in (1, 2):
        floor = _point(c, "front_floor", None, o)
        assert _point(c, "front_gates", None, o, 16) <= floor + 0.12
    assert c["labels"]["history"] != "SIGNAL"


# ---------------------------------------------------------------------------
# lambda selection, FREE_PREV, tables
# ---------------------------------------------------------------------------

def _bare_stage(lambdas, horizons=(1,), leads=(1,)):
    st = pr.Stage1.__new__(pr.Stage1)
    st.lambdas = tuple(float(x) for x in lambdas); st.horizons = horizons; st.leads = leads
    st.val_table, st.lambda_selected, st.grid_edge = {}, {}, {}
    return st


def _val_dict(scores_of, lambdas, horizons=(1,), leads=(1,)):
    val = {}
    for lam in lambdas:
        for j in horizons:
            for arm in pr.LEARNED_ARMS_OF_HORIZON[j]:
                val[(arm, pr.LABEL_BUDGET, j, None, lam)] = (np.array([[scores_of(arm, lam) * 80]]), np.array([[80]]))
        for k in leads:
            val[("intra", pr.LABEL_BUDGET, k, None, lam)] = (np.array([[scores_of("intra", lam) * 80]]), np.array([[80]]))
        val[("front_free", None, 1, None, lam)] = (np.array([[scores_of("front_free", lam) * 80]]), np.array([[80]]))
        for l in range(1, L + 1):
            val[("front_gates", None, 1, l, lam)] = (np.array([[scores_of("front_gates", lam) * 80]]), np.array([[80]]))
    return val


def test_lambda_tie_keeps_smaller_and_grid_edge_is_flagged():
    lams = (1.0, 10.0, 100.0)
    st = _bare_stage(lams)
    st.select_lambdas(_val_dict(lambda arm, lam: 0.5, lams))            # all tied
    assert all(v == 1.0 for v in st.lambda_selected.values())
    assert all(st.grid_edge.values())
    st = _bare_stage(lams)
    st.select_lambdas(_val_dict(lambda arm, lam: {1.0: 0.4, 10.0: 0.6, 100.0: 0.5}[lam], lams))
    assert all(v == 10.0 for v in st.lambda_selected.values())
    assert not any(st.grid_edge.values())
    st = _bare_stage(lams)
    st.select_lambdas(_val_dict(lambda arm, lam: lam / 100.0, lams))      # increasing: top edge
    assert all(v == 100.0 for v in st.lambda_selected.values()) and all(st.grid_edge.values())


def test_free_prev_reads_the_previous_position_with_train_moments(tmp_path):
    d, b, g = make_fake_harvest(tmp_path, rule="random", n_shards=1)
    data = pr.S3Data(d)
    lab, C = pr.load_label_space(b, g)
    # garbage in a VAL row must not move the TRAIN moments
    val_rows = np.flatnonzero(data.split == "val")
    data.mass16[val_rows] = 1e4; data.mass64[val_rows] = -1e4; data.entropy[val_rows] = 1e4
    st = pr.Stage1(data, lab, C, lambdas=(1.0,))
    st.fit()
    rows, anchors = pr.restrict(*pr.positions_iv(data.lengths, 1, data.T), data.split == "train")
    raw = np.hstack([data.mass16[rows, anchors - 1], data.mass64[rows, anchors - 1], data.entropy[rows, anchors - 1][:, None]])
    np.testing.assert_allclose(st.fp_mean, raw.mean(axis=0))
    assert np.all(np.abs(st.fp_mean) < 10)
    # the feature reads a-1: perturbing the anchor's own position leaves it unchanged, perturbing a-1 changes it
    # (one anchor, so the perturbed position is never another chosen anchor's a-1)
    r, a = rows[:1], anchors[:1]
    f0 = st.free_prev(r, a)
    data.mass16[r, a] += 5.0
    np.testing.assert_array_equal(st.free_prev(r, a), f0)
    data.mass16[r, a - 1] += 5.0
    assert not np.array_equal(st.free_prev(r, a), f0)
    assert f0.shape[1] == 16 + 64 + 1 + C


def test_free_prev_sd_guard_replaces_only_exact_zero_sd(tmp_path):
    d, b, g = make_fake_harvest(tmp_path, rule="random", n_shards=1)
    data = pr.S3Data(d)
    lab, C = pr.load_label_space(b, g)
    data.mass16[:, :, 0] = 0.5                       # constant channel: sd exactly 0 -> 1
    data.mass16[:, :, 1] = 0.5 + 0.01 * (data.mass16[:, :, 1] - 0.5)   # small but nonzero sd: kept, not floored
    st = pr.Stage1(data, lab, C, lambdas=(1.0,))
    st.fit()
    assert st.fp_sd[0] == 1.0
    assert 0 < st.fp_sd[1] < 0.1


def _table_without_prompt(data, st, tok, prompt):
    """Brute force: the train table for key `tok` with every contribution of
    `prompt` (all its rows, all positions t with t+1 < length) removed."""
    counts = st.token_table[tok].astype(np.float64).copy()
    for r in np.flatnonzero((data.split == "train") & (data.prompt_idx == prompt)):
        for t in range(int(data.lengths[r]) - 1):
            if int(data.tokens[r, t]) == tok:
                for l in range(L):
                    counts[l, data.slots[r, t + 1, l].astype(np.int64)] -= 1.0
    tot = counts.sum(axis=1, keepdims=True)
    return np.where(tot > 0, counts / np.maximum(tot, 1.0), st.marginal_freq).reshape(-1)


def test_train_rows_read_the_table_leave_one_prompt_out(tmp_path):
    d, b, g = make_fake_harvest(tmp_path, rule="token", n_shards=2, vocab=12)
    data = pr.S3Data(d)
    lab, C = pr.load_label_space(b, g)
    st = pr.Stage1(data, lab, C, lambdas=(1.0,))
    st.fit()
    rows, anchors = pr.restrict(*pr.positions_horizon(data.lengths, 1, data.T), data.split == "train")
    # a train row's feature equals the table built without EVERY contribution of its own prompt (both seeds)
    for i in (0, 7, 19, 40):
        r, a = rows[i:i + 1], anchors[i:i + 1]
        tok, prompt = int(data.tokens[r[0], a[0]]), int(data.prompt_idx[r[0]])
        X, _ = st.horizon_design(r, a, 1, lopo=True)
        np.testing.assert_allclose(X[0, pr.D_MH:2 * pr.D_MH], _table_without_prompt(data, st, tok, prompt))
    # at j = 2 the draft block is read without the prompt's contributions under tokens[t+1]
    rows2, anchors2 = pr.restrict(*pr.positions_horizon(data.lengths, 2, data.T), data.split == "train")
    r, a = rows2[:1], anchors2[:1]
    tok1, prompt = int(data.tokens[r[0], a[0] + 1]), int(data.prompt_idx[r[0]])
    X2, _ = st.horizon_design(r, a, 2, lopo=True)
    np.testing.assert_allclose(X2[0, 2 * pr.D_MH:3 * pr.D_MH], _table_without_prompt(data, st, tok1, prompt))
    # val / test rows read the full train table (no subtraction)
    rv, av = pr.restrict(*pr.positions_horizon(data.lengths, 1, data.T), data.split == "test")
    Xv, _ = st.horizon_design(rv[:1], av[:1], 1)
    np.testing.assert_allclose(Xv[0, pr.D_MH:2 * pr.D_MH], st.table_vec(data.tokens[rv[:1], av[:1]])[0])
    cov = st.table_coverage()
    assert set(cov) == {"train", "val", "test"} and "singleton_key_share" in cov["train"]


def test_in_sample_table_is_the_target_and_leave_one_prompt_out_is_not(tmp_path):
    """Discriminating probe (critic's third pass): under independent random
    routing with a large vocabulary almost every (prompt, token) key is a
    singleton, so the in-sample table's top-8 at a train row IS that row's
    own target (hit rate near 1) while the leave-one-prompt-out read falls
    back to the marginal (hit rate near chance)."""
    d, b, g = make_fake_harvest(tmp_path, rule="random", n_shards=2, R=21, T=14, vocab=3000, seed=3)
    data = pr.S3Data(d)
    lab, C = pr.load_label_space(b, g)
    st = pr.Stage1(data, lab, C, lambdas=(1.0,))
    st.fit()
    rows, anchors = pr.restrict(*pr.positions_horizon(data.lengths, 1, data.T), data.split == "train")
    Xin, Y = st.horizon_design(rows, anchors, 1, lopo=False)
    Xlo, _ = st.horizon_design(rows, anchors, 1, lopo=True)
    hit_in = pr.hits_from_scores(Xin[:, pr.D_MH:2 * pr.D_MH], Y, K).sum() / (rows.shape[0] * L * K)
    hit_lo = pr.hits_from_scores(Xlo[:, pr.D_MH:2 * pr.D_MH], Y, K).sum() / (rows.shape[0] * L * K)
    assert hit_in > 0.9
    assert hit_lo < 0.3


def test_token_table_keys_on_the_input_token_and_falls_back_to_marginal(tmp_path):
    d, b, g = make_fake_harvest(tmp_path, rule="token", n_shards=1, vocab=12)
    data = pr.S3Data(d)
    lab, C = pr.load_label_space(b, g)
    st = pr.Stage1(data, lab, C, lambdas=(1.0,))
    st.fit()
    # TABLE(x): the forward that token x feeds routes to {(7x + 3l + 9i) mod 64}
    for x in range(12):
        if st.token_table[x].sum() == 0:
            continue
        v = st.table_vec(np.array([x])).reshape(L, E)
        for l in range(L):
            want = np.sort((7 * x + 3 * l + 9 * np.arange(K)) % E)
            assert set(np.flatnonzero(v[l] > 0).tolist()) == set(want.tolist())
    # an unseen token takes the marginal frequencies at the j = 1 targets
    unseen = np.array([data.tokens.max()])
    st.token_table[unseen[0]] = 0
    np.testing.assert_allclose(st.table_vec(unseen).reshape(L, E), st.marginal_freq)
    assert st.counts_all.sum() == st.n_positions["all/train"] * L * K


# ---------------------------------------------------------------------------
# CLI guards, labels
# ---------------------------------------------------------------------------

def test_smoke_split_and_results_guards(tmp_path):
    d, b, g = make_fake_harvest(tmp_path, rule="random", R=42)
    with pytest.raises(SystemExit, match="may not write under results/"):
        pr.run(_args(d, b, g, ROOT / "results" / "smoke" / "x.json", only_seeds="0"))
    with pytest.raises(SystemExit, match="lambda grid"):
        pr.run(_args(d, b, g, ROOT / "results" / "smoke" / "y.json"))
    out = tmp_path / "smoke.json"
    payload = pr.run(_args(d, b, g, out, only_seeds="1", smoke_split_val=True, lambdas="100"))
    prov = payload["provenance"]
    assert prov["smoke"] is True and prov["seeds"] == [1]
    data = pr.S3Data(d, only_seeds=[1], smoke_split_val=True)
    assert set(np.unique(data.prompt_idx % 7).tolist()) == {5}
    assert set(np.unique(data.split).tolist()) == {"train", "val", "test"}


def _label_rows(rec16, rec32, hist, free_tok, hist_tok1, hist_tok2, draft_full, intra):
    """Two prompts, equal trials; per-gate rows so the pooled rates equal the arguments."""
    rows = []
    n = 1600
    per = n // L

    def add(arm, B, key, rate, gates=range(L), depth=None):
        for p in (0, 1):
            for gt in gates:
                rows.append({"arm": arm, "budget": B, "key": key, "depth": depth, "gate": gt,
                             "prompt_idx": p, "hits": int(per * rate), "needed": per})

    add("recency", 16, 1, rec16); add("recency", 32, 1, rec32); add("recency", 16, 2, rec16)
    add("marginal", 16, 1, 0.3); add("marginal", 16, 2, 0.3)
    add("free_table", 16, 1, free_tok); add("free_tok", 16, 1, free_tok); add("free_tok", 16, 2, free_tok)
    add("history", 16, 1, hist); add("history", 16, 2, hist)
    add("history_tok", 16, 1, hist_tok1); add("history_tok", 16, 2, hist_tok2)
    add("draft_free", 16, 2, hist_tok2); add("draft_full", 16, 2, draft_full)
    add("marginal_all", 16, 0, 0.3); add("intra", 16, 1, intra, gates=range(1, L))
    for p in (0, 1):
        rows.append({"arm": "front_gates", "budget": None, "key": 1, "depth": 1, "gate": -1, "prompt_idx": p, "hits": 1, "needed": 2})
        rows.append({"arm": "front_free", "budget": None, "key": 1, "depth": None, "gate": -1, "prompt_idx": p, "hits": 1, "needed": 2})
        rows.append({"arm": "front_floor", "budget": None, "key": 1, "depth": None, "gate": -1, "prompt_idx": p, "hits": 1, "needed": 2})
    return rows


def test_labels_are_mechanical():
    kw = dict(n_boot=200, budgets=(16,), horizons=(1, 2), leads=(1,))
    c = pr.conclude(_label_rows(0.5, 0.8, 0.7, 0.6, 0.7, 0.5, 0.9, 0.5), **kw)
    lab = c["labels"]
    assert lab["stage"] == "PREFETCH-HEADROOM" and lab["cache_sufficient"] is False
    assert lab["p1_window_kill_would_fire"] is False
    assert lab["history"] == "SIGNAL" and lab["intra_forward"] == "SIGNAL"
    assert lab["address_beyond_token"] == "SIGNAL" and "adds a material margin" in lab["sideband_sentence"]
    assert lab["draft"] == "SIGNAL"
    c = pr.conclude(_label_rows(0.95, 0.99, 0.96, 0.9, 0.9, 0.5, 0.9, 0.5), **kw)
    assert c["labels"]["stage"] == "CACHE-SUFFICIENT" and c["labels"]["p1_window_kill_would_fire"] is True
    c = pr.conclude(_label_rows(0.5, 0.8, 0.52, 0.6, 0.6, 0.5, 0.5, 0.2), **kw)   # intra 0.2 < marginal_all 0.3
    lab = c["labels"]
    assert lab["stage"] == "PREFETCH-NOT-SHOWN"
    assert lab["address_beyond_token"] == "NOT-SHOWN" and "no material margin" in lab["sideband_sentence"]
    assert lab["intra_forward"] == "NEGATIVE"
    c = pr.conclude(_label_rows(0.5, 0.8, 0.7, 0.6, 0.5, 0.5, 0.9, 0.5), **kw)
    assert c["labels"]["address_beyond_token"] == "NEGATIVE" and "reads below" in c["labels"]["sideband_sentence"]
    # a missing registered arm is INCOMPLETE
    rows = [r for r in _label_rows(0.5, 0.8, 0.7, 0.6, 0.7, 0.5, 0.9, 0.5) if r["arm"] != "draft_free"]
    assert pr.conclude(rows, **kw)["labels"]["stage"] == "INCOMPLETE"
    # a missing LABEL CELL (arm present, cell absent) is INCOMPLETE, not a crash
    rows = [r for r in _label_rows(0.5, 0.8, 0.7, 0.6, 0.7, 0.5, 0.9, 0.5) if not (r["arm"] == "recency" and r["budget"] == 32)]
    lab = pr.conclude(rows, **kw)["labels"]
    assert lab["stage"] == "INCOMPLETE" and lab["missing_label_cells"]


def test_pairing_violation_is_refused():
    rows = [{"arm": "history", "budget": 16, "key": 1, "depth": None, "gate": 0, "prompt_idx": 0, "hits": 1, "needed": 8},
            {"arm": "history", "budget": 16, "key": 1, "depth": None, "gate": 0, "prompt_idx": 1, "hits": 1, "needed": 8},
            {"arm": "recency", "budget": 16, "key": 1, "depth": None, "gate": 0, "prompt_idx": 0, "hits": 1, "needed": 8},
            {"arm": "recency", "budget": 16, "key": 1, "depth": None, "gate": 0, "prompt_idx": 1, "hits": 1, "needed": 16}]
    with pytest.raises(SystemExit, match="pairing violated"):
        pr.conclude(rows, n_boot=50, budgets=(16,), horizons=(1,), leads=())


def test_layout_guards(tmp_path):
    d, b, g = make_fake_harvest(tmp_path, rule="random", n_shards=1)
    npz = d / "moe_s0.npz"
    z = dict(np.load(npz))
    z["slots"][0, 0, 0] = np.array([3, 3, 4, 5, 6, 7, 8, 9], np.int16)
    np.savez(npz, **z)
    meta = json.loads((d / "moe_s0.meta.json").read_text())
    meta["npz_sha256"] = hashlib.sha256(npz.read_bytes()).hexdigest()
    (d / "moe_s0.meta.json").write_text(json.dumps(meta))
    with pytest.raises(SystemExit, match="strictly increasing"):
        pr.S3Data(d)
    meta["npz_sha256"] = "0" * 64
    (d / "moe_s0.meta.json").write_text(json.dumps(meta))
    with pytest.raises(SystemExit, match="sha mismatch"):
        pr.S3Data(d)


def test_tool_imports_no_torch():
    """A fresh interpreter that imports only the tool must not load torch
    (checked in a subprocess: the full suite imports torch elsewhere first)."""
    code = ("import sys; sys.path.insert(0, r'%s'); import run_prefetch_readouts; "
            "print('torch' in sys.modules)" % str(ROOT / "tools"))
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)
    assert out.stdout.strip() == "False"
