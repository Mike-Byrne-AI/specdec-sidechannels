"""K-3 live-tap fidelity rider (stage-E clarification E9, 2026-09-02).

Validates the LIVE capture path (LiveShadowTap/LiveNormCatch reading the
block anchor inside multi-token verify forwards, mid spec-decode) against
the harvest-style reference: a fresh batch-1 teacher-forced full forward
over the exact token prefix the anchor row conditions on (prompt +
emitted tokens through the anchor position; proposal coupling guarantees
no rejected content in that prefix). Metrics verbatim from R1: per-layer
slot-set overlap, mass512 L-inf (stored f16 vs recomputed f32), entropy
|delta|, argmax-with-gap; h_a L-inf is REPORTED, non-gating.

Two modes on the SAME machinery (shared-run design, disclosed in E9):

--mode calibrate: 30 aligned + 30 off-by-one misaligned comparisons on
  the calibration live run (arm 1, rng seed 100, val prompts) ->
  calibration evidence json. The tolerance MAPPING is already pinned
  (E9): MASS_LINF_MAX and ENTROPY_ABS_MAX = 3.0x calibrated aligned max;
  SLOT_OVERLAP_MIN = ceil((aligned min-overlap minimum + misaligned
  max-overlap maximum) / 2); ARGMAX_GAP = MASS_LINF_MAX.

--mode rider: >= 16 sampled (prompt, block) anchors of the same run,
  >= 4 from REJECTION-TERMINATED blocks (topped up from that
  subpopulation if the draw falls short — the registered must-include);
  judged against the constants below. Refuses to run until the dated
  tolerance amendment pins them (S3 pattern; the guard re-arms if
  anyone reverts them to None). A FAIL quarantines the live instrument
  under the S3 cycle bound (no widening absent a named mechanism +
  critic review). Rider rng lineage starts 0, +1 per rerun.

GPU box. Run (after the calibration run of tools/run_k3_arms.py):
    python -m sideband.real.k3_tap_rider --mode calibrate --load-4bit \
        --run results/real/k3_tapcal_arm1.jsonl \
        --out results/real/k3_tap_calibration.json
    python -m sideband.real.k3_tap_rider --mode rider --load-4bit \
        --run results/real/k3_tapcal_arm1.jsonl \
        --out results/real/k3_tap_rider.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import numpy as np

from . import require_real_deps

# Pinned by the STAGE-E TOLERANCE AMENDMENT (BLUEPRINT, 2026-09-02;
# evidence results/real/k3_tap_calibration.json, 30 aligned + 30
# off-by-one anchors, 15/30 rejection-terminated) under the E9 mapping
# registered BEFORE the calibration ran. Calibrated bands: ALIGNED
# per-anchor min-overlap 27..32/32, mass512 L-inf <= 0.03698, entropy
# <= 0.13030; MISALIGNED overlap <= 13, mass >= 0.21398, entropy min
# 0.0063 (entropy does NOT separate at the minimum — adjacent
# positions can share near-identical distributions, the S1 caveat —
# so the AND-structure is load-bearing and OVERLAP is the sharp
# discriminator). Exact 3.0x products, not rounded (the mapping
# licenses no rounding; S1/S3 rounded — disclosed difference).
# CYCLE BOUND armed: a FAIL quarantines with no further widening
# absent a named mechanism + critic review; rerun rng-seeds +1.
# The refuse-until-pinned guard below re-arms if these revert to None.
SLOT_OVERLAP_MIN: int | None = 20     # ceil((27 + 13) / 2), E9 mapping
MASS_LINF_MAX: float | None = 0.11094206571578979   # 3.0 x aligned max
ENTROPY_ABS_MAX: float | None = 0.3908865451812744  # 3.0 x aligned max
ARGMAX_GAP: float | None = 0.11094206571578979      # = MASS_LINF_MAX

N_TRIPLES = 16
MIN_REJECTION_TERMINATED = 4
N_CAL = 30
CAL_RUN_SEED = 100  # the registered calibration live-run rng seed (E9)


def load_run(run_base: str):
    """Load a completed run_k3_arms run with its bindings enforced:
    byproduct npz shas must equal the summary's, the summary must exist
    (completion marker), and the run must be the registered calibration
    configuration (arm 1, seed 100, instruments on)."""
    base = Path(run_base)
    meta = json.loads(base.with_suffix(".meta.json").read_text())
    summary_path = base.with_suffix(".summary.json")
    if not summary_path.exists():
        raise SystemExit(f"{summary_path} missing — the run did not complete")
    summary = json.loads(summary_path.read_text())
    if int(meta["arm"]) != 1 or int(meta["seed"]) != CAL_RUN_SEED:
        raise SystemExit(f"rider runs on the registered calibration run "
                         f"(arm 1, seed {CAL_RUN_SEED}); got arm "
                         f"{meta['arm']} seed {meta['seed']}")
    if not meta.get("instruments", False):
        raise SystemExit("run has no instruments — nothing to validate")
    if float(meta.get("temperature", 1.0)) != 1.0:
        # E12(ii): the recompute softmax carries no /t (S1-lineage
        # convention) — valid only at temperature 1.0.
        raise SystemExit(f"run temperature {meta['temperature']} != 1.0 — the "
                         "rider's recompute convention does not apply")
    byp_dir = Path(str(base) + ".byproduct")
    rows = {}
    for name, want in summary["byproduct_sha256"].items():
        p = byp_dir / name
        got = hashlib.sha256(p.read_bytes()).hexdigest()
        if got != want:
            raise SystemExit(f"{p} sha mismatch vs summary — refusing unbound byproduct")
        rows[int(name[1:-4])] = np.load(p)
    gens = {}
    for line in base.with_suffix(".gen.jsonl").read_text().splitlines():
        d = json.loads(line)
        gens[int(d["prompt_idx"])] = d
    return meta, summary, rows, gens


def anchor_population(rows: dict) -> list[tuple[int, int, bool]]:
    """(prompt_idx, block_row, rejection_terminated) for every recorded
    block. Row b's anchor was produced by block b-1 (row 0 = the prefill
    anchor); it is rejection-terminated iff block b-1 rejected mid-block."""
    pop = []
    for pidx, z in sorted(rows.items()):
        n = int(z["n_blocks"])
        acc = z["accepted"] if n else None
        gu = z["gamma_used"] if n else None
        for b in range(n):
            rej = bool(b >= 1 and int(acc[b - 1]) < int(gu[b - 1]))
            pop.append((pidx, b, rej))
    return pop


def main() -> None:  # pragma: no cover - GPU box entrypoint
    torch, transformers = require_real_deps()
    from .hf_specdec import (PINNED_DATE, _assert_gpu_resident,
                             _atomic_write_text, load_buckets)
    from .k3_live import LiveNormCatch, LiveShadowTap, load_probe_weights

    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", required=True, choices=["calibrate", "rider"])
    ap.add_argument("--run", required=True,
                    help="base path of the completed calibration run "
                         "(tools/run_k3_arms.py --arm 1 --seed 100 --select-split val)")
    ap.add_argument("--prompts", default="data/prompts.jsonl")
    ap.add_argument("--probe-weights", default="results/real/k3_probe_weights.npz")
    ap.add_argument("--buckets512", default="results/real/buckets_k512.json")
    ap.add_argument("--rng-seed", type=int, default=0,
                    help="rider sampling lineage (starts 0, +1 per rerun); "
                         "calibrate mode always samples with seed 0")
    ap.add_argument("--load-4bit", action="store_true")
    ap.add_argument("--allow-cpu-offload", action="store_true")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    if args.mode == "rider" and None in (SLOT_OVERLAP_MIN, MASS_LINF_MAX,
                                         ENTROPY_ABS_MAX, ARGMAX_GAP):
        raise SystemExit(
            "K-3 live-tap tolerances are not pinned yet: run --mode calibrate, "
            "land the dated tolerance amendment (BLUEPRINT stage-E block, "
            "critic-reviewed, E9 mapping), set the constants in k3_tap_rider.py "
            "— in that order.")

    meta, summary, rows, gens = load_run(args.run)
    if hashlib.sha256(Path(args.prompts).read_bytes()).hexdigest() != meta["prompts_sha256"]:
        raise SystemExit("prompts file sha does not match the run meta")
    probes, pmeta = load_probe_weights(args.probe_weights)
    if meta.get("probe_weights_sha256") != pmeta["npz_sha256"]:
        raise SystemExit("--probe-weights is not the file the run used")
    tap_meta = pmeta["tap"]
    want_load = "nf4-double-quant-bf16compute" if args.load_4bit else "bf16"
    if meta["target_load"] != want_load:
        raise SystemExit(f"load regime {want_load} != run meta {meta['target_load']}")
    expect512 = pmeta["buckets_sha256"].get("buckets512")
    if expect512 and hashlib.sha256(Path(args.buckets512).read_bytes()).hexdigest() != expect512:
        raise SystemExit("--buckets512 sha != the harvest-bound sha — the mass "
                         "comparison needs the exact logged space")

    tok = transformers.AutoTokenizer.from_pretrained(meta["target"])
    kwargs: dict = {"device_map": "auto", "torch_dtype": torch.bfloat16}
    if args.load_4bit:
        kwargs["quantization_config"] = transformers.BitsAndBytesConfig(
            load_in_4bit=True, bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=torch.bfloat16)
    model = transformers.AutoModelForCausalLM.from_pretrained(
        meta["target"], **kwargs).eval()
    _assert_gpu_resident(model, "target", args.allow_cpu_offload)
    dev = model.device
    vocab = int(model.config.vocab_size)
    b512 = load_buckets(args.buckets512, vocab, expect_model=meta["target"])
    b512_t = torch.from_numpy(b512).to(dev)
    n512 = int(b512.max()) + 1

    tap = LiveShadowTap(model, tap_meta["layer_regex"],
                        {int(x) for x in tap_meta["layers"].split(",")},
                        int(tap_meta["n_slots"]), int(tap_meta["top_n"]),
                        seed=int(tap_meta["sketch_seed"]))
    if tap.layer_names != list(tap_meta["layer_names"]):
        raise SystemExit("rider tap layers do not reproduce the export meta")
    nc = LiveNormCatch(model.model.norm)

    prompts = [json.loads(l)["prompt"]
               for l in Path(args.prompts).read_text().splitlines() if l.strip()]
    use_chat = meta["chat_template_used"] and tok.chat_template is not None
    if use_chat != meta["chat_template_used"]:
        raise SystemExit("chat-template availability differs from the run regime")

    def full_ids(pidx: int) -> list[int]:
        orig = meta["selected_original_indices"][pidx]
        if use_chat:
            text = tok.apply_chat_template(
                [{"role": "user", "content": prompts[orig]}],
                add_generation_prompt=True, tokenize=False,
                date_string=PINNED_DATE)
            enc = tok(text, return_tensors="pt", add_special_tokens=False)
        else:
            enc = tok(prompts[orig], return_tensors="pt")
        ids = enc["input_ids"][0].tolist()
        if len(ids) != int(gens[pidx]["prompt_len"]):
            raise SystemExit(f"prompt {pidx}: re-encoded length {len(ids)} != "
                             f"recorded {gens[pidx]['prompt_len']} — encoding drift")
        return ids + [int(t) for t in gens[pidx]["generated_ids"]]

    def recompute(prefix: list[int]):
        with torch.no_grad():
            out = model(input_ids=torch.tensor([prefix], device=dev))
        pos = len(prefix) - 1
        slots_rec = tap.collect_at(pos)
        h_rec = nc.collect_at(pos)
        p = torch.softmax(out.logits[0, -1].float(), dim=-1)
        mass = torch.zeros(n512, device=dev).scatter_add_(0, b512_t, p).cpu().numpy()
        ent = float(-torch.special.xlogy(p, p).sum())
        top2 = torch.topk(p, 2).values
        return slots_rec, h_rec, mass, ent, int(p.argmax()), float(top2[0] - top2[1])

    def compare(z, b: int, slots_rec, h_rec, mass_rec, ent_rec, am_rec, gap):
        stored_slots = z["slots"][b]
        overlaps = []
        for li in range(stored_slots.shape[0]):
            s_st = set(stored_slots[li][stored_slots[li] >= 0].tolist())
            s_re = set(slots_rec[li][slots_rec[li] >= 0].tolist())
            overlaps.append(len(s_st & s_re))
        return {
            "slot_overlaps": overlaps,
            "min_overlap": int(min(overlaps)),
            "mass512_linf": float(np.abs(z["mass512"][b].astype(np.float32)
                                         - mass_rec).max()),
            "entropy_abs": abs(float(z["entropy"][b]) - ent_rec),
            "argmax_equal": bool(int(z["argmax"][b]) == am_rec),
            "argmax_gap": gap,
            "h_linf": float(np.abs(z["h"][b].astype(np.float32)
                                   - h_rec.astype(np.float32)).max()),
        }

    pop = anchor_population(rows)
    rej_pop = [t for t in pop if t[2]]
    if args.mode == "rider" and len(rej_pop) < MIN_REJECTION_TERMINATED:
        raise SystemExit(f"only {len(rej_pop)} rejection-terminated anchors in "
                         "the run — cannot satisfy the registered must-include")

    t0 = time.time()
    payload: dict
    if args.mode == "calibrate":
        rng = np.random.default_rng(0)
        picks = [pop[i] for i in rng.choice(len(pop), size=min(N_CAL, len(pop)),
                                            replace=False)]
        aligned, misaligned = [], []
        for pidx, b, rej in picks:
            ids = full_ids(pidx)
            apos = int(rows[pidx]["anchor_pos"][b])
            res = compare(rows[pidx], b, *recompute(ids[: apos + 1]))
            res.update({"prompt_idx": pidx, "block": b, "rejection_terminated": rej})
            aligned.append(res)
            mis = compare(rows[pidx], b, *recompute(ids[: apos]))
            mis.update({"prompt_idx": pidx, "block": b})
            misaligned.append(mis)
            print(f"[cal] p{pidx} b{b}: overlap>={res['min_overlap']} "
                  f"linf={res['mass512_linf']:.2e} (mis {mis['min_overlap']})",
                  flush=True)

        def dist(vals):
            v = np.array(vals, dtype=np.float64)
            return {"min": float(v.min()), "p50": float(np.percentile(v, 50)),
                    "p90": float(np.percentile(v, 90)), "max": float(v.max())}

        payload = {
            "purpose": ("K-3 live-tap tolerance calibration (E9; mapping "
                        "registered 2026-09-02 BEFORE this data existed: "
                        "mass/entropy = 3.0x aligned max; overlap = "
                        "ceil((aligned min + misaligned max)/2); argmax gap "
                        "= mass tolerance)"),
            "run": str(args.run),
            "regime": {"live": "verify-forward capture mid spec-decode "
                               "(LiveShadowTap all-position)",
                       "recompute": "batch-1 teacher-forced full forward, "
                                    "no KV reuse (harvest-style last-position)",
                       "model": meta["target"], "target_load": meta["target_load"],
                       "n_compared": len(picks),
                       "n_rejection_terminated_in_sample":
                           sum(1 for _, _, r in picks if r)},
            "aligned": {k: dist([x[k] for x in aligned])
                        for k in ("min_overlap", "mass512_linf", "entropy_abs",
                                  "h_linf")},
            "misaligned_control": {k: dist([x[k] for x in misaligned])
                                   for k in ("min_overlap", "mass512_linf",
                                             "entropy_abs")},
            "raw": {"aligned": aligned, "misaligned": misaligned},
            "byproduct_sha256_validated": summary["byproduct_sha256"],
            "runtime_s": round(time.time() - t0, 1),
        }
    else:
        rng = np.random.default_rng(args.rng_seed)
        picks = [pop[i] for i in rng.choice(len(pop), size=min(N_TRIPLES, len(pop)),
                                            replace=False)]
        n_rej = sum(1 for t in picks if t[2])
        topped_up = 0
        while n_rej < MIN_REJECTION_TERMINATED:
            cand = rej_pop[int(rng.integers(len(rej_pop)))]
            if cand not in picks:
                # replace the first non-rejection pick (registered top-up)
                for k, t in enumerate(picks):
                    if not t[2]:
                        picks[k] = cand
                        topped_up += 1
                        break
            n_rej = sum(1 for t in picks if t[2])
        results = []
        for pidx, b, rej in picks:
            ids = full_ids(pidx)
            apos = int(rows[pidx]["anchor_pos"][b])
            r = compare(rows[pidx], b, *recompute(ids[: apos + 1]))
            argmax_ok = (r["argmax_gap"] <= ARGMAX_GAP) or r["argmax_equal"]
            ok = (r["min_overlap"] >= SLOT_OVERLAP_MIN
                  and r["mass512_linf"] <= MASS_LINF_MAX
                  and r["entropy_abs"] <= ENTROPY_ABS_MAX and argmax_ok)
            r.update({"prompt_idx": pidx, "block": b,
                      "rejection_terminated": rej,
                      "argmax_checked": r["argmax_gap"] > ARGMAX_GAP,
                      "argmax_ok": bool(argmax_ok), "pass": bool(ok)})
            results.append(r)
            print(f"[rider] p{pidx} b{b}{' REJ' if rej else ''}: "
                  f"overlap>={r['min_overlap']} linf={r['mass512_linf']:.2e} "
                  f"{'PASS' if ok else 'FAIL'}", flush=True)
        # Shared-run disclosure (E12(iv)): recompute the calibration draw
        # deterministically and record how many anchors both samples share.
        cal_rng = np.random.default_rng(0)
        cal_picks = {tuple(pop[i][:2]) for i in
                     cal_rng.choice(len(pop), size=min(N_CAL, len(pop)),
                                    replace=False)}
        n_shared = sum(1 for t in picks if (t[0], t[1]) in cal_picks)
        verdict = "PASS" if all(r["pass"] for r in results) else "FAIL"
        payload = {
            "criteria": {"slot_overlap_min": SLOT_OVERLAP_MIN,
                         "mass_linf_max": MASS_LINF_MAX,
                         "entropy_abs_max": ENTROPY_ABS_MAX,
                         "argmax_gap": ARGMAX_GAP,
                         "n_triples": N_TRIPLES,
                         "min_rejection_terminated": MIN_REJECTION_TERMINATED},
            "run": str(args.run),
            "rng_seed": args.rng_seed,
            "n_anchors_shared_with_calibration_sample": n_shared,
            "topped_up_rejection_terminated": topped_up,
            "n_rejection_terminated": sum(1 for r in results
                                          if r["rejection_terminated"]),
            "h_linf_reported_nongating": [r["h_linf"] for r in results],
            "triples": results,
            "verdict": verdict,
            "byproduct_sha256_validated": summary["byproduct_sha256"],
            "runtime_s": round(time.time() - t0, 1),
        }
    tap.close()
    nc.close()
    _atomic_write_text(Path(args.out), json.dumps(payload, indent=1, sort_keys=True))
    if args.mode == "rider":
        print(f"[rider] verdict: {payload['verdict']} -> {args.out}")
        if payload["verdict"] != "PASS":
            raise SystemExit("K-3 live-tap rider FAILED: live instrument "
                             "quarantined pending diagnosis")
    else:
        print(json.dumps({k: payload[k] for k in ("aligned", "misaligned_control")},
                         indent=2))


if __name__ == "__main__":  # pragma: no cover
    main()
