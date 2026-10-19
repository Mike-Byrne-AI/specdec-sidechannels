"""OQ-15 Stage-I machinery tests (CPU/numpy only, no torch, no real data).

The registered constants are asserted verbatim; the end-to-end tool test
monkeypatches ONLY sizing knobs (N_SLOTS, LAMBDA_GRID) so the identical
code path runs on synthetic data in seconds — the constants' registered
values are covered by test_registered_constants, not by the e2e run.
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

from sideband import outcome_head as oh  # noqa: E402
from sideband.scheduler import probe_input  # noqa: E402


# --------------------------------------------------------------------------
# registered constants
# --------------------------------------------------------------------------

def test_registered_constants():
    assert oh.SPLIT_SEED == 15
    assert (oh.TRAIN_FRAC, oh.VAL_FRAC) == (0.6, 0.2)
    assert oh.NOISE_SHIFT == 17
    assert oh.LAMBDA_GRID == (1e-4, 1e-3, 1e-2, 1e-1, 1.0, 10.0)
    assert oh.GATE_OFFSETS == (1, 2, 3, 4)
    assert oh.FEATURE_SETS == ("free", "tel", "noise")
    assert oh.N_SLOTS == 512


def test_split_registered_sizes():
    s = oh.stage1_split(210)
    assert (len(s["train"]), len(s["val"]), len(s["test"])) == (126, 42, 42)
    allidx = np.concatenate([s["train"], s["val"], s["test"]])
    assert sorted(allidx.tolist()) == list(range(210))
    s2 = oh.stage1_split(210)
    for k in s:
        assert np.array_equal(s[k], s2[k])  # deterministic


# --------------------------------------------------------------------------
# noise shift (F-16 recipe)
# --------------------------------------------------------------------------

def test_noise_shift_bijection_and_self_map():
    for n in (2, 5, 16, 18, 84):
        idx = oh.noise_shift_index(n)
        assert sorted(idx.tolist()) == list(range(n))
        assert not np.array_equal(idx, np.arange(n))
        assert not oh.noise_self_maps(n)
    for n in (1, 17):
        assert oh.noise_self_maps(n)
        assert np.array_equal(oh.noise_shift_index(n), np.arange(n))


# --------------------------------------------------------------------------
# synthetic byproduct rows
# --------------------------------------------------------------------------

def _mk_prompt(rng: np.random.Generator, n_blocks: int, n_slots: int,
               gamma: int = 4, informative: bool = True) -> dict:
    u = rng.uniform(size=n_blocks)
    slots = np.full((n_blocks, 4, 32), -1, dtype=np.int16)
    for b in range(n_blocks):
        k = int(rng.integers(1, min(8, n_slots)))
        ids = rng.choice(n_slots, size=k, replace=False)
        # the informative slot: present iff the latent is high; with informative=False
        # (the null control of 2026-10-16) the same slot is drawn independently of the latent
        ids[0] = (3 if u[b] > 0.5 else 1) if informative else int(rng.choice([1, 3]))
        ids = np.unique(ids)  # sorted unique; may shrink after overwrite
        row = np.full(32, -1, dtype=np.int16)
        row[:len(ids)] = ids
        slots[b] = row  # same set at every layer — fine for these tests
    ana = np.full((n_blocks, 6), np.nan, dtype=np.float32)
    ana[:, :gamma] = np.clip(
        0.3 + 0.4 * u[:, None] + rng.normal(0, 0.05, (n_blocks, gamma)), 0, 1)
    acc = np.full((n_blocks, 6), -1, dtype=np.int8)
    for b in range(n_blocks):
        a = int(rng.integers(0, gamma + 1))
        acc[b, :a] = 1
        if a < gamma:
            acc[b, a] = 0
    return {
        "gamma_used": np.full(n_blocks, gamma, dtype=np.int16),
        "slots": slots,
        "mass16": rng.dirichlet(np.ones(16), n_blocks).astype(np.float16),
        "mass32": rng.dirichlet(np.ones(32), n_blocks).astype(np.float16),
        "mass64": rng.dirichlet(np.ones(64), n_blocks).astype(np.float16),
        "mass512": rng.dirichlet(np.ones(512), n_blocks).astype(np.float16),
        "entropy": rng.uniform(0, 5, n_blocks).astype(np.float32),
        "argmax": rng.integers(0, 1000, n_blocks).astype(np.int32),
        "top_ids": rng.integers(0, 1000, (n_blocks, 32)).astype(np.int32),
        "top_p": np.sort(rng.uniform(0, 1, (n_blocks, 32)).astype(np.float16),
                         axis=1)[:, ::-1],
        "q_sig": rng.uniform(0.01, 0.99, (n_blocks, 2)).astype(np.float32),
        "analytic": ana,
        "acc_flags": acc,
    }


def test_core_features_are_probe_input():
    rng = np.random.default_rng(0)
    z = _mk_prompt(rng, 5, 8)
    free = oh.block_core_features(z, "free", n_slots=8)
    tel = oh.block_core_features(z, "tel", n_slots=8)
    noise = oh.block_core_features(z, "noise", n_slots=8)
    assert free.shape == (5, 657) and tel.shape == (5, 657 + 4 * 8)
    shift = oh.noise_shift_index(5)
    for b in range(5):
        summ = {k: np.asarray(z[k])[b] for k in oh.SUMMARY_KEYS}
        assert np.allclose(free[b], probe_input(summ))
        assert np.allclose(tel[b], probe_input(summ, slots=z["slots"][b], n_slots=8))
        assert np.allclose(
            noise[b], probe_input(summ, slots=z["slots"][shift[b]], n_slots=8))
    # noise differs from tel only in the slot block
    assert np.allclose(noise[:, :657], tel[:, :657])


def test_qsig_availability_rule_and_nan_refusal():
    rng = np.random.default_rng(1)
    z = _mk_prompt(rng, 4, 8)
    assert oh.qsig_cols(z, 1).shape == (4, 1)
    for off in (2, 3, 4):
        assert oh.qsig_cols(z, off).shape == (4, 2)
    z["q_sig"] = z["q_sig"].copy()
    z["q_sig"][2, 1] = np.nan
    assert oh.qsig_cols(z, 1).shape == (4, 1)  # NaN col not consumed
    with pytest.raises(SystemExit):
        oh.qsig_cols(z, 3)


def test_target_masking_semantics():
    rng = np.random.default_rng(2)
    z = _mk_prompt(rng, 6, 8)
    z["gamma_used"] = np.array([4, 4, 2, 4, 1, 4], dtype=np.int16)
    y3 = oh.analytic_target(z, 3)
    assert len(y3) == 4  # rows with gamma_used >= 3
    assert np.all((y3 >= 0) & (y3 <= 1))
    m, yb = oh.binary_target(z, 2)
    assert len(yb) == int(m.sum())
    assert set(np.unique(yb)).issubset({0.0, 1.0})
    # unreached (-1) positions are excluded, not treated as rejections
    flags = np.asarray(z["acc_flags"])[:, 1]
    assert int(m.sum()) == int((flags >= 0).sum())


# --------------------------------------------------------------------------
# standardizer + ridge
# --------------------------------------------------------------------------

def test_standardizer_moments_and_zero_variance():
    rng = np.random.default_rng(3)
    x = rng.normal(2.0, 3.0, (500, 4))
    x[:, 2] = 7.0  # zero-variance
    st = oh.Standardizer.from_moments(x.sum(0), (x * x).sum(0), len(x))
    xs = st.apply(x)
    assert np.allclose(xs.mean(0), 0, atol=1e-9)
    assert np.allclose(xs[:, 2], 0.0)
    assert np.allclose(xs[:, 0].std(), 1.0, atol=1e-6)


def test_ridge_recovers_linear_signal_and_unpenalized_intercept():
    rng = np.random.default_rng(4)
    x = rng.normal(0, 1, (400, 6))
    w_true = rng.normal(0, 0.1, 6)
    y = np.clip(0.5 + x @ w_true, 0, 1)
    st = oh.Standardizer.from_moments(x.sum(0), (x * x).sum(0), len(x))
    xa = oh.augment(st.apply(x))
    gram, xty = xa.T @ xa, xa.T @ y
    pred = oh.predict_clipped(oh.ridge_fit(gram, xty, 1e-6), st.apply(x))
    assert float(((pred - y) ** 2).mean()) < 1e-3
    # huge lambda kills the slopes but NOT the intercept: pred -> mean(y)
    pred_big = oh.predict_clipped(oh.ridge_fit(gram, xty, 1e9), st.apply(x))
    assert np.allclose(pred_big, y.mean(), atol=1e-3)
    # determinism
    w1 = oh.ridge_fit(gram, xty, 0.1)
    w2 = oh.ridge_fit(gram.copy(), xty.copy(), 0.1)
    assert np.array_equal(w1, w2)
    assert pred.min() >= 0.0 and pred.max() <= 1.0


# --------------------------------------------------------------------------
# sidebar metrics
# --------------------------------------------------------------------------

def test_auc_and_precision_at_coverage():
    s = np.array([0.9, 0.8, 0.7, 0.2, 0.1])
    y = np.array([1.0, 1.0, 1.0, 0.0, 0.0])
    assert oh.auc_score(s, y) == 1.0
    assert oh.auc_score(-s, y) == 0.0
    assert np.isnan(oh.auc_score(s, np.ones(5)))
    # midranks: all-tied scores -> 0.5
    assert abs(oh.auc_score(np.ones(6), np.array([1, 1, 1, 0, 0, 0.0])) - 0.5) < 1e-12
    prec, cov = oh.precision_at_coverage(s, y, coverage=0.4)
    assert prec == 1.0 and cov >= 0.4


# --------------------------------------------------------------------------
# end-to-end tool run on a synthetic data root
# --------------------------------------------------------------------------

def _write_run(root: Path, stem: str, n_prompts: int, rng, n_slots: int,
               gamma: int = 4, informative: bool = True):
    byp = root / f"{stem}.jsonl.byproduct"
    byp.mkdir(parents=True)
    shas, gen_lines = {}, []
    for i in range(n_prompts):
        z = _mk_prompt(rng, int(rng.integers(3, 6)), n_slots, gamma=gamma, informative=informative)
        f = byp / f"p{i:03d}.npz"
        np.savez(f, **z)
        shas[f.name] = hashlib.sha256(f.read_bytes()).hexdigest()
        gen_lines.append(json.dumps({"prompt_idx": i, "orig_prompt_idx": i}))
    (root / f"{stem}.summary.json").write_text(
        json.dumps({"byproduct_sha256": shas}))
    (root / f"{stem}.gen.jsonl").write_text("\n".join(gen_lines) + "\n")


def _run_tool(root: Path, out: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(Path(__file__).resolve().parents[1] / "tools"
                             / "train_outcome_head.py"),
         "--data-root", str(root), "--out", str(out),
         "--n-slots", "8", "--lambdas", "0.01,1.0"],
        capture_output=True, text=True)


@pytest.fixture()
def synth_root(tmp_path):
    rng = np.random.default_rng(7)
    root = tmp_path / "real"
    root.mkdir()
    for stem in ("k3_verdict_arm1", "k3_verdict_s1_arm1"):
        _write_run(root, stem, 20, rng, n_slots=8)
    for stem in ("k3_val_arm1", "k3_tapcal_arm1"):
        _write_run(root, stem, 6, rng, n_slots=8)
    return root


def test_tool_end_to_end(synth_root, tmp_path):
    # shrink ONLY sizing knobs (recorded as overrides in the evidence);
    # the registered values are asserted in test_registered_constants
    out = tmp_path / "oq15_stage1.json"
    res = _run_tool(synth_root, out)
    assert res.returncode == 0, res.stderr
    summary = json.loads(out.read_text())
    assert summary["sizing_overrides"] == {"n_slots": 8,
                                           "lambda_grid": [0.01, 1.0]}
    assert set(summary["chosen_lambda"].values()) <= {0.01, 1.0}
    assert isinstance(summary["stage1_pass"], bool)
    branch = summary["branch"]
    assert ("PASS" in branch) == summary["stage1_pass"]
    lo, hi = summary["delta_noise"]["ci95"]
    assert lo <= summary["delta_noise"]["delta"] <= hi
    assert summary["n_test_clusters"] == 4  # 20 * 0.2
    # state file: header + one row per (run, test prompt)
    lines = [json.loads(l) for l in
             (Path(str(out) + ".state.jsonl")).read_text().splitlines()]
    assert lines[0].get("header") is True
    assert len(lines) == 1 + 2 * 4
    # per-head rows carry se/n and free/tel/noise are paired per row
    row = lines[1]
    for fs in ("free", "tel", "noise"):
        assert row[f"{fs}_off2"]["n"] == row["free_off2"]["n"]
        assert row[f"{fs}_off2"]["se"] <= row[f"{fs}_off2"]["n"]  # SE<=1/pos
    # meta written, overrides recorded there too
    meta = json.loads((Path(str(out) + ".meta.json")).read_text())
    assert meta["sizing_overrides"] == summary["sizing_overrides"]
    # overwrite refusal
    res2 = _run_tool(synth_root, out)
    assert res2.returncode != 0


def test_head_scorer_matches_predict_clipped(tmp_path):
    # HeadScorer (STAGE-C FREEZE live path) must bit-equal the training
    # pipeline's predict_clipped on identical inputs
    rng = np.random.default_rng(11)
    core_dim = 7
    arrays = {}
    params = {}
    for fam in ("free", "tel"):
        for off in (1, 2, 3, 4, 5):
            d = core_dim + min(off, 2)
            mu = rng.normal(0, 1, d)
            sd = np.abs(rng.normal(1, 0.2, d))
            w = rng.normal(0, 0.5, d + 1)
            arrays[f"{fam}_off{off}_mu"] = mu
            arrays[f"{fam}_off{off}_sd"] = sd
            arrays[f"{fam}_off{off}_w"] = w
            params[(fam, off)] = (mu, sd, w)
    npz = tmp_path / "heads.npz"
    np.savez(npz, **arrays)
    sc = oh.HeadScorer(npz, "free")
    core = rng.normal(0, 1, core_dim)
    qs = [0.3, 0.7]
    for off in (1, 2, 3, 4, 5):
        mu, sd, w = params[("free", off)]
        k = min(off, 2)
        x = np.concatenate([core, qs[:k]])
        st = oh.Standardizer(mu=mu, sd=sd)
        want = oh.predict_clipped(w, st.apply(x[None, :]))[0]
        assert sc.a_hat(core, qs, off) == want
    # survival product
    s3 = sc.a_hat(core, qs, 1) * sc.a_hat(core, qs, 2) * sc.a_hat(core, qs, 3)
    assert sc.survival(core, qs, 3) == s3
    # availability: offset 2 needs both q_sigs
    with pytest.raises(ValueError):
        sc.a_hat(core, [0.3], 2)
    with pytest.raises(ValueError):
        oh.HeadScorer(npz, "noise")


def _run_freeze(root: Path, overwrite: bool) -> subprocess.CompletedProcess:
    """stage_c_freeze with the test's sizing parameters in a FRESH interpreter: the
    contract the tool has in use, where the freeze is a process of its own reading a
    summary another process wrote (main() runs --stage-c-freeze that way; nothing else
    calls stage_c_freeze in-process). Dated 2026-10-14 (call PC-5 of the public-cut
    decision batch): until then the recompute ran inside this pytest process, and under
    numpy 2.4.6 the full suite's process state moved `delta_noise` by 2.5e-15 against the
    subprocess's value, so the binding gate refused, while the same test passed alone and
    the full run under 2.3.5 passed (docs/PUBLIC_CUT_PLAN.md 12.7). The state is the BLAS  # [withheld: docs/PUBLIC_CUT_PLAN.md not in this repository; see WITHHELD.md]
    thread count: a frozen instrument sets the thread variables to 2 when they are unset,
    at import during collection, after numpy's OpenBLAS loaded in the pytest process at
    the box's logical-processor count, and a child inherits 2 (docs/SHARP_EDGES.md, the
    2026-10-14 thread-count entry). The gate stays bit-exact; this test no longer asserts
    a bit-exact match ACROSS a long-lived process. Stage I and the freeze are still
    separate invocations; what that entry measured is that under numpy 2.4.6 their
    delta_noise differs between thread caps of 2 and 24 on this test's synthetic fixture
    and agrees under 2.3.5; other caps, other wheels and the real data are unmeasured
    (wording dated 2026-10-15, lane 2 of the public-cut batch, from the critic's read of
    lane 1: the count is of logical processors, and the agreement claim is as measured)."""
    tools = Path(__file__).resolve().parents[1] / "tools"
    code = ("import sys; sys.path.insert(0, %r); from pathlib import Path; "
            "import train_outcome_head as t; "
            "t.stage_c_freeze(Path(%r), overwrite=%r, n_slots=8, lambda_grid=(0.01, 1.0))"
            % (str(tools), str(root), overwrite))
    return subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)


def test_stage_c_freeze_end_to_end(synth_root, tmp_path):
    # arm-5 runs (gamma 6) join the synthetic root; then: stage-I run ->
    # freeze (binding gate + offset-5 + export + self-check) -> refusal
    # when the committed summary is tampered with; the freeze runs in a
    # fresh interpreter each time (_run_freeze)
    rng = np.random.default_rng(21)
    for stem in ("k3_verdict_arm5", "k3_verdict_s1_arm5"):
        _write_run(synth_root, stem, 20, rng, n_slots=8, gamma=6)
    out = synth_root / "oq15_stage1.json"
    res = _run_tool(synth_root, out)
    assert res.returncode == 0, res.stderr

    res = _run_freeze(synth_root, overwrite=False)
    assert res.returncode == 0, res.stderr + res.stdout
    assert "binding gate PASS" in res.stdout
    npz = synth_root / "oq15_head_weights.npz"
    assert npz.exists()
    meta = json.loads((synth_root / "oq15_head_weights.meta.json").read_text())
    assert meta["npz_sha256"] == hashlib.sha256(npz.read_bytes()).hexdigest()
    off5 = json.loads((synth_root / "oq15_offset5.json").read_text())
    assert set(off5["chosen_lambda"]) == {"free", "tel"}
    assert (synth_root / "oq15_offset5.json.state.jsonl").exists()
    for fam in ("free", "tel"):
        sc = oh.HeadScorer(npz, fam)
        assert set(sc.params) == {1, 2, 3, 4, 5}
    # binding-gate refusal on a tampered committed summary
    committed = json.loads(out.read_text())
    original = committed["delta_noise"]["delta"]
    committed["delta_noise"]["delta"] += 1e-9
    out.write_text(json.dumps(committed))
    res = _run_freeze(synth_root, overwrite=True)
    assert res.returncode != 0, res.stdout
    assert "BINDING GATE REFUSED" in res.stderr, res.stderr + res.stdout
    # a 1e-9 tamper is far beyond floating-point drift: the drift hint must NOT fire (lane 2, 2026-10-15)
    assert "far larger than the floating-point drift" in res.stderr and "BLAS thread caps" not in res.stderr, res.stderr
    # one ulp of drift is the signature of the measured thread-count and wheel effects: the drift hint fires
    committed["delta_noise"]["delta"] = float(np.nextafter(original, np.inf))
    out.write_text(json.dumps(committed))
    res = _run_freeze(synth_root, overwrite=True)
    assert res.returncode != 0 and "BINDING GATE REFUSED" in res.stderr, res.stderr + res.stdout
    assert "hint: " in res.stderr and "BLAS thread caps" in res.stderr and "numpy wheels" in res.stderr, res.stderr


def test_tool_stale_target_control(synth_root, tmp_path):
    # DI-1: the stale-target run completes, records the override, and
    # its delta_noise differs from the live run's (targets permuted)
    live_out = tmp_path / "live.json"
    stale_out = tmp_path / "stale.json"
    res1 = _run_tool(synth_root, live_out)
    assert res1.returncode == 0, res1.stderr
    res2 = subprocess.run(
        [sys.executable, str(Path(__file__).resolve().parents[1] / "tools"
                             / "train_outcome_head.py"),
         "--data-root", str(synth_root), "--out", str(stale_out),
         "--n-slots", "8", "--lambdas", "0.01,1.0",
         "--stale-target-perm-seed", "0"],
        capture_output=True, text=True)
    assert res2.returncode == 0, res2.stderr
    live = json.loads(live_out.read_text())
    stale = json.loads(stale_out.read_text())
    assert stale["sizing_overrides"]["stale_target_perm_seed"] == 0
    assert stale["delta_noise"]["delta"] != live["delta_noise"]["delta"]
    # paired trial structure is preserved under the permutation
    assert stale["n_test_positions"] == live["n_test_positions"]


def test_tool_refuses_overrides_on_registered_path(synth_root):
    # the registered-outs guard: sizing overrides may not write the
    # registered output path (fires before anything is written)
    res = subprocess.run(
        [sys.executable, str(Path(__file__).resolve().parents[1] / "tools"
                             / "train_outcome_head.py"),
         "--data-root", str(synth_root),
         "--out", str(Path("results") / "real" / "oq15_stage1.json"),
         "--n-slots", "8", "--lambdas", "0.01,1.0"],
        capture_output=True, text=True)
    assert res.returncode != 0
    assert "registered output path" in (res.stderr + res.stdout)


def test_tool_refuses_sha_mismatch(synth_root, tmp_path):
    victim = next((synth_root / "k3_verdict_arm1.jsonl.byproduct").glob("p*.npz"))
    victim.write_bytes(victim.read_bytes() + b"x")
    res = _run_tool(synth_root, tmp_path / "out.json")
    assert res.returncode != 0
    assert "sha256 mismatch" in (res.stderr + res.stdout)


# --------------------------------------------------------------------------
# positive and null controls (2026-10-16, lane C of the 2026-10-15 image audit, item S6b-C-4)
# --------------------------------------------------------------------------
# Before this block no test asserted the sign of the Stage-I criterion: a sign flip of delta() in
# tools/train_outcome_head.py passed every test above (the end-to-end test only checks that
# stage1_pass is a bool and that the branch string agrees with it). The synthetic root's TEL block
# carries the latent (the informative slot is present iff the latent is high) and NOISE is the
# F-16 shift of other blocks' slots, so on the informative root MSE(TEL) must sit below MSE(NOISE)
# and delta_noise must be positive, and delta_noise is by definition the difference of the two
# pooled test MSEs the summary also reports.
#
# The null root draws the same slot independently of the latent (informative=False). Its control
# is on magnitude, not on the interval: a null root read CI-clear in two of ten (seed, size) cells
# tried on 2026-10-16 (seeds 7 to 11 at 20 and 40 verdict prompts), so "null reads not CI-clear"
# would be a false pin. The probable cause is the percentile cluster bootstrap's undercoverage at
# four to eight test clusters (docs/audits/2026-10-15-image-audit/coverage_out.json: about 0.90
# at ten clusters); it was not measured here. The fixture's cell, seed 11 at 20 prompts, was
# picked from that grid (its ratio to the positive delta is 0.035); nine of the ten cells pass the
# one-third bar below and (8, 40) does not (0.38). The seeds are fixed and the bootstrap inside the
# tool is seeded, so the numbers are deterministic on one numpy; if a numpy upgrade moves them,
# rerun the grid with _write_run(..., informative=False), re-pick a cell and rewrite this comment.


@pytest.fixture()
def null_root(tmp_path):
    rng = np.random.default_rng(11)
    root = tmp_path / "real_null"
    root.mkdir()
    for stem in ("k3_verdict_arm1", "k3_verdict_s1_arm1"):
        _write_run(root, stem, 20, rng, n_slots=8, informative=False)
    for stem in ("k3_val_arm1", "k3_tapcal_arm1"):
        _write_run(root, stem, 6, rng, n_slots=8, informative=False)
    return root


def test_stage1_positive_control_sign_and_identity(synth_root, tmp_path):
    out = tmp_path / "pos.json"
    res = _run_tool(synth_root, out)
    assert res.returncode == 0, res.stderr
    s = json.loads(out.read_text())
    mse = s["test_mse"]
    assert mse["tel"] < mse["noise"] and mse["tel"] < mse["free"]
    d = s["delta_noise"]
    assert d["delta"] > 0.0 and d["ci95"][0] > 0.0 and s["stage1_pass"] is True
    assert "PASS" in s["branch"]
    # the criterion is the difference of the pooled test MSEs the summary reports, in this order
    assert d["delta"] == pytest.approx(mse["noise"] - mse["tel"], abs=1e-12)
    assert s["delta_free"]["delta"] == pytest.approx(mse["free"] - mse["tel"], abs=1e-12)
    for off in oh.GATE_OFFSETS:
        po = s["per_offset"][f"off{off}"]
        ph = s["per_head_test_mse"]
        assert po["noise_minus_tel"]["delta"] == pytest.approx(ph[f"noise_off{off}"] - ph[f"tel_off{off}"], abs=1e-12)


def test_stage1_null_control_is_small_against_the_positive(synth_root, null_root, tmp_path):
    r_pos = _run_tool(synth_root, tmp_path / "pos.json")
    r_null = _run_tool(null_root, tmp_path / "null.json")
    assert r_pos.returncode == 0 and r_null.returncode == 0, (r_pos.stderr, r_null.stderr)
    pos = json.loads((tmp_path / "pos.json").read_text())
    null = json.loads((tmp_path / "null.json").read_text())
    d_pos = pos["delta_noise"]["delta"]
    d_null = null["delta_noise"]["delta"]
    assert d_pos > 0.0
    assert abs(d_null) < d_pos / 3.0, (d_pos, d_null)
    # the label follows the interval in both roots (the rule, not the data)
    for s in (pos, null):
        assert s["stage1_pass"] == (s["delta_noise"]["ci95"][0] > 0.0)
