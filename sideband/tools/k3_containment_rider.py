#!/usr/bin/env python3
"""K-3 containment rider (stage-E clarification E10, 2026-09-02): the
empirical check that the live instruments are READ-ONLY.

Three in-process runs of the vanilla arm (fixed gamma=4, prefill active)
on the first 10 val prompts at rng seed 100:

  ON   — LiveShadowTap + LiveNormCatch + reader + byproduct recorder
  OFF  — identical execution pattern (K3Config with reader=None: the
         prefill runs, no hooks exist)
  OFF2 — OFF repeated (the kernel-determinism baseline)

Branch, pinned in E10 before this tool ran: if OFF vs OFF2 emitted ids
are bit-identical, the bar is BIT-IDENTITY of ON vs OFF (passive hooks
may not change one bit). Otherwise the bar is |mean acceptance
delta(ON, OFF)| <= max per-prompt |delta(OFF, OFF2)| + 0.005, with
first-divergence positions reported. Which branch armed is decided by
the OFF/OFF2 outcome and disclosed in the payload.

GPU box. Run (after tools/export_probe_weights.py):
    python tools/k3_containment_rider.py --load-4bit \
        --out results/real/k3_containment_rider.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from sideband.dists import spawn  # noqa: E402
from sideband.harvest import split_of_prompt  # noqa: E402
from sideband.scheduler import SchedulerPolicy  # noqa: E402

REAL = Path(__file__).resolve().parent.parent / "results" / "real"
RIDER_SEED = 100
N_PROMPTS = 10
ACC_DELTA_SLACK = 0.005  # E10, pinned


def first_divergence(a: list[int], b: list[int]) -> int | None:
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            return i
    return None if len(a) == len(b) else min(len(a), len(b))


def main() -> None:  # pragma: no cover - GPU box entrypoint
    from sideband.real import require_real_deps

    torch, transformers = require_real_deps()
    from sideband.real.hf_specdec import (PINNED_DATE, _assert_gpu_resident,
                                          _atomic_write_text,
                                          spec_decode_prompt)
    from sideband.real.k3_live import (ByproductRecorder, K3Config,
                                       build_live_reader, load_probe_weights)

    ap = argparse.ArgumentParser()
    ap.add_argument("--target", default="meta-llama/Llama-3.1-8B-Instruct")
    ap.add_argument("--draft", default="meta-llama/Llama-3.2-1B-Instruct")
    ap.add_argument("--prompts", default="data/prompts.jsonl")
    ap.add_argument("--probe-weights", default=str(REAL / "k3_probe_weights.npz"))
    ap.add_argument("--buckets16", default=str(REAL / "buckets_k16.json"))
    ap.add_argument("--glue16", default=str(REAL / "glue_k16.json"))
    ap.add_argument("--buckets32", default=str(REAL / "buckets_k32.json"))
    ap.add_argument("--buckets64", default=str(REAL / "buckets_k64.json"))
    ap.add_argument("--buckets512", default=str(REAL / "buckets_k512.json"))
    ap.add_argument("--max-new", type=int, default=256)
    ap.add_argument("--load-4bit", action="store_true")
    ap.add_argument("--allow-cpu-offload", action="store_true")
    ap.add_argument("--skip-preflight", action="store_true")
    ap.add_argument("--out", default=str(REAL / "k3_containment_rider.json"))
    args = ap.parse_args()

    from sideband.real._preflight import preflight

    preflight_report = preflight(disk_path=Path(args.out).resolve().anchor or ".",
                                 force=args.skip_preflight)

    tok = transformers.AutoTokenizer.from_pretrained(args.target)
    target_kwargs: dict = {"device_map": "auto", "torch_dtype": torch.bfloat16}
    if args.load_4bit:
        target_kwargs["quantization_config"] = transformers.BitsAndBytesConfig(
            load_in_4bit=True, bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=torch.bfloat16)
    target = transformers.AutoModelForCausalLM.from_pretrained(
        args.target, **target_kwargs).eval()
    draft = transformers.AutoModelForCausalLM.from_pretrained(
        args.draft, torch_dtype=torch.bfloat16, device_map="auto").eval()
    _assert_gpu_resident(target, "target", args.allow_cpu_offload)
    _assert_gpu_resident(draft, "draft", args.allow_cpu_offload)

    lines = [json.loads(l)["prompt"]
             for l in Path(args.prompts).read_text().splitlines() if l.strip()]
    prompts = [p for i, p in enumerate(lines)
               if split_of_prompt(i) == "val"][:N_PROMPTS]
    use_chat = tok.chat_template is not None

    def encode_prompt(p: str):
        if use_chat:
            return tok.apply_chat_template(
                [{"role": "user", "content": p}], add_generation_prompt=True,
                return_tensors="pt", date_string=PINNED_DATE)
        return tok(p, return_tensors="pt").input_ids

    probes, pmeta = load_probe_weights(args.probe_weights)

    def run(config_name: str) -> list[dict]:
        # Reader/hook lifetime is per run: OFF configurations must have NO
        # hooks registered at all, so the reader is built and closed here.
        reader = None
        if config_name == "on":
            reader = build_live_reader(
                target, pmeta, probes,
                bucket_paths={"16": args.buckets16, "32": args.buckets32,
                              "64": args.buckets64, "512": args.buckets512},
                glue16_path=args.glue16, load_4bit=args.load_4bit,
                expect_target=args.target)
        policy = SchedulerPolicy("fixed", gamma_base=4, gamma_max=4)
        gens = spawn(RIDER_SEED, len(prompts))
        out = []
        try:
            for i, prompt in enumerate(prompts):
                ids = encode_prompt(prompt)
                recorder = ByproductRecorder(6) if reader is not None else None
                cfg = K3Config(policy=policy, reader=reader, recorder=recorder)
                out_ids, _rec, stats = spec_decode_prompt(
                    target, draft, ids, 4, args.max_new, 1.0, gens[i],
                    bucket_of_token=None, prompt_idx=i, use_kv_cache=True,
                    k3=cfg)
                out.append({"emitted": out_ids[0, ids.shape[1]:].tolist(),
                            "acceptance_rate": stats["acceptance_rate"],
                            "n_blocks": stats["n_blocks"]})
                print(f"[{config_name}] [{i + 1}/{len(prompts)}] "
                      f"acc={stats['acceptance_rate']:.4f}", flush=True)
        finally:
            if reader is not None:
                reader.close()
        return out

    t0 = time.time()
    res_on = run("on")
    res_off = run("off")
    res_off2 = run("off2")

    off_off2_identical = all(a["emitted"] == b["emitted"]
                             for a, b in zip(res_off, res_off2))
    on_off_identical = all(a["emitted"] == b["emitted"]
                           for a, b in zip(res_on, res_off))
    div_on_off = [first_divergence(a["emitted"], b["emitted"])
                  for a, b in zip(res_on, res_off)]
    div_off_off2 = [first_divergence(a["emitted"], b["emitted"])
                    for a, b in zip(res_off, res_off2)]

    if off_off2_identical:
        branch = "bit-identity"
        ok = on_off_identical
        detail = {"on_off_identical": on_off_identical,
                  "first_divergence_on_off": div_on_off}
    else:
        branch = "noise-matched"
        base_band = max(abs(a["acceptance_rate"] - b["acceptance_rate"])
                        for a, b in zip(res_off, res_off2))
        mean_delta = float(np.mean([a["acceptance_rate"] - b["acceptance_rate"]
                                    for a, b in zip(res_on, res_off)]))
        ok = abs(mean_delta) <= base_band + ACC_DELTA_SLACK
        detail = {"mean_acceptance_delta_on_off": mean_delta,
                  "max_abs_per_prompt_delta_off_off2": base_band,
                  "slack": ACC_DELTA_SLACK,
                  "first_divergence_on_off": div_on_off,
                  "first_divergence_off_off2": div_off_off2}

    verdict = "PASS" if ok else "FAIL"
    payload = {
        "purpose": "K-3 containment rider (E10): live instruments are read-only",
        "branch_armed": branch,
        "branch_rule": ("OFF/OFF2 bit-identical -> ON/OFF must be bit-identical; "
                        "else |mean acc delta(ON,OFF)| <= max |delta(OFF,OFF2)| "
                        "+ 0.005 (both branches pinned 2026-09-02 pre-run)"),
        "off_off2_identical": off_off2_identical,
        "detail": detail,
        "n_prompts": len(prompts),
        "rng_seed": RIDER_SEED,
        "per_prompt": [{"acc_on": a["acceptance_rate"],
                        "acc_off": b["acceptance_rate"],
                        "acc_off2": c["acceptance_rate"],
                        "len_on": len(a["emitted"]),
                        "len_off": len(b["emitted"])}
                       for a, b, c in zip(res_on, res_off, res_off2)],
        "probe_weights_sha256": pmeta["npz_sha256"],
        "target_load": "nf4-double-quant-bf16compute" if args.load_4bit else "bf16",
        "preflight": preflight_report,
        "verdict": verdict,
        "runtime_s": round(time.time() - t0, 1),
    }
    _atomic_write_text(Path(args.out), json.dumps(payload, indent=1, sort_keys=True))
    print(f"[containment] branch={branch} verdict={verdict} -> {args.out}")
    if verdict != "PASS":
        raise SystemExit("K-3 containment rider FAILED: the live instrument "
                         "is not read-only — stage E fails closed")


if __name__ == "__main__":  # pragma: no cover
    main()
