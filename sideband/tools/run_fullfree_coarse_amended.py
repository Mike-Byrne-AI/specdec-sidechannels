#!/usr/bin/env python
"""OQ-18 AMENDED INSTRUMENT — the leak rider's leg 2 amended on 2026-09-07
(docs/BLUEPRINT.md, OQ-18 dated amendment; docs/OQ18_RIDER_DIAGNOSTIC.md,
Consequence under B). A NEW FILE that imports the frozen instrument
(tools/run_fullfree_coarse.py at the freeze 15c4e9c, sha 5efa7063..., asserted
at start), so the frozen file stays byte-identical on disk while frozen-
instrument runs are in flight — their payloads hash the instrument file at
write time.

WHAT CHANGES, and nothing else:
(1) the rider grid has FOUR shuffled cells per space — (a), fplus, fplus_b,
    fplus_r at off2 / linear / seed 0 — trained with the prediction dump
    (run_oq18_rider_diag.run_cell_diag: the registered rider cell plus
    train_probe full_eval=True; per-prompt prediction / shifted-label
    histograms stored in the state row);
(2) leg 2 is the AMENDED LEG: E(sh fplus_b) - E(sh fplus_r) at seed 0, where
    E = acc - sum_c q(c) p(c) is the dependence excess, FAILS if > 0.01 OR
    (CI95 lower > 0 AND >= +0.005), the CI a cluster bootstrap over the 30
    test prompts (n_boot 2000, seed 0, marginals recomputed per resample).
    The registered raw leg 2 (fplus_b - fplus <= 0.01) is REPORTED per
    harvest as registered_leg2_raw and never halts; X_raw = acc(fplus_b) -
    acc(fplus_r) is reported with its pinned sentence; leg 1 is unchanged
    and still halts. A failed amended leg HALTS THE RUN before any payload
    is written, exactly as the original did;
(3) --resume on a registered out path is licensed for the four amendment
    resumes (resumed_cells recorded nonzero); a shuffled state row WITHOUT
    histograms (a frozen-instrument row) is RE-TRAINED, never reused — the
    frozen rows stay in the state file as the record;
(4) an existing frozen-instrument payload at the registered out path is
    PRESERVED as <stem>.rider_v1.json before anything trains, never
    overwritten and never concluded (--conclude-from refuses it);
(5) the payload carries the amendment block, the diagnostic's verdict and
    the reroute disclosure, which --conclude-from prefixes to its output.
GUARDS: on a registered out path the tracked tree must be clean and this
file must be git-tracked (fails closed) — no amended cell trains before the
amendment is committed; the diagnostic payload must exist and read branch
AMENDABLE (the amendment is licensed under that branch only).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from sideband.provenance import redact_args  # noqa: E402
from sideband.recon import FREETOK_BINS  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))
from sideband.probes import HarvestData  # noqa: E402
import run_fullfree_coarse as fz  # noqa: E402  (the FROZEN instrument)
from run_fullfree_coarse import (SEEDS, ARMS, TWIN_ARM, BASE_ARM, GATE_OFFSET,  # noqa: E402
                                 GATE_CAPACITY, LEVELS, REGISTERED_OUTS, HARVESTS_OF_TAG,
                                 OUT_STEM_OF_TAG, offsets_for_space, registered_spaces,
                                 make_factories, check_grid_against_committed,
                                 relabel_committed_linear_a, reader_validity, gate_row,
                                 gate_fires, only_match, committed_moments_sha)
from run_oq18_rider_diag import (run_cell_diag, normalize_hist, excess_stats, amended_leg,  # noqa: E402
                                 BAND, MATERIAL, N_BOOT, BOOT_SEED, EXPECTED_CLUSTERS,
                                 PAIR_TWIN, BRANCH_B, DIAG_OUT)
from run_posthoc_topic import load_phase3_cells  # noqa: E402
from run_probes import (REAL, bind_spaces_to_harvest, build_spaces, cell_id,  # noqa: E402
                        feature_blocks, margins, parse_state, run_cell, state_header)
from run_fullfree import LABEL_READER_INVALID, _same_path, _sha, train_moments  # noqa: E402
from run_fullfree_twin import TWIN_SEED_BASE, CONSTRUCTION, derangement_by_prompt, twin_geometry  # noqa: E402

FROZEN_INSTRUMENT = Path(__file__).resolve().parent / "run_fullfree_coarse.py"
FROZEN_INSTRUMENT_SHA256 = "5efa7063767be062208eb3755cedf6a4e30f4c306927a1c3d2527098d69a5281"
AMENDMENT_DATE = "2026-09-07"
AMENDED_MARK = f"AMENDED {AMENDMENT_DATE}"
SHUFFLED_ARMS = ("a", "fplus", "fplus_b", "fplus_r")
RIDER_V1_SUFFIX = ".rider_v1.json"
DIAG_PAYLOAD = REAL / Path(DIAG_OUT).name
REROUTE_SENTENCE = ("a post-hoc reroute around a fired kill condition: the leg that fired was replaced "
                    "after the fire by a twin-referenced dependence-excess leg whose S1 seed-0 values at "
                    "both spaces were known from the diagnostic payload when the amendment was written; "
                    "it is a fresh test only at the other three harvests")
DOMINANCE_SENTENCE = ("the E leg sees every non-causal block the raw leg sees (the twin lacks it) and is "
                      "sharper under a drifted reader; what it drops (prediction-marginal drift and "
                      "twin-shared position information) are non-leaks")
# The ONLY tracked modification an amended run may start over or record: the S1
# primary resume APPENDS to its committed state file (BLUEPRINT dated amendment,
# RUNS). Anything else is a violation: refused at start, refused at conclude.
LICENSED_DIRTY = (" M results/real/fullfree_coarse_s1.json.state.jsonl",)


# ---------------------------------------------------------------------------
# Grid, reuse rule, rider
# ---------------------------------------------------------------------------

def build_grid_amended(spaces: tuple[str, ...] | list[str], offsets_of: dict | None = None) -> list[tuple]:
    """The frozen grid with a FOURTH shuffled cell (fplus_r) per space; the
    trained cells are identical to the frozen instrument's."""
    grid: list[tuple] = []
    for sp in spaces:
        offs = offsets_for_space(sp, offsets_of)
        grid += [(sp, GATE_OFFSET, arm, "linear", 0, True) for arm in SHUFFLED_ARMS]
        grid += [(sp, GATE_OFFSET, BASE_ARM, GATE_CAPACITY, seed, False) for seed in SEEDS]
        for off in offs:
            caps = ("linear", GATE_CAPACITY) if off == GATE_OFFSET else (GATE_CAPACITY,)
            for seed in SEEDS:
                for cap in caps:
                    for arm in ARMS:
                        grid.append((sp, off, arm, cap, seed, False))
    if len({cell_id(*c) for c in grid}) != len(grid):
        raise SystemExit("duplicate cell ids in the grid")
    return grid


