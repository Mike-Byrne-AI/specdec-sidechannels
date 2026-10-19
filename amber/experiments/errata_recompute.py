#!/usr/bin/env python3
"""Errata recompute (experiments/ERRATA_PROTOCOL.md, rows E1-E14) -> results/errata_recompute.json.

Every value in the payload is computed here from sources committed at the
pinned commit (or, for E8c, from local dumps pinned by results/p2_dumps.sha256);
the decision rules are the protocol's, applied verbatim. The script refuses to
write on a dirty tracked tree (`--dry-run` prints instead). CPU only: torch is
blocked below before any import, and the payload records that flag. The
tokenizer is loaded for E7 only, offline.

    python experiments/errata_recompute.py            # writes results/errata_recompute.json
    python experiments/errata_recompute.py --dry-run  # prints the payload, writes nothing
"""

import sys

sys.modules["torch"] = None  # the protocol's CPU-only guard: any `import torch` now raises
import os  # noqa: E402

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import argparse  # noqa: E402
import glob  # noqa: E402
import inspect  # noqa: E402
import json  # noqa: E402
import platform  # noqa: E402
import re  # noqa: E402
import time  # noqa: E402
import urllib.request  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
RESULTS = REPO / "results"
sys.path.insert(0, str(REPO / "experiments"))
sys.path.insert(0, str(REPO / "tools"))

import errata_lib as L  # noqa: E402
import p1_divergence as P1  # noqa: E402  (amber_bits; D-1)
import p2b_escape_robustness as P2B  # noqa: E402  (simulate, rank_of_true; D-1)
import sha256_manifest as SM  # noqa: E402
from amber.real import archive as ARCHIVE  # noqa: E402
from amber.real.capture import load_arm, load_corpus  # noqa: E402
from amber.real.divergence import load_generated, load_rank  # noqa: E402
from amber.real.longhorizon import distinct_ngram_ratio, loop_fraction  # noqa: E402
from amber.rankcensus import canonical_topk  # noqa: E402

PROTOCOL = "experiments/ERRATA_PROTOCOL.md"
INPUTS = [
    "results/p1_divergence.json", "results/p1/generate", "results/p1/draft", "results/p4/encode_meta.json", "results/p4_real_archive.json",
    "results/p4/decode_cuda_fp32", "results/p4/decode_cpu_fp32", "results/p2b_escape_robustness.json",
    "results/p2_dumps.sha256", "src/amber/real/archive.py", "src/amber/real/divergence.py",
    "src/amber/real/longhorizon.py", "src/amber/real/capture.py", "src/amber/codec.py", "src/amber/binformat.py",
    "src/amber/rac_codec.py", "experiments/p1_divergence.py", "experiments/p2b_escape_robustness.py",
    "experiments/p4_real_archive.py", "FINDINGS.md", "DECISIONS.md", "OPEN_QUESTIONS.md", "README.md",
    "docs/BLUEPRINT.md", "docs/PRIOR_ART.md", "pyproject.toml", "experiments/P7_PROTOCOL.md", PROTOCOL,
    "experiments/errata_lib.py", "experiments/errata_recompute.py", "tools/sha256_manifest.py",
    # second batch (E15, E16)
    "results/p4/archives", "results/p4/decode_cuda_bf16", "results/p4/decode_cuda_fp16", "results/p2_llama32_rank_census.json",
    "src/amber/rac_codec.py", "src/amber/rankcensus.py", "results/errata_recompute.json", "results/errata_critic/REPORT.md",
    # third batch (E17, E18, E19)
    "results/p2_rank_census.json", "experiments/p2_rank_census.py", "results/p5_binformat.json", "results/p5/encode_meta.json",
    "results/p6_sessions.json", "results/p6/k8_m0", "results/p6/k16_m0", "experiments/p5_binformat.py", "experiments/p6_sessions.py",
    "results/errata_recompute_2.json", "results/errata_critic/c2_e15_gapsens.out.json", "results/p2_tinyllama_dumps.sha256",
]
BATCH2 = {"E15", "E16"}
BATCH3 = {"E17", "E18", "E19"}
E18_SIZES = (4096, 16384, 65536, 262144)
E18_PRIMARY = 16384
E18_SPLIT = 100                                   # rows below train the dictionaries; rows from here are held out
E19_BINNINGS = (("quantile", 20), ("quantile", 10), ("quantile", 50), ("log", 8), ("log", 16), ("log", 32), ("log", 64))
E15_ARMS = {"cuda_bf16_b1": "cuda_bf16", "cuda_fp16_b1": "cuda_fp16"}     # P2b decoder -> P4 arm (both batch 1)
E16_SCORED = ("cuda_fp32_b1", "cuda_fp32_b8")
E16_INFO = ("cuda_fp16_b1", "cuda_bf16_b1", "cuda_bf16_b8")
LOOP_W, LOOP_P, LOOP_T = 128, 64, 0.5     # E3 pinned setting
STALL_F = 0.25                            # E6 pinned factor
EOS, EOT = 128001, 128009                 # E2 pinned ids
BOMB = (1 << 24) + 1                      # E11: one past codec.DEFAULT_MAX_LENGTH
CONTROL = 3


def jload(rel: str):
    return json.loads((REPO / rel).read_text(encoding="utf-8"))


def row(claim, where, value, st, prediction, note=None):
    return {"claim": claim, "where": where, "value": value, "status": st, "prediction": prediction, "note": note}


# ----------------------------------------------------------------------------
# shared loads (each done once)
# ----------------------------------------------------------------------------


def load_p1():
    seqs = load_generated(RESULTS / "p1")                      # [(row, ids, prompt_len)]
    gen = {r: ids[pl:] for r, ids, pl in seqs}
    return seqs, gen


# ----------------------------------------------------------------------------
# rows
# ----------------------------------------------------------------------------


def e1():
    enc = jload("results/p4/encode_meta.json"); gmeta = jload("results/p1/generate/meta.json"); p1 = jload("results/p1_divergence.json")
    doc_lines = (REPO / "src/amber/real/archive.py").read_text(encoding="utf-8").splitlines()
    doc_line1 = doc_lines[0]
    src = (REPO / "experiments/p4_real_archive.py").read_text(encoding="utf-8")
    body = src[src.index("def encode_stage"):]
    m = re.search(r"load_model\(([^,)]+)", body)
    value = {"encode_meta_draft": enc["draft"], "encode_meta_model_id": enc["model"]["id"], "p1_generate_target": gmeta["target"],
             "p1_divergence_draft": p1["draft"], "p1_divergence_target": p1["target"],
             "archive_py_line1": doc_line1, "archive_py_line2": doc_lines[1], "p4_encode_stage_load_model_arg": m.group(1) if m else None}
    corrected = value["encode_meta_model_id"] == value["p1_divergence_draft"] and value["encode_meta_model_id"] != value["p1_divergence_target"]
    confirmed = value["encode_meta_model_id"] == value["p1_divergence_target"]
    st = "CORRECTED" if corrected else ("CONFIRMED" if confirmed else "UNRECOMPUTABLE")
    return row("compress with the target model, decode with the draft alone",
               ["README.md:3-4", "docs/BLUEPRINT.md:3-4", "pyproject.toml:8"], value, st,
               {"encoder": "the draft codes both ends; the target only generates"})


def e2(seqs, gen):
    gmeta = jload("results/p1/generate/meta.json"); max_new = int(gmeta["max_new"])
    lens = {r: int(len(g)) for r, g in gen.items()}
    value = {"n_rows": len(lens), "max_new": max_new, "n_cap": sum(1 for v in lens.values() if v == max_new),
             "n_eos": sum(1 for r, g in gen.items() if len(g) and int(g[-1]) == EOS),
             "n_eot": sum(1 for r, g in gen.items() if len(g) and int(g[-1]) == EOT),
             "min_gen": min(lens.values()), "n_empty": sum(1 for v in lens.values() if v == 0), "total_gen": sum(lens.values())}
    if max_new != 256:
        return row("193/200 prompts hit the 256 cap", ["FINDINGS.md:57"], value, "UNRECOMPUTABLE", {"n_cap": 186, "n_eos": 14}, "max_new != 256")
    ok = value["n_cap"] == 193 and value["min_gen"] == 21 and value["n_empty"] == 0
    return row("193/200 prompts hit the 256 cap, min 21, 0 empty", ["FINDINGS.md:57"], value, L.status(ok), {"n_cap": 186, "n_eos": 14})


def e3(seqs, gen):
    rows_ = [gen[r] for r, _, _ in seqs]
    pinned = L.loop_flags(rows_, loop_fraction, LOOP_W, LOOP_P, LOOP_T)
    total = sum(len(g) for g in rows_)
    num, den = L.repeat_4gram_share(rows_)
    value = {"W": LOOP_W, "P": LOOP_P, "t": LOOP_T, "n_rows": len(rows_), "n_looped": pinned["n_looped"],
             "tokens_in_loop": pinned["tokens_in_loop_total"], "total_gen": total,
             "tokens_in_loop_share": pinned["tokens_in_loop_total"] / total,
             "looped_rows": [int(r) for (r, _, _), f in zip(seqs, pinned["flags"]) if f],
             "periods_of_looped": sorted({p for p, f in zip(pinned["periods"], pinned["flags"]) if f}),
             "grid": L.loop_grid(rows_, loop_fraction),
             "distinct_4gram": L.distinct_ngram_stats(rows_, distinct_ngram_ratio, 4),
             "repeat_4gram_share": {"num": num, "den": den, "share": num / den if den else None}}
    corrected = value["n_looped"] >= 20 or value["tokens_in_loop"] >= 0.10 * total
    flags = {r: f for (r, _, _), f in zip(seqs, pinned["flags"])}
    return row("continuations are fluent", ["FINDINGS.md:60"], value, L.status(not corrected),
               {"n_looped": 125, "n_looped_range": [106, 138], "repeat_4gram_share": 0.708}), flags


def e4(seqs, gen, flags):
    draft = load_rank(RESULTS / "p1", "draft"); p1 = jload("results/p1_divergence.json")["row"]
    ranks = np.concatenate([p["rank"] for p in draft["per_prompt"]]); log2q = np.concatenate([p["log2q"] for p in draft["per_prompt"]])
    N = int(ranks.size)
    amber_all = P1.amber_bits(ranks) / N
    ac_all = float(-log2q.mean())                      # the instrument's own expression (float32 mean, p1_divergence.py:119)
    ac_all_f64 = float(-log2q.astype(np.float64).mean())
    check = {"N": N, "json_positions": p1["positions"], "amber_v0_recomputed": float(amber_all), "amber_v0_json": p1["amber_v0_bits_per_token"],
             "ac_recomputed_instrument_f32": ac_all, "ac_recomputed_f64": ac_all_f64, "ac_json": p1["ac_under_draft_bits_per_token"]}
    instrument_ok = (N == p1["positions"] and abs(amber_all - p1["amber_v0_bits_per_token"]) < 1e-9
                     and abs(ac_all - p1["ac_under_draft_bits_per_token"]) < 1e-9)
    pred = {"delta_concat_nonlooped": 0.0835, "delta_concat_looped": -0.0422,
            "harvest_wording": "per archive, amber trails AC-under-draft by 7-10% on non-looped rows (sign convention unclear; not scored)"}
    if not instrument_ok:
        return row("amber v0 0.4738 ties AC-under-draft 0.4723", ["FINDINGS.md:59"], {"instrument_check": check}, "UNRECOMPUTABLE", pred, "instrument mismatch")
    strata = L.stratified_rates([(p["rank"], p["log2q"], bool(flags[p["row"]])) for p in draft["per_prompt"]], P1.amber_bits)
    s_l, s_n = strata["looped"], strata["nonlooped"]
    corrected = (np.sign(s_l["delta_concat"]) != np.sign(s_n["delta_concat"])) or abs(s_n["rel_perarchive"]) > 0.02
    # informational (post-critic): the same strata at every loop-grid setting
    per_row = {p["row"]: (p["rank"], p["log2q"]) for p in draft["per_prompt"]}
    rows_ = [gen[r] for r, _, _ in seqs]; ids = [r for r, _, _ in seqs]; grid = []
    for W, Pp, t in L.grid_settings():
        fl = L.loop_flags(rows_, loop_fraction, W, Pp, t)["flags"]
        sg = L.stratified_rates([(per_row[r][0], per_row[r][1], bool(f)) for r, f in zip(ids, fl)], P1.amber_bits)
        grid.append({"W": W, "P": Pp, "t": t, "n_looped": sg["looped"]["rows"],
                     "delta_concat_looped": sg["looped"].get("delta_concat"), "delta_concat_nonlooped": sg["nonlooped"].get("delta_concat"),
                     "rel_perarchive_nonlooped": sg["nonlooped"].get("rel_perarchive"), "rel_perarchive_looped": sg["looped"].get("rel_perarchive")})
    ok_grid = [g for g in grid if g["delta_concat_looped"] is not None and g["delta_concat_nonlooped"] is not None]
    rel = [g["rel_perarchive_nonlooped"] for g in ok_grid]
    grid_summary = {"settings": len(grid), "sign_split_holds_at": sum(1 for g in ok_grid if np.sign(g["delta_concat_looped"]) != np.sign(g["delta_concat_nonlooped"])),
                    "rel_perarchive_nonlooped_min": min(rel), "rel_perarchive_nonlooped_max": max(rel),
                    "rel_perarchive_nonlooped_positive_at": sum(1 for x in rel if x > 0)}
    r = row("amber v0 0.4738 ties AC-under-draft 0.4723 bits/token (within 0.0015)", ["FINDINGS.md:59"],
            {"instrument_check": check, "strata": strata, "grid": grid, "grid_summary": grid_summary}, L.status(not corrected), pred)
    r["status_under_pinned_rule"] = "UNRECOMPUTABLE"
    r["amended_by"] = "E4 amendment, 2026-10-10, written after the first dry run showed the float64 miss (instrument's float32 mean)"
    return r


