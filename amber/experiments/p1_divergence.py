"""P1 — Real greedy divergence rate and the D-6 four-way rate table (OQ-1; K-2).

Reads results/p1/{generate,draft,target_selfcheck} and reports, per token of
TARGET-GENERATED text:

  amber_v0_bits        Elias-gamma gaps+ranks, exactly as codec.encode would
                       emit them (headers excluded), computed from the draft
                       ranks — the format's real rate on this text
  ideal_regimeA_bits   the format's own information bound: H2(divergence rate)
                       + mean over corrections of -log2 P_emp(rank) — an
                       empirical-entropy bound (model cost not charged)
  ac_under_draft_bits  -mean log2 q_draft(true token): what arithmetic coding
                       with the draft as the probability model would pay
                       (the regime-B baseline; requires the draft at decode)
  zstd19 / lzma / zlib on the generated TEXT bytes, expressed per token
  raw_bits             log2(V)

plus divergence rate overall / per prompt family / by position-in-generation,
the target self-consistency rate (teacher-forced target argmax == generated
token), and the draft near-tie mass at the P2 thresholds.

Pre-registered kill (WHY_THIS_DIES K-2): amber_v0_bits > zstd19 bits on this
target-generated text kills the compression story for this pair; the
attestation salvage survives independently.
"""

from __future__ import annotations

import argparse
import json
import lzma
import time
import zlib
from collections import Counter
from pathlib import Path

import numpy as np

from amber.bits import BitWriter, gamma_encode
from amber.real.divergence import load_generated, load_rank

RESULTS = Path(__file__).resolve().parent.parent / "results"


def amber_bits(ranks: np.ndarray) -> int:
    """Exact payload bits codec.encode would emit for this rank sequence."""
    w = BitWriter(); gap = 0
    for r in ranks:
        if r == 1:
            gap += 1; continue
        gamma_encode(w, gap + 1); gamma_encode(w, int(r) - 1); gap = 0
    return w.n_bits


def _h2(p: float) -> float:
    return 0.0 if p in (0.0, 1.0) else float(-(p * np.log2(p) + (1 - p) * np.log2(1 - p)))


def ideal_bits(ranks: np.ndarray, log2q: np.ndarray, log2qmax: np.ndarray) -> float:
    """a01's definition: H2(d) + d * E[-log2 q~(x) | divergence], q~ = q
    renormalized over non-argmax tokens (q(x) / (1 - q_max))."""
    div = ranks != 1; p = float(div.mean())
    if not div.any():
        return _h2(p)
    qmax = np.exp2(log2qmax[div].astype(np.float64))
    corr = -(log2q[div].astype(np.float64) - np.log2(np.maximum(1.0 - qmax, 1e-300)))
    return _h2(p) + p * float(corr.mean())


def ideal_rank_entropy_bits(ranks: np.ndarray) -> float:
    """Empirical-entropy variant: H2(d) + d * H(empirical rank | correction).
    Model cost not charged — a floor for any static rank coder on this data."""
    div = ranks != 1; p = float(div.mean())
    cnt = Counter(int(r) for r in ranks[div]); m = sum(cnt.values())
    hr = -sum(c / m * np.log2(c / m) for c in cnt.values()) if m else 0.0
    return _h2(p) + p * hr


