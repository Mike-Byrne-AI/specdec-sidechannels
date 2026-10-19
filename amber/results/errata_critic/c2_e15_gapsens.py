#!/usr/bin/env python3
"""Critic, second batch, E15 audit (post hoc, NOT a protocol quantity): sensitivity of the
gap-conditioned theta-0 prediction to the binning of P2b's A-desync rate.

A-desync hazard at a P4 rank-1 position = P2b's A-desync rate (cpu_fp32 -> D, theta 0) in the
bin of the encoder's top-1/top-2 gap; C hazards per rank as pinned (P2b theta-0 row); X = 0.
Reports, per binning, the four comparisons of E15's pinned rule against that prediction and the
compensator (expected A first desyncs on the decoded positions). Standalone; torch blocked.
"""
import sys

sys.modules["torch"] = None
import glob  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
RES = REPO / "results"; OUT = RES / "p2_llama32"; R = 64


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def load(name):
    meta = json.loads((OUT / name / "meta.json").read_text()); ii, vv = [], []
    for s in range((meta["n_seqs"] + meta["shard_size"] - 1) // meta["shard_size"]):
        with np.load(OUT / name / f"shard_{s:04d}.npz") as z:
            ii.append(z["idx"]); vv.append(z["val"])
    i = np.concatenate(ii); v = np.concatenate(vv).astype(np.float64); k = i.shape[2]
    i, v = i.reshape(-1, k), v.reshape(-1, k)
    o1 = np.argsort(i, 1, kind="stable"); i, v = np.take_along_axis(i, o1, 1), np.take_along_axis(v, o1, 1)
    o2 = np.argsort(-v, 1, kind="stable"); return np.take_along_axis(i, o2, 1), np.take_along_axis(v, o2, 1)


def main():
    man = {}
    for ln in (RES / "p2_dumps.sha256").read_text().splitlines():
        if ln.strip():
            d, _, rel = ln.partition("  "); man[rel] = d
    used = ["results/p2_llama32/corpus.npz"] + [r for r in man if any(r.startswith(f"results/p2_llama32/{a}/") for a in ("cpu_fp32", "cuda_bf16_b1", "cuda_fp16_b1"))]
    bad = [r for r in used if sha(REPO / r) != man[r]]
    assert not bad, bad
    tokens = np.load(OUT / "corpus.npz")["tokens"]; L = tokens.shape[1]
    keep = np.ones(tokens.shape[0] * L, bool); keep[L - 1::L] = False
    true = tokens[:, 1:].reshape(-1).astype(np.int64)
    Ei, Ev = load("cpu_fp32"); Ei, Ev = Ei[keep], Ev[keep]; g12 = Ev[:, 0] - Ev[:, 1]; r1 = Ei[:, 0] == true
    b = json.loads((RES / "p2b_escape_robustness.json").read_text())
    rep = json.loads((RES / "p4_real_archive.json").read_text())["report"]
    p4 = {}
    for f in sorted(glob.glob(str(RES / "p4/archives/row_*_symbols.npz"))):
        with np.load(f) as z:
            p4[int(Path(f).name[4:8])] = (z["flag"].astype(int), z["rank"].astype(np.int64), z["gap"].astype(np.float64))
    gA4 = np.concatenate([g[fl == 0] for fl, _, g in p4.values()])
    binnings = {f"log{n}": np.concatenate([[0.0], np.logspace(-6, 1.5, n), [np.inf]]) for n in (8, 16, 31, 61)}
    gq = np.quantile(g12[r1], np.linspace(0, 1, 21)); gq[0] = 0.0; gq[-1] = np.inf
    binnings["p2_quantile20"] = np.unique(gq)
    out = {"manifest_files_checked": len(used)}
    for D, arm in (("cuda_bf16_b1", "cuda_bf16"), ("cuda_fp16_b1", "cuda_fp16")):
        Di, _ = load(D); Di = Di[keep]; dA = (Di[:, 0] != true) & r1
        row0 = [r for r in b["report"]["cpu_fp32"]["decoders"][D] if r["theta"] == 0.0][0]
        assert int(dA.sum()) == row0["desyncs"]["A"] and int(r1.sum()) == row0["symbol_counts"]["A"]
        pC = np.zeros(R + 2)
        for rr, e in row0["C_desync_by_rank"].items():
            pC[int(rr)] = e["desync"] / e["n"]
        rws, fst, ndd = [], [], []
        for f in sorted(glob.glob(str(RES / f"p4/decode_{arm}/shard_*.npz"))):
            with np.load(f) as z:
                rws += z["row"].tolist(); fst += z["first"].tolist(); ndd += z["n_decoded"].tolist()
        m = rep["arms"][arm]; res = {}
        for name, edges in binnings.items():
            cnt, _ = np.histogram(g12[r1], edges); des, _ = np.histogram(g12[dA], edges)
            rate = np.where(cnt > 0, des / np.maximum(cnt, 1), 0.0)
            c4, _ = np.histogram(gA4, edges)
            idx = lambda x: np.clip(np.searchsorted(edges, x, side="right") - 1, 0, len(rate) - 1)  # noqa: E731
            haz = {}
            for k_, (fl, rk, g) in p4.items():
                h = np.zeros(rk.size); h[fl == 0] = rate[idx(g[fl == 0])]; h[fl == 1] = pC[rk[fl == 1]]; haz[k_] = h
            allh = np.concatenate([haz[k_] for k_ in sorted(haz)])
            fe = 1 - np.mean([np.prod(1 - haz[k_]) for k_ in sorted(haz)])
            compA = sum(float(haz[r_][:n_][p4[r_][0][:n_] == 0].sum()) for r_, n_ in zip(rws, ndd))
            res[name] = {"bins": int(len(edges) - 1), "p4_A_mass_in_empty_p2_bins": int(c4[cnt == 0].sum()),
                         "one_in": float(1 / allh.mean()), "fail_exact": float(fe), "compensator_A": compA,
                         "rate_measured_gt_predicted": m["desyncs_per_token"] > allh.mean(), "fail_measured_gt_predicted": m["fail_rate"] > fe}
        out[D] = {"measured_one_in": 1 / m["desyncs_per_token"], "measured_fail_rate": m["fail_rate"],
                  "measured_A_first": m["first_desync_class_counts"].get("A", 0), "by_binning": res}
    Path(__file__).with_suffix(".out.json").write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(out, indent=1, default=float))


if __name__ == "__main__":
    main()
