"""OQ-16 STAGE-A FREEZE (BLUEPRINT 2026-09-04): train ONE injection adapter
on the GPU box. Never imported by CI (torch); the numpy contracts it
relies on live in sideband.real.steer_inject and are CPU-tested.

  python tools/train_inject.py --arm oracle_h   --out results/real/oq16_inject_oracle_h.pt
  python tools/train_inject.py --arm free_inject --out results/real/oq16_inject_free_inject.pt
  python tools/train_inject.py --arm tel_inject  --out results/real/oq16_inject_tel_inject.pt

DATA (pinned): the four registered vanilla runs (recon.RECON_RUNS). Per
run: prompts re-encoded through the runner's encode_prompt (chat template
+ pinned date from the run meta; prompt 0's ids sha BOUND to the meta),
generated ids from <stem>.gen.jsonl, accepted / anchor_pos / h from the
sha-verified byproducts; the per-block vector is the byproduct's TRUE h
(oracle_h) or the cross-fitted h_hat of the STAGE-A export (free_inject
-> freetok, tel_inject -> union; sha-verified against the committed
export summary). Roles by the registered per-population split
(stage1_split): TRAIN + TEST prompts train, VAL prompts select the epoch
(best VAL KL, ties -> earlier). Data contracts (anchor arithmetic, emitted
counts) are asserted per prompt, never assumed.

OBJECTIVE (pinned): forward KL(p_verifier || q_drafter) per row over the
full vocabulary, teacher-forced on the run's own generated text (the
verifier loaded exactly as in the runs — NF4 — and frozen; the drafter
bf16 and FROZEN; only the adapter trains), averaged over rows that carry
a block delta; TVD reported. AdamW (weight decay 0), cosine lr_start ->
lr_end with linear warmup, gradient accumulation over --accum prompts,
batch 1 prompt, grad-norm clip 1.0, seed 0. bf16 GPU kernels are not
bit-deterministic: the saved weights (sha in the meta) ARE the evidence.

OUTPUTS: <out> (adapter state_dict; gitignored) and <out>.json (committed:
every input sha, hyperparameters, per-epoch train/VAL KL + TVD, the
selected epoch, the torch-vs-numpy adapter self-check deviation, peak
VRAM, versions, git commit).

--smoke N: N prompts, 1 epoch — REFUSES the registered out paths.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sideband.outcome_head import stage1_split  # noqa: E402
from sideband.recon import RECON_RUNS  # noqa: E402
from sideband.real.steer_inject import (  # noqa: E402
    ADAPTER_RANK,
    INJECT_ARMS,
    UpProjInjector,
    adapter_self_check,
    assemble_prompt,
    build_adapter,
    encode_prompt_ids,
    ids_sha,
    load_hhat,
)

REAL = Path(__file__).resolve().parents[1] / "results" / "real"
REGISTERED_OUTS = {arm: REAL / f"oq16_inject_{arm}.pt" for arm in INJECT_ARMS}
EXPORT_SUMMARY = REAL / "oq16_stage_a_export.json"
HHAT_DIR = REAL / "oq16_recon_hhat"

# pinned hyperparameters (STAGE-A FREEZE; judgment-call labels)
EPOCHS = 6
LR_START, LR_END, WARMUP = 1e-3, 1e-4, 50
ACCUM = 8
CLIP = 1.0
SEED = 0


def _sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _git_commit() -> str:
    import subprocess
    try:
        r = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                           text=True, timeout=10)
        d = subprocess.run(["git", "status", "--porcelain"], capture_output=True,
                           text=True, timeout=10)
        return (r.stdout.strip() or "unknown") + ("-dirty" if d.stdout.strip() else "")
    except Exception:
        return "unknown"


def load_runs(root: Path, arm: str, export: dict | None) -> list[dict]:
    """Every prompt of every registered run as an assembled record with
    its role and vectors; all shas verified."""
    from sideband.outcome_head import prompt_index_map, verify_byproduct
    out = []
    metas = {}
    for run_idx, spec in enumerate(RECON_RUNS):
        stem = spec["stem"]
        meta = json.loads((root / f"{stem}.meta.json").read_text())
        metas[stem] = meta
        files = verify_byproduct(root / f"{stem}.jsonl.byproduct",
                                 root / f"{stem}.summary.json")
        idx_map = prompt_index_map(root / f"{stem}.gen.jsonl")
        gen_rows = {}
        for line in (root / f"{stem}.gen.jsonl").read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                gen_rows[int(r["prompt_idx"])] = r
        prompts_path = Path(meta["prompts"])
        if not prompts_path.is_absolute():
            prompts_path = Path(__file__).resolve().parents[1] / prompts_path
        if _sha(prompts_path) != meta["prompts_sha256"]:
            raise SystemExit(f"{stem}: prompts file sha != run meta")
        prompts = [json.loads(l)["prompt"] for l in
                   prompts_path.read_text(encoding="utf-8").splitlines() if l.strip()]
        sel = meta.get("selected_original_indices") or list(range(len(prompts)))
        split = stage1_split(len(sel))
        role_of = {}
        for name, idx in split.items():
            for i in idx:
                role_of[int(i)] = name
        for f in files:
            pidx = int(f.stem[1:])
            pid = idx_map[pidx]
            z = dict(np.load(f))
            if arm == "oracle_h":
                vec = np.asarray(z["h"], dtype=np.float64)
            else:
                vec = load_hhat(HHAT_DIR, export, stem, pid, INJECT_ARMS[arm])
            out.append({"stem": stem, "run_idx": run_idx, "pop": spec["pop"],
                        "prompt_idx": pidx, "pid": pid, "role": role_of[pid],
                        "prompt": prompts[sel[pidx]], "gen": gen_rows[pidx],
                        "byp": {k: z[k] for k in ("accepted", "anchor_pos",
                                                  "n_blocks")},
                        "vectors": vec, "meta": meta})
    return out, metas


def main() -> None:  # pragma: no cover - GPU box entrypoint
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arm", required=True, choices=sorted(INJECT_ARMS))
    ap.add_argument("--out", required=True)
    ap.add_argument("--data-root", default=str(REAL))
    ap.add_argument("--epochs", type=int, default=EPOCHS)
    ap.add_argument("--lr-start", type=float, default=LR_START)
    ap.add_argument("--lr-end", type=float, default=LR_END)
    ap.add_argument("--warmup", type=int, default=WARMUP)
    ap.add_argument("--accum", type=int, default=ACCUM)
    ap.add_argument("--rank", type=int, default=ADAPTER_RANK)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--grad-checkpoint", action="store_true",
                    help="OOM fallback #1 (pinned order): gradient checkpointing "
                         "on the frozen drafter (recorded in the meta)")
    ap.add_argument("--smoke", type=int, default=None,
                    help="N prompts, 1 epoch; refuses the registered outs")
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    out = Path(args.out)
    registered = out.resolve() == REGISTERED_OUTS[args.arm].resolve()
    pinned = (args.epochs, args.lr_start, args.lr_end, args.warmup, args.accum,
              args.rank, args.seed) == (EPOCHS, LR_START, LR_END, WARMUP, ACCUM,
                                        ADAPTER_RANK, SEED)
    if registered and (args.smoke or not pinned):
        raise SystemExit("the registered out paths take the pinned "
                         "hyperparameters and no --smoke (registered-outs guard)")
    if out.exists() and not args.overwrite:
        raise SystemExit(f"{out} exists; pass --overwrite to redo")

    from sideband.real import require_real_deps
    torch, transformers = require_real_deps()
    import torch.nn.functional as F
    from sideband.real._preflight import preflight
    from sideband.real.hf_specdec import _assert_gpu_resident
    preflight_report = preflight(disk_path=out.resolve().anchor or ".", force=False)

    root = Path(args.data_root)
    export = None
    if args.arm != "oracle_h":
        export = json.loads(EXPORT_SUMMARY.read_text())
        if INJECT_ARMS[args.arm] not in export["arms"]:
            raise SystemExit(f"export summary lacks arm {INJECT_ARMS[args.arm]}")
    records, metas = load_runs(root, args.arm, export)
    meta0 = next(iter(metas.values()))
    for m in metas.values():
        for k in ("target", "draft", "load_4bit", "chat_template_used",
                  "date_string_pinned", "temperature", "gamma_base"):
            if m[k] != meta0[k]:
                raise SystemExit(f"run metas disagree on {k}")
    if args.smoke:
        records = records[: args.smoke]
        epochs = 1
    else:
        epochs = args.epochs

    # ---- models exactly as the runs loaded them -------------------------
    tok = transformers.AutoTokenizer.from_pretrained(meta0["target"])
    target_kwargs: dict = {"device_map": "auto", "torch_dtype": torch.bfloat16}
    if meta0["load_4bit"]:
        target_kwargs["quantization_config"] = transformers.BitsAndBytesConfig(
            load_in_4bit=True, bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=torch.bfloat16)
    target = transformers.AutoModelForCausalLM.from_pretrained(
        meta0["target"], **target_kwargs).eval()
    draft = transformers.AutoModelForCausalLM.from_pretrained(
        meta0["draft"], torch_dtype=torch.bfloat16, device_map="auto").eval()
    _assert_gpu_resident(target, "target", False)
    _assert_gpu_resident(draft, "draft", False)
    for p in list(target.parameters()) + list(draft.parameters()):
        p.requires_grad_(False)
    if args.grad_checkpoint:
        # Llama has no dropout, so train() only enables checkpointing
        draft.gradient_checkpointing_enable()
        draft.enable_input_require_grads()
        draft.train()
    device = next(draft.parameters()).device
    use_chat = bool(meta0["chat_template_used"])
    pinned_date = meta0["date_string_pinned"]

    # ---- prompt ids: re-encode + bind prompt 0's sha per run --------------
    for stem, m in metas.items():
        first = next(r for r in records if r["stem"] == stem and r["prompt_idx"] == 0)
        ids0 = encode_prompt_ids(tok, first["prompt"], use_chat, pinned_date)[0]
        if ids_sha(ids0.tolist()) != m["templated_prompt0_ids_sha256"]:
            raise SystemExit(f"{stem}: re-encoded prompt 0 ids sha != run meta "
                             "(tokenizer/template drift)")
    assembled = []
    for r in records:
        pids = encode_prompt_ids(tok, r["prompt"], use_chat, pinned_date)[0].numpy()
        a = assemble_prompt(pids, r["gen"], r["byp"], r["vectors"])
        a.update({"role": r["role"], "stem": r["stem"], "pid": r["pid"],
                  "vectors": r["vectors"]})
        assembled.append(a)
    train = [a for a in assembled if a["role"] in ("train", "test")]
    val = [a for a in assembled if a["role"] == "val"]
    if args.smoke:
        train, val = assembled, assembled[: max(1, len(assembled) // 4)]
    print(f"[inject] arm {args.arm}: {len(train)} train prompts, {len(val)} val "
          f"prompts, {sum(a['n_blocks'] for a in assembled)} blocks")

    # ---- adapter ----------------------------------------------------------
    h_dim = int(records[0]["vectors"].shape[1])
    n_layers = len(draft.model.layers)
    d_ff = int(draft.config.intermediate_size)
    torch.manual_seed(args.seed)
    adapter = build_adapter(h_dim, n_layers, d_ff, r=args.rank).to(device)
    dev0 = adapter_self_check(adapter)
    injector = UpProjInjector(draft)
    opt = torch.optim.AdamW(adapter.parameters(), lr=args.lr_start, weight_decay=0.0)
    n_steps = max(1, epochs * ((len(train) + args.accum - 1) // args.accum))

    def lr_at(step: int) -> float:
        if step < args.warmup:
            return args.lr_start * (step + 1) / args.warmup
        t = (step - args.warmup) / max(1, n_steps - args.warmup)
        return args.lr_end + 0.5 * (args.lr_start - args.lr_end) * (1 + np.cos(np.pi * min(1.0, t)))

    def row_deltas(a: dict):
        vec = torch.tensor(a["vectors"], dtype=torch.float32, device=device)
        deltas = adapter(vec)                                # (L_d, n_blocks, d_ff)
        guide = torch.tensor(a["guide"], device=device)
        rows = guide >= 0
        per_row = deltas.new_zeros(n_layers, guide.shape[0], d_ff)
        per_row[:, rows] = deltas[:, guide[rows]]
        return per_row, rows

    def prompt_loss(a: dict):
        ids = torch.tensor(a["ids"], device=device)[None]
        with torch.no_grad():
            v_logits = target(ids, use_cache=False).logits[0]
        per_row, rows = row_deltas(a)
        injector.set_rows(per_row)
        try:
            d_logits = draft(ids, use_cache=False).logits[0]
        finally:
            injector.clear()
        p_log = F.log_softmax(v_logits[rows].float(), dim=-1)
        q_log = F.log_softmax(d_logits[rows].float(), dim=-1)
        p = p_log.exp()
        kl = (p * (p_log - q_log)).sum(-1).mean()
        tvd = 0.5 * (p - q_log.exp()).abs().sum(-1).mean()
        return kl, tvd, int(rows.sum())

    def evaluate(rows_set):
        adapter.eval()
        tot_kl = tot_tvd = 0.0
        n = 0
        with torch.no_grad():
            for a in rows_set:
                kl, tvd, k = prompt_loss(a)
                tot_kl += float(kl) * k
                tot_tvd += float(tvd) * k
                n += k
        adapter.train()
        return {"kl": tot_kl / max(1, n), "tvd": tot_tvd / max(1, n), "rows": n}

    # ---- train ------------------------------------------------------------
    t0 = time.time()
    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()
    curves = {"val_before": evaluate(val)}
    print(f"[inject] epoch 0 val kl {curves['val_before']['kl']:.5f} "
          f"tvd {curves['val_before']['tvd']:.5f}")
    epochs_log = []
    best = None
    step = 0
    adapter.train()
    for epoch in range(1, epochs + 1):
        order = np.random.default_rng(args.seed + epoch).permutation(len(train))
        tr_kl = tr_tvd = 0.0
        tr_rows = 0
        opt.zero_grad(set_to_none=True)
        for i, j in enumerate(order.tolist()):
            kl, tvd, k = prompt_loss(train[j])
            (kl / args.accum).backward()
            tr_kl += float(kl) * k
            tr_tvd += float(tvd) * k
            tr_rows += k
            if (i + 1) % args.accum == 0 or i + 1 == len(order):
                for g in opt.param_groups:
                    g["lr"] = lr_at(step)
                torch.nn.utils.clip_grad_norm_(adapter.parameters(), CLIP)
                opt.step()
                opt.zero_grad(set_to_none=True)
                step += 1
        v = evaluate(val)
        rec = {"epoch": epoch, "train_kl": tr_kl / max(1, tr_rows),
               "train_tvd": tr_tvd / max(1, tr_rows), "val": v, "steps": step}
        epochs_log.append(rec)
        print(f"[inject] epoch {epoch} train kl {rec['train_kl']:.5f} | val kl "
              f"{v['kl']:.5f} tvd {v['tvd']:.5f} ({time.time() - t0:.0f}s)")
        if best is None or v["kl"] < best["val"]["kl"]:
            best = {"epoch": epoch, "val": v,
                    "state": {k: t.detach().clone().cpu()
                              for k, t in adapter.state_dict().items()}}
    curves["epochs"] = epochs_log
    adapter.load_state_dict(best["state"])
    dev1 = adapter_self_check(adapter)
    injector.close()

    out.parent.mkdir(parents=True, exist_ok=True)
    torch.save(best["state"], out)
    meta = {
        "registration": "OQ-16 STAGE-A FREEZE (BLUEPRINT 2026-09-04)",
        "arm": args.arm, "vector_source": INJECT_ARMS[args.arm],
        "adapter": {"h_dim": h_dim, "n_layers": n_layers, "d_ff": d_ff,
                    "rank": args.rank, "ln_eps": 1e-5},
        "hyperparameters": {"epochs": epochs, "lr_start": args.lr_start,
                            "lr_end": args.lr_end, "warmup": args.warmup,
                            "accum": args.accum, "clip": CLIP, "seed": args.seed,
                            "loss": "forward KL(p_verifier || q_drafter), full vocab; "
                                    "train = per-prompt mean of row KLs (accumulated "
                                    "over prompts), val = row-weighted pooled KL",
                            "drafter": "frozen", "grad_checkpoint": args.grad_checkpoint,
                            "smoke": args.smoke},
        "data": {"runs": [s["stem"] for s in RECON_RUNS],
                 "run_summary_sha256": {stem: _sha(root / f"{stem}.summary.json")
                                        for stem in metas},
                 "run_meta_sha256": {stem: _sha(root / f"{stem}.meta.json")
                                     for stem in metas},
                 "export_summary_sha256": (_sha(EXPORT_SUMMARY) if export else None),
                 "n_train_prompts": len(train), "n_val_prompts": len(val),
                 "n_blocks": sum(a["n_blocks"] for a in assembled)},
        "selected_epoch": best["epoch"], "selected_val": best["val"],
        # selection is over epochs 1..E only; a selected adapter worse than
        # the untrained no-op is flagged, never silently swapped for it —
        # the arm then fails the gate on its own (pinned disposition)
        "adapter_worse_than_noop": bool(best["val"]["kl"] > curves["val_before"]["kl"]),
        "curves": curves,
        "adapter_self_check_dev": {"init": dev0, "final": dev1},
        "weights_sha256": _sha(out),
        "peak_vram_gb": (round(torch.cuda.max_memory_allocated() / 2**30, 2)
                         if torch.cuda.is_available() else None),
        "target": meta0["target"], "draft": meta0["draft"],
        "target_load": meta0["target_load"],
        "torch_version": torch.__version__,
        "transformers_version": transformers.__version__,
        "numpy_version": np.__version__,
        "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        "preflight": preflight_report,
        "git_commit": _git_commit(),
        "note": "wall-clock banned (D-9); bf16 kernels are not bit-deterministic — "
                "the saved weights (sha above) are the evidence",
    }
    Path(str(out) + ".json").write_text(json.dumps(meta, indent=2, sort_keys=True))
    print(f"[inject] wrote {out} (sha {meta['weights_sha256'][:12]}..) + meta; "
          f"selected epoch {best['epoch']} val kl {best['val']['kl']:.5f}")


if __name__ == "__main__":
    main()
