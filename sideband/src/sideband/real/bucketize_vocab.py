"""Cluster the vocabulary into semantic buckets from UNEMBEDDING rows.

Needs the model weights on disk (HF cache), not a GPU — and not the RAM for
the model either: the unembedding matrix is read DIRECTLY from the
safetensors shard that holds it (~2GB for Llama-3.1-8B), never instantiating
the model (a full fp32 8B load needs ~32GB and OOMs a 32GB box).

Output-side vectors are the right geometry: acceptance is about which OUTPUT
token the target picks, so buckets should partition the lm_head rows, not the
input embeddings. Falling back to the input embedding is only legitimate for
tied-embedding models (where it IS the lm_head); for untied models whose head
is serialized under an unknown name, this script refuses rather than silently
bucketing input-side geometry.

Writes buckets.json consumed by hf_specdec.py:
    {"k": 512, "bucket_of_token": {"0": 17, ...}, ...provenance...}
Findings cite this file by sha256 (hf_specdec meta), so it carries its own
provenance: which key was read, shape/dtype, git commit, size stats, n_iter
(if n_iter == max_iter the clustering is max_iter-bound, not converged —
say so in any writeup).

Notes for the audit's interpretation:
- expect heavy frequency structure: several buckets will be glue/function
  tokens. That is fine — the audit question is only whether draft/target
  REJECTION pairs cross bucket boundaries;
- k is a knob (256/512/1024); rerun the audit summary per k, it's cheap once
  the rejection log exists.

Usage:
    python -m sideband.real.bucketize_vocab \
        --model meta-llama/Llama-3.1-8B-Instruct --k 512 \
        --out results/real/buckets_k512.json
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import numpy as np

from ..buckets import kmeans, pca_project
from . import require_real_deps

# Checked in order; first key present in the checkpoint wins. lm_head first:
# output-side is the point. Tied models (e.g. Llama-3.2-1B/3B) only ship the
# input embedding, which IS their lm_head.
UNEMBED_KEYS = ("lm_head.weight", "model.embed_tokens.weight", "transformer.wte.weight")


def load_unembedding_rows(model_id: str) -> tuple[np.ndarray, dict]:
    """Read the unembedding matrix straight from the (cached) safetensors
    shards; returns (float32 (V, d), provenance dict). No model
    instantiation. Refuses input-embedding fallback for untied models."""
    torch, _ = require_real_deps()  # torch decodes bf16 tensors; numpy has no bf16
    from huggingface_hub import hf_hub_download
    from safetensors import safe_open

    try:
        index_path = hf_hub_download(model_id, "model.safetensors.index.json")
        weight_map: dict | None = json.loads(Path(index_path).read_text())["weight_map"]
    except Exception:
        weight_map = None  # single-file model

    for key in UNEMBED_KEYS:
        if weight_map is not None:
            if key not in weight_map:
                continue
            shard = hf_hub_download(model_id, weight_map[key])
        else:
            shard = hf_hub_download(model_id, "model.safetensors")
        with safe_open(shard, framework="pt") as f:
            if key not in f.keys():
                continue
            W = f.get_tensor(key)
        if key != "lm_head.weight":
            cfg = json.loads(Path(hf_hub_download(model_id, "config.json")).read_text())
            if not cfg.get("tie_word_embeddings", False):
                raise ValueError(
                    f"{model_id} has no lm_head.weight and is NOT tied "
                    f"(tie_word_embeddings falsy): its head must live under an "
                    f"unknown key. Refusing to bucket input-side geometry; extend "
                    f"UNEMBED_KEYS for this architecture."
                )
        prov = {"unembed_key_used": key, "shard": Path(shard).name,
                "shape": list(W.shape), "source_dtype": str(W.dtype)}
        print(f"[bucketize] {key} from {prov['shard']}: {tuple(W.shape)} {W.dtype}")
        return W.float().numpy(), prov
    raise ValueError(f"none of {UNEMBED_KEYS} found in {model_id}'s checkpoint")


def normalize_rows(W: np.ndarray) -> np.ndarray:
    """L2-normalize rows: cluster by direction, not by norm (norm tracks
    frequency more than meaning)."""
    norms = np.linalg.norm(W, axis=1, keepdims=True)
    return W / np.clip(norms, 1e-8, None)


def _git_commit() -> str:
    try:
        r = subprocess.run(["git", "status", "--porcelain"], capture_output=True,
                           text=True, cwd=Path(__file__).resolve().parent, timeout=10)
        dirty = "-dirty" if r.stdout.strip() else ""
        h = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                           text=True, cwd=Path(__file__).resolve().parent, timeout=10).stdout.strip()
        return (h or "unknown") + dirty
    except Exception:
        return "unknown"


def main() -> None:  # pragma: no cover - weights-on-disk entrypoint
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--k", type=int, default=512)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--pca-dim", type=int, default=128, help="project rows before k-means; 0 disables")
    ap.add_argument("--max-iter", type=int, default=200)
    ap.add_argument("--out", default="results/real/buckets.json")
    ap.add_argument("--overwrite", action="store_true",
                    help="allow replacing an existing buckets file (results/ files are "
                         "committed evidence cited by sha256; refusing is the default)")
    args = ap.parse_args()

    path = Path(args.out)
    if path.exists() and not args.overwrite:
        raise SystemExit(f"{path} already exists; pass --overwrite to replace it.")

    W, prov = load_unembedding_rows(args.model)
    X = normalize_rows(W)
    del W
    if args.pca_dim and args.pca_dim < X.shape[1]:
        X = pca_project(X, args.pca_dim)

    result = kmeans(X, k=args.k, seed=args.seed, max_iter=args.max_iter)
    sizes = np.bincount(result.labels, minlength=args.k)
    stats = {
        "n_tokens": int(result.labels.shape[0]),
        "n_iter": result.n_iter,
        "max_iter_bound": bool(result.n_iter >= args.max_iter),
        "inertia": result.inertia,
        "largest_bucket": int(sizes.max()),
        "median_bucket": float(np.median(sizes)),
        "empty_buckets": int((sizes == 0).sum()),
    }
    out = {
        "model": args.model,
        "k": args.k,
        "pca_dim": args.pca_dim,
        "seed": args.seed,
        "max_iter": args.max_iter,
        "git_commit": _git_commit(),
        **prov,
        **stats,
        "bucket_of_token": {str(i): int(b) for i, b in enumerate(result.labels)},
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out))
    print(json.dumps({**stats, "k": args.k, "out": str(path)}, indent=2))


if __name__ == "__main__":  # pragma: no cover
    main()
