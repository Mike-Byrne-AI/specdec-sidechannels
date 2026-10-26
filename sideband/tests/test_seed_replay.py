"""tools/run_seed_replay.py: the OQ-20 seed-replay readouts on synthetic
210-prompt fixtures (numpy only, no torch: four runs per population, the
policy and bound files, a fake committed noise_floor payload bound to the
vanilla runs), the refusals, the conclude-from round trip, and — where the
committed evidence is present — the identity checks that the tool's leg
equals tools/e6_gate.pair on F-19's and F-21's gate legs and reproduces the
numbers FINDINGS.md prints. No test reads a seed-6 statistic of real runs:
the registered runs do that after the freeze.

Amended 2026-10-10 at the landing (docs/BLUEPRINT.md, the OQ-20 block's
DATED AMENDMENT): three assertions written for the pre-run tree (no
registered payload under results/, the seed-6 runs missing) failed by
construction once the committed evidence existed; each now branches on the
evidence's presence. No readout, label or instrument moves; the file's sha
is re-pinned there."""

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
import run_seed_replay as sr  # noqa: E402

REAL = ROOT / "results" / "real"
needs_evidence = pytest.mark.skipif(
    not (REAL / "k3_verdict_s1_arm4.summary.json").exists(), reason="committed verdict summaries not present")
LAUNCH = "0123456789abcdef0123456789abcdef01234567"
SMOKE_BOOT, SMOKE_DRAWS = 120, 60
CONFIG = {"target": "t", "draft": "d", "target_load": "nf4", "load_4bit": True, "gamma_base": 4, "gamma_base_effective": 4,
          "gamma_max": 6, "max_new": 256, "temperature": 1.0, "chat_template_used": True, "no_chat_template": False,
          "no_instruments": False, "instruments": True, "select_split": "none", "n_prompts": None,
          "templated_prompt0_ids_sha256": "ids", "date_string_pinned": "2026-01-01", "rng_scheme": "spawn",
          "torch_version": "2.6", "transformers_version": "4.57", "numpy_version": "2.3", "gpu": "g", "resume": False}


def _sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _write_run(root: Path, stem: str, meta: dict, emitted, blocks, drafted) -> None:
    pp = [{"prompt_idx": i, "orig_prompt_idx": i, "n_emitted": int(e), "n_blocks": int(b), "n_drafted": int(d),
           "tokens_per_call": int(e) / int(b)} for i, (e, b, d) in enumerate(zip(emitted, blocks, drafted))]
    (root / f"{stem}.summary.json").write_text(json.dumps({
        "arm": meta["arm"], "per_prompt_stats": pp, "tokens_per_call": float(sum(emitted) / sum(blocks)),
        "drafted_per_emitted": float(sum(drafted) / sum(emitted)), "n_prompts_completed": len(pp)}), encoding="utf-8")
    (root / f"{stem}.meta.json").write_text(json.dumps(meta), encoding="utf-8")