def reusable(cid: str, done: dict, shuffled: bool) -> bool:
    """A state row is reused iff present and, for a shuffled cell, carrying
    the histograms (a frozen-instrument shuffled row is re-trained)."""
    return cid in done and (not shuffled or "_hist" in done[cid])


def x_raw_sentence(x_raw: float, band: float = BAND) -> str:
    return ("the registered statistic, twin-referenced, would also have passed" if x_raw <= band
            else "the registered statistic, twin-referenced, would still have fired")


def rider_check_amended(cells: list[dict], space: str, n_classes: int, band: float = BAND,
                        material: float = MATERIAL, n_boot: int = N_BOOT,
                        expected_clusters: int | None = EXPECTED_CLUSTERS) -> dict | None:
    """Leg 1 as registered (raw, halts). Leg 2 AMENDED: the twin-referenced
    dependence excess at seed 0 (halts on failure); the registered raw leg 2
    is reported and never halts. Fresh or resumed cells alike."""
    sh = [c for c in cells if c["shuffled"] and c["space"] == space and c["offset"] == GATE_OFFSET
          and c["capacity"] == "linear"]
    if not sh:
        return None
    by = {arm: next((c for c in sh if c["features"] == arm), None) for arm in SHUFFLED_ARMS}
    sa, sf, sb, sr = by["a"], by["fplus"], by["fplus_b"], by["fplus_r"]
    if sa is None:
        raise SystemExit(f"{space}: the fresh shuffled (a) reference is missing — leg 1 of the "
                         "leak rider cannot run (--only too narrow?)")
    out: dict = {"band": band, "material": material, "space": space, "amended": AMENDED_MARK,
                 "shuffled_a": sa["test_acc"], "leg1_pass": None, "leg2_pass": None, "pass": False,
                 "rule": ("leg 1: shuffled fplus <= shuffled (a) + band (raw, unchanged); leg 2 AMENDED: "
                          "E(sh fplus_b) - E(sh fplus_r) at seed 0 fails if > band OR (CI95 lower > 0 AND "
                          ">= material); the registered raw leg 2 is reported, never halts")}
    if sf is not None:
        out["shuffled_fplus"] = sf["test_acc"]
        out["leg1_pass"] = bool(sf["test_acc"] <= sa["test_acc"] + band)
        if not out["leg1_pass"]:
            raise SystemExit(f"LEAK RIDER leg 1 FAILED at {space}: shuffled fplus {sf['test_acc']:.4f} "
                             f"> shuffled (a) {sa['test_acc']:.4f} + {band} — a leak in the TOK / hz "
                             "blocks; halting")
    if sb is not None:
        if sf is None:
            raise SystemExit(f"{space}: shuffled fplus_b has no shuffled fplus partner")
        out["shuffled_fplus_b"] = sb["test_acc"]
        raw = float(sb["test_acc"] - sf["test_acc"])
        out["registered_leg2_raw"] = {"excess": raw, "pass": bool(raw <= band),
                                      "note": "REPORTED under the amendment; never halts"}
    if sr is not None:
        if sb is None:
            raise SystemExit(f"{space}: shuffled fplus_r has no shuffled fplus_b partner")
        for c in (sb, sr):
            if "_hist" not in c:
                raise SystemExit(f"{space}: shuffled {c['features']} row carries no histograms — the "
                                 "amended leg needs the prediction dump (re-train, never reuse)")
        out["shuffled_fplus_r"] = sr["test_acc"]
        arms = {"fplus_b": [sb], "fplus_r": [sr]}
        for arm, c in (("fplus", sf), ("a", sa)):
            if c is not None and "_hist" in c:
                arms[arm] = [c]
        st = excess_stats(arms, n_classes, "all", n_boot, BOOT_SEED, expected_clusters)
        pair = st["pairs"][PAIR_TWIN]
        leg = amended_leg(pair, band, material)
        out["amended_leg2"] = leg
        out["x_raw_seed0"] = float(pair["d_acc"])
        out["x_raw_ci95"] = pair.get("ci95_d_acc")
        out["x_raw_sentence"] = x_raw_sentence(out["x_raw_seed0"], band)
        out["E"] = {arm: st["arms"][arm]["E"] for arm in st["arms"]}
        out["E_ci95"] = {arm: st["arms"][arm].get("ci95_E") for arm in st["arms"]}
        out["q_majority"] = {arm: st["arms"][arm]["q_majority"] for arm in st["arms"]}
        out["n_boot"] = int(n_boot)
        out["leg2_pass"] = not leg["fails"]
        if leg["fails"]:
            raise SystemExit(f"AMENDED LEAK RIDER leg 2 FAILED at {space}: E(fplus_b) - E(fplus_r) = "
                             f"{leg['d_E']:+.4f} (CI95 {leg['ci95_d_E']}) — {leg['reason']}; halting")
    out["pass"] = bool(out["leg1_pass"] and out["leg2_pass"])
    return out


