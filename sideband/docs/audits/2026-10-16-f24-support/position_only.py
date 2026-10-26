"""F-24 support figure 2 (FINDINGS.md F-24 (iii); lever 2 of the operator's science-lever decisions of 2026-10-16): the
position-only predictor at the gate cell of both primaries.

F-24 says: "A weak free channel both twins share — the anchor's position — was measured by the critic on
both primaries and is negligible (a position-only predictor gains nothing over the floor; no committed
artifact records it)". This script is that artifact.

For each PRIMARY harvest (S1 results/real/harvest_shadow, label space L1_concept_k16; S3
results/real/harvest_moe, label space L1_olmoe_k16), at the gate offset 2: the anchors and labels exactly
as the registered cells read them (sideband.probes.anchor_table and labels_for through the committed label
space built by tools/run_probes.build_spaces with the harvest's companions from
tools/run_reader_lens.HARVEST_FILES; split by prompt_idx % 7 through HarvestData.row_split), then

  FLOOR      the constant majority predictor (the TRAIN majority class), whose TEST accuracy is the
             registered majority_rate_test; asserted equal to the committed gate-cell row's value to
             1e-12 (reproduction pin);
  POSITION   the position-only predictor: at every anchor index a, the majority TRAIN label among the
             anchors at that index (the global majority where an index has no train anchor); its TEST
             accuracy, and its gain over the floor as the Phase-3 paired estimand (one cluster per test
             prompt, successes of the two predictors on the same trials, paired_cluster_delta_ci with
             n_boot 2000, seed 0);
  BINNED     a description beside it: the same predictor over bins of eight anchor indices.

Pinned 2026-10-16 before the rerun, asserted by the script: the floor reproduces on both primaries; the
position-only predictor's gain over the floor is at most +0.002 on both primaries ("gains nothing";
negative gains pass). The script reads the gitignored harvest shards (docs/DATA.md), so it refuses with a
message on a box without them; where it runs it always writes position_only_out.json beside itself (LF)
with every value and each pin's verdict, and exits non-zero if any pin failed. CPU, under a minute.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "tools"))
from sideband.probes import HarvestData, anchor_table, labels_for  # noqa: E402
from sideband.stats import paired_cluster_delta_ci  # noqa: E402
from run_probes import build_spaces  # noqa: E402  (frozen; read-only use)
from run_reader_lens import HARVEST_FILES, SPACE_L1  # noqa: E402  (frozen; the companions table)

R = REPO / "results" / "real"
OUT = Path(__file__).resolve().with_name("position_only_out.json")
OFFSET = 2
BIN = 8
PRIMARIES = {"S1": ("harvest_shadow", "fullfree_s1.json"), "S3": ("harvest_moe", "fullfree_s3.json")}
PINS = {"floor_reproduces_to": 1e-12, "gain_over_floor_at_most": 0.002}


def _committed_floor(payload: str, space: str) -> float:
    p = json.loads((R / payload).read_text(encoding="utf-8"))
    rows = [c for c in p["cells"] if c["space"] == space and c["offset"] == OFFSET and c["capacity"] == "mlp256" and not c["shuffled"]]
    floors = {float(c["majority_rate_test"]) for c in rows}
    if len(floors) != 1:
        raise SystemExit(f"{payload}: the gate cells disagree on majority_rate_test ({sorted(floors)})")
    return floors.pop()


def _majority_by_key(keys: np.ndarray, labels: np.ndarray, n_classes: int, fallback: int) -> tuple[np.ndarray, np.ndarray]:
    """(table, seen): the majority TRAIN label per key, the fallback where a key has no train anchor."""
    table = np.full(int(keys.max()) + 1, fallback, dtype=np.int64)
    counts = np.zeros((int(keys.max()) + 1, n_classes), dtype=np.int64)
    np.add.at(counts, (keys, labels), 1)
    seen = counts.sum(1) > 0
    table[seen] = counts[seen].argmax(1)
    return table, seen


def _predict(table: np.ndarray, keys: np.ndarray, fallback: int) -> np.ndarray:
    """The table's label where the key is inside it, the fallback (the global majority) beyond it."""
    inside = keys < len(table)
    return np.where(inside, table[np.minimum(keys, len(table) - 1)], fallback)


