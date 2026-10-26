"""tools/run_noise_floor.py: the seed-noise floor readouts on synthetic
210-prompt fixtures (numpy only, no torch) and the PRECONDITION on the
committed summaries where they are present. No test reads a cross-seed
statistic of the committed pairs: the registered runs do that after the
freeze."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import run_noise_floor as nf  # noqa: E402

REAL = ROOT / "results" / "real"
needs_evidence = pytest.mark.skipif(
    not (REAL / "oq15c_verdict_s3_arm1.summary.json").exists(),
    reason="committed verdict summaries not present")

SMOKE_SIZES = (30, 42, 210)
SMOKE_M, SMOKE_BOOT = 6, 120


def _write_run(root: Path, stem: str, seed: int, prompts_rel: str, prompts_sha: str, emitted, blocks, drafted) -> None:
    pp = [{"prompt_idx": i, "orig_prompt_idx": i, "n_emitted": int(e), "n_blocks": int(b), "n_drafted": int(d),
           "tokens_per_call": int(e) / int(b)} for i, (e, b, d) in enumerate(zip(emitted, blocks, drafted))]
    (root / f"{stem}.summary.json").write_text(json.dumps({
        "arm": 1, "per_prompt_stats": pp, "tokens_per_call": float(sum(emitted) / sum(blocks)),
        "drafted_per_emitted": float(sum(drafted) / sum(emitted))}), encoding="utf-8")
    (root / f"{stem}.meta.json").write_text(json.dumps({"seed": seed, "arm": 1, "prompts": prompts_rel,
                                                        "prompts_sha256": prompts_sha}), encoding="utf-8")


def make_fixture(root: Path, key: str = "k3", mode: str = "noisy", seed: int = 0, shift: float = 0.1,
                 gamma: int = nf.GAMMA) -> tuple[Path, Path]:
    """Two fake vanilla summaries (with metas) for population `key` plus its
    prompt file, all under root. Modes: 'noisy' (independent seed noise),
    'identical' (seed B == seed A), 'shift' (seed B's per-prompt tokens/call
    lower than seed A's by exactly `shift`)."""
    gen = np.random.default_rng(seed)
    spec = nf.POPULATIONS[key]
    n = nf.FULL_N
    fam = np.array([nf.FAMILIES[i % 3] for i in range(n)])
    pfile = root / spec["prompts"]
    pfile.parent.mkdir(parents=True, exist_ok=True)
    pfile.write_text("".join(json.dumps({"prompt": f"p{i}", "family": fam[i], "topic": f"t{i}"}) + "\n" for i in range(n)),
                     encoding="utf-8")
    psha = hashlib.sha256(pfile.read_bytes()).hexdigest()
    blocks = gen.integers(4, 11, size=n) * 10                      # multiples of 10: a 0.1 shift stays integer
    base = 3.0 + 0.3 * gen.standard_normal(n) + np.where(fam == "story", -0.25, 0.0)
    ea = np.rint(blocks * (base + 0.2 * gen.standard_normal(n))).astype(int)
    if mode == "identical":
        eb = ea.copy()
    elif mode == "shift":
        eb = ea - np.rint(blocks * shift).astype(int)
    else:
        eb = np.rint(blocks * (base + 0.2 * gen.standard_normal(n))).astype(int)
    drafted = blocks * gamma
    _write_run(root, spec["a"][0], spec["a"][1], spec["prompts"], psha, ea, blocks, drafted)
    _write_run(root, spec["b"][0], spec["b"][1], spec["prompts"], psha, eb, blocks, drafted)
    return root, root


def _pop(tmp_path, **kw):
    data_root, prompts_root = make_fixture(tmp_path, **kw)
    return nf.load_population(kw.get("key", "k3"), data_root, prompts_root)


# ---------------------------------------------------------------------------
# pieces
# ---------------------------------------------------------------------------

def test_decomposition_identity_and_mom_definitions_on_random_data():
    gen = np.random.default_rng(3)
    ya, yb = 3 + gen.standard_normal(210), 3 + gen.standard_normal(210)
    fam = [nf.FAMILIES[i % 3] for i in range(210)]
    d = nf.decompose(ya, yb, fam)
    assert d["identity_holds"] and d["identity_rel_err"] <= 1e-12
    assert abs(sum(d["share"].values()) - 1.0) <= 1e-12
    assert d["n_prompt_runs"] == 420
    assert d["mom"]["df"] == {"seed_within_prompt": 210, "prompt_within_family": 207, "family": 2}
    ms = d["mom"]["mean_square"]
    assert ms["seed_within_prompt"] == d["ss"]["seed_within_prompt"] / 210
    assert ms["prompt_within_family"] == d["ss"]["prompt_within_family"] / 207
    assert ms["family"] == d["ss"]["family"] / 2
    comp = d["mom"]["component"]
    assert comp["prompt_within_family"] == (ms["prompt_within_family"] - ms["seed_within_prompt"]) / 2.0
    assert comp["family"] == (ms["family"] - ms["prompt_within_family"]) / 140.0
    assert (d["mom"]["share"] is None) == (not d["mom"]["all_nonnegative"])
    # ML normalisation: total variance equals the population variance of the 420 values
    assert abs(d["variance"]["total"] - np.concatenate([ya, yb]).var(ddof=0)) <= 1e-12


def test_mom_recovers_planted_components_where_ml_shares_do_not():
    gen = np.random.default_rng(11)
    n = 210
    fam = np.array([nf.FAMILIES[i % 3] for i in range(n)])
    prompt_effect = 0.30 * gen.standard_normal(n) + np.where(fam == "story", -0.4, 0.2)
    sd_seed = 0.25
    ya = 3 + prompt_effect + sd_seed * gen.standard_normal(n)
    yb = 3 + prompt_effect + sd_seed * gen.standard_normal(n)
    d = nf.decompose(ya, yb, list(fam))
    # SS_seed / 210 is the unbiased within-prompt variance; SS_seed / 420 is half of it
    assert abs(d["mom"]["component"]["seed_within_prompt"] - sd_seed ** 2) < 0.35 * sd_seed ** 2
    assert abs(d["variance"]["seed_within_prompt"] - 0.5 * sd_seed ** 2) < 0.2 * sd_seed ** 2
    assert abs(d["mom"]["component"]["prompt_within_family"] - 0.09) < 0.04
    assert d["mom"]["all_nonnegative"] and abs(sum(d["mom"]["share"].values()) - 1.0) <= 1e-12


def test_reliability_reports_per_family_and_within_family_r():
    gen = np.random.default_rng(5)
    n = 210
    fam = [nf.FAMILIES[i % 3] for i in range(n)]
    shift = np.array([{"instruct": 0.0, "story": -2.0, "summarize": 2.0}[f] for f in fam])
    ya = 3 + shift + gen.standard_normal(n)
    yb = 3 + shift + gen.standard_normal(n)
    r = nf.reliability(ya, yb, fam, draws=300, seed=0)
    assert set(r["r_per_family"]) == set(nf.FAMILIES)
    # the family shift inflates the pooled r far above the within-family r
    assert r["r"] > 0.6 and abs(r["r_within_family"]) < 0.3
    assert r["ci_half_width"] == (r["ci_upper"] - r["ci_lower"]) / 2.0
    assert r["ci_lower"] <= r["r"] <= r["ci_upper"]


def test_draw_subsets_are_sorted_deterministic_and_full_at_n_total():
    s1 = nf.draw_subsets((30, 42, 210), 7, 210, seed=1)
    s2 = nf.draw_subsets((30, 42, 210), 7, 210, seed=1)
    for n in (30, 42):
        assert s1[n].shape == (7, n) and np.array_equal(s1[n], s2[n])
        assert all(np.all(np.diff(row) > 0) for row in s1[n])          # sorted, no repeats
    assert s1[210].shape == (1, 210) and np.array_equal(s1[210][0], np.arange(210))
    s3 = nf.draw_subsets((30, 42, 210), 7, 210, seed=2)
    assert not np.array_equal(s1[30], s3[30])
    with pytest.raises(ValueError):
        nf.draw_subsets((300,), 1, 210)


def test_draw_swaps_shape_determinism_and_hex_round_trip():
    w1 = nf.draw_swaps((30, 210), 5, seed=2)
    w2 = nf.draw_swaps((30, 210), 5, seed=2)
    assert w1[30].shape == (5, 30) and w1[210].shape == (5, 210) and w1[30].dtype == bool
    assert np.array_equal(w1[30], w2[30]) and np.array_equal(w1[210], w2[210])
    assert not np.array_equal(w1[30], nf.draw_swaps((30, 210), 5, seed=3)[30])
    for mask in (w1[30][0], w1[210][3], np.zeros(30, dtype=bool), np.ones(7, dtype=bool), np.array([True] + [False] * 29)):
        assert np.array_equal(nf.hex_to_mask(nf.mask_to_hex(mask)), mask)


def test_subset_row_matches_the_e6_recipe_and_the_swap_mirrors():
    from sideband.stats import paired_ratio_delta_ci
    gen = np.random.default_rng(0)
    a = {"emitted": gen.integers(100, 300, 40).astype(float), "blocks": gen.integers(30, 90, 40).astype(float),
         "drafted": gen.integers(200, 400, 40).astype(float)}
    b = {"emitted": gen.integers(100, 300, 40).astype(float), "blocks": gen.integers(30, 90, 40).astype(float),
         "drafted": gen.integers(200, 400, 40).astype(float)}
    idx = np.arange(40)
    row = nf.subset_row(a, b, idx, n_boot=300, boot_seed=0)
    d, lo, hi = paired_ratio_delta_ci(a["emitted"], a["blocks"], b["emitted"], b["blocks"], n_boot=300, seed=0)
    assert (row["delta"], row["lo"], row["hi"]) == (d, lo, hi)
    assert row["hw"] == (hi - lo) / 2.0
    assert row["dpe_a"] == a["drafted"].sum() / a["emitted"].sum()
    none = nf.subset_row(a, b, idx, swap=np.zeros(40, dtype=bool), n_boot=300)
    assert (none["delta_sw"], none["lo_sw"], none["hi_sw"]) == (d, lo, hi) and none["n_swapped"] == 0
    full = nf.subset_row(a, b, idx, swap=np.ones(40, dtype=bool), n_boot=300)
    assert abs(full["delta_sw"] + d) <= 1e-12 and full["n_swapped"] == 40


def test_rates_for_n_counts_both_orientations_the_guard_and_the_full_set_branch():
    rows = [
        {"idx": 0, "delta": 0.07, "lo": 0.01, "hi": 0.13, "hw": 0.06, "dpe_a": 1.30, "dpe_b": 1.30},   # A wins, rule passes, guard ok
        {"idx": 1, "delta": 0.07, "lo": -0.01, "hi": 0.15, "hw": 0.08, "dpe_a": 1.30, "dpe_b": 1.30},  # point only
        {"idx": 2, "delta": -0.07, "lo": -0.13, "hi": -0.01, "hw": 0.06, "dpe_a": 1.30, "dpe_b": 1.35},  # B wins; B's guard FAILS
        {"idx": 3, "delta": 0.01, "lo": -0.05, "hi": 0.07, "hw": 0.06, "dpe_a": 1.30, "dpe_b": 1.30},
    ]
    r = nf.rates_for_n(rows, n=30, bar=0.062, epsilon=0.01)
    assert r["f_plus"]["count"] == 2 and r["f_minus"]["count"] == 1 and r["f_two"]["count"] == 3
    assert r["f_one"]["rate"] == 3 / 8 and r["f_one"]["se"] == r["f_two"]["se"] / 2
    assert r["g_plus"]["count"] == 1 and r["g_minus"]["count"] == 1 and r["g_two"]["count"] == 2
    assert r["g_plus_guard"]["count"] == 1 and r["g_minus_guard"]["count"] == 0 and r["g_two_guard"]["count"] == 1
    assert r["g_one_guard"]["rate"] == 1 / 8 and not r["guard_identity_holds"]   # non-vanilla budgets: the guard binds
    assert r["half_width"]["median"] == 0.06 and r["m"] == 4 and not r["single_draw"] and "swap" not in r
    # at the full set the primary is one draw (idx 0) while every row feeds the swap companion
    full = [dict(x, n=210, delta_sw=s, lo_sw=s - 0.02, hi_sw=s + 0.02, hw_sw=0.02, n_swapped=100)
            for x, s in zip(rows, (0.07, -0.07, 0.0, 0.01))]
    rf = nf.rates_for_n(full, n=210, full_n=210)
    assert rf["single_draw"] and rf["m"] == 1 and rf["single"]["delta"] == 0.07
    assert rf["swap"]["m"] == 4 and rf["swap"]["f_two"]["count"] == 2 and rf["swap"]["f_one"]["rate"] == 0.25
    assert rf["swap"]["g_two"]["count"] == 2 and "g_one_guard" not in rf["swap"]


def test_f19_percentile_pools_both_orientations_and_the_swap():
    rows = [{"delta": d, "delta_sw": s} for d, s in ((0.08, 0.0), (0.02, 0.1), (-0.07, 0.0), (0.0, 0.0))]
    out = nf.f19_percentile(rows, advantage=0.0597)
    # pooled {0.08, 0.02, -0.07, 0.0, -0.08, -0.02, 0.07, 0.0}: 0.08 and 0.07 are at or above
    assert out["count"] == 2 and out["n_pooled"] == 8 and out["share_at_or_above"] == 0.25
    assert out["percentile_of_advantage"] == 0.75
    assert out["swap"]["count"] == 1 and out["swap"]["share_at_or_above"] == 0.125


# ---------------------------------------------------------------------------
# whole populations on fixtures
# ---------------------------------------------------------------------------

def test_identical_seeds_read_r_one_zero_deltas_and_floor_weak(tmp_path):
    pop = _pop(tmp_path, mode="identical")
    prec = nf.precondition(pop)
    assert prec["holds"], prec
    assert prec["n_checks"] == 19
    rows, readouts, conclusion = nf.compute_population(pop, sizes=SMOKE_SIZES, m_subsets=SMOKE_M, n_boot=SMOKE_BOOT,
                                                       reliability_draws=200)
    assert abs(readouts["reliability"]["r"] - 1.0) <= 1e-12
    assert readouts["reliability"]["ci_lower"] >= 1.0 - 1e-9 and readouts["reliability"]["ci_upper"] <= 1.0 + 1e-9
    assert readouts["decomposition"]["share"]["seed_within_prompt"] == 0.0
    assert readouts["decomposition"]["mom"]["component"]["seed_within_prompt"] == 0.0
    assert all(r["delta"] == 0.0 and r["lo"] == 0.0 and r["hi"] == 0.0 and r["delta_sw"] == 0.0 for r in rows)
    assert readouts["per_n"]["30"]["f_one"]["rate"] == 0.0 and readouts["per_n"]["30"]["g_one"]["rate"] == 0.0
    assert readouts["per_n"]["210"]["single_draw"] and readouts["per_n"]["210"]["swap"]["m"] == SMOKE_M
    assert readouts["full_set_delta"] == 0.0 and readouts["guard_identity_holds_everywhere"]
    assert conclusion["label"] == "FLOOR-WEAK" and conclusion["stage"] == "NOTE-COLLAPSES"
    assert conclusion["readings"] == {"bar": "BAR-RESOLVED@210", "rule": "RULE-TIGHT@30"}
    assert len(rows) == SMOKE_M * len(SMOKE_SIZES)
    assert all(r["prompts"] == "all" for r in rows if r["n"] == 210)


def test_exact_shift_reads_floor_material_and_a_leaking_rule(tmp_path):
    pop = _pop(tmp_path, mode="shift", shift=0.1)
    rows, readouts, conclusion = nf.compute_population(pop, sizes=SMOKE_SIZES, m_subsets=SMOKE_M, n_boot=SMOKE_BOOT,
                                                       reliability_draws=200)
    # every subset's pooled delta is exactly +0.1 (A over B), the CI excludes zero, A's guard holds
    assert all(abs(r["delta"] - 0.1) <= 1e-9 and r["lo"] > 0 for r in rows)
    p30 = readouts["per_n"]["30"]
    assert p30["f_plus"]["rate"] == 1.0 and p30["f_minus"]["rate"] == 0.0 and p30["f_one"]["rate"] == 0.5
    assert p30["g_plus"]["rate"] == 1.0 and p30["g_one"]["rate"] == 0.5 and p30["g_one_guard"]["rate"] == 0.5
    assert p30["guard_identity_holds"] and readouts["guard_identity_holds_everywhere"]
    assert readouts["f19"]["share_at_or_above"] == 0.5
    # the swap companion is centred: swapped prompts contribute -0.1, so |delta_sw| <= 0.1 with the sign of the majority
    assert all(abs(r["delta_sw"]) <= 0.1 + 1e-9 for r in rows)
    assert 0.0 <= p30["swap"]["f_one"]["rate"] <= 0.5
    assert conclusion["label"] == "FLOOR-MATERIAL" and conclusion["stage"] == "NOTE-STANDS"
    assert conclusion["readings"]["rule"] == "RULE-LEAKS@30"
    assert not conclusion["within_two_se_of_threshold"]
    assert readouts["reliability"]["r"] > 0.99


def test_replication_role_carries_no_stage(tmp_path):
    pop = _pop(tmp_path, key="oq15", mode="noisy")
    rows, readouts, conclusion = nf.compute_population(pop, sizes=SMOKE_SIZES, m_subsets=SMOKE_M, n_boot=SMOKE_BOOT,
                                                       reliability_draws=100)
    assert conclusion["role"] == "replication" and conclusion["stage"] is None
    assert conclusion["label"] in ("FLOOR-MATERIAL", "FLOOR-WEAK")
    assert 0.0 <= readouts["per_n"]["42"]["f_one"]["rate"] <= 0.5


def test_precondition_fails_on_a_mismatched_prompt_set_and_reads_void(tmp_path):
    pop = _pop(tmp_path, mode="noisy")
    pop["b"]["prompt_idx"] = pop["b"]["prompt_idx"][::-1].copy()
    prec = nf.precondition(pop)
    assert not prec["holds"] and not prec["checks"]["prompt_sets_identical"]
    rows, readouts, conclusion = nf.compute_population(pop, sizes=(30, 210), m_subsets=2, n_boot=50, reliability_draws=50)
    assert conclusion["label"] == "REPRODUCE-INVALID" and conclusion["void"] and conclusion["stage"] is None


def test_precondition_binds_families_gamma_metas_and_pooled_fields(tmp_path):
    pop = _pop(tmp_path, mode="noisy")
    assert nf.precondition(pop)["holds"]
    fam = dict(pop)
    fam["families"] = list(pop["families"])
    fam["families"][0] = "story"
    assert not nf.precondition(fam)["checks"]["family_counts"]
    gamma = dict(pop)
    gamma["a"] = dict(pop["a"], drafted=pop["a"]["drafted"] + 1.0)
    assert not nf.precondition(gamma)["checks"]["drafted_is_gamma_blocks_a"]
    seed = dict(pop)
    seed["b"] = dict(pop["b"], meta_seed=7)
    assert not nf.precondition(seed)["checks"]["meta_seed_is_registered_b"]
    psha = dict(pop)
    psha["a"] = dict(pop["a"], meta_prompts_sha256="0" * 64)
    assert not nf.precondition(psha)["checks"]["meta_prompts_sha_is_file_a"]
    pooled = dict(pop)
    pooled["b"] = dict(pop["b"], summary_tokens_per_call=pop["b"]["summary_tokens_per_call"] + 1e-9)
    assert not nf.precondition(pooled)["checks"]["pooled_tokens_per_call_bit_exact_b"]
    orig = dict(pop)
    orig["a"] = dict(pop["a"], orig_prompt_idx=pop["a"]["orig_prompt_idx"][::-1].copy())
    assert not nf.precondition(orig)["checks"]["orig_prompt_idx_is_prompt_idx_a"]


def test_conclude_flags_a_label_within_two_se_and_the_bar_readings():
    base = {"per_n": {"30": {"f_one": {"rate": 0.021, "se": 0.01}, "g_one": {"rate": 0.0}},
                      "210": {"half_width": {"median": 0.03}}},
            "decomposition": {"identity_holds": True}, "guard_identity_holds_everywhere": True}
    c = nf.conclude(base, {"holds": True}, "label")
    assert c["label"] == "FLOOR-MATERIAL" and c["within_two_se_of_threshold"] and c["stage"] == "NOTE-STANDS"
    assert any("within Monte Carlo error" in s for s in c["sentences"])
    weak = {**base, "per_n": {**base["per_n"], "30": {"f_one": {"rate": 0.005, "se": 0.002}, "g_one": {"rate": 0.02}}}}
    c2 = nf.conclude(weak, {"holds": True}, "label")
    assert c2["label"] == "FLOOR-WEAK" and c2["stage"] == "NOTE-COLLAPSES" and c2["readings"]["rule"] == "RULE-LEAKS@30"
    wide = {**base, "per_n": {**base["per_n"], "210": {"half_width": {"median": 0.07}}}}
    assert nf.conclude(wide, {"holds": True}, "label")["readings"]["bar"] == "BAR-UNRESOLVED@210"
    broken = {**base, "guard_identity_holds_everywhere": False}
    assert any("guard identity FAILED" in s for s in nf.conclude(broken, {"holds": True}, "label")["sentences"])
    void = nf.conclude(base, {"holds": False}, "label")
    assert void["label"] == "REPRODUCE-INVALID" and void["void"] and void["stage"] is None


# ---------------------------------------------------------------------------
# CLI, refusals, evidence writer, conclude-from
# ---------------------------------------------------------------------------

def _cli(*args):
    return subprocess.run([sys.executable, str(ROOT / "tools" / "run_noise_floor.py"), *args],
                          capture_output=True, text=True, cwd=ROOT)


def test_cli_run_writes_lf_and_conclude_from_reproduces_then_refuses_tampering(tmp_path):
    data_root, prompts_root = make_fixture(tmp_path, mode="noisy", seed=5)
    out = tmp_path / "nf_smoke.json"
    state = Path(str(out) + ".state.jsonl")
    roots = ("--data-root", str(data_root), "--prompts-root", str(prompts_root))
    res = _cli("--population", "k3", *roots, "--sizes", "30,42,210", "--m-subsets", str(SMOKE_M),
               "--n-boot", str(SMOKE_BOOT), "--out", str(out))
    assert res.returncode == 0, res.stderr
    assert b"\r\n" not in out.read_bytes() and b"\r\n" not in state.read_bytes()
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["provenance"]["smoke"] is True and payload["n_state_rows"] == SMOKE_M * 3
    assert payload["provenance"]["constants"]["sizes"] == [30, 42, 210]
    assert payload["provenance"]["instrument_sha256"] == hashlib.sha256((ROOT / "tools" / "run_noise_floor.py").read_bytes()).hexdigest()
    assert payload["provenance"]["blas_threads_env"]["OMP_NUM_THREADS"] is not None
    assert payload["provenance"]["state_sha256"] == hashlib.sha256(state.read_bytes()).hexdigest()
    header = json.loads(state.read_text(encoding="utf-8").splitlines()[0])
    assert header["header"] and header["n_rows"] == payload["n_state_rows"] and header["population"] == "k3"
    assert header["constants"] == payload["provenance"]["constants"]
    res2 = _cli("--conclude-from", str(out), *roots)
    assert res2.returncode == 0, res2.stderr
    assert "reproduces the payload exactly" in res2.stdout
    # (1) a tampered stored readout: the recompute refuses
    bad = json.loads(out.read_text(encoding="utf-8"))
    bad["readouts"]["per_n"]["30"]["f_one"]["rate"] += 1e-6
    out.write_text(json.dumps(bad, indent=1) + "\n", encoding="utf-8")
    res3 = _cli("--conclude-from", str(out), *roots)
    assert res3.returncode != 0 and "differs from the payload" in (res3.stderr + res3.stdout)
    out.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")
    # (2) a tampered state file: its sha no longer matches the provenance (bytes in, bytes out: a
    # text-mode write would turn the LF file into CRLF on Windows and change the sha by itself)
    raw = state.read_bytes()
    state.write_bytes(raw.replace(b'"idx": 1,', b'"idx": 1 ,', 1))
    res4 = _cli("--conclude-from", str(out), *roots)
    assert res4.returncode != 0 and "state file's sha differs" in (res4.stderr + res4.stdout)
    state.write_bytes(raw)
    assert _cli("--conclude-from", str(out), *roots).returncode == 0
    # (3) a summary on disk that is not the one the state file read
    spath = data_root / f"{nf.POPULATIONS['k3']['b'][0]}.summary.json"
    sraw = spath.read_bytes()
    s = json.loads(sraw.decode("utf-8"))
    s["per_prompt_stats"][0]["n_emitted"] += 1
    spath.write_text(json.dumps(s), encoding="utf-8")
    res5 = _cli("--conclude-from", str(out), *roots)
    assert res5.returncode != 0 and "summary.json on disk is not the one the state file read" in (res5.stderr + res5.stdout)
    spath.write_bytes(sraw)
    assert _cli("--conclude-from", str(out), *roots).returncode == 0
    # (4) a meta file on disk that is not the one the state file read (the binding the header carries)
    mpath = data_root / f"{nf.POPULATIONS['k3']['a'][0]}.meta.json"
    mraw = mpath.read_bytes()
    m = json.loads(mraw.decode("utf-8"))
    m["note"] = "touched"
    mpath.write_text(json.dumps(m), encoding="utf-8")
    res6 = _cli("--conclude-from", str(out), *roots)
    assert res6.returncode != 0 and "meta.json on disk is not the one the state file read" in (res6.stderr + res6.stdout)
    mpath.write_bytes(mraw)
    assert _cli("--conclude-from", str(out), *roots).returncode == 0


def test_conclude_from_refuses_a_smoke_or_unregistered_constants_under_results(tmp_path, monkeypatch):
    data_root, prompts_root = make_fixture(tmp_path, mode="noisy", seed=6)
    out = tmp_path / "nf_smoke2.json"
    res = _cli("--population", "k3", "--data-root", str(data_root), "--prompts-root", str(prompts_root),
               "--sizes", "30,210", "--m-subsets", "3", "--n-boot", "60", "--out", str(out))
    assert res.returncode == 0, res.stderr
    monkeypatch.setattr(nf, "_under_results", lambda p: True)
    with pytest.raises(SystemExit, match="smoke payload under results"):
        nf.conclude_from(out, data_root, prompts_root)
    payload = json.loads(out.read_text(encoding="utf-8"))
    payload["provenance"]["smoke"] = False
    out.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="unregistered constants under results"):
        nf.conclude_from(out, data_root, prompts_root)


