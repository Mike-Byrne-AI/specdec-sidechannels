#!/usr/bin/env python3
"""K-3 threshold-search driver (THRESHOLD-SEARCH REGISTRATION, BLUEPRINT
2026-09-02; Amendment #1 objective/grid/tie-break; E5/E12 materialization).

For ONE adaptive arm (2/3/4): freezes B_ref from the committed seed-0
vanilla val run, materializes the 19-level quantile grids on that run's
CONSULTING-block signals (byproduct rows >= 1 — E12's pinned row-0
filter), then runs the registered frontier procedure
(sideband.scheduler.search_frontier / select_thresholds — the search
logic lives in the CI-tested pure module, not here) with live in-process
evals: models loaded ONCE, each eval a fresh spawn(0, n) pass over the
30 val prompts at seed 0 through the committed spec_decode k3 path.

Driver-gate carries (critic 2026-09-02, binding): (1) the selection-time
feasibility assert lives in select_thresholds; (2) every eval rebuilds
fresh per-prompt generators and the prompt encoding is asserted against
the val run's recorded sha — model-loaded-once must not leak RNG or
cache state across evals (per-eval state is created inside the eval).

Every eval is checkpointed to <out>.state.jsonl (sha-headed: B_ref +
val-run byproduct shas + prompts sha + a hash of the materialized grids;
resume refuses a mismatch). Dedupe: grid points whose materialized
threshold values are identical reuse the earlier eval, recorded as
dedupe_of. FAILED-INFEASIBLE arms get the registered comparability-
fallback corner, labeled.

Outputs: results/real/k3_threshold_search_arm{N}.json (+ state file,
committed evidence) and results/real/k3_thresholds_arm{N}.json (the
frozen thresholds run_k3_arms --thresholds consumes).

Run (GPU box), per arm:
    python tools/k3_threshold_search.py --arm 4 --load-4bit
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
from sideband.provenance import redact_args  # noqa: E402
from sideband.dists import spawn  # noqa: E402
from sideband.harvest import split_of_prompt  # noqa: E402
from sideband.scheduler import (QUANTILE_LEVELS, SchedulerPolicy,  # noqa: E402
                                Thresholds, search_frontier,
                                select_thresholds)

REAL = Path(__file__).resolve().parent.parent / "results" / "real"
ARM_KIND = {2: "draft_conf", 3: "probe", 4: "probe", 6: "head", 7: "head"}
ARM_PROBE = {3: "a", 4: "c"}
ARM_HEAD_FAMILY = {6: "free", 7: "tel"}  # OQ-15 STAGE-C FREEZE arms
ARM_SIGNAL_KEY = {2: "q_sig", 3: "probe_conf_a", 4: "probe_conf_c"}
# The registered comparability-fallback corner (maximal stop, minimal
# extend, mapped through each arm's signal direction; head arms share
# arm 2's orientation — STAGE-C FREEZE directions note).
CORNER = {2: (len(QUANTILE_LEVELS) - 1, len(QUANTILE_LEVELS) - 1),
          3: (0, len(QUANTILE_LEVELS) - 1),
          4: (0, len(QUANTILE_LEVELS) - 1),
          6: (len(QUANTILE_LEVELS) - 1, len(QUANTILE_LEVELS) - 1),
          7: (len(QUANTILE_LEVELS) - 1, len(QUANTILE_LEVELS) - 1)}


def _sha(p: str | Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load_val_run(base: Path, expect_seed: int = 0,
                 expect_split: str = "val") -> tuple[dict, dict, dict]:
    """Load the registered B_ref/materialization run with bindings: must
    be arm 1, the expected seed/split (K-3: seed 0 val split; OQ-15
    Stage C: seed 2, select_split none on the fresh val file — STAGE-C
    FREEZE), temperature 1.0, instruments on, completed; byproduct npzs
    sha-verified against the summary."""
    meta = json.loads(base.with_suffix(".meta.json").read_text())
    summary_path = base.with_suffix(".summary.json")
    if not summary_path.exists():
        raise SystemExit(f"{summary_path} missing — the val run did not complete")
    summary = json.loads(summary_path.read_text())
    checks = {"arm": 1, "seed": expect_seed, "select_split": expect_split,
              "temperature": 1.0}
    for k, want in checks.items():
        if meta.get(k) != want:
            raise SystemExit(f"val run {k}={meta.get(k)!r}, need {want!r} "
                             "(the E5 materialization run)")
    if not meta.get("instruments", False):
        raise SystemExit("val run has no instruments — no signals to materialize")
    byp_dir = Path(str(base) + ".byproduct")
    rows = {}
    for name, want in summary["byproduct_sha256"].items():
        p = byp_dir / name
        if _sha(p) != want:
            raise SystemExit(f"{p} sha mismatch vs summary — refusing unbound byproduct")
        rows[int(name[1:-4])] = np.load(p)
    return meta, summary, rows


def materialize_grids(rows: dict, arm: int, head_scorer=None) -> dict:
    """E5 + E12: per-level stop pairs and extend values from the val
    run's CONSULTING-block signals (byproduct rows >= 1 per prompt).
    Head arms (STAGE-C FREEZE): per-block S_1/S_2 and S_4*a_hat_5
    computed OFFLINE through the exported heads from the same rows;
    stop grids = quantiles of S_1/S_2, extend grid = quantiles of the
    S_4*a_hat_5 distribution (np.quantile linear, pinned)."""
    if ARM_KIND[arm] == "head":
        if head_scorer is None:
            raise SystemExit(f"arm {arm} materialization needs the head scorer")
        from sideband.outcome_head import block_core_features
        fam_key = "free" if head_scorer.family == "free" else "tel"
        s1_parts, s2_parts, se_parts = [], [], []
        for _pidx, z in sorted(rows.items()):
            zz = dict(z)
            if int(zz["n_blocks"]) < 2:
                continue
            cores = block_core_features(zz, fam_key)
            qs = np.asarray(zz["q_sig"], dtype=np.float64)
            for b in range(1, int(zz["n_blocks"])):
                a = [head_scorer.a_hat(cores[b], qs[b].tolist(), i)
                     for i in range(1, 6)]
                s1_parts.append(a[0])
                s2_parts.append(a[0] * a[1])
                se_parts.append(a[0] * a[1] * a[2] * a[3] * a[4])
        s1 = np.asarray(s1_parts, dtype=np.float64)
        s2 = np.asarray(s2_parts, dtype=np.float64)
        se = np.asarray(se_parts, dtype=np.float64)
        if s1.size == 0 or np.isnan(s1).any() or np.isnan(s2).any() or np.isnan(se).any():
            raise SystemExit("empty/NaN head materialization signals")
        stop_pairs = [(float(np.quantile(s1, lv)), float(np.quantile(s2, lv)))
                      for lv in QUANTILE_LEVELS]
        extend_vals = [float(np.quantile(se, lv)) for lv in QUANTILE_LEVELS]
        return {"stop_pairs": stop_pairs, "extend_vals": extend_vals,
                "n_consulting_blocks": int(s1.shape[0]),
                "signal_key": f"head:{head_scorer.family}"}
    key = ARM_SIGNAL_KEY[arm]
    s1_parts, s2_parts = [], []
    for _pidx, z in sorted(rows.items()):
        sig = z[key]
        if int(z["n_blocks"]) >= 2:
            s1_parts.append(sig[1:, 0])
            s2_parts.append(sig[1:, 1])
    s1 = np.concatenate(s1_parts).astype(np.float64)
    s2 = np.concatenate(s2_parts).astype(np.float64)
    if np.isnan(s1).any() or np.isnan(s2).any():
        raise SystemExit("NaN in the materialization signals — vanilla gamma-4 "
                         "blocks must always carry both consult positions")
    stop_pairs = [(float(np.quantile(s1, lv)), float(np.quantile(s2, lv)))
                  for lv in QUANTILE_LEVELS]
    extend_vals = [float(np.quantile(np.minimum(s1, s2), lv))
                   for lv in QUANTILE_LEVELS]
    return {"stop_pairs": stop_pairs, "extend_vals": extend_vals,
            "n_consulting_blocks": int(s1.shape[0]),
            "signal_key": key}


def main() -> None:  # pragma: no cover - GPU box entrypoint
    from sideband.real import require_real_deps

    torch, transformers = require_real_deps()
    from sideband.real.hf_specdec import (PINNED_DATE, _assert_gpu_resident,
                                          _atomic_write_text,
                                          spec_decode_prompt)
    from sideband.real.k3_live import (K3Config, build_live_reader,
                                       load_probe_weights)

    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", type=int, required=True, choices=(2, 3, 4, 6, 7))
    ap.add_argument("--val-run", default=str(REAL / "k3_val_arm1.jsonl"))
    ap.add_argument("--prompts", default="data/prompts.jsonl")
    ap.add_argument("--expect-seed", type=int, default=0,
                    help="the materialization run's seed (K-3: 0; "
                         "OQ-15 Stage C: 2 — STAGE-C FREEZE)")
    ap.add_argument("--eval-split", default="val", choices=["val", "none"],
                    help="prompt selection for the evals: K-3 uses the "
                         "val split of data/prompts.jsonl; Stage C uses "
                         "ALL lines of the fresh val file (none)")
    ap.add_argument("--head-weights", default=None,
                    help="frozen OQ-15 head-weights npz (arms 6/7 only)")
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
    ap.add_argument("--out", default=None,
                    help="default results/real/k3_threshold_search_arm{N}.json")
    ap.add_argument("--thresholds-out", default=None,
                    help="default results/real/k3_thresholds_arm{N}.json")
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    out_path = Path(args.out or REAL / f"k3_threshold_search_arm{args.arm}.json")
    thr_out = Path(args.thresholds_out or REAL / f"k3_thresholds_arm{args.arm}.json")
    state_path = Path(str(out_path) + ".state.jsonl")
    # Critic fix (2026-09-02): a completed search leaves its state file
    # in place forever (committed evidence), so the payload's existence
    # alone must refuse — crash-resume is the state-file-present,
    # payload-absent case and still works.
    if out_path.exists() and not args.overwrite:
        raise SystemExit(f"{out_path} exists — committed evidence; a completed "
                         "search is never silently re-run (--overwrite to redo "
                         "deliberately)")

    from sideband.real._preflight import preflight

    preflight_report = preflight(disk_path=out_path.resolve().anchor or ".",
                                 force=args.skip_preflight)

    # ---- val run bindings, B_ref freeze, materialization -----------------
    if ARM_KIND[args.arm] == "head" and not args.head_weights:
        raise SystemExit(f"arm {args.arm} needs --head-weights")
    if ARM_KIND[args.arm] != "head" and args.head_weights:
        raise SystemExit("--head-weights is a head-arm (6/7) argument only")
    meta_v, summary_v, byp_rows = load_val_run(
        Path(args.val_run), expect_seed=args.expect_seed,
        expect_split=args.eval_split)
    if _sha(args.prompts) != meta_v["prompts_sha256"]:
        raise SystemExit("prompts file sha != val run meta")
    head_scorer = None
    if ARM_KIND[args.arm] == "head":
        from sideband.outcome_head import HeadScorer
        head_scorer = HeadScorer(args.head_weights, ARM_HEAD_FAMILY[args.arm])
    b_ref = float(summary_v["drafted_per_emitted"])  # frozen at first read
    grids = materialize_grids(byp_rows, args.arm, head_scorer=head_scorer)
    grids_sha = hashlib.sha256(json.dumps(
        [grids["stop_pairs"], grids["extend_vals"]]).encode()).hexdigest()
    print(f"[search] arm {args.arm}: B_ref={b_ref:.6f} "
          f"({grids['n_consulting_blocks']} consulting blocks)", flush=True)

    # ---- models + instrument (one load; the eval loop reuses them) -------
    tok = transformers.AutoTokenizer.from_pretrained(meta_v["target"])
    target_kwargs: dict = {"device_map": "auto", "torch_dtype": torch.bfloat16}
    if args.load_4bit:
        target_kwargs["quantization_config"] = transformers.BitsAndBytesConfig(
            load_in_4bit=True, bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=torch.bfloat16)
    target = transformers.AutoModelForCausalLM.from_pretrained(
        meta_v["target"], **target_kwargs).eval()
    draft = transformers.AutoModelForCausalLM.from_pretrained(
        meta_v["draft"], torch_dtype=torch.bfloat16, device_map="auto").eval()
    _assert_gpu_resident(target, "target", args.allow_cpu_offload)
    _assert_gpu_resident(draft, "draft", args.allow_cpu_offload)
    want_load = "nf4-double-quant-bf16compute" if args.load_4bit else "bf16"
    if meta_v["target_load"] != want_load:
        raise SystemExit(f"load regime {want_load} != val run {meta_v['target_load']}")

    probes, pmeta = load_probe_weights(args.probe_weights)
    if meta_v.get("probe_weights_sha256") != pmeta["npz_sha256"]:
        raise SystemExit("--probe-weights is not the file the val run used")
    reader = None
    glue_class = int(pmeta["n_classes"]) - 1
    if args.arm in (3, 4, 6, 7):
        reader = build_live_reader(
            target, pmeta, probes,
            bucket_paths={"16": args.buckets16, "32": args.buckets32,
                          "64": args.buckets64, "512": args.buckets512},
            glue16_path=args.glue16, load_4bit=args.load_4bit,
            expect_target=meta_v["target"])

    lines = [json.loads(l)["prompt"]
             for l in Path(args.prompts).read_text().splitlines() if l.strip()]
    prompts = [p for i, p in enumerate(lines)
               if args.eval_split == "none" or split_of_prompt(i) == "val"]
    use_chat = meta_v["chat_template_used"] and tok.chat_template is not None

    def encode_prompt(p: str):
        if use_chat:
            return tok.apply_chat_template(
                [{"role": "user", "content": p}], add_generation_prompt=True,
                return_tensors="pt", date_string=PINNED_DATE)
        return tok(p, return_tensors="pt").input_ids

    enc_ids = [encode_prompt(p) for p in prompts]
    ids0_sha = hashlib.sha256(json.dumps(enc_ids[0][0].tolist()).encode()).hexdigest()
    if ids0_sha != meta_v["templated_prompt0_ids_sha256"]:
        # driver-gate carry #2: encoding must be the val run's encoding.
        raise SystemExit("prompt encoding sha != the val run's — tokenizer or "
                         "template drift; the materialization would not match")

    # ---- eval oracle with cache + state-file checkpoint ------------------
    header = {"kind": "state_header", "arm": args.arm, "b_ref": b_ref,
              "val_run_byproduct_sha256": summary_v["byproduct_sha256"],
              "prompts_sha256": meta_v["prompts_sha256"],
              "materialized_grids_sha256": grids_sha}
    cache: dict[tuple[int, int], dict] = {}
    if state_path.exists():
        slines = state_path.read_text().splitlines()
        h = json.loads(slines[0])
        if h != header:
            raise SystemExit("state file header mismatch (different B_ref, "
                             "grids, or val run) — delete it or fix inputs")
        for ln in slines[1:]:
            if ln.strip():
                try:
                    rec = json.loads(ln)
                except json.JSONDecodeError:
                    print("[resume] dropping torn final state line")
                    continue
                cache[(rec["stop_idx"], rec["extend_idx"])] = rec
        print(f"[resume] {len(cache)} evals already done", flush=True)
    else:
        with state_path.open("w") as f:
            f.write(json.dumps(header) + "\n")

    kind = ARM_KIND[args.arm]
    by_values: dict[tuple, tuple[int, int]] = {}
    for (si, ei), rec in cache.items():
        by_values.setdefault((tuple(rec["stop_values"]), rec["extend_value"]),
                             (si, ei))
    t0 = time.time()

    def eval_fn(si: int, ei: int) -> dict:
        if (si, ei) in cache:
            return cache[(si, ei)]
        stop_vals = grids["stop_pairs"][si]
        ext_val = grids["extend_vals"][ei]
        vkey = (tuple(stop_vals), ext_val)
        rec: dict
        if vkey in by_values and by_values[vkey] != (si, ei):
            src = cache[by_values[vkey]]
            rec = {**src, "stop_idx": si, "extend_idx": ei,
                   "stop_level": QUANTILE_LEVELS[si],
                   "extend_level": QUANTILE_LEVELS[ei],
                   "dedupe_of": f"s{by_values[vkey][0]}|e{by_values[vkey][1]}"}
        else:
            thr = Thresholds(kind=kind, stop_level=QUANTILE_LEVELS[si],
                             extend_level=QUANTILE_LEVELS[ei],
                             stop=(stop_vals[0], stop_vals[1]), extend=ext_val)
            policy = SchedulerPolicy(kind, gamma_base=4, gamma_max=6,
                                     thresholds=thr,
                                     probe_arm=ARM_PROBE.get(args.arm),
                                     glue_class=(glue_class if kind == "probe"
                                                 else None))
            gens = spawn(args.expect_seed, len(prompts))  # fresh per eval (carry #2)
            per_prompt = []
            t_eval = time.time()
            for i, ids in enumerate(enc_ids):
                cfg = K3Config(policy=policy, reader=reader, recorder=None,
                               head_scorer=head_scorer)
                _out, _r, st = spec_decode_prompt(
                    target, draft, ids, 4, args.max_new, 1.0, gens[i],
                    bucket_of_token=None, prompt_idx=i, use_kv_cache=True,
                    k3=cfg)
                per_prompt.append([st["n_emitted"], st["n_blocks"],
                                   st["n_drafted"], st["n_stop_blocks"],
                                   st["n_extend_blocks"]])
            arr = np.array(per_prompt, dtype=np.int64)
            rec = {"stop_idx": si, "extend_idx": ei,
                   "stop_level": QUANTILE_LEVELS[si],
                   "extend_level": QUANTILE_LEVELS[ei],
                   "stop_values": list(stop_vals), "extend_value": ext_val,
                   "tokens_per_call": float(arr[:, 0].sum() / arr[:, 1].sum()),
                   "budget": float(arr[:, 2].sum() / arr[:, 0].sum()),
                   "per_prompt": per_prompt,
                   "runtime_s": round(time.time() - t_eval, 1)}
        cache[(si, ei)] = rec
        by_values.setdefault(vkey, (si, ei))
        with state_path.open("a") as f:
            f.write(json.dumps(rec) + "\n")
            f.flush()
            os.fsync(f.fileno())
        print(f"[eval {len(cache)}] s{si}(q{QUANTILE_LEVELS[si]}) "
              f"e{ei}(q{QUANTILE_LEVELS[ei]}): t/c={rec['tokens_per_call']:.4f} "
              f"budget={rec['budget']:.4f}"
              f"{' (dedupe)' if 'dedupe_of' in rec else ''} "
              f"total {time.time() - t0:.0f}s", flush=True)
        return rec

    # ---- the registered procedure ---------------------------------------
    res = search_frontier(eval_fn, n_levels=len(QUANTILE_LEVELS), b_ref=b_ref)
    sel = select_thresholds(eval_fn, res["frontier"], b_ref)
    if sel["label"] == "FAILED_INFEASIBLE":
        si, ei = CORNER[args.arm]
        corner_rec = eval_fn(si, ei)
        sel = {"label": "FAILED_INFEASIBLE_CORNER", "stop_idx": si,
               "extend_idx": ei, "stop_level": QUANTILE_LEVELS[si],
               "extend_level": QUANTILE_LEVELS[ei],
               "tokens_per_call": corner_rec["tokens_per_call"],
               "budget": corner_rec["budget"],
               "note": ("comparability fallback OUTSIDE the constrained-max "
                        "frame (registration 2026-09-02); no feasibility "
                        "guarantee — the verdict-time pairwise budget guard "
                        "is the enforcement; B_ref itself is suspect "
                        "(named tripwire)")}

    def _git() -> str:
        import subprocess
        try:
            r = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                               text=True, timeout=10)
            d = subprocess.run(["git", "status", "--porcelain"],
                               capture_output=True, text=True, timeout=10)
            return (r.stdout.strip() or "unknown") + ("-dirty" if d.stdout.strip() else "")
        except Exception:
            return "unknown"

    payload = {
        "registered": "THRESHOLD-SEARCH REGISTRATION (BLUEPRINT 2026-09-02; "
                      "Amendment #1 objective/grid/tie-break; E5/E12 "
                      "materialization; driver-gate carries applied)",
        "arm": args.arm, "arm_kind": kind, "b_ref": b_ref,
        "quantile_levels": list(QUANTILE_LEVELS),
        "materialized": grids, "materialized_grids_sha256": grids_sha,
        "n_evals": len(cache),
        "evals": [cache[k] for k in sorted(cache)],
        "frontier": {str(s): e for s, e in sorted(res["frontier"].items())},
        "excluded_stop_levels": res["excluded"],
        "procedure_notes": ("warm start carries across EXCLUDED stop levels "
                            "from the last successful answer (the registration's "
                            "'previous stop level's result', read as the "
                            "previous ANSWERED level — deterministic and "
                            "arm-uniform; critic advisory disclosure); arm 2 "
                            "evals run reader-free (zero trajectory effect per "
                            "the containment rider's bit-identity)"),
        "selection": sel,
        "provenance": {
            "val_run": str(args.val_run),
            "val_run_byproduct_sha256": summary_v["byproduct_sha256"],
            "head_weights_sha256": _sha(args.head_weights) if args.head_weights else None,
            "probe_weights_sha256": pmeta["npz_sha256"],
            "prompts_sha256": meta_v["prompts_sha256"],
            "args": redact_args(vars(args)),
            "git_commit": _git(),
            "torch_version": torch.__version__,
            "preflight": preflight_report,
        },
        "runtime_s": round(time.time() - t0, 1),
    }
    _atomic_write_text(out_path, json.dumps(payload, indent=1, sort_keys=True))

    thr_payload = {
        "kind": kind, "arm": args.arm,
        "stop_level": sel["stop_level"], "extend_level": sel["extend_level"],
        "stop": list(grids["stop_pairs"][sel["stop_idx"]]),
        "extend": grids["extend_vals"][sel["extend_idx"]],
        "selection_label": sel["label"],
        "provenance": {"b_ref": b_ref, "search_payload": out_path.name,
                       "search_payload_sha256": _sha(out_path),
                       "materialized_grids_sha256": grids_sha,
                       "val_run": str(args.val_run)},
    }
    _atomic_write_text(thr_out, json.dumps(thr_payload, indent=1, sort_keys=True))
    if reader is not None:
        reader.close()
    print(f"[search] arm {args.arm}: {sel['label']} stop q{sel['stop_level']} "
          f"extend q{sel['extend_level']} t/c={sel['tokens_per_call']:.4f} "
          f"budget={sel['budget']:.4f} ({len(cache)} evals, "
          f"{payload['runtime_s']}s) -> {thr_out}")


if __name__ == "__main__":  # pragma: no cover
    main()