def analyse(tag: str) -> dict:
    harvest, payload = PRIMARIES[tag]
    hf = HARVEST_FILES[harvest]
    space = SPACE_L1[hf["space_tag"]]
    hdir = R / harvest
    if not hdir.exists() or not any(hdir.glob("*.npz")):
        raise SystemExit(f"{hdir} holds no harvest shards on this box (docs/DATA.md) — refusing")
    data = HarvestData(str(hdir))
    spaces = build_spaces(data, hf["space_tag"], buckets16=R / hf["buckets16"], glue16=R / hf["glue16"],
                          buckets512=R / hf["buckets512"], glue512=R / hf["glue512"], groups_path=R / hf["groups"])
    sp = spaces[space]
    rows, anchors = anchor_table(data.lengths, OFFSET, data.tokens.shape[1])
    labels = labels_for(data.tokens, rows, anchors, OFFSET, sp["label_map"])
    split = data.row_split()[rows]
    tr, te = split == "train", split == "test"
    maj = int(np.bincount(labels[tr], minlength=sp["n_classes"]).argmax())
    y_te = labels[te]
    floor = float((y_te == maj).mean())
    committed = _committed_floor(payload, space)
    pos_table, pos_seen = _majority_by_key(anchors[tr], labels[tr], sp["n_classes"], maj)
    pred_pos = _predict(pos_table, anchors[te], maj)
    bin_table, _bin_seen = _majority_by_key(anchors[tr] // BIN, labels[tr], sp["n_classes"], maj)
    pred_bin = _predict(bin_table, anchors[te] // BIN, maj)
    prompts = data.prompt_idx[rows[te]]
    uniq = np.unique(prompts)
    hit_pos, hit_bin, hit_maj = (pred_pos == y_te), (pred_bin == y_te), (y_te == maj)
    succ = lambda hit: np.array([int(hit[prompts == p].sum()) for p in uniq])  # noqa: E731
    n = np.array([int((prompts == p).sum()) for p in uniq])
    d_pos = paired_cluster_delta_ci(succ(hit_pos), succ(hit_maj), n, n_boot=2000, seed=0)
    d_bin = paired_cluster_delta_ci(succ(hit_bin), succ(hit_maj), n, n_boot=2000, seed=0)
    return {"harvest": harvest, "space": space, "offset": OFFSET, "n_classes": int(sp["n_classes"]),
            "n_train": int(tr.sum()), "n_test": int(te.sum()), "n_test_clusters": int(len(uniq)),
            "train_majority_class": maj,
            "floor": {"majority_rate_test": floor, "committed": committed, "abs_diff": abs(floor - committed)},
            "position_only": {"test_acc": float(hit_pos.mean()), "gain_over_floor": float(hit_pos.mean() - floor),
                              "paired_delta_ci95": {"delta": d_pos[0], "lo": d_pos[1], "hi": d_pos[2]},
                              "n_positions_with_train_anchors": int(pos_seen.sum()), "table_length": int(len(pos_table)),
                              "n_positions_predicting_non_majority": int((pos_table != maj).sum())},
            "binned_by_8": {"test_acc": float(hit_bin.mean()), "gain_over_floor": float(hit_bin.mean() - floor),
                            "paired_delta_ci95": {"delta": d_bin[0], "lo": d_bin[1], "hi": d_bin[2]}}}


def main() -> int:
    results = {tag: analyse(tag) for tag in PRIMARIES}
    pins = {}
    for tag, r in results.items():
        pins[f"floor_reproduces:{tag}"] = {"value": r["floor"]["abs_diff"], "pin": f"<= {PINS['floor_reproduces_to']}",
                                           "ok": r["floor"]["abs_diff"] <= PINS["floor_reproduces_to"]}
        g = r["position_only"]["gain_over_floor"]
        pins[f"gain_over_floor:{tag}"] = {"value": g, "pin": f"<= +{PINS['gain_over_floor_at_most']} (F-24: gains nothing over the floor)",
                                          "ok": g <= PINS["gain_over_floor_at_most"]}
    ok = all(p["ok"] for p in pins.values())
    out = {"pinned_on": "2026-10-16, before the rerun; the pins are F-24's figures, the construction this file's",
           "pins": pins, "all_pins_hold": ok, "results": results, "numpy_version": np.__version__}
    OUT.write_bytes((json.dumps(out, indent=1) + "\n").encode("utf-8"))
    for k, p in pins.items():
        print(f"{'PASS' if p['ok'] else 'FAIL'} {k}: {p['value']:+.6f} {p['pin']}")
    print("wrote", OUT.name, "; all pins hold" if ok else "; A PIN FAILED (recorded)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