def test_conclude_from_refuses_a_changed_instrument(tmp_path, monkeypatch):
    data_root, prompts_root = make_fixture(tmp_path, mode="noisy", seed=7)
    out = tmp_path / "nf_smoke3.json"
    res = _cli("--population", "k3", "--data-root", str(data_root), "--prompts-root", str(prompts_root),
               "--sizes", "30,210", "--m-subsets", "2", "--n-boot", "60", "--out", str(out))
    assert res.returncode == 0, res.stderr
    real_sha = nf._sha
    monkeypatch.setattr(nf, "_sha", lambda p: "0" * 64 if Path(p).name == "run_noise_floor.py" else real_sha(p))
    with pytest.raises(SystemExit, match="instrument's bytes differ"):
        nf.conclude_from(out, data_root, prompts_root)


def test_run_refuses_a_smoke_and_a_dirty_tree_under_results(tmp_path, monkeypatch):
    data_root, prompts_root = make_fixture(tmp_path, mode="noisy")
    smoke_out = ROOT / "results" / "smoke" / "noise_floor_refused.json"
    ns = lambda **kw: type("A", (), kw)()  # noqa: E731
    with pytest.raises(SystemExit, match="smoke"):
        nf.run(ns(out=str(smoke_out), sizes="30,210", m_subsets=None, n_boot=None, population="k3",
                  data_root=str(data_root), prompts_root=str(prompts_root)))
    monkeypatch.setattr(nf, "_git", lambda: ("deadbeef", " M docs/BLUEPRINT.md"))
    with pytest.raises(SystemExit, match="not clean"):
        nf.run(ns(out=str(smoke_out), sizes=None, m_subsets=None, n_boot=None, population="k3",
                  data_root=str(data_root), prompts_root=str(prompts_root)))
    assert not smoke_out.exists()