def make_fixture(root: Path, key: str = "k3", mode: str = "replay", seed: int = 0, committed_r: float = 0.42,
                 launch: str = LAUNCH) -> Path:
    """Four fake runs for population `key` under root (the verdict pair at the
    verdict seed, the new pair at seed 6, the other committed vanilla seed),
    the prompt file, the policy and bound files, and a fake committed
    noise_floor payload whose provenance names the two vanilla runs by sha.
    Modes: 'replay' (the new pair's rows equal the verdict pair's: a zero
    cross-seed difference), 'noisy' (fresh seed noise), 'shift' (the new tel
    arm's emitted count lowered so the leg moves far)."""
    gen = np.random.default_rng(seed)
    spec = sr.POPULATIONS[key]
    n = sr.FULL_N
    fam = [sr.FAMILIES[i % 3] for i in range(n)]
    pfile = root / spec["prompts"]
    pfile.parent.mkdir(parents=True, exist_ok=True)
    pfile.write_text("".join(json.dumps({"prompt": f"p{i}", "family": fam[i]}) + "\n" for i in range(n)), encoding="utf-8")
    psha = _sha_bytes(pfile.read_bytes())
    shas = {}
    for name, fn in spec["policy_files"].items():
        (root / fn).write_bytes(f"{key}-{name}".encode())
        shas[name] = _sha_bytes((root / fn).read_bytes())
    for fn in spec["bound_files"]:
        (root / fn).write_bytes(f"{key}-{fn}".encode())
    blocks = gen.integers(40, 100, size=n)
    base = 3.0 + 0.3 * gen.standard_normal(n)

    def emitted(effect: float, noise: float = 0.2):
        return np.rint(blocks * (base + effect + noise * gen.standard_normal(n))).astype(int)

    e_vv, e_vt, e_vf = emitted(0.0), emitted(0.01), emitted(0.005)   # the verdict triple: null-sized legs
    e_other = emitted(0.0)                                           # the other committed vanilla seed
    if mode == "replay":
        e_nv, e_nt, e_nf = e_vv.copy(), e_vt.copy(), e_vf.copy()
    elif mode == "shift":
        e_nv, e_nt, e_nf = emitted(0.0), emitted(-0.25), emitted(0.005)
    else:
        e_nv, e_nt, e_nf = emitted(0.0), emitted(0.01), emitted(0.005)
    drafted_v = blocks * sr.GAMMA
    drafted_t = blocks * sr.GAMMA - gen.integers(0, 3, size=n)   # the tel arm stops now and then
    drafted_f = blocks * sr.GAMMA - gen.integers(0, 2, size=n)   # so does the free arm
    if mode == "freeid":                                         # the free arm never fires: identical to vanilla at both seeds
        e_vf, e_nf, drafted_f = e_vv.copy(), e_nv.copy(), drafted_v
    tel_keys = {"thresholds_sha256": shas["thresholds"], "probe_weights_sha256": shas.get("probe_weights"),
                "probe_weights_meta_sha256": "pwm", "head_weights_sha256": shas.get("head_weights"),
                "probe_arm": "c" if key == "k3" else None, "head_family": "tel" if key == "oq15" else None}
    free_keys = {"thresholds_sha256": shas["free_thresholds"], "probe_weights_sha256": shas.get("probe_weights"),
                 "probe_weights_meta_sha256": "pwm", "head_weights_sha256": shas.get("head_weights"),
                 "probe_arm": "a" if key == "k3" else None, "head_family": "free" if key == "oq15" else None}
    van_keys = {"thresholds_sha256": None, "probe_weights_sha256": shas.get("probe_weights"), "probe_weights_meta_sha256": "pwm",
                "head_weights_sha256": None, "probe_arm": None, "head_family": None}

    def meta(arm, kind, s, git, extra):
        return {**CONFIG, "arm": arm, "arm_kind": kind, "seed": s, "git_commit": git, "prompts": spec["prompts"],
                "prompts_sha256": psha, **extra}

    other_seed = [s for s in spec["vanilla_seeds"] if s != spec["verdict_seed"]][0]
    vs = spec["verdict_seed"]
    _write_run(root, spec["verdict"]["vanilla"], meta(1, "fixed", vs, "old-dirty", van_keys), e_vv, blocks, drafted_v)
    _write_run(root, spec["verdict"]["tel"], meta(spec["tel_arm"], "tel", vs, "old-dirty", tel_keys), e_vt, blocks, drafted_t)
    _write_run(root, spec["verdict"]["free"], meta(spec["free_arm"], "free", vs, "old-dirty", free_keys), e_vf, blocks, drafted_f)
    _write_run(root, spec["vanilla_seeds"][other_seed], meta(1, "fixed", other_seed, "older-dirty", van_keys), e_other, blocks, drafted_v)
    _write_run(root, spec["new"]["vanilla"], meta(1, "fixed", sr.NEW_SEED, launch, van_keys), e_nv, blocks, drafted_v)
    _write_run(root, spec["new"]["tel"], meta(spec["tel_arm"], "tel", sr.NEW_SEED, launch, tel_keys), e_nt, blocks, drafted_t)
    _write_run(root, spec["new"]["free"], meta(spec["free_arm"], "free", sr.NEW_SEED, launch, free_keys), e_nf, blocks, drafted_f)
    summaries = {stem: {"path": f"results/real/{stem}.summary.json", "sha256": _sha_bytes((root / f"{stem}.summary.json").read_bytes()),
                        "meta_sha256": _sha_bytes((root / f"{stem}.meta.json").read_bytes())}
                 for stem in spec["vanilla_seeds"].values()}
    (root / f"{spec['noise_floor']}.json").write_text(json.dumps({
        "population": key, "readouts": {"reliability": {"r": committed_r, "ci_lower": committed_r - 0.1,
                                                        "ci_upper": committed_r + 0.1}},
        "provenance": {"summaries": summaries, "prompts": {"path": spec["prompts"], "sha256": psha}}}), encoding="utf-8")
    return root


