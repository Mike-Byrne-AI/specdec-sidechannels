"""F-24 support figure 1 (FINDINGS.md F-24 (iii); lever 2 of the operator's science-lever decisions of 2026-10-16): the
per-cluster correlations of the twin payloads, cross-seed, with the same-subtrahend control.

F-24 says: "The per-cluster correlations recorded in the twin payloads (aligned gain against twin gain,
+0.58..+0.76) are a shared-subtrahend artifact — the three deltas share the fplus probe — and license
nothing: cross-seed the correlations collapse to about +0.1 and a same-subtrahend control sits at +0.49
(critic-recomputed on the S3 primary; no committed artifact records it)". This script is that artifact.

Reads, for each of the four committed twin payloads (fullfree_s1_twin, fullfree_s1_r_twin, fullfree_s3_twin,
fullfree_s3_r_twin), the twin state file (the three fplus_r cells) and the full-free state file it paired
against (the fplus, fplus_b and fplus_n cells at the gate cell, train seeds 0, 1, 2), and from the
per-cluster [successes, trials] rows computes, over the 30 test clusters:

  A  REPRODUCTION: the pooled (seed-summed) Pearson of Mt against Mn_r and of Mt against Mn exactly as
     tools/run_fullfree_twin.per_cluster_corr defines them; asserted equal to the payload's
     per_cluster_corr values to 1e-9 on every harvest.
  B  CROSS-SEED: Pearson of Mt from train seed i (acc(fplus_b_i) - acc(fplus_i) per cluster) against Mn_r
     from train seed j != i (acc(fplus_r_j) - acc(fplus_j)), the six ordered pairs and their mean; the
     three within-seed (i = j) values beside them.
  C  SAME-SUBTRAHEND CONTROL: Pearson of Mt from seed i against acc(fplus_j) - acc(fplus_i), j != i — a
     delta that shares the subtrahend with Mt and whose minuend carries no slots block (another seed's
     full-free probe) — the six ordered pairs and their mean. This is the script's reading of F-24's
     "same-subtrahend control"; the record does not say how the critic built that control, so the reading
     is named here and pinned to F-24's figure, and a failed pin is a discrepancy reported in README.md,
     never a patched construction.
  D  DESCRIPTIONS, not pinned: pooled Mn against Mn_r (the two twins share the subtrahend, the train seed
     and the 6801 free dims, and no slots content); cross-seed Mt_i against Mn_j (the shift twin); the
     pooled correlations with fplus_b against fplus_n and fplus_r RAW accuracies (no shared subtrahend).

The state files are bound by sha, not by name: each twin payload records the full-free payload's and state
file's sha256 it paired against, and both are asserted against the files read here before any number.

Pinned 2026-10-16 before the rerun, asserted by the script on the S3 PRIMARY (fullfree_s3_twin), the
harvest F-24 names: A reproduces to 1e-9 on every harvest; B's cross-seed mean lies in [0.00, 0.20]
("about +0.1"); C's mean lies in [0.39, 0.59] ("+0.49"). The script always writes corr_control_out.json
beside itself (LF) with every value and each pin's verdict, and exits non-zero if any pin failed, so a
discrepancy is on the record rather than absent from it (the folder's README says why this differs from
the 2026-10-15 audit folder's write-only-on-pass rule). numpy only; a second on CPU.
"""
from __future__ import annotations

import json
import sys
from itertools import permutations
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[3]
R = REPO / "results" / "real"
OUT = Path(__file__).resolve().with_name("corr_control_out.json")
SEEDS = (0, 1, 2)
PAYLOADS = {  # twin payload stem -> (full-free payload stem, label space of the gate cell, F-24's harvest words)
    "fullfree_s1_twin": ("fullfree_s1", "L1_concept_k16", "S1 primary"),
    "fullfree_s1_r_twin": ("fullfree_s1_r", "L1_concept_k16", "S1 replication"),
    "fullfree_s3_twin": ("fullfree_s3", "L1_olmoe_k16", "S3 primary"),
    "fullfree_s3_r_twin": ("fullfree_s3_r", "L1_olmoe_k16", "S3 replication"),
}
PINNED_HARVEST = "fullfree_s3_twin"
PINS = {"A_reproduces_to": 1e-9, "B_cross_seed_mean": (0.00, 0.20), "C_same_subtrahend_mean": (0.39, 0.59)}


