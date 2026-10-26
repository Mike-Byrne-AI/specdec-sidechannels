#!/usr/bin/env python3
"""Build the L3 label space concept_groups_v1 (BLUEPRINT Phase 3, registered
2026-08-30, BEFORE this artifact existed).

Registered rule, implemented verbatim:
- over the 510 k512 CONCEPT buckets (glue_remap of the committed
  buckets_k512 + glue_k512), estimate the bucket-bigram transition matrix on
  consecutive TRAIN-SPLIT tokens only (all 8 seeds; glue/unbucketed tokens
  dropped from the chain);
- symmetrize the row-normalized matrix (S = P + P^T);
- spectral clustering into 16 groups (seed 0, n_init 10, precomputed
  affinity); if degenerate (any empty group), fall back to average-linkage
  agglomerative on distance = S.max() - S, and record the fallback.

Output: results/real/concept_groups_v1.json — group_of_concept (510 ints),
full provenance, and persistence diagnostics (L3 vs concept_k16, train
split, both the full-chain-with-glue-class and glue-dropped views). The
motivation and the report-even-if-it-fails-to-beat-k16 clause live in the
registration.

Run: python tools/build_concept_groups.py
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from sideband.glue import glue_remap, load_glue  # noqa: E402
from sideband.harvest import split_of_prompt, verified_seed_files  # noqa: E402

REAL = Path(__file__).resolve().parent.parent / "results" / "real"
N_GROUPS = 16
SEED = 0


def transition_matrix(chains: list[np.ndarray], C: int) -> np.ndarray:
    """Row-normalized bigram matrix over concept chains (glue already
    dropped by the caller). Rows with no outgoing transitions stay zero."""
    T = np.zeros((C, C), dtype=np.float64)
    for ch in chains:
        if len(ch) >= 2:
            np.add.at(T, (ch[:-1], ch[1:]), 1.0)
    row = T.sum(axis=1, keepdims=True)
    with np.errstate(invalid="ignore", divide="ignore"):
        P = np.where(row > 0, T / row, 0.0)
    return P


def group_concepts(chains: list[np.ndarray], C: int, n_groups: int = N_GROUPS,
                   seed: int = SEED) -> tuple[np.ndarray, dict]:
    """The registered grouping rule + the dated pre-build amendment:
    zero-degree buckets are excluded from clustering (a disconnected
    affinity graph degenerates the spectral embedding without tripping the
    empty-group check); the nonzero subgraph falls back to agglomerative
    if it still has > n_groups connected components; zero-degree buckets
    join the LARGEST group (ties to lower id), count recorded."""
    P = transition_matrix(chains, C)
    S = P + P.T
    import scipy.sparse as sp
    import sklearn
    from scipy.sparse.csgraph import connected_components
    from sklearn.cluster import AgglomerativeClustering, SpectralClustering

    degree = S.sum(axis=1)
    nz = degree > 0
    Snz = S[np.ix_(nz, nz)]
    n_comp, _ = connected_components(sp.csr_matrix(Snz > 0), directed=False)
    info: dict = {"algorithm": "spectral", "n_groups": n_groups, "seed": seed,
                  "n_init": 10, "fallback_used": False,
                  "sklearn_version": sklearn.__version__,
                  "assign_labels": "kmeans (SpectralClustering default)",
                  "n_zero_degree": int((~nz).sum()),
                  "n_connected_components_nonzero": int(n_comp)}

    def _agglomerative(A):
        dist = A.max() - A
        np.fill_diagonal(dist, 0.0)
        return AgglomerativeClustering(n_clusters=n_groups, metric="precomputed",
                                       linkage="average").fit_predict(dist)

    if n_comp > n_groups:
        info["fallback_used"] = True
        info["algorithm"] = "agglomerative-average (disconnected subgraph)"
        labels_nz = _agglomerative(Snz)
    else:
        labels_nz = SpectralClustering(n_clusters=n_groups, affinity="precomputed",
                                       random_state=seed, n_init=10).fit_predict(Snz)
        if (np.bincount(labels_nz, minlength=n_groups) == 0).any():
            info["fallback_used"] = True
            info["algorithm"] = "agglomerative-average (empty spectral group)"
            labels_nz = _agglomerative(Snz)
    sizes_nz = np.bincount(labels_nz, minlength=n_groups)
    largest = int(np.argmax(sizes_nz))  # argmax ties break to lower id
    labels = np.full(C, largest, dtype=np.int64)
    labels[nz] = labels_nz
    info["zero_degree_assigned_to_group"] = largest
    info["group_sizes"] = np.bincount(labels, minlength=n_groups).tolist()
    info["group_sizes_nonzero_only"] = sizes_nz.tolist()
    return labels, info


def persistence(seq: np.ndarray) -> float:
    """Fraction of consecutive pairs with equal labels."""
    if len(seq) < 2:
        return float("nan")
    return float((seq[:-1] == seq[1:]).mean())


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--harvest", default="results/real/harvest_shadow")
    ap.add_argument("--buckets512", default=str(REAL / "buckets_k512.json"))
    ap.add_argument("--glue512", default=str(REAL / "glue_k512.json"))
    ap.add_argument("--buckets16", default=str(REAL / "buckets_k16.json"))
    ap.add_argument("--glue16", default=str(REAL / "glue_k16.json"))
    ap.add_argument("--name", default="concept_groups_v1",
                    help="artifact name; output file is results/real/{name}.json")
    ap.add_argument("--overwrite", action="store_true",
                    help="results/ files are committed evidence; the registered "
                         "first-successful-run-is-the-artifact rule means an "
                         "existing artifact is never silently rebuilt")
    args = ap.parse_args()

    out_path = REAL / f"{args.name}.json"
    if out_path.exists() and not args.overwrite:
        raise SystemExit(f"{out_path} exists; first-successful-run-is-the-artifact "
                         "(pass --overwrite only with a registered reason)")

    t0 = time.time()
    bpath = Path(args.buckets512)
    gpath = Path(args.glue512)
    bdata = json.loads(bpath.read_text())
    buckets = np.full(int(bdata["n_tokens"]), -1, dtype=np.int64)
    for tok, b in bdata["bucket_of_token"].items():
        buckets[int(tok)] = int(b)
    bsha = hashlib.sha256(bpath.read_bytes()).hexdigest()
    glue_ids, _ = load_glue(str(gpath), expect_buckets_sha256=bsha)
    steer_map, _mask, C = glue_remap(buckets, glue_ids)

    # k16 comparison space (same merged-label convention as the probes)
    b16path, g16path = Path(args.buckets16), Path(args.glue16)
    b16data = json.loads(b16path.read_text())
    b16 = np.full(int(b16data["n_tokens"]), -1, dtype=np.int64)
    for tok, b in b16data["bucket_of_token"].items():
        b16[int(tok)] = int(b)
    g16_ids, _ = load_glue(str(g16path),
                           expect_buckets_sha256=hashlib.sha256(b16path.read_bytes()).hexdigest())
    steer16, _m16, C16 = glue_remap(b16, g16_ids)

    harvest = Path(args.harvest)
    chains: list[np.ndarray] = []            # glue-dropped concept chains (train only)
    train_tokens: list[np.ndarray] = []      # raw token rows (train only)
    harvest_shas = {}
    ref_meta = None
    for meta, npz_path in verified_seed_files(harvest):  # sha-verified reads
        harvest_shas[meta["npz_file"]] = meta["npz_sha256"]
        if ref_meta is None:
            ref_meta = meta
            # The chain must be built over the bucketization this harvest
            # logged (critic blocker 2026-08-31 — cross-model spaces index
            # silently; refuse a buckets512 the meta did not bind).
            expect = ref_meta.get("buckets512_sha256")
            if expect and bsha != expect:
                raise SystemExit(f"{bpath} sha != harvest meta buckets512_sha256 — "
                                 "wrong --buckets512 for this harvest")
        z = np.load(npz_path)
        toks, lens, pidx = z["tokens"], z["lengths"], z["prompt_idx"]
        for i in range(toks.shape[0]):
            if split_of_prompt(int(pidx[i])) != "train":
                continue
            row = toks[i, : int(lens[i])]
            train_tokens.append(row)
            cc = steer_map[row]
            chains.append(cc[cc >= 0])

    group_of_concept, info = group_concepts(chains, C)

    # Persistence diagnostics on the train split, both views, both spaces.
    def label_seqs(space_map: np.ndarray, n_concept: int, groups: np.ndarray | None):
        full, dropped = [], []
        for row in train_tokens:
            m = space_map[row]
            if groups is not None:
                lab = np.where(m >= 0, groups[np.clip(m, 0, None)], n_concept)
            else:
                lab = np.where(m >= 0, m, n_concept)
            full.append(lab)
            dropped.append(lab[m >= 0])
        return full, dropped

    l3_full, l3_drop = label_seqs(steer_map, N_GROUPS, group_of_concept)
    k16_full, k16_drop = label_seqs(steer16, C16, None)

    def mean_pers(seqs):
        vals = [persistence(s) for s in seqs if len(s) >= 2]
        return float(np.mean(vals))

    out = {
        "name": args.name,
        "group_of_concept": group_of_concept.tolist(),
        "n_groups": N_GROUPS,
        "C_source_concepts": C,
        "glue_class_id": N_GROUPS,
        "construction": info,
        "provenance": {
            "rule": "BLUEPRINT Phase 3 protocol (registered 2026-08-30, before this artifact)",
            "buckets_k512_sha256": bsha,
            "glue_k512": str(gpath.name),
            "train_split_rule": "prompt_idx % 7 in {0..4}",
            "n_train_rows": len(train_tokens),
            "harvest_meta_shas": harvest_shas,
            "chain_semantics": ("skip-and-join: glue/unbucketed removed, flanking "
                                "concept tokens become adjacent bigrams; bigrams "
                                "within one row only, never across rows or seeds"),
            "first_run_is_artifact": True,
        },
        "diagnostics": {
            "persistence_train_full_chain": {
                "concept_groups_v1": mean_pers(l3_full),
                "concept_k16": mean_pers(k16_full),
            },
            "persistence_train_glue_dropped": {
                "concept_groups_v1": mean_pers(l3_drop),
                "concept_k16": mean_pers(k16_drop),
            },
        },
        "runtime_s": round(time.time() - t0, 1),
    }
    out_path.write_text(json.dumps(out, indent=1, sort_keys=True))
    print(json.dumps({"fallback_used": info["fallback_used"],
                      "group_sizes": info["group_sizes"],
                      "diagnostics": out["diagnostics"]}, indent=2))


if __name__ == "__main__":
    main()
