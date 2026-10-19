#!/usr/bin/env python3
"""Generate the errata text from an errata recompute payload (ERRATA_PLAN step 5; second batch 2026-10-10).

Every numeral, date, commit id and status word in the generated text comes
from the payload; nothing is typed here. The generator emits:
  - the finding appended to FINDINGS.md (F-14 for results/errata_recompute.json,
    F-15 for results/errata_recompute_2.json; regime + source lines for lint);
  - one dated "erratum" line at the end of every finding a row points at
    (derived from each row's `where` entries into FINDINGS.md);
  - dated pointer notes after the other claim locations each row names
    (README, BLUEPRINT, DECISIONS, OPEN_QUESTIONS, PRIOR_ART, P7_PROTOCOL)
    and one under the README status header.
Append-only: every original line survives unchanged and in order; each
target file's HEAD blob must still equal the blob the run pinned; a run is
refused once its finding exists.

    python experiments/errata_text.py --dry-run                                                  # F-14 from the first payload
    python experiments/errata_text.py --payload results/errata_recompute_2.json --finding F-15   # the second batch
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PAYLOAD = REPO / "results" / "errata_recompute.json"
FINDING_ID = "F-14"
ROW_ORDER = ["E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8a", "E8b", "E8c", "E9", "E10", "E11", "E12", "E13", "E14", "E15", "E16", "E17", "E18", "E19"]
# how a pointer note is placed relative to the referenced line(s): after the paragraph, or right after the line
PLACEMENT = {"README.md": "paragraph", "docs/BLUEPRINT.md": "paragraph", "docs/PRIOR_ART.md": "paragraph", "DECISIONS.md": "paragraph",
             "OPEN_QUESTIONS.md": "line", "experiments/P7_PROTOCOL.md": "line"}
SKIP_FILES = {"pyproject.toml"}          # a TOML string cannot carry a note; its claim is covered by README/BLUEPRINT


def esc(s: str) -> str:
    """Markdown-safe: no unescaped pipes in generated text."""
    return s.replace("|", "\\|")


def pct(x: float, nd: int = 1) -> str:
    return f"{100 * x:.{nd}f}%"


def date_of(payload: dict) -> str:
    return time.strftime("%Y-%m-%d", time.gmtime(payload["provenance"]["written_unix"]))


def rows_present(P: dict) -> list[str]:
    return [rid for rid in ROW_ORDER if rid in P["rows"]]


# ----------------------------------------------------------------------------
# per-row text (one sentence group per row; used in the finding and in the pointer notes)
# ----------------------------------------------------------------------------


def _t_E1(R):
    v = R["E1"]["value"]
    doc = v["archive_py_line1"].strip('"') + " " + v["archive_py_line2"].strip()
    return (f"the real-archive encoder loads {v['encode_meta_model_id']} (the draft; the target is {v['p1_divergence_target']}): "
            f"archive.py opens \"{doc}\" and encode_stage calls "
            f"load_model({v['p4_encode_stage_load_model_arg']}). The draft codes both ends; the target only generates.")


def _t_E2(R):
    v = R["E2"]["value"]
    return (f"{v['n_cap']} of {v['n_rows']} rows reach the cap of {v['max_new']}; {v['n_eos']} end at the EOS token (the protocol's pinned id); "
            f"min generated length {v['min_gen']}, {v['n_empty']} empty, {v['total_gen']} generated tokens.")


def _t_E3(R):
    v = R["E3"]["value"]; g = v["grid"]; nl = [x["n_looped"] for x in g]
    return (f"under the pinned loop rule (window {v['W']}, max period {v['P']}, threshold {v['t']}) {v['n_looped']} of {v['n_rows']} rows end in an "
            f"exact periodic tail, covering {v['tokens_in_loop']} of {v['total_gen']} generated tokens ({pct(v['tokens_in_loop_share'])}); "
            f"across the {len(g)} grid settings the looped-row count spans {min(nl)}-{max(nl)}; "
            f"{pct(v['repeat_4gram_share']['share'])} of eligible positions repeat an earlier 4-gram of their row "
            f"(pooled distinct-4-gram ratio {v['distinct_4gram']['pooled_ratio']:.3f}). \"Fluent\" is not what the corpus is.")


def _t_E4(R):
    v = R["E4"]["value"]; s = v["strata"]; c = v["instrument_check"]; gs = v["grid_summary"]
    return (f"the all-rows tie reproduces (amber {c['amber_v0_recomputed']:.4f} vs AC-under-draft {c['ac_json']:.4f} bits/token) and is a mixture: "
            f"concatenated, non-looped rows ({s['nonlooped']['rows']} rows, {s['nonlooped']['N']} tokens) amber {s['nonlooped']['amber_concat']:.4f} vs AC "
            f"{s['nonlooped']['ac']:.4f} ({s['nonlooped']['delta_concat']:+.4f}); looped rows ({s['looped']['rows']}, {s['looped']['N']}) "
            f"{s['looped']['amber_concat']:.4f} vs {s['looped']['ac']:.4f} ({s['looped']['delta_concat']:+.4f}). The per-archive direction "
            f"depends on the loop rule: across the {gs['settings']} grid settings the sign split holds at {gs['sign_split_holds_at']}, while "
            f"amber's per-archive rate on non-looped rows runs from {gs['rel_perarchive_nonlooped_min']:+.1%} to "
            f"{gs['rel_perarchive_nonlooped_max']:+.1%} against AC (positive at {gs['rel_perarchive_nonlooped_positive_at']}), so no "
            f"per-archive direction is stated.")


def _t_E5(R):
    v = R["E5"]["value"]
    return (f"the printed figure is the unweighted mean of {v['n']} per-shard rates ({v['unweighted']:.1f} tok/s); token-weighted, "
            f"{v['units_total']:.0f} tokens in {v['seconds_total']:.0f} s is {v['weighted']:.1f} tok/s; median shard {v['median']:.1f}, "
            f"range {v['min']:.1f}-{v['max']:.1f}.")


def _t_E6(R):
    v = R["E6"]["value"]; p = v["pinned"]; grid = "; ".join(f"f={x['f']}: {x['n_stalled']} stalled, clean {x['clean']:.0f}" for x in v["grid"])
    return (f"the aggregate reproduces ({p['aggregate']:.0f} pos/s over {p['n_rows']} rows, {p['seconds_total']:.1f} s) but {p['n_stalled']} rows "
            f"under {p['f']}x the median per-row rate hold {p['seconds_stalled']:.1f} of those seconds; excluding them the rate is "
            f"{p['clean']:.0f} pos/s (median per-row rate {p['median_v']:.0f}); grid: {grid}.")


def _t_E7(R):
    v = R["E7"]["value"]
    return (f"reproduces ({v['a_as_printed']:.4f} bits per generated token with zstandard {v['zstandard_version']}, tokenizer snapshot "
            f"{v['snapshot'][:8]}); the per-archive text includes decoded special-token literals ({v['n_rows_with_bot']} of {v['n_rows']} archives "
            f"carry <|begin_of_text|>, {v['n_rows_with_eot']} carry <|end_of_text|>, {v['literal_bytes']} B in all); without them "
            f"{v['b_skip_special']:.2f}.")


def _t_E8a(R):
    v = R["E8a"]["value"]; by = v["desync_total_by_theta_m"]; nz = sorted({k.split("/")[0] for k in by if not k.startswith("0.0/")})
    od = R["E8c"]["value"]["order_differences_vs_cpu_fp32"]["cuda_fp32_b1"]
    return (f"at theta 0 (the shipped default) cpu_fp32 -> cuda_fp32_b1 has {v['desync_total_theta0']} desync in {v['n']} positions "
            f"(class A, gap {v['A_desync_gap_max_theta0']:.2e}); {v['desync_total_escape_on']} at theta in {{{', '.join(nz)}}}, as F-10's body "
            f"states, so the headline's zero is the escape-on count and the shipped contract has one. As an ORDER claim (OQ-2) it is false at "
            f"every theta: the top-64 order differs from cpu_fp32 at {od['positions_top64_order_differs']} positions, every one a near-tie (the "
            f"largest encoder gap between the two tokens competing for the first differing slot is "
            f"{od['max_encoder_gap_between_tokens_competing_for_first_differing_slot']:.2e}); what is stable is the resolved token, and only "
            f"at batch 1 with the escape on.")


def _t_E8b(R):
    v = R["E8b"]["value"]
    return (f"confirmed: {v['n_fail_total']} failures over {v['positions_total']} replayed positions "
            f"({v['cuda_fp32']['n_rows']} GPU archives with {v['cuda_fp32']['positions']} positions, {v['cpu_fp32']['n_rows']} CPU with "
            f"{v['cpu_fp32']['positions']}, which F-11 prints rounded to the hundred); F-11's own results/p4_real_archive.json is read into the payload.")


def _t_E8c(R):
    v = R["E8c"]["value"]; ev = v["events"]; od8 = v["order_differences_vs_cpu_fp32"]["cuda_fp32_b8"]
    evs = "; ".join(f"sequence {e['sequence']} offset {e['offset']}: the true token at encoder rank {e['enc_rank_of_true']} resolves at decoder rank "
                    f"{e['dec_rank_of_true']}; the swapped pair sits {e['enc_gap_at_swapped_pair']:.2e} apart (top-1 to top-2 gap {e['enc_gap_top1_top2']:.3f})"
                    for e in ev)
    persists = [k for k, n in v["desync_total_by_theta_m"].items() if n > 0]
    return (f"the batch-8 fp32 decoder P2b never ran: cpu_fp32 -> cuda_fp32_b8 has {v['desync_total']} desync in {v['n']} positions at theta 0 "
            f"({evs}); it persists under the escape at theta/m {', '.join(persists)}; top-64 order differs at {od8['positions_top64_order_differs']} "
            f"positions. \"All ranks to 64\" holds for the fp32 decoder only at batch 1 with the escape on (theta above zero), and for batch 8 at no theta.")


def _t_E9(R):
    v = R["E9"]["value"]; tb = v["tables"]["cpu_fp32"]; ck = v["printed_figure_checks"]

    def arm(dec):
        t = tb[dec]; b = t["buckets"]
        top1 = pct(t["primary"]["1"], 2) + (f" ({t['desyncs_A']} of {t['symbol_counts']['A']})" if "desyncs_A" in t else "")
        return (f"{dec}: top-1 {top1}, rank 2 {pct(t['primary']['2'])}, ranks 3-8 {pct(b['3-8']['primary'])}, "
                f"9-16 {pct(b['9-16']['primary'])}, 17-64 {pct(b['17-64']['primary'])}, overall {pct(t['overall'], 3)}")
    regime = ", ".join(v["claim_regime_rows"]); bf = tb["cuda_bf16_b1"]; fp = tb["cuda_fp16_b1"]
    return (f"F-10 does not state the theta of its per-rank table; every one of its {len(ck)} printed figures matches the theta/m row(s) {regime} "
            f"(escape on) and {sum(ck.values())} of them match at the shipped theta 0, where the rank-2 figures are {pct(bf['primary']['2'])} (bf16) and "
            f"{pct(fp['primary']['2'])} (fp16) and the other printed depths are unchanged. Depth table at theta 0, encoder cpu_fp32, per-class denominators: "
            f"{arm('cuda_bf16_b1')}; {arm('cuda_fp16_b1')}; {arm('cuda_fp32_b1')}.")


def _t_E10(R):
    v = R["E10"]["value"]; d = v["draft_scoring"]
    return (f"draft rank scoring {d['weighted']:.0f} positions/s token-weighted over {d['n']} shards ({d['unweighted']:.0f} unweighted); "
            f"{v['content_bytes_per_token']:.4f} bytes/token; amber v0 {v['amber_v0_bits_per_token']:.4f}, AC-under-draft "
            f"{v['ac_under_draft_bits_per_token']:.4f}, zstd-19 {v['zstd19_bits_per_token']:.4f} bits/token over {v['positions']} positions; "
            f"divergence {pct(v['divergence_rate'], 2)}.")


def _t_E11(R):
    v = R["E11"]["value"]; b = v["bomb"]
    return (f"a declared length of {v['bomb_length']}: the hf JSON path refuses before any work (\"{b['hf_json']['message']}\"); "
            f"the v3 binary path ({b['v3']['outcome']}) and the v4 session path ({b['v4']['outcome']}) begin work proportional to the declared length; "
            f"the control length {v['control_length']} reaches work on all three paths. F-4 was accurate for the JSON format it described; the ceiling "
            f"was not carried to the v3/v4 binary formats. Fixing binformat is a separate change (roundtrip + corruption tests).")


def _t_E12(R):
    v = R["E12"]["value"]
    return (f"no L1 path exists for real archives: attest_with_target replays the synthetic world and the hf header carries "
            f"{len(v['synthetic_keys_in_HF_REQUIRED'])} of the synthetic-world keys it reads; it mentions the payload on "
            f"{v['payload_lines_in_attest_with_target']} lines; attestation appears on {v['attest_lines_in_real_paths']} lines of the real-archive "
            f"code and the P4-P6 experiments, and across all of src/, experiments/, tools/ and tests/ only in "
            f"{', '.join(v['files_mentioning_attest_anywhere'])}. F-2's synthetic L1 stands as stated.")


def _t_E13(R):
    v = R["E13"]["value"]; pg = v["pages"]

    def page(aid):
        p = pg[aid]; return f"arXiv {aid}, \"{p['title']}\" ({'; '.join(p['authors'])}; page sha256 {p['sha256'][:12]})"
    pm = [a for a, ok in v["abstract_contains_pmatic"].items() if ok]
    return (f"PMATIC is {' and '.join(page(a) for a in pm)}; the cited id is {'; '.join(page(a) for a in pg if a not in pm)}, "
            f"a different paper that is relevant prior art in its own right (re-identify the citation, do not remove it); pages saved under "
            f"results/errata_web/.")


def _t_E14(R):
    v = R["E14"]["value"]
    return (f"no stage of the P7 pre-registration ran (results/p7 on disk: {str(v['results_p7_on_disk']).lower()}; tracked files: "
            f"{v['results_p7_tracked_files']}) and none will; the pre-registration stands as frozen text, withdrawn.")


def _t_E15(R):
    v = R["E15"]["value"]; a = v["arms"]; cr = v["claim_regime_rows"][0]; rc = v["regime_check"]; sh = v["instrument_check"]["shards"]
    bf = a["cuda_bf16_b1"]; fp = a["cuda_fp16_b1"]; gs = v["gap_shares"]; sides = rc["sides"]
    corpus = Path(gs["corpus"]["text_path"]).name if "corpus" in gs else "the P2 corpus"

    def prefix(arm):
        return sh[arm]["n_decoded_total"] / sh[arm]["archives"]

    def oe(x, c):
        e = x["compensator_theta0_h4"][c]; return f"{e['observed']:.0f} vs {e['expected']:.1f} ({e['ratio']:.2f}x, z {e['z']:+.1f})"

    def share(side, D):
        return pct(gs[side][D]["share"])
    zc = fp["compensator_theta0_h4"]["C"]["z"]
    noise = f" (fp16 within noise at z {zc:+.1f})" if abs(zc) < 2 else ""
    import math

    def c_fail(x):                                    # C-caused failures against the C-hazards-only prediction, in binomial sd of the predicted rate
        n = x["measured"]["archives"]; o = x["compensator_theta0_h4"]["C"]["observed"]; p = x["fail_exact"]["c_only_theta0_h4"]["fail_rate"]
        return {"n": n, "o": o, "rate": o / n, "pred": p, "sd_units": (o / n - p) / math.sqrt(p * (1 - p) / n)}
    cb, cfp = c_fail(bf), c_fail(fp)
    direction = ("the same direction" if cb["sd_units"] > 0 and cfp["sd_units"] > 0 else "the direction reverses on the failure metric")
    noise2 = ", within noise" if max(abs(cb["sd_units"]), abs(cfp["sd_units"])) < 2 else ""
    return (f"F-10's figures reproduce in their own regime: weighting P2b's per-rank C-desync rates at theta/m {cr} by P1's rank histogram gives one "
            f"C-desync per {bf['c_only'][cr]['h1']['one_in']:.0f} target-generated tokens for bf16 (set-coded {bf['setcoded_c_only_claim_regime_h1']['one_in']:.0f}) "
            f"and per {fp['c_only'][cr]['h1']['one_in']:.0f} for fp16 (set-coded {fp['setcoded_c_only_claim_regime_h1']['one_in']:.0f}), and "
            f"1 - exp(-{v['Lbar']:.0f}/N) from them prints the {100 * bf['fail_poisson']['c_only_claim_regime_h1']:.0f}% and "
            f"{100 * fp['fail_poisson']['c_only_claim_regime_h1']:.0f}% F-11 compared its failure rates against. That regime is the escape on, and the "
            f"prediction counts C desyncs only; F-11 decoded with the escape off (the {rc['archives']} archives' {rc['positions']} coded symbols hold "
            f"{rc['flag_totals']['T']} "
            f"escapes), where rank-1 desyncs count too, so the printed comparison crossed regimes. The theta-0 all-class prediction, weighted by the "
            f"archives' own coded ranks, is one desync per {bf['all_theta0']['h4']['one_in']:.1f} tokens for bf16 and per {fp['all_theta0']['h4']['one_in']:.1f} "
            f"for fp16, with whole-archive failure rates {pct(bf['fail_exact']['all_theta0_h4']['fail_rate'])} and "
            f"{pct(fp['fail_exact']['all_theta0_h4']['fail_rate'])}; F-11 measured one first desync per {bf['measured']['one_in']:.1f} and "
            f"{fp['measured']['one_in']:.1f} decoded positions (a hazard over decoded prefixes of mean {prefix('cuda_bf16'):.0f} and {prefix('cuda_fp16'):.0f} "
            f"positions: decode stops at the first desync) and failure rates {pct(bf['measured']['fail_rate'])} and {pct(fp['measured']['fail_rate'])}, so "
            f"under the pinned all-class rule {len(v['reversals'])} of {2 * len(a)} comparisons reverse. Split by class over the positions actually decoded "
            f"(observed first desyncs against the expected count): rank-1 desyncs bf16 {oe(bf, 'A')}, fp16 {oe(fp, 'A')}; corrections bf16 {oe(bf, 'C')}, "
            f"fp16 {oe(fp, 'C')}. F-11's direction holds for corrections on both arms{noise}; on the failure metric, C-caused failures are "
            f"{pct(cb['rate'])} and {pct(cfp['rate'])} ({cb['o']:.0f} and {cfp['o']:.0f} of {cb['n']}) against {pct(cb['pred'])} and {pct(cfp['pred'])} "
            f"with correction hazards alone: {direction}, by {cb['sd_units']:.1f} and {cfp['sd_units']:.1f} binomial sd of the predicted rate{noise2}. "
            f"The all-class reversal is the rank-1 term, which P2b's rank-only rate over-predicts here: the share of rank-1 positions with a top-2 gap "
            f"under the bf16 pair budget is "
            f"{share('p2_dumps_rank1', 'cuda_bf16_b1')} in the dumps ({sides['p2b']['model']}, teacher-forced windows of {corpus}) and "
            f"{share('p4_archives_rank1', 'cuda_bf16_b1')} in the archives ({sides['p4']['draft']}, target-generated text, incremental KV); under the fp16 "
            f"budget {share('p2_dumps_rank1', 'cuda_fp16_b1')} and {share('p4_archives_rank1', 'cuda_fp16_b1')}. The pinned rule scored a corrections claim "
            f"on an all-class quantity, a protocol defect recorded in the amendment log; whether the correction excess is a property of target-generated "
            f"content is not identified, since model, content and kernel path all differ.")


def _t_E16(R):
    v = R["E16"]["value"]; A = v["arms"]; b1 = A["cuda_fp32_b1"]; b8 = A["cuda_fp32_b8"]; eg = v["encoder_top2_gap_quantiles"]; td = v["tau_definition"]
    d1 = b1["drift"]; d8 = b8["drift"]; nctx = b1["distinct_contexts_above_budget"]
    adj = "always the adjacent token" if b1["n_nonadjacent"] == 0 else f"{b1['n_nonadjacent']} of them not adjacent"
    evs = "; ".join(f"sequence {e['sequence']} offset {e['offset']}, slot {e['slot_j']}, gap {e['g']:.2e} ({e['g'] / b1['budget']:.1f}x the budget), "
                    f"pair drift {e['pair_drift']:.2e}" for e in b1["events_above_budget"])

    def buckets(s):
        items = sorted(s["by_slot_bucket"].items(), key=lambda kv: int(kv[0].split("-")[0]))
        return "; ".join(f"slot{'s' if '-' in k else ''} {k}: {x['n']}" + (f" ({x['above_budget']} above)" if x["above_budget"] else "") for k, x in items)

    def qs(d):
        items = sorted(d["abs_delta_q_by_slot_bucket"].items(), key=lambda kv: int(kv[0].split("-")[0]))
        return ", ".join(f"slot{'s' if '-' in k else ''} {k}: {x['q']:.1e}" for k, x in items)
    info = "; ".join(f"{D}: order differs at {s['n_diff']} of {v['n']} ({s['distinct_contexts']} contexts), {s['count_above_budget']} above its budget "
                     f"{s['budget']:.2e}" for D, s in A.items() if s["role"] == "informational")
    slot0 = "; ".join(f"{D} {s['by_slot_bucket']['0']['above_budget']} of {s['by_slot_bucket']['0']['n']}" for D, s in A.items())
    return (f"the top-64 order of cuda_fp32_b1 differs from cpu_fp32 at {b1['n_diff']} of {v['n']} positions ({b1['distinct_contexts']} distinct contexts); "
            f"the encoder gap between the two tokens competing for the first differing slot ({adj}) has median {b1['g_quantiles']['p50']:.1e} and max "
            f"{b1['g_quantiles']['max']:.2e} against an encoder top-2 gap of median {eg['p50']:.2f} (p01 {eg['p01']:.3f}), so F-14's \"every one a "
            f"near-tie\" holds at logit scale; at the record's fp32 pair budget 2(tau_enc + tau_dec) = {b1['budget']:.1e}, which that sentence did not "
            f"state, {b1['count_above_budget']} positions exceed it, {nctx} distinct context{'s' if nctx != 1 else ''} ({evs}): a tail drift, not "
            f"evidence of a pipeline bug, since tau is the {td['quantile']} quantile of the aligned top-{td['topk_used']} deltas (not a top-1 "
            f"calibration), that quantile falls with depth on this arm ({qs(d1)}), and {d1['adjacent_pairs_drift_above_budget']} of "
            f"{d1['adjacent_pairs']} adjacent top-64 pairs drift by more than the budget. By first differing slot: {buckets(b1)}. At slot 0, the scope "
            f"of every claim site (F-7's and OQ-2's top-1 flips, F-10's A desyncs), the counts above budget are {slot0}: the top-1 claims stand. At "
            f"batch 8 ({b8['n_diff']} positions, {b8['distinct_contexts']} contexts, max {b8['g_quantiles']['max']:.2e}) {b8['count_above_budget']} exceed "
            f"that arm's 2 tau of {b8['budget']:.2e} (a census-derived proxy; P2b has no batch-8 budget) and {d8['adjacent_pairs_drift_above_budget']} of "
            f"{d8['adjacent_pairs']} adjacent pairs drift by more than it. The other decoders at depth, informational: {info}.")


def _g(x, nd=3):
    return "none" if x is None else f"{x:.{nd}g}"


def _short(arm):
    return arm.replace("cuda_", "").replace("_b1", "")


def _t_E17(R):
    v = R["E17"]["value"]; th = v["p2b_thetas_over_llama_tau"]; S = v["sites"]
    label_sites = {n: s for n, s in S.items() if "arms" in s}

    def labels(name, s):
        parts = []
        for arm, a in s["arms"].items():
            parts.append(f"{_short(arm)} {a['label']} is {a['multiple']} tau (tau {_g(a['tau'], 4)}; printed {a['printed_beyond']} beyond, census "
                         f"{a['census_beyond_at_2tau']} beyond 2 tau = {_g(a['tau_field'], 4)}; largest flip gap {_g(a['flip_gap_max'])})")
        return name + ": " + "; ".join(parts)

    def cost(name, s):
        c = s["escape_cost"]
        if "mass_pct_at_2tau" not in c:
            return f"{name}: the escape cost was not recomputed ({'; '.join(c.get('problems') or ['dumps unavailable'])})"
        rep = ", ".join(f"{c['mass_pct'][k]:.1f}% at {k} (printed {c['printed_mass_pct_at'][k]})" for k in c["printed_mass_pct_at"])
        at2 = "; ".join(f"{_short(arm)} {c['mass_pct_at_2tau'][arm]:.1f}% at 2 tau = {_g(c['two_tau'][arm], 3)} against the printed {c['printed_cost_pct'][arm]}%"
                        for arm in c["two_tau"])
        return f"{name}: the near-tie mass reproduces at the printed thresholds ({rep}), and at the census's 2 tau it is {at2}"
    oq = S.get("OPEN_QUESTIONS.md:16") or {}
    oq_txt = (f"; OPEN_QUESTIONS.md:16 repeats the printed {oq['printed_cost_pct']['cuda_fp16_b1']}% and {oq['printed_cost_pct']['cuda_bf16_b1']}%"
              if oq.get("printed_cost_pct") else "")
    thetas = ", ".join(f"{t} ({x['over_fp16_tau']:.1f} fp16 tau, {x['over_bf16_tau']:.1f} bf16 tau)" for t, x in th.items())
    two = [t for t, x in th.items() if round(x["over_bf16_tau"]) == 2]
    return (f"{v['n_labels_4tau']} of the {v['n_labels']} printed \"2tau\" thresholds are 4 tau and {v['n_labels_2tau']} is 2 tau by the census's own "
            f"calibrated tau; every printed beyond-count equals the census's count, which the census took at 2 tau (its per-row tau field holds 2 tau "
            f"and its beyond-count compares each flip gap with that field), so the claims \"every flip within 2 tau\" stand. The escape-cost figures "
            f"quoted at those labels do not: {'. '.join(cost(n, s) for n, s in label_sites.items())}{oq_txt}. Labels: "
            f"{'. '.join(labels(n, s) for n, s in label_sites.items())}. P2b's escape thresholds, taken from F-5's labels, are {thetas}"
            + (f"; {', '.join(two)} is bf16's 2 tau, the setting the record used" if two else "") + ".")


def _t_E18(R):
    v = R["E18"]["value"]; pa = v["per_archive"]; z = pa["zstd"]; cf = v["concatenated_full_text"]; ct = v["content"]; ss = v["sessions"]
    rs = v["repetition_split"]; ef = v["effects"]; sp = v["split"]; k16 = "16384"; thr = v["threshold"]
    hd = v["harvest_definitions"]; ewl = v["effects_without_literals"]
    sizes = sorted((k for k in z if k != "none"), key=int); dinfo = v["dictionaries"]
    dict_list = ", ".join(f"{z[k]:.3f} with a {dinfo[k]['bytes']} B dictionary (requested {int(k) // 1024} KB)" for k in sizes)

    def sess(k):
        s = ss[k]
        return (f"k={k[1:]} ({s['sessions']} sessions): amber v4 {s['amber_v4_reset']:.2f}, zstd-19 {s['zstd_none']:.2f} without and {s['zstd_16384']:.2f} "
                f"with the 16 KB dictionary (multiples {s['multiple_none']:.1f}x and {s['multiple_16384']:.1f}x; effect {pct(s['effect'], 0)})")
    scale = lambda e: "strawmen" if e > thr else "fair"  # noqa: E731
    return (f"on the held-out half (P1 rows {sp['held_rows'][0]}-{sp['held_rows'][1]}, {sp['G']} generated tokens; dictionaries trained on rows "
            f"{sp['train_rows'][0]}-{sp['train_rows'][1]}), per archive on the full text: zstd-19 {z['none']:.3f} bits per generated token without a "
            f"dictionary (the text carries the special-token literals E7 found, which a dictionary absorbs), {dict_list}; amber v3 {pa['amber_v3']:.3f} "
            f"({pa['amber_v3_payload_only']:.3f} without its {pa['fixed_header_bytes']} B fixed header). The 16 KB dictionary lowers the comparator by "
            f"{pct(ef['arch'], 0)}; amber's per-archive advantage is "
            f"{pa['ratio_zstd_over_amber']['none']:.2f}x without it and {pa['ratio_zstd_over_amber'][k16]:.2f}x with it "
            f"({pa['zstd_16384_amortised']:.3f} for zstd once the dictionary's own bytes are spread over these archives). Sessions in reset mode whose "
            f"rows are all held out: {sess('k16')}; {sess('k8')}. Concatenated full text: {cf['zstd']['none']:.2f} without and {cf['zstd'][k16]:.2f} with "
            f"the dictionary (effect {pct(ef['concat'], 0)}); by F-12's rate law the crossover moves from L {cf['crossover_L']['none']:.0f} to "
            f"{cf['crossover_L'][k16]:.0f}. Content, concatenated generated text: amber v0 {ct['amber_v0_held']:.4f} against zstd-19 "
            f"{ct['zstd_gen_concat']['none']:.3f} without and {ct['zstd_gen_concat']['gen_16384']:.3f} with a dictionary trained on generated text "
            f"(effect {pct(ef['gen_concat'], 0)}): {ct['multiple']['none']:.1f}x and {ct['multiple']['gen_16384']:.1f}x. On the {rs['rows']} held-out "
            f"rows whose repeat-4-gram share is below one half: amber v3 {rs['amber_v3_arch']:.2f} against dictionary zstd {rs['zstd_arch_16384']:.2f} "
            f"({rs['zstd_arch_none']:.2f} without). Under the harvest's own definitions (special tokens skipped; repeat share over the row length) the "
            f"same quantities are {hd['zstd_arch']['none']:.3f} and {hd['zstd_arch'][k16]:.3f} per archive and, on {hd['rep_rows']} rows, "
            f"{hd['rep_amber_v3_arch']:.3f} against {hd['rep_zstd_arch_16384']:.3f}, which is what its predictions were; without the literals the "
            f"effects are {pct(ewl['arch'], 0)} per archive, {pct(ewl['session16'], 0)} and {pct(ewl['session8'], 0)} for the sessions and "
            f"{pct(ewl['concat'], 0)} concatenated, every status unchanged. D-6's zstd rows were {scale(ef['arch'])} at the per-archive scale, "
            f"{scale(ef['session16'])} at the session scale and {scale(ef['concat'])} at the concatenated scale; the dictionaries were trained on the "
            f"other half of the same prompt families, which favours zstd.")


def _t_E19(R):
    r = R["E19"]; v = r["value"]; A = v["arms"]; prim = v["primary"]

    def arm(D, tag):
        a = A[D]; p = a["by_binning"][prim]; ro = a["rank_only"]; m = a["measured"]; iv = a["oe_interval_primary"]; mg = a["margins_primary"]
        return (f"{tag}: {p['E_A']:.1f} rank-1 first desyncs predicted against {p['O_A']:.0f} observed (z {p['z']:+.1f}; observed over expected "
                f"{iv['ratio']:.2f}, {int(100 * iv['level'])}% interval {iv['low']:.2f} to {iv['high']:.2f}; rank-only {ro['expected']:.1f}, z {ro['z']:+.1f}), "
                f"{a['grid_E_A_range'][0]:.1f} to {a['grid_E_A_range'][1]:.1f} with z {a['grid_z_range'][0]:+.1f} to {a['grid_z_range'][1]:+.1f} across the "
                f"{a['binnings']} binnings; with that term and the rank-only correction term the theta-0 prediction is one desync per {p['one_in']:.0f} "
                f"tokens and {pct(p['fail_exact'])} failure against the measured one per {m['one_in']:.1f} and {pct(m['fail_rate'])} (margins "
                f"{mg['one_in_predicted_over_measured_minus_1']:+.1%} and {100 * mg['fail_measured_minus_predicted']:+.1f} points), E15's rule holding at "
                f"{a['e15_rule_holds_at_binnings']} of {a['binnings']} binnings")
    nb = A["cuda_bf16_b1"]["by_binning"][prim]["bins"]
    excl = "; ".join(f"{tag} {1 - A[D]['oe_interval_primary']['low']:.0%}" for D, tag in (("cuda_bf16_b1", "bf16"), ("cuda_fp16_b1", "fp16")))
    return (f"in the dumps the rank-1 desyncs sit at small top-2 gaps; binning the dumps' {v['dump_rank1_positions']} rank-1 gaps into {nb} equal-count "
            f"bins and applying each bin's desync rate to the archives' rank-1 positions over the decoded prefixes gives {arm('cuda_bf16_b1', 'bf16')}; "
            f"{arm('cuda_fp16_b1', 'fp16')}. That is consistent with transfer at this sample size, which cannot exclude an archive rank-1 rate below "
            f"the dumps' by {excl}; E15's pinned rule returns {r['status_e15_rule_gap_conditioned']} at the primary binning once the rank-1 term is "
            f"conditioned on the gap. The primary binning is the second batch's critic's own post-hoc binning, so its values were in the record before "
            f"this rule was written; the other binnings are the out-of-sample evidence ({r['status_out_of_sample']}). The rank-only rank-1 rate did "
            f"not transfer (E15, F-10's caveat corrected); the correction term stays rank-only, since the P4 streams carry no gaps beyond the top-2, and "
            f"its excess stays unexplained.")


TEXT_FNS = {"E1": _t_E1, "E2": _t_E2, "E3": _t_E3, "E4": _t_E4, "E5": _t_E5, "E6": _t_E6, "E7": _t_E7, "E8a": _t_E8a, "E8b": _t_E8b,
            "E8c": _t_E8c, "E9": _t_E9, "E10": _t_E10, "E11": _t_E11, "E12": _t_E12, "E13": _t_E13, "E14": _t_E14, "E15": _t_E15, "E16": _t_E16,
            "E17": _t_E17, "E18": _t_E18, "E19": _t_E19}


def row_texts(P: dict) -> dict[str, str]:
    R = P["rows"]
    return {rid: esc(TEXT_FNS[rid](R)) for rid in rows_present(P)}


def score_predictions(P: dict) -> dict[str, list[str]]:
    """Prediction keys that share a name with a value key, scored at the prediction's own precision."""
    out = {}
    for rid in rows_present(P):
        r = P["rows"][rid]; hits = []; src = (r.get("value") or {}).get("prediction_sources") or {}
        if not r.get("prediction") and (r.get("value") or {}).get("prediction_note"):
            out[rid] = [r["value"]["prediction_note"]]; continue

        def tag(k):
            return f" ({'harvest' if 'harvest' in src[k] else 'critic' if 'critic' in src[k] else 'protocol'})" if k in src else ""
        for k, pv in (r.get("prediction") or {}).items():
            vv = r["value"].get(k)
            if isinstance(pv, bool) or isinstance(vv, bool):
                if isinstance(vv, bool):
                    hits.append(f"{k} {'hit' if vv == pv else 'miss'}{tag(k)}")
            elif isinstance(pv, (int, float)) and isinstance(vv, (int, float)):
                nd = len(str(pv).split(".")[1]) if isinstance(pv, float) and "." in str(pv) else 0
                hits.append(f"{k} {'hit' if round(vv, nd) == round(pv, nd) else 'miss'}{tag(k)}")
        if hits:
            out[rid] = hits
    return out


