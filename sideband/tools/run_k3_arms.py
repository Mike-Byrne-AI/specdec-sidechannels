#!/usr/bin/env python3
"""K-3 Attempt #1 arm runner (stage E; BLUEPRINT arc registration
2026-09-01, freeze pins + stage-E clarifications E1-E11, 2026-09-02).

Runs ONE arm on ONE prompt population at ONE seed through the extended
spec-decode loop (hf_specdec.spec_decode_prompt with k3=...):

  arm 1  vanilla fixed gamma=4          (scheduler inert)
  arm 2  draft-confidence scheduler     (E3; needs --thresholds)
  arm 3  (a)-probe scheduler            (needs --thresholds)
  arm 4  (c)-probe scheduler            (needs --thresholds)
  arm 5  fixed gamma=6 descriptive control (never in the MIN)

Every arm runs with the prefill + live reader + byproduct recorder
active (E8/E11: cross-arm comparability; the vanilla arm's log is the
signal-materialization source E5 and OQ-15's paired dataset).
--no-instruments (fixed arms only) is the containment rider's OFF
configuration: same execution pattern, no hooks.

Outputs next to --out (house conventions: meta BEFORE the run, per-prompt
stats checkpoint fsync'd, summary as completion marker, --resume exact):
  <out>.meta.json, <out>.stats.jsonl, <out>.gen.jsonl,
  <out>.byproduct/p{idx}.npz (gitignored raw; shas in the summary),
  <out>.summary.json (tokens/call, drafted-per-emitted, totals).

Wall-clock claims stay banned (D-9). Gate arithmetic per E6: tokens/call
= emitted per verify call, prefill excluded uniformly.

Run (GPU box), e.g. the B_ref/materialization val run:
    python tools/run_k3_arms.py --arm 1 --prompts data/prompts.jsonl \
        --select-split val --seed 0 --load-4bit \
        --out results/real/k3_val_arm1.jsonl
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from sideband.harvest import split_of_prompt  # noqa: E402
from sideband.dists import spawn  # noqa: E402
from sideband.scheduler import (GAMMA_BASE, GAMMA_MAX, SchedulerPolicy,  # noqa: E402
                                Thresholds)

REAL = Path(__file__).resolve().parent.parent / "results" / "real"

RESUME_IDENTITY_ARGS = (
    "arm", "target", "draft", "prompts", "select_split", "n_prompts",
    "gamma_base", "gamma_max", "max_new", "temperature", "seed", "load_4bit",
    "no_chat_template", "no_instruments", "inject_adapter", "recon_weights",
)

ARM_KINDS = {1: "fixed", 2: "draft_conf", 3: "probe", 4: "probe", 5: "fixed",
             6: "head", 7: "head",       # 6/7: OQ-15 STAGE-C FREEZE head arms
             8: "fixed", 9: "fixed", 10: "fixed"}  # 8-10: OQ-16 STAGE-A inject arms
ARM_PROBE = {3: "a", 4: "c"}
ARM_HEAD_FAMILY = {6: "free", 7: "tel"}
# OQ-16 STAGE-A FREEZE: fixed gamma-4 schedule + SD^2-style draft-side
# injection of (8) the TRUE anchor h_a — NON-DEPLOYABLE ceiling, D-2-named;
# (9) the frozen FREETOK2 reconstruction; (10) the frozen UNION
# reconstruction (sideband.real.steer_inject).
ARM_INJECT = {8: "oracle_h", 9: "free_inject", 10: "tel_inject"}
THRESHOLD_KIND = {2: "draft_conf", 3: "probe", 4: "probe",
                  6: "head", 7: "head"}


def _sha(p: str | Path | None) -> str | None:
    if p is None or not Path(p).exists():
        return None
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load_thresholds(path: str, arm: int) -> tuple[Thresholds, dict]:
    """Load a frozen-thresholds file (written by the registered freeze
    stage). The file carries MATERIALIZED values; the runner never
    re-derives them. Refuses arm/kind mismatches."""
    data = json.loads(Path(path).read_text())
    want_kind = THRESHOLD_KIND[arm]
    if data.get("kind") != want_kind or int(data.get("arm", -1)) != arm:
        raise SystemExit(f"thresholds file is for kind={data.get('kind')!r} "
                         f"arm={data.get('arm')}, not arm {arm}")
    thr = Thresholds(kind=data["kind"], stop_level=float(data["stop_level"]),
                     extend_level=float(data["extend_level"]),
                     stop=(float(data["stop"][0]), float(data["stop"][1])),
                     extend=float(data["extend"]))
    return thr, data


def select_prompts(path: str, split: str, n_prompts: int | None):
    """(prompt_text, original_line_index) pairs; split selection uses the
    pinned idx % 7 rule on the ORIGINAL line index (E5 names the 30 val
    prompts of data/prompts.jsonl this way)."""
    lines = [json.loads(l)["prompt"] for l in Path(path).read_text().splitlines()
             if l.strip()]
    pairs = [(p, i) for i, p in enumerate(lines)
             if split == "none" or split_of_prompt(i) == split]
    if n_prompts is not None:
        pairs = pairs[:n_prompts]
    if not pairs:
        raise SystemExit(f"no prompts selected from {path} (split={split})")
    return pairs


def _atomic_text(path: Path, text: str) -> None:
    """Local twin of hf_specdec._atomic_write_text (torch-free import
    path): fsync'd tmp + os.replace so a crash mid-repair cannot lose
    the checkpoint file (critic advisory 2026-09-02)."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w") as fh:
        fh.write(text)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def repair_stats(stats_path: Path, gen_path: Path) -> set[int]:
    """Drop the stats file's torn tail; keep the first parseable gen line
    per completed prompt (fsync ordering: gen before stats). Byproduct
    npzs of incomplete prompts are simply overwritten on re-run."""
    rows = []
    if stats_path.exists():
        for line in stats_path.read_text().splitlines():
            try:
                d = json.loads(line)
                int(d["prompt_idx"])
            except (json.JSONDecodeError, KeyError, ValueError):
                break
            rows.append(d)
    completed = {int(d["prompt_idx"]) for d in rows}
    tmp = "\n".join(json.dumps(d) for d in rows)
    _atomic_text(stats_path, tmp + ("\n" if tmp else ""))
    if gen_path.exists():
        kept, seen = [], set()
        for line in gen_path.read_text().splitlines():
            try:
                i = int(json.loads(line)["prompt_idx"])
            except (json.JSONDecodeError, KeyError, ValueError):
                continue
            if i in completed and i not in seen:
                seen.add(i)
                kept.append(line)
        _atomic_text(gen_path, "\n".join(kept) + ("\n" if kept else ""))
    return completed