# ---------------------------------------------------------------------------
# Guards, preservation, conclusion
# ---------------------------------------------------------------------------

def assert_frozen_instrument() -> None:
    got = _sha(FROZEN_INSTRUMENT)
    if got != FROZEN_INSTRUMENT_SHA256:
        raise SystemExit(f"the frozen instrument {FROZEN_INSTRUMENT.name} on disk hashes to {got[:12]}, "
                         f"not the freeze's {FROZEN_INSTRUMENT_SHA256[:12]} — refusing")


def unlicensed_lines(porcelain: list[str]) -> list[str]:
    """Tracked-status lines beyond the licensed S1 state-file append."""
    return [ln for ln in porcelain if ln.strip() and ln.rstrip() not in LICENSED_DIRTY]


def guard_lines(porcelain: list[str], instrument_tracked: bool) -> None:
    """Pure rule behind committed_guard: the tracked tree may carry exactly
    the licensed line (the S1 primary resume's state-file append) and nothing
    else; this file must be tracked. Fails closed."""
    extra = unlicensed_lines(porcelain)
    if extra:
        raise SystemExit("tracked tree carries modifications beyond the licensed S1 state-file "
                         "append — the amendment (or the landing) must be committed before any "
                         "amended cell trains:\n" + "\n".join(extra))
    if not instrument_tracked:
        raise SystemExit("the amended instrument is not git-tracked — commit the amendment first")