def claim_site_counts(P: dict) -> tuple[int, int]:
    """(claim sites standing at their own scope, claim sites) over the rows present; a row without
    status_by_claim_site counts as one site with its pinned status."""
    stand = total = 0
    for rid in rows_present(P):
        r = P["rows"][rid]
        for st in (r.get("status_by_claim_site") or {"": r["status"]}).values():
            total += 1; stand += st == "CONFIRMED"
    return stand, total


def site_tokens(key: str) -> list[tuple[str, int]]:
    return [(m.group(1), int(m.group(2))) for m in re.finditer(r"([\w./-]+\.md):(\d+)", key)]


def location_label(P: dict, rids: list[str], file: str, lo: int, hi: int) -> str:
    """'erratum' where, in lines lo..hi of `file`, a row's claim-site status is not CONFIRMED or a row's pinned rule scores
    a site there (a row without claim-site fields counts by its pinned status); 'note' otherwise."""
    def inside(key):
        return any(f == file and lo <= n <= hi for f, n in site_tokens(key))
    for rid in rids:
        r = P["rows"][rid]; sites = r.get("status_by_claim_site")
        if not sites:
            if r["status"] != "CONFIRMED":
                return "erratum"
            continue
        if any(st != "CONFIRMED" and inside(key) for key, st in sites.items()):
            return "erratum"
        if r["status"] != "CONFIRMED" and any(inside(w) for w in (r.get("value") or {}).get("pinned_rule_sites") or []):
            return "erratum"
    return "note"