def _args(root: Path, key: str, out: Path, launch: str | None = LAUNCH, smoke: bool = True) -> argparse.Namespace:
    return argparse.Namespace(population=key, out=str(out), launch_commit=launch, data_root=str(root),
                              prompts_root=str(root), n_boot=str(SMOKE_BOOT) if smoke else None,
                              draws=str(SMOKE_DRAWS) if smoke else None)


def test_replay_mode_reads_a_zero_difference_and_round_trips(tmp_path):
    root = make_fixture(tmp_path, "k3", "replay")
    out = tmp_path / "seed_replay_k3.json"
    ro = sr.run(_args(root, "k3", out))
    assert ro["R2"]["label"] == "MUTUAL-COVERAGE" and ro["R2"]["reading"] == "REPRODUCES"
    assert ro["R2"]["difference"] == 0.0 and ro["R2"]["ci_lower"] == 0.0 and ro["R2"]["ci_upper"] == 0.0
    assert ro["R1"]["delta"] == ro["R2"]["delta_verdict"] == ro["R2"]["verdict_leg"]["delta"]
    assert ro["R3"]["label"] == "BAR-NOT-CLEARED"
    assert ro["R1"]["guard_label"] == ("GUARD-HELD" if ro["R1"]["guard_holds"] else "GUARD-BREACHED")
    assert ro["R1"]["resumed"] == {"vanilla": False, "tel": False}
    # the free legs replay too: R5 equals the verdict free leg, R6 reads a zero difference, R8 likewise
    assert ro["R6"]["label"] == "MUTUAL-COVERAGE" and ro["R6"]["reading"] == "REPRODUCES" and ro["R6"]["difference"] == 0.0
    assert ro["R5"]["delta"] == ro["R6"]["delta_verdict"] and ro["R5"]["free_arm"] == 3
    assert ro["R5"]["guard_label"] == ("GUARD-FREE-HELD" if ro["R5"]["guard_holds"] else "GUARD-FREE-BREACHED")
    assert ro["R7"]["label"] == "BAR-NOT-CLEARED-FREE"
    assert ro["R8"]["label"] == "MUTUAL-COVERAGE" and ro["R8"]["difference"] == 0.0 and ro["R8"]["new_leg"]["delta"] == ro["R8"]["delta_verdict"]
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["smoke"] is True and payload["labels"]["R2"] == "MUTUAL-COVERAGE" and payload["labels"]["R6"] == "MUTUAL-COVERAGE"
    assert payload["n_state_rows"] == 8 and (tmp_path / "seed_replay_k3.json.state.jsonl").exists()
    assert set(payload["provenance"]["bound_files"]) == {"buckets_k16.json", "glue_k16.json"}
    # the committed vanilla seed 1 IS the new vanilla in replay mode: r = 1 exactly on that pair
    assert ro["R4"]["pairs"]["1_6"]["reliability"]["r"] == pytest.approx(1.0)
    assert ro["R4"]["pairs"]["1_6"]["cross_seed_null_delta"]["delta"] == 0.0
    back = sr.conclude_from(out, root, root)
    assert back["labels"] == payload["labels"]


def test_shift_mode_moves_the_delta(tmp_path):
    root = make_fixture(tmp_path, "oq15", "shift")
    ro = sr.run(_args(root, "oq15", tmp_path / "seed_replay_oq15.json"))
    assert ro["R2"]["label"] == "DELTA-MOVES" and ro["R2"]["reading"] == "MOVED-BEYOND-JOINT-CI"
    assert not ro["R2"]["new_delta_inside_verdict_ci"] and not ro["R2"]["difference_ci_contains_zero"]
    assert ro["R1"]["delta"] < ro["R2"]["delta_verdict"] - 0.1
    assert ro["R1"]["tel_arm"] == 7 and ro["R2"]["verdict_seed"] == 3
    # the tel arm moved, the free arm did not: the free leg (tel - free) moves too, free - vanilla does not
    assert ro["R6"]["label"] == "DELTA-MOVES" and ro["R5"]["free_arm"] == 6 and ro["R6"]["verdict_seed"] == 3
    assert ro["R8"]["label"] == "MUTUAL-COVERAGE" and ro["R8"]["free_arm"] == 6


