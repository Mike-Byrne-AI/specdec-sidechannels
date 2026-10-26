"""Token-frequency harvest from the TARGET's own sampled generations (OQ-4).

The glue-identification rule (docs/WHY_THIS_DIES.md K-7 addendum) needs token
frequencies in the deployment regime. This harvests them from target-only
sampling on the committed prompt set — deliberately independent of the draft,
of speculative decoding, and of any steering outcome, so the glue set cannot
be fit to the thing it later gates. Spec decoding is lossless (F-0/F-1), so
these frequencies estimate the same distribution the audit's emitted stream
follows.

GPU box. Usage:
    python -m sideband.real.harvest_freq \
        --model meta-llama/Llama-3.1-8B-Instruct --load-4bit \
        --prompts data/prompts.jsonl --n-prompts 210 --max-new 256 \
        --out results/real/gen_freq.json

Counts include terminal EOS/EOT tokens (they are glue-ish by nature);
right-padding debris after an early EOS is excluded by truncating each row at
its first EOS. CUDA sampling is not bitwise deterministic; frequency COUNTS
need no bit determinism — the derived glue json pins this file by sha256.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import time
from collections import Counter
from pathlib import Path

from . import require_real_deps
from .hf_specdec import PINNED_DATE, _atomic_write_text, redact_args


def main() -> None:  # pragma: no cover - GPU box entrypoint
    torch, transformers = require_real_deps()
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--prompts", required=True, help="jsonl with a 'prompt' field")
    ap.add_argument("--n-prompts", type=int, default=210)
    ap.add_argument("--max-new", type=int, default=256)
    ap.add_argument("--temperature", type=float, default=1.0)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--load-4bit", action="store_true")
    ap.add_argument("--bf16-routers", action="store_true",
                    help="exclude MoE router gates (+ lm_head) from 4-bit quantization "
                         "(the registered S3 deployment regime; no-op without --load-4bit)")
    ap.add_argument("--no-chat-template", action="store_true")
    ap.add_argument("--out", default="results/real/gen_freq.json")
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--skip-preflight", action="store_true")
    ap.add_argument("--allow-cpu-offload", action="store_true")
    args = ap.parse_args()

    if Path(args.out).exists() and not args.overwrite:
        raise SystemExit(f"{args.out} exists; results/ files are committed evidence (--overwrite to replace)")

    from ._preflight import preflight

    preflight_report = preflight(disk_path=Path(args.out).resolve().anchor or ".",
                                 force=args.skip_preflight)

    tok = transformers.AutoTokenizer.from_pretrained(args.model)
    use_chat = (not args.no_chat_template) and tok.chat_template is not None
    if tok.pad_token_id is None:
        tok.pad_token = tok.eos_token
    tok.padding_side = "left"

    from .moe_telemetry import load_quantized_moe, verify_load_regime

    model, load_tag = load_quantized_moe(transformers, torch, args.model,
                                         args.load_4bit, args.bf16_routers)
    load_verified = verify_load_regime(model, args.load_4bit, args.bf16_routers)
    from .hf_specdec import _assert_gpu_resident

    _assert_gpu_resident(model, "model", args.allow_cpu_offload)

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

    torch.manual_seed(args.seed)
    counts: Counter[int] = Counter()
    n_generated = 0
    t0 = time.time()
    with torch.no_grad():
        for s in range(0, len(prompts), args.batch_size):
            batch = prompts[s: s + args.batch_size]
            enc = encode_batch(batch).to(model.device)
            out = model.generate(**enc, do_sample=True, temperature=args.temperature,
                                 top_p=1.0, top_k=0, max_new_tokens=args.max_new,
                                 pad_token_id=tok.pad_token_id)
            gen = out[:, enc["input_ids"].shape[1]:]
            for row in gen.tolist():
                kept = []
                for t in row:
                    kept.append(t)
                    if t in eos_set:
                        break  # everything after is right-padding debris
                counts.update(kept)
                n_generated += len(kept)
            print(f"[{min(s + args.batch_size, len(prompts))}/{len(prompts)}] "
                  f"tokens={n_generated} {time.time() - t0:.0f}s", flush=True)

    def _git_commit() -> str:
        try:
            r = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True,
                               cwd=Path(__file__).resolve().parent, timeout=10)
            d = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True,
                               cwd=Path(__file__).resolve().parent, timeout=10)
            return ("unknown" if r.returncode != 0
                    else r.stdout.strip() + ("-dirty" if d.stdout.strip() else ""))
        except Exception:
            return "unknown"

    payload = {
        **redact_args(vars(args)),
        "regime": "target-only sampled generations (no draft, no spec decode)",
        "target_load": load_tag,
        "load_regime_verified": load_verified,
        "chat_template_used": use_chat,
        "date_string_pinned": PINNED_DATE if use_chat else None,
        "prompts_sha256": hashlib.sha256(Path(args.prompts).read_bytes()).hexdigest(),
        "n_prompts_used": len(prompts),
        "n_generated_tokens": n_generated,
        "n_distinct_tokens": len(counts),
        "eos_included_note": "counts include each row's terminal EOS/EOT; padding beyond it excluded",
        "determinism_note": "CUDA sampling is not bitwise deterministic; consumers pin this file by sha256",
        "torch_version": torch.__version__,
        "transformers_version": transformers.__version__,
        "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        "preflight": preflight_report,
        "git_commit": _git_commit(),
        "counts": {str(t): int(n) for t, n in sorted(counts.items())},
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    _atomic_write_text(Path(args.out), json.dumps(payload, indent=1, sort_keys=True))
    print(f"[harvest] {n_generated} tokens, {len(counts)} distinct -> {args.out}")


if __name__ == "__main__":  # pragma: no cover
    main()