def status_bracket(r: dict) -> str:
    st = r["status"]
    if r.get("status_under_pinned_rule"):
        st += f"; {r['status_under_pinned_rule']} under the pinned rule, decided by the {r['amended_by']}"
    if r.get("status_in_claim_regime"):
        st += f"; {r['status_in_claim_regime']} in the claim's own regime"
    if r.get("status_by_class"):
        st += "; by class over the decoded positions: " + ", ".join(f"{c} {s}" for c, s in r["status_by_class"].items())
    if r.get("status_by_count"):
        st += f"; {r['status_by_count']} by beyond-count"
    if r.get("post_hoc"):
        st += f"; post hoc: {r['post_hoc']}"
    if r.get("status_out_of_sample"):
        st += f"; {r['status_out_of_sample']} out of sample (the other binnings)"
    if r.get("status_by_arm"):
        st += "; by arm: " + ", ".join(f"{arm} {s}" for arm, s in r["status_by_arm"].items())
    if r.get("status_at_claim_scope"):
        st += "; at the claims' own scope, slot 0: " + ", ".join(f"{arm} {s}" for arm, s in r["status_at_claim_scope"].items())
    if r.get("status_by_claim_site"):
        st += "; by claim site: " + ", ".join(f"{site} {s}" for site, s in r["status_by_claim_site"].items())
    if r.get("status_under_pinned_tolerance"):
        diff = [f"{site} {s}" for site, s in r["status_under_pinned_tolerance"].items() if s != r["status_by_claim_site"].get(site)]
        if diff:
            st += "; under the entry's original tolerance " + ", ".join(diff) + f", decided by {r['amended_by']}"
    return st