def _rows(path: Path) -> dict[str, dict]:
    rows = [json.loads(ln) for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    return {r["cell"]: r for r in rows if "cell" in r and not r.get("shuffled")}


def _cell(space: str, arm: str, seed: int) -> str:
    return f"{space}|off2|{arm}|mlp256|s{seed}"


def _acc_by_cluster(cells: dict[str, dict], space: str, arm: str, seed: int, prompts: list[str]) -> tuple[np.ndarray, np.ndarray]:
    c = cells[_cell(space, arm, seed)]["_clusters"]
    succ = np.array([c[p][0] for p in prompts], dtype=np.float64)
    n = np.array([c[p][1] for p in prompts], dtype=np.float64)
    return succ, n


def _pearson(a: np.ndarray, b: np.ndarray) -> float | None:
    """None on a zero-variance side, as per_cluster_corr returns None there."""
    if a.std() == 0 or b.std() == 0:
        return None
    return float(np.corrcoef(a, b)[0, 1])


def _mean(values) -> float | None:
    vals = list(values)
    return None if any(v is None for v in vals) else float(np.mean(vals))


def pooled_corr(cells, space, top_a, top_b, prompts, base="fplus") -> float | None:
    """tools/run_fullfree_twin.per_cluster_corr, re-stated: seed-summed per-cluster deltas, Pearson."""
    da = np.zeros(len(prompts)); db = np.zeros(len(prompts)); n = np.zeros(len(prompts))
    for s in SEEDS:
        sa, _ = _acc_by_cluster(cells, space, top_a, s, prompts)
        sb, _ = _acc_by_cluster(cells, space, top_b, s, prompts)
        sbase, nb = _acc_by_cluster(cells, space, base, s, prompts)
        da += sa - sbase; db += sb - sbase; n += nb
    return _pearson(da / n, db / n)


def _find_key(d, name: str):
    """The first value under key `name` anywhere in a nested dict (the twin payloads record the full-free
    payload's and state file's sha256 they paired against)."""
    if isinstance(d, dict):
        if name in d:
            return d[name]
        for v in d.values():
            got = _find_key(v, name)
            if got is not None:
                return got
    return None


def _sha(path: Path) -> str:
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest()


def analyse(twin_stem: str) -> dict:
    ff_stem, space, words = PAYLOADS[twin_stem]
    payload = json.loads((R / f"{twin_stem}.json").read_text(encoding="utf-8"))
    for name, path in (("fullfree_state_sha256", R / f"{ff_stem}.json.state.jsonl"), ("fullfree_payload_sha256", R / f"{ff_stem}.json")):
        recorded = _find_key(payload, name)
        if recorded is None:
            raise SystemExit(f"{twin_stem}.json records no {name} — the pairing cannot be bound; refusing")
        if recorded != _sha(path):
            raise SystemExit(f"{twin_stem}.json's {name} differs from {path.name} on disk — refusing")
    twin = _rows(R / f"{twin_stem}.json.state.jsonl")
    ff = _rows(R / f"{ff_stem}.json.state.jsonl")
    cells = {**ff, **twin}
    prompts = sorted(set.intersection(*(set(cells[_cell(space, arm, s)]["_clusters"]) for arm in ("fplus", "fplus_b", "fplus_n", "fplus_r") for s in SEEDS)),
                     key=int)
    acc = {(arm, s): (lambda sn: sn[0] / sn[1])(_acc_by_cluster(cells, space, arm, s, prompts))
           for arm in ("fplus", "fplus_b", "fplus_n", "fplus_r") for s in SEEDS}
    out: dict = {"harvest": words, "space": space, "n_clusters": len(prompts), "twin_payload": f"{twin_stem}.json",
                 "fullfree_payload": f"{ff_stem}.json"}
    # A: reproduction of the payload's pooled correlations
    rec = payload["per_cluster_corr"]
    out["A_pooled"] = {"mt_vs_mn_r": pooled_corr(cells, space, "fplus_b", "fplus_r", prompts),
                       "mt_vs_mn": pooled_corr(cells, space, "fplus_b", "fplus_n", prompts),
                       "payload_mt_vs_mn_r": rec["mt_vs_mn_r"]["pearson"], "payload_mt_vs_mn": rec["mt_vs_mn"]["pearson"]}
    out["A_pooled"]["max_abs_diff"] = max(abs(out["A_pooled"]["mt_vs_mn_r"] - rec["mt_vs_mn_r"]["pearson"]),
                                          abs(out["A_pooled"]["mt_vs_mn"] - rec["mt_vs_mn"]["pearson"]))
    # B: cross-seed Mt_i vs Mn_r_j
    mt = {s: acc[("fplus_b", s)] - acc[("fplus", s)] for s in SEEDS}
    mn_r = {s: acc[("fplus_r", s)] - acc[("fplus", s)] for s in SEEDS}
    mn = {s: acc[("fplus_n", s)] - acc[("fplus", s)] for s in SEEDS}
    cross = {f"{i}->{j}": _pearson(mt[i], mn_r[j]) for i, j in permutations(SEEDS, 2)}
    within = {str(s): _pearson(mt[s], mn_r[s]) for s in SEEDS}
    out["B_cross_seed"] = {"mt_i_vs_mn_r_j": cross, "mean": _mean(cross.values()),
                           "within_seed": within, "within_mean": _mean(within.values())}
    # C: the same-subtrahend control, Mt_i vs (fplus_j - fplus_i)
    ctrl = {f"{i}->{j}": _pearson(mt[i], acc[("fplus", j)] - acc[("fplus", i)]) for i, j in permutations(SEEDS, 2)}
    out["C_same_subtrahend"] = {"mt_i_vs_fplus_j_minus_fplus_i": ctrl, "mean": _mean(ctrl.values())}
    # D: descriptions
    cross_mn = {f"{i}->{j}": _pearson(mt[i], mn[j]) for i, j in permutations(SEEDS, 2)}
    out["D_descriptions"] = {
        "pooled_mn_vs_mn_r": pooled_corr(cells, space, "fplus_n", "fplus_r", prompts),
        "cross_seed_mt_i_vs_mn_j": cross_mn, "cross_seed_mt_i_vs_mn_j_mean": _mean(cross_mn.values()),
        "pooled_raw_fplus_b_vs_fplus_r": _pearson(sum(acc[("fplus_b", s)] for s in SEEDS), sum(acc[("fplus_r", s)] for s in SEEDS)),
        "pooled_raw_fplus_b_vs_fplus_n": _pearson(sum(acc[("fplus_b", s)] for s in SEEDS), sum(acc[("fplus_n", s)] for s in SEEDS)),
    }
    return out


def main() -> int:
    results = {stem: analyse(stem) for stem in PAYLOADS}
    pins = {}
    for stem, r in results.items():
        pins[f"A_reproduces:{stem}"] = {"value": r["A_pooled"]["max_abs_diff"], "pin": f"<= {PINS['A_reproduces_to']}",
                                        "ok": r["A_pooled"]["max_abs_diff"] <= PINS["A_reproduces_to"]}
    s3 = results[PINNED_HARVEST]
    lo, hi = PINS["B_cross_seed_mean"]
    b = s3["B_cross_seed"]["mean"]
    pins["B_cross_seed_mean:S3 primary"] = {"value": b, "pin": f"in [{lo}, {hi}] (F-24: about +0.1)",
                                            "ok": b is not None and lo <= b <= hi}
    lo, hi = PINS["C_same_subtrahend_mean"]
    c = s3["C_same_subtrahend"]["mean"]
    pins["C_same_subtrahend_mean:S3 primary"] = {"value": c, "pin": f"in [{lo}, {hi}] (F-24: +0.49)",
                                                 "ok": c is not None and lo <= c <= hi}
    ok = all(p["ok"] for p in pins.values())
    out = {"pinned_on": "2026-10-16, before the rerun; the pins are F-24's figures, the constructions this file's",
           "pins": pins, "all_pins_hold": ok, "results": results, "numpy_version": np.__version__}
    OUT.write_bytes((json.dumps(out, indent=1) + "\n").encode("utf-8"))
    for k, p in pins.items():
        v = "None" if p["value"] is None else f"{p['value']:.6f}"
        print(f"{'PASS' if p['ok'] else 'FAIL'} {k}: {v} {p['pin']}")
    print("wrote", OUT.name, "; all pins hold" if ok else "; A PIN FAILED (recorded)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