def committed_guard(registered: bool) -> None:
    """On a registered out path: guard_lines over the live git status."""
    if not registered:
        return
    try:
        d = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"],
                           capture_output=True, text=True, timeout=10, check=True)
        t = subprocess.run(["git", "ls-files", "--error-unmatch", str(Path(__file__).resolve())],
                           capture_output=True, text=True, timeout=10)
    except Exception as e:  # noqa: BLE001
        raise SystemExit(f"git check failed ({e}) — refusing to train on a registered out path")
    guard_lines([ln for ln in d.stdout.splitlines() if ln.strip()], t.returncode == 0)


def load_diagnostic(path: Path = DIAG_PAYLOAD, require_branch: str | None = BRANCH_B) -> dict:
    if not path.exists():
        raise SystemExit(f"diagnostic payload {path} missing — the amendment is licensed by its verdict")
    p = json.loads(path.read_text())
    v = p.get("verdict") or {}
    if p.get("partial"):
        raise SystemExit("the diagnostic payload is PARTIAL — it licenses nothing")
    if require_branch is not None and v.get("branch") != require_branch:
        raise SystemExit(f"diagnostic verdict is {v.get('branch')!r}, not {require_branch!r} — the "
                         "amendment is licensed under that branch only")
    return {"payload_sha256": _sha(path), "registration_sha256": p.get("registration_sha256"),
            "branch": v.get("branch"), "mechanism": v.get("mechanism"), "qualifiers": v.get("qualifiers"),
            "tie_scope": v.get("tie_scope"), "leg2_raw_seed0": v.get("leg2_raw_seed0"),
            "dE_br_seed0": v.get("dE_br_seed0"), "dE_br_seed0_ci95": v.get("dE_br_seed0_ci95"),
            "dE_br_pooled": v.get("dE_br_pooled"), "dE_br_ci95": v.get("dE_br_ci95"),
            "x_raw_seed0": v.get("x_raw_seed0"), "x_raw_sentence": v.get("x_raw_sentence")}


def disclosure_sentence(diag: dict) -> str:
    quals = [q for q in (diag.get("qualifiers") or []) if q.startswith("underpowered")]
    power = ("; " + quals[0]) if quals else ""
    return (f"read under the {AMENDMENT_DATE} rider amendment after the registered rider fired at S1 L3 "
            f"(raw leg 2 +0.0132 against the 0.01 band); diagnostic branch {diag.get('branch')}, "
            f"mechanism {diag.get('mechanism')}; {REROUTE_SENTENCE}; {DOMINANCE_SENTENCE}; "
            f"S1 diagnostic X_raw at seed 0 {diag.get('x_raw_seed0'):+.4f}, "
            f"{diag.get('x_raw_sentence')}{power}")


def preserve_v1(out_path: Path) -> dict | None:
    """A frozen-instrument payload at the registered out path is renamed to
    <stem>.rider_v1.json before anything trains; an amended payload is left
    for re-emission; an existing v1 file is never overwritten."""
    if not out_path.exists():
        return None
    p = json.loads(out_path.read_text())
    if AMENDED_MARK in str(p.get("registered", "")):
        return None
    v1 = out_path.with_name(out_path.stem + RIDER_V1_SUFFIX)
    if v1.exists():
        raise SystemExit(f"{v1} already exists — refusing to overwrite a preserved rider-v1 payload")
    out_path.rename(v1)
    return {"path": str(v1), "sha256": _sha(v1), "frozen_instrument_sha256":
            ((p.get("provenance") or {}).get("instrument_sha256"))}