def e5():
    sh = jload("results/p1/generate/meta.json")["shards"]
    stats = L.rate_stats([s["new_tokens"] for s in sh.values()], [s["seconds"] for s in sh.values()])
    stats["unweighted_from_tok_per_s"] = float(np.mean([s["tok_per_s"] for s in sh.values()]))
    matches = [k for k in ("weighted", "unweighted", "median") if L.rounds_to(stats[k], "32.8", 1)]
    stats["definitions_rounding_to_32_8"] = matches
    return row("target generation 32.8 tok/s", ["FINDINGS.md:59"], stats, L.status("weighted" in matches),
               {"unweighted": 32.8, "weighted": 25.0})


def e6():
    enc = jload("results/p4/encode_meta.json"); pr = enc["per_row"]
    keys = sorted(pr, key=int)
    lengths = [pr[k]["length"] for k in keys]; secs = [pr[k]["score_seconds"] for k in keys]
    pinned = L.stall_split(lengths, secs, STALL_F)
    pinned["stalled_rows"] = [int(keys[i]) for i in pinned["stalled_rows"]]
    pinned["stalled_row_seconds"] = {str(keys[i]): secs[i] for i in range(len(keys)) if int(keys[i]) in pinned["stalled_rows"]}
    value = {"encode_pos_per_s_json": enc["encode_pos_per_s"], "pinned": pinned,
             "grid": [{k: v for k, v in L.stall_split(lengths, secs, f).items() if k != "stalled_rows"} for f in (0.1, 0.25, 0.5)]}
    pred = {"n_stalled": 15, "seconds_stalled": 36.3, "seconds_total": 49.4, "clean": 4200}
    if abs(pinned["aggregate"] - enc["encode_pos_per_s"]) > 1e-9:
        return row("991 pos/s teacher-forced encode", ["FINDINGS.md:78", "FINDINGS.md:80"], value, "UNRECOMPUTABLE", pred, "aggregate != encode_pos_per_s")
    ok = L.rounds_to(pinned["aggregate"], "991", 0) and pinned["clean"] < 1.5 * pinned["aggregate"]
    return row("991 pos/s teacher-forced encode (incl. rank/top-k extraction)", ["FINDINGS.md:78", "FINDINGS.md:80"], value, L.status(ok), pred)


def e7(seqs, gen):
    import zstandard

    from amber.real.capture import _load_tokenizer
    enc = jload("results/p4/encode_meta.json"); model_id = enc["draft"]
    pred = {"b": 6.75, "bot_literal_bytes_per_archive": 17, "n_rows_with_eot": 14}
    try:
        from huggingface_hub import try_to_load_from_cache
        tj = try_to_load_from_cache(model_id, "tokenizer.json")
        tj_path = Path(tj) if isinstance(tj, str) else None
        if tj_path is None or not tj_path.exists():
            raise FileNotFoundError(f"tokenizer.json for {model_id} is not in the local HF cache")
        # amendment 2026-10-10: transformers 4.57 contacts the Hub for a repo id even with local_files_only=True
        # (_patch_mistral_regex -> model_info), so the same loader is pointed at the cached snapshot directory.
        tok = _load_tokenizer(str(tj_path.parent))
    except Exception as e:  # noqa: BLE001
        return row("zstd-19 per archive 7.28 bits/generated token", ["FINDINGS.md:80", "OPEN_QUESTIONS.md:31"],
                   {"error": f"{type(e).__name__}: {e}"}, "UNRECOMPUTABLE", pred, "tokenizer unavailable offline")
    z = zstandard.ZstdCompressor(level=19)
    n_tok = sum(len(g) for g in gen.values())
    bytes_a = bytes_b = literal = 0; n_bot = n_eot = 0
    for r, ids, pl in seqs:
        ta = tok.decode(ids.tolist()); tb = tok.decode(ids.tolist(), skip_special_tokens=True)
        ea, eb = ta.encode("utf-8"), tb.encode("utf-8")
        bytes_a += len(z.compress(ea)); bytes_b += len(z.compress(eb)); literal += len(ea) - len(eb)
        n_bot += "<|begin_of_text|>" in ta; n_eot += "<|end_of_text|>" in ta
    value = {"model_id": model_id, "tokenizer_json": str(tj_path), "tokenizer_loaded_from": str(tj_path.parent),
             "snapshot": tj_path.parent.name, "tokenizer_json_sha256": L.sha256_bytes(tj_path.read_bytes()),
             "zstandard_version": zstandard.__version__, "n_rows": len(seqs), "n_tok": n_tok,
             "a_as_printed": 8 * bytes_a / n_tok, "b_skip_special": 8 * bytes_b / n_tok, "bytes_a": bytes_a, "bytes_b": bytes_b,
             "literal_bytes": literal, "n_rows_with_bot": n_bot, "n_rows_with_eot": n_eot}
    r = row("zstd-19 on the full text per archive: 7.28 bits per generated token", ["FINDINGS.md:80", "OPEN_QUESTIONS.md:31"],
            value, L.status(L.rounds_to(value["a_as_printed"], "7.28", 2)), pred)
    r["status_under_pinned_rule"] = "UNRECOMPUTABLE"
    r["amended_by"] = "E7 amendment, 2026-10-10, written after the first dry run could not load the tokenizer offline (loaded from the cached snapshot dir)"
    return r


def _theta_row(rows_, theta, m):
    for r in rows_:
        if r["theta"] == theta and r["m"] == m:
            return r
    raise KeyError((theta, m))


def e8a():
    b = jload("results/p2b_escape_robustness.json"); rows_ = b["report"]["cpu_fp32"]["decoders"]["cuda_fp32_b1"]
    r0 = _theta_row(rows_, 0.0, 2)
    value = {"n": r0["n"], "desync_total_theta0": r0["desync_total"], "desyncs_theta0": r0["desyncs"],
             "A_desync_gap_max_theta0": r0["A_desync_gap"]["max"],
             "desync_total_by_theta_m": {f"{r['theta']}/{r['m']}": r["desync_total"] for r in rows_},
             "desync_total_escape_on": sum(r["desync_total"] for r in rows_ if r["theta"] > 0)}
    ok = value["desync_total_theta0"] == 0 and value["n"] == 49056
    r = row("0 desyncs / 49k positions / all ranks to 64 (fp32-class decoder, F-10 headline)",
            ["FINDINGS.md:69", "README.md:34", "OPEN_QUESTIONS.md:14"], value, L.status(ok), {"desync_total_theta0": 1, "gap": 1.3e-5})
    # per claim site (second critic pass): the headline's regime is the escape-on setting its body states; README reads as the
    # shipped theta 0 contract; OQ-2 is an ORDER claim, filled in from E8c's order-difference count by finalize_e8a
    r["status_by_claim_site"] = {"FINDINGS.md:69 (F-10 headline; its body states the escape-on regime)": L.status(value["desync_total_escape_on"] == 0),
                                 "README.md:34 (the shipped theta 0 contract)": L.status(value["desync_total_theta0"] == 0),
                                 "OPEN_QUESTIONS.md:14 (an order claim)": "UNRECOMPUTABLE"}
    r["note"] = ("F-10's body states 1 desync at theta 0 and 0 at theta >= 0.142; the headline, README and OQ-2 read as the shipped theta 0; "
                 "the resolved token is stable only at batch 1 with the escape on, and the top-64 order is not stable at any theta (E8c)")
    return r


def finalize_e8a(r8a: dict, r8c: dict) -> None:
    od = (r8c.get("value") or {}).get("order_differences_vs_cpu_fp32")
    if od:
        r8a["status_by_claim_site"]["OPEN_QUESTIONS.md:14 (an order claim)"] = L.status(od["cuda_fp32_b1"]["positions_top64_order_differs"] == 0)


def e8b():
    value = {}; fails = 0; positions = 0
    for arm in ("cuda_fp32", "cpu_fp32"):
        first, ndec = [], []
        for f in sorted(glob.glob(str(RESULTS / "p4" / f"decode_{arm}" / "shard_*.npz"))):
            with np.load(f) as zf:
                first += zf["first"].tolist(); ndec += zf["n_decoded"].tolist()
        a = {"n_rows": len(first), "n_fail": int(sum(1 for x in first if x >= 0)), "positions": int(sum(ndec))}
        value[arm] = a; fails += a["n_fail"]; positions += a["positions"]
    value["n_fail_total"] = fails; value["positions_total"] = positions
    p4 = jload("results/p4_real_archive.json")["report"]            # F-11's own source (post-critic cross-check)
    value["p4_real_archive_report"] = {"content_tokens": p4["content_tokens"], "arms": {k: p4["arms"][k] for k in ("cuda_fp32", "cpu_fp32")}}
    ok = fails == 0 and 54500 <= positions < 55500
    return row("0 desyncs / 55k positions (D-8 verification, F-11 decode); cpu_fp32: 24/24 (5,900 positions)", ["DECISIONS.md:100", "FINDINGS.md:80"],
               value, L.status(ok), {"n_fail_total": 0, "positions_total": 54858},
               "the rule scores the 55k figure only; F-11:80's CPU count is printed rounded to the hundred and the recomputed count is value.cpu_fp32.positions")