def test_r8_reads_near_identical_arms_when_the_free_arm_never_fires_and_carries_no_bar_or_guard(tmp_path):
    root = make_fixture(tmp_path, "k3", "freeid")
    ro = sr.run(_args(root, "k3", tmp_path / "seed_replay_k3.json"))
    assert ro["R8"]["label"] == "NEAR-IDENTICAL-ARMS" and ro["R8"]["reading"] is None
    assert ro["R8"]["n_differing_prompts"] == {"verdict": 0, "new": 0} and ro["R8"]["either_ci_zero_width"] is True
    assert ro["R8"]["difference"] == 0.0 and ro["R8"]["min_differing_prompts"] == sr.R8_MIN_DIFFERING
    for legk in ("new_leg", "verdict_leg"):
        assert not {"ci_lower_positive", "point_at_bar", "budget_guard_margin", "guard_holds", "leg_holds"} & set(ro["R8"][legk])
        assert {"delta", "ci_lower", "ci_upper"} <= set(ro["R8"][legk])
    payload = json.loads((tmp_path / "seed_replay_k3.json").read_text(encoding="utf-8"))
    assert payload["labels"]["R8"] == "NEAR-IDENTICAL-ARMS" and payload["provenance"]["constants"]["r8_min_differing"] == 10
    assert payload["provenance"]["constants"]["new_seeds"] == {"k3": 6, "oq15": 6}
    # with the arms differing on most prompts (the other fixtures) R8 carries a label and a reading
    root2 = make_fixture(tmp_path / "b", "k3", "noisy")
    ro2 = sr.run(_args(root2, "k3", tmp_path / "b" / "seed_replay_k3.json"))
    assert ro2["R8"]["label"] in ("MUTUAL-COVERAGE", "DELTA-MOVES") and ro2["R8"]["reading"] in sr.R2_READING.values()
    assert min(ro2["R8"]["n_differing_prompts"].values()) >= sr.R8_MIN_DIFFERING


def test_r2_reading_table_and_stage_words():
    assert sr.R2_READING[(True, True)] == "REPRODUCES"
    assert sr.R2_READING[(True, False)] == "PROMPT-STABLE-SHIFT"
    assert sr.R2_READING[(False, True)] == "WITHIN-CROSS-SEED-NOISE"
    assert sr.R2_READING[(False, False)] == "MOVED-BEYOND-JOINT-CI"
    assert sr.stage_word("MUTUAL-COVERAGE", "MUTUAL-COVERAGE") == "SPREAD-COVERED"
    assert sr.stage_word("MUTUAL-COVERAGE", "DELTA-MOVES") == "SPREAD-SPLIT"
    assert sr.stage_word("DELTA-MOVES", "DELTA-MOVES") == "SPREAD-MOVES"
    assert sr.stage_word("DELTA-MOVES", "MUTUAL-COVERAGE", "FREE-") == "FREE-SPREAD-SPLIT"
    assert len(sr.REPLAY_SPECS) == 6 and {s[0] for s in sr.REPLAY_SPECS} >= {"oq20_replay_k3_s1_arm3", "oq20_replay_oq15c_s3_arm6"}


def test_r4_rule_follows_the_committed_r(tmp_path):
    root = make_fixture(tmp_path, "k3", "noisy")
    pop = sr.load_pop("k3", root, root)
    assert sr.precondition(pop, LAUNCH)["holds"]
    ro = sr.readouts(pop, n_boot=SMOKE_BOOT, draws=SMOKE_DRAWS)
    pairs = ro["R4"]["pairs"]
    inside = max(p["reliability"]["ci_lower"] for p in pairs.values()) + 1e-9
    assert inside <= min(p["reliability"]["ci_upper"] for p in pairs.values())
    pop["noise_floor"]["readouts"]["reliability"]["r"] = float(inside)
    assert sr.readouts(pop, n_boot=SMOKE_BOOT, draws=SMOKE_DRAWS)["R4"]["label"] == "R-CONSISTENT"
    pop["noise_floor"]["readouts"]["reliability"]["r"] = 0.999
    assert sr.readouts(pop, n_boot=SMOKE_BOOT, draws=SMOKE_DRAWS)["R4"]["label"] == "R-SHIFTS"