def conclude_amended(primary_payload: dict, replication_payload: dict) -> dict:
    """The frozen conclusion on two AMENDED payloads, with the amendment
    block and the disclosure; a frozen-instrument (rider v1) payload is
    refused — no v1 label is read."""
    for role, p in (("primary", primary_payload), ("replication", replication_payload)):
        if AMENDED_MARK not in str(p.get("registered", "")):
            raise SystemExit(f"{role} payload was written by the frozen instrument (rider v1) — the "
                             "amended --conclude-from refuses it; no v1 label is read")
        if not p.get("amendment"):
            raise SystemExit(f"{role} payload carries no amendment block")
        prov = p.get("provenance") or {}
        if "git_status_tracked" not in prov:
            raise SystemExit(f"{role} payload carries no tracked-status attestation")
        extra = unlicensed_lines(list(prov["git_status_tracked"]))
        if extra:
            raise SystemExit(f"{role} payload was written over tracked modifications beyond the "
                             f"licensed S1 state-file append — a violation, not concluded: {extra}")
    out = fz.conclude(primary_payload, replication_payload)
    for sp in out["spaces"]:
        out["spaces"][sp]["rider_amended"] = {
            "primary": primary_payload["per_space"][sp]["rider"],
            "replication": replication_payload["per_space"][sp]["rider"]}
    diag = primary_payload["amendment"]["diagnostic"]
    out["amendment"] = {"date": AMENDMENT_DATE, "reroute": REROUTE_SENTENCE,
                        "dominance": DOMINANCE_SENTENCE,
                        "disclosure": disclosure_sentence(diag),
                        "diagnostic": diag,
                        "rider_v1_preserved": {"primary": primary_payload["amendment"].get("rider_v1_preserved"),
                                               "replication": replication_payload["amendment"].get("rider_v1_preserved")}}
    out["rule"] = out["rule"] + f"; {AMENDED_MARK}: rider leg 2 = the twin-referenced dependence-excess leg"
    return out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = fz.build_parser()
    ap.add_argument("--n-boot", type=int, default=N_BOOT)
    return ap