def row_bullets(P: dict, T: dict[str, str]) -> list[str]:
    return [f"  - {rid} [{status_bracket(P['rows'][rid])}] {esc(P['rows'][rid]['claim'])} ({', '.join(esc(w) for w in P['rows'][rid]['where'])}): {T[rid]}"
            for rid in rows_present(P)]


def status_counts(P: dict) -> tuple[int, int, int]:
    S = P["summary"]
    return (sum(1 for s in S.values() if s == "CORRECTED"), sum(1 for s in S.values() if s == "CONFIRMED"),
            sum(1 for s in S.values() if s == "UNRECOMPUTABLE"))


# ----------------------------------------------------------------------------
# finding blocks
# ----------------------------------------------------------------------------


def f14_block(P: dict, T: dict[str, str]) -> str:
    pv = P["provenance"]; S = P["summary"]; d = date_of(P)
    n_corr, n_conf, n_unr = status_counts(P)
    n_amended = sum(1 for r in P["rows"].values() if r.get("status_under_pinned_rule"))
    sc = score_predictions(P)
    lines = [
        f"## F-14 — {d[:7]} errata pass: {n_corr} of {len(S)} checked claims corrected, {n_conf} confirmed, {n_unr} unrecomputable "
        f"({n_amended} decided only through logged amendments); the record is amended append-only from a pre-registered recompute of the committed evidence",
        f"- date: {d}",
        f"- regime: recompute of printed claims from evidence committed at amber {pv['head'][:7]} (tree {pv['tree'][:7]}), CPU only "
        f"(torch blocked: {str(pv['torch_blocked']).lower()}), python {pv['python']}, numpy {pv['numpy']}, zstandard {pv['zstandard']}, "
        f"transformers {pv['transformers']} (E7's tokenizer only, offline); rules pre-registered in experiments/ERRATA_PROTOCOL.md "
        f"(blob {pv['inputs']['experiments/ERRATA_PROTOCOL.md'][:12]}) with a dated amendment log; the review harvest's values (docs/ERRATA_PLAN.md) "
        f"were scored predictions, never citations; every numeral in this entry is generated from results/errata_recompute.json by experiments/errata_text.py",
        "- source: results/errata_recompute.json, experiments/ERRATA_PROTOCOL.md, experiments/errata_recompute.py, experiments/errata_lib.py, "
        "experiments/errata_text.py, tests/test_errata_recompute.py, tests/test_errata_text.py, results/errata_web/, results/errata_dryruns/, "
        "results/errata_critic/, docs/ERRATA_PLAN.md",
        "- finding: one bullet per protocol row (claim as printed; recomputed value; status under the pinned rule, and where the protocol's amendment "
        "log says so, the status under the pinned rule before the amendment or in the claim's own regime). Values are addressable as "
        "rows.<id>.value.<key> in the payload; the critic's independent recompute (results/errata_critic/) reproduced every value.",
    ]
    lines += row_bullets(P, T)
    lines.append("- predictions scored (the harvest's values, where a prediction key names a payload key): "
                 + "; ".join(f"{rid}: {', '.join(h)}" for rid, h in sc.items()) + ".")
    lines.append("- not carried: the harvest's product-positioning rewrites (BLUEPRINT economics and phases, WHY_THIS_DIES status lines, the patent and FTO "
                 "readings, the OQ-3 / OQ-4 priced states, the D-6 dictionary-zstd amendment, CLAUDE.md rule additions, pyproject extras) and its protocol "
                 "fixes: the thesis is parked and those documents describe a product no reader will see. The original finding texts are never rewritten; "
                 "each affected finding carries one dated erratum line pointing here.")
    lines.append(f"- caveats: one box, one recompute; E8c reads local dumps pinned by results/p2_dumps.sha256 (not in the repo); E13 reads two saved web pages; "
                 f"the pinned loop and stall rules are choices, with their sensitivity grids in the payload; E11 records a regression and does not fix it.")
    return "\n".join(lines) + "\n"