def test_instrument_imports_no_torch_and_nothing_under_tools():
    src = (ROOT / "tools" / "run_noise_floor.py").read_text(encoding="utf-8")
    assert not re.search(r"^\s*(?:from|import)\s+torch\b", src, flags=re.M)
    for dep in re.findall(r"^\s*(?:from|import)\s+(\w+)", src, flags=re.M):
        assert not (ROOT / "tools" / f"{dep}.py").exists(), f"imports tools/{dep}.py: the frozen closure would grow"


def test_registered_constants_are_the_block_s():
    c = nf.registered_constants()
    assert c["sizes"] == [30, 42, 84, 126, 210] and c["m_subsets"] == 1000 and c["n_boot"] == 2000 and c["boot_seed"] == 0
    assert c["bar"] == 0.062 and c["epsilon"] == 0.01 and c["gamma"] == 4 and c["kill"] == 0.02 and c["rule_report"] == 0.01
    assert (c["reliability_seed"], c["subset_seed"], c["swap_seed"]) == (0, 1, 2) and c["reliability_draws"] == 2000
    assert c["label_n"] == 30 and c["full_n"] == 210 and c["family_count"] == 70
    assert nf.F19_VAL_ADVANTAGE == 3.191969887076537 - 3.1322448979591835
    assert round(nf.F19_VAL_ADVANTAGE, 6) == 0.059725


@needs_evidence
def test_precondition_holds_on_the_committed_summaries():
    """The loader and the PRECONDITION on the real pairs; no cross-seed
    statistic is computed here (the registered runs do that after the freeze)."""
    for key in ("k3", "oq15"):
        pop = nf.load_population(key)
        prec = nf.precondition(pop)
        assert prec["holds"], (key, prec)
        assert prec["n_checks"] == 19 and prec["n_prompts"] == 210
        assert prec["family_counts"] == {"instruct": 70, "story": 70, "summarize": 70}
