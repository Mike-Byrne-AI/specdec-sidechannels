#!/usr/bin/env python3
"""Pre-probe data audit of the Phase-2 S1 harvest (leak/degeneracy/marginals).

Run BEFORE any Phase-3 probe trains; its numbers feed the Phase-3
registration's baselines and are the committed answer to "did we check the
dataset for leaks and issues". Read-only diagnostics — no verdict here can
create a finding, only block one.

Sections:
- split_integrity: the pinned prompt-level split recomputed from stored
  prompt_idx; any anchor whose prompt sits in two splits is impossible by
  construction (prompt_idx is the split key) — checked anyway.
- contamination: token-8-gram overlap between splits (distinct-gram basis
  and test-occurrence-weighted). High overlap would mean test continuations
  replay train text and probe accuracy partly measures memorized surface
  overlap rather than generalization.
- duplication/degeneracy: within-prompt-across-seed distinct-8-gram ratio
  (8 sampled continuations of the same prompt), and loopy-row fraction
  (rows where some 8-gram repeats >= 4 times — temp-1.0 repetition traps).
- label_marginals: per label space (concept-k16, concept-k512; glue and
  unbucketed labels mapped to one extra GLUE class), per offset 1..4 on
  each split: class count, majority class rate, glue-class rate, entropy.
  These are the floors every probe must beat; pinned into the Phase-3
  registration as named baselines.

Run: python tools/audit_harvest.py --dir results/real/harvest_shadow \
        --out results/real/harvest_audit.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from sideband.glue import glue_remap, load_glue  # noqa: E402
from sideband.harvest import GAMMA_DEFAULT, label_index, split_of_prompt  # noqa: E402

REAL = Path(__file__).resolve().parent.parent / "results" / "real"
NGRAM = 8
LOOP_REPEATS = 4


def _load_bucket_array(path: Path) -> tuple[np.ndarray, str]:
    data = json.loads(path.read_text())
    n = int(data["n_tokens"])
    arr = np.full(n, -1, dtype=np.int64)
    for tok, b in data["bucket_of_token"].items():
        arr[int(tok)] = int(b)
    return arr, hashlib.sha256(path.read_bytes()).hexdigest()


def _rows(harvest_dir: Path, shas_out: dict | None = None,
          metas_out: list | None = None):
    """Yield (seed, prompt_idx, tokens_list) per continuation row through
    verified_seed_files — the single sanctioned sha-verified reader (also
    the single home of the prefix-generic glob + mixed-prefix refusal)."""
    from sideband.harvest import verified_seed_files

    for meta, npz_path in verified_seed_files(harvest_dir):
        if shas_out is not None:
            shas_out[meta["npz_file"].replace(".npz", ".meta.json")] = meta["npz_sha256"]
        if metas_out is not None:
            metas_out.append(meta)
        z = np.load(npz_path)
        toks, lens, pidx = z["tokens"], z["lengths"], z["prompt_idx"]
        for i in range(toks.shape[0]):
            yield int(meta["seed"]), int(pidx[i]), toks[i, : int(lens[i])].tolist()


def _grams(tokens: list[int], n: int = NGRAM):
    return [tuple(tokens[i: i + n]) for i in range(len(tokens) - n + 1)]


DEFAULT_SPACES = (
    ("concept_k16", REAL / "buckets_k16.json", REAL / "glue_k16.json"),
    ("concept_k512", REAL / "buckets_k512.json", REAL / "glue_k512.json"),
)


def _git_commit() -> str:
    import subprocess

    try:
        r = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True,
                           cwd=Path(__file__).resolve().parent, timeout=10)
        d = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True,
                           cwd=Path(__file__).resolve().parent, timeout=10)
        return ("unknown" if r.returncode != 0
                else r.stdout.strip() + ("-dirty" if d.stdout.strip() else ""))
    except Exception:
        return "unknown"


def audit(harvest_dir: Path, space_files=DEFAULT_SPACES) -> dict:
    npz_shas: dict = {}
    metas: list = []
    rows = list(_rows(harvest_dir, shas_out=npz_shas, metas_out=metas))
    if not rows:
        raise SystemExit(f"no harvest rows in {harvest_dir}")
    # Space files must be the exact ones the harvest logged masses against
    # (critic blocker 2026-08-31 — same guard as run_probes' binding).
    ref = metas[0]
    for kname, bpath, _g in space_files:
        key = "buckets" + kname.rsplit("_k", 1)[-1] + "_sha256"
        expect = ref.get(key)
        if expect and hashlib.sha256(Path(bpath).read_bytes()).hexdigest() != expect:
            raise SystemExit(f"{bpath} sha != harvest meta {key} — wrong space "
                             "files for this harvest (wrong --buckets* args?)")

    # --- contamination: 8-gram overlap across the pinned split ---
    gram_sets = {"train": set(), "val": set(), "test": set()}
    gram_lists = {"train": [], "val": [], "test": []}
    for _seed, pidx, toks in rows:
        sp = split_of_prompt(pidx)
        g = _grams(toks)
        gram_sets[sp].update(g)
        gram_lists[sp].append(g)

    def overlap(a: str, b: str) -> dict:
        """Distinct grams of split `a` also present in split `b`, plus the
        occurrence-weighted rate over split a's stream."""
        inter = len(gram_sets[a] & gram_sets[b])
        occ = sum(1 for gl in gram_lists[a] for g in gl if g in gram_sets[b])
        total_occ = sum(len(gl) for gl in gram_lists[a])
        return {
            "distinct_frac": inter / max(1, len(gram_sets[a])),
            "occurrence_frac": occ / max(1, total_occ),
            "n_distinct": len(gram_sets[a]),
        }

    contamination = {
        "test_in_train": overlap("test", "train"),
        "val_in_train": overlap("val", "train"),
        "ngram": NGRAM,
    }

    # --- duplication across seeds of the same prompt; loopy rows ---
    per_prompt: dict[int, list[list[tuple]]] = {}
    loopy_rows = 0
    for _seed, pidx, toks in rows:
        per_prompt.setdefault(pidx, []).append(_grams(toks))
        if toks:
            counts = Counter(_grams(toks))
            if counts and max(counts.values()) >= LOOP_REPEATS:
                loopy_rows += 1
    distinct_ratios = []
    for pidx, gls in per_prompt.items():
        total = sum(len(g) for g in gls)
        distinct = len({g for gl in gls for g in gl})
        if total:
            distinct_ratios.append(distinct / total)
    duplication = {
        "within_prompt_across_seed_distinct_8gram_ratio": ({
            "mean": float(np.mean(distinct_ratios)),
            "p10": float(np.percentile(distinct_ratios, 10)),
            "min": float(np.min(distinct_ratios)),
        } if distinct_ratios else None),
        "loopy_row_fraction": loopy_rows / len(rows),
        "loop_rule": f"some 8-gram repeats >= {LOOP_REPEATS}x within one row",
        "n_rows": len(rows),
    }

    # --- label marginals per concept label space ---
    spaces = {}
    for kname, bpath, gpath in space_files:
        buckets, bsha = _load_bucket_array(bpath)
        glue_ids, _gmeta = load_glue(str(gpath), expect_buckets_sha256=bsha)
        steer_map, _mask, C = glue_remap(buckets, glue_ids)
        # Label rule pinned for Phase 3: concept ids 0..C-1; glue AND
        # unbucketed both -> class C (one merged GLUE class).
        label_of_token = np.where(steer_map >= 0, steer_map, C)
        per_offset = {}
        for j in range(1, GAMMA_DEFAULT + 1):
            split_stats = {}
            for sp in ("train", "val", "test"):
                labels: Counter = Counter()
                for _seed, pidx, toks in rows:
                    if split_of_prompt(pidx) != sp:
                        continue
                    for a in range(len(toks)):
                        li = label_index(a, j)
                        if li < len(toks):
                            labels[int(label_of_token[toks[li]])] += 1
                n = sum(labels.values())
                if n == 0:
                    split_stats[sp] = None  # split empty in this dataset
                    continue
                freqs = np.array([c / n for c in labels.values()])
                split_stats[sp] = {
                    "n_pairs": n,
                    "n_classes_seen": len(labels),
                    "majority_class": int(max(labels, key=labels.get)),
                    "majority_rate": max(labels.values()) / n,
                    "glue_class_rate": labels.get(C, 0) / n,
                    "entropy_bits": float(-(freqs * np.log2(freqs)).sum()),
                }
            per_offset[f"offset_{j}"] = split_stats
        spaces[kname] = {
            "C_concept": C,
            "n_classes": C + 1,
            "glue_class_id": C,
            "buckets_sha256": bsha,
            "per_offset": per_offset,
        }

    return {
        "dir": str(harvest_dir).replace("\\", "/"),
        "provenance": {
            "npz_sha256_verified": npz_shas,
            "git_commit": _git_commit(),
            "ngram": NGRAM,
            "loop_repeats": LOOP_REPEATS,
            "space_files": [(n, str(Path(b).name), str(Path(g).name)) for n, b, g in space_files],
        },
        "n_rows": len(rows),
        "n_tokens": sum(len(t) for _, _, t in rows),
        "contamination": contamination,
        "duplication": duplication,
        "label_marginals": spaces,
        "note": ("read-only pre-probe diagnostics; label rule (glue+unbucketed -> "
                 "one merged class C) is the Phase-3 label convention"),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="results/real/harvest_shadow")
    ap.add_argument("--out", default="results/real/harvest_audit.json")
    ap.add_argument("--space-tag", default="concept",
                    help="label-space name prefix in the report ({tag}_k16/{tag}_k512)")
    ap.add_argument("--buckets16", default=str(REAL / "buckets_k16.json"))
    ap.add_argument("--glue16", default=str(REAL / "glue_k16.json"))
    ap.add_argument("--buckets512", default=str(REAL / "buckets_k512.json"))
    ap.add_argument("--glue512", default=str(REAL / "glue_k512.json"))
    args = ap.parse_args()
    space_files = (
        (f"{args.space_tag}_k16", Path(args.buckets16), Path(args.glue16)),
        (f"{args.space_tag}_k512", Path(args.buckets512), Path(args.glue512)),
    )
    report = audit(Path(args.dir), space_files=space_files)
    Path(args.out).write_text(json.dumps(report, indent=1, sort_keys=True))
    slim = {
        "contamination_test_in_train": report["contamination"]["test_in_train"],
        "duplication": report["duplication"]["within_prompt_across_seed_distinct_8gram_ratio"],
        "loopy_row_fraction": report["duplication"]["loopy_row_fraction"],
        "majority_k16_offset2_test": report["label_marginals"][f"{args.space_tag}_k16"]["per_offset"]["offset_2"]["test"],
    }
    print(json.dumps(slim, indent=2))


if __name__ == "__main__":
    main()