def f15_block(P: dict, T: dict[str, str]) -> str:
    pv = P["provenance"]; S = P["summary"]; d = date_of(P); rows = rows_present(P)
    n_corr, n_conf, n_unr = status_counts(P); stand, total = claim_site_counts(P)
    sc = score_predictions(P)
    lines = [
        f"## F-15 — {d[:7]} errata pass, second batch (rows {', '.join(rows)}): {n_corr} of {len(S)} rows corrected under their pinned rules, "
        f"{n_conf} confirmed, {n_unr} unrecomputable, both rules carrying a recorded defect, {stand} of {total} claim-site statuses standing at their own scope; "
        f"F-11's comparison of its failure rates with F-10's prediction crossed escape regimes while corrections stay more fragile than predicted, and "
        f"F-14's \"every one a near-tie\" gets the threshold the record's own instrument uses while the top-1 claims it was read from stand",
        f"- date: {d}",
        f"- regime: recompute of printed claims from evidence committed at amber {pv['head'][:7]} (tree {pv['tree'][:7]}), CPU only "
        f"(torch blocked: {str(pv['torch_blocked']).lower()}), python {pv['python']}, numpy {pv['numpy']}; both rows pre-registered as the dated "
        f"\"second batch\" entry of experiments/ERRATA_PROTOCOL.md, committed before the first code for them (the history shows that order; the order "
        f"of writing is self-reported); the file's blob at this payload's head "
        f"({pv['inputs']['experiments/ERRATA_PROTOCOL.md'][:12]}) holds that entry, a post-dry-run entry (one informational field) and the post-critic "
        f"entries that added the by-class, claim-scope and claim-site statuses in the brackets below and corrected the generated text; both rows were "
        f"proposed by F-14's critic, whose values are this batch's scored predictions, never citations; every numeral in this entry is generated from "
        f"results/errata_recompute_2.json by experiments/errata_text.py",
        "- source: results/errata_recompute_2.json, experiments/ERRATA_PROTOCOL.md, experiments/errata_recompute.py, experiments/errata_lib.py, "
        "experiments/errata_text.py, tests/test_errata_recompute.py, tests/test_errata_text.py, results/errata_dryruns/dry_b2_pre.json, "
        "results/errata_dryruns/dry_b2.json, results/errata_critic/REPORT.md",
        "- finding: one bullet per row (claim as printed; recomputed value; status under the pinned rule, with the status in the claim's own regime, by "
        "symbol class, per decoder arm and per claim site where the protocol defines one). Values are addressable as rows.<id>.value.<key> in the "
        "payload; the critic's independent recompute (results/errata_critic/REPORT.md, second batch) reproduced every value.",
    ]
    lines += row_bullets(P, T)
    lines.append("- predictions scored (each labelled by its source, the critic's values or this protocol's own, where a prediction key names a payload key): "
                 + "; ".join(f"{rid}: {', '.join(h)}" for rid, h in sc.items()) + ".")
    lines.append("- caveats: one box, one recompute; both pinned rules carry a protocol defect recorded in the amendment log after the critic's passes (a "
                 "corrections claim scored on an all-class quantity; top-1 claims scored at depth), with the status at each claim's own scope beside the "
                 "pinned one. E15's measured rate is a hazard over the decoded prefix, its prediction weights teacher-forced dump rates (the instruct "
                 "draft on wiki text, one forward per window) by the archives' coded ranks (the base draft on target-generated text, incremental KV), "
                 "and the per-class split carries no noise allowance beyond the z scores printed; E16 reads local dumps pinned by "
                 "results/p2_dumps.sha256, its batch-8 budget is a census-derived proxy, every budget is a quantile of aligned top-64 deltas rather than a "
                 "bound, and the order-differing positions are not independent contexts. Observed while pinning, unscored and recorded in the protocol's "
                 "amendment log: F-5's four and F-7's bf16 and int8 printed \"2tau\" thresholds are four times the census tau (F-7's fp16 label is 2 tau), "
                 "while the census's own beyond-2tau counts were taken at 2 tau: a label defect, a candidate row for a later batch. The original finding "
                 "texts are never rewritten; each finding a row points into carries one dated line pointing here, labelled erratum where a site there is "
                 "corrected or is the site a pinned rule scores, and note where every site there stands.")
    return "\n".join(lines) + "\n"