def content_coders(text: str) -> dict:
    b = text.encode("utf-8")
    out = {"utf8_bytes": len(b), "zlib9_bytes": len(zlib.compress(b, 9)), "lzma_bytes": len(lzma.compress(b, preset=9))}
    try:
        import zstandard
        out["zstd19_bytes"] = len(zstandard.ZstdCompressor(level=19).compress(b))
    except ImportError:
        out["zstd19_bytes"] = None
    return out


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default="results/p1")
    a = ap.parse_args(argv); out = Path(a.out)
    gen = {r: (ids, plen) for r, ids, plen in load_generated(out)}
    draft = load_rank(out, "draft"); prompts = json.loads((out / "prompts.json").read_text())["prompts"]
    self_ok = None
    if (out / "target_selfcheck" / "DONE").exists():
        tsc = load_rank(out, "target_selfcheck")
        agree = np.concatenate([p["rank"] == 1 for p in tsc["per_prompt"]])
        self_ok = {"rate": float(agree.mean()), "mismatches": int((~agree).sum()), "positions": int(agree.size)}

    ranks = np.concatenate([p["rank"] for p in draft["per_prompt"]])
    log2q = np.concatenate([p["log2q"] for p in draft["per_prompt"]])
    log2qmax = np.concatenate([p["log2qmax"] for p in draft["per_prompt"]])
    gaps = np.concatenate([p["gap"] for p in draft["per_prompt"]])
    n = len(ranks)
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(draft["meta"]["model"], local_files_only=True)
    V = len(tok)
    gen_text = "".join(tok.decode(gen[p["row"]][0][gen[p["row"]][1]:]) for p in draft["per_prompt"])
    cc = content_coders(gen_text)

    row = {
        "positions": n, "vocab": V,
        "divergence_rate": float((ranks != 1).mean()),
        "rank_quantiles_at_corrections": {q: int(np.quantile(ranks[ranks != 1], float(q))) for q in ("0.5", "0.9", "0.99")} if (ranks != 1).any() else {},
        "amber_v0_bits_per_token": amber_bits(ranks) / n,
        "ideal_regimeA_bits_per_token": ideal_bits(ranks, log2q, log2qmax),
        "ideal_rank_entropy_bits_per_token": ideal_rank_entropy_bits(ranks),
        "ac_under_draft_bits_per_token": float(-log2q.mean()),
        "raw_bits_per_token": float(np.log2(V)),
        **{k.replace("_bytes", "_bits_per_token"): (8 * v / n if v is not None else None) for k, v in cc.items()},
        "content_bytes_per_token": cc["utf8_bytes"] / n,
        "target_selfconsistency": self_ok,
        "near_tie_mass": {t: float((gaps < t).mean()) for t in (0.142, 0.465, 0.93)},
    }
    # by family and by position bucket
    fam = {}
    for p in draft["per_prompt"]:
        f = prompts[p["row"]].get("family", "?"); fam.setdefault(f, []).append(p["rank"])
    row["divergence_by_family"] = {f: float((np.concatenate(v) != 1).mean()) for f, v in fam.items()}
    pos = {}
    for p in draft["per_prompt"]:
        for b in range(0, len(p["rank"]), 64):
            pos.setdefault(str(b), []).append(p["rank"][b:b + 64] != 1)
    row["divergence_by_position_bucket64"] = {k: float(np.concatenate(v).mean()) for k, v in pos.items()}
    per_prompt_div = np.array([float((p["rank"] != 1).mean()) for p in draft["per_prompt"]])
    row["divergence_per_prompt_spread"] = {"p10": float(np.quantile(per_prompt_div, .1)), "p50": float(np.median(per_prompt_div)), "p90": float(np.quantile(per_prompt_div, .9))}
    zs = row.get("zstd19_bits_per_token")
    row["K2_kill_amber_loses_to_zstd"] = None if zs is None else bool(row["amber_v0_bits_per_token"] > zs)

    payload = {"_experiment": "p1_divergence", "_written_unix": int(time.time()),
               "target": json.loads((out / "generate" / "meta.json").read_text()).get("target"),
               "draft": draft["meta"]["model"], "dtype": draft["meta"].get("dtype"),
               "provenance": {"draft": draft["meta"].get("provenance")},
               "prompts_sha256": json.loads((out / "prompts.json").read_text())["sha256"],
               "row": row,
               "regime": f"{row.get('positions')} target-generated tokens (greedy, max_new per prompt) from sideband's 210-prompt set; "
                         f"draft teacher-forced replay in {draft['meta'].get('dtype')} on one 3080 Ti; headers excluded; content coders on decoded UTF-8 text"}
    RESULTS.mkdir(exist_ok=True)
    fname = f"{out.name}_divergence.json"
    (RESULTS / fname).write_text(json.dumps(payload, indent=2, sort_keys=True))
    for k in ("positions", "divergence_rate", "amber_v0_bits_per_token", "ideal_regimeA_bits_per_token",
              "ac_under_draft_bits_per_token", "zstd19_bits_per_token", "lzma_bits_per_token", "zlib9_bits_per_token",
              "raw_bits_per_token", "target_selfconsistency", "divergence_by_family", "divergence_per_prompt_spread",
              "near_tie_mass", "K2_kill_amber_loses_to_zstd"):
        print(f"{k}: {row[k]}")
    print(f"[saved] results/{fname}")


if __name__ == "__main__":
    main()