def test_precondition_refusals(tmp_path):
    root = make_fixture(tmp_path, "k3", "noisy")
    pop = sr.load_pop("k3", root, root)
    assert not sr.precondition(pop, LAUNCH + "-dirty")["holds"]
    assert not sr.precondition(pop, None)["checks"]["meta_launch_commit_clean_new_tel"]
    stem = sr.POPULATIONS["k3"]["new"]["tel"]
    mpath = root / f"{stem}.meta.json"
    m = json.loads(mpath.read_text(encoding="utf-8"))
    m["max_new"] = 128                                             # a configuration key differing from the verdict meta
    mpath.write_text(json.dumps(m), encoding="utf-8")
    prec = sr.precondition(sr.load_pop("k3", root, root), LAUNCH)
    assert prec["checks"]["same_configuration_as_verdict_new_tel"] is False
    assert prec["checks"]["same_configuration_detail_new_tel"] == ["max_new"] and not prec["holds"]
    m["max_new"], m["seed"] = 256, 1
    mpath.write_text(json.dumps(m), encoding="utf-8")
    prec = sr.precondition(sr.load_pop("k3", root, root), LAUNCH)
    assert prec["checks"]["meta_seed_is_new_new_tel"] is False and not prec["holds"]
    (root / "k3_thresholds_arm4_v2.json").write_bytes(b"tampered")
    prec = sr.precondition(sr.load_pop("k3", root, root), LAUNCH)
    assert prec["checks"]["thresholds_file_is_verdict_tel_meta_sha"] is False
    nfp = root / "noise_floor_k3.json"
    d = json.loads(nfp.read_text(encoding="utf-8"))
    d["provenance"]["summaries"]["k3_verdict_arm1"]["sha256"] = "0" * 64
    nfp.write_text(json.dumps(d), encoding="utf-8")
    prec = sr.precondition(sr.load_pop("k3", root, root), LAUNCH)
    assert prec["checks"]["noise_floor_inputs_are_the_loaded_vanilla_runs"] is False
    (root / f"{stem}.summary.json").unlink()
    prec = sr.precondition(sr.load_pop("k3", root, root), LAUNCH)
    assert prec["holds"] is False and prec["missing"] == [stem]
    with pytest.raises(SystemExit, match="precondition"):
        sr.run(_args(root, "k3", tmp_path / "x.json"))


def test_registered_run_refusals_under_results(tmp_path, monkeypatch):
    root = make_fixture(tmp_path, "k3", "replay")
    out = REAL / "seed_replay_k3_TEST_NEVER_WRITTEN.json"
    with pytest.raises(SystemExit, match="smoke"):
        sr.run(_args(root, "k3", out))
    with pytest.raises(SystemExit, match="launch-commit"):
        sr.run(_args(REAL, "k3", out, launch=None, smoke=False))
    registered_out = REAL / "seed_replay_k3.json"                     # the registered name: the out-name check passes, git decides
    # amended 2026-10-10 at the landing (the block's DATED AMENDMENT): the registered payload exists once the readouts land,
    # so the refusal must leave it and its state file byte-identical; before the landing this asserted it did not exist
    kept = [registered_out, Path(str(registered_out) + ".state.jsonl")]
    before = [p.read_bytes() if p.exists() else None for p in kept]
    monkeypatch.setattr(sr, "_git", lambda: ("abc", [" M tools/x.py"]))
    with pytest.raises(SystemExit, match="not clean"):
        sr.run(_args(REAL, "k3", registered_out, launch="abc", smoke=False))
    assert not out.exists() and not Path(str(out) + ".state.jsonl").exists()
    assert [p.read_bytes() if p.exists() else None for p in kept] == before


def test_conclude_from_refuses_a_tampered_summary(tmp_path):
    root = make_fixture(tmp_path, "k3", "noisy")
    out = tmp_path / "seed_replay_k3.json"
    sr.run(_args(root, "k3", out))
    stem = sr.POPULATIONS["k3"]["new"]["tel"]
    p = root / f"{stem}.summary.json"
    s = json.loads(p.read_text(encoding="utf-8"))
    s["per_prompt_stats"][3]["n_emitted"] += 1
    p.write_text(json.dumps(s), encoding="utf-8")
    with pytest.raises(SystemExit, match="not the one the state file read"):
        sr.conclude_from(out, root, root)


def test_stage_word_from_two_payloads(tmp_path):
    ra, rb = make_fixture(tmp_path / "a", "k3", "replay"), make_fixture(tmp_path / "b", "oq15", "shift")
    oa, ob = tmp_path / "a" / "k3.json", tmp_path / "b" / "oq15.json"
    sr.run(_args(ra, "k3", oa))
    sr.run(_args(rb, "oq15", ob))
    assert sr.stage_word_from(oa, ob) == "SPREAD-SPLIT"
    with pytest.raises(SystemExit, match="label payload then the replication"):
        sr.stage_word_from(ob, oa)