def f16_block(P: dict, T: dict[str, str]) -> str:
    pv = P["provenance"]; S = P["summary"]; d = date_of(P); rows = rows_present(P)
    n_corr, n_conf, n_unr = status_counts(P); stand, total = claim_site_counts(P); sc = score_predictions(P)
    e17 = P["rows"]["E17"]["value"]; e18 = P["rows"]["E18"]; e19 = P["rows"]["E19"]
    t17 = f"{e17['n_labels_4tau']} of {e17['n_labels']} printed \"2tau\" labels are 4 tau"
    t18 = "the zstd baselines were strawmen at the per-archive scale" if e18["status"] == "CORRECTED" else "the zstd baselines hold at the per-archive scale"
    t19 = ((f"the dumps' rank-1 desync rate is consistent with transfer to the archives once conditioned on the top-2 gap (post hoc at the primary "
            f"binning; {e19.get('status_out_of_sample', 'unscored')} at the others)") if e19["status"] == "CONFIRMED"
           else "the dumps' rank-1 desync rate does not transfer to the archives even when conditioned on the top-2 gap")
    lines = [
        f"## F-16 — {d[:7]} errata pass, third batch (rows {', '.join(rows)}): {n_corr} of {len(S)} rows corrected under their pinned rules, "
        f"{n_conf} confirmed, {n_unr} unrecomputable, {stand} of {total} claim-site statuses standing at their own scope; {t17}, {t18}, and {t19}",
        f"- date: {d}",
        f"- regime: recompute of printed claims from evidence committed at amber {pv['head'][:7]} (tree {pv['tree'][:7]}), CPU only "
        f"(torch blocked: {str(pv['torch_blocked']).lower()}), python {pv['python']}, numpy {pv['numpy']}, zstandard {pv['zstandard']}; the three rows "
        f"pre-registered as the dated \"third batch\" entry of experiments/ERRATA_PROTOCOL.md, committed before the first code for them (the history "
        f"shows that order; the order of writing is self-reported), the file's blob at this payload's head being "
        f"{pv['inputs']['experiments/ERRATA_PROTOCOL.md'][:12]}; E18's predictions are the review harvest's, agent output scored after the run and never "
        f"cited; E17's label ratios and E19's primary values (the second batch's critic's own post-hoc binning) had been seen before the entry, are "
        f"recorded as such in the amendment log, and E19 is not scored; every numeral in this entry is generated from results/errata_recompute_3.json "
        f"by experiments/errata_text.py",
        "- source: results/errata_recompute_3.json, experiments/ERRATA_PROTOCOL.md, experiments/errata_recompute.py, experiments/errata_lib.py, "
        "experiments/errata_text.py, tests/test_errata_recompute.py, tests/test_errata_text.py, results/errata_dryruns/dry_b3.json, "
        "results/errata_dryruns/dry_b3b.json, results/p2_tinyllama_dumps.sha256, results/errata_critic/REPORT.md",
        "- finding: one bullet per row (claim as printed; recomputed value; status under the pinned rule, with the status per claim site, per count or "
        "under E15's rule where the protocol defines one). Values are addressable as rows.<id>.value.<key> in the payload; the critic's independent "
        "recompute (results/errata_critic/REPORT.md, third batch) reproduced every value.",
    ]
    lines += row_bullets(P, T)
    lines.append("- predictions scored (each labelled by its source where the payload names one, the harvest's or the critic's values, where a prediction key "
                 "names a payload key): " + "; ".join(f"{rid}: {', '.join(h)}" for rid, h in sc.items()) + ".")
    lines.append("- caveats: one box, one recompute. E17's beyond-counts stand; its escape costs are near-tie masses over all census positions of each "
                 "model's dumps, as the census counted them. E18 uses one split (the first half trains, the second is held out), dictionaries trained on the other half of the same "
                 "prompt families (which favours zstd), the zstandard version in the payload, and a pinned threshold of a tenth for the dictionary "
                 "effect; its sessions are the held-out sessions only, so their multiples are not the printed all-row ones. E19 is post hoc at its "
                 "primary binning (recorded in the amendment log, not scored) with the other binnings as the out-of-sample evidence, scores the rank-1 "
                 "term alone by a pinned absolute z below 2 at a sample size that cannot exclude a substantially lower archive rate, and leaves the "
                 "correction term rank-only. The original finding texts are never rewritten; each finding a row points into carries one dated line "
                 "pointing here, labelled erratum where a claim-site status there is not CONFIRMED or, for a row corrected under its pinned rule, where "
                 "that rule's site lies, and note otherwise.")
    return "\n".join(lines) + "\n"


