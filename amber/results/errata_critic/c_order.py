"""Critic aside: fp32 top-64 ORDER stability between cpu_fp32 and the two cuda fp32 arms (context for F-10 verdict / OQ-2:14),
and E8c under m=4 escapes."""
import sys
sys.modules["torch"] = None
import json
from pathlib import Path
import numpy as np
D = Path(r"C:\Users\Michael\Desktop\SaaS\amber\results\p2_llama32")
tokens = np.load(D / "corpus.npz")["tokens"].astype(np.int64); S, L = tokens.shape; true = tokens[:, 1:].reshape(-1)
def load(arm):
    meta = json.loads((D / arm / "meta.json").read_text()); idx, val = [], []
    for s in range((meta["n_seqs"] + meta["shard_size"] - 1) // meta["shard_size"]):
        z = np.load(D / arm / f"shard_{s:04d}.npz"); idx.append(z["idx"]); val.append(z["val"])
    idx = np.concatenate(idx); v = np.concatenate(val).astype(np.float64)
    o = np.lexsort((idx, -v), axis=-1); idx = np.take_along_axis(idx, o, -1); v = np.take_along_axis(v, o, -1)
    return idx[:, :L - 1].reshape(-1, idx.shape[-1]), v[:, :L - 1].reshape(-1, idx.shape[-1])
ei, ev = load("cpu_fp32")
for arm in ("cuda_fp32_b1", "cuda_fp32_b8"):
    di, dv = load(arm)
    for K in (1, 2, 8, 64):
        diff = (ei[:, :K] != di[:, :K]).any(1)
        print(f"  cpu_fp32 vs {arm}: positions with top-{K} order difference: {int(diff.sum())} / {len(diff)}")
    # first differing slot and encoder value gap there
    diff = (ei[:, :64] != di[:, :64]); rows = np.flatnonzero(diff.any(1))
    first = diff[rows].argmax(1)
    gaps = ev[rows, first] - ev[rows, first + 1]
    ties = int((gaps == 0).sum())
    print(f"    first-diff slot distribution (1-based) quantiles: {np.quantile(first + 1, [0, .5, .9, 1]).tolist()}; enc gap at first diff: exact ties {ties}, max {gaps.max():.3e}, median {np.median(gaps):.3e}")
    # E8c-style sim with m=4 escapes
    re_ = np.where((ei == true[:, None]).any(1), (ei == true[:, None]).argmax(1) + 1, 257)
    gap = ev[:, 0] - ev[:, 1]
    for th, m in ((0.0, 2), (0.465, 4), (0.93, 4)):
        T = (th > 0) & (gap < th) & (re_ <= m); A = (~T) & (re_ == 1); C = (~T) & (re_ >= 2) & (re_ <= 64)
        res = true.copy(); res[A] = di[A, 0]; res[C] = di[C, re_[C] - 1]
        if T.any():
            es = np.sort(ei[T, :m], 1); ds = np.sort(di[T, :m], 1); tt = true[T]
            slot = np.array([int(np.flatnonzero(es[i] == tt[i])[0]) for i in range(len(tt))]); res[T] = ds[np.arange(len(tt)), slot]
        des = res != true
        print(f"    {arm} theta {th}/m{m}: desync total {int(des.sum())} (A {int((des&A).sum())} C {int((des&C).sum())} T {int((des&T).sum())})")
