"""P2b — cross-arm byte-exactness of the v2 symbol grammar (experiments/P3_PROTOCOL.md).

Uses the P2 Llama-3.2-1B-Instruct dumps (results/p2_llama32: top-256 idx/val per
arm, 96 x 512 positions; true token = corpus next token, so the last position
of each sequence is dropped). For each (encoder arm, decoder arm, variant) the
v2 classifier builds the symbol stream under the ENCODER arm and every symbol
is resolved under the DECODER arm's canonical top-256:

    A  -> decoder argmax                      desync iff != true
    C  -> decoder order[rank-1]               desync iff != true
    T  -> sorted(decoder top-m)[slot]         desync iff != true
    X  -> raw id                              never desyncs

With an adaptive coder one desync ends the archive, so COUNTS are reported.
Also the `set-coded` C variant: rank r coded as (bucket b, slot among the
top-2^(b+1) set by index) — robust iff that SET is stable; +1 bit per C.
Positions whose encoder rank is > 256 are X anyway (max_rank=64 < 256).
Top-k arrays are canonicalised (value desc, index asc) so tie order matches
the codec's stable_order on every arm.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from amber.rac_codec import FLAG_A, FLAG_C, FLAG_T, FLAG_X, FLAG_NAMES
from amber.rankcensus import canonical_topk
from amber.real.capture import load_arm, load_corpus

RESULTS = Path(__file__).resolve().parent.parent / "results"
ENCODERS = ("cpu_fp32", "cuda_bf16_b1")
DECODERS = ("cuda_fp32_b1", "cuda_fp16_b1", "cuda_bf16_b1", "cuda_bf16_b8", "cuda_int8_b1", "cuda_nf4_b1")
THETAS = (0.0, 0.142, 0.465, 0.93)
MS = (2, 4)
R_MAX = 64
# per-arm calibrated tau vs the cpu_fp32 reference (F-7 census, results/p2_llama32_rank_census.json);
# a pair's drift budget is 2 * (tau_enc + tau_dec) with tau_cpu = 0
TAU = {"cpu_fp32": 0.0, "cuda_bf16_b1": 0.2327, "cuda_bf16_b8": 0.2260, "cuda_fp16_b1": 0.0331, "cuda_fp32_b1": 4.3e-05}


def rank_of_true(idx: np.ndarray, true: np.ndarray) -> np.ndarray:
    """1-based rank of true[t] in idx[t] (canonical), K+1 if absent."""
    hit = idx == true[:, None]
    r = np.where(hit.any(1), hit.argmax(1) + 1, idx.shape[1] + 1)
    return r


def slot_in_set(idx_set: np.ndarray, true: np.ndarray) -> np.ndarray:
    """Index-order slot of true within each row's set (-1 if absent)."""
    s = np.sort(idx_set, axis=1)
    pos = np.array([int(np.searchsorted(s[i], true[i])) for i in range(len(true))])
    ok = (pos < s.shape[1]) & (s[np.arange(len(true)), np.minimum(pos, s.shape[1] - 1)] == true)
    return np.where(ok, pos, -1)


def resolve_slot(idx_set: np.ndarray, slot: np.ndarray) -> np.ndarray:
    s = np.sort(idx_set, axis=1)
    return s[np.arange(len(slot)), np.minimum(slot, s.shape[1] - 1)]


