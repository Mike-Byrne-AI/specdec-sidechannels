#!/usr/bin/env python3
"""Phase-2 harvest summary: the committed exit evidence for the shadow
weight-slot harvest (BLUEPRINT Phase 2 protocol, registered 2026-08-30).

Reads every shadow_s{S}.meta.json + npz pair in --dir, verifies each npz
against its meta sha256 (the binding that makes gitignored raw arrays citable
evidence), enforces cross-seed meta consistency on everything
identity-relevant except the seed, and reports:

  - pair counts (total, per offset, per pinned probe split) vs the >= 1M
    exit bar;
  - length / EOS-attrition stats;
  - per-layer slot diagnostics: occupancy entropy over slot usage (bits, vs
    log2(n_slots)), top-32-slot usage share, mean unique slots per anchor;
  - sanity: mass-vector sums ~ 1 (f16 rounding tolerance), entropy and
    hidden-norm ranges, meta-vs-array count agreement.

Run: python tools/summarize_harvest.py --dir results/real/harvest_shadow \
        --out results/real/harvest_shadow_summary.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from sideband.harvest import pairs_per_row, split_of_prompt, total_pairs  # noqa: E402

EXIT_BAR = 1_000_000

MUST_MATCH = (
    "model", "layer_regex", "layers", "n_slots", "top_n", "sketch_seed",
    "prompts", "n_prompts", "n_prompts_used", "max_new", "temperature",
    "top_m", "buckets16", "buckets32", "buckets64", "buckets512",
    "load_4bit", "no_chat_template", "chat_template_used",
    "date_string_pinned", "target_load", "alignment", "split_rule",
    "layer_names", "sketch_layer_seeds", "row_seed_convention",
    "prompts_sha256", "buckets16_sha256", "buckets32_sha256",
    "buckets64_sha256", "buckets512_sha256", "gamma",
    # S3 (moe_telemetry) identity keys; absent from S1 metas, where they
    # compare None == None across seeds and change nothing.
    "gate_regex", "n_experts", "top_k", "bf16_routers",
    "telemetry_semantics", "load_regime_verified",
    # Library drift across seeds (e.g. a pip upgrade before a +4-seed
    # extension) would change tokenization/template/kernels mid-dataset.
    "torch_version", "transformers_version",
)


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def summarize(harvest_dir: Path) -> dict:
    metas = sorted(harvest_dir.glob("*_s*.meta.json"))
    if not metas:
        raise SystemExit(f"no *_s*.meta.json in {harvest_dir}")
    prefixes = {mp.name.split("_s")[0] for mp in metas}
    if len(prefixes) > 1:
        raise SystemExit(f"mixed harvest prefixes in {harvest_dir}: {sorted(prefixes)} — "
                         "one source per directory (S3 registration, 2026-08-31)")

    seeds, per_seed = [], []
    ref = None
    n_slots = top_n = gamma = None
    layer_names: list[str] = []

    # Accumulators across seeds
    all_lengths: list[np.ndarray] = []
    prompt_idx_ref: np.ndarray | None = None
    slot_counts: np.ndarray | None = None  # (L, n_slots)
    uniq_sum = np.zeros(0)
    uniq_n = 0
    mass_err: dict[str, float] = {}
    ent_min, ent_max, ent_sum, ent_n = np.inf, -np.inf, 0.0, 0
    hid_norm_min, hid_norm_max = np.inf, -np.inf
    problems: list[str] = []

    for mp in metas:
        meta = json.loads(mp.read_text())
        seed = int(meta["seed"])
        seeds.append(seed)
        npz_path = harvest_dir / meta["npz_file"]
        if not npz_path.exists():
            raise SystemExit(f"{mp.name}: missing npz {meta['npz_file']}")
        if _sha(npz_path) != meta["npz_sha256"]:
            raise SystemExit(f"{mp.name}: npz sha mismatch — raw data does not match committed meta")

        ident = {k: meta.get(k) for k in MUST_MATCH}
        if ref is None:
            ref = ident
            # S1 metas record n_slots/top_n (HashSketch); S3 metas record
            # n_experts/top_k (router address stream). Same array geometry.
            n_slots = int(meta.get("n_slots") or meta["n_experts"])
            top_n = int(meta.get("top_n") or meta["top_k"])
            gamma = int(meta["gamma"])
            layer_names = list(meta["layer_names"])
            slot_counts = np.zeros((len(layer_names), n_slots), dtype=np.int64)
        elif ident != ref:
            diff = [k for k in MUST_MATCH if ident.get(k) != ref.get(k)]
            raise SystemExit(f"{mp.name}: meta disagrees with seed {seeds[0]} on {diff}")

        z = np.load(npz_path)
        lengths = z["lengths"].astype(np.int64)
        pidx = z["prompt_idx"].astype(np.int64)
        if prompt_idx_ref is None:
            prompt_idx_ref = pidx
        elif not np.array_equal(pidx, prompt_idx_ref):
            raise SystemExit(f"{mp.name}: prompt_idx differs across seeds")
        if int(lengths.sum()) != int(meta["n_anchors"]):
            problems.append(f"seed {seed}: n_anchors meta={meta['n_anchors']} arrays={int(lengths.sum())}")
        if total_pairs(lengths, gamma) != int(meta["n_pairs"]):
            problems.append(f"seed {seed}: n_pairs meta={meta['n_pairs']} recomputed={total_pairs(lengths, gamma)}")
        all_lengths.append(lengths)

        T = z["tokens"].shape[1]
        valid = np.arange(T)[None, :] < lengths[:, None]  # (P, T)

        slots = z["slots"]  # (P, T, L, top_n)
        for li in range(len(layer_names)):
            s = slots[valid][:, li, :].ravel()
            s = s[s >= 0]
            slot_counts[li] += np.bincount(s, minlength=n_slots)
        uniq = (slots[valid] >= 0).sum(axis=-1)  # (n_valid, L)
        uniq_sum = uniq.sum(axis=0) + (uniq_sum if uniq_sum.size else 0)
        uniq_n += uniq.shape[0]

        for key in z.files:
            if key.startswith("mass"):
                s = z[key][valid].astype(np.float32).sum(axis=-1)
                mass_err[key] = max(mass_err.get(key, 0.0), float(np.abs(s - 1.0).max()))

        ent = z["entropy"][valid]
        ent_min = min(ent_min, float(ent.min()))
        ent_max = max(ent_max, float(ent.max()))
        ent_sum += float(ent.sum())
        ent_n += int(ent.size)

        hn = np.linalg.norm(z["hidden"][valid].astype(np.float32), axis=-1)
        hid_norm_min = min(hid_norm_min, float(hn.min()))
        hid_norm_max = max(hid_norm_max, float(hn.max()))

        per_seed.append({
            "seed": seed,
            "n_anchors": int(lengths.sum()),
            "n_pairs": int(total_pairs(lengths, gamma)),
            "mean_length": float(lengths.mean()),
            "eos_hit_fraction": float((lengths < int(meta["max_new"])).mean()),
            "npz_sha256": meta["npz_sha256"],
            "git_commit": meta.get("git_commit"),
        })

    L_all = np.concatenate(all_lengths)
    pairs_by_offset = {
        f"offset_{j}": int(sum(max(0, int(n) - (j - 1)) for n in L_all))
        for j in range(1, gamma + 1)
    }
    n_pairs_total = int(sum(pairs_by_offset.values()))
    assert n_pairs_total == int(total_pairs(L_all, gamma))

    split_names = [split_of_prompt(int(i)) for i in prompt_idx_ref]
    pairs_by_split: dict[str, int] = {"train": 0, "val": 0, "test": 0}
    prompts_by_split: dict[str, int] = {"train": 0, "val": 0, "test": 0}
    for name in split_names:
        prompts_by_split[name] += 1
    for lengths in all_lengths:
        for i, n in enumerate(lengths):
            pairs_by_split[split_names[i]] += pairs_per_row(int(n), gamma)

    freq = slot_counts / np.maximum(slot_counts.sum(axis=1, keepdims=True), 1)
    with np.errstate(divide="ignore", invalid="ignore"):
        occ_entropy = [float(-(f[f > 0] * np.log2(f[f > 0])).sum()) for f in freq]
    top32_share = [float(np.sort(f)[::-1][:32].sum()) for f in freq]
    slots_never = [int((c == 0).sum()) for c in slot_counts]

    if not mass_err:
        problems.append("no mass arrays found in npz files")
    for key, err in sorted(mass_err.items()):
        if err > 0.01:
            problems.append(f"{key} sums drift beyond f16 tolerance: {err:.4f}")
    # Every bucket space the meta binds must actually be logged — a future
    # edit dropping a mass array would otherwise summarize clean.
    for k in ("16", "32", "64", "512"):
        if ref.get(f"buckets{k}_sha256") and f"mass{k}" not in mass_err:
            problems.append(f"meta binds buckets{k} but npz has no mass{k} array")

    return {
        "dir": str(harvest_dir).replace("\\", "/"),
        "seeds": seeds,
        "identity": ref,
        "per_seed": per_seed,
        "n_prompts": int(len(prompt_idx_ref)),
        "prompts_by_split": prompts_by_split,
        "n_anchors_total": int(L_all.sum()),
        "n_pairs_total": n_pairs_total,
        "pairs_by_offset": pairs_by_offset,
        "pairs_by_split": pairs_by_split,
        "exit_bar": EXIT_BAR,
        "exit_met": bool(n_pairs_total >= EXIT_BAR),
        "length_stats": {
            "mean": float(L_all.mean()),
            "median": float(np.median(L_all)),
            "p10": float(np.percentile(L_all, 10)),
            "p90": float(np.percentile(L_all, 90)),
            "min": int(L_all.min()),
            "max": int(L_all.max()),
            "eos_hit_fraction": float((L_all < int(ref["max_new"])).mean()),
        },
        "slot_diagnostics": {
            "layer_names": layer_names,
            "occupancy_entropy_bits": occ_entropy,
            "max_entropy_bits": float(np.log2(n_slots)),
            "top32_slot_usage_share": top32_share,
            "slots_never_used": slots_never,
            "mean_unique_slots_per_anchor": [float(u / max(uniq_n, 1)) for u in np.atleast_1d(uniq_sum)],
            "top_n": top_n,
        },
        "sanity": {
            "mass_sum_max_abs_err": {k: v for k, v in sorted(mass_err.items())},
            "entropy_nats": {"min": ent_min, "max": ent_max, "mean": ent_sum / max(ent_n, 1)},
            "hidden_l2": {"min": hid_norm_min, "max": hid_norm_max},
        },
        "problems": problems,
        "verdict": "OK" if (not problems and n_pairs_total >= EXIT_BAR) else
                   ("PROBLEMS" if problems else "EXIT_BAR_NOT_MET"),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="results/real/harvest_shadow")
    ap.add_argument("--out", default="results/real/harvest_shadow_summary.json")
    args = ap.parse_args()

    summary = summarize(Path(args.dir))
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(summary, indent=1, sort_keys=True))
    print(json.dumps({k: summary[k] for k in
                      ("n_pairs_total", "exit_met", "pairs_by_split", "verdict", "problems")}, indent=2))


if __name__ == "__main__":
    main()