def test_resumed_is_read_from_the_resumed_flag_and_run_ids(tmp_path):
    root = make_fixture(tmp_path, "k3", "replay")
    stem = sr.POPULATIONS["k3"]["new"]["vanilla"]
    mpath = root / f"{stem}.meta.json"
    m = json.loads(mpath.read_text(encoding="utf-8"))
    assert sr.resumed(m) is False
    m["resume"] = True                                             # the ARGUMENT alone marks nothing (the instrument keeps it False)
    assert sr.resumed(m) is False
    assert sr.resumed({"run_ids": ["a", "b"]}) is True
    m["resume"], m["resumed"], m["run_ids"] = False, True, ["a", "b"]
    mpath.write_text(json.dumps(m), encoding="utf-8")
    ro = sr.run(_args(root, "k3", tmp_path / "seed_replay_k3.json"))
    assert ro["R1"]["resumed"] == {"vanilla": True, "tel": False}
    payload = json.loads((tmp_path / "seed_replay_k3.json").read_text(encoding="utf-8"))
    assert payload["precondition"]["checks"]["resumed_new_vanilla"] is True and payload["precondition"]["holds"] is True


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


def make_replay_fixture(root: Path, k: int = 2, n: int = 4) -> list[tuple]:
    """A committed-style verdict run (gen + stats + meta, n prompts) and a replay of its first k prompts whose
    run_id, seconds and peak_vram_gb differ but whose tokens and counters are identical."""
    gen = np.random.default_rng(3)
    vgen = [{"prompt_idx": i, "orig_prompt_idx": i, "run_id": "v", "prompt_len": 40 + i,
             "generated_ids": [int(x) for x in gen.integers(0, 1000, size=16)]} for i in range(n)]
    vstats = [{"prompt_idx": i, "orig_prompt_idx": i, "run_id": "v", "seconds": 1.0 + i, "peak_vram_gb": 7.0,
               "n_blocks": 10 + i, "n_accepted": 20 + i, "n_emitted": 30 + i, "n_drafted": 40 + i, "n_stop_blocks": i % 2,
               "n_extend_blocks": 0, "tokens_per_call": (30 + i) / (10 + i)} for i in range(n)]
    bound = {"arm": 4, "seed": 1, "prompts_sha256": "p", "thresholds_sha256": "t", "probe_weights_sha256": "w",
             "head_weights_sha256": None}
    _write_jsonl(root / "ver_a.gen.jsonl", vgen)
    _write_jsonl(root / "ver_a.stats.jsonl", vstats)
    (root / "ver_a.meta.json").write_text(json.dumps({**bound, "n_prompts": None, "git_commit": "old-dirty"}), encoding="utf-8")
    rgen = [{**r, "run_id": "r"} for r in vgen[:k]]
    rstats = [{**r, "run_id": "r", "seconds": 9.0, "peak_vram_gb": 8.0} for r in vstats[:k]]
    _write_jsonl(root / "rep_a.gen.jsonl", rgen)
    _write_jsonl(root / "rep_a.stats.jsonl", rstats)
    (root / "rep_a.meta.json").write_text(json.dumps({**bound, "n_prompts": k, "git_commit": "abc"}), encoding="utf-8")
    return [("rep_a", "ver_a", k, 1)]


def test_replay_check_passes_on_an_exact_replay_and_fails_on_any_token_or_counter(tmp_path):
    specs = make_replay_fixture(tmp_path)
    rep = sr.replay_check(tmp_path, specs, launch_commit="abc")
    assert rep["all_match"] and rep["arms"]["rep_a"]["meta"]["launch_commit_clean"]
    assert all(r["match"] for r in rep["arms"]["rep_a"]["gen_rows"]) and len(rep["arms"]["rep_a"]["gen_rows"]) == 2
    rows = [json.loads(ln) for ln in (tmp_path / "rep_a.gen.jsonl").read_text(encoding="utf-8").splitlines()]
    rows[1]["generated_ids"][3] += 1
    _write_jsonl(tmp_path / "rep_a.gen.jsonl", rows)
    rep = sr.replay_check(tmp_path, specs, launch_commit="abc")
    assert not rep["all_match"] and rep["arms"]["rep_a"]["gen_rows"][1]["differing_fields"] == ["generated_ids"]
    rows[1]["generated_ids"][3] -= 1
    _write_jsonl(tmp_path / "rep_a.gen.jsonl", rows)
    srows = [json.loads(ln) for ln in (tmp_path / "rep_a.stats.jsonl").read_text(encoding="utf-8").splitlines()]
    srows[0]["n_accepted"] += 1
    _write_jsonl(tmp_path / "rep_a.stats.jsonl", srows)
    rep = sr.replay_check(tmp_path, specs, launch_commit="abc")
    assert not rep["all_match"] and rep["arms"]["rep_a"]["stats_rows"][0]["differing_fields"] == ["n_accepted"]
    srows[0]["n_accepted"] -= 1
    _write_jsonl(tmp_path / "rep_a.stats.jsonl", srows)
    assert sr.replay_check(tmp_path, specs, launch_commit="abc")["all_match"]
    assert not sr.replay_check(tmp_path, specs, launch_commit="other")["arms"]["rep_a"]["meta"]["launch_commit_clean"]
    m = json.loads((tmp_path / "rep_a.meta.json").read_text(encoding="utf-8"))
    m["git_commit"] = "abc-dirty"
    (tmp_path / "rep_a.meta.json").write_text(json.dumps(m), encoding="utf-8")
    assert not sr.replay_check(tmp_path, specs, launch_commit="abc")["all_match"]
    (tmp_path / "rep_a.stats.jsonl").unlink()
    rep = sr.replay_check(tmp_path, specs)
    assert rep["arms"]["rep_a"]["missing"] == ["rep_a.stats.jsonl"] and not rep["all_match"]