def simulate(enc_idx, enc_val, dec_idx, true, theta, m):
    n = len(true)
    r_enc = rank_of_true(enc_idx, true)
    gap = enc_val[:, 0] - enc_val[:, 1]
    flag = np.full(n, FLAG_X)
    is_t = (theta > 0) & (gap < theta) & (r_enc <= m)
    flag[is_t] = FLAG_T
    flag[(~is_t) & (r_enc == 1)] = FLAG_A
    flag[(~is_t) & (r_enc >= 2) & (r_enc <= R_MAX)] = FLAG_C
    resolved = true.copy()                                   # X: exact by construction
    a = flag == FLAG_A; resolved[a] = dec_idx[a, 0]
    c = flag == FLAG_C; resolved[c] = dec_idx[c, r_enc[c] - 1]
    t = flag == FLAG_T
    if t.any():
        slot = slot_in_set(enc_idx[t, :m], true[t]); assert (slot >= 0).all()
        resolved[t] = resolve_slot(dec_idx[t, :m], slot)
    desync = resolved != true
    out = {"theta": theta, "m": m, "n": int(n),
           "symbol_counts": {FLAG_NAMES[f]: int((flag == f).sum()) for f in range(4)},
           "desyncs": {FLAG_NAMES[f]: int((desync & (flag == f)).sum()) for f in range(4)},
           "desync_total": int(desync.sum())}
    # A-desyncs beyond the encoder gap (bug detector, XB-3): report the gap distribution of A desyncs
    ag = gap[a & desync]
    out["A_desync_gap"] = {"n": int(ag.size), "max": float(ag.max()) if ag.size else None,
                           "median": float(np.median(ag)) if ag.size else None}
    # per-rank C desync curve
    curve = {}
    for r in range(2, R_MAX + 1):
        sel = c & (r_enc == r)
        if sel.any():
            curve[str(r)] = {"n": int(sel.sum()), "desync": int((desync & sel).sum())}
    out["C_desync_by_rank"] = curve
    # set-coded C variant: slot among the top-2^(b+1) set, b = bit_length(r-1)-1
    u = r_enc - 1; b = np.floor(np.log2(np.maximum(u, 1))).astype(int); K = 1 << (b + 1)
    sc_desync = 0; sc_n = 0; sc_by_b = {}
    for bb in np.unique(b[c]):
        sel = c & (b == bb); k = int(1 << (bb + 1))
        slot = slot_in_set(enc_idx[sel, :k], true[sel]); assert (slot >= 0).all()
        res = resolve_slot(dec_idx[sel, :k], slot); d = int((res != true[sel]).sum())
        sc_by_b[str(int(bb))] = {"K": k, "n": int(sel.sum()), "desync": d}; sc_desync += d; sc_n += int(sel.sum())
    out["setcoded_C"] = {"n": sc_n, "desync": sc_desync, "by_bucket": sc_by_b,
                         "desync_total_with_setcoded_C": int(out["desyncs"]["A"] + out["desyncs"]["T"] + sc_desync)}
    return out


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default="results/p2_llama32")
    a = ap.parse_args(argv); out = Path(a.out)
    tokens, cmeta = load_corpus(out)
    true = tokens[:, 1:].reshape(-1).astype(np.int64)         # next token for positions 0..L-2
    L = tokens.shape[1]
    keep = np.ones(tokens.shape[0] * L, bool); keep[L - 1::L] = False

    arms = {}
    for name in sorted(set(ENCODERS) | set(DECODERS)):
        idx, val, meta = load_arm(out, name)
        idx, val = canonical_topk(idx, val)
        arms[name] = (idx[keep], val[keep], meta)
    print(f"loaded {len(arms)} arms, {keep.sum()} positions")

    report = {}
    t0 = time.perf_counter()
    for e in ENCODERS:
        eidx, eval_, _ = arms[e]
        r_enc = rank_of_true(eidx, true)
        report[e] = {"rank_of_true_quantiles": {q: int(np.quantile(r_enc, float(q))) for q in ("0.5", "0.9", "0.99")},
                     "rank_gt_R_rate": float((r_enc > R_MAX).mean()), "rank_gt_256_rate": float((r_enc > 256).mean()),
                     "decoders": {}}
        for d in DECODERS:
            if d == e:
                continue
            didx, _, _ = arms[d]
            rows = []
            for theta in THETAS:
                for m in (MS if theta > 0 else (2,)):
                    rows.append(simulate(eidx, eval_, didx, true, theta, m))
            report[e]["decoders"][d] = rows
            summ = "  ".join(f"th{r['theta']}/m{r['m']}: A{r['desyncs']['A']} T{r['desyncs']['T']} C{r['desyncs']['C']} sc{r['setcoded_C']['desync']}" for r in rows)
            print(f"{e:12s} -> {d:12s}  {summ}")
    print(f"({time.perf_counter()-t0:.1f}s)")

    # pipeline-bug check (XB-3): any A desync with encoder gap >= 2*tau_decoder for the fp32/fp16/bf16 decoders
    bug = {}
    for e in ENCODERS:
        for d, rows in report[e]["decoders"].items():
            if d in TAU:
                r0 = rows[0]; budget = 2 * (TAU[e] + TAU[d])
                bug[f"{e}->{d}"] = {"A_desyncs": r0["desyncs"]["A"], "max_gap": r0["A_desync_gap"]["max"], "pair_budget_2tau": budget,
                                    "beyond_budget": bool(r0["A_desync_gap"]["max"] is not None and r0["A_desync_gap"]["max"] > budget)}
    payload = {"_experiment": "p2b_escape_robustness", "_written_unix": int(time.time()), "protocol": "experiments/P3_PROTOCOL.md",
               "model": cmeta["model_id"], "corpus_sha256": cmeta["corpus_sha256"], "positions": int(keep.sum()),
               "encoders": ENCODERS, "decoders": DECODERS, "thetas": THETAS, "ms": MS, "R_max": R_MAX,
               "xb3_wide_gap_check": bug, "report": report,
               "regime": f"Llama-3.2-1B-Instruct top-256 dumps over {cmeta['n_seqs']}x{L} tokens of tokenizer-lab mix_docs50_wiki50 text (teacher-forced, NOT target-generated); "
                         "symbol stream built under the encoder arm, resolved under the decoder arm; counts of desync positions"}
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "p2b_escape_robustness.json").write_text(json.dumps(payload, indent=2, sort_keys=True))
    print("XB-3 wide-gap check:", json.dumps(bug, indent=1))
    print("[saved] results/p2b_escape_robustness.json")


if __name__ == "__main__":
    main()
