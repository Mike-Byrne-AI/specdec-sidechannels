#!/usr/bin/env python
"""tools/build_balanced_groups.py — the BALANCED L3 lens over the OLMoE k512
concepts (docs/BLUEPRINT.md, "READER-AND-LENS RE-TEST AT S3 REGISTRATION",
2026-10-05; THE BALANCED LENS, pinned before this file ran).

The same transition affinity as the registered lens (tools/build_concept_groups:
glue-dropped k512 concept chains of the TRAIN-split rows, all seeds; S = P +
P^T), then FIEDLER-ORDER QUANTILE BINNING over the nonzero-degree concepts:
  - the symmetric normalised Laplacian L = I - D^-1/2 S D^-1/2 (one connected
    component asserted; a disconnected graph is a refusal, not a fallback);
  - its eigenvector for the second-smallest eigenvalue (numpy.linalg.eigh);
  - the Fiedler coordinate f = D^-1/2 v, sign fixed so the highest-degree
    concept's coordinate is non-negative (ties on degree to the lower id);
  - concepts sorted by f ascending (ties by concept id), cut into n_groups
    CONTIGUOUS bins, the remainder spread as one extra concept over the first
    bins (490 = 16 x 30 + 10: ten bins of 31 then six of 30);
  - zero-degree concepts assigned one by one, in concept-id order, to the
    currently smallest bin (ties to the lower bin id).
Glue stays class n_groups (17 classes at L3, as the registered lens). The
first successful run is the artifact (results/ files are committed evidence);
the output records the eigenvalues, the sign anchor, the bin edges, the sizes,
the zero-degree assignment and the persistence diagnostics the registered
builder records, beside the LOPSIDED lens's and k16's, as descriptions.

Run (the registered build):
  python tools/build_balanced_groups.py --harvest results/real/harvest_moe \
      --buckets512 results/real/buckets_olmoe_k512.json --glue512 results/real/glue_olmoe_k512.json \
      --buckets16 results/real/buckets_olmoe_k16.json --glue16 results/real/glue_olmoe_k16.json \
      --lopsided results/real/concept_groups_olmoe_v1.json --name concept_groups_olmoe_balanced_v1
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from sideband.glue import glue_remap, load_glue  # noqa: E402
from sideband.harvest import split_of_prompt, verified_seed_files  # noqa: E402
from build_concept_groups import persistence, transition_matrix  # noqa: E402

REAL = Path(__file__).resolve().parent.parent / "results" / "real"
N_GROUPS = 16
REGISTERED = ("READER-AND-LENS RE-TEST AT S3 REGISTRATION (docs/BLUEPRINT.md, 2026-10-05; THE BALANCED LENS, "
              "pinned before this artifact was built)")
RULE = ("Fiedler-order quantile binning: normalised Laplacian of S = P + P^T on the nonzero-degree concepts "
        "(one component asserted), eigenvector of the second-smallest eigenvalue, f = D^-1/2 v with the "
        "highest-degree concept non-negative, sort by f (ties by id), contiguous bins with the remainder on "
        "the first bins, zero-degree concepts to the smallest bin in id order; glue class n_groups")


def _sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _rel(path) -> str:
    """Repo-relative posix path where the file is under the repo, else as given."""
    try:
        return Path(path).resolve().relative_to(REAL.parent.parent.resolve()).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def bin_sizes(n: int, n_groups: int) -> list[int]:
    """n items into n_groups contiguous bins: the remainder as one extra item on the first bins."""
    base, rem = divmod(int(n), int(n_groups))
    return [base + 1] * rem + [base] * (n_groups - rem)


def fiedler_order(S: np.ndarray) -> tuple[np.ndarray, dict]:
    """The Fiedler coordinate of every node of a connected weighted graph and the
    ordering it induces (ties by node id). Refuses a disconnected graph."""
    S = np.asarray(S, dtype=np.float64)
    n = S.shape[0]
    if n < 2:
        raise SystemExit("the affinity has fewer than two nodes — refusing")
    d = S.sum(axis=1)
    if np.any(d <= 0):
        raise SystemExit("a zero-degree node reached the Laplacian — remove zero-degree concepts first")
    import scipy.sparse as sp
    from scipy.sparse.csgraph import connected_components
    n_comp, _ = connected_components(sp.csr_matrix(S > 0), directed=False)
    if n_comp != 1:
        raise SystemExit(f"the nonzero subgraph has {n_comp} connected components — the registered lens "
                         "requires one; refusing (no fallback is pinned)")
    dis = 1.0 / np.sqrt(d)
    L = np.eye(n) - (dis[:, None] * S * dis[None, :])
    L = 0.5 * (L + L.T)
    w, V = np.linalg.eigh(L)
    v = V[:, 1]
    f = dis * v
    anchor = int(np.argmax(d))          # argmax: the first (lowest id) among ties
    if f[anchor] < 0:
        f = -f
    order = np.lexsort((np.arange(n), f))
    return order, {"eigenvalues_first_three": [float(x) for x in w[:3]], "fiedler_gap": float(w[2] - w[1]),
                   "sign_anchor_node": anchor, "sign_anchor_degree": float(d[anchor]),
                   "fiedler_coordinate_range": [float(f.min()), float(f.max())]}


def balanced_groups(S_full: np.ndarray, n_groups: int = N_GROUPS) -> tuple[np.ndarray, dict]:
    """Group labels for every concept of the full affinity (zero-degree rows
    included) by the pinned rule."""
    S_full = np.asarray(S_full, dtype=np.float64)
    C = S_full.shape[0]
    degree = S_full.sum(axis=1)
    nz = np.nonzero(degree > 0)[0]
    zero = np.nonzero(degree <= 0)[0]
    order_nz, finfo = fiedler_order(S_full[np.ix_(nz, nz)])
    sizes = bin_sizes(len(nz), n_groups)
    labels = np.full(C, -1, dtype=np.int64)
    edges, start = [], 0
    for g, sz in enumerate(sizes):
        members = nz[order_nz[start:start + sz]]
        labels[members] = g
        edges.append([int(start), int(start + sz)])
        start += sz
    counts = np.bincount(labels[nz], minlength=n_groups)
    assignment = []
    for cidx in zero:                   # concept-id order
        g = int(np.argmin(counts))      # the smallest bin, ties to the lower id
        labels[cidx] = g
        counts[g] += 1
        assignment.append([int(cidx), g])
    assert np.all(labels >= 0)
    info = {"algorithm": "fiedler-order quantile binning (registered 2026-10-05)", "n_groups": int(n_groups),
            "bin_sizes_nonzero": sizes, "bin_edges_in_fiedler_order": edges,
            "group_sizes": np.bincount(labels, minlength=n_groups).tolist(),
            "group_sizes_nonzero_only": np.bincount(labels[nz], minlength=n_groups).tolist(),
            "n_zero_degree": int(len(zero)), "zero_degree_assignment": assignment,
            "n_connected_components_nonzero": 1, "numpy_version": np.__version__, **finfo}
    info["sign_anchor_concept"] = int(nz[info.pop("sign_anchor_node")])
    return labels, info


def load_concept_map(buckets_path: Path, glue_path: Path) -> tuple[np.ndarray, int, str]:
    bdata = json.loads(buckets_path.read_text())
    buckets = np.full(int(bdata["n_tokens"]), -1, dtype=np.int64)
    for tok, b in bdata["bucket_of_token"].items():
        buckets[int(tok)] = int(b)
    bsha = _sha(buckets_path)
    glue_ids, _ = load_glue(str(glue_path), expect_buckets_sha256=bsha)
    steer_map, _mask, C = glue_remap(buckets, glue_ids)
    return steer_map, int(C), bsha


def load_train_chains(harvest: Path, steer_map: np.ndarray, bsha: str) -> tuple[list[np.ndarray], list[np.ndarray], dict]:
    """Glue-dropped concept chains and raw token rows of the TRAIN split, sha-verified reads."""
    chains, train_tokens, shas = [], [], {}
    ref = None
    for meta, npz_path in verified_seed_files(harvest):
        shas[meta["npz_file"]] = meta["npz_sha256"]
        if ref is None:
            ref = meta
            expect = ref.get("buckets512_sha256")
            if expect and bsha != expect:
                raise SystemExit("--buckets512 sha != the harvest meta's buckets512_sha256 — wrong file for this harvest")
        z = np.load(npz_path)
        toks, lens, pidx = z["tokens"], z["lengths"], z["prompt_idx"]
        for i in range(toks.shape[0]):
            if split_of_prompt(int(pidx[i])) != "train":
                continue
            row = toks[i, : int(lens[i])]
            train_tokens.append(row)
            cc = steer_map[row]
            chains.append(cc[cc >= 0])
    return chains, train_tokens, shas


def label_seqs(train_tokens: list[np.ndarray], space_map: np.ndarray, glue_class: int, groups: np.ndarray | None):
    full, dropped = [], []
    for row in train_tokens:
        m = space_map[row]
        lab = np.where(m >= 0, (groups[np.clip(m, 0, None)] if groups is not None else m), glue_class)
        full.append(lab)
        dropped.append(lab[m >= 0])
    return full, dropped


def mean_pers(seqs) -> float:
    vals = [persistence(s) for s in seqs if len(s) >= 2]
    return float(np.mean(vals))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--harvest", default="results/real/harvest_moe")
    ap.add_argument("--buckets512", default=str(REAL / "buckets_olmoe_k512.json"))
    ap.add_argument("--glue512", default=str(REAL / "glue_olmoe_k512.json"))
    ap.add_argument("--buckets16", default=str(REAL / "buckets_olmoe_k16.json"))
    ap.add_argument("--glue16", default=str(REAL / "glue_olmoe_k16.json"))
    ap.add_argument("--lopsided", default=str(REAL / "concept_groups_olmoe_v1.json"),
                    help="the registered lens, for the side-by-side persistence diagnostic")
    ap.add_argument("--name", default="concept_groups_olmoe_balanced_v1")
    ap.add_argument("--out-dir", default=str(REAL), help="tests only: a scratch directory")
    ap.add_argument("--n-groups", type=int, default=N_GROUPS)
    args = ap.parse_args()

    out_path = Path(args.out_dir) / f"{args.name}.json"
    if out_path.exists():
        raise SystemExit(f"{out_path} exists; the first successful run is the artifact — refusing")
    if args.n_groups != N_GROUPS and Path(args.out_dir).resolve() == REAL.resolve():
        raise SystemExit("an unregistered --n-groups may not write under results/")

    t0 = time.time()
    steer_map, C, bsha = load_concept_map(Path(args.buckets512), Path(args.glue512))
    steer16, C16, _b16 = load_concept_map(Path(args.buckets16), Path(args.glue16))
    chains, train_tokens, harvest_shas = load_train_chains(Path(args.harvest), steer_map, bsha)
    P = transition_matrix(chains, C)
    S = P + P.T
    labels, info = balanced_groups(S, args.n_groups)

    lop = json.loads(Path(args.lopsided).read_text()) if Path(args.lopsided).exists() else None
    lop_groups = np.asarray(lop["group_of_concept"], dtype=np.int64) if lop else None
    bal_full, bal_drop = label_seqs(train_tokens, steer_map, args.n_groups, labels)
    k16_full, k16_drop = label_seqs(train_tokens, steer16, C16, None)
    diag = {"persistence_train_full_chain": {"balanced_L3": mean_pers(bal_full), "k16": mean_pers(k16_full)},
            "persistence_train_glue_dropped": {"balanced_L3": mean_pers(bal_drop), "k16": mean_pers(k16_drop)}}
    if lop_groups is not None:
        lf, ld = label_seqs(train_tokens, steer_map, int(lop["n_groups"]), lop_groups)
        diag["persistence_train_full_chain"]["lopsided_L3"] = mean_pers(lf)
        diag["persistence_train_glue_dropped"]["lopsided_L3"] = mean_pers(ld)
        diag["lopsided_group_sizes"] = lop["construction"]["group_sizes"]

    out = {
        "name": args.name, "group_of_concept": labels.tolist(), "n_groups": int(args.n_groups),
        "C_source_concepts": int(C), "glue_class_id": int(args.n_groups),
        "construction": info, "diagnostics": diag,
        "provenance": {"registered": REGISTERED, "rule": RULE,
                       "buckets_k512_sha256": bsha, "glue_k512": _rel(args.glue512), "glue_k512_sha256": _sha(Path(args.glue512)),
                       "buckets_k16_sha256": _b16, "harvest": _rel(args.harvest), "harvest_meta_shas": harvest_shas,
                       "n_train_rows": len(train_tokens), "train_split_rule": "sideband.harvest.split_of_prompt == 'train'",
                       "chain_semantics": "k512 concept ids after glue_remap; glue / unbucketed tokens dropped from the chain",
                       "lopsided_artifact": (_rel(args.lopsided) if lop else None),
                       "lopsided_artifact_sha256": (_sha(Path(args.lopsided)) if lop else None),
                       "builder_sha256": _sha(Path(__file__)), "first_run_is_artifact": True},
        "runtime_s": round(time.time() - t0, 1),
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(out, indent=1) + "\n")
    print(f"wrote {out_path}: sizes {info['group_sizes']} (max {max(info['group_sizes'])}), "
          f"zero-degree {info['n_zero_degree']}, gap {info['fiedler_gap']:.4f}, "
          f"persistence glue-dropped balanced {diag['persistence_train_glue_dropped']['balanced_L3']:.4f}"
          + (f" lopsided {diag['persistence_train_glue_dropped']['lopsided_L3']:.4f}" if lop else "")
          + f" k16 {diag['persistence_train_glue_dropped']['k16']:.4f}; {out['runtime_s']} s")


if __name__ == "__main__":
    main()