@needs_evidence
def test_replay_check_reads_the_committed_verdict_files_against_themselves():
    specs = [(vs, vs, k, seed) for _rs, vs, k, seed in sr.REPLAY_SPECS]
    rep = sr.replay_check(REAL, specs)                                # no launch commit: the stamp is not checked
    for vs, entry in rep["arms"].items():
        assert all(r["match"] for r in entry["gen_rows"]) and all(r["match"] for r in entry["stats_rows"])
        assert len(entry["gen_rows"]) == entry["n_prompts"]
        meta = entry["meta"]
        assert meta["n_prompts_is_pinned"] is False                   # a verdict meta carries n_prompts None
        assert all(v for key, v in meta.items() if key != "n_prompts_is_pinned")


def test_conclude_from_refuses_a_tampered_state_row_label_or_launch_commit(tmp_path):
    root = make_fixture(tmp_path, "k3", "noisy")
    out = tmp_path / "seed_replay_k3.json"
    sr.run(_args(root, "k3", out))
    state = Path(str(out) + ".state.jsonl")
    lines = state.read_text(encoding="utf-8").splitlines()
    pristine_state, pristine_payload = state.read_bytes(), out.read_bytes()
    row = json.loads(lines[1])
    row["values"]["delta"] += 1e-9                                   # beyond the 1e-12 tolerance
    lines[1] = json.dumps(row, sort_keys=True)
    state.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    payload = json.loads(out.read_text(encoding="utf-8"))
    payload["provenance"]["state_sha256"] = hashlib.sha256(state.read_bytes()).hexdigest()
    out.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    with pytest.raises(SystemExit, match="differs from the state row"):
        sr.conclude_from(out, root, root)
    state.write_bytes(pristine_state)
    payload = json.loads(pristine_payload.decode("utf-8"))
    payload["labels"]["R2"] = "DELTA-MOVES" if payload["labels"]["R2"] == "MUTUAL-COVERAGE" else "MUTUAL-COVERAGE"
    out.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    with pytest.raises(SystemExit, match="readouts or labels differ"):
        sr.conclude_from(out, root, root)
    payload = json.loads(pristine_payload.decode("utf-8"))
    payload["launch_commit"] = "deadbeef"
    out.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    with pytest.raises(SystemExit, match="launch commit or inputs differ"):
        sr.conclude_from(out, root, root)
    out.write_bytes(pristine_payload)
    assert sr.conclude_from(out, root, root)["labels"] == json.loads(pristine_payload.decode("utf-8"))["labels"]


def test_replay_check_fails_on_a_short_replay_even_when_every_compared_row_matches(tmp_path):
    specs = make_replay_fixture(tmp_path, k=3)
    for ext in ("gen.jsonl", "stats.jsonl"):
        p = tmp_path / f"rep_a.{ext}"
        rows = [json.loads(ln) for ln in p.read_text(encoding="utf-8").splitlines()]
        _write_jsonl(p, rows[:-1])
    rep = sr.replay_check(tmp_path, specs, launch_commit="abc")
    entry = rep["arms"]["rep_a"]
    assert not rep["all_match"] and not entry["match"]
    assert len(entry["gen_rows"]) == 2 and all(r["match"] for r in entry["gen_rows"]) and all(r["match"] for r in entry["stats_rows"])


