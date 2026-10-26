"""Phase-2/3 S3 harvester: MoE router address-stream telemetry (OLMoE).

GPU box. Per DECISIONS D-1: expert routing is the architecture-native
input-dependent ADDRESS stream — which experts each token fetches per layer
IS what a weight-serving device observes, zero simulation. This is the S3
run of the registered Phase-2/3 protocol (docs/BLUEPRINT.md, S3 block dated
2026-08-31); the v0.2.0 jsonl prototype this file used to hold is retired by
that registration.

Design, per the registration:
- Hooks on the router gates (default regex ``mlp\\.gate$``; on OLMoE these
  are model.layers.{0..15}.mlp.gate, nn.Linear 2048->64). Telemetry per
  anchor per layer = the model's OWN selected top-k expert ids, reproduced
  as the block computes them (topk over float32 softmax of the same logits
  tensor the hook observes; modeling_olmoe.OlmoeSparseMoeBlock.forward).
  Tie handling across tensor shapes is not guaranteed identical to the
  block's internal call — measure-zero for real logits and covered by the
  R1-S3 calibration band. Ids are stored SORTED ascending (set semantics:
  an address observer sees which experts are fetched, not rank). Router
  softmax weights are NOT stored (addresses only).
- Storage reuses the npz key "slots" with shape (rows, T, n_layers, top_k)
  int16 so the entire committed Phase-3 instrument (HarvestData, multi-hot,
  grid runner, riders, state files) runs verbatim with n_slots = n_experts.
- Generation/alignment/free-info logging: shadow_telemetry.harvest_batch,
  the SAME committed code — block-start alignment, all four exact bucket
  masses, entropy, argmax, top-32 ids+probs, h_a = model.norm output.
- Load regime (registered deviation): NF4 double-quant bf16-compute with
  the router gates (and lm_head, the bnb default) excluded from
  quantization via --bf16-routers; recorded in the meta.

Usage (GPU box):
    python -m sideband.real.moe_telemetry \
        --model allenai/OLMoE-1B-7B-0125-Instruct --load-4bit --bf16-routers \
        --prompts data/prompts.jsonl --n-prompts 210 --max-new 256 \
        --seeds 0,1,2,3,4,5,6,7 \
        --out-dir results/real/harvest_moe
    (bucket spaces default to the four committed results/real/buckets_olmoe_k*.json)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from pathlib import Path

import numpy as np

from ..harvest import GAMMA_DEFAULT, total_pairs
from . import require_real_deps
from .shadow_telemetry import NormCatch, _pad_cat, harvest_batch, row_generator_seeds

# transformers' bnb skip matching (integrations/bitsandbytes.py) honors a
# LEAF module name or a dotted PREFIX — "mlp.gate" is neither for a leaf
# module and silently skips nothing (measured on-box: router got quantized).
# Leaf "gate" matches exactly the 16 routers (expert projections are leaf
# "gate_proj"). The explicit list REPLACES bnb's auto-skip (which covers
# lm_head), so lm_head must be re-listed here.
ROUTER_SKIP_MODULES = ["gate", "lm_head"]


class RouterTap:
    """Forward hooks on regex-matched router-gate Linears; captures the
    model's own top-k expert selection per (row, layer) at the LAST
    position of each forward (real for every row under LEFT padding).

    Interface-compatible with ShadowTap (layer_names / top_n / collect /
    close) so shadow_telemetry.harvest_batch drives it unchanged. collect()
    returns sorted-ascending expert ids, int16, (n_rows, n_layers, top_k);
    no -1 padding ever occurs (top_k distinct experts always fire)."""

    def __init__(self, model, gate_regex: str, top_k: int):
        import torch  # noqa: F401 - GPU-box dependency, asserted by caller

        self.top_n = int(top_k)  # ShadowTap-interface name
        self.latest: dict = {}
        self._handles = []
        pattern = re.compile(gate_regex)
        matched = [(n, m) for n, m in model.named_modules() if pattern.search(n)]
        if not matched:
            raise ValueError(f"no modules matched {gate_regex!r}")
        self.layer_names = [n for n, _ in matched]
        self.n_experts: dict[str, int] = {}
        for name, module in matched:
            n_exp = int(getattr(module, "out_features", 0) or module.weight.shape[0])
            if n_exp <= self.top_n:
                raise ValueError(f"{name}: {n_exp} experts <= top_k {self.top_n}")
            self.n_experts[name] = n_exp
            self._handles.append(module.register_forward_hook(self._make_hook(name)))

    def _make_hook(self, name: str):
        def hook(_module, _inputs, output):
            logits = output[0] if isinstance(output, tuple) else output
            self.latest[name] = logits.detach()

        return hook

    def collect(self, n_rows: int) -> np.ndarray:
        """(n_rows, n_layers, top_k) int16 sorted expert ids. Clears captured
        state; refuses if a tapped gate did not fire since the last collect()
        or if the captured row count is not a multiple of n_rows (the
        (B, T, H) -> (B*T, H) row-major flatten is the layout contract)."""
        import torch

        out = np.full((n_rows, len(self.layer_names), self.top_n), -1, dtype=np.int16)
        for li, name in enumerate(self.layer_names):
            if name not in self.latest:
                raise RuntimeError(f"tapped gate {name} did not fire since last collect()")
            logits = self.latest[name]
            n_exp = self.n_experts[name]
            if int(logits.shape[-1]) != n_exp:
                raise RuntimeError(f"{name}: gate output width {int(logits.shape[-1])} != {n_exp}")
            flat = logits.reshape(-1, n_exp)
            if flat.shape[0] % n_rows:
                raise RuntimeError(
                    f"{name}: captured {int(flat.shape[0])} positions, not a multiple of batch {n_rows}")
            last = flat.reshape(n_rows, -1, n_exp)[:, -1]  # (B, E): last position per row
            # The block's own selection op on the same tensor: topk over
            # float32 softmax (softmax is monotone, so ids == topk on logits
            # up to ties; we replicate the exact op anyway).
            top = torch.topk(torch.softmax(last.float(), dim=-1), k=self.top_n, dim=-1).indices
            out[:, li] = np.sort(top.cpu().numpy().astype(np.int16), axis=-1)
        self.latest = {}
        return out

    def close(self) -> None:
        for h in self._handles:
            h.remove()
        self._handles = []


def load_quantized_moe(transformers, torch, model_id: str, load_4bit: bool,
                       bf16_routers: bool):
    """Model load under the registered S3 regime; returns (model, load_tag)."""
    kwargs: dict = {"device_map": "auto", "torch_dtype": torch.bfloat16}
    tag = "bf16"
    if load_4bit:
        qk = dict(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                  bnb_4bit_use_double_quant=True,
                  bnb_4bit_compute_dtype=torch.bfloat16)
        tag = "nf4-double-quant-bf16compute"
        if bf16_routers:
            qk["llm_int8_skip_modules"] = list(ROUTER_SKIP_MODULES)
            tag += "+bf16-routers"
        kwargs["quantization_config"] = transformers.BitsAndBytesConfig(**qk)
    model = transformers.AutoModelForCausalLM.from_pretrained(model_id, **kwargs).eval()
    return model, tag


def verify_load_regime(model, load_4bit: bool, bf16_routers: bool,
                       gate_regex: str = r"mlp\.gate$") -> dict:
    """POST-LOAD verification of the registered load regime, by module
    INSPECTION rather than flag trust (critic blocker, 2026-08-31: the
    skip-list matching semantics silently quantized the routers under an
    earlier spelling, and the failure is self-consistent — the rider
    recomputes under the same wrong load and passes). Raises on any
    violation; the returned record is what the meta stores."""
    import re as _re

    def _quantized(m) -> bool:
        w = getattr(m, "weight", None)
        return w is not None and w.__class__.__name__ == "Params4bit"

    rec = {"load_4bit": bool(load_4bit), "bf16_routers": bool(bf16_routers)}
    if not load_4bit:
        rec["verified"] = "bf16 load; no quantization present"
        return rec
    lm = getattr(model, "lm_head", None)
    if lm is None or _quantized(lm):
        raise SystemExit("lm_head is quantized or missing — the registered load "
                         "regime keeps it unquantized (bnb skip)")
    rec["lm_head_weight_class"] = lm.weight.__class__.__name__
    if bf16_routers:
        pat = _re.compile(gate_regex)
        gates = [(n, m) for n, m in model.named_modules()
                 if pat.search(n) and getattr(m, "weight", None) is not None]
        if not gates:
            raise SystemExit(f"--bf16-routers: no modules match {gate_regex!r}")
        bad = [n for n, m in gates if _quantized(m)]
        if bad:
            raise SystemExit(
                f"--bf16-routers requested but {len(bad)}/{len(gates)} routers are "
                f"QUANTIZED (skip-list matching failed; first: {bad[0]}) — refusing")
        rec["gates_verified_unquantized"] = len(gates)
        rec["gate_weight_class"] = gates[0][1].weight.__class__.__name__
    return rec


def main() -> None:  # pragma: no cover - GPU box entrypoint
    torch, transformers = require_real_deps()
    from .hf_specdec import (PINNED_DATE, _assert_gpu_resident, _atomic_write_text,
                             load_buckets, redact_args)

    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="allenai/OLMoE-1B-7B-0125-Instruct")
    ap.add_argument("--gate-regex", default=r"mlp\.gate$")
    ap.add_argument("--prompts", required=True, help="jsonl with a 'prompt' field")
    ap.add_argument("--n-prompts", type=int, default=210)
    ap.add_argument("--max-new", type=int, default=256)
    ap.add_argument("--temperature", type=float, default=1.0)
    ap.add_argument("--top-m", type=int, default=32)
    ap.add_argument("--seeds", default="0,1,2,3,4,5,6,7")
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--buckets16", default="results/real/buckets_olmoe_k16.json")
    ap.add_argument("--buckets32", default="results/real/buckets_olmoe_k32.json")
    ap.add_argument("--buckets64", default="results/real/buckets_olmoe_k64.json")
    ap.add_argument("--buckets512", default="results/real/buckets_olmoe_k512.json")
    ap.add_argument("--load-4bit", action="store_true")
    ap.add_argument("--bf16-routers", action="store_true",
                    help="exclude router gates (+ lm_head) from 4-bit quantization "
                         "(the registered S3 regime)")
    ap.add_argument("--no-chat-template", action="store_true")
    ap.add_argument("--out-dir", default="results/real/harvest_moe")
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--skip-preflight", action="store_true")
    ap.add_argument("--allow-cpu-offload", action="store_true")
    args = ap.parse_args()

    from ._preflight import preflight

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    preflight_report = preflight(disk_path=out_dir.resolve().anchor or ".",
                                 force=args.skip_preflight)

    tok = transformers.AutoTokenizer.from_pretrained(args.model)
    use_chat = (not args.no_chat_template) and tok.chat_template is not None
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
    # The registered telemetry is the model's OWN selection width — not a knob.
    top_k = int(model.config.num_experts_per_tok)

    bucket_paths = {"16": args.buckets16, "32": args.buckets32,
                    "64": args.buckets64, "512": args.buckets512}
    bucket_spaces = {}
    for name, path in bucket_paths.items():
        arr = load_buckets(path, vocab, expect_model=args.model)
        if (arr < 0).any():
            raise SystemExit(f"buckets{name} does not cover the full vocab; mass logging requires full coverage")
        bucket_spaces[name] = torch.from_numpy(arr).to(dev)

    prompts = [json.loads(l)["prompt"] for l in Path(args.prompts).read_text().splitlines() if l.strip()]
    prompts = prompts[: args.n_prompts]

    def encode_batch(batch: list[str]):
        if use_chat:
            texts = [tok.apply_chat_template([{"role": "user", "content": p}],
                                             add_generation_prompt=True, tokenize=False,
                                             date_string=PINNED_DATE) for p in batch]
            return tok(texts, return_tensors="pt", padding=True, add_special_tokens=False)
        return tok(batch, return_tensors="pt", padding=True)

    eos = model.config.eos_token_id
    eos_set = set(eos) if isinstance(eos, (list, tuple)) else {eos}

    norm_module = getattr(getattr(model, "model", None), "norm", None)
    if norm_module is None:
        raise SystemExit("expected a *ForCausalLM exposing .model.norm")

    import inspect

    fkw = {"logits_to_keep": 1} if "logits_to_keep" in inspect.signature(model.forward).parameters else {}

    tap = RouterTap(model, args.gate_regex, top_k)
    normcatch = NormCatch(norm_module)
    n_experts = sorted(set(tap.n_experts.values()))
    if len(n_experts) != 1:
        raise SystemExit(f"tapped gates disagree on expert count: {n_experts}")
    print(f"[tap] {len(tap.layer_names)} gates x top-{top_k} of {n_experts[0]} experts: "
          f"{tap.layer_names[0]} .. {tap.layer_names[-1]}", flush=True)

    def _git(cmd):
        import subprocess

        r = subprocess.run(["git", *cmd], capture_output=True, text=True,
                           cwd=Path(__file__).resolve().parent, timeout=10)
        return r.stdout.strip() if r.returncode == 0 else None

    def _git_commit() -> str:
        try:
            dirty = "-dirty" if _git(["status", "--porcelain"]) else ""
            return (_git(["rev-parse", "HEAD"]) or "unknown") + dirty
        except Exception:
            return "unknown"

    def _sha(p: str) -> str:
        return hashlib.sha256(Path(p).read_bytes()).hexdigest()

    seeds = [int(s) for s in args.seeds.split(",")]
    grand_pairs = 0
    try:
        for seed in seeds:
            npz_path = out_dir / f"moe_s{seed}.npz"
            meta_path = out_dir / f"moe_s{seed}.meta.json"
            if npz_path.exists() and meta_path.exists() and not args.overwrite:
                meta = json.loads(meta_path.read_text())
                if meta.get("npz_sha256") == _sha(str(npz_path)):
                    grand_pairs += int(meta["n_pairs"])
                    print(f"[seed {seed}] exists (sha verified), skipping", flush=True)
                    continue
                raise SystemExit(f"{npz_path} exists but does not match its meta sha; "
                                 "delete or --overwrite deliberately")

            row_seeds = row_generator_seeds(seed, len(prompts))
            chunks: list[dict] = []
            t0 = time.time()
            for s in range(0, len(prompts), args.batch_size):
                batch = prompts[s: s + args.batch_size]
                enc = encode_batch(batch).to(dev)
                res = harvest_batch(model, tap, normcatch, enc["input_ids"], enc["attention_mask"],
                                    row_seeds[s: s + len(batch)], eos_set, args.max_new,
                                    args.temperature, bucket_spaces, top_m=args.top_m,
                                    forward_kwargs=fkw)
                chunks.append(res)
                done = min(s + args.batch_size, len(prompts))
                print(f"[seed {seed}] {done}/{len(prompts)} prompts "
                      f"anchors={sum(int(x) for c in chunks for x in c['lengths'])} "
                      f"{time.time() - t0:.0f}s", flush=True)

            arrays = {
                "tokens": _pad_cat([c["tokens"] for c in chunks], 0),
                "entropy": _pad_cat([c["entropy"] for c in chunks], 0.0),
                "argmax": _pad_cat([c["argmax"] for c in chunks], 0),
                "top_ids": _pad_cat([c["top_ids"] for c in chunks], 0),
                "top_p": _pad_cat([c["top_p"] for c in chunks], 0),
                "slots": _pad_cat([c["slots"] for c in chunks], -1),
                "hidden": _pad_cat([c["hidden"] for c in chunks], 0),
                "lengths": np.concatenate([c["lengths"] for c in chunks]),
                "prompt_idx": np.arange(len(prompts), dtype=np.int32),
            }
            for name in bucket_spaces:
                arrays[f"mass{name}"] = _pad_cat([c[f"mass{name}"] for c in chunks], 0)
            n_finished = int(sum(int(c["finished"].sum()) for c in chunks))
            np.savez(npz_path, **arrays)
            lengths = arrays["lengths"]
            n_pairs = total_pairs(lengths, GAMMA_DEFAULT)
            grand_pairs += n_pairs
            meta = {
                **redact_args(vars(args)),
                "seed": seed,
                "regime": ("target-only sampled generations; MoE router top-k expert-id "
                           "taps (S3 address stream, registered protocol 2026-08-31)"),
                "target_load": load_tag,
                # From verify_load_regime's module INSPECTION, never the flag.
                "load_regime_verified": load_verified,
                "telemetry_semantics": (f"slots = router top-{top_k} expert ids per MoE layer, "
                                        "sorted ascending (address stream; set semantics; "
                                        "no router weights stored)"),
                "n_experts": n_experts[0],
                "top_k": top_k,
                "chat_template_used": use_chat,
                "date_string_pinned": PINNED_DATE if use_chat else None,
                "chat_template_has_no_date_variable": True,
                "alignment": "block-start: label_index(a, j) = a + j - 1 (sideband.harvest)",
                "split_rule": "prompt_idx % 7: {0..4} train, 5 val, 6 test",
                "layer_names": tap.layer_names,
                "row_seed_convention": "SeedSequence(seed).spawn(n_prompts)[i] % (2**63-1)",
                "prompts_sha256": _sha(args.prompts),
                **{f"buckets{name}_sha256": _sha(path) for name, path in bucket_paths.items()},
                "n_prompts_used": len(prompts),
                "n_anchors": int(lengths.sum()),
                "n_pairs": int(n_pairs),
                "gamma": GAMMA_DEFAULT,
                "mean_length": float(lengths.mean()),
                "n_rows_finished_by_eos": n_finished,
                "eos_hit_fraction": float((lengths < args.max_new).mean()),
                "eos_hit_note": ("a row whose token at max_new-1 IS its EOS counts in "
                                 "n_rows_finished_by_eos but not eos_hit_fraction"),
                "runtime_s": round(time.time() - t0, 1),
                "npz_file": npz_path.name,
                "npz_sha256": _sha(str(npz_path)),
                "torch_version": torch.__version__,
                "transformers_version": transformers.__version__,
                "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
                "preflight": preflight_report,
                "git_commit": _git_commit(),
            }
            _atomic_write_text(meta_path, json.dumps(meta, indent=1, sort_keys=True))
            print(f"[seed {seed}] anchors={meta['n_anchors']} pairs={n_pairs} "
                  f"mean_len={meta['mean_length']:.1f} -> {npz_path}", flush=True)
    finally:
        tap.close()
        normcatch.close()

    print(f"[harvest] total pairs (gamma={GAMMA_DEFAULT}) across seeds run/skipped: {grand_pairs} "
          f"(exit bar 1,000,000: {'MET' if grand_pairs >= 1_000_000 else 'NOT MET - extend seeds'})",
          flush=True)


if __name__ == "__main__":  # pragma: no cover
    main()
