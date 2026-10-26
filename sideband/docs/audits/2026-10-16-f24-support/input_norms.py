"""F-24 support figure 3 (FINDINGS.md F-24 (iv); lever 2 of the operator's science-lever decisions of 2026-10-16): the
per-anchor input norms of the full-free arm's blocks at the S1 primary gate cell.

F-24 says: "The dense standardized hz block dominates the input norm (per-anchor L2 about 65 against at
most about 11 for the 128-hot slots block and about 6 for TOK on S1; critic-recomputed, no committed
artifact records it)". This script is that artifact.

On the S1 PRIMARY (results/real/harvest_shadow) at the gate offset 2, over every TEST anchor (the split by
prompt_idx % 7 through HarvestData.row_split), the fplus_b arm's blocks are built through the FROZEN
classes the registered cells used — the six (a) blocks of tools/run_probes.feature_blocks (657 dims),
tools/run_fullfree.TokAnchorBlock (the top-32 ids hashed mod 2048, multi-hot), tools/run_fullfree.
HiddenZBlock (h_a clipped to the TRAIN support and z-scored with the TRAIN moments of
tools/run_fullfree.train_moments, whose sha is asserted equal to the committed fullfree_s1.json's) and
tools/run_probes.SlotsAnchorBlock (the 32-of-512 slots at each of four layers, multi-hot, 2048 dims) —
in batches of 4096, and the per-anchor L2 norm of each block is summarised (median, mean, p10, p90, max)
with the pairwise ratios of the medians.

Beside the norms, the per-anchor HOT COUNTS of the two multi-hot blocks (how many of the slots block's 2048
and the TOK block's 2048 entries are set), as descriptions: the construction maxima are 128 (32 slots at
each of four layers, fewer where the harvest stored fewer than 32 ids for a layer and padded the row with
-1; the ids never repeat within a layer, counted here) and 32 (fewer when hashed ids collide).

Pinned 2026-10-16 before the rerun, asserted by the script: the moments sha reproduces; the hz block's
median per-anchor L2 lies in [55, 75] ("about 65"); the slots block's maximum per-anchor L2 is at most
11.4 (at most sqrt(128) = 11.31 by construction: "at most about 11"); the TOK block's median lies in
[5, 7] ("about 6"; at most sqrt(32) = 5.66 by construction). The script reads the gitignored harvest
shards (docs/DATA.md) and loads the primary's hidden array (about 3.5 GB), so it refuses with a message on
a box without the shards; where it runs it always writes input_norms_out.json beside itself (LF) with
every value and each pin's verdict, and exits non-zero if any pin failed. CPU, a few minutes.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "tools"))
from sideband.probes import HarvestData, anchor_table  # noqa: E402
from run_probes import SlotsAnchorBlock, feature_blocks  # noqa: E402  (frozen; read-only use)
from run_fullfree import HiddenZBlock, TokAnchorBlock, train_moments  # noqa: E402  (frozen; read-only use)

R = REPO / "results" / "real"
OUT = Path(__file__).resolve().with_name("input_norms_out.json")
HARVEST = "harvest_shadow"
FULLFREE = "fullfree_s1.json"
OFFSET = 2
N_SLOTS = 512
BATCH = 4096
PINS = {"hz_median": (55.0, 75.0), "slots_max_at_most": 11.4, "tok_median": (5.0, 7.0)}


def _summary(norms: np.ndarray) -> dict:
    return {"median": float(np.median(norms)), "mean": float(norms.mean()), "p10": float(np.percentile(norms, 10)),
            "p90": float(np.percentile(norms, 90)), "max": float(norms.max()), "min": float(norms.min()), "n": int(norms.size)}


def main() -> int:
    hdir = R / HARVEST
    if not hdir.exists() or not any(hdir.glob("*.npz")):
        raise SystemExit(f"{hdir} holds no harvest shards on this box (docs/DATA.md) — refusing")
    data = HarvestData(str(hdir))
    split_names = data.row_split()
    hidden = data.array("hidden")
    moments = train_moments(hidden, data.lengths, split_names)
    committed = json.loads((R / FULLFREE).read_text(encoding="utf-8"))["standardization"]["moments_sha256"]
    rows, anchors = anchor_table(data.lengths, OFFSET, data.tokens.shape[1])
    te = np.nonzero(split_names[rows] == "test")[0]
    blocks = {
        "a_657": feature_blocks(data, "a", rows, anchors, n_slots=N_SLOTS),
        "tok_2048": [TokAnchorBlock(data.array("top_ids"), rows, anchors)],
        "hz_4096": [HiddenZBlock(hidden, rows, anchors, moments)],
        "slots_2048": [SlotsAnchorBlock(data.array("slots"), rows, anchors, N_SLOTS)],
    }
    dims = {k: int(sum(b.dim for b in bs)) for k, bs in blocks.items()}
    norms = {k: np.zeros(len(te), dtype=np.float64) for k in blocks}
    hot = {k: np.zeros(len(te), dtype=np.int64) for k in ("tok_2048", "slots_2048")}
    for start in range(0, len(te), BATCH):
        idx = te[start:start + BATCH]
        for k, bs in blocks.items():
            x = np.concatenate([b.batch(idx) for b in bs], axis=1).astype(np.float64)
            norms[k][start:start + len(idx)] = np.sqrt((x * x).sum(1))
            if k in hot:
                hot[k][start:start + len(idx)] = (x != 0).sum(1)
    summaries = {k: _summary(v) for k, v in norms.items()}
    hot_counts = {k: {"median": float(np.median(v)), "p10": float(np.percentile(v, 10)), "p90": float(np.percentile(v, 90)),
                      "min": int(v.min()), "max": int(v.max()), "construction_max": cmax,
                      "fraction_at_construction_max": float((v == cmax).mean())}
                  for (k, v), cmax in zip(hot.items(), (32, 128))}
    # why the slots block falls short of 128: the harvest's -1 padding, not repeated ids (counted on the same anchors)
    s = data.array("slots")[rows[te], anchors[te]]                       # (n_test, layers, 32), -1-padded
    srt = np.sort(s, axis=2)
    hot_counts["slots_2048"]["padding_entries_total"] = int((s < 0).sum())
    hot_counts["slots_2048"]["padding_entries_per_anchor_mean"] = float((s < 0).sum() / len(te))
    hot_counts["slots_2048"]["repeated_ids_within_a_layer_total"] = int(((srt[:, :, 1:] == srt[:, :, :-1]) & (srt[:, :, 1:] >= 0)).sum())
    med = {k: s["median"] for k, s in summaries.items()}
    pins = {
        "moments_sha_reproduces": {"value": moments["sha256"][:12], "pin": committed[:12], "ok": moments["sha256"] == committed},
        "hz_median": {"value": med["hz_4096"], "pin": f"in [{PINS['hz_median'][0]}, {PINS['hz_median'][1]}] (F-24: about 65)",
                      "ok": PINS["hz_median"][0] <= med["hz_4096"] <= PINS["hz_median"][1]},
        "slots_max": {"value": summaries["slots_2048"]["max"], "pin": f"<= {PINS['slots_max_at_most']} (F-24: at most about 11; sqrt(128) by construction)",
                      "ok": summaries["slots_2048"]["max"] <= PINS["slots_max_at_most"]},
        "tok_median": {"value": med["tok_2048"], "pin": f"in [{PINS['tok_median'][0]}, {PINS['tok_median'][1]}] (F-24: about 6)",
                       "ok": PINS["tok_median"][0] <= med["tok_2048"] <= PINS["tok_median"][1]},
    }
    ok = all(p["ok"] for p in pins.values())
    out = {"pinned_on": "2026-10-16, before the rerun; the pins are F-24's figures, the construction this file's",
           "pins": pins, "all_pins_hold": ok,
           "harvest": HARVEST, "space_offset": OFFSET, "arm": "fplus_b (a ++ TOK ++ hz ++ slots)", "anchors": "every TEST anchor",
           "dims": dims, "n_test_anchors": int(len(te)), "per_anchor_l2": summaries, "hot_counts": hot_counts,
           "median_ratios": {"hz_over_slots": med["hz_4096"] / med["slots_2048"], "hz_over_tok": med["hz_4096"] / med["tok_2048"],
                             "hz_over_a": med["hz_4096"] / med["a_657"]},
           "moments": {"sha256": moments["sha256"], "n_train_rows": moments["n_train_rows"], "n_train_positions": moments["n_train_positions"],
                       "sd_floor": moments["sd_floor"]},
           "numpy_version": np.__version__}
    OUT.write_bytes((json.dumps(out, indent=1) + "\n").encode("utf-8"))
    for k, p in pins.items():
        v = p["value"] if isinstance(p["value"], str) else f"{p['value']:.4f}"
        print(f"{'PASS' if p['ok'] else 'FAIL'} {k}: {v} {p['pin']}")
    print("wrote", OUT.name, "; all pins hold" if ok else "; A PIN FAILED (recorded)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