def test_registered_out_name_is_enforced_under_results(tmp_path, monkeypatch):
    # amended 2026-10-10 at the landing (the block's DATED AMENDMENT): the registered payload exists once the readouts
    # land, so both refusals must leave it byte-identical; before the landing this asserted it did not exist
    kept = [REAL / "seed_replay_k3.json", REAL / "seed_replay_k3.json.state.jsonl"]
    before = [p.read_bytes() if p.exists() else None for p in kept]
    monkeypatch.setattr(sr, "_git", lambda: ("abc", []))
    with pytest.raises(SystemExit, match="registered out"):
        sr.run(_args(REAL, "oq15", REAL / "seed_replay_k3.json", launch="abc", smoke=False))
    monkeypatch.setattr(sr, "_git", lambda: ("unknown", ["git unavailable"]))
    with pytest.raises(SystemExit, match="not clean"):
        sr.run(_args(REAL, "k3", REAL / "seed_replay_k3.json", launch="abc", smoke=False))
    assert [p.read_bytes() if p.exists() else None for p in kept] == before


def test_help_runs_without_torch():
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "run_seed_replay.py"), "--help"], capture_output=True, text=True)
    assert r.returncode == 0 and "SEED-REPLAY" in r.stdout


def test_imports_only_the_frozen_f27_instrument_from_tools_and_no_torch():
    tools_dir = str(ROOT / "tools")
    code = ("import sys, pathlib\n"
            f"sys.path.insert(0, {tools_dir!r})\n"
            "import run_seed_replay\n"
            f"here = pathlib.Path({tools_dir!r}).resolve()\n"
            "loaded = sorted(m for m, mod in list(sys.modules.items()) if getattr(mod, '__file__', None)\n"
            "                and pathlib.Path(mod.__file__).resolve().parent == here)\n"
            "print(loaded); print('torch' in sys.modules)\n")
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env={**dict(__import__('os').environ), "CUDA_VISIBLE_DEVICES": ""})
    assert r.returncode == 0, r.stderr
    loaded, torch_loaded = r.stdout.strip().splitlines()
    assert loaded == "['run_noise_floor', 'run_seed_replay']" and torch_loaded == "False"


@needs_evidence
def test_committed_verdict_legs_equal_e6_gate_and_findings_text():
    import e6_gate as e6
    for key, pop_key, t, c, f, want, want_free in (
            ("k3", "k3_s1", 4, 1, 3, [0.006860, -0.015024, 0.025572], [0.006974, -0.014909, 0.025690]),
            ("oq15", "oq15c_s3", 7, 1, 6, [0.002664, -0.044719, 0.046727], [-0.081846, -0.132484, -0.035567])):
        pop = sr.load_pop(key)
        got = sr.leg(pop["runs"]["verdict_tel"], pop["runs"]["verdict_vanilla"])
        ref = e6.evaluate(pop_key)["legs"][f"arm{t}_vs_arm{c}"]
        assert got == ref, (key, got, ref)
        assert [round(got[k], 6) for k in ("delta", "ci_lower", "ci_upper")] == want
        got_free = sr.leg(pop["runs"]["verdict_tel"], pop["runs"]["verdict_free"])   # F-19's arm 4 vs arm 3; F-21's arm 7 vs arm 6
        assert got_free == e6.evaluate(pop_key)["legs"][f"arm{t}_vs_arm{f}"]
        assert [round(got_free[k], 6) for k in ("delta", "ci_lower", "ci_upper")] == want_free
        assert pop["policy"]["thresholds"]["sha256"] == pop["metas"]["verdict_tel"]["thresholds_sha256"]
        assert pop["policy"]["free_thresholds"]["sha256"] == pop["metas"]["verdict_free"]["thresholds_sha256"]
        assert pop["metas"]["verdict_free"]["arm"] == f
        assert pop["noise_floor"]["readouts"]["reliability"]["r"] > 0.3
        prec = sr.precondition(pop, None)
        if pop["missing"]:       # the tree this file was frozen on: the seed-6 runs did not exist yet
            assert prec["holds"] is False and set(prec["missing"]) == set(sr.POPULATIONS[key]["new"].values())
        else:                    # amended 2026-10-10 at the landing (the block's DATED AMENDMENT): the six seed-6 runs are committed,
            assert prec["holds"] is False and "missing" not in prec              # nothing is missing, and without a launch commit the
            assert not any(v for k, v in prec["checks"].items()                  # clean-commit binding alone refuses
                           if k.startswith("meta_launch_commit_clean_"))
