"""Rider R1-S3 (BLUEPRINT S3 registration, 2026-08-31): harvest fidelity
for the MoE router address-stream harvest.

Structure verbatim from fidelity_rider (S1): teacher-forces prompt +
tokens[:a] through the target as a FRESH full forward (no KV reuse, batch 1,
no padding) at 16 uniform-random (seed, prompt, anchor) triples (>= 4 with
anchor >= 128) and compares the stored anchor. S3 metrics, checked per
triple:
  - per-layer EXPERT-SET overlap (|stored top-k ∩ recomputed top-k|);
  - mass512 L-infinity on the OLMoE space (stored f16 vs recomputed f32);
  - entropy |delta|;
  - argmax equal wherever the recomputed top1-top2 prob gap exceeds the
    pinned gap.
FAIL on any triple quarantines the harvest pending diagnosis.

TOLERANCES: pinned by the dated amendment of 2026-08-31 (BLUEPRINT S3
block) from results/real/fidelity_calibration_olmoe.json (fresh seed-100
non-audit anchors + off-by-one controls), under the derivation mapping
registered BEFORE the calibration ran — S1's NF4 kernel-noise band does
not transfer across models or telemetry types, which is why the S3 lineage
calibrated fresh. The refuse-until-pinned guard below is retained (inert
while constants are set; it re-arms if anyone reverts them to None).
CYCLE BOUND, armed at these values: a FAIL quarantines with no further
widening absent the pre-named entropy mechanism or a NEW named mechanism
+ critic review. Rider rng-seed lineage for S3 starts at 0 and advances
+1 per rerun.

GPU box. Run (after the tolerance amendment):
    python -m sideband.real.fidelity_rider_moe --load-4bit --bf16-routers \
        --prompts data/prompts.jsonl \
        --dir results/real/harvest_moe \
        --out results/real/harvest_fidelity_rider_olmoe.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import numpy as np

from ..harvest import verified_seed_files
from . import require_real_deps
from .fidelity_rider import LONG_ANCHOR, MIN_LONG, N_TRIPLES, sample_triples
from .moe_telemetry import RouterTap, load_quantized_moe, verify_load_regime

# Pinned by the dated TOLERANCE AMENDMENT (BLUEPRINT S3 block, 2026-08-31;
# evidence results/real/fidelity_calibration_olmoe.json, 30 aligned + 30
# off-by-one anchors, derivation mapping registered before the calibration
# ran). Calibrated bands: ALIGNED overlap 7..8/8, mass512 L-inf <= 0.0666,
# entropy <= 0.1676; MISALIGNED overlap <= 2, mass p50 0.887, entropy p50
# 0.766. Overlap is the sharp discriminator (entropy sits only 1.53x below
# the misaligned median) — the AND-structure is load-bearing, as at S1.
# CYCLE BOUND armed: a FAIL at these values quarantines with no further
# widening absent the pre-named entropy mechanism or a NEW named mechanism
# plus critic review; rerun rng-seeds advance +1.
SLOT_OVERLAP_MIN: int | None = 5      # of top_k (8): min per-layer |stored ∩ recomputed|
MASS_LINF_MAX: float | None = 0.20    # 3.0x calibrated aligned max
ENTROPY_ABS_MAX: float | None = 0.50  # 3.0x calibrated aligned max
ARGMAX_GAP: float | None = 0.20       # = mass tolerance (S1 pattern)


def main() -> None:  # pragma: no cover - GPU box entrypoint
    torch, transformers = require_real_deps()
    from .hf_specdec import PINNED_DATE, _assert_gpu_resident, _atomic_write_text, load_buckets

    if None in (SLOT_OVERLAP_MIN, MASS_LINF_MAX, ENTROPY_ABS_MAX, ARGMAX_GAP):
        raise SystemExit(
            "R1-S3 tolerances are not pinned yet: run tools/calibrate_fidelity_moe.py, "
            "land the dated tolerance amendment in the BLUEPRINT S3 block (critic-"
            "reviewed), and set the constants in fidelity_rider_moe.py — in that order.")

    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="allenai/OLMoE-1B-7B-0125-Instruct")
    ap.add_argument("--dir", default="results/real/harvest_moe")
    ap.add_argument("--prompts", default="data/prompts.jsonl")
    ap.add_argument("--buckets512", default="results/real/buckets_olmoe_k512.json")
    ap.add_argument("--rng-seed", type=int, default=0)
    ap.add_argument("--load-4bit", action="store_true")
    ap.add_argument("--bf16-routers", action="store_true")
    ap.add_argument("--allow-cpu-offload", action="store_true")
    ap.add_argument("--out", default="results/real/harvest_fidelity_rider_olmoe.json")
    args = ap.parse_args()

    harvest = Path(args.dir)
    seed_files = []
    npz_shas = {}
    for meta, npz_path in verified_seed_files(harvest):  # sha-verified reads
        z = np.load(npz_path)
        seed_files.append({"meta": meta, "z": z, "lengths": z["lengths"].astype(np.int64)})
        npz_shas[meta["npz_file"]] = meta["npz_sha256"]
    ref_meta = seed_files[0]["meta"]
    if args.model != ref_meta["model"]:
        raise SystemExit(f"--model {args.model} != harvest meta model {ref_meta['model']}")
    if bool(args.load_4bit) != bool(ref_meta["load_4bit"]) or \
            bool(args.bf16_routers) != bool(ref_meta.get("bf16_routers")):
        raise SystemExit("load regime flags do not match the harvest meta "
                         f"(meta: load_4bit={ref_meta['load_4bit']}, "
                         f"bf16_routers={ref_meta.get('bf16_routers')})")

    rng = np.random.default_rng(args.rng_seed)
    triples, topped_up = sample_triples(seed_files, rng)

    tok = transformers.AutoTokenizer.from_pretrained(args.model)
    model, load_tag = load_quantized_moe(transformers, torch, args.model,
                                         args.load_4bit, args.bf16_routers)
    if load_tag != ref_meta["target_load"]:
        raise SystemExit(f"load regime {load_tag} != harvest meta {ref_meta['target_load']}")
    load_verified = verify_load_regime(model, args.load_4bit, args.bf16_routers,
                                       gate_regex=ref_meta["gate_regex"])
    _assert_gpu_resident(model, "model", args.allow_cpu_offload)
    dev = model.device
    vocab = int(model.config.vocab_size)
    expect512 = ref_meta.get("buckets512_sha256")
    if expect512 and hashlib.sha256(Path(args.buckets512).read_bytes()).hexdigest() != expect512:
        raise SystemExit("--buckets512 sha != harvest meta buckets512_sha256 — the "
                         "mass comparison needs the exact space the harvest logged")
    b512 = load_buckets(args.buckets512, vocab, expect_model=args.model)
    b512_t = torch.from_numpy(b512).to(dev)
    n512 = int(b512.max()) + 1

    prompts = [json.loads(l)["prompt"] for l in Path(args.prompts).read_text().splitlines() if l.strip()]
    if hashlib.sha256(Path(args.prompts).read_bytes()).hexdigest() != ref_meta["prompts_sha256"]:
        raise SystemExit("prompts file sha does not match the harvest metas")

    use_chat = (not ref_meta.get("no_chat_template")) and tok.chat_template is not None
    if use_chat != ref_meta["chat_template_used"]:
        raise SystemExit("chat-template availability differs from the harvest regime")

    tap = RouterTap(model, ref_meta["gate_regex"], int(ref_meta["top_k"]))
    if tap.layer_names != list(ref_meta["layer_names"]):
        raise SystemExit("tap gates do not reproduce the harvest meta")
    if sorted(set(tap.n_experts.values())) != [int(ref_meta["n_experts"])]:
        raise SystemExit("expert count does not reproduce the harvest meta")

    results = []
    t0 = time.time()
    with torch.no_grad():
        for fi, r, a in triples:
            sf = seed_files[fi]
            z = sf["z"]
            pidx = int(z["prompt_idx"][r])
            if use_chat:
                text = tok.apply_chat_template([{"role": "user", "content": prompts[pidx]}],
                                               add_generation_prompt=True, tokenize=False,
                                               date_string=PINNED_DATE)
                enc = tok(text, return_tensors="pt", add_special_tokens=False)
            else:
                enc = tok(prompts[pidx], return_tensors="pt")
            prefix = enc["input_ids"][0].tolist() + z["tokens"][r, :a].astype(int).tolist()
            ids = torch.tensor([prefix], device=dev)
            out = model(input_ids=ids)  # fresh full forward, no cache
            experts_rec = tap.collect(1)[0]  # (L, top_k)
            p = torch.softmax(out.logits[0, -1].float(), dim=-1)
            mass = torch.zeros(n512, device=dev).scatter_add_(0, b512_t, p).cpu().numpy()
            ent = float(-torch.special.xlogy(p, p).sum())
            top2 = torch.topk(p, 2).values
            gap = float(top2[0] - top2[1])
            am = int(p.argmax())

            stored = z["slots"][r, a]  # (L, top_k) expert ids
            overlaps = []
            for li in range(stored.shape[0]):
                s_st = set(stored[li][stored[li] >= 0].tolist())
                s_re = set(experts_rec[li][experts_rec[li] >= 0].tolist())
                overlaps.append(len(s_st & s_re))
            mass_linf = float(np.abs(z["mass512"][r, a].astype(np.float32) - mass).max())
            ent_abs = abs(float(z["entropy"][r, a]) - ent)
            argmax_ok = (gap <= ARGMAX_GAP) or (int(z["argmax"][r, a]) == am)
            ok = (min(overlaps) >= SLOT_OVERLAP_MIN and mass_linf <= MASS_LINF_MAX
                  and ent_abs <= ENTROPY_ABS_MAX and argmax_ok)
            results.append({
                "seed": int(sf["meta"]["seed"]), "prompt_idx": pidx, "anchor": a,
                "expert_overlaps": overlaps, "mass512_linf": mass_linf,
                "entropy_abs_delta": ent_abs, "argmax_gap": gap,
                "argmax_checked": gap > ARGMAX_GAP, "argmax_ok": bool(argmax_ok),
                "pass": bool(ok),
            })
            print(f"[rider] seed {sf['meta']['seed']} prompt {pidx} anchor {a}: "
                  f"overlap>={min(overlaps)}/{ref_meta['top_k']} linf={mass_linf:.2e} "
                  f"{'PASS' if ok else 'FAIL'}", flush=True)
    tap.close()

    verdict = "PASS" if all(t["pass"] for t in results) else "FAIL"
    payload = {
        "criteria": {"expert_overlap_min": SLOT_OVERLAP_MIN, "overlap_denominator": int(ref_meta["top_k"]),
                     "mass_linf_max": MASS_LINF_MAX, "entropy_abs_max": ENTROPY_ABS_MAX,
                     "argmax_gap": ARGMAX_GAP,
                     "n_triples": N_TRIPLES, "min_long": MIN_LONG, "long_anchor": LONG_ANCHOR},
        # Binds this PASS to the exact harvest bytes it validated: consumers
        # must refuse a rider that vouches for a different data version.
        "npz_sha256_validated": npz_shas,
        "rng_seed": args.rng_seed,
        "topped_up_long": topped_up,
        "n_long": sum(1 for t in results if t["anchor"] >= LONG_ANCHOR),
        "triples": results,
        "verdict": verdict,
        "runtime_s": round(time.time() - t0, 1),
        "regime": f"teacher-forced full forward, no KV reuse, batch 1, {load_tag}",
        "load_regime_verified": load_verified,
    }
    _atomic_write_text(Path(args.out), json.dumps(payload, indent=1, sort_keys=True))
    print(f"[rider] verdict: {verdict} -> {args.out}")
    if verdict != "PASS":
        raise SystemExit("R1-S3 FAILED: harvest quarantined pending diagnosis")


if __name__ == "__main__":  # pragma: no cover
    main()