def main() -> None:
    args = build_parser().parse_args()
    if args.conclude_from:
        pp = json.loads(Path(args.conclude_from[0]).read_text())
        rp = json.loads(Path(args.conclude_from[1]).read_text())
        print(json.dumps(conclude_amended(pp, rp), indent=1))
        return

    assert_frozen_instrument()
    registered_outs = {(REAL / n).resolve() for n in REGISTERED_OUTS}
    out_path = Path(args.out).resolve()
    registered = out_path in registered_outs
    if args.only and registered:
        raise SystemExit("--only smoke runs may not write a registered out path")
    if registered and OUT_STEM_OF_TAG[args.space_tag] not in out_path.name:
        raise SystemExit(f"registered out {out_path.name} does not belong to --space-tag {args.space_tag}")
    state_path = Path(args.out + ".state.jsonl")
    if registered and state_path.exists() and not args.resume:
        raise SystemExit(f"FRESH-STATE PIN: {state_path} exists; pass --resume only for the four "
                         f"resumes the {AMENDMENT_DATE} amendment licenses (or a crashed run)")
    if args.space_tag not in HARVESTS_OF_TAG:
        raise SystemExit(f"unregistered --space-tag {args.space_tag!r}")
    committed_guard(registered)
    diag = load_diagnostic(require_branch=(BRANCH_B if registered else None))

    data = HarvestData(args.harvest)
    split_names = data.row_split()
    bind_spaces_to_harvest(data.ref_meta,
                           {"buckets16": args.buckets16, "buckets512": args.buckets512},
                           n_slots=args.n_slots)

    fid = Path(args.fidelity)
    if not fid.exists():
        raise SystemExit("R1 harvest-fidelity rider missing (registered gate)")
    rider_payload = json.loads(fid.read_text())
    if rider_payload.get("verdict") != "PASS":
        raise SystemExit("R1 rider verdict is not PASS — harvest quarantined")
    if rider_payload.get("npz_sha256_validated") != data.npz_shas:
        raise SystemExit("R1 rider validated a DIFFERENT harvest version")

    p3_cells = load_phase3_cells(Path(args.phase3_state), Path(args.phase3_payload), data.npz_shas)
    p3_payload = json.loads(Path(args.phase3_payload).read_text())
    re_m = margins(p3_cells, "c", expected_clusters=30)
    want = {(m["space"], m["offset"], m["capacity"]): m for m in p3_payload["margins"]}
    for m in re_m:
        w = want.get((m["space"], m["offset"], m["capacity"]))
        if w is None or abs(m["margin"] - w["margin"]) > 1e-12 \
                or max(abs(a - b) for a, b in zip(m["ci95"], w["ci95"])) > 1e-12:
            raise SystemExit("phase-3 state file does not reproduce its own payload "
                             f"margins at {m['space']} off{m['offset']} {m['capacity']}")
    p3_ids = {c["cell"] for c in p3_cells}

    spaces = build_spaces(data, tag=args.space_tag,
                          buckets16=args.buckets16, glue16=args.glue16,
                          buckets512=args.buckets512, glue512=args.glue512,
                          groups_path=args.groups)
    reg_spaces = registered_spaces(args.space_tag)
    for sp in reg_spaces:
        if sp not in spaces:
            raise SystemExit(f"label space {sp} not built")
    grid = build_grid_amended(reg_spaces)
    check_grid_against_committed(grid, p3_ids, reg_spaces)

    hidden = data.array("hidden")
    top_ids = data.array("top_ids")
    slots = data.array("slots")
    t_m = time.time()
    moments = train_moments(hidden, data.lengths, split_names)
    committed_sha = committed_moments_sha(args.harvest)
    if committed_sha is not None and committed_sha != moments["sha256"]:
        raise SystemExit("hz moments sha differs from the committed OQ-17 payload's for this harvest "
                         f"({moments['sha256'][:12]} vs {committed_sha[:12]}) — refusing")
    print(f"[moments] train rows {moments['n_train_rows']}, positions "
          f"{moments['n_train_positions']}, sha {moments['sha256'][:12]}"
          f"{' == committed OQ-17' if committed_sha else ' (harvest outside the registered four)'}, "
          f"{time.time() - t_m:.0f}s", flush=True)
    perms = {seed: derangement_by_prompt(data.prompt_idx, split_names, seed) for seed in SEEDS}
    all_offsets = sorted({o for sp in reg_spaces for o in offsets_for_space(sp)})
    geometry = {str(seed): {f"off{o}": twin_geometry(data.lengths, perms[seed], o,
                                                     data.tokens.shape[1], data.prompt_idx)
                            for o in all_offsets}
                for seed in SEEDS}
    for seed, g in geometry.items():
        for o, gg in g.items():
            if gg["corrected_twin_same_prompt_frac"] != 0.0:
                raise SystemExit(f"corrected twin reads its own prompt at seed {seed} {o} — refusing")
    perm_shas = {str(seed): hashlib.sha256(perms[seed].astype(np.int64).tobytes()).hexdigest()
                 for seed in SEEDS}
    factory_of = make_factories(top_ids, hidden, slots, data.lengths, args.n_slots, moments, perms)

    probe_rows = np.zeros(1, np.int64)
    a_dim = sum(b.dim for b in feature_blocks(data, "a", probe_rows, probe_rows, n_slots=args.n_slots))
    dims_recorded = {arm: [b.dim for b in factory_of[(arm, SEEDS[0])](probe_rows, probe_rows)]
                     for arm in ARMS}
    dims_recorded["a"] = int(a_dim)
    dims_recorded["hidden"] = int(hidden.shape[2])
    dims_recorded["tok_bins"] = int(FREETOK_BINS)
    dims_total = {arm: int(a_dim + sum(dims_recorded[arm])) for arm in ARMS}
    if dims_total["fplus_b"] != dims_total["fplus_r"]:
        raise SystemExit("twin arms are not equal-dims — refusing")

    v1 = preserve_v1(out_path) if registered else None
    if v1:
        print(f"[preserve] frozen-instrument payload moved to {v1['path']} (sha {v1['sha256'][:12]})", flush=True)

    done: dict[str, dict] = {}
    if state_path.exists():
        done = {k: normalize_hist(v) for k, v in parse_state(state_path.read_text(), data.npz_shas).items()}
        print(f"[resume] {len(done)} cells already in the state file", flush=True)
    else:
        with state_path.open("w") as f:
            f.write(json.dumps(state_header(data.npz_shas)) + "\n")

    expected = None if args.only else EXPECTED_CLUSTERS
    t0 = time.time()
    cells: list[dict] = []
    n_resumed = 0
    n_retrained_shuffled = 0
    riders: dict[str, dict | None] = {sp: None for sp in reg_spaces}
    for i, (sp, off, arm, cap, seed, shuffled) in enumerate(grid):
        cid = cell_id(sp, off, arm, cap, seed, shuffled)
        if not only_match(args.only, cid):
            continue
        if reusable(cid, done, shuffled):
            cells.append(done[cid])
            n_resumed += 1
        else:
            if shuffled:
                if cid in done:
                    n_retrained_shuffled += 1
                res = run_cell_diag(data, spaces, sp, off, arm, seed, args.device, factory_of, args.n_slots)
            elif arm == BASE_ARM:
                res = run_cell(data, spaces, sp, off, "a", cap, seed, args.device,
                               shuffled=shuffled, n_slots=args.n_slots)
            else:
                res = run_cell(data, spaces, sp, off, "a", cap, seed, args.device,
                               shuffled=shuffled, extra_factory=factory_of[(arm, seed)],
                               feats_label=arm, n_slots=args.n_slots)
            cells.append(res)
            with state_path.open("a") as f:
                f.write(json.dumps(res) + "\n")
            print(f"[{i + 1}/{len(grid)}] {cid}: test_acc={res['test_acc']:.4f} "
                  f"(maj {res['majority_rate_test']:.4f}) {res['runtime_s']}s "
                  f"total {time.time() - t0:.0f}s", flush=True)
        if shuffled:
            riders[sp] = rider_check_amended(cells, sp, int(spaces[sp]["n_classes"]),
                                             n_boot=args.n_boot, expected_clusters=expected)

    pooled = cells + p3_cells
    per_space = {}
    for sp in reg_spaces:
        r2_ok = bool(riders[sp] and riders[sp].get("pass"))
        sp_cells = [c for c in cells if c["space"] == sp]
        sp_pooled = [c for c in pooled if c["space"] == sp]
        sp_lin = relabel_committed_linear_a(p3_cells, sp)
        d_rows = margins(sp_cells, "fplus_b", expected_clusters=expected, base_feats=TWIN_ARM) if r2_ok else []
        mt = margins(sp_cells, "fplus_b", expected_clusters=expected, base_feats="fplus") if r2_ok else []
        mnr = margins(sp_cells, TWIN_ARM, expected_clusters=expected, base_feats="fplus") if r2_ok else []
        mf = margins(sp_pooled, "fplus", expected_clusters=expected, base_feats="a") if r2_ok else []
        mfx = margins(sp_cells + sp_lin, "fplus", expected_clusters=expected, base_feats=fz.LIN_BASE) if r2_ok else []
        mc = margins(sp_pooled, "fplus", expected_clusters=expected, base_feats="c") if r2_ok else []
        reader = reader_validity(sp_cells, mf, mfx, sp)
        gate = gate_row(d_rows, sp)
        per_space[sp] = {
            "offsets": list(offsets_for_space(sp)),
            "n_cells": len([c for c in sp_cells if not c["shuffled"]]),
            "rider": riders[sp],
            "reader_valid": reader,
            "gate": {"space": sp, "offset": GATE_OFFSET, "capacity": GATE_CAPACITY,
                     "row": gate, "fires": bool(reader["ok"] and gate_fires(gate)),
                     "label_if_alone": (LABEL_READER_INVALID if not reader["ok"] else None),
                     "rule": ("three-leg READER-INVALID precondition, then D CI95 lower > 0, all "
                              "three seeds positive, point >= +0.005")},
            "d_fplus_b_vs_fplus_r": d_rows,
            "mt_fplus_b_vs_fplus": mt,
            "mn_r_fplus_r_vs_fplus": mnr,
            "mf_fplus_vs_a": mf,
            "mfx_fplus_vs_committed_linear_a": mfx,
            "mc_fplus_vs_c": mc,
        }

    def _git() -> tuple[str, list[str]]:
        try:
            r = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=10)
            d = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"],
                               capture_output=True, text=True, timeout=10)
            lines = [ln for ln in d.stdout.splitlines() if ln.strip()]
            return (r.stdout.strip() or "unknown") + ("-dirty" if lines else ""), lines
        except Exception:  # noqa: BLE001
            return "unknown", []

    git_commit, git_porcelain = _git()
    import torch

    payload = {
        "registered": ("OQ-18 COARSE-LABEL FULL-FREE RE-TEST REGISTRATION (docs/BLUEPRINT.md, "
                       "2026-09-06, before any registered cell ran; critic round applied before "
                       f"the freeze commit); consequence rules act on {args.parent_finding} — "
                       f"{AMENDED_MARK} (rider leg 2; docs/BLUEPRINT.md dated amendment; "
                       "docs/OQ18_RIDER_DIAGNOSTIC.md)"),
        "amendment": {"date": AMENDMENT_DATE, "what": "rider leg 2 = the twin-referenced dependence-excess "
                      "leg at seed 0; fourth shuffled cell (fplus_r) per space; registered raw leg 2 "
                      "reported; leg 1 unchanged; nothing else",
                      "reroute": REROUTE_SENTENCE, "dominance": DOMINANCE_SENTENCE,
                      "diagnostic": diag, "disclosure": disclosure_sentence(diag),
                      "rider_v1_preserved": v1,
                      "resumed_cells": int(n_resumed), "retrained_shuffled_rows": int(n_retrained_shuffled)},
        "harvest": args.harvest,
        "tag": args.space_tag,
        "levels": list(LEVELS),
        "spaces_registered": list(reg_spaces),
        "n_cells": len([c for c in cells if not c["shuffled"]]),
        "partial": bool(args.only),
        "resumed_cells": int(n_resumed),
        "offsets_of_space": {sp: list(offsets_for_space(sp)) for sp in reg_spaces},
        "cells": [{k: v for k, v in c.items() if k not in ("_clusters", "_hist")} for c in cells],
        "per_space": per_space,
        "standardization": {
            "block": "hz = clip(h_a, train lo, train hi) then (x - train mu) / max(train sd, sd_floor)",
            "moments_sha256": moments["sha256"],
            "moments_sha_matches_committed_oq17": (None if committed_sha is None else True),
            "n_train_rows": moments["n_train_rows"],
            "n_train_positions": moments["n_train_positions"],
            "sd_floor": moments["sd_floor"],
            "sd_min": float(moments["sd"].min()), "sd_median": float(np.median(moments["sd"])),
            "sd_max": float(moments["sd"].max()),
            "abs_lo_hi_max": float(max(np.abs(moments["lo"]).max(), np.abs(moments["hi"]).max())),
        },
        "twin": {"arm": TWIN_ARM, "seed_base": TWIN_SEED_BASE, "construction": CONSTRUCTION,
                 "perm_sha256": perm_shas, "geometry": geometry},
        "phase3_state": str(args.phase3_state),
        "phase3_payload_margins_reproduced": True,
        "provenance": {
            "git_commit": git_commit,
            "git_status_tracked": git_porcelain,
            "git_status_licensed": not unlicensed_lines(git_porcelain),
            "licensed_dirty_lines": list(LICENSED_DIRTY),
            "instrument_sha256": _sha(Path(__file__)),
            "amended_instrument_sha256": _sha(Path(__file__)),
            "frozen_instrument_sha256": FROZEN_INSTRUMENT_SHA256,
            "diagnostic_payload_sha256": diag["payload_sha256"],
            "args": redact_args(vars(args)),
            "harvest_npz_sha256": data.npz_shas,
            "label_space_sha256": {p.name: _sha(p) for p in (
                Path(args.buckets16), Path(args.glue16),
                Path(args.buckets512), Path(args.glue512),
                Path(args.groups)) if p.exists()},
            "feature_dims_recorded": dims_recorded,
            "arm_dims_total": dims_total,
            "phase3_state_sha256": _sha(Path(args.phase3_state)),
            "phase3_payload_sha256": _sha(Path(args.phase3_payload)),
            "torch_version": torch.__version__,
            "device": args.device,
            "determinism_note": ("CUDA probe training uses atomics; per-cell results are "
                                 "evidenced by the recorded state file, not rerun-exactness"),
        },
        "runtime_s": round(time.time() - t0, 1),
    }
    Path(args.out).write_text(json.dumps(payload, indent=1))
    print(json.dumps({sp: {"reader_valid": per_space[sp]["reader_valid"]["ok"],
                           "gate_fires": per_space[sp]["gate"]["fires"],
                           "gate": per_space[sp]["gate"]["row"],
                           "rider": {k: per_space[sp]["rider"].get(k) for k in
                                     ("pass", "leg1_pass", "leg2_pass", "registered_leg2_raw",
                                      "amended_leg2", "x_raw_seed0", "x_raw_sentence")}
                                    if per_space[sp]["rider"] else None,
                           "n_d_rows": len(per_space[sp]["d_fplus_b_vs_fplus_r"])}
                      for sp in reg_spaces}, indent=1))


if __name__ == "__main__":
    main()