def e8c():
    pred = {"desync_total": 1, "swap": "rank 4/5", "per_position_two_arms": "2/98112"}
    where = ["FINDINGS.md:69 (fp32-class decoders are clean, extended to cuda_fp32_b8)"]
    prefixes = ("results/p2_llama32/corpus", "results/p2_llama32/cpu_fp32/", "results/p2_llama32/cuda_fp32_b8/", "results/p2_llama32/cuda_fp32_b1/")
    rows_m = [(d, rel) for d, rel in SM.parse_manifest((REPO / "results/p2_dumps.sha256").read_text(encoding="utf-8")) if rel.startswith(prefixes)]
    problems = []
    for d, rel in rows_m:
        p = REPO / rel
        if not p.is_file():
            problems.append(f"MISSING {rel}")
        elif SM.sha256_file(p) != d:
            problems.append(f"MISMATCH {rel}")
    if problems or not rows_m:
        return row("fp32-class decoders clean at batch 8", where, {"manifest_checked": len(rows_m), "problems": problems}, "UNRECOMPUTABLE", pred, "dumps missing or changed")
    out = RESULTS / "p2_llama32"
    tokens, cmeta = load_corpus(out)
    true = tokens[:, 1:].reshape(-1).astype(np.int64); Lseq = tokens.shape[1]
    keep = np.ones(tokens.shape[0] * Lseq, bool); keep[Lseq - 1::Lseq] = False
    arms = {}
    for name in ("cpu_fp32", "cuda_fp32_b8", "cuda_fp32_b1"):
        idx, val, _ = load_arm(out, name); idx, val = canonical_topk(idx, val); arms[name] = (idx[keep], val[keep])
    eidx, eval_ = arms["cpu_fp32"]; didx, _ = arms["cuda_fp32_b8"]
    sim = P2B.simulate(eidx, eval_, didx, true, 0.0, 2)
    # per-position mask with the same theta-0 resolution rules, to name each desync
    r_enc = P2B.rank_of_true(eidx, true); resolved = true.copy()
    a = r_enc == 1; resolved[a] = didx[a, 0]
    c = (r_enc >= 2) & (r_enc <= P2B.R_MAX); resolved[c] = didx[c, r_enc[c] - 1]
    desync = resolved != true; pos = np.flatnonzero(desync)
    r_dec = P2B.rank_of_true(didx, true)
    events = [{"position": int(t), "sequence": int(t // (Lseq - 1)), "offset": int(t % (Lseq - 1)), "enc_rank_of_true": int(r_enc[t]),
               "dec_rank_of_true": int(r_dec[t]), "enc_gap_top1_top2": float(eval_[t, 0] - eval_[t, 1]),
               "enc_gap_at_swapped_pair": float(eval_[t, r_enc[t] - 1] - eval_[t, r_enc[t]]) if r_enc[t] < eidx.shape[1] else None} for t in pos]
    b = jload("results/p2b_escape_robustness.json")
    persistence = {f"{th}/{m}": P2B.simulate(eidx, eval_, didx, true, th, m)["desync_total"]
                   for th in b["thetas"] for m in (b["ms"] if th > 0 else [2])}

    def order_diff(dec_name):                           # positions whose top-64 ORDER differs (not desyncs)
        R_ = P2B.R_MAX; d_idx = arms[dec_name][0]; neq = eidx[:, :R_] != d_idx[:, :R_]; diff = neq.any(1); p = np.flatnonzero(diff)
        min_adj = (-np.diff(eval_[p, :R_], axis=1)).min(1) if p.size else np.zeros(0)
        # the two tokens competing for the first differing slot: the encoder's value difference between them is the near-tie
        j = neq[p].argmax(1) if p.size else np.zeros(0, int); tok_d = d_idx[p, j]
        hit = eidx[p] == tok_d[:, None]; found = hit.any(1); k = hit.argmax(1)
        gap_pair = np.abs(eval_[p, j] - eval_[p, k])[found] if p.size else np.zeros(0)
        return {"positions_top64_order_differs": int(diff.sum()),
                "max_over_those_of_min_adjacent_gap_in_top64": float(min_adj.max()) if p.size else None,
                "max_encoder_gap_between_tokens_competing_for_first_differing_slot": float(gap_pair.max()) if gap_pair.size else None,
                "competing_token_outside_encoder_top256": int((~found).sum()) if p.size else 0}
    value = {"manifest_checked": len(rows_m), "corpus_sha256": cmeta["corpus_sha256"], "n": sim["n"], "desync_total": sim["desync_total"],
             "desyncs": sim["desyncs"], "C_desync_by_rank_2_8": {str(r): sim["C_desync_by_rank"][str(r)] for r in range(2, 9)},
             "mask_desync_total": int(desync.sum()), "events": events, "desync_total_by_theta_m": persistence,
             "order_differences_vs_cpu_fp32": {d: order_diff(d) for d in ("cuda_fp32_b1", "cuda_fp32_b8")}}
    note = None if int(desync.sum()) == sim["desync_total"] else "mask total != simulate total"
    return row("fp32-class decoders clean at batch 8 (cpu_fp32 -> cuda_fp32_b8, theta 0)", where, value, L.status(sim["desync_total"] == 0), pred, note)


def e9():
    b = jload("results/p2b_escape_robustness.json"); tables = {}; rank2_by_theta_m = {}
    for enc, rep in b["report"].items():
        tables[enc] = {dec: L.depth_table(_theta_row(rows_, 0.0, 2)) for dec, rows_ in rep["decoders"].items()}
        # informational (amendment 2026-10-10): rank-2 under every escape setting; the escape only touches ranks <= m
        rank2_by_theta_m[enc] = {dec: {f"{r['theta']}/{r['m']}": L.depth_table(r)["primary"]["2"] for r in rows_}
                                 for dec, rows_ in rep["decoders"].items()}
    pct = lambda v, nd: f"{100 * v:.{nd}f}"  # noqa: E731

    def checks_for(bf, fp):                                   # F-10's printed figures against a (bf16, fp16) depth-table pair
        return {
            "bf16_rank2_2.7": pct(bf["primary"]["2"], 1) == "2.7", "bf16_rank3_9.3": pct(bf["primary"]["3"], 1) == "9.3",
            "bf16_rank4_15.3": pct(bf["primary"]["4"], 1) == "15.3", "bf16_rank8_25.6": pct(bf["primary"]["8"], 1) == "25.6",
            "bf16_17-64_60": pct(bf["buckets"]["17-64"]["primary"], 0) == "60",
            "fp16_rank2_0.4": pct(fp["primary"]["2"], 1) == "0.4", "fp16_rank3_1.5": pct(fp["primary"]["3"], 1) == "1.5",
            "fp16_rank8_3.7": pct(fp["primary"]["8"], 1) == "3.7", "fp16_17-64_14": pct(fp["buckets"]["17-64"]["primary"], 0) == "14",
            "headline_rank2_3pct": pct(bf["primary"]["2"], 0) == "3",
            "headline_rank3-8_9-26": (min(round(100 * bf["primary"][str(r)]) for r in range(3, 9)) == 9
                                      and max(round(100 * bf["primary"][str(r)]) for r in range(3, 9)) == 26),
        }
    checks = checks_for(tables["cpu_fp32"]["cuda_bf16_b1"], tables["cpu_fp32"]["cuda_fp16_b1"])
    # post-critic: the same checks at every theta/m row, to identify the regime the printed table came from
    dec = b["report"]["cpu_fp32"]["decoders"]
    bf_rows = {f"{r['theta']}/{r['m']}": r for r in dec["cuda_bf16_b1"]}; fp_rows = {f"{r['theta']}/{r['m']}": r for r in dec["cuda_fp16_b1"]}
    checks_by_theta_m = {k: checks_for(L.depth_table(bf_rows[k]), L.depth_table(fp_rows[k])) for k in bf_rows if k in fp_rows}
    claim_regime_rows = [k for k, c in checks_by_theta_m.items() if all(c.values())]
    printed_rank2_matches = [k for k, c in checks_by_theta_m.items() if c["bf16_rank2_2.7"] and c["fp16_rank2_0.4"]]
    value = {"tables": tables, "printed_figure_checks": checks, "rank2_by_theta_m": rank2_by_theta_m,
             "theta_m_matching_printed_rank2": printed_rank2_matches, "checks_by_theta_m": checks_by_theta_m,
             "claim_regime_rows": claim_regime_rows,
             "tables_claim_regime": {k: {d: L.depth_table(_theta_row(dec[d], float(k.split("/")[0]), int(k.split("/")[1]))) for d in dec} for k in claim_regime_rows}}
    r = row("depth table: 3% of rank-2 and 9-26% of rank-3..8 (bf16); body per-rank figures", ["FINDINGS.md:69"], value,
            L.status(all(checks.values())), {"bf16_top1": 0.0063, "bf16_rank2": 0.060, "bf16_17_64": 0.598, "fp32": "1/49056 per arm"})
    r["status_in_claim_regime"] = L.status(bool(claim_regime_rows))
    r["note"] = ("protocol defect: the pinned rule checks the printed table at theta 0; F-10 does not state its theta and every printed figure "
                 "matches the row(s) listed in claim_regime_rows")
    return r


def e10():
    sh = jload("results/p1/draft/meta.json")["shards"]; p1 = jload("results/p1_divergence.json")["row"]
    stats = L.rate_stats([s["positions"] for s in sh.values()], [s["seconds"] for s in sh.values()])
    value = {"draft_scoring": stats, **{k: p1[k] for k in ("content_bytes_per_token", "amber_v0_bits_per_token", "ac_under_draft_bits_per_token",
                                                            "zstd19_bits_per_token", "positions", "divergence_rate")}}
    ok = 9150 <= stats["weighted"] < 9250 and L.rounds_to(p1["content_bytes_per_token"], "4.73", 2)
    return row("draft rank scoring 9.2k positions/s; 4.73 bytes/token (lockstep F-14's inputs)", ["FINDINGS.md:57", "FINDINGS.md:59"],
               value, L.status(ok), {"weighted": 9233, "content_bytes_per_token": 4.7277})


def e11():
    paths = {"hf_json": (L.craft_hf_json, ARCHIVE.decode_archive), "v3": (L.craft_v3, ARCHIVE.decode_binary_archive),
             "v4": (L.craft_v4, ARCHIVE.decode_session_archive)}
    value = {"bomb_length": BOMB, "control_length": CONTROL, "bomb": {}, "control": {}}
    for name, (craft, dec) in paths.items():
        value["control"][name] = L.probe(dec, craft(CONTROL), ARCHIVE)
        value["bomb"][name] = L.probe(dec, craft(BOMB), ARCHIVE)
    pred = {"hf_json": "refused", "v3": "work_started", "v4": "work_started"}
    if any(v["outcome"] != "work_started" for v in value["control"].values()):
        return row("declared-length ceiling checked before any replay", ["FINDINGS.md:31"], value, "UNRECOMPUTABLE", pred, "control did not reach work")
    ok = all(v["outcome"] == "refused" for v in value["bomb"].values())
    return row("declared-length ceiling (default 2^24) checked BEFORE any replay, on every decode path", ["FINDINGS.md:31"], value, L.status(ok), pred)


def e12():
    from amber.codec import attest_with_target
    src = inspect.getsource(attest_with_target)
    files = [REPO / p for p in ("experiments/p4_real_archive.py", "experiments/p5_binformat.py", "experiments/p6_sessions.py")]
    files += sorted((REPO / "src/amber/real").glob("*.py"))
    wide = sorted(str(p.relative_to(REPO)).replace("\\", "/") for d in ("src", "experiments", "tools", "tests")
                  for p in (REPO / d).rglob("*.py") if "attest" in p.read_text(encoding="utf-8"))
    value = {"synthetic_keys_in_HF_REQUIRED": sorted({"cfg", "path_seed", "draft_seed"} & set(ARCHIVE.HF_REQUIRED)),
             "attest_lines_in_real_paths": L.count_lines_containing(files, "attest"),
             "payload_lines_in_attest_with_target": sum(1 for ln in src.splitlines() if "payload" in ln),
             "files_searched": [str(f.relative_to(REPO)).replace("\\", "/") for f in files],
             "files_mentioning_attest_anywhere": wide}
    corrected = not value["synthetic_keys_in_HF_REQUIRED"] and value["attest_lines_in_real_paths"] == 0
    return row("'attesting' (README/BLUEPRINT/pyproject) read onto real archives; F-2's L1 is synthetic",
               ["README.md:3-4", "docs/BLUEPRINT.md:3-4", "pyproject.toml:8", "FINDINGS.md:13"], value, L.status(not corrected),
               {"synthetic_keys_in_HF_REQUIRED": [], "attest_lines_in_real_paths": 0, "payload_lines": 0})


def e13(dry_run: bool):
    import tempfile
    out = Path(tempfile.mkdtemp(prefix="errata_web_")) if dry_run else RESULTS / "errata_web"
    out.mkdir(exist_ok=True)
    pages = {}
    for aid in ("2601.17684", "2601.10678"):
        url = f"https://arxiv.org/abs/{aid}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "amber-errata-recompute/1.0 (local research; contact via repo)"})
            t0 = time.time()
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read()
            p = out / f"arxiv_{aid}.html"; p.write_bytes(data)
            meta = L.parse_arxiv_meta(data.decode("utf-8", errors="replace"))
            pages[aid] = {"url": url, "file": f"results/errata_web/arxiv_{aid}.html", "sha256": L.sha256_bytes(data), "bytes": len(data),
                          "fetched_unix": int(t0), **meta}
        except Exception as e:  # noqa: BLE001
            pages[aid] = {"url": url, "error": f"{type(e).__name__}: {e}"}
    pred = {"pmatic_id": "2601.10678", "authors": ["Adler", "Tang"]}
    if any("error" in p for p in pages.values()):
        return row("PMATIC is arXiv 2601.17684", ["docs/PRIOR_ART.md:10"], pages, "UNRECOMPUTABLE", pred, "fetch failed")
    in_title = {aid: bool(p.get("title")) and "pmatic" in p["title"].lower() for aid, p in pages.items()}
    # amendment 2026-10-10: the name is in the abstract, not the title; the rule keys on citation_abstract
    in_abstract = {aid: bool(p.get("abstract")) and "pmatic" in p["abstract"].lower() for aid, p in pages.items()}

    def decide(has):
        return "CONFIRMED" if has["2601.17684"] else ("CORRECTED" if has["2601.10678"] else "UNRECOMPUTABLE")
    st = decide(in_abstract)
    r = row("PMATIC is arXiv 2601.17684", ["docs/PRIOR_ART.md:10"],
            {"pages": pages, "title_contains_pmatic": in_title, "abstract_contains_pmatic": in_abstract}, st, pred,
            None if st != "UNRECOMPUTABLE" else "neither abstract contains PMATIC")
    r["status_under_pinned_rule"] = decide(in_title)
    r["amended_by"] = "E13 amendment, 2026-10-10, written after the fetched pages were read (citation_abstract instead of citation_title)"
    return r


def e14():
    tracked = L.git(REPO, "ls-files", "results/p7")
    value = {"results_p7_on_disk": (RESULTS / "p7").exists(), "results_p7_tracked_files": len(tracked.splitlines()) if tracked else 0,
             "results_p7_longhorizon_json_on_disk": (RESULTS / "p7_longhorizon.json").exists()}
    value["ran"] = value["results_p7_on_disk"] or value["results_p7_tracked_files"] > 0 or value["results_p7_longhorizon_json_on_disk"]
    return row("P7 pre-registration frozen 2026-08-30 (no GPU stage ran; withdraw)", ["experiments/P7_PROTOCOL.md:1-3"], value,
               L.status(not value["ran"]), {"ran": False}, "action: dated withdrawal line in experiments/P7_PROTOCOL.md")


# ----------------------------------------------------------------------------
# second batch (protocol amendment of 2026-10-10, "second batch")
# ----------------------------------------------------------------------------


def _manifest_problems(prefixes, manifest: str = "results/p2_dumps.sha256") -> tuple[int, list[str]]:
    rows_m = [(d, rel) for d, rel in SM.parse_manifest((REPO / manifest).read_text(encoding="utf-8")) if rel.startswith(prefixes)]
    problems = []
    for d, rel in rows_m:
        p = REPO / rel
        if not p.is_file():
            problems.append(f"MISSING {rel}")
        elif SM.sha256_file(p) != d:
            problems.append(f"MISMATCH {rel}")
    return len(rows_m), problems


def _p4_streams():
    """The P4 archives' own symbol streams, by row: the coded rank per position (A -> 1, C -> rank, X -> R_MAX + 1),
    the flag and the encoder's top-2 gap."""
    from amber.rac_codec import FLAG_A, FLAG_C, FLAG_NAMES, FLAG_X
    files = sorted((RESULTS / "p4" / "archives").glob("row_*_symbols.npz"))
    totals = {n: 0 for n in FLAG_NAMES}; recs = {}; consistent = True
    for f in files:
        rowid = int(re.search(r"row_(\d+)_symbols", f.name).group(1))
        with np.load(f) as z:
            fl = z["flag"].astype(int); rk = z["rank"].astype(np.int64); gp = z["gap"].astype(np.float64)
        for i, n in enumerate(FLAG_NAMES):
            totals[n] += int((fl == i).sum())
        consistent &= bool(((fl != FLAG_A) | (rk == 1)).all() and ((fl != FLAG_C) | ((rk >= 2) & (rk <= L.R_MAX))).all()
                           and ((fl != FLAG_X) | (rk > L.R_MAX)).all())
        recs[rowid] = {"ranks": np.where(fl == FLAG_X, L.R_MAX + 1, rk), "flags": fl, "gaps": gp}
    return files, totals, recs, consistent


def e15():
    from amber.rac_codec import FLAG_A
    p4full = jload("results/p4_real_archive.json"); p4 = p4full["report"]; p1 = jload("results/p1_divergence.json")
    b = jload("results/p2b_escape_robustness.json"); dec = b["report"]["cpu_fp32"]["decoders"]; xb3 = b["xb3_wide_gap_check"]
    cens = jload("results/p2_llama32_rank_census.json")
    claim_regime = jload("results/errata_recompute.json")["rows"]["E9"]["value"]["claim_regime_rows"]   # E9's finding, read not typed
    where = ["FINDINGS.md:72", "FINDINGS.md:76", "FINDINGS.md:85", "docs/BLUEPRINT.md:57"]
    claim = ("one desync per ~170 target-generated tokens (F-10 headline; item (4): fp16 1/1070, bf16 1/170) and F-11's caveat "
             "that target-generated corrections are slightly MORE fragile than the dumps' mix")
    # the critic's values (REPORT.md first pass item 13; it weighted by the P1 ranks, h1) and this protocol's own
    pred = {"bf16_all_theta0_one_in_h1": 77, "fp16_all_theta0_one_in_h1": 502,
            "bf16_claim_regime_one_in": 170, "fp16_claim_regime_one_in": 1070,
            "bf16_fail_poisson_claim_regime_pct": 76, "fp16_fail_poisson_claim_regime_pct": 20}
    pred_sources = {k: ("the critic (results/errata_critic/REPORT.md, first pass item 13)" if "all_theta0" in k
                        else "this protocol (second-batch entry)") for k in pred}
    f11_printed = {"cuda_bf16_b1": 65, "cuda_fp16_b1": 670}          # F-11's "1 desync per 65 decoded tokens", "1 per 670 tokens" (FINDINGS.md:84), quoted
    if b["R_max"] != L.R_MAX or p4.get("archives") is None:
        return row(claim, where, {"R_max": b["R_max"]}, "UNRECOMPUTABLE", pred, "R_max mismatch")
    # regime check: the archives' own streams were coded with the escape off
    files, totals, recs, consistent = _p4_streams(); streams = [recs[k]["ranks"] for k in sorted(recs)]
    regime = {"archives": len(files), "flag_totals": totals, "positions": int(sum(len(s) for s in streams)),
              "content_tokens_json": p4["content_tokens"], "class_rank_consistent": consistent,
              # post-critic: the two sides of the comparison, as the JSONs record them
              "sides": {"p2b": {"model": b["model"], "snapshot": cens["provenance"]["cpu_fp32"]["snapshot"], "regime": b["regime"],
                                "census_regime": cens["regime"]},
                        "p4": {"draft": p4full["draft"], "model": p4full["model"], "regime": p4full["regime"]}}}
    regime["ok"] = totals["T"] == 0 and regime["positions"] == p4["content_tokens"] and consistent and len(files) == p4["archives"]
    # instrument checks
    draft = load_rank(RESULTS / "p1", "draft"); ranks1 = np.concatenate([p["rank"] for p in draft["per_prompt"]]).astype(np.int64)
    div = float((ranks1 != 1).mean())
    shards = {}; exposures = {}
    for D, arm in E15_ARMS.items():
        first, ndec, rws = [], [], []
        for f in sorted(glob.glob(str(RESULTS / "p4" / f"decode_{arm}" / "shard_*.npz"))):
            with np.load(f) as zf:
                first += zf["first"].tolist(); ndec += zf["n_decoded"].tolist(); rws += zf["row"].tolist()
        fails = sum(1 for x in first if x >= 0)
        shards[arm] = {"archives": len(first), "fails": fails, "n_decoded_total": int(sum(ndec)),
                       "rate_from_shards": fails / sum(ndec), "rate_json": p4["arms"][arm]["desyncs_per_token"],
                       "n_decoded_minus_first_on_fails": sorted({int(n - f) for n, f in zip(ndec, first) if f >= 0}),
                       "rows_in_streams": all(int(r) in recs for r in rws)}
        exposures[arm] = [recs[int(r)]["ranks"][:int(n)] for r, n in zip(rws, ndec) if int(r) in recs]
    instrument = {"N1": int(ranks1.size), "p1_positions": p1["row"]["positions"], "divergence_recomputed": div,
                  "divergence_json": p1["row"]["divergence_rate"], "p1_scoring_dtype": p1.get("dtype"), "shards": shards}
    instrument["ok"] = (instrument["N1"] == instrument["p1_positions"] and abs(div - instrument["divergence_json"]) < 1e-6
                        and all(abs(s["rate_from_shards"] - s["rate_json"]) < 1e-12 and s["rows_in_streams"] for s in shards.values()))
    value = {"regime_check": regime, "instrument_check": instrument, "claim_regime_rows": claim_regime, "arm_map": E15_ARMS}
    if not (regime["ok"] and instrument["ok"]):
        return row(claim, where, value, "UNRECOMPUTABLE", pred, "regime or instrument check failed")
    h4 = L.rank_histogram(np.concatenate(streams)); h1 = L.rank_histogram(ranks1)
    Lbar = p4["content_tokens"] / p4["archives"]
    # post-critic, no model: the share of rank-1 positions with a top-2 gap under each arm's pair budget, dumps vs archives
    thresholds = {D: xb3[f"cpu_fp32->{D}"]["pair_budget_2tau"] for D in E15_ARMS}
    checked, problems = _manifest_problems(("results/p2_llama32/corpus", "results/p2_llama32/cpu_fp32/"))
    gap_shares = {"manifest_checked": checked, "problems": problems, "thresholds_source": "results/p2b_escape_robustness.json xb3_wide_gap_check pair_budget_2tau"}
    if checked and not problems:
        out = RESULTS / "p2_llama32"; tokens, cmeta = load_corpus(out); Lseq = tokens.shape[1]
        true = tokens[:, 1:].reshape(-1).astype(np.int64); keep = np.ones(tokens.shape[0] * Lseq, bool); keep[Lseq - 1::Lseq] = False
        idx, val, _ = load_arm(out, "cpu_fp32"); idx, val = canonical_topk(idx, val); idx, val = idx[keep], val[keep]
        r1 = P2B.rank_of_true(idx, true) == 1
        gap_shares["p2_dumps_rank1"] = L.gap_share_below((val[:, 0] - val[:, 1])[r1], thresholds)
        gap_shares["corpus"] = {k: cmeta[k] for k in ("model_id", "text_path", "text_sha256", "corpus_sha256")}
    p4_gaps = np.concatenate([recs[k]["gaps"][recs[k]["flags"] == FLAG_A] for k in sorted(recs)])
    gap_shares["p4_archives_rank1"] = L.gap_share_below(p4_gaps, thresholds)
    value.update({"h4": h4, "h1": h1, "Lbar": Lbar, "gap_shares": gap_shares, "arms": {}})
    reversals = []; claim_ok = []; class_ok = {c: [] for c in ("A", "C", "all")}
    try:
        for D, arm in E15_ARMS.items():
            rows_ = {f"{r['theta']}/{r['m']}": r for r in dec[D]}; r0 = rows_["0.0/2"]; rates0 = L.rank_rates(r0)
            c_only = {k: {"h4": {kk: v for kk, v in L.expected_rate(h4, L.rank_rates(r), ("C",)).items() if kk != "by_rank"},
                          "h1": {kk: v for kk, v in L.expected_rate(h1, L.rank_rates(r), ("C",)).items() if kk != "by_rank"}}
                      for k, r in rows_.items()}
            all0_h4 = L.expected_rate(h4, rates0); all0_h1 = L.expected_rate(h1, rates0)
            cr = claim_regime[0]; rcr = rows_[cr]; cr_rates = L.rank_rates(rcr)
            setcoded = {kk: v for kk, v in L.expected_rate(h1, L.setcoded_rates(rcr), ("C",)).items() if kk != "by_rank"}
            meas = p4["arms"][arm]
            fail_exact = {"all_theta0_h4": L.fail_rate_exact(streams, rates0), "c_only_claim_regime_h4": L.fail_rate_exact(streams, cr_rates, ("C",)),
                          # post-critic (second pass): the theta-0 whole-archive prediction under one class's hazards alone
                          "c_only_theta0_h4": L.fail_rate_exact(streams, rates0, ("C",)), "a_only_theta0_h4": L.fail_rate_exact(streams, rates0, ("1",))}
            fail_poisson = {"c_only_claim_regime_h1": L.fail_rate_poisson(Lbar, c_only[cr]["h1"]["rate"]),
                            "all_theta0_h4": L.fail_rate_poisson(Lbar, all0_h4["rate"])}
            cmp_ = {"rate_measured_gt_predicted": meas["desyncs_per_token"] > all0_h4["rate"],
                    "fail_measured_gt_predicted": meas["fail_rate"] > fail_exact["all_theta0_h4"]["fail_rate"]}
            for name, ok in cmp_.items():
                if not ok:
                    reversals.append(f"{D}: {name}")
            one_in_cr = c_only[cr]["h1"]["one_in"]
            claim_ok.append(one_in_cr is not None and round(one_in_cr, -1) == pred[f"{'bf16' if 'bf16' in D else 'fp16'}_claim_regime_one_in"])
            # post-critic: observed first desyncs by class against the expected count over the positions actually decoded
            comp = L.compensator(exposures[arm], rates0, L.observed_by_class(meas["first_desync_class_counts"]))
            for c in class_ok:
                class_ok[c].append(comp[c]["ratio"] is not None and comp[c]["ratio"] > 1)
            value["arms"][D] = {
                "p4_arm": arm,
                "measured": {"desyncs_per_token": meas["desyncs_per_token"], "one_in": 1 / meas["desyncs_per_token"], "fail_rate": meas["fail_rate"],
                             "archives": meas["archives"], "byte_exact": meas["byte_exact"], "first_desync_class_counts": meas["first_desync_class_counts"],
                             "definition": "first desyncs per decoded position (decode stops at the first desync; n_decoded = first + 1 on a failing archive)"},
                "c_only": c_only, "all_theta0": {"h4": {kk: v for kk, v in all0_h4.items() if kk != "by_rank"}, "h1": {kk: v for kk, v in all0_h1.items() if kk != "by_rank"}},
                "setcoded_c_only_claim_regime_h1": setcoded, "fail_exact": fail_exact, "fail_poisson": fail_poisson,
                "compensator_theta0_h4": comp, "comparisons": cmp_,
            }
            tag = "bf16" if "bf16" in D else "fp16"
            value[f"{tag}_all_theta0_one_in"] = all0_h4["one_in"]; value[f"{tag}_all_theta0_one_in_h1"] = all0_h1["one_in"]
            value[f"{tag}_measured_one_in"] = 1 / meas["desyncs_per_token"]
            value[f"{tag}_claim_regime_one_in"] = one_in_cr; value[f"{tag}_fail_poisson_claim_regime_pct"] = 100 * fail_poisson["c_only_claim_regime_h1"]
    except ValueError as e:
        return row(claim, where, value, "UNRECOMPUTABLE", pred, f"missing per-rank rate: {e}")
    value["reversals"] = reversals; value["prediction_sources"] = pred_sources
    value["f11_printed_one_in"] = {D: {"printed": f11_printed[D], "recomputed": value["arms"][D]["measured"]["one_in"],
                                       "rounds_to_printed": round(value["arms"][D]["measured"]["one_in"]) == f11_printed[D]} for D in E15_ARMS}
    value["pinned_rule_sites"] = ["FINDINGS.md:85"]
    r = row(claim, where, value, L.status(not reversals), pred,
            "protocol defect (the critic's BLOCKING 1, amendment of 2026-10-11 UTC): the pinned rule scores F-11:85, a claim about corrections, on an "
            "all-class quantity, and the reversal is the rank-1 term; status_by_class and status_by_claim_site score the claim at its own scope. "
            "The measured rate is a hazard over the decoded prefix; the two sides differ in model, content and kernel path (regime_check.sides)")
    r["status_in_claim_regime"] = L.status(all(claim_ok))
    r["status_by_class"] = {c: L.status(all(v)) for c, v in class_ok.items()}
    cr_st = r["status_in_claim_regime"]
    r["status_by_claim_site"] = {"FINDINGS.md:72 (F-10 headline, in its own regime)": cr_st, "FINDINGS.md:76 (item (4), in its own regime)": cr_st,
                                 "docs/BLUEPRINT.md:57 (in its own regime)": cr_st,
                                 "FINDINGS.md:85 (F-11, corrections more fragile: class C over the decoded positions)": r["status_by_class"]["C"]}
    return r


def e16():
    import inspect

    from amber.rankcensus import calibrate_tau_topk
    b = jload("results/p2b_escape_robustness.json"); xb3 = b["xb3_wide_gap_check"]
    cens = jload("results/p2_llama32_rank_census.json"); census = cens["calibrated_tau_per_arm"]
    # the three top-1 claim sites, then (post-critic) the three sites of F-14's E8a sentence, the depth claim this row's count corrects
    where = ["FINDINGS.md:76", "FINDINGS.md:55", "OPEN_QUESTIONS.md:16", "FINDINGS.md:114", "OPEN_QUESTIONS.md:15", "README.md:50"]
    claim = ("every flip a near-tie (F-7, OQ-2) and XB-3's no wide-gap flip (F-10), read onto the top-64 order differences of the fp32 decoders; "
             "F-14's E8a sentence calls every one of those order differences a near-tie")
    pred = {"b1_count_above_budget": 2, "b1_n_diff": 379, "b1_max_g": 1.478195e-04, "b8_count_above_budget": 0, "b8_n_diff": 411, "b8_max_g": 5.722046e-05,
            "b1_n_nonadjacent": 0}
    arms_needed = ("cpu_fp32",) + E16_SCORED + E16_INFO
    checked, problems = _manifest_problems(("results/p2_llama32/corpus",) + tuple(f"results/p2_llama32/{a}/" for a in arms_needed))
    if problems or not checked or b["R_max"] != L.R_MAX:
        return row(claim, where, {"manifest_checked": checked, "problems": problems, "R_max": b["R_max"]}, "UNRECOMPUTABLE", pred, "dumps missing or changed")
    out = RESULTS / "p2_llama32"; tokens, cmeta = load_corpus(out); Lseq = tokens.shape[1]
    keep = np.ones(tokens.shape[0] * Lseq, bool); keep[Lseq - 1::Lseq] = False
    arms = {}
    for name in arms_needed:
        idx, val, _ = load_arm(out, name); idx, val = canonical_topk(idx, val); arms[name] = (idx[keep], val[keep])
    eidx, eval_ = arms["cpu_fp32"]; g12 = eval_[:, 0] - eval_[:, 1]
    value = {"manifest_checked": checked, "corpus_sha256": cmeta["corpus_sha256"], "n": int(eidx.shape[0]), "dump_width": int(eidx.shape[1]),
             "R": L.R_MAX, "tau_cpu_fp32": 0.0,
             # informational (amendment after the second batch's dry run): the scale the order-difference gaps are read against
             "encoder_top2_gap_quantiles": {"p01": float(np.quantile(g12, 0.01)), "p50": float(np.median(g12))},
             # post-critic: tau as the census computed it (not a top-1 calibration)
             "tau_definition": {"function": "amber.rankcensus.calibrate_tau_topk", "topk_used": cens["topk_used"],
                                "quantile": inspect.signature(calibrate_tau_topk).parameters["quantile"].default,
                                "note": "the quantile of the aligned |delta logit| over the dumps truncated to topk_used; the census's per-row `tau` field holds 2 * tau"},
             "arms": {}}

    def dec_delta(p, tok, dvals, didx):
        hit = np.flatnonzero(didx[p] == tok); src = np.flatnonzero(eidx[p] == tok)
        return float(dvals[p, hit[0]] - eval_[p, src[0]]) if hit.size and src.size else None
    for D in E16_SCORED + E16_INFO:
        didx, dval = arms[D]; ev = L.order_diff_events(eidx, eval_, didx)
        key = f"cpu_fp32->{D}"; two_tau = 2 * census[D] if D in census else None
        if key in xb3:
            budget, src = xb3[key]["pair_budget_2tau"], "results/p2b_escape_robustness.json xb3_wide_gap_check pair_budget_2tau (the XB-3 check's own budget)"
        else:
            budget, src = two_tau, "2 * calibrated_tau_per_arm from results/p2_llama32_rank_census.json (census-derived proxy; P2b's TAU has no entry)"
        s = L.gap_summary(ev, budget, two_tau); s["budget_source"] = src; s["calibrated_tau_census"] = census.get(D)
        above = np.flatnonzero(np.isfinite(ev["g"]) & (ev["g"] > budget))
        events = []
        for i in above:
            p, j, k = int(ev["pos"][i]), int(ev["j"][i]), int(ev["k"][i])
            dj = dec_delta(p, int(eidx[p, j]), dval, didx); dk = dec_delta(p, int(eidx[p, k]), dval, didx) if k >= 0 else None
            events.append({"position": p, "sequence": p // (Lseq - 1), "offset": p % (Lseq - 1), "slot_j": j, "encoder_slot_k": k, "g": float(ev["g"][i]),
                           "enc_gap_top1_top2": float(eval_[p, 0] - eval_[p, 1]), "dec_delta_token_j": dj, "dec_delta_token_k": dk,
                           "pair_drift": (dk - dj) if (dj is not None and dk is not None) else None})
        s["events_above_budget"] = events
        s["distinct_contexts"] = L.distinct_prefixes(tokens, ev["pos"], Lseq - 1)
        s["distinct_contexts_above_budget"] = L.distinct_prefixes(tokens, ev["pos"][above], Lseq - 1)
        s["role"] = "scored" if D in E16_SCORED else "informational"
        if D in E16_SCORED:            # post-critic: the aligned deltas of every encoder top-64 token, by slot, and the adjacent-pair drift
            s["drift"] = L.drift_summary(L.aligned_deltas(eidx, eval_, didx, dval), budget)
        value["arms"][D] = s
    for D, tag in (("cuda_fp32_b1", "b1"), ("cuda_fp32_b8", "b8")):
        s = value["arms"][D]
        value[f"{tag}_count_above_budget"] = s["count_above_budget"]; value[f"{tag}_n_diff"] = s["n_diff"]; value[f"{tag}_max_g"] = s["g_quantiles"]["max"]
        value[f"{tag}_n_nonadjacent"] = s["n_nonadjacent"]
    value["prediction_sources"] = {"b1_n_diff": "the critic (results/errata_critic/REPORT.md, first pass item 5; second pass item 4)",
                                   "b8_n_diff": "the critic (results/errata_critic/REPORT.md, first pass item 5; second pass item 4)",
                                   "b1_count_above_budget": "the critic (results/errata_critic/REPORT.md, third pass item 2)",
                                   "b1_max_g": "the critic (results/errata_critic/REPORT.md, third pass item 2)",
                                   "b8_max_g": "the critic (results/errata_critic/REPORT.md, third pass item 2)",
                                   "b1_n_nonadjacent": "the critic (results/errata_critic/REPORT.md, third pass item 2)",
                                   "b8_count_above_budget": "this protocol (second-batch entry; inferred from the critic's b8 maximum)"}
    r = row(claim, where, value, L.status(value["b1_count_above_budget"] == 0), pred,
            "protocol defect (the critic's BLOCKING 2, amendment of 2026-10-11 UTC): the pinned rule counts order differences at every depth while "
            "the three claim sites are top-1 statements; status_at_claim_scope and status_by_claim_site score them at slot 0, and the pinned count "
            "corrects F-14's E8a sentence. Scored on cuda_fp32_b1 (the XB-3 check's arm); cuda_fp32_b8's budget is the census-derived proxy")
    r["status_by_arm"] = {D: L.status(value["arms"][D]["count_above_budget"] == 0) for D in E16_SCORED}
    # post-critic (second pass): the top-1 claim sites speak of every arm, so the claim-scope status is per arm and the sites take all of them
    r["status_at_claim_scope"] = {D: L.status(value["arms"][D]["by_slot_bucket"]["0"]["above_budget"] == 0) for D in E16_SCORED + E16_INFO}
    scope_all = L.status(all(s == "CONFIRMED" for s in r["status_at_claim_scope"].values()))
    value["pinned_rule_sites"] = ["FINDINGS.md:114", "OPEN_QUESTIONS.md:15", "README.md:50"]
    r["status_by_claim_site"] = {"FINDINGS.md:76 (F-10 item (1), A desyncs at theta 0: slot 0, every arm)": scope_all,
                                 "FINDINGS.md:55 (F-7 caveats, top-1 flips: slot 0, every arm)": scope_all,
                                 "OPEN_QUESTIONS.md:16 (top-1 flips: slot 0, every arm)": scope_all,
                                 "FINDINGS.md:114, OPEN_QUESTIONS.md:15, README.md:50 (F-14's E8a sentence, every order difference a near-tie: all depths)": r["status"]}
    return r


# ----------------------------------------------------------------------------
# third batch (protocol entry of 2026-10-11 UTC, "third batch")
# ----------------------------------------------------------------------------


def _near_tie_masses(dumps: str, manifest: str, thresholds: dict) -> dict:
    """Share of kept positions whose cpu_fp32 top-2 gap lies below each threshold, from the pinned dumps."""
    checked, problems = _manifest_problems((f"{dumps}/corpus", f"{dumps}/cpu_fp32/"), manifest)
    if problems or not checked:
        return {"manifest_checked": checked, "problems": problems}
    out = REPO / dumps; tokens, cmeta = load_corpus(out); Lseq = tokens.shape[1]
    keep = np.ones(tokens.shape[0] * Lseq, bool); keep[Lseq - 1::Lseq] = False
    idx, val, _ = load_arm(out, "cpu_fp32"); idx, val = canonical_topk(idx, val); gap_all = val[:, 0] - val[:, 1]; gap = gap_all[keep]
    # amendment after the revised dry run: the census counted every window position; the kept-position masses stay beside
    return {"manifest_checked": checked, "problems": [], "positions": int(gap_all.size), "positions_kept": int(gap.size), "corpus_sha256": cmeta["corpus_sha256"],
            "mass_pct": {k: float(100 * (gap_all < float(t)).mean()) for k, t in thresholds.items()},
            "mass_pct_kept_positions": {k: float(100 * (gap < float(t)).mean()) for k, t in thresholds.items()}}


def e17():
    where = ["FINDINGS.md:40", "FINDINGS.md:54", "OPEN_QUESTIONS.md:16"]
    claim = ('F-5 and F-7 print "0 beyond 2tau=<label>" thresholds (fp16, bf16, int8, nf4) against the census tau and price the escape at those labels '
             '(F-5: 6.7% of positions at 0.142, 32.6% at 0.93; F-7 and OQ-2: ~8% for fp16, ~39% for bf16)')
    printed = {"F-5 (FINDINGS.md:40)": {"census": "results/p2_rank_census.json", "dumps": "results/p2", "manifest": "results/p2_tinyllama_dumps.sha256",
                                        "labels": {"cuda_fp16_b1": 0.142, "cuda_bf16_b1": 0.93, "cuda_int8_b1": 5.0, "cuda_nf4_b1": 12.3},
                                        "beyond": {"cuda_fp16_b1": 0, "cuda_bf16_b1": 0, "cuda_int8_b1": 0, "cuda_nf4_b1": 3},
                                        "printed_mass_pct_at": {"0.142": 6.7, "0.465": 19.0, "0.93": 32.6}, "printed_cost_pct": {"cuda_fp16_b1": 6.7, "cuda_bf16_b1": 32.6}, "cost_nd": 1},
               "F-7 (FINDINGS.md:54)": {"census": "results/p2_llama32_rank_census.json", "dumps": "results/p2_llama32", "manifest": "results/p2_dumps.sha256",
                                        "labels": {"cuda_fp16_b1": 0.066, "cuda_bf16_b1": 0.93, "cuda_int8_b1": 6.6},
                                        "beyond": {"cuda_fp16_b1": 0, "cuda_bf16_b1": 0, "cuda_int8_b1": 2},
                                        "printed_mass_pct_at": {"0.142": 8.3, "0.465": 23.2, "0.93": 39.1}, "printed_cost_pct": {"cuda_fp16_b1": 8, "cuda_bf16_b1": 39}, "cost_nd": 0}}
    oq_cost = {"site": "OPEN_QUESTIONS.md:16", "same_dumps_as": "F-7 (FINDINGS.md:54)", "printed_cost_pct": {"cuda_fp16_b1": 8, "cuda_bf16_b1": 39}, "cost_nd": 0}
    pred = {"n_labels_4tau": 6, "n_labels_2tau": 1, "counts_all_match": True}
    value = {"sites": {}, "code_semantics": "experiments/p2_rank_census.py census_row passes tau = 2 * tau; amber.rankcensus._census_core counts flip_gaps > tau"}
    n4 = n2 = n_labels = 0; matches = []; field_ok = True; site_status = {}; cost_problem = None
    for site, spec in printed.items():
        c = jload(spec["census"]); taus = c["calibrated_tau_per_arm"]; rows_ = {r["arm"]: r for r in c["rows"]}
        out = {"census": spec["census"], "arms": {}}
        for arm, label in spec["labels"].items():
            tau = taus[arm]; r = rows_[arm]; mult = L.label_multiple(label, tau)
            n4 += mult == 4; n2 += mult == 2; n_labels += 1
            ok_field = abs(r["tau"] - 2 * tau) < 1e-9; field_ok &= ok_field
            cm = r["flips_beyond_tau"] == spec["beyond"][arm]; matches.append(cm)
            gm = r["flip_gap_max"]
            out["arms"][arm] = {"label": label, "tau": tau, "tau_field": r["tau"], "tau_field_is_2tau": ok_field, "label_over_tau": label / tau,
                                "multiple": mult, "label_is_2tau": mult == 2, "printed_beyond": spec["beyond"][arm], "census_beyond_at_2tau": r["flips_beyond_tau"],
                                "count_matches": cm, "top1_flips": r["top1_flips"], "flip_gap_max": gm,
                                "gap_max_below_2tau": (gm is None) or gm < r["tau"], "gap_max_below_label": (gm is None) or gm < label}
        site_status[f"{site}, labels"] = L.status(all(a["label_is_2tau"] for a in out["arms"].values()))
        # post-critic (BLOCKING 1 of the third batch): the escape-cost figures quoted at the labels, against the near-tie mass at 2 tau
        two_tau = {arm: 2 * taus[arm] for arm in ("cuda_fp16_b1", "cuda_bf16_b1")}
        th = {k: float(k) for k in spec["printed_mass_pct_at"]} | {f"2tau_{arm}": t for arm, t in two_tau.items()}
        m = _near_tie_masses(spec["dumps"], spec["manifest"], th)
        cost = {"dumps": spec["dumps"], "manifest": spec["manifest"], **m}
        if "mass_pct" in m:
            cost["printed_mass_pct_at"] = spec["printed_mass_pct_at"]
            cost["instrument_ok"] = all(round(m["mass_pct"][k], 1) == v for k, v in spec["printed_mass_pct_at"].items())
            cost["instrument_ok_under_pinned_tolerance"] = all(abs(m["mass_pct_kept_positions"][k] - v) < 0.05 for k, v in spec["printed_mass_pct_at"].items())
            cost["two_tau"] = two_tau; cost["mass_pct_at_2tau"] = {arm: m["mass_pct"][f"2tau_{arm}"] for arm in two_tau}
            cost["printed_cost_pct"] = spec["printed_cost_pct"]
            cost["cost_differs_at_printed_precision"] = {arm: round(cost["mass_pct_at_2tau"][arm], spec["cost_nd"]) != spec["printed_cost_pct"][arm] for arm in two_tau}
            site_status[f"{site}, escape cost at 2 tau"] = ("CORRECTED" if any(cost["cost_differs_at_printed_precision"].values()) else "CONFIRMED") if cost["instrument_ok"] else "UNRECOMPUTABLE"
        else:
            site_status[f"{site}, escape cost at 2 tau"] = "UNRECOMPUTABLE"; cost_problem = m["problems"]
        out["escape_cost"] = cost
        value["sites"][site] = out
    f7 = value["sites"][oq_cost["same_dumps_as"]]["escape_cost"]
    if "mass_pct_at_2tau" in f7 and f7["instrument_ok"]:
        differs = {arm: round(f7["mass_pct_at_2tau"][arm], oq_cost["cost_nd"]) != oq_cost["printed_cost_pct"][arm] for arm in f7["mass_pct_at_2tau"]}
        value["sites"][oq_cost["site"]] = {"same_dumps_as": oq_cost["same_dumps_as"], "printed_cost_pct": oq_cost["printed_cost_pct"], "mass_pct_at_2tau": f7["mass_pct_at_2tau"],
                                          "cost_differs_at_printed_precision": differs}
        site_status[f"{oq_cost['site']} (escape cost at 2 tau)"] = L.status(not any(differs.values()))
    else:
        site_status[f"{oq_cost['site']} (escape cost at 2 tau)"] = "UNRECOMPUTABLE"
    b = jload("results/p2b_escape_robustness.json"); tl = jload("results/p2_llama32_rank_census.json")["calibrated_tau_per_arm"]
    value["p2b_thetas_over_llama_tau"] = {str(th): {"over_fp16_tau": th / tl["cuda_fp16_b1"], "over_bf16_tau": th / tl["cuda_bf16_b1"]} for th in b["thetas"] if th > 0}
    value.update({"n_labels_4tau": n4, "n_labels_2tau": n2, "n_labels": n_labels, "counts_all_match": all(matches)})
    value["pinned_rule_sites"] = ["FINDINGS.md:40", "FINDINGS.md:54"]
    if not field_ok:
        return row(claim, where, value, "UNRECOMPUTABLE", pred, "a census row's tau field is not 2 * tau")
    r = row(claim, where, value, L.status(n4 == 0 and n2 == n_labels), pred,
            "the labels and the escape-cost figures quoted at them are wrong; the census's beyond-counts were taken at 2 tau (its per-row tau field) and stand"
            + (f"; cost dumps unavailable: {cost_problem}" if cost_problem else ""))
    r["status_by_count"] = L.status(all(matches))
    r["status_by_claim_site"] = site_status
    # the cost sites' status under the entry's original tolerance (kept positions, 0.05 points), per the amendment after the revised dry run
    under = {}
    for k, v in site_status.items():
        if k.endswith("labels"):
            under[k] = v; continue
        base = oq_cost["same_dumps_as"] if k.startswith(oq_cost["site"]) else k.split(",")[0]
        ok_pinned = value["sites"].get(base, {}).get("escape_cost", {}).get("instrument_ok_under_pinned_tolerance", False)
        under[k] = v if ok_pinned else "UNRECOMPUTABLE"
    r["status_under_pinned_tolerance"] = under
    r["amended_by"] = "the entry after the revised third-batch dry run (masses over all census positions, checked at the printed precision)"
    return r


def _tokenizer_offline(model_id: str):
    from huggingface_hub import try_to_load_from_cache

    from amber.real.capture import _load_tokenizer
    tj = try_to_load_from_cache(model_id, "tokenizer.json"); tj_path = Path(tj) if isinstance(tj, str) else None
    if tj_path is None or not tj_path.exists():
        raise FileNotFoundError(f"tokenizer.json for {model_id} is not in the local HF cache")
    return _load_tokenizer(str(tj_path.parent)), tj_path


def e18():
    import zstandard
    where = ["DECISIONS.md:39-44", "FINDINGS.md:58", "FINDINGS.md:62", "FINDINGS.md:91", "FINDINGS.md:95", "FINDINGS.md:102", "FINDINGS.md:86", "README.md:31",
             "README.md:45-46", "docs/BLUEPRINT.md:50", "docs/BLUEPRINT.md:81", "OPEN_QUESTIONS.md:31", "OPEN_QUESTIONS.md:32", "DECISIONS.md:132", "DECISIONS.md:105"]
    claim = ("the zstd-19 comparators of F-8 (7.6x below zstd-19), F-11 and F-12 (7.28 per archive; crossover vs zstd-19-concatenated L~263) and F-13 "
             "(3.4x under zstd-19 per session) carry no dictionary; D-6: a format that only beats strawmen is not a format")
    # the harvest's values, scored against the same quantities computed under its own definitions (text with special tokens skipped; repeat share over the row length)
    pred = {"amber_v3_arch": 4.181, "zstd_arch_none": 6.251, "zstd_arch_4096": 4.737, "zstd_arch_16384": 4.446, "zstd_arch_65536": 4.408,
            "rep_below_half_amber_v3_arch": 5.253, "rep_below_half_zstd_arch_16384": 10.330,          # the entry's pinned quantities
            "harvest_def_zstd_arch_none": 6.251, "harvest_def_zstd_arch_4096": 4.737, "harvest_def_zstd_arch_16384": 4.446,
            "harvest_def_zstd_arch_65536": 4.408, "harvest_def_rep_amber_v3_arch": 5.253, "harvest_def_rep_zstd_arch_16384": 10.330}   # the same under the harvest's definitions
    pred_sources = {k: "the review harvest (sideband harvest scratchpad/amber-audit/spot6.py, spot7.py; agent output)" for k in pred}
    p5 = jload("results/p5_binformat.json"); rep5 = p5["report"]; em = jload("results/p5/encode_meta.json"); p1 = jload("results/p1_divergence.json")
    try:
        tok, tj_path = _tokenizer_offline(p5["draft"])
    except Exception as e:  # noqa: BLE001
        return row(claim, where, {"error": f"{type(e).__name__}: {e}"}, "UNRECOMPUTABLE", pred, "tokenizer unavailable offline")
    seqs = load_generated(RESULTS / "p1"); full = {}; gen = {}; gen_len = {}; gen_ids = {}; full_s = {}; gen_s = {}
    for r, ids, pl in seqs:
        full[r] = tok.decode(ids.tolist()).encode("utf-8"); gen[r] = tok.decode(ids[pl:].tolist()).encode("utf-8"); gen_len[r] = int(len(ids) - pl); gen_ids[r] = ids[pl:]
        full_s[r] = tok.decode(ids.tolist(), skip_special_tokens=True).encode("utf-8"); gen_s[r] = tok.decode(ids[pl:].tolist(), skip_special_tokens=True).encode("utf-8")
    train = sorted(r for r in full if r < E18_SPLIT); held = sorted(r for r in full if r >= E18_SPLIT); G = sum(gen_len[r] for r in held)
    # instrument check (as E4): amber v0 over all rows reproduces the P1 json
    draft = load_rank(RESULTS / "p1", "draft"); by_row = {p["row"]: p["rank"] for p in draft["per_prompt"]}
    ranks_all = np.concatenate([by_row[r] for r, _, _ in seqs]); amber_all = P1.amber_bits(ranks_all) / ranks_all.size
    instrument = {"N": int(ranks_all.size), "amber_v0_recomputed": float(amber_all), "amber_v0_json": p1["row"]["amber_v0_bits_per_token"],
                  "rows_train": len(train), "rows_held": len(held), "G": G, "tokenizer_json": str(tj_path), "tokenizer_json_sha256": L.sha256_bytes(tj_path.read_bytes()),
                  "zstandard_version": zstandard.__version__}
    instrument["ok"] = abs(amber_all - p1["row"]["amber_v0_bits_per_token"]) < 1e-9 and ranks_all.size == p1["row"]["positions"] and len(train) == len(held) == E18_SPLIT
    if not instrument["ok"]:
        return row(claim, where, {"instrument_check": instrument}, "UNRECOMPUTABLE", pred, "instrument check failed")
    # dictionaries
    dicts = {}; dinfo = {}
    for size in E18_SIZES:
        try:
            d = zstandard.train_dictionary(size, [full[r] for r in train], level=19); dicts[size] = d
            dinfo[str(size)] = {"bytes": len(d.as_bytes()), "sha256": L.sha256_bytes(d.as_bytes()), "dict_id": d.dict_id()}
        except Exception as e:  # noqa: BLE001
            dinfo[str(size)] = {"error": f"{type(e).__name__}: {e}"}
    if E18_PRIMARY not in dicts:
        return row(claim, where, {"instrument_check": instrument, "dictionaries": dinfo}, "UNRECOMPUTABLE", pred, "primary dictionary could not be trained")
    d16g = zstandard.train_dictionary(E18_PRIMARY, [gen[r] for r in train], level=19)
    dinfo["gen_16384"] = {"bytes": len(d16g.as_bytes()), "sha256": L.sha256_bytes(d16g.as_bytes()), "dict_id": d16g.dict_id()}
    comp = {"none": zstandard.ZstdCompressor(level=19), **{str(s): zstandard.ZstdCompressor(level=19, dict_data=d) for s, d in dicts.items()}}
    cgen = zstandard.ZstdCompressor(level=19, dict_data=d16g)

    def zb(c, blobs):
        return sum(len(c.compress(b)) for b in blobs)
    fixed = rep5["fixed_header_bytes"]
    arch = {k: L.bits_per_token(zb(c, [full[r] for r in held]), G) for k, c in comp.items()}
    amber_arch = L.bits_per_token(sum(em["per_row"][str(r)]["bytes"] for r in held), G)
    amber_payload_only = L.bits_per_token(sum(em["per_row"][str(r)]["bytes"] - fixed for r in held), G)
    key16 = str(E18_PRIMARY)
    concat = {k: L.bits_per_token(len(c.compress(b"".join(full[r] for r in held))), G) for k, c in comp.items() if k in ("none", key16)}
    cm = rep5["curve_model"]
    cross = {k: L.crossover_length(cm["per_archive_const_bits"], v, cm["payload_gen_rate"]) for k, v in concat.items()}
    amber_v0_held = P1.amber_bits(np.concatenate([by_row[r] for r in held])) / G
    gen_concat = {"none": L.bits_per_token(len(comp["none"].compress(b"".join(gen[r] for r in held))), G),
                  "gen_16384": L.bits_per_token(len(cgen.compress(b"".join(gen[r] for r in held))), G)}
    sessions = {}
    for k in (8, 16):
        meta = jload(f"results/p6/k{k}_m0/meta.json")["sessions"]
        sel = [s for s in meta.values() if min(s["rows"]) >= E18_SPLIT]; gt = sum(s["gen_tokens"] for s in sel)
        z_none = L.bits_per_token(sum(len(comp["none"].compress(b"".join(full[r] for r in s["rows"]))) for s in sel), gt)
        z_d16 = L.bits_per_token(sum(len(comp[key16].compress(b"".join(full[r] for r in s["rows"]))) for s in sel), gt)
        a = L.bits_per_token(sum(s["bytes"] for s in sel), gt)
        sessions[f"k{k}"] = {"sessions": len(sel), "gen_tokens": gt, "gen_tokens_match_rows": gt == sum(gen_len[r] for s in sel for r in s["rows"]),
                             "amber_v4_reset": a, "zstd_none": z_none, "zstd_16384": z_d16, "multiple_none": z_none / a, "multiple_16384": z_d16 / a,
                             "effect": L.dictionary_effect(z_none, z_d16),
                             "printed_all_rows": jload("results/p6_sessions.json")["report"]["by_k_mode"][f"k{k}_m0"]}
    rep_rows = [r for r in held if (lambda nd: nd[0] / nd[1] if nd[1] else 0.0)(L.repeat_4gram_share([gen_ids[r]])) < 0.5]
    Gr = sum(gen_len[r] for r in rep_rows)
    rep_split = {"rows": len(rep_rows), "gen_tokens": Gr,
                 "amber_v3_arch": L.bits_per_token(sum(em["per_row"][str(r)]["bytes"] for r in rep_rows), Gr) if Gr else None,
                 "zstd_arch_16384": L.bits_per_token(zb(comp[key16], [full[r] for r in rep_rows]), Gr) if Gr else None,
                 "zstd_arch_none": L.bits_per_token(zb(comp["none"], [full[r] for r in rep_rows]), Gr) if Gr else None}
    effects = {"arch": L.dictionary_effect(arch["none"], arch[key16]), "session16": sessions["k16"]["effect"], "session8": sessions["k8"]["effect"],
               "concat": L.dictionary_effect(concat["none"], concat[key16]), "gen_concat": L.dictionary_effect(gen_concat["none"], gen_concat["gen_16384"])}
    # post-critic (third batch): the same quantities on text decoded with special tokens skipped (the harvest's definition), dictionaries retrained on it
    dicts_s = {}
    for size in E18_SIZES[:3]:
        try:
            dicts_s[size] = zstandard.train_dictionary(size, [full_s[r] for r in train], level=19)
        except Exception:  # noqa: BLE001
            pass
    comp_s = {"none": comp["none"], **{str(s): zstandard.ZstdCompressor(level=19, dict_data=d) for s, d in dicts_s.items()}}
    arch_s = {k: L.bits_per_token(zb(c, [full_s[r] for r in held]), G) for k, c in comp_s.items()}
    concat_s = {k: L.bits_per_token(len(c.compress(b"".join(full_s[r] for r in held))), G) for k, c in comp_s.items() if k in ("none", key16)}
    sess_s = {}
    for k in (8, 16):
        meta = jload(f"results/p6/k{k}_m0/meta.json")["sessions"]; sel = [s for s in meta.values() if min(s["rows"]) >= E18_SPLIT]; gt = sum(s["gen_tokens"] for s in sel)
        zn = L.bits_per_token(sum(len(comp_s["none"].compress(b"".join(full_s[r] for r in s["rows"]))) for s in sel), gt)
        zd = L.bits_per_token(sum(len(comp_s[key16].compress(b"".join(full_s[r] for r in s["rows"]))) for s in sel), gt)
        sess_s[f"k{k}"] = {"zstd_none": zn, "zstd_16384": zd, "effect": L.dictionary_effect(zn, zd)}
    rep_rows_h = [r for r in held if (lambda nd: nd[0] / len(gen_ids[r]) if len(gen_ids[r]) else 0.0)(L.repeat_4gram_share([gen_ids[r]])) < 0.5]
    Grh = sum(gen_len[r] for r in rep_rows_h)
    harvest_def = {"text": "special tokens skipped (the harvest's spot6.py/spot7.py decode)", "dictionaries": {str(s): {"bytes": len(d.as_bytes()), "sha256": L.sha256_bytes(d.as_bytes()), "dict_id": d.dict_id()} for s, d in dicts_s.items()},
                   "zstd_arch": arch_s, "repeat_share_denominator": "row length (the harvest's rep_frac)", "rep_rows": len(rep_rows_h), "rep_gen_tokens": Grh,
                   "rep_amber_v3_arch": L.bits_per_token(sum(em["per_row"][str(r)]["bytes"] for r in rep_rows_h), Grh) if Grh else None,
                   "rep_zstd_arch_16384": L.bits_per_token(zb(comp_s[key16], [full_s[r] for r in rep_rows_h]), Grh) if Grh else None}
    effects_without_literals = {"arch": L.dictionary_effect(arch_s["none"], arch_s[key16]), "session16": sess_s["k16"]["effect"], "session8": sess_s["k8"]["effect"],
                                "concat": L.dictionary_effect(concat_s["none"], concat_s[key16]), "sessions": sess_s, "zstd_concat": concat_s}
    value = {"instrument_check": instrument, "split": {"train_rows": [train[0], train[-1]], "held_rows": [held[0], held[-1]], "G": G}, "dictionaries": dinfo,
             "per_archive": {"zstd": arch, "amber_v3": amber_arch, "amber_v3_payload_only": amber_payload_only, "fixed_header_bytes": fixed,
                             "zstd_16384_amortised": arch[key16] + L.bits_per_token(dinfo[key16]["bytes"], G),
                             "ratio_zstd_over_amber": {k: v / amber_arch for k, v in arch.items()},
                             "printed_all_rows": {"zstd19_full_text_per_archive": rep5["zstd19_full_text_per_archive_bits_per_generated_token"],
                                                  "amber_v3": rep5["v3_total_bits_per_generated_token"]}},
             "concatenated_full_text": {"zstd": concat, "crossover_L": cross, "curve_model": cm,
                                        "printed_all_rows": {"zstd19_full_text_concatenated": rep5["zstd19_full_text_concatenated_bits_per_generated_token"]}},
             "content": {"amber_v0_held": float(amber_v0_held), "zstd_gen_concat": gen_concat,
                         "multiple": {k: v / amber_v0_held for k, v in gen_concat.items()},
                         "printed_all_rows": {"amber_v0": p1["row"]["amber_v0_bits_per_token"], "zstd19": p1["row"]["zstd19_bits_per_token"]}},
             "sessions": sessions, "repetition_split": rep_split, "effects": effects, "threshold": 0.10,
             "harvest_definitions": harvest_def, "effects_without_literals": effects_without_literals,
             "amber_v3_arch": amber_arch, "zstd_arch_none": arch["none"], **{f"zstd_arch_{s}": arch[str(s)] for s in E18_SIZES if str(s) in arch},
             "rep_below_half_amber_v3_arch": rep_split["amber_v3_arch"], "rep_below_half_zstd_arch_16384": rep_split["zstd_arch_16384"],
             "harvest_def_zstd_arch_none": arch_s["none"], **{f"harvest_def_zstd_arch_{s}": arch_s[str(s)] for s in E18_SIZES[:3] if str(s) in arch_s},
             "harvest_def_rep_amber_v3_arch": harvest_def["rep_amber_v3_arch"], "harvest_def_rep_zstd_arch_16384": harvest_def["rep_zstd_arch_16384"],
             "effect_arch": effects["arch"], "prediction_sources": pred_sources,
             "pinned_rule_sites": ["DECISIONS.md:39-44", "FINDINGS.md:95", "FINDINGS.md:86", "DECISIONS.md:105"]}
    st = {k: L.status(not (e > 0.10)) for k, e in effects.items()}
    r = row(claim, where, value, st["arch"], pred,
            "the dictionary effect is scored at each claim's own scale (threshold 0.10); the row status is the per-archive one (D-6 at the per-archive scale); "
            "the dictionaries were trained on the other half of the same prompt families, which favours zstd; effects_without_literals reports the same "
            "effects on text decoded with special tokens skipped")
    r["status_by_claim_site"] = {"DECISIONS.md:39-44 (D-6, per archive)": st["arch"], "FINDINGS.md:95 (F-12, zstd per archive)": st["arch"],
                                 "FINDINGS.md:86 (F-11, 7.28 per archive)": st["arch"], "DECISIONS.md:105 (comparable to zstd, per archive)": st["arch"],
                                 "FINDINGS.md:102, README.md:46, OPEN_QUESTIONS.md:31, DECISIONS.md:132 (3.4x per session, k=16)": st["session16"],
                                 "FINDINGS.md:91, README.md:45, docs/BLUEPRINT.md:81, OPEN_QUESTIONS.md:32 (crossover vs zstd concatenated)": st["concat"],
                                 "FINDINGS.md:58, FINDINGS.md:62, README.md:31, docs/BLUEPRINT.md:50 (7.6x, concatenated generated text)": st["gen_concat"]}
    return r


def e19():
    where = ["FINDINGS.md:78", "FINDINGS.md:136"]
    claim = ("F-10's caveat 'the per-rank rates are what transfer, the mix is not' (and item (4)'s cross-experiment estimate, 'probable, different content'): "
             "does the rank-1 term transfer once conditioned on the encoder's top-2 gap")
    crit = jload("results/errata_critic/c2_e15_gapsens.out.json")
    # post-critic (the third batch's BLOCKING 2): the primary binning equals the critic's post-hoc p2_quantile20, so its values are not predictions; not scored
    pred = {}; pred_sources = {}
    critic_primary = {D: {k: crit[D]["by_binning"]["p2_quantile20"][k] for k in ("compensator_A", "one_in", "fail_exact")} for D in ("cuda_bf16_b1", "cuda_fp16_b1")}
    arms_needed = ("cpu_fp32", "cuda_bf16_b1", "cuda_fp16_b1")
    checked, problems = _manifest_problems(("results/p2_llama32/corpus",) + tuple(f"results/p2_llama32/{a}/" for a in arms_needed))
    if problems or not checked:
        return row(claim, where, {"manifest_checked": checked, "problems": problems}, "UNRECOMPUTABLE", pred, "dumps missing or changed")
    out = RESULTS / "p2_llama32"; tokens, cmeta = load_corpus(out); Lseq = tokens.shape[1]
    true = tokens[:, 1:].reshape(-1).astype(np.int64); keep = np.ones(tokens.shape[0] * Lseq, bool); keep[Lseq - 1::Lseq] = False
    arms = {}
    for name in arms_needed:
        idx, val, _ = load_arm(out, name); idx, val = canonical_topk(idx, val); arms[name] = (idx[keep], val[keep])
    eidx, eval_ = arms["cpu_fp32"]; r_enc = P2B.rank_of_true(eidx, true); a_mask = r_enc == 1
    gaps_dump = (eval_[:, 0] - eval_[:, 1])[a_mask]
    b = jload("results/p2b_escape_robustness.json"); dec = b["report"]["cpu_fp32"]["decoders"]
    p4 = jload("results/p4_real_archive.json")["report"]; e15 = jload("results/errata_recompute_2.json")["rows"]["E15"]["value"]
    files, totals, recs, consistent = _p4_streams()
    from amber.rac_codec import FLAG_A
    exposure = {}
    for D, arm in E15_ARMS.items():
        rws, ndec = [], []
        for f in sorted(glob.glob(str(RESULTS / "p4" / f"decode_{arm}" / "shard_*.npz"))):
            with np.load(f) as zf:
                rws += zf["row"].tolist(); ndec += zf["n_decoded"].tolist()
        exposure[D] = [(recs[int(r)], int(n)) for r, n in zip(rws, ndec)]
    value = {"manifest_checked": checked, "corpus_sha256": cmeta["corpus_sha256"], "dump_rank1_positions": int(a_mask.sum()),
             "dump_rank1_gap_quantiles": {q: float(np.quantile(gaps_dump, float(q))) for q in ("0.01", "0.1", "0.5", "0.9")},
             "binnings": [f"{k}{n}" for k, n in E19_BINNINGS], "primary": f"{E19_BINNINGS[0][0]}{E19_BINNINGS[0][1]}", "arms": {}, "prediction_sources": pred_sources}
    ok_primary = []; e15_ok = []; oos_ok = []; rank_only_z_beyond_2 = []
    for D, arm in E15_ARMS.items():
        didx, _ = arms[D]; desync_A = (didx[:, 0] != true)[a_mask]
        r0 = next(r for r in dec[D] if r["theta"] == 0.0 and r["m"] == 2)
        if int(desync_A.sum()) != r0["desyncs"]["A"]:
            return row(claim, where, value, "UNRECOMPUTABLE", pred, f"A desyncs in the dumps ({int(desync_A.sum())}) differ from the P2b row ({r0['desyncs']['A']})")
        rates_C = L.rank_rates(r0); meas = p4["arms"][arm]; obs = L.observed_by_class(meas["first_desync_class_counts"])
        rank_only = e15["arms"][D]["compensator_theta0_h4"]["A"]
        per_bin = {}
        for kind, n in E19_BINNINGS:
            edges = L.gap_edges_equal_count(gaps_dump, n) if kind == "quantile" else L.gap_edges_log(gaps_dump, n)
            rates = L.binned_rates(gaps_dump, desync_A, edges)
            E_A = 0.0; n_empty = 0
            for rec, nd in exposure[D]:
                fl = rec["flags"][:nd]; g = rec["gaps"][:nd][fl == FLAG_A]
                if g.size:
                    hz, ne = L.apply_rates(g, edges, rates); E_A += float(hz.sum()); n_empty += ne
            # full theta-0 prediction over every position of the streams: gap-conditioned A, rank-only C, X 0
            hz_sum = 0.0; N = 0; surv = []
            for key in sorted(recs):
                rec = recs[key]; fl = rec["flags"]; rk = rec["ranks"]; h = np.zeros(fl.size)
                a = fl == FLAG_A
                if a.any():
                    h[a], _ = L.apply_rates(rec["gaps"][a], edges, rates)
                c = (rk >= 2) & (rk <= L.R_MAX)
                h[c] = np.array([rates_C[str(int(r))] or 0.0 for r in rk[c]])
                hz_sum += float(h.sum()); N += fl.size; surv.append(float(np.prod(1.0 - h)))
            one_in = N / hz_sum if hz_sum else None; fail = 1.0 - float(np.mean(surv))
            cmp_ = {"rate_measured_gt_predicted": meas["desyncs_per_token"] > hz_sum / N, "fail_measured_gt_predicted": meas["fail_rate"] > fail}
            per_bin[f"{kind}{n}"] = {"bins": len(edges) + 1, "empty_dump_bins": sum(1 for x in rates["rate"] if x is None), "p4_rank1_exposure_in_empty_bins": n_empty,
                                    "E_A": E_A, "O_A": obs["A"], "z": (obs["A"] - E_A) / np.sqrt(E_A) if E_A else None,
                                    "one_in": one_in, "fail_exact": fail, "comparisons": cmp_}
        prim = per_bin[value["primary"]]; others = {k: x for k, x in per_bin.items() if k != value["primary"]}
        ok_primary.append(prim["z"] is not None and abs(prim["z"]) < 2); e15_ok.append(all(prim["comparisons"].values()))
        oos_ok.append(all(x["z"] is not None and abs(x["z"]) < 2 for x in others.values()))
        rank_only_z_beyond_2.append(rank_only["z"] is not None and abs(rank_only["z"]) >= 2)
        m_one_in = e15["arms"][D]["measured"]["one_in"]
        tag = "bf16" if "bf16" in D else "fp16"
        value["arms"][D] = {"p4_arm": arm, "dump_A_desyncs": int(desync_A.sum()), "observed_A_first": obs["A"], "rank_only": rank_only, "by_binning": per_bin,
                            "measured": {"one_in": m_one_in, "fail_rate": meas["fail_rate"]},
                            "grid_E_A_range": [min(x["E_A"] for x in per_bin.values()), max(x["E_A"] for x in per_bin.values())],
                            "grid_z_range": [min(x["z"] for x in per_bin.values()), max(x["z"] for x in per_bin.values())],
                            # post-critic: interval, margins, robustness, and the critic's earlier values the primary binning reproduces
                            "oe_interval_primary": L.poisson_ratio_interval(obs["A"], prim["E_A"]),
                            "margins_primary": {"one_in_predicted_over_measured_minus_1": prim["one_in"] / m_one_in - 1, "fail_measured_minus_predicted": meas["fail_rate"] - prim["fail_exact"]},
                            "e15_rule_holds_at_binnings": sum(1 for x in per_bin.values() if all(x["comparisons"].values())), "binnings": len(per_bin),
                            "critic_p2_quantile20": critic_primary[D],
                            "primary_equals_critic": all(abs(prim[a] - critic_primary[D][b]) < 1e-9 for a, b in (("E_A", "compensator_A"), ("one_in", "one_in"), ("fail_exact", "fail_exact")))}
        value[f"{tag}_E_A"] = prim["E_A"]; value[f"{tag}_z"] = prim["z"]; value[f"{tag}_one_in"] = prim["one_in"]; value[f"{tag}_fail_exact"] = prim["fail_exact"]
    value["pinned_rule_sites"] = ["FINDINGS.md:78"]
    value["prediction_note"] = ("not scored: the primary binning's values equal the second batch's critic's post-hoc p2_quantile20 values "
                                "(results/errata_critic/c2_e15_gapsens.out.json, in the record before the entry) by construction")
    r = row(claim, where, value, L.status(all(ok_primary)), pred,
            "post hoc (the third batch's critic, BLOCKING 2): the rule and its primary binning were written after those values were in the record; the six "
            "other binnings are the out-of-sample evidence. The rank-1 term only; the correction term stays rank-only because the P4 symbol streams carry "
            "no gaps beyond the top-2")
    r["post_hoc"] = ("the status is decided by a rule written after its primary values were seen (the critic's second-batch p2_quantile20, committed before "
                     "the third-batch entry); the six other binnings were not seen")
    r["status_out_of_sample"] = L.status(all(oos_ok))
    r["status_e15_rule_gap_conditioned"] = L.status(all(e15_ok))
    r["status_by_claim_site"] = {"FINDINGS.md:78 (F-10 caveat: the per-rank rates are what transfer; the rank-only rank-1 rate does not, on E15's rank-only compensator z, a field "
                                 "added after the second batch's values were seen)": L.status(not any(rank_only_z_beyond_2)),
                                 "FINDINGS.md:136 (F-15's E15 bullet: the correction excess is not identified; stands, not conditioned here)": "CONFIRMED"}
    return r


# ----------------------------------------------------------------------------
# main
# ----------------------------------------------------------------------------


def provenance(head: str, dirty: list[str]) -> dict:
    import zstandard
    inputs = {}
    for p in INPUTS:
        try:
            inputs[p] = L.blob_id(REPO, head, p)
        except Exception:  # noqa: BLE001 — an uncommitted script has no blob yet; recorded as None
            inputs[p] = None
    try:
        import transformers
        tv = transformers.__version__
    except Exception:  # noqa: BLE001
        tv = None
    return {"head": head, "tree": L.git(REPO, "rev-parse", "HEAD^{tree}"), "clean_tracked_tree": not dirty, "protocol": PROTOCOL,
            "script_blob": inputs.get("experiments/errata_recompute.py"), "script_sha256_lf": L.sha256_lf(Path(__file__)),
            "lib_sha256_lf": L.sha256_lf(REPO / "experiments/errata_lib.py"), "python": platform.python_version(),
            "numpy": np.__version__, "zstandard": zstandard.__version__, "transformers": tv,
            "torch_blocked": sys.modules.get("torch", "absent") is None,
            "torch_in_sys_modules": isinstance(sys.modules.get("torch"), type(sys)), "written_unix": int(time.time()), "inputs": inputs}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="print the payload; write nothing")
    default_out = str(RESULTS / "errata_recompute.json")
    ap.add_argument("--out", default=default_out)
    ap.add_argument("--rows", default="", help="comma-separated subset, e.g. E15,E16 (dry runs, or a non-default --out)")
    a = ap.parse_args(argv)
    dirty = L.dirty_tracked(REPO); head = L.git(REPO, "rev-parse", "HEAD")
    if dirty and not a.dry_run:
        print("errata_recompute: refusing to write on a dirty tracked tree:\n  " + "\n  ".join(dirty), file=sys.stderr)
        return 2
    if a.rows and not a.dry_run and Path(a.out).resolve() == Path(default_out).resolve():
        print("errata_recompute: a row subset may only be written to a non-default --out", file=sys.stderr)
        return 2
    want = set(a.rows.split(",")) if a.rows else None
    rows = {}

    def run(key, fn, *args):
        if want is None or key in want:
            t0 = time.perf_counter(); rows[key] = fn(*args); rows[key]["seconds"] = round(time.perf_counter() - t0, 3)
            print(f"[{key}] {rows[key]['status']} ({rows[key]['seconds']}s)", file=sys.stderr)
    seqs, gen = load_p1()
    run("E1", e1); run("E2", e2, seqs, gen)
    if want is None or want & {"E3", "E4"}:
        t0 = time.perf_counter(); r3, flags = e3(seqs, gen); r3["seconds"] = round(time.perf_counter() - t0, 3); rows["E3"] = r3
        print(f"[E3] {r3['status']} ({r3['seconds']}s)", file=sys.stderr)
        run("E4", e4, seqs, gen, flags)
    run("E5", e5); run("E6", e6); run("E7", e7, seqs, gen); run("E8a", e8a); run("E8b", e8b); run("E8c", e8c)
    if "E8a" in rows and "E8c" in rows:
        finalize_e8a(rows["E8a"], rows["E8c"])
    run("E9", e9); run("E10", e10); run("E11", e11); run("E12", e12); run("E13", e13, a.dry_run); run("E14", e14)
    run("E15", e15); run("E16", e16)                                   # second batch (amendment of 2026-10-10)
    run("E17", e17); run("E18", e18); run("E19", e19)                  # third batch (entry of 2026-10-11 UTC)
    pv = provenance(head, dirty)
    pv["batch"] = 3 if (want is not None and want <= BATCH3) else (2 if (want is not None and want <= BATCH2) else 1)
    pv["rows_requested"] = sorted(want) if want is not None else "all"
    payload = {"provenance": pv, "rows": rows, "summary": {k: v["status"] for k, v in rows.items()}}
    text = json.dumps(payload, indent=1, sort_keys=True) + "\n"
    if a.dry_run:
        sys.stdout.write(text); return 0
    Path(a.out).write_bytes(text.encode("utf-8"))
    print(f"wrote {a.out}: " + ", ".join(f"{k}={v}" for k, v in payload["summary"].items()), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
