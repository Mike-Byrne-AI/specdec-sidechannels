"""OQ-16 anchor-state identity check (dated erratum evidence, 2026-09-05):
is the byproduct-logged anchor hidden state h_a a function of information
the decoder already has?

h_a is the verifier's final-norm output at the anchor, i.e. the lm_head
input; the lm_head is a bias-free linear map W_U (vocab x d, untied in
Llama-3.1-8B, full column rank), so logits = W_U h_a determines h_a
exactly (least squares over the vocab), and the top-k (id, log-prob)
pairs determine it to the extent k >= d + 1 rows span the space. The
identity is generic to any linear unembedding of full column rank with
vocab > d, tied or untied; it is measured here on one model. This tool
measures, on committed byproduct rows: (i) FORWARD consistency - W_U @ h
reproduces the logged argmax / top-32 ids / top-1 probability (the logged
values came from the live bf16 lm_head of the NF4-loaded verifier, on the
float16-logged h, so small gaps are expected); (ii) INVERSE - the relative
error of h recovered from the full logits (float32 logits, and float64
logits to show the float32 floor); (iii) the closed-form recovery from
only the top-k (id, log-prob) pairs of the RECOMPUTED logits W_U h (the
logged float16 top_p rows contain zeros, so the logged pairs are not usable
directly) for k in TOPK, by SVD least squares over [h, logZ] with no ridge
(minimum-norm when k < d + 1), reported as per-row R^2 (1 - SSE / SS about
the row's own mean, raw h space; NOT Stage-R's standardized pooled-MSE R^2
and not comparable to its ridge arms) and cosine against the logged h;
(iv) CONDITIONING - singular values of W_U, the fraction of the all-ones
vector inside col(W_U) (the softmax's additive-constant direction, the one
place "p determines h_a" could degrade), and the smallest singular value
of the augmented system [W_U, -1] that recovers (h, logZ) from
log-probabilities alone; (v) PRECISION - h recovered from bfloat16-rounded
full logits and from bfloat16-rounded full log-probabilities (logZ unknown),
i.e. what a p-only consumer at serving precision would get.

Needs the cached HF checkpoint (safetensors, read through torch for the
bf16 dtype) and the gitignored byproduct raws: GPU-box only; CI imports the
module (tests/test_ha_identity.py exercises the closed-form arithmetic on a
synthetic unembedding) but never runs it - torch and safetensors are
imported lazily inside load_lm_head. Rows: the first ROWS_PER_PROMPT blocks
of the first N_PROMPTS prompts of each of the four registered vanilla runs
(recon.RECON_RUNS) - pinned, no RNG.

  python tools/ha_identity_check.py --out results/real/oq16_ha_identity.json
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from sideband.recon import RECON_RUNS  # noqa: E402

REAL = Path(__file__).resolve().parents[1] / "results" / "real"
MODEL = "meta-llama/Llama-3.1-8B-Instruct"
TOPK = (4097, 2048, 512, 128, 32)
N_PROMPTS = 3
ROWS_PER_PROMPT = 4


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _git_commit() -> str:
    try:
        r = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True)
        d = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        return (r.stdout.strip() or "unknown") + ("-dirty" if d.stdout.strip() else "")
    except OSError:
        return "unknown"


def load_lm_head() -> tuple[np.ndarray, dict]:
    from safetensors import safe_open
    snaps = sorted(glob.glob(str(Path.home() / ".cache/huggingface/hub"
                                 / ("models--" + MODEL.replace("/", "--")) / "snapshots" / "*")))
    if not snaps:
        raise SystemExit(f"{MODEL} is not in the HF cache")
    snap = Path(snaps[-1])
    idx = json.loads((snap / "model.safetensors.index.json").read_text())
    shard = idx["weight_map"]["lm_head.weight"]
    cfg = json.loads((snap / "config.json").read_text())
    with safe_open(str(snap / shard), framework="pt") as f:
        W = f.get_tensor("lm_head.weight").float().numpy()
    meta = {"model": MODEL, "snapshot": snap.name, "shard": shard,
            "shard_sha256": _sha(snap / shard), "tie_word_embeddings": cfg.get("tie_word_embeddings"),
            "vocab": int(W.shape[0]), "d": int(W.shape[1])}
    return W, meta


def rows_from_runs() -> tuple[dict, list]:
    H, IDS, P, AM, prov = [], [], [], [], []
    for spec in RECON_RUNS:
        stem = spec["stem"]
        shas = json.loads((REAL / f"{stem}.summary.json").read_text())["byproduct_sha256"]
        for i in range(N_PROMPTS):
            f = REAL / f"{stem}.jsonl.byproduct" / f"p{i:03d}.npz"
            if _sha(f) != shas[f.name]:
                raise SystemExit(f"sha mismatch for {f}")
            z = np.load(f)
            n = min(ROWS_PER_PROMPT, int(z["n_blocks"]))
            H.append(z["h"][:n].astype(np.float32)); IDS.append(z["top_ids"][:n])
            P.append(z["top_p"][:n].astype(np.float32)); AM.append(z["argmax"][:n])
            prov.append({"stem": stem, "file": f.name, "rows": n, "sha256": shas[f.name]})
    return {"h": np.concatenate(H), "ids": np.concatenate(IDS), "p": np.concatenate(P),
            "argmax": np.concatenate(AM)}, prov


def topk_recover(W: np.ndarray, logits_row: np.ndarray, k: int) -> np.ndarray:
    """Least squares for [h, logZ] from the top-k rows of the recomputed logits:
    W[ids] h - logZ = logp[ids]. SVD (np.linalg.lstsq), no ridge; minimum-norm
    when the system is underdetermined (k < d + 1)."""
    ids = np.argsort(-logits_row)[:k]
    m = logits_row.max()
    logp = logits_row[ids] - (m + np.log(np.exp(logits_row - m).sum()))
    A = np.hstack([W[ids].astype(np.float64), -np.ones((k, 1), np.float64)])
    sol = np.linalg.lstsq(A, logp.astype(np.float64), rcond=None)[0]
    return sol[:-1]


def bf16_round(x: np.ndarray) -> np.ndarray:
    """Round float32 values to bfloat16 (round-to-nearest-even); returned as float32."""
    b = np.ascontiguousarray(x, dtype=np.float32).view(np.uint32)
    lsb = (b >> np.uint32(16)) & np.uint32(1)
    r = (b + np.uint32(0x7FFF) + lsb) & np.uint32(0xFFFF0000)
    return r.view(np.float32)


def _r2_cos(hh: np.ndarray, hi: np.ndarray) -> tuple[float, float]:
    r2 = 1.0 - ((hh - hi) ** 2).sum() / ((hi - hi.mean()) ** 2).sum()
    cos = float(hh @ hi / (np.linalg.norm(hh) * np.linalg.norm(hi)))
    return float(r2), cos


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True)
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()
    out = Path(args.out)
    if out.exists() and not args.overwrite:
        raise SystemExit(f"{out} exists; pass --overwrite to redo")
    t0 = time.time()
    W, wmeta = load_lm_head()
    data, prov = rows_from_runs()
    H = data["h"]; n = H.shape[0]
    V, d = W.shape
    logits = H @ W.T                                   # float32, as a float32 host would hold them
    am = logits.argmax(1)
    top32 = np.argsort(-logits, axis=1)[:, :32]
    overlap = np.array([len(set(top32[i]) & set(data["ids"][i][data["ids"][i] >= 0])) / 32 for i in range(n)])
    sm = np.exp(logits - logits.max(1, keepdims=True)); sm /= sm.sum(1, keepdims=True)
    p_top1 = sm[np.arange(n), data["ids"][:, 0]]

    # --- full-logit inverse (normal equations in float64; cond(W)^2 is benign, see conditioning)
    Wd = W.astype(np.float64)
    G = Wd.T @ Wd
    H64 = H.astype(np.float64)
    h_full = np.linalg.solve(G, Wd.T @ logits.T.astype(np.float64)).T
    rel = np.linalg.norm(h_full - H64, axis=1) / np.linalg.norm(H64, axis=1)
    logits64 = H64 @ Wd.T                               # exact float64 forward: shows the float32 floor
    h_full64 = np.linalg.solve(G, Wd.T @ logits64.T).T
    rel64 = np.linalg.norm(h_full64 - H64, axis=1) / np.linalg.norm(H64, axis=1)

    # --- conditioning: singular values of W_U, the ones-vector direction, the augmented system
    ev = np.linalg.eigvalsh(G)
    sigma_min, sigma_max = float(np.sqrt(ev[0])), float(np.sqrt(ev[-1]))
    u = Wd.sum(0)                                       # W^T 1
    c = np.linalg.solve(G, u)
    Wc = Wd @ c
    ones_in_col = float(np.linalg.norm(Wc) / np.sqrt(V))
    ones_resid_rel = float(np.linalg.norm(1.0 - Wc) / np.sqrt(V))
    G_aug = np.zeros((d + 1, d + 1)); G_aug[:d, :d] = G; G_aug[:d, d] = -u; G_aug[d, :d] = -u; G_aug[d, d] = V
    ev_aug = np.linalg.eigvalsh(G_aug)
    sigma_min_aug = float(np.sqrt(ev_aug[0]))
    conditioning = {"sigma_max": sigma_max, "sigma_min": sigma_min, "cond": sigma_max / sigma_min,
                    "numerical_rank": int((np.sqrt(np.maximum(ev, 0)) > sigma_max * d * np.finfo(np.float64).eps).sum()),
                    "ones_vector_fraction_in_col": ones_in_col, "ones_vector_residual_rel": ones_resid_rel,
                    "sigma_min_augmented_W_minus_ones": sigma_min_aug,
                    "h_cos_with_ones_direction_median": float(np.median(np.abs(H64 @ c) / (np.linalg.norm(H64, axis=1) * np.linalg.norm(c)))),
                    "h_cos_with_ones_direction_max": float(np.max(np.abs(H64 @ c) / (np.linalg.norm(H64, axis=1) * np.linalg.norm(c))))}

    # --- precision: recovery from bfloat16-rounded logits, and from bfloat16-rounded log-probs (logZ unknown)
    lb = bf16_round(logits).astype(np.float64)
    h_b = np.linalg.solve(G, Wd.T @ lb.T).T
    rel_bf16_logits = np.linalg.norm(h_b - H64, axis=1) / np.linalg.norm(H64, axis=1)
    m = logits.max(1, keepdims=True)
    logp = logits - (m + np.log(np.exp(logits - m).sum(1, keepdims=True)))
    lpb = bf16_round(logp.astype(np.float32)).astype(np.float64)
    rhs = np.vstack([Wd.T @ lpb.T, -lpb.sum(1)[None, :]])
    x = np.linalg.solve(G_aug, rhs).T
    rel_bf16_logp = np.linalg.norm(x[:, :d] - H64, axis=1) / np.linalg.norm(H64, axis=1)
    precision = {"from_bf16_logits_rel_err_median": float(np.median(rel_bf16_logits)),
                 "from_bf16_logits_rel_err_max": float(rel_bf16_logits.max()),
                 "from_bf16_logprobs_logZ_unknown_rel_err_median": float(np.median(rel_bf16_logp)),
                 "from_bf16_logprobs_logZ_unknown_rel_err_max": float(rel_bf16_logp.max()),
                 "h_norm_median": float(np.median(np.linalg.norm(H64, axis=1)))}

    # --- top-k closed form
    topk = {}
    for k in TOPK:
        r2, cos = [], []
        for i in range(n):
            hh = topk_recover(W, logits[i], k)
            a, b = _r2_cos(hh, H64[i]); r2.append(a); cos.append(b)
        topk[str(k)] = {"r2_median": float(np.median(r2)), "r2_min": float(np.min(r2)),
                        "r2_max": float(np.max(r2)), "cosine_median": float(np.median(cos))}
        print(f"top-{k:>5}: median per-row R^2 {topk[str(k)]['r2_median']:+.6f}  cosine {topk[str(k)]['cosine_median']:.4f}")
    summary = {
        "check": "OQ-16 anchor-state identity (dated erratum 2026-09-05)",
        "lm_head": wmeta, "n_rows": int(n), "rows_per_prompt": ROWS_PER_PROMPT,
        "n_prompts_per_run": N_PROMPTS, "provenance": prov,
        "forward": {"argmax_match_rate": float((am == data["argmax"]).mean()),
                    "top32_overlap_mean": float(overlap.mean()),
                    "top32_overlap_min": float(overlap.min()),
                    "top1_p_max_abs_gap": float(np.abs(p_top1 - data["p"][:, 0]).max())},
        "inverse_full_logits": {"rel_err_median": float(np.median(rel)),
                                "rel_err_max": float(rel.max()),
                                "f64_logits_rel_err_median": float(np.median(rel64)),
                                "f64_logits_rel_err_max": float(rel64.max())},
        "conditioning": conditioning,
        "precision": precision,
        "topk_closed_form": topk,
        "git_commit": _git_commit(), "numpy_version": np.__version__,
        "seconds": round(time.time() - t0, 1),
        "note": ("forward gaps reflect the live bf16 lm_head of the NF4-loaded verifier vs this bf16->f32 "
                 "lm_head on the float16-logged h; the inverse is the identity logits = W_U h_a with W_U of "
                 "full column rank, solved by float64 normal equations (rel_err from float32 logits is the "
                 "float32 rounding floor; f64_logits_* shows the identity itself); top-k recovery uses the "
                 "RECOMPUTED logits' top-k (id, log-prob) pairs, SVD least squares over [h, logZ] with no "
                 "ridge (minimum-norm when k < d + 1); r2_* are per-row R^2 about the row's own mean in raw h "
                 "space, NOT Stage-R's standardized pooled-MSE R^2; bf16 rounding is round-to-nearest-even "
                 "emulated on float32"),
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2))
    print(f"argmax match {summary['forward']['argmax_match_rate']:.4f}; top-32 overlap "
          f"{summary['forward']['top32_overlap_mean']:.4f}; full-logit inverse rel err "
          f"median {summary['inverse_full_logits']['rel_err_median']:.2e} (f64 {summary['inverse_full_logits']['f64_logits_rel_err_median']:.1e}); "
          f"sigma_min {sigma_min:.4f} cond {sigma_max / sigma_min:.1f}; ones-in-col {ones_in_col:.4f}; "
          f"sigma_min_aug {sigma_min_aug:.4f}; bf16 logprob recovery rel err median "
          f"{precision['from_bf16_logprobs_logZ_unknown_rel_err_median']:.2e}; wrote {out}")


if __name__ == "__main__":
    main()