BLOCKS = {"F-14": f14_block, "F-15": f15_block, "F-16": f16_block}


def readme_status_note(P: dict, fid: str) -> str:
    d = date_of(P); S = P["summary"]; n_corr, _, _ = status_counts(P)
    if fid == "F-14":
        return (f"> Erratum pass ({d}): {fid} corrects {n_corr} of {len(S)} checked claims from a pre-registered recompute "
                f"(experiments/ERRATA_PROTOCOL.md, results/errata_recompute.json); the lines below stand as written, with dated erratum "
                f"notes where a figure changed.")
    stand, total = claim_site_counts(P)
    if fid == "F-15":
        return (f"> Second errata batch ({d}): {fid} adds rows {', '.join(rows_present(P))} from a second pre-registered recompute "
                f"(experiments/ERRATA_PROTOCOL.md amendment log, results/errata_recompute_2.json): {n_corr} of {len(S)} rows corrected under their pinned "
                f"rules, {stand} of {total} claim-site statuses standing at their own scope; the lines below stand as written.")
    return (f"> Third errata batch ({d}): {fid} adds rows {', '.join(rows_present(P))} from a third pre-registered recompute "
            f"(experiments/ERRATA_PROTOCOL.md amendment log, results/errata_recompute_3.json): {n_corr} of {len(S)} rows corrected under their pinned "
            f"rules, {stand} of {total} claim-site statuses standing at their own scope; the zstd figures below carry no dictionary, and F-16 gives the "
            f"dictionary comparator; the lines stand as written.")


# ----------------------------------------------------------------------------
# placement
# ----------------------------------------------------------------------------


def parse_where(w: str) -> tuple[str, int, int] | None:
    m = re.match(r"^([\w./-]+):(\d+)(?:-(\d+))?", w)
    if not m:
        return None
    return m.group(1), int(m.group(2)), int(m.group(3) or m.group(2))


def finding_blocks(text: str) -> list[tuple[str, int, int]]:
    """(finding id, first line index 0-based, last line index exclusive) for every `## F-*` block."""
    lines = text.split("\n"); heads = [(m.group(1), i) for i, ln in enumerate(lines) for m in [re.match(r"^## +(F-[\w.]+)\b", ln)] if m]
    out = []
    for j, (fid, i) in enumerate(heads):
        end = heads[j + 1][1] if j + 1 < len(heads) else len(lines)
        out.append((fid, i, end))
    return out


