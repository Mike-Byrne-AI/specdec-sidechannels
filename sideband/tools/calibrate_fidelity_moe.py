#!/usr/bin/env python3
"""R1-S3 tolerance calibration (BLUEPRINT S3 registration, 2026-08-31):
S1's NF4 kernel-noise tolerances do NOT transfer across models or telemetry
types, so the S3 rider's tolerances are pinned by dated amendment FROM this
evidence BEFORE the rider runs on the real harvest — the S1 recalibration
protocol (tools/calibrate_fidelity.py), run prospectively:

- generate FRESH continuations (seed 100 — no overlap with dataset seeds
  0..7; these anchors are not audit data) with the exact harvest code
  (moe_telemetry's RouterTap + shadow_telemetry.harvest_batch, batch 10,
  the registered load regime);
- for sampled anchors, teacher-force a batch-1 full forward (the rider's
  regime) and record ALIGNED metrics (stored anchor a vs recomputed a) and
  MISALIGNED negative controls (stored anchor a vs recomputed a-1) — the
  separation between the two distributions is what justifies the pinned
  tolerances. S3 metrics: per-layer expert-set overlap (of top_k), mass512
  L-inf on the OLMoE space, entropy |delta|.

Output: results/real/fidelity_calibration_olmoe.json (committed evidence).

Run: python tools/calibrate_fidelity_moe.py --load-4bit --bf16-routers
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

CAL_SEED = 100
N_PROMPTS = 10
MAX_NEW = 64
N_ANCHORS = 30


def main() -> None:
    from sideband.real import require_real_deps

    torch, transformers = require_real_deps()
    from sideband.real.hf_specdec import (PINNED_DATE, _assert_gpu_resident,
                                          _atomic_write_text, load_buckets)
    from sideband.real.moe_telemetry import (RouterTap, load_quantized_moe,
                                             verify_load_regime)
    from sideband.real.shadow_telemetry import (NormCatch, harvest_batch,
                                                row_generator_seeds)

    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="allenai/OLMoE-1B-7B-0125-Instruct")
    ap.add_argument("--gate-regex", default=r"mlp\.gate$")
    ap.add_argument("--prompts", default="data/prompts.jsonl")
    ap.add_argument("--buckets512", default="results/real/buckets_olmoe_k512.json")
    ap.add_argument("--load-4bit", action="store_true")
    ap.add_argument("--bf16-routers", action="store_true")
    ap.add_argument("--allow-cpu-offload", action="store_true")
    ap.add_argument("--out", default="results/real/fidelity_calibration_olmoe.json")
    args = ap.parse_args()

    tok = transformers.AutoTokenizer.from_pretrained(args.model)
    if tok.pad_token_id is None:
        tok.pad_token = tok.eos_token
    tok.padding_side = "left"
    model, load_tag = load_quantized_moe(transformers, torch, args.model,
                                         args.load_4bit, args.bf16_routers)
    load_verified = verify_load_regime(model, args.load_4bit, args.bf16_routers,
                                       gate_regex=args.gate_regex)
    _assert_gpu_resident(model, "model", args.allow_cpu_offload)
    dev = model.device
    vocab = int(model.config.vocab_size)
    top_k = int(model.config.num_experts_per_tok)
    b512 = load_buckets(args.buckets512, vocab, expect_model=args.model)
    b512_t = torch.from_numpy(b512).to(dev)
    n512 = int(b512.max()) + 1

    prompts = [json.loads(l)["prompt"] for l in Path(args.prompts).read_text().splitlines()
               if l.strip()][:N_PROMPTS]
    use_chat = tok.chat_template is not None
    if use_chat:
        texts = [tok.apply_chat_template([{"role": "user", "content": p}],
                                         add_generation_prompt=True, tokenize=False,
                                         date_string=PINNED_DATE) for p in prompts]
        enc = tok(texts, return_tensors="pt", padding=True, add_special_tokens=False).to(dev)
        encs_single = [tok(t, return_tensors="pt", add_special_tokens=False) for t in texts]
    else:
        enc = tok(prompts, return_tensors="pt", padding=True).to(dev)
        encs_single = [tok(p, return_tensors="pt") for p in prompts]

    eos = model.config.eos_token_id
    eos_set = set(eos) if isinstance(eos, (list, tuple)) else {eos}

    import inspect

    fkw = {"logits_to_keep": 1} if "logits_to_keep" in inspect.signature(model.forward).parameters else {}
    tap = RouterTap(model, args.gate_regex, top_k)
    nc = NormCatch(model.model.norm)

    t0 = time.time()
    # Fresh non-audit generations under the EXACT harvest regime.
    res = harvest_batch(model, tap, nc, enc["input_ids"], enc["attention_mask"],
                        row_generator_seeds(CAL_SEED, len(prompts)), eos_set, MAX_NEW,
                        1.0, {"512": b512_t}, top_m=32, forward_kwargs=fkw)
    nc.close()
    lengths = res["lengths"]
    print(f"[cal] fresh gen: {int(lengths.sum())} anchors {time.time() - t0:.0f}s", flush=True)

    rng = np.random.default_rng(0)
    pop = [(r, a) for r in range(len(prompts)) for a in range(1, int(lengths[r]))]
    picks = [pop[i] for i in rng.choice(len(pop), size=min(N_ANCHORS, len(pop)), replace=False)]

    def recompute(r: int, a: int):
        """Rider-regime batch-1 full forward at anchor a of row r."""
        prefix = encs_single[r]["input_ids"][0].tolist() + res["tokens"][r, :a].astype(int).tolist()
        with torch.no_grad():
            out = model(input_ids=torch.tensor([prefix], device=dev))
        experts_rec = tap.collect(1)[0]  # (L, top_k)
        p = torch.softmax(out.logits[0, -1].float(), dim=-1)
        mass = torch.zeros(n512, device=dev).scatter_add_(0, b512_t, p).cpu().numpy()
        ent = float(-torch.special.xlogy(p, p).sum())
        return experts_rec, mass, ent

    def compare(stored_r: int, stored_a: int, experts_rec, mass_rec, ent_rec) -> dict:
        overlaps = []
        st = res["slots"][stored_r, stored_a]  # (L, top_k) expert ids
        for li in range(st.shape[0]):
            s1 = set(st[li][st[li] >= 0].tolist())
            s2 = set(experts_rec[li][experts_rec[li] >= 0].tolist())
            overlaps.append(len(s1 & s2))
        return {
            "min_overlap": int(min(overlaps)),
            "mass_linf": float(np.abs(res["mass512"][stored_r, stored_a].astype(np.float32)
                                      - mass_rec).max()),
            "ent_abs": abs(float(res["entropy"][stored_r, stored_a]) - ent_rec),
        }

    aligned, misaligned = [], []
    with torch.no_grad():
        for r, a in picks:
            sr, mr, er = recompute(r, a)
            aligned.append(compare(r, a, sr, mr, er))
            # negative control: stored anchor a vs recomputed a-1
            sr2, mr2, er2 = recompute(r, a - 1)
            misaligned.append(compare(r, a, sr2, mr2, er2))
    tap.close()

    def dist(vals):
        v = np.array(vals, dtype=np.float64)
        return {"min": float(v.min()), "p50": float(np.percentile(v, 50)),
                "p90": float(np.percentile(v, 90)), "p99": float(np.percentile(v, 99)),
                "max": float(v.max())}

    payload = {
        "purpose": ("R1-S3 tolerance calibration evidence (S3 registration 2026-08-31; "
                    "non-audit anchors; tolerances pinned by dated amendment from this "
                    "file BEFORE the rider runs)"),
        "regime": {"generation": f"harvest_batch batch-{N_PROMPTS} {load_tag} KV-cached "
                                 "(exact harvest code, RouterTap)",
                   "recompute": "batch-1 full forward, no KV reuse (exact rider regime)",
                   "model": args.model, "top_k": top_k,
                   "load_regime_verified": load_verified,
                   "cal_seed": CAL_SEED, "n_prompts": N_PROMPTS, "max_new": MAX_NEW,
                   "n_anchors_compared": len(picks),
                   "non_audit_note": "seed 100 continuations; dataset seeds are 0..7"},
        "overlap_denominator": top_k,
        "aligned": {
            "min_overlap": dist([x["min_overlap"] for x in aligned]),
            "mass_linf": dist([x["mass_linf"] for x in aligned]),
            "ent_abs": dist([x["ent_abs"] for x in aligned]),
        },
        "misaligned_control": {
            "min_overlap": dist([x["min_overlap"] for x in misaligned]),
            "mass_linf": dist([x["mass_linf"] for x in misaligned]),
            "ent_abs": dist([x["ent_abs"] for x in misaligned]),
        },
        "raw": {"aligned": aligned, "misaligned": misaligned},
        "runtime_s": round(time.time() - t0, 1),
    }
    _atomic_write_text(Path(args.out), json.dumps(payload, indent=1, sort_keys=True))
    print(json.dumps({k: payload[k] for k in ("aligned", "misaligned_control")}, indent=2))


if __name__ == "__main__":
    main()
