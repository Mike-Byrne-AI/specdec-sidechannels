"""Glue-bucket identification in real k-means vocab space (OQ-4).

D-7's real analog. The synthetic world has a LABELED function bucket that is
excluded from both sides of every prediction/gate argmax; real k-means buckets
carry no labels, so glue must be identified. The pre-registered rule
(docs/WHY_THIS_DIES.md K-7 addendum) is frequency-based:

  glue = the smallest prefix of buckets, ordered by their share of the
  top-`top_n` tokens' frequency mass, whose cumulative share reaches
  `mass_cover` (primary: top_n=100, mass_cover=0.80).

Frequency source: token counts from the TARGET's own sampled generations on
the committed prompt set (real/harvest_freq.py) — the deployment regime, with
no dependence on the draft or on any steering outcome.

Everything here is pure numpy/json (CI-safe; no torch). The consumers are
hf_specdec (gate + posterior in concept space, glue zero-boost via
steering.posterior_bias's negative-id convention) and the OQ-4 validation
tooling (tools/analyze_glue.py).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

Array = np.ndarray


def top_frequency_tokens(counts: dict[int, int] | dict[str, int], top_n: int) -> tuple[Array, Array]:
    """Top-`top_n` token ids by count, ties broken by LOWER token id.

    Deterministic by construction: the glue set must not depend on dict
    ordering. Returns (token_ids, counts) sorted by (-count, id).
    """
    ids = np.array([int(t) for t in counts.keys()], dtype=np.int64)
    ns = np.array([int(v) for v in counts.values()], dtype=np.int64)
    if (ns < 0).any():
        raise ValueError("negative token counts")
    order = np.lexsort((ids, -ns))[: int(top_n)]
    return ids[order], ns[order]


def identify_glue_buckets(
    bucket_of_token: Array,
    counts: dict[int, int] | dict[str, int],
    top_n: int = 100,
    mass_cover: float = 0.80,
    concentration_cap_frac: float = 1 / 8,
) -> dict:
    """Apply the pre-registered OQ-4 rule; returns ids + full diagnostics.

    - Rank buckets by their frequency-mass share of the top-`top_n` tokens;
      glue = the shortest prefix reaching `mass_cover` of that mass.
    - Bucket ties broken by lower bucket id (deterministic).
    - Tokens with bucket id < 0 (absent from the buckets file) cannot vote;
      they are counted in `n_top_tokens_unbucketed`.
    - `count_rule_ge5_buckets` is the cross-check from OQ-4's original
      wording (buckets holding >= 5 of the top-100 tokens); a large mismatch
      between the two rules is a robustness red flag to report, not hide.
    - `concentration_flag` fires when glue needs more than k/8 buckets:
      frequency mass NOT being concentrated in a few buckets is the K-7
      warning sign (the gate exclusion would then carve out a large chunk of
      the space).
    """
    bucket_of_token = np.asarray(bucket_of_token, dtype=np.int64)
    if not (0.0 < mass_cover <= 1.0):
        raise ValueError("mass_cover must be in (0, 1]")
    k = int(bucket_of_token.max()) + 1
    if k < 2:
        raise ValueError("need at least 2 buckets")

    tok_ids, tok_ns = top_frequency_tokens(counts, top_n)
    in_range = tok_ids < bucket_of_token.shape[0]
    if not in_range.all():
        raise ValueError(
            f"frequency counts contain token ids outside the vocab "
            f"({int((~in_range).sum())} of top-{top_n} >= {bucket_of_token.shape[0]})"
        )
    tok_buckets = bucket_of_token[tok_ids]
    bucketed = tok_buckets >= 0
    total_mass = float(tok_ns[bucketed].sum())
    if total_mass <= 0:
        raise ValueError("top tokens carry no bucketed frequency mass")

    mass_by_bucket = np.bincount(tok_buckets[bucketed], weights=tok_ns[bucketed].astype(np.float64), minlength=k)
    ntop_by_bucket = np.bincount(tok_buckets[bucketed], minlength=k)
    order = np.lexsort((np.arange(k), -mass_by_bucket))
    cum = np.cumsum(mass_by_bucket[order]) / total_mass
    n_glue = int(np.searchsorted(cum, mass_cover - 1e-12) + 1)
    glue = sorted(int(b) for b in order[:n_glue])

    return {
        "glue_bucket_ids": glue,
        "k": k,
        "rule": {"name": "top_n-frequency-mass-cover", "top_n": int(top_n), "mass_cover": float(mass_cover)},
        "diagnostics": {
            "covered_mass_share": float(cum[n_glue - 1]),
            "n_top_tokens_in_glue": int(sum(ntop_by_bucket[b] for b in glue)),
            "n_top_tokens_unbucketed": int((~bucketed).sum()),
            "per_bucket": [
                {
                    "bucket": int(b),
                    "n_top_tokens": int(ntop_by_bucket[b]),
                    "top_mass_share": float(mass_by_bucket[b] / total_mass),
                }
                for b in glue
            ],
            "count_rule_ge5_buckets": sorted(int(b) for b in np.flatnonzero(ntop_by_bucket >= 5)),
            "concentration_flag": bool(len(glue) > k * concentration_cap_frac),
        },
    }


def glue_remap(bucket_of_token: Array, glue_bucket_ids) -> tuple[Array, Array, int]:
    """(steer_bucket_of_token, glue_mask, C_concept) for the steering path.

    Concept buckets get compact ids 0..C-1 (order-preserving); glue buckets
    and tokens absent from the buckets file map to -1, which
    steering.posterior_bias treats as zero-boost — the exact real analog of
    the synthetic world's `[:C]` slice + labeled function bucket.

    glue_mask is over TOKENS (True where the token's bucket is glue); tokens
    with bucket -1 are NOT glue-masked — they are unbucketed, a different
    condition that summarize_audit tracks separately.
    """
    bucket_of_token = np.asarray(bucket_of_token, dtype=np.int64)
    k = int(bucket_of_token.max()) + 1
    glue = sorted(int(b) for b in glue_bucket_ids)
    if any(b < 0 or b >= k for b in glue):
        raise ValueError(f"glue bucket ids outside [0, {k})")
    if len(set(glue)) != len(glue):
        raise ValueError("duplicate glue bucket ids")
    concept = [b for b in range(k) if b not in set(glue)]
    C = len(concept)
    if C < 2:
        raise ValueError(f"glue set leaves {C} concept bucket(s); need >= 2 to steer")
    lut = np.full(k, -1, dtype=np.int64)
    lut[np.array(concept, dtype=np.int64)] = np.arange(C, dtype=np.int64)
    steer_map = np.where(bucket_of_token >= 0, lut[np.clip(bucket_of_token, 0, None)], -1)
    glue_mask = np.zeros(bucket_of_token.shape[0], dtype=bool)
    if glue:
        glue_mask = np.isin(bucket_of_token, np.array(glue, dtype=np.int64))
    return steer_map, glue_mask, C


def rejection_masses(
    p: Array, q: Array, bucket_of_token: Array, proposed: int,
    glue_mask: Array | None = None,
) -> tuple[float, float | None]:
    """(cross_bucket_residual_mass, residual_mass_glue) for one rejection.

    r = the normalized residual (specdec.residual_distribution — the same
    function the synthetic pipeline uses; never re-derived here). Cross mass
    is r's mass OUTSIDE the proposed token's bucket (F-8 estimand); glue mass
    is r's mass on glue-bucket tokens (None without a glue_mask), including
    the proposed token's own bucket when that bucket is glue — the
    concept-other derivation on AuditRecord accounts for that. NOTE: the
    derivation assumes every token is bucketed (no -1 ids); hf_specdec
    refuses --glue on a partial-coverage buckets file for exactly this
    reason.
    """
    from .specdec import residual_distribution

    r = residual_distribution(p, q)
    bucket_of_token = np.asarray(bucket_of_token)
    same = bucket_of_token == int(bucket_of_token[int(proposed)])
    cross = float(1.0 - r[same].sum())
    glue = float(r[glue_mask].sum()) if glue_mask is not None else None
    return cross, glue


def load_glue(
    path: str | None,
    expect_buckets_sha256: str | None = None,
    allow_mismatch: bool = False,
) -> tuple[list[int], dict] | tuple[None, None]:
    """Load a glue json, refusing one derived from a DIFFERENT buckets file.

    A glue set is meaningful only against the exact bucketization it was
    computed from; a stale pair would silently misclassify every bucket id.
    """
    if path is None:
        return None, None
    data = json.loads(Path(path).read_text())
    glue = [int(b) for b in data["glue_bucket_ids"]]
    problems = []
    if expect_buckets_sha256 is not None:
        got = data.get("buckets_sha256")
        if got is None:
            # A missing binding must not slide through as "compatible".
            problems.append("glue file carries no buckets_sha256 binding")
        elif got != expect_buckets_sha256:
            problems.append(
                f"glue file was derived from buckets sha {got[:12]}..., "
                f"loaded buckets file is {expect_buckets_sha256[:12]}..."
            )
    if problems and not allow_mismatch:
        raise SystemExit("refusing glue file:\n  - " + "\n  - ".join(problems)
                         + "\n(--allow-buckets-mismatch to override deliberately)")
    for pr in problems:
        print(f"[glue MISMATCH OVERRIDDEN] {pr}")
    return glue, data


def _main() -> None:  # pragma: no cover - thin CLI over the tested functions
    import argparse
    import hashlib
    import subprocess
    import time

    ap = argparse.ArgumentParser(description="Identify glue buckets (OQ-4 pre-registered rule)")
    ap.add_argument("--buckets", required=True)
    ap.add_argument("--freq", required=True, help="json with a 'counts' {token_id: n} field (harvest_freq.py)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--top-n", type=int, default=100)
    ap.add_argument("--mass-cover", type=float, default=0.80)
    ap.add_argument("--sensitivity", type=float, nargs="*", default=[0.70, 0.90])
    ap.add_argument("--tokenizer", default=None,
                    help="optional HF tokenizer id: decode the top glue tokens into the output for eyeballing")
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    if Path(args.out).exists() and not args.overwrite:
        raise SystemExit(f"{args.out} exists; results/ files are committed evidence (--overwrite to replace)")

    bdata = json.loads(Path(args.buckets).read_text())
    n_tokens = int(bdata["n_tokens"])
    bucket_of_token = np.full(n_tokens, -1, dtype=np.int64)
    for tok, b in bdata["bucket_of_token"].items():
        bucket_of_token[int(tok)] = int(b)
    fdata = json.loads(Path(args.freq).read_text())
    counts = fdata["counts"]

    res = identify_glue_buckets(bucket_of_token, counts, top_n=args.top_n, mass_cover=args.mass_cover)
    res["sensitivity"] = {
        f"{mc:.2f}": identify_glue_buckets(bucket_of_token, counts, top_n=args.top_n, mass_cover=mc)["glue_bucket_ids"]
        for mc in args.sensitivity
    }
    if args.tokenizer:
        from transformers import AutoTokenizer

        tok = AutoTokenizer.from_pretrained(args.tokenizer)
        ids, ns = top_frequency_tokens(counts, args.top_n)
        in_glue = np.isin(bucket_of_token[ids], np.array(res["glue_bucket_ids"], dtype=np.int64))
        res["top_glue_tokens_decoded"] = [
            {"id": int(t), "count": int(n), "text": tok.decode([int(t)])}
            for t, n, g in zip(ids, ns, in_glue) if g
        ][:50]

    def _git_commit() -> str:
        try:
            r = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True,
                               cwd=Path(__file__).resolve().parent, timeout=10)
            d = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True,
                               cwd=Path(__file__).resolve().parent, timeout=10)
            if r.returncode != 0:
                return "unknown"
            return r.stdout.strip() + ("-dirty" if d.stdout.strip() else "")
        except Exception:
            return "unknown"

    res.update({
        "buckets_file": args.buckets,
        "buckets_sha256": hashlib.sha256(Path(args.buckets).read_bytes()).hexdigest(),
        "buckets_model": bdata.get("model"),
        "freq_file": args.freq,
        "freq_sha256": hashlib.sha256(Path(args.freq).read_bytes()).hexdigest(),
        "git_commit": _git_commit(),
        "created": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    })
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(res, indent=2, sort_keys=True))
    print(f"[glue] k={res['k']} -> {len(res['glue_bucket_ids'])} glue buckets "
          f"(covered {res['diagnostics']['covered_mass_share']:.3f} of top-{args.top_n} mass; "
          f"concentration_flag={res['diagnostics']['concentration_flag']}) -> {args.out}")


if __name__ == "__main__":  # pragma: no cover
    _main()