def rows_by_finding(P: dict, findings_text: str) -> dict[str, list[str]]:
    blocks = finding_blocks(findings_text); out: dict[str, list[str]] = {}
    for rid in rows_present(P):
        for w in P["rows"][rid]["where"]:
            pw = parse_where(w)
            if not pw or pw[0] != "FINDINGS.md":
                continue
            line0 = pw[1] - 1
            for fid, i, end in blocks:
                if i <= line0 < end and rid not in out.setdefault(fid, []):
                    out[fid].append(rid)
    return out


def pointer_notes(P: dict, T: dict[str, str]) -> dict[str, dict[tuple[int, int], list[str]]]:
    """{file: {(first_line, last_line): [row ids]}} for every non-FINDINGS location a row names."""
    out: dict[str, dict[tuple[int, int], list[str]]] = {}
    for rid in rows_present(P):
        for w in P["rows"][rid]["where"]:
            pw = parse_where(w)
            if not pw or pw[0] == "FINDINGS.md" or pw[0] in SKIP_FILES:
                continue
            loc = out.setdefault(pw[0], {}).setdefault((pw[1], pw[2]), [])
            if rid not in loc:
                loc.append(rid)
    return {file: merge_locations(locs) for file, locs in out.items()}


def merge_locations(locs: dict) -> dict:
    """Locations in one file whose line ranges overlap or touch take one note (after the later line), rows merged in order."""
    merged: list[tuple[tuple[int, int], list[str]]] = []
    for (a, b), rids in sorted(locs.items()):
        if merged and a <= merged[-1][0][1] + 1:
            (pa, pb), prids = merged[-1]
            merged[-1] = ((pa, max(pb, b)), prids + [r for r in rids if r not in prids])
        else:
            merged.append(((a, b), list(rids)))
    return dict(merged)


def paragraph_end(lines: list[str], idx: int) -> int:
    """Index of the last line of the paragraph containing lines[idx] (stops before a blank line or a new block)."""
    j = idx
    while j + 1 < len(lines) and lines[j + 1].strip() and not re.match(r"^(- |#|>|\|)", lines[j + 1]):
        j += 1
    return j


def note_line(file: str, d: str, rids: list[str], T: dict[str, str], fid: str = FINDING_ID, label: str = "erratum") -> str:
    body = f"{label.capitalize()} ({d}; {fid} " + ("rows " if len(rids) > 1 else "row ") + ", ".join(rids) + "): " + " ".join(f"{r}: {T[r]}" for r in rids)
    if file == "DECISIONS.md":
        return "- " + body[0].lower() + body[1:]
    if file == "experiments/P7_PROTOCOL.md":
        return f"Withdrawn ({d}; {fid} row {', '.join(rids)}): " + " ".join(T[r] for r in rids)
    return "> " + body


def insert_lines(lines: list[str], inserts: list[tuple[int, str]]) -> list[str]:
    """Insert each text AFTER line index i (0-based), applied bottom-up so indices stay valid; texts sharing an index
    keep their list order in the file. Append-only by construction."""
    out = list(lines)
    for _, (i, text) in sorted(enumerate(inserts), key=lambda x: (-x[1][0], -x[0])):
        out[i + 1:i + 1] = [text]
    return out


def is_subsequence(original: list[str], new: list[str]) -> bool:
    """Every original line survives, unchanged and in order."""
    it = iter(new)
    return all(any(ln == x for x in it) for ln in original)


# ----------------------------------------------------------------------------
# apply
# ----------------------------------------------------------------------------


def git_blob(path: str) -> str:
    return subprocess.check_output(["git", "-C", str(REPO), "rev-parse", f"HEAD:{path}"]).decode().strip()


def read_lf(path: Path) -> tuple[str, bytes]:
    raw = path.read_bytes(); nl = b"\r\n" if b"\r\n" in raw else b"\n"
    return raw.decode("utf-8").replace("\r\n", "\n"), nl


def plan_edits(P: dict, fid: str = FINDING_ID) -> dict[str, list[tuple[int, str]]]:
    """{file: [(after_line_index, text)]} — every insertion the generator will make."""
    ftext, _ = read_lf(REPO / "FINDINGS.md")
    if re.search(rf"^## +{re.escape(fid)}\b", ftext, flags=re.M):
        raise ValueError(f"{fid} already exists in FINDINGS.md; the generator runs once per finding")
    T = row_texts(P); d = date_of(P); edits: dict[str, list[tuple[int, str]]] = {}
    flines = ftext.split("\n")
    fe = []
    for bfid, rids in rows_by_finding(P, ftext).items():
        _, i, end = next(b for b in finding_blocks(ftext) if b[0] == bfid)
        last = end - 1
        while last > i and not flines[last].strip():
            last -= 1
        label = location_label(P, rids, "FINDINGS.md", i + 1, end)
        fe.append((last, f"- {label} ({d}): see {fid}, " + ("rows " if len(rids) > 1 else "row ") + ", ".join(rids)))
    # the finding block goes after the last non-blank line of the file, separated by one blank line
    last = len(flines) - 1
    while last > 0 and not flines[last].strip():
        last -= 1
    fe.append((last, "\n" + BLOCKS[fid](P, T).rstrip("\n")))
    edits["FINDINGS.md"] = fe
    for file, locs in pointer_notes(P, T).items():
        text, _ = read_lf(REPO / file); lines = text.split("\n"); by_idx: dict[int, tuple[list[str], str]] = {}
        for (a, b), rids in locs.items():
            idx = b - 1
            if PLACEMENT.get(file, "line") == "paragraph":
                idx = paragraph_end(lines, idx)
            label = location_label(P, rids, file, a, b)
            if idx in by_idx:                      # two locations in one paragraph take one note; erratum if either is
                prev_rids, prev_label = by_idx[idx]
                by_idx[idx] = (prev_rids + [r for r in rids if r not in prev_rids], "erratum" if "erratum" in (prev_label, label) else "note")
            else:
                by_idx[idx] = (list(rids), label)
        edits[file] = [(idx, note_line(file, d, rids, T, fid, label)) for idx, (rids, label) in sorted(by_idx.items())]
    # README status header: one summary note under the heading, after any earlier batch's note
    rtext, _ = read_lf(REPO / "README.md"); rlines = rtext.split("\n")
    edits.setdefault("README.md", []).append((status_note_index(rlines), readme_status_note(P, fid)))
    return edits


def status_note_index(rlines: list[str]) -> int:
    """Index of the line after which a status note goes: the blank line under `## Status`, or the last `> ` note already there."""
    hdr = next(i for i, ln in enumerate(rlines) if ln.startswith("## Status"))
    i = hdr + 1
    while i + 1 < len(rlines) and rlines[i + 1].startswith("> "):
        i += 1
    return i


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--payload", default=str(PAYLOAD))
    ap.add_argument("--finding", default=FINDING_ID, choices=sorted(BLOCKS))
    a = ap.parse_args(argv)
    P = json.loads(Path(a.payload).read_text(encoding="utf-8"))
    pinned = P["provenance"]["inputs"]
    edits = plan_edits(P, a.finding)
    stale = [f for f in edits if pinned.get(f) and git_blob(f) != pinned[f]]
    if stale:
        print(f"errata_text: refusing: files changed since the recompute pinned them: {stale}", file=sys.stderr); return 2
    for file, ins in edits.items():
        path = REPO / file; text, nl = read_lf(path); lines = text.split("\n")
        new = insert_lines(lines, ins)
        if len(new) != len(lines) + len(ins) or not is_subsequence(lines, new):
            raise RuntimeError(f"append-only violated for {file}")
        if a.dry_run:
            print(f"=== {file}")
            for _, (i, t) in sorted(enumerate(ins), key=lambda x: (x[1][0], x[0])):      # write order
                print(f"--- after line {i + 1}:\n{t}")
            continue
        path.write_bytes("\n".join(new).replace("\n", nl.decode()).encode("utf-8"))
        print(f"errata_text: {file}: {len(ins)} insertion(s)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
