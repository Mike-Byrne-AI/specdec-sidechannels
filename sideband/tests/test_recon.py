"""OQ-16 Stage-R machinery tests (CPU/numpy only, no torch, no real data).

Registered constants asserted verbatim; the end-to-end pipeline test runs
the identical code path on synthetic byproducts with sizing overrides
(n_slots, lambda grid, tiny h_dim/N) — the registered values are covered
by test_registered_constants, not the e2e run. Two e2e constructions pin
the gate semantics: slot-carried h -> STAGE-R PASS; pure-noise h ->
RECONSTRUCTION-CEILING NULL.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from sideband import recon  # noqa: E402
from sideband.stats import paired_ratio_delta_ci  # noqa: E402

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

import train_recon  # noqa: E402


# --------------------------------------------------------------------------
# registered constants
# --------------------------------------------------------------------------

def test_registered_constants():
    assert recon.RECON_LAMBDA_GRID == (1e-2, 1e-1, 1.0, 10.0, 1e2, 1e3,
                                       1e4, 1e5)
    assert recon.STALE_SEEDS == (0, 1, 2, 3, 4)
    assert recon.H_DIM == 4096
    assert recon.N_PROMPTS_PER_POP == 210
    assert tuple(r["stem"] for r in recon.RECON_RUNS) == (
        "k3_verdict_arm1", "k3_verdict_s1_arm1",
        "oq15c_verdict_arm1", "oq15c_verdict_s3_arm1")
    assert tuple(r["pop"] for r in recon.RECON_RUNS) == (
        "k3", "k3", "oq15", "oq15")
    assert recon.FEATURE_SETS == ("free", "tel", "noise")
    assert recon.PASS_LABEL == "STAGE-R PASS"
    assert recon.CEILING_LABEL == "RECONSTRUCTION-CEILING NULL"
    assert recon.DILUTION_LABEL == "RECONSTRUCTION-DILUTION NULL"
    assert train_recon.VARIANTS == ("live", 0, 1, 2, 3, 4)
    # repo-anchored (critic advisory: the guard must not be cwd-relative)
    assert train_recon.REGISTERED_OUT.is_absolute()
    assert train_recon.REGISTERED_OUT.parts[-3:] == (
        "results", "real", "oq16_stage_r.json")
    assert train_recon.REGISTERED_OUT.parents[2] == \
        Path(train_recon.__file__).resolve().parents[1]


# --------------------------------------------------------------------------
# stale permutation (DI-1 recipe verbatim)
# --------------------------------------------------------------------------

def test_stale_perm_recipe_and_determinism():
    p1 = recon.stale_perm(3, 2, 7, 20)
    p2 = recon.stale_perm(3, 2, 7, 20)
    assert np.array_equal(p1, p2)
    ref = np.random.default_rng(3 * 1_000_000 + 2 * 10_000 + 7).permutation(20)
    assert np.array_equal(p1, ref)
    assert sorted(p1.tolist()) == list(range(20))
    assert not np.array_equal(recon.stale_perm(4, 2, 7, 20), p1)
    assert not np.array_equal(recon.stale_perm(3, 2, 8, 20), p1)


# --------------------------------------------------------------------------
# gate logic (the pinned two-leg rules and labels)
# --------------------------------------------------------------------------

def test_stage_r_gate_labels():
    stales = [0.001, -0.002, 0.0005, -0.001, 0.0015]
    s = np.asarray(stales)
    bar = s.mean() + 3 * s.std(ddof=1)
    big = max(bar, s.max()) + 0.01

    g = recon.stage_r_gate((big, big - 0.001, big + 0.001),
                           (0.05, 0.01, 0.09), stales)
    assert g["label"] == recon.PASS_LABEL
    assert g["leg1"]["holds"] and g["leg2"]["holds"]

    # leg 2 straddle -> dilution null
    g = recon.stage_r_gate((big, big - 0.001, big + 0.001),
                           (0.05, -0.001, 0.10), stales)
    assert g["label"] == recon.DILUTION_LABEL

    # CI straddle on leg 1 -> ceiling null even with a huge point
    g = recon.stage_r_gate((big, -0.0001, big + 1), (0.05, 0.01, 0.09), stales)
    assert g["label"] == recon.CEILING_LABEL

    # point below the 3-sd bar -> ceiling null even when CI-positive
    below = min(bar, s.max()) - 1e-6
    g = recon.stage_r_gate((below, 1e-7, below + 1), (0.05, 0.01, 0.09), stales)
    assert g["label"] == recon.CEILING_LABEL

    # the stale-max clause is implied by the 3-sd clause at n=5 (max
    # z-score with ddof=1 is bounded by (4/sqrt(5))*sqrt(4/5) ~ 1.60 < 3;
    # critic advisory) — assert the impossibility rather than pretend to
    # cover an unreachable branch
    rng = np.random.default_rng(0)
    for _ in range(200):
        t = rng.normal(0, 1, 5)
        assert t.max() <= t.mean() + 3 * t.std(ddof=1) + 1e-12

    with pytest.raises(SystemExit):
        recon.stage_r_gate((0.1, 0.05, 0.2), (0.1, 0.05, 0.2), [0.1, 0.2])


# --------------------------------------------------------------------------
# target loading + cosine
# --------------------------------------------------------------------------

def test_h_target_cast_and_refusals():
    z = {"h": np.ones((4, 8), dtype=np.float16)}
    y = recon.h_target(z)
    assert y.dtype == np.float64 and y.shape == (4, 8)
    with pytest.raises(SystemExit):
        recon.h_target({"h": np.array([[np.nan, 1.0]], dtype=np.float16)})
    with pytest.raises(SystemExit):
        recon.h_target({"h": np.ones(4, dtype=np.float16)})


def test_centered_cosine_rows():
    p = np.array([[1.0, 0.0], [0.0, 2.0], [0.0, 0.0], [1.0, 1.0]])
    y = np.array([[2.0, 0.0], [0.0, -1.0], [1.0, 1.0], [1.0, 1.0]])
    c = recon.centered_cosine_rows(p, y)
    assert c[0] == pytest.approx(1.0)
    assert c[1] == pytest.approx(-1.0)
    assert np.isnan(c[2])
    assert c[3] == pytest.approx(1.0)


def test_multi_output_ridge_matrix_rhs():
    rng = np.random.default_rng(11)
    x = rng.normal(0, 1, (300, 5))
    w_true = rng.normal(0, 1, (5, 3))
    y = x @ w_true
    xa = recon.augment(x)
    w = recon.ridge_fit(xa.T @ xa, xa.T @ y, 1e-8)
    assert w.shape == (6, 3)
    assert np.allclose(xa @ w, y, atol=1e-6)


# --------------------------------------------------------------------------
# synthetic byproducts for the e2e path
# --------------------------------------------------------------------------

H_DIM_TEST = 8


def _mk_prompt(rng, n_blocks: int, n_slots: int, h_mode: str) -> dict:
    u = rng.uniform(size=n_blocks)
    slot_bit = (u > 0.5)
    slots = np.full((n_blocks, 4, 32), -1, dtype=np.int16)
    for b in range(n_blocks):
        k = int(rng.integers(1, min(8, n_slots)))
        ids = rng.choice(n_slots, size=k, replace=False)
        ids[0] = 3 if slot_bit[b] else 1     # the informative slot
        ids = np.unique(ids)
        row = np.full(32, -1, dtype=np.int16)
        row[:len(ids)] = ids
        slots[b] = row
    top_ids = rng.integers(0, 1000, (n_blocks, 32)).astype(np.int32)
    top_p = np.sort(rng.uniform(0, 1, (n_blocks, 32)).astype(np.float16),
                    axis=1)[:, ::-1]
    if h_mode == "slot":
        # h carried by the informative slot: strong block-aligned signal
        direction = np.arange(1, H_DIM_TEST + 1, dtype=np.float64)
        h = (np.where(slot_bit, 1.0, -1.0)[:, None] * direction[None, :]
             + rng.normal(0, 0.05, (n_blocks, H_DIM_TEST)))
    elif h_mode == "slottok":
        # the DR-4 teeth construction: the slot signal PLUS a value-paired
        # token signal sum_i p_i V[id_i] over a 12-token vocabulary (every
        # token is present in nearly every row, so the multi-hot alone says
        # little; the p-to-id pairing does). Slot signal outweighs pairing.
        top_ids = rng.integers(0, 12, (n_blocks, 32)).astype(np.int32)
        vocab_vec = np.random.default_rng(777).normal(0, 1, (12, H_DIM_TEST))
        direction = np.arange(1, H_DIM_TEST + 1, dtype=np.float64)
        pair = np.stack([top_p[b].astype(np.float64) @ vocab_vec[top_ids[b]]
                         for b in range(n_blocks)])
        h = (np.where(slot_bit, 1.0, -1.0)[:, None] * direction[None, :]
             + 0.5 * pair + rng.normal(0, 0.05, (n_blocks, H_DIM_TEST)))
    elif h_mode == "noise":
        h = rng.normal(0, 1.0, (n_blocks, H_DIM_TEST))
    elif h_mode == "prompt":
        # per-prompt constant + block noise: prompt-level statistics only,
        # zero block-aligned information — the noise twin and the stale
        # control both preserve prompt-level content, so the gate must
        # emit a ceiling null (critic gate-soundness probe)
        const = rng.normal(0, 1.0, H_DIM_TEST)
        h = const[None, :] + rng.normal(0, 0.1, (n_blocks, H_DIM_TEST))
    else:
        raise ValueError(h_mode)
    return {
        "gamma_used": np.full(n_blocks, 4, dtype=np.int16),
        "slots": slots,
        "mass16": rng.dirichlet(np.ones(16), n_blocks).astype(np.float16),
        "mass32": rng.dirichlet(np.ones(32), n_blocks).astype(np.float16),
        "mass64": rng.dirichlet(np.ones(64), n_blocks).astype(np.float16),
        "mass512": rng.dirichlet(np.ones(512), n_blocks).astype(np.float16),
        "entropy": rng.uniform(0, 5, n_blocks).astype(np.float32),
        "argmax": rng.integers(0, 1000, n_blocks).astype(np.int32),
        "top_ids": top_ids,
        "top_p": top_p,
        "h": h.astype(np.float16),
        "n_blocks": np.int64(n_blocks),
    }


def _write_run(root: Path, stem: str, n_prompts: int, rng, n_slots: int,
               h_mode: str):
    byp = root / f"{stem}.jsonl.byproduct"
    byp.mkdir(parents=True)
    shas, gen_lines = {}, []
    for i in range(n_prompts):
        z = _mk_prompt(rng, int(rng.integers(4, 8)), n_slots, h_mode)
        f = byp / f"p{i:03d}.npz"
        np.savez(f, **z)
        shas[f.name] = hashlib.sha256(f.read_bytes()).hexdigest()
        gen_lines.append(json.dumps({"prompt_idx": i, "orig_prompt_idx": i}))
    (root / f"{stem}.summary.json").write_text(
        json.dumps({"byproduct_sha256": shas}))
    (root / f"{stem}.gen.jsonl").write_text("\n".join(gen_lines) + "\n")


def _synth_root(tmp_path: Path, h_mode: str, n_prompts: int = 12) -> Path:
    rng = np.random.default_rng(23)
    root = tmp_path / f"real_{h_mode}"
    root.mkdir()
    for spec in recon.RECON_RUNS:
        _write_run(root, spec["stem"], n_prompts, rng, n_slots=8,
                   h_mode=h_mode)
    return root


TEST_GRID = (1e-2, 1.0, 1e2)


def test_pipeline_slot_signal_passes(tmp_path):
    root = _synth_root(tmp_path, "slot")
    out = tmp_path / "oq16_r_slot.json"
    res = train_recon.pipeline(root, out, n_slots=8, lambda_grid=TEST_GRID)
    s = res["summary"]
    assert s["gate"]["label"] == recon.PASS_LABEL
    assert s["delta_noise"]["live"][1] > 0        # CI lower
    assert s["delta_free"]["live"][1] > 0
    assert s["h_dim"] == H_DIM_TEST
    assert s["test_mse"]["tel"] < s["test_mse"]["free"]
    assert s["test_mse"]["tel"] < s["test_mse"]["noise"]
    # outputs on disk, meta records the overrides
    meta = json.loads((tmp_path / "oq16_r_slot.json.meta.json").read_text())
    assert meta["sizing_overrides"] == {"n_slots": 8,
                                        "lambda_grid": list(TEST_GRID)}
    # state reproduces every delta bit-exactly
    rows = [json.loads(l) for l in
            (tmp_path / "oq16_r_slot.json.state.jsonl").read_text().splitlines()]
    header, rows = rows[0], rows[1:]
    assert header["summary_sha256"].keys() == {
        r["stem"] for r in recon.RECON_RUNS}
    for v in train_recon.VARIANTS:
        by = {}
        for r in rows:
            if r["variant"] == str(v):
                by.setdefault(r["arm"], {})[(r["pop"], r["orig_prompt_idx"])] \
                    = (r["sse"], r["count"])
        keys = sorted(by["tel"])
        cnt = np.array([by["tel"][k][1] for k in keys])
        for arm in ("free", "noise"):
            assert sorted(by[arm]) == keys
            assert np.array_equal(
                np.array([by[arm][k][1] for k in keys]), cnt)
        d = paired_ratio_delta_ci(
            np.array([by["noise"][k][0] for k in keys]), cnt,
            np.array([by["tel"][k][0] for k in keys]), cnt,
            n_boot=2000, seed=0)
        assert list(d) == s["delta_noise"][str(v)]
    # gate recomputes from the summary's own numbers
    g = recon.stage_r_gate(tuple(s["delta_noise"]["live"]),
                           tuple(s["delta_free"]["live"]),
                           [s["delta_noise"][str(k)][0]
                            for k in recon.STALE_SEEDS])
    assert g == s["gate"]
    # lambda re-selected per variant (the control's own DOF)
    for fs in recon.FEATURE_SETS:
        assert set(s["chosen_lambda"][fs]) == {str(v)
                                               for v in train_recon.VARIANTS}


def test_pipeline_noise_target_is_ceiling_null(tmp_path):
    root = _synth_root(tmp_path, "noise")
    out = tmp_path / "oq16_r_noise.json"
    res = train_recon.pipeline(root, out, n_slots=8, lambda_grid=TEST_GRID,
                               write=False)
    assert res["summary"]["gate"]["label"] == recon.CEILING_LABEL


def test_pipeline_prompt_level_signal_is_ceiling_null(tmp_path):
    # h carries ONLY prompt-level statistics: if the gate emitted anything
    # but a ceiling null here, the stale control would not be pricing
    # prompt-level content and the registered ceiling-null meaning would
    # be wrong (critic's what-would-change-my-mind probe)
    root = _synth_root(tmp_path, "prompt")
    out = tmp_path / "oq16_r_prompt.json"
    res = train_recon.pipeline(root, out, n_slots=8, lambda_grid=TEST_GRID,
                               write=False)
    assert res["summary"]["gate"]["label"] == recon.CEILING_LABEL


def test_registered_shape_assert_fires_without_overrides(tmp_path):
    root = _synth_root(tmp_path, "noise", n_prompts=4)
    with pytest.raises(SystemExit, match="210"):
        train_recon.pipeline(root, tmp_path / "x.json", write=False)


def test_sha_tamper_refusal(tmp_path):
    root = _synth_root(tmp_path, "noise")
    victim = next((root / "k3_verdict_arm1.jsonl.byproduct").glob("p*.npz"))
    data = bytearray(victim.read_bytes())
    data[-1] ^= 0xFF
    victim.write_bytes(bytes(data))
    with pytest.raises(SystemExit, match="sha256 mismatch"):
        train_recon.pipeline(root, tmp_path / "x.json", n_slots=8,
                             lambda_grid=TEST_GRID, write=False)


# --------------------------------------------------------------------------
# DR-1 / DR-2 post-gate diagnostics (registered 2026-09-04, non-criterion)
# --------------------------------------------------------------------------

def test_dr_constants_and_labels():
    assert recon.FREETOK_ARM == "freetok" and recon.FREETOK_BINS == 2048
    assert recon.TRIVIAL_ARM == "trivial"
    assert recon.DR1_CONFIRMED == "DEPLOYABLE-MARGIN CONFIRMED"
    assert recon.DR1_NOT_CONFIRMED == "DEPLOYABLE-MARGIN NOT CONFIRMED"
    assert recon.DR2_ABOVE_TOKEN == "TELEMETRY-ABOVE-TOKEN"
    assert recon.DR2_NOT_EXCLUDED == "TOKEN-IDENTITY-NOT-EXCLUDED"
    ok = {"pooled": (0.2, 0.1, 0.3), "per_pop": {"a": (0.2, 0.05, 0.3),
                                                 "b": (0.1, 0.01, 0.2)}}
    assert recon.dr1_label(ok) == recon.DR1_CONFIRMED
    bad_pop = {"pooled": (0.2, 0.1, 0.3), "per_pop": {"a": (0.2, 0.05, 0.3),
                                                      "b": (0.1, -0.01, 0.2)}}
    assert recon.dr1_label(bad_pop) == recon.DR1_NOT_CONFIRMED
    bad_pooled = {"pooled": (0.1, -0.1, 0.3), "per_pop": {"a": (0.2, 0.05, 0.3)}}
    assert recon.dr1_label(bad_pooled) == recon.DR1_NOT_CONFIRMED
    assert recon.dr2_label((0.05, 0.01, 0.1)) == recon.DR2_ABOVE_TOKEN
    assert recon.dr2_label((0.05, -0.01, 0.1)) == recon.DR2_NOT_EXCLUDED


def test_freetok_features_dims_and_hash():
    rng = np.random.default_rng(5)
    z = _mk_prompt(rng, 6, 8, "noise")
    z["top_ids"] = np.array([[3, 2051, -1] + [-1] * 29] * 6, dtype=np.int32)
    x = recon.freetok_features(z, n_slots=8)
    free = recon.block_core_features(z, "free", n_slots=8)
    assert x.shape == (6, free.shape[1] + recon.FREETOK_BINS)
    assert np.array_equal(x[:, :free.shape[1]], free)
    tok = x[:, free.shape[1]:]
    # 3 and 2051 collide mod 2048 -> a single active bin; padding ignored
    assert tok.sum() == 6 and np.all(tok[:, 3] == 1.0)
    assert np.array_equal(recon.arm_features(z, "freetok", n_slots=8), x)
    assert np.array_equal(recon.arm_features(z, "tel", n_slots=8),
                          recon.block_core_features(z, "tel", n_slots=8))


def test_pipeline_modes_emit_diagnostics_and_trivial_rows(tmp_path):
    root = _synth_root(tmp_path, "slot")
    out = tmp_path / "oq16_r_dr.json"
    res = train_recon.pipeline(root, out, n_slots=8, lambda_grid=TEST_GRID,
                               feature_clip=True, freetok=True)
    s = res["summary"]
    assert s["modes"] == {"feature_clip": True, "freetok": 2048}
    assert set(s["diagnostic_labels"]) == {"dr1", "dr2"}
    assert s["diagnostic_labels"]["dr1"] in (recon.DR1_CONFIRMED,
                                             recon.DR1_NOT_CONFIRMED)
    assert s["diagnostic_labels"]["dr2"] in (recon.DR2_ABOVE_TOKEN,
                                             recon.DR2_NOT_EXCLUDED)
    rd = s["reported_deltas"]
    assert set(rd) == {"tel_vs_trivial", "tel_vs_freetok",
                       "freetok_vs_free", "freetok_vs_trivial"}
    # labels recompute from the summary's own numbers
    tvt = {"pooled": tuple(rd["tel_vs_trivial"]["pooled"]),
           "per_pop": {p: tuple(v) for p, v in
                       rd["tel_vs_trivial"]["per_pop"].items()}}
    assert recon.dr1_label(tvt) == s["diagnostic_labels"]["dr1"]
    assert recon.dr2_label(tuple(rd["tel_vs_freetok"]["pooled"])) == \
        s["diagnostic_labels"]["dr2"]
    # the slot-carried construction: telemetry beats the token arm too
    assert s["diagnostic_labels"]["dr2"] == recon.DR2_ABOVE_TOKEN
    # state carries trivial rows whose pooled ratio is the trivial MSE
    rows = [json.loads(l) for l in
            (tmp_path / "oq16_r_dr.json.state.jsonl").read_text().splitlines()][1:]
    triv = [r for r in rows if r["arm"] == "trivial"]
    assert len(triv) == s["n_test_clusters"]
    assert sum(r["sse"] for r in triv) / sum(r["count"] for r in triv) == \
        pytest.approx(s["trivial_baseline_test_mse"])
    tel = {(r["pop"], r["orig_prompt_idx"]): r for r in rows
           if r["arm"] == "tel" and r["variant"] == "live"}
    keys = sorted(tel)
    cnt = np.array([tel[k]["count"] for k in keys])
    d = paired_ratio_delta_ci(
        np.array([next(r["sse"] for r in triv
                       if (r["pop"], r["orig_prompt_idx"]) == k) for k in keys]),
        cnt, np.array([tel[k]["sse"] for k in keys]), cnt, n_boot=2000, seed=0)
    assert list(d) == rd["tel_vs_trivial"]["pooled"]
    # the four registered arms' feature dims
    assert s["feature_dims"]["freetok"] == s["feature_dims"]["free"] + 2048


def test_feature_clip_restricts_to_train_support(tmp_path):
    root = _synth_root(tmp_path, "slot")
    res = train_recon.pipeline(root, tmp_path / "x.json", n_slots=8,
                               lambda_grid=TEST_GRID, feature_clip=True,
                               write=False)
    lo, hi = res["lo_hi"]["free"]
    assert np.all(lo <= hi)
    # modes OFF: pipeline result carries no clip mode and no labels
    res0 = train_recon.pipeline(root, tmp_path / "y.json", n_slots=8,
                                lambda_grid=TEST_GRID, write=False)
    assert res0["summary"]["modes"] == {}
    assert res0["summary"]["diagnostic_labels"] == {}
    assert set(res0["summary"]["reported_deltas"]) == {"tel_vs_trivial"}
    assert list(res0["summary"]["test_mse"]) == list(recon.FEATURE_SETS)


def test_dr3_union_arms_and_label():
    rng = np.random.default_rng(9)
    z = _mk_prompt(rng, 5, 8, "slot")
    tel = recon.block_core_features(z, "tel", n_slots=8)
    noise = recon.block_core_features(z, "noise", n_slots=8)
    tok = recon.tok_block(z)
    u = recon.arm_features(z, "union", n_slots=8)
    un = recon.arm_features(z, "unionnoise", n_slots=8)
    assert u.shape == (5, tel.shape[1] + 2048) and un.shape == u.shape
    assert np.array_equal(u[:, :tel.shape[1]], tel)
    assert np.array_equal(un[:, :tel.shape[1]], noise)
    assert np.array_equal(u[:, tel.shape[1]:], tok)
    assert np.array_equal(un[:, tel.shape[1]:], tok)
    assert recon.DR3_BEYOND == "TELEMETRY-BEYOND-P"
    assert recon.DR3_NOT_BEYOND == "TELEMETRY-NOT-BEYOND-P"
    assert recon.dr3_label((0.02, 0.01, 0.03), (0.02, 0.01, 0.03)) == recon.DR3_BEYOND
    assert recon.dr3_label((0.02, -0.01, 0.03), (0.02, 0.01, 0.03)) == recon.DR3_NOT_BEYOND
    assert recon.dr3_label((0.02, 0.01, 0.03), (0.0, -0.01, 0.01)) == recon.DR3_NOT_BEYOND


def test_pipeline_union_mode(tmp_path):
    root = _synth_root(tmp_path, "slot")
    with pytest.raises(SystemExit, match="needs --freetok"):
        train_recon.pipeline(root, tmp_path / "u0.json", n_slots=8,
                             lambda_grid=TEST_GRID, union=True, write=False)
    res = train_recon.pipeline(root, tmp_path / "u.json", n_slots=8,
                               lambda_grid=TEST_GRID, feature_clip=True,
                               freetok=True, union=True)
    s = res["summary"]
    assert s["modes"] == {"feature_clip": True, "freetok": 2048, "union": True}
    assert list(s["test_mse"]) == ["free", "tel", "noise", "freetok",
                                   "union", "unionnoise"]
    rd = s["reported_deltas"]
    assert {"union_vs_freetok", "union_vs_unionnoise", "union_vs_tel"} <= set(rd)
    assert recon.dr3_label(tuple(rd["union_vs_freetok"]["pooled"]),
                           tuple(rd["union_vs_unionnoise"]["pooled"])) == \
        s["diagnostic_labels"]["dr3"]
    # slot-carried h, random tokens: the union adds the slot signal on top
    # of the token arm and beats its alignment-destroyed anchor
    assert s["diagnostic_labels"]["dr3"] == recon.DR3_BEYOND
    assert s["feature_dims"]["union"] == s["feature_dims"]["tel"] + 2048


def test_dr4_hash_block_and_label():
    # hash B: a genuinely different collision pattern from id mod 2048,
    # near-uniform over the Llama-3 vocabulary
    ids = np.arange(0, 128256)
    hb = recon.tokb_bins(ids)
    assert hb.dtype == np.int64 and hb.min() >= 0 and hb.max() < 2048
    assert np.mean(hb == (ids % 2048)) < 0.01
    load = np.bincount(hb, minlength=2048)
    assert load.max() <= 1.5 * load.mean() and load.min() >= 0.5 * load.mean()
    assert np.array_equal(recon.tokb_bins(np.array([-1, 5])),
                          recon.tokb_bins(np.array([-1, 5])))
    # the value-paired block: top_p lands at the hashed bin, padding ignored
    rng = np.random.default_rng(5)
    z = _mk_prompt(rng, 3, 8, "noise")
    z["top_ids"] = np.array([[3, 2051, 7] + [-1] * 29] * 3, dtype=np.int32)
    p = np.zeros((3, 32), dtype=np.float16)
    p[:, 0], p[:, 1], p[:, 2] = 0.5, 0.25, 0.125
    z["top_p"] = p
    b3, b2051, b7 = recon.tokb_bins(np.array([3, 2051, 7])).tolist()
    assert len({b3, b2051, b7}) == 3, "fixture ids must not collide"
    tb = recon.tokb_block(z)
    assert tb.shape == (3, 2048)
    assert tb[0, b3] == 0.5 and tb[0, b2051] == 0.25 and tb[0, b7] == 0.125
    assert tb.sum() == pytest.approx(3 * 0.875)
    # within-row collision sums
    z2 = dict(z)
    z2["top_ids"] = np.array([[3, 3, 7] + [-1] * 29] * 3, dtype=np.int32)
    assert recon.tokb_block(z2)[0, b3] == 0.75
    # shape refusal
    z3 = dict(z)
    z3["top_p"] = p[:, :31]
    with pytest.raises(SystemExit):
        recon.tokb_block(z3)
    # FREETOK2 = FREETOK ++ TOK_B at UNION's dims; dispatch agrees
    x = recon.freetok2_features(z, n_slots=8)
    ft = recon.freetok_features(z, n_slots=8)
    assert x.shape == (3, ft.shape[1] + 2048)
    assert np.array_equal(x[:, :ft.shape[1]], ft)
    assert np.array_equal(x[:, ft.shape[1]:], tb)
    assert np.array_equal(recon.arm_features(z, "freetok2", n_slots=8), x)
    # equal dims to UNION at the REGISTERED slot count (4 x 512 = 2048)
    assert recon.freetok2_features(z, n_slots=512).shape[1] == 4753 == \
        recon.arm_features(z, "union", n_slots=512).shape[1]
    # labels
    assert recon.FREETOK2_ARM == "freetok2"
    assert (recon.TOKB_MULT, recon.TOKB_SALT, recon.TOKB_SHIFT) == \
        (2654435761, 0x9E3779B9, 21)
    assert recon.DR4_CONFIRMED == "BEYOND-P CONFIRMED"
    assert recon.DR4_REDUCES == "REDUCES-TO-ENCODING"
    assert recon.DR4_TOOTHLESS == "COMPARATOR-TOOTHLESS"
    assert recon.dr4_label((0.03, 0.01, 0.05), (0.03, 0.01, 0.05)) == \
        recon.DR4_CONFIRMED
    assert recon.dr4_label((0.01, -0.01, 0.03), (0.03, 0.01, 0.05)) == \
        recon.DR4_REDUCES
    assert recon.dr4_label((-0.02, -0.04, -0.01), (0.03, 0.01, 0.05)) == \
        recon.DR4_REDUCES
    assert recon.dr4_label((0.03, 0.01, 0.05), (0.0, -0.01, 0.01)) == \
        recon.DR4_TOOTHLESS


def test_pipeline_freetok2_mode(tmp_path):
    root = _synth_root(tmp_path, "slottok")
    with pytest.raises(SystemExit, match="needs --union"):
        train_recon.pipeline(root, tmp_path / "f0.json", n_slots=8,
                             lambda_grid=TEST_GRID, freetok=True,
                             freetok2=True, write=False)
    res = train_recon.pipeline(root, tmp_path / "f.json", n_slots=8,
                               lambda_grid=TEST_GRID, feature_clip=True,
                               freetok=True, union=True, freetok2=True)
    s = res["summary"]
    assert s["modes"] == {"feature_clip": True, "freetok": 2048,
                          "union": True, "freetok2": True}
    assert list(s["test_mse"]) == ["free", "tel", "noise", "freetok",
                                   "union", "unionnoise", "freetok2"]
    rd = s["reported_deltas"]
    assert {"union_vs_freetok2", "freetok2_vs_freetok", "freetok2_vs_free",
            "tel_vs_freetok2"} <= set(rd)
    assert recon.dr4_label(tuple(rd["union_vs_freetok2"]["pooled"]),
                           tuple(rd["freetok2_vs_freetok"]["pooled"])) == \
        s["diagnostic_labels"]["dr4"]
    assert s["feature_dims"]["freetok2"] == s["feature_dims"]["free"] + 4096
    # (equal to UNION's dims at the registered n_slots=512 only; the sized
    # run has 4x8 slot dims — asserted in test_dr4_hash_block_and_label)
    # the construction: the value pairing gives the comparator teeth and
    # the slot signal outweighs it
    assert rd["freetok2_vs_freetok"]["pooled"][1] > 0
    assert s["diagnostic_labels"]["dr4"] == recon.DR4_CONFIRMED
    # state rows carry the new arm for every variant
    rows = [json.loads(l) for l in
            (tmp_path / "f.json.state.jsonl").read_text().splitlines()][1:]
    assert sum(r["arm"] == "freetok2" for r in rows) == \
        s["n_test_clusters"] * len(train_recon.VARIANTS)
    # token-free slot construction: the comparator is toothless (random
    # tokens carry nothing about h)
    root0 = _synth_root(tmp_path, "slot")
    s0 = train_recon.pipeline(root0, tmp_path / "g.json", n_slots=8,
                              lambda_grid=TEST_GRID, feature_clip=True,
                              freetok=True, union=True, freetok2=True,
                              write=False)["summary"]
    assert s0["diagnostic_labels"]["dr4"] == recon.DR4_TOOTHLESS


# --------------------------------------------------------------------------
# STAGE A (OQ-16 STAGE-A FREEZE): CPU-side actuator machinery
# --------------------------------------------------------------------------

def test_block_arithmetic_matches_logged_byproduct():
    # the first six blocks of the committed k3_verdict_arm1 p000 byproduct
    # (prompt_len 44; read 2026-09-04): accepted [4,4,1,0,2,1] logged
    # anchor_pos [43,47,52,54,55,58]
    spans = recon.block_token_spans(44, [4, 4, 1, 0, 2, 1])
    assert spans.tolist() == [[44, 48], [49, 53], [54, 55], [56, 56],
                              [57, 59], [60, 61]]
    assert recon.anchor_positions_from_spans(44, spans).tolist() == \
        [43, 47, 52, 54, 55, 58]
    g = recon.guide_block_per_row(44, spans, 62)
    assert g[:43].tolist() == [-1] * 43
    assert g[43:48].tolist() == [0] * 5           # prefill row + 4 more
    assert g[48:53].tolist() == [1] * 5
    assert g[53:55].tolist() == [2, 2]
    assert g[55] == 3
    assert g[56:59].tolist() == [4] * 3
    assert g[59:61].tolist() == [5, 5]
    assert g[61] == -1                              # last row: no target
    with pytest.raises(ValueError):
        recon.guide_block_per_row(44, spans, 61)
    with pytest.raises(ValueError):
        recon.block_token_spans(44, [1, -1])
    assert recon.anchor_positions_from_spans(5, np.zeros((0, 2), int)).shape == (0,)


def test_adapter_reference_arithmetic():
    rng = np.random.default_rng(3)
    h = rng.normal(0, 2, 16)
    ln_w, ln_b = rng.normal(1, 0.1, 16), rng.normal(0, 0.1, 16)
    x = recon.layer_norm_np(h, ln_w, ln_b)
    mu, var = h.mean(), ((h - h.mean()) ** 2).mean()
    assert np.allclose(x, (h - mu) / np.sqrt(var + 1e-5) * ln_w + ln_b)
    u = rng.normal(0, 1, (16, 4))
    v0 = np.zeros((3, 4, 6))
    assert np.array_equal(recon.adapter_forward_np(h, ln_w, ln_b, u, v0),
                          np.zeros((3, 6)))
    v = rng.normal(0, 1, (3, 4, 6))
    d = recon.adapter_forward_np(h, ln_w, ln_b, u, v)
    g = x @ u
    assert d.shape == (3, 6)
    assert np.allclose(d, np.stack([g @ v[l] for l in range(3)]))


def _committed_dr4(tmp_path, root):
    out = tmp_path / "oq16_stage_r_dr4.json"
    train_recon.pipeline(root, out, n_slots=8, lambda_grid=TEST_GRID,
                         feature_clip=True, freetok=True, union=True,
                         freetok2=True)
    return out


def test_stage_a_export_end_to_end(tmp_path):
    root = _synth_root(tmp_path, "slottok")
    committed = _committed_dr4(tmp_path, root)
    arms = ("freetok", "union")
    npz = tmp_path / "w.npz"
    hh = tmp_path / "hhat"
    summ = tmp_path / "export.json"
    res = train_recon.stage_a_export(
        root, arms, n_slots=8, lambda_grid=TEST_GRID, committed=committed,
        npz_path=npz, hhat_dir=hh, summary_path=summ, self_check_blocks=20)
    s = json.loads(summ.read_text())
    assert s["arms"] == list(arms)
    assert s["binding"]["bound_fields"] == list(train_recon.STAGE_A_BIND_FIELDS)
    dr4 = json.loads(committed.read_text())
    assert s["lambda_by_arm"] == {a: dr4["chosen_lambda"][a]["live"] for a in arms}
    # weight-level binding to the DR-4 live TRAIN fit (measured + bounded)
    for a in arms:
        assert s["weight_binding"][a]["max_abs_dev"] <= train_recon.STAGE_A_WEIGHT_TOL
    assert s["n_folds"] == 5 and set(s["folds"]) == {"0", "1", "2", "3", "4"}
    # every fold fits the other 4/5 of BOTH populations: 12 prompts per
    # pop -> folds of 3/3/2/2/2 by the pinned permutation
    fi = train_recon.fold_index(12)
    assert sorted(np.bincount(fi).tolist()) == [2, 2, 2, 3, 3]
    # h_hat: one file per prompt per run, fold by the pinned permutation
    files = sorted(hh.glob("*/p*.npz"))
    assert len(files) == 4 * 12 and len(s["hhat_sha256"]) == 4 * 12
    for f in files:
        z = np.load(f)
        pid = int(z["orig_prompt_idx"])
        assert str(z["fold"]) == str(int(fi[pid]))
        for a in arms:
            assert z[a].dtype == np.float32 and z[a].shape[1] == H_DIM_TEST
        assert hashlib.sha256(f.read_bytes()).hexdigest() == \
            s["hhat_sha256"][f"{f.parent.name}/{f.name}"]
    # the exported npz + live class reproduce the full-fit arithmetic
    z = np.load(npz)
    assert set(z.files) >= {"target_mu", "target_sd"} | {
        f"{a}_{k}" for a in arms for k in ("mu", "sd", "lo", "hi", "w")}
    assert hashlib.sha256(npz.read_bytes()).hexdigest() == s["weights_sha256"]
    lr = recon.LiveReconstructor(npz, "union", n_slots=8)
    run0 = res["res"]["runs"][0]
    pid, zb = next(train_recon.iter_prompts(run0))
    x = recon.arm_features(zb, "union", n_slots=8)
    manual = lr.t_mu + lr.t_sd * (recon.augment(lr.std.apply(
        np.clip(x, lr.lo, lr.hi))) @ lr.w)
    assert np.array_equal(lr.reconstruct_rows(x), manual)
    summ0 = {k: np.asarray(zb[k])[0] for k in
             ("mass16", "mass32", "mass64", "mass512", "entropy", "argmax",
              "top_ids", "top_p")}
    assert np.array_equal(lr.reconstruct(summ0, np.asarray(zb["slots"])[0]),
                          lr.reconstruct_rows(x[:1])[0])
    assert s["self_check_blocks"] >= 20
    assert s["self_check_max_batch_deviation"] <= train_recon.STAGE_A_BATCH_TOL
    # the cross-fit beats the trivial predictor on every fold's readout
    for fold in s["folds"].values():
        assert fold["std_mse"]["union"] < fold["trivial_std_mse"]
        assert fold["n_pred_prompt_runs"] in (8, 12)   # 2 or 3 prompts x 4 runs
    # binding gate: a tampered committed summary is refused
    d = json.loads(committed.read_text())
    d["test_mse"]["union"] += 1e-9
    committed.write_text(json.dumps(d))
    with pytest.raises(SystemExit, match="BINDING GATE REFUSED"):
        train_recon.stage_a_export(
            root, arms, n_slots=8, lambda_grid=TEST_GRID, committed=committed,
            npz_path=tmp_path / "w2.npz", hhat_dir=tmp_path / "hh2",
            summary_path=tmp_path / "e2.json", self_check_blocks=5)


def test_steer_inject_row_assembly_and_contracts(tmp_path):
    from sideband.real import steer_inject as si   # no torch at import
    assert si.INJECT_ARMS == {"oracle_h": "h", "free_inject": "freetok",
                              "tel_inject": "union"}
    assert si.ADAPTER_RANK == 512 and si.ADAPTER_LN_EPS == 1e-5
    prompt_ids = np.arange(100, 144)                     # prompt_len 44
    gen = {"prompt_len": 44, "generated_ids": list(range(18))}   # 5+5+2+1+3+2
    byp = {"accepted": np.array([4, 4, 1, 0, 2, 1], np.int16),
           "anchor_pos": np.array([43, 47, 52, 54, 55, 58], np.int32),
           "n_blocks": np.int64(6)}
    vec = np.zeros((6, 8))
    a = si.assemble_prompt(prompt_ids, gen, byp, vec)
    assert a["ids"].shape == (62,) and a["ids"][44] == 0 and a["ids"][43] == 143
    assert a["guide"][43:48].tolist() == [0] * 5 and a["guide"][61] == -1
    assert a["anchors"].tolist() == [43, 47, 52, 54, 55, 58]
    bad = dict(byp)
    bad["anchor_pos"] = np.array([43, 48, 52, 54, 55, 58], np.int32)
    with pytest.raises(ValueError, match="DATA CONTRACT"):
        si.assemble_prompt(prompt_ids, gen, bad, vec)
    with pytest.raises(ValueError, match="DATA CONTRACT"):
        si.assemble_prompt(prompt_ids, {"prompt_len": 44,
                                        "generated_ids": list(range(17))}, byp, vec)
    with pytest.raises(ValueError, match="prompt_len"):
        si.assemble_prompt(prompt_ids[:-1], gen, byp, vec)
    with pytest.raises(ValueError, match="n_blocks"):
        si.assemble_prompt(prompt_ids, gen, byp, np.zeros((5, 8)))
    # h_hat loading is sha-bound to the export summary
    d = tmp_path / "hh" / "k3_verdict_arm1"
    d.mkdir(parents=True)
    f = d / "p007.npz"
    np.savez(f, union=np.ones((3, 8), np.float16), fold=np.array("A"))
    summ = {"hhat_sha256": {"k3_verdict_arm1/p007.npz":
                            hashlib.sha256(f.read_bytes()).hexdigest()}}
    x = si.load_hhat(tmp_path / "hh", summ, "k3_verdict_arm1", 7, "union")
    assert x.dtype == np.float64 and x.shape == (3, 8)
    with pytest.raises(SystemExit):
        si.load_hhat(tmp_path / "hh", summ, "k3_verdict_arm1", 8, "union")
    np.savez(f, union=np.zeros((3, 8), np.float16), fold=np.array("A"))
    with pytest.raises(SystemExit, match="sha256"):
        si.load_hhat(tmp_path / "hh", summ, "k3_verdict_arm1", 7, "union")
    assert si.ids_sha([1, 2, 3]) == hashlib.sha256(b"[1, 2, 3]").hexdigest()


def test_k3config_inject_rules():
    from sideband.real.k3_live import K3Config
    from sideband.scheduler import SchedulerPolicy
    fixed = SchedulerPolicy("fixed", gamma_base=4, gamma_max=4)
    with pytest.raises(ValueError, match="live reader"):
        K3Config(policy=fixed, inject=object())
    from sideband.scheduler import Thresholds
    thr = Thresholds(kind="draft_conf", stop_level=0.5, extend_level=0.5,
                     stop=(0.5, 0.5), extend=0.5)
    sched = SchedulerPolicy("draft_conf", gamma_base=4, gamma_max=6, thresholds=thr)
    with pytest.raises(ValueError, match="fixed schedule"):
        K3Config(policy=sched, reader=object(), inject=object())
    cfg = K3Config(policy=fixed, reader=object(), inject=object())
    assert cfg.inject is not None
    assert K3Config(policy=fixed).inject is None


def test_cli_stage_a_export_refuses_mode_flags(tmp_path):
    res = subprocess.run(
        [sys.executable, str(TOOLS / "train_recon.py"),
         "--data-root", str(tmp_path), "--stage-a-export", "union",
         "--freetok2"],
        capture_output=True, text=True,
        cwd=str(Path(__file__).resolve().parents[1]))
    assert res.returncode != 0
    assert "takes no sizing/mode flags" in (res.stdout + res.stderr)


def test_cli_guard_refuses_freetok2_on_registered_out(tmp_path):
    res = subprocess.run(
        [sys.executable, str(TOOLS / "train_recon.py"),
         "--data-root", str(tmp_path), "--freetok", "--union", "--freetok2",
         "--out", str(train_recon.REGISTERED_OUT)],
        capture_output=True, text=True,
        cwd=str(Path(__file__).resolve().parents[1]))
    assert res.returncode != 0
    assert "registered-outs guard" in (res.stdout + res.stderr)


def test_cli_guard_refuses_mode_overrides_on_registered_out(tmp_path):
    res = subprocess.run(
        [sys.executable, str(TOOLS / "train_recon.py"),
         "--data-root", str(tmp_path), "--feature-clip",
         "--out", str(train_recon.REGISTERED_OUT)],
        capture_output=True, text=True,
        cwd=str(Path(__file__).resolve().parents[1]))
    assert res.returncode != 0
    assert "registered-outs guard" in res.stderr


def test_cli_guard_refuses_registered_out(tmp_path):
    res = subprocess.run(
        [sys.executable, str(TOOLS / "train_recon.py"),
         "--data-root", str(tmp_path), "--n-slots", "8",
         "--out", str(train_recon.REGISTERED_OUT)],
        capture_output=True, text=True,
        cwd=str(Path(__file__).resolve().parents[1]))
    assert res.returncode != 0
    assert "registered-outs guard" in res.stderr


def test_cli_end_to_end(tmp_path):
    root = _synth_root(tmp_path, "slot")
    out = tmp_path / "cli_out.json"
    res = subprocess.run(
        [sys.executable, str(TOOLS / "train_recon.py"),
         "--data-root", str(root), "--out", str(out),
         "--n-slots", "8", "--lambdas", "0.01,1.0,100.0"],
        capture_output=True, text=True)
    assert res.returncode == 0, res.stderr
    s = json.loads(out.read_text())
    assert s["gate"]["label"] in (recon.PASS_LABEL, recon.CEILING_LABEL,
                                  recon.DILUTION_LABEL)
    assert "[stage-r] label:" in res.stdout