def main() -> None:  # pragma: no cover - GPU box entrypoint
    from sideband.real import require_real_deps

    torch, transformers = require_real_deps()
    from sideband.real.hf_specdec import (PINNED_DATE, _assert_gpu_resident,
                                          _atomic_write_text, redact_args,
                                          spec_decode_prompt)
    from sideband.real.k3_live import (ByproductRecorder, K3Config,
                                       build_live_reader, load_probe_weights)

    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", type=int, required=True, choices=sorted(ARM_KINDS))
    ap.add_argument("--target", default="meta-llama/Llama-3.1-8B-Instruct")
    ap.add_argument("--draft", default="meta-llama/Llama-3.2-1B-Instruct")
    ap.add_argument("--prompts", required=True)
    ap.add_argument("--select-split", default="none",
                    choices=["none", "train", "val", "test"],
                    help="filter by the pinned idx %% 7 split of the ORIGINAL "
                         "line index (E5: val = the 30 tuning prompts)")
    ap.add_argument("--n-prompts", type=int, default=None)
    ap.add_argument("--gamma-base", type=int, default=GAMMA_BASE)
    ap.add_argument("--gamma-max", type=int, default=GAMMA_MAX)
    ap.add_argument("--max-new", type=int, default=256)
    ap.add_argument("--temperature", type=float, default=1.0)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--thresholds", default=None,
                    help="frozen-thresholds json (arms 2-4/6-7; refused for 1/5)")
    ap.add_argument("--head-weights", default=None,
                    help="frozen OQ-15 head-weights npz (arms 6/7 only; "
                         "STAGE-C FREEZE export)")
    ap.add_argument("--inject-adapter", default=None,
                    help="STAGE-A adapter state_dict (.pt; its .json meta is "
                         "sha-bound); arms 8-10 only")
    ap.add_argument("--recon-weights", default=None,
                    help="STAGE-A reconstruction export npz (arms 9/10 only; "
                         "sha-bound to --recon-export)")
    ap.add_argument("--recon-export", default=str(REAL / "oq16_stage_a_export.json"))
    ap.add_argument("--probe-weights", default=str(REAL / "k3_probe_weights.npz"))
    ap.add_argument("--buckets16", default=str(REAL / "buckets_k16.json"))
    ap.add_argument("--glue16", default=str(REAL / "glue_k16.json"))
    ap.add_argument("--buckets32", default=str(REAL / "buckets_k32.json"))
    ap.add_argument("--buckets64", default=str(REAL / "buckets_k64.json"))
    ap.add_argument("--buckets512", default=str(REAL / "buckets_k512.json"))
    ap.add_argument("--load-4bit", action="store_true")
    ap.add_argument("--no-chat-template", action="store_true")
    ap.add_argument("--no-instruments", action="store_true",
                    help="containment-rider OFF configuration (E10): fixed "
                         "arms only; prefill runs, no hooks, no byproduct")
    ap.add_argument("--out", required=True)
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--skip-preflight", action="store_true")
    ap.add_argument("--allow-cpu-offload", action="store_true")
    args = ap.parse_args()

    if args.resume and args.overwrite:
        raise SystemExit("--resume and --overwrite are mutually exclusive")
    kind = ARM_KINDS[args.arm]
    if kind == "fixed" and args.thresholds:
        raise SystemExit(f"arm {args.arm} is fixed — takes no thresholds")
    if kind != "fixed" and not args.thresholds:
        raise SystemExit(f"arm {args.arm} needs --thresholds (frozen on val)")
    if kind == "head" and not args.head_weights:
        raise SystemExit(f"arm {args.arm} needs --head-weights (the frozen "
                         "STAGE-C export)")
    if kind != "head" and args.head_weights:
        raise SystemExit("--head-weights is a head-arm (6/7) argument only")
    if args.no_instruments and kind != "fixed":
        raise SystemExit("--no-instruments is a fixed-arm containment mode only")
    inject_arm = ARM_INJECT.get(args.arm)
    if inject_arm:
        if not args.inject_adapter:
            raise SystemExit(f"arm {args.arm} needs --inject-adapter (STAGE-A)")
        if args.no_instruments:
            raise SystemExit("injection arms need the live reader (no --no-instruments)")
        if inject_arm == "oracle_h" and args.recon_weights:
            raise SystemExit("arm 8 injects the TRUE anchor state — no --recon-weights")
        if inject_arm != "oracle_h" and not args.recon_weights:
            raise SystemExit(f"arm {args.arm} needs --recon-weights (STAGE-A export)")
    elif args.inject_adapter or args.recon_weights:
        raise SystemExit("--inject-adapter/--recon-weights are STAGE-A arm (8-10) "
                         "arguments only")
    gamma_base = args.gamma_base if args.arm != 5 else max(args.gamma_base, 6)
    if args.arm == 5:
        gamma_base = 6  # the descriptive always-extend control

    from sideband.real._preflight import preflight

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    preflight_report = preflight(disk_path=out_path.resolve().anchor or ".",
                                 force=args.skip_preflight)

    thr = thr_data = None
    if args.thresholds:
        thr, thr_data = load_thresholds(args.thresholds, args.arm)

    # ---- models (mirrors hf_specdec main) --------------------------------
    tok = transformers.AutoTokenizer.from_pretrained(args.target)
    use_chat = (not args.no_chat_template) and tok.chat_template is not None
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
    tok_draft = transformers.AutoTokenizer.from_pretrained(args.draft)
    if target.config.vocab_size != draft.config.vocab_size or \
            tok.get_vocab() != tok_draft.get_vocab():
        raise SystemExit("target/draft tokenizer mismatch — cannot spec-decode")

    # ---- live instrument (E1/E7 bindings via the shared constructor) -----
    probes, pmeta = load_probe_weights(args.probe_weights)
    reader = None
    if not args.no_instruments:
        # E12(ii): the probes' features assume the harvest temperature.
        # Hard-indexed (critic nit): a meta lacking the field must fail,
        # not silently default.
        want_t = float(pmeta["harvest_temperature"])
        if float(args.temperature) != want_t:
            raise SystemExit(f"--temperature {args.temperature} != harvest "
                             f"temperature {want_t} — the probes would read "
                             "off-distribution features silently")
        reader = build_live_reader(
            target, pmeta, probes,
            bucket_paths={"16": args.buckets16, "32": args.buckets32,
                          "64": args.buckets64, "512": args.buckets512},
            glue16_path=args.glue16, load_4bit=args.load_4bit,
            expect_target=args.target)
    glue_class = int(pmeta["n_classes"]) - 1

    policy = SchedulerPolicy(kind, gamma_base=gamma_base,
                             gamma_max=(args.gamma_max if kind != "fixed"
                                        else gamma_base),
                             thresholds=thr,
                             probe_arm=ARM_PROBE.get(args.arm),
                             glue_class=(glue_class if kind == "probe" else None))

    head_scorer = None
    if kind == "head":
        from sideband.outcome_head import HeadScorer
        head_scorer = HeadScorer(args.head_weights, ARM_HEAD_FAMILY[args.arm])

    # ---- STAGE-A injection (arms 8-10): every binding enforced ----------
    inject = None
    inject_info: dict = {}
    if inject_arm:
        from sideband.real.steer_inject import (INJECT_ARMS, BlockInjector,
                                                UpProjInjector, adapter_self_check,
                                                build_adapter)
        from sideband.recon import LiveReconstructor
        ameta_path = Path(args.inject_adapter + ".json")
        ameta = json.loads(ameta_path.read_text())
        if ameta["arm"] != inject_arm:
            raise SystemExit(f"adapter was trained for {ameta['arm']}, not {inject_arm}")
        if _sha(args.inject_adapter) != ameta["weights_sha256"]:
            raise SystemExit("adapter .pt sha != its meta (tampered or mismatched)")
        if ameta["hyperparameters"].get("smoke"):
            raise SystemExit("a --smoke-trained adapter is refused for a verdict arm")
        if ameta["target"] != args.target or ameta["draft"] != args.draft:
            raise SystemExit("adapter meta model pair != this run's pair")
        a = ameta["adapter"]
        if a["n_layers"] != len(draft.model.layers) or \
                a["d_ff"] != int(draft.config.intermediate_size):
            raise SystemExit("adapter geometry != the loaded drafter")
        device = next(draft.parameters()).device
        adapter = build_adapter(a["h_dim"], a["n_layers"], a["d_ff"], r=a["rank"]).to(device)
        # weights_only: the adapter is a user-supplied file (2026-10-16, lane C of the image audit, S5a-C-3)
        adapter.load_state_dict(torch.load(args.inject_adapter, map_location=device, weights_only=True))
        adapter.eval()
        for p in adapter.parameters():
            p.requires_grad_(False)
        self_dev = adapter_self_check(adapter)
        recon = None
        recon_export_sha = None
        if INJECT_ARMS[inject_arm] != "h":
            export = json.loads(Path(args.recon_export).read_text())
            if _sha(args.recon_weights) != export["weights_sha256"]:
                raise SystemExit("--recon-weights sha != the committed export summary")
            if INJECT_ARMS[inject_arm] not in export["arms"]:
                raise SystemExit(f"export lacks arm {INJECT_ARMS[inject_arm]}")
            if ameta["data"].get("export_summary_sha256") != _sha(args.recon_export):
                raise SystemExit("adapter was trained against a different export summary")
            recon_export_sha = _sha(args.recon_export)
            recon = LiveReconstructor(args.recon_weights, INJECT_ARMS[inject_arm],
                                      n_slots=int(pmeta["tap"]["n_slots"]))
        inject = BlockInjector(UpProjInjector(draft), adapter, INJECT_ARMS[inject_arm],
                               recon=recon, device=device, gamma=gamma_base)
        inject_info = {"inject_arm": inject_arm,
                       "inject_vector_source": INJECT_ARMS[inject_arm],
                       "inject_adapter_sha256": _sha(args.inject_adapter),
                       "inject_adapter_meta_sha256": _sha(ameta_path),
                       "inject_adapter_selected_epoch": ameta.get("selected_epoch"),
                       "recon_weights_sha256": _sha(args.recon_weights),
                       "recon_export_sha256": recon_export_sha,
                       "adapter_self_check_dev": self_dev}
        print(f"[arm {args.arm}] STAGE-A injection {inject_arm}: adapter rank "
              f"{a['rank']} self-check dev {self_dev:.2e}")

    # ---- prompts + RNG ---------------------------------------------------
    pairs = select_prompts(args.prompts, args.select_split, args.n_prompts)
    prompts = [p for p, _ in pairs]
    orig_idx = [i for _, i in pairs]
    gens = spawn(args.seed, len(prompts))

    def encode_prompt(p: str):
        if use_chat:
            return tok.apply_chat_template(
                [{"role": "user", "content": p}], add_generation_prompt=True,
                return_tensors="pt", date_string=PINNED_DATE)
        return tok(p, return_tensors="pt").input_ids

    # ---- sidecars, meta, resume (house conventions) ----------------------
    stats_path = out_path.with_suffix(".stats.jsonl")
    meta_path = out_path.with_suffix(".meta.json")
    summary_path = out_path.with_suffix(".summary.json")
    gen_path = out_path.with_suffix(".gen.jsonl")
    byp_dir = Path(str(out_path) + ".byproduct")

    def _git_commit() -> str:
        import subprocess
        try:
            r = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                               text=True, timeout=10,
                               cwd=Path(__file__).resolve().parent)
            d = subprocess.run(["git", "status", "--porcelain"], capture_output=True,
                               text=True, timeout=10,
                               cwd=Path(__file__).resolve().parent)
            return (r.stdout.strip() or "unknown") + ("-dirty" if d.stdout.strip() else "")
        except Exception:
            return "unknown"

    run_id = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    completed: set[int] = set()
    cur_ids_sha = (hashlib.sha256(json.dumps(
        encode_prompt(prompts[0])[0].tolist()).encode()).hexdigest())

    if args.resume:
        if not (stats_path.exists() and meta_path.exists()):
            raise SystemExit(f"--resume needs existing {stats_path} and {meta_path}")
        if summary_path.exists():
            raise SystemExit(f"{summary_path} exists — that run completed")
        old = json.loads(meta_path.read_text())
        mism = [f"{k}: {old.get(k)!r} != {getattr(args, k)!r}"
                for k in RESUME_IDENTITY_ARGS if old.get(k) != getattr(args, k)]
        for k, cur in (("prompts_sha256", _sha(args.prompts)),
                       ("thresholds_sha256", _sha(args.thresholds)),
                       ("probe_weights_sha256", _sha(args.probe_weights)),
                       ("head_weights_sha256", _sha(args.head_weights)),
                       ("inject_adapter_sha256", inject_info.get("inject_adapter_sha256")),
                       ("recon_weights_sha256", inject_info.get("recon_weights_sha256")),
                       ("templated_prompt0_ids_sha256", cur_ids_sha)):
            if old.get(k) != cur:
                mism.append(f"{k}: {old.get(k)!r} != {cur!r}")
        if mism:
            raise SystemExit("--resume refused, invocation differs:\n  - "
                             + "\n  - ".join(mism))
        completed = repair_stats(stats_path, gen_path)
        meta = old
        meta.setdefault("run_ids", [meta.get("run_id")]).append(run_id)
        meta["resumed"] = True
        _atomic_write_text(meta_path, json.dumps(meta, indent=2, sort_keys=True))
        print(f"[resume] {len(completed)} prompts already complete")
    else:
        if out_path.exists() or stats_path.exists():
            if not args.overwrite:
                raise SystemExit(f"{out_path} sidecars exist; results/ files are "
                                 "committed evidence. --resume, --overwrite, or a "
                                 "distinct --out.")
        summary_path.unlink(missing_ok=True)
        stats_path.unlink(missing_ok=True)
        gen_path.unlink(missing_ok=True)
        out_path.write_text("")  # marker file (jsonl reserved; stats carry data)
        if byp_dir.exists():
            for f in byp_dir.glob("p*.npz"):
                f.unlink()
        byp_dir.mkdir(parents=True, exist_ok=True)
        meta = {
            **redact_args(vars(args)),
            "run_id": run_id, "run_ids": [run_id],
            "arm_kind": kind, "probe_arm": ARM_PROBE.get(args.arm),
            "gamma_base_effective": gamma_base,
            "instruments": not args.no_instruments,
            "rng_scheme": "per-prompt spawn(seed, n)[i] (dists.spawn; "
                          "resume-stable, prompt-paired)",
            "target_load": "nf4-double-quant-bf16compute" if args.load_4bit else "bf16",
            "chat_template_used": use_chat,
            "date_string_pinned": PINNED_DATE if use_chat else None,
            "templated_prompt0_ids_sha256": cur_ids_sha,
            "prompts_sha256": _sha(args.prompts),
            "selected_original_indices": orig_idx,
            "thresholds_sha256": _sha(args.thresholds),
            "thresholds": thr_data,
            "head_weights_sha256": _sha(args.head_weights),
            "head_family": ARM_HEAD_FAMILY.get(args.arm),
            **inject_info,
            "probe_weights_sha256": _sha(args.probe_weights),
            "probe_weights_meta_sha256": _sha(Path(args.probe_weights).with_suffix(".meta.json")),
            "estimand_note": "tokens/call = emitted per verify call, prefill "
                             "excluded uniformly (E6); wall-clock banned (D-9)",
            "torch_version": torch.__version__,
            "transformers_version": transformers.__version__,
            "numpy_version": np.__version__,
            "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
            "preflight": preflight_report,
            "git_commit": _git_commit(),
        }
        _atomic_write_text(meta_path, json.dumps(meta, indent=2, sort_keys=True))

    # ---- run -------------------------------------------------------------
    import contextlib

    with contextlib.ExitStack() as stack:
        sf = stack.enter_context(stats_path.open("a"))
        gf = stack.enter_context(gen_path.open("a"))
        for i, prompt in enumerate(prompts):
            if i in completed:
                continue
            t0 = time.time()
            if torch.cuda.is_available():
                torch.cuda.reset_peak_memory_stats()
            ids = encode_prompt(prompt)
            recorder = ByproductRecorder(args.gamma_max) if reader is not None else None
            cfg = K3Config(policy=policy, reader=reader, recorder=recorder,
                           head_scorer=head_scorer, inject=inject)
            blocks_before = inject.n_blocks if inject is not None else 0
            out_ids, _records, stats = spec_decode_prompt(
                target, draft, ids, gamma_base, args.max_new, args.temperature,
                gens[i], bucket_of_token=None, prompt_idx=i, run_id=run_id,
                use_kv_cache=True, k3=cfg)
            if inject is not None and \
                    inject.n_blocks - blocks_before != int(stats["n_blocks"]):
                raise SystemExit(f"prompt {i}: injected {inject.n_blocks - blocks_before} "
                                 f"blocks != {stats['n_blocks']} verify blocks")
            if recorder is not None:
                np.savez(byp_dir / f"p{i:03d}.npz", **recorder.finalize())
            gf.write(json.dumps({"prompt_idx": i, "orig_prompt_idx": orig_idx[i],
                                 "run_id": run_id,
                                 "prompt_len": int(ids.shape[1]),
                                 "generated_ids": out_ids[0, ids.shape[1]:].tolist()})
                     + "\n")
            gf.flush(); os.fsync(gf.fileno())
            dt = time.time() - t0
            line = {"prompt_idx": i, "orig_prompt_idx": orig_idx[i],
                    "run_id": run_id, "seconds": round(dt, 2),
                    "peak_vram_gb": (round(torch.cuda.max_memory_allocated() / 2**30, 2)
                                     if torch.cuda.is_available() else None),
                    **stats}
            sf.write(json.dumps(line) + "\n")
            sf.flush(); os.fsync(sf.fileno())
            print(f"[arm {args.arm}] [{i + 1}/{len(prompts)}] "
                  f"t/c={stats['tokens_per_call']:.3f} "
                  f"budget={stats['drafted_per_emitted']:.3f} "
                  f"stop={stats['n_stop_blocks']} ext={stats['n_extend_blocks']} "
                  f"{dt:.1f}s", flush=True)

    # ---- summary from DISK (resume-safe) ---------------------------------
    per_prompt = sorted((json.loads(l) for l in stats_path.read_text().splitlines()),
                        key=lambda d: d["prompt_idx"])
    tot = {k: sum(int(s[k]) for s in per_prompt)
           for k in ("n_emitted", "n_blocks", "n_drafted", "n_accepted",
                     "n_proposed", "n_stop_blocks", "n_extend_blocks")}
    byp_shas = {f.name: hashlib.sha256(f.read_bytes()).hexdigest()
                for f in sorted(byp_dir.glob("p*.npz"))} if reader is not None else {}
    summary = {
        "run_id": run_id, "run_ids": meta.get("run_ids", [run_id]),
        "arm": args.arm, "arm_kind": kind,
        "n_prompts_completed": len(per_prompt),
        "totals": tot,
        "tokens_per_call": tot["n_emitted"] / max(1, tot["n_blocks"]),
        "drafted_per_emitted": tot["n_drafted"] / max(1, tot["n_emitted"]),
        "mean_acceptance_rate": float(np.mean([s["acceptance_rate"]
                                               for s in per_prompt])),
        **({"inject_arm": inject_arm,
            "inject_blocks_this_process": inject.n_blocks} if inject else {}),
        "byproduct_sha256": byp_shas,
        "per_prompt_stats": per_prompt,
    }
    _atomic_write_text(summary_path, json.dumps(summary, indent=1, sort_keys=True))
    print(json.dumps({k: v for k, v in summary.items()
                      if k not in ("per_prompt_stats", "byproduct_sha256")}, indent=2))


if __name__ == "__main__":  # pragma: no cover
    main()
