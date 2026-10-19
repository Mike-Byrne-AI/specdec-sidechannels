#!/usr/bin/env python3
"""Post-hoc diagnostic P1: the prefix-topic control (BLUEPRINT, registered
2026-08-31 AFTER F-15 landed and BEFORE any diagnostic probe ran).

NON-CRITERION: nothing here can amend F-15's verdict. The question is what
the tap's margin IS: F-15's free baseline (a) is p_a-summaries only, but a
runtime decoder also owns the accepted-token history for free. If prefix-
derived topic features reproduce the tap's offset-2/3 margin, a software
prefix-tracker replaces the sideband (pricing deflates); if the tap still
adds over prefix+p_a features, the anticipatory reading strengthens.

Cells (pinned): {L1, L2, L3} x offsets {2, 3} x features {t, at, abt, atn}
x LINEAR x train seeds {0, 1, 2} = 72, per harvest ((atn) added by the
registered budget-dilution amendment, critic round, before any result was
read). (t) = PrefixTopicBlock (560 decoder-free dims for the committed
S1 alphabets — dim follows the LOADED alphabets; per-source dims are
recorded in the payload's feature_dims_recorded, none asserted here —
from tokens[row, :anchor] only); (at) = (a)+(t); (abt) =
(a)+(b)+(t); (atn) = (a)+(t)+ALIGNMENT-DESTROYED slots (the slot vector
of anchor (a+17) mod row-length — R2's shift trick on features: per-row
slot statistics preserved, alignment destroyed; rows shorter than 18
partially self-map, the known sliver). Readouts (pinned):
M2  = (abt)-(at)  [dims-asymmetric tap test],
M2n = (abt)-(atn) [EQUAL-DIMS tap test — dilution cancels; S1 dims per
      the F-16 erratum, S3 dims in feature_dims_recorded],
M2noise = (atn)-(at) [pure dilution estimate, descriptive],
M3 = (at)-(a), M4 = (c)-(at), descriptive (t)-(b) — those three paired
against the COMMITTED Phase-3 state-file cluster counts (same harvest/
split/anchors; trials must match or the pairing aborts).

Conclusion labels (pinned in the BLUEPRINT P1 block, DEFLATES gate per
the amendment): P1-SURVIVES iff the primary cell (L1/off2/linear M2,
primary harvest) fires all three Phase-3 conditions (conservative under
dilution); P1-DEFLATES iff all six M2 CI uppers < +0.005 AND all six M2n
CI uppers < +0.005 on the primary harvest; else MIXED.

Run (GPU box):
    python tools/run_posthoc_topic.py --out results/real/posthoc_topic_s1.json
    python tools/run_posthoc_topic.py \
        --harvest results/real/harvest_shadow_r \
        --fidelity results/real/harvest_fidelity_rider_r.json \
        --phase3-state results/real/probes_s1_replication.json.state.jsonl \
        --phase3-payload results/real/probes_s1_replication.json \
        --out results/real/posthoc_topic_s1_r.json

S3 P1-ANALOG (conditional pin in the S3 registration, owed once EXISTENCE
confirmed — F-17): same cells/readouts/labels verbatim, features from the
OLMoE alphabets. The tool is source-parametrized the same way run_probes
was (registered S3 instrument-change pattern): every new argument DEFAULTS
to the S1 path/tag/alphabet, so the default invocation is byte-identical
to the committed S1 instrument (asserted by tests); the S3 invocation
passes the same space/alphabet args the S3 grid recorded in its payload
provenance, and bind_spaces_to_harvest refuses cross-source mixups.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from sideband.provenance import redact_args  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))
from sideband.probes import (HarvestData, PrefixTopicBlock,  # noqa: E402
                             load_label_space)
from run_probes import (REAL, MATERIALITY, SlotsAnchorBlock,  # noqa: E402
                        bind_spaces_to_harvest, build_spaces, cell_id,
                        margins, normalize_clusters, parse_state, run_cell,
                        space_names, state_header)

def _sha(p: Path) -> str:
    import hashlib

    return hashlib.sha256(p.read_bytes()).hexdigest()


OFFSETS = (2, 3)  # the F-15-established horizon; off4 excluded (not established)
SEEDS = (0, 1, 2)
FEATS = ("t", "at", "abt", "atn")
SLOT_SHIFT = 17  # R2's shift, applied to the (atn) noise arm's slot anchors


def load_phase3_cells(state_path: Path, payload_path: Path,
                      npz_shas: dict[str, str]) -> list[dict]:
    """Committed Phase-3 cells, harvest-bound. The replication state file
    carries the sha header (verified directly); the original predates the
    header, so it binds through its payload's provenance shas (the payload
    and state file were committed together and the critic recomputed one
    from the other bit-exact — that recorded gate is the link)."""
    lines = state_path.read_text().splitlines()
    if not lines:
        raise SystemExit(f"empty phase-3 state file {state_path}")
    first = json.loads(lines[0])
    if isinstance(first, dict) and first.get("kind") == "state_header":
        if first.get("harvest_npz_sha256") != npz_shas:
            raise SystemExit("phase-3 state header binds a DIFFERENT harvest")
        body = lines[1:]
    else:
        payload = json.loads(payload_path.read_text())
        bound = payload.get("provenance", {}).get("harvest_npz_sha256")
        if bound != npz_shas:
            raise SystemExit("phase-3 payload provenance binds a DIFFERENT "
                             "harvest (legacy headerless state file)")
        body = lines
    return [normalize_clusters(json.loads(ln)) for ln in body if ln.strip()]


def conclusion(m2_rows: list[dict], m2n_rows: list[dict],
               primary_space: str = "L1_concept_k16",
               parent: str = "F-15") -> dict:
    """The pinned P1 labels, mechanical. Primary cell: L1/off2/linear
    (primary_space follows the source's registered tag; default = S1).
    DEFLATES gate per the registered budget-dilution amendment: BOTH the
    dims-asymmetric M2 uppers AND the equal-dims M2n uppers must sit
    below the floor — dilution alone may not produce a deflation."""
    n_cells = len(list(OFFSETS)) * 3
    primary = next((m for m in m2_rows if m["space"] == primary_space
                    and m["offset"] == 2), None)
    if primary is None or len(m2_rows) != n_cells or len(m2n_rows) != n_cells:
        return {"label": "INCOMPLETE", "n_m2": len(m2_rows), "n_m2n": len(m2n_rows)}
    fires = (primary["ci95"][0] > 0
             and all(v > 0 for v in primary["per_seed_margin"].values())
             and primary["margin"] >= MATERIALITY)
    if fires:
        label = "P1-SURVIVES"
    elif (all(m["ci95"][1] < MATERIALITY for m in m2_rows)
          and all(m["ci95"][1] < MATERIALITY for m in m2n_rows)):
        label = "P1-DEFLATES"
    else:
        label = "MIXED"
    return {"label": label, "primary": primary,
            "materiality_floor": MATERIALITY,
            "rule": "post-hoc P1, registered 2026-08-31 before any "
                    "diagnostic probe ran (DEFLATES gate amended same day, "
                    "critic round, before results); NON-CRITERION — cannot "
                    f"amend {parent}; see BLUEPRINT P1 block"}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    ap.add_argument("--harvest", default="results/real/harvest_shadow")
    ap.add_argument("--fidelity", default="results/real/harvest_fidelity_rider.json")
    ap.add_argument("--phase3-state", default="results/real/probes_s1.json.state.jsonl")
    ap.add_argument("--phase3-payload", default="results/real/probes_s1.json")
    ap.add_argument("--out", default="results/real/posthoc_topic_s1.json")
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--only", default=None, help="substring filter on cell ids (smoke)")
    # Source parametrization (registered S3 instrument-change pattern):
    # every default is the S1 path/tag/alphabet — the default invocation
    # is byte-identical to the committed S1 instrument.
    ap.add_argument("--space-tag", default="concept",
                    help="registered space-name tag (S1 'concept', S3 'olmoe')")
    ap.add_argument("--n-slots", type=int, default=512,
                    help="telemetry alphabet (S1 slots 512, S3 experts 64); "
                         "bound against the harvest meta")
    ap.add_argument("--buckets16", default=str(REAL / "buckets_k16.json"))
    ap.add_argument("--glue16", default=str(REAL / "glue_k16.json"))
    ap.add_argument("--buckets512", default=str(REAL / "buckets_k512.json"))
    ap.add_argument("--glue512", default=str(REAL / "glue_k512.json"))
    ap.add_argument("--groups", default=str(REAL / "concept_groups_v1.json"))
    ap.add_argument("--parent-finding", default="F-15",
                    help="the finding this NON-CRITERION diagnostic cannot "
                         "amend (S1 F-15, S3 F-17)")
    return ap


def main() -> None:
    args = build_parser().parse_args()

    registered_outs = {(REAL / "posthoc_topic_s1.json").resolve(),
                       (REAL / "posthoc_topic_s1_r.json").resolve(),
                       (REAL / "posthoc_topic_s3.json").resolve(),
                       (REAL / "posthoc_topic_s3_r.json").resolve()}
    if args.only and Path(args.out).resolve() in registered_outs:
        raise SystemExit("--only smoke runs may not write a registered out path")

    data = HarvestData(args.harvest)
    data.row_split()  # R3 abort-on-violation, before anything trains
    bind_spaces_to_harvest(data.ref_meta,
                           {"buckets16": args.buckets16,
                            "buckets512": args.buckets512},
                           n_slots=args.n_slots)

    fid = Path(args.fidelity)
    if not fid.exists():
        raise SystemExit("R1 harvest-fidelity rider missing (registered gate)")
    rider = json.loads(fid.read_text())
    if rider.get("verdict") != "PASS":
        raise SystemExit("R1 rider verdict is not PASS — harvest quarantined")
    if rider.get("npz_sha256_validated") != data.npz_shas:
        raise SystemExit("R1 rider validated a DIFFERENT harvest version")

    p3_cells = load_phase3_cells(Path(args.phase3_state),
                                 Path(args.phase3_payload), data.npz_shas)

    # State<->payload live cross-check (critic round: closes the residual on
    # the legacy headerless chain for free): the committed payload's (c)-(a)
    # margins must be reproducible from the state cells we just loaded.
    p3_payload = json.loads(Path(args.phase3_payload).read_text())
    re_m = margins(p3_cells, "c", expected_clusters=30)
    want = {(m["space"], m["offset"], m["capacity"]): m for m in p3_payload["margins"]}
    for m in re_m:
        w = want.get((m["space"], m["offset"], m["capacity"]))
        if w is None or abs(m["margin"] - w["margin"]) > 1e-12 \
                or max(abs(a - b) for a, b in zip(m["ci95"], w["ci95"])) > 1e-12:
            raise SystemExit("phase-3 state file does not reproduce its own "
                             f"payload margins at {m['space']} off{m['offset']} "
                             f"{m['capacity']} — wrong training run?")

    names = space_names(args.space_tag)
    spaces = build_spaces(data, tag=args.space_tag,
                          buckets16=args.buckets16, glue16=args.glue16,
                          buckets512=args.buckets512, glue512=args.glue512,
                          groups_path=args.groups)
    if names["L3"] not in spaces:
        raise SystemExit(f"{Path(args.groups).name} missing")

    map512, n512 = load_label_space(Path(args.buckets512), Path(args.glue512))
    map16, n16 = load_label_space(Path(args.buckets16), Path(args.glue16))

    def t_factory(rows: np.ndarray, anchors: np.ndarray) -> list:
        return [PrefixTopicBlock(data.tokens, rows, anchors,
                                 map512, n512, map16, n16)]

    # Dims recorded from the LOADED alphabets/arrays via the blocks' own
    # .dim (S3 registration: recorded, never asserted); instantiating the
    # slots block here also runs its id-range guard before any training.
    dims_recorded = {
        "t": t_factory(np.zeros(1, np.int64), np.zeros(1, np.int64))[0].dim,
        "slots_block": SlotsAnchorBlock(data.array("slots"), np.zeros(1, np.int64),
                                        np.zeros(1, np.int64), args.n_slots).dim,
        "n16_alphabet": n16, "n512_alphabet": n512,
    }

    def tn_factory(rows: np.ndarray, anchors: np.ndarray) -> list:
        """(atn): (t) plus ALIGNMENT-DESTROYED slots — the slot vector of
        anchor (a + SLOT_SHIFT) mod row-length. Per-row slot statistics
        preserved; anchor alignment destroyed; equal dims to (abt)."""
        shifted = (anchors + SLOT_SHIFT) % data.lengths[rows]
        return t_factory(rows, anchors) + [
            SlotsAnchorBlock(data.array("slots"), rows, shifted, args.n_slots)]

    base_of = {"t": None, "at": "a", "abt": "c", "atn": "a"}
    factory_of = {"t": t_factory, "at": t_factory, "abt": t_factory,
                  "atn": tn_factory}
    grid = [(space, off, f3, seed)
            for off in OFFSETS
            for seed in SEEDS
            for f3 in FEATS
            for space in (names["L1"], names["L2"], names["L3"])]

    state_path = Path(args.out + ".state.jsonl")
    done: dict[str, dict] = {}
    if state_path.exists():
        done = parse_state(state_path.read_text(), data.npz_shas)
        print(f"[resume] {len(done)} cells already done")
    else:
        with state_path.open("w") as f:
            f.write(json.dumps(state_header(data.npz_shas)) + "\n")

    t0 = time.time()
    cells: list[dict] = []
    for i, (space, off, f3, seed) in enumerate(grid):
        cid = cell_id(space, off, f3, "linear", seed)
        if args.only and args.only not in cid:
            continue
        if cid in done:
            cells.append(done[cid])
            continue
        res = run_cell(data, spaces, space, off, base_of[f3], "linear", seed,
                       args.device, extra_factory=factory_of[f3], feats_label=f3,
                       n_slots=args.n_slots)
        cells.append(res)
        with state_path.open("a") as f:
            f.write(json.dumps(res) + "\n")
        print(f"[{i + 1}/{len(grid)}] {cid}: test_acc={res['test_acc']:.4f} "
              f"(maj {res['majority_rate_test']:.4f}) {res['runtime_s']}s "
              f"total {time.time() - t0:.0f}s", flush=True)

    expected = None if args.only else 30
    pooled = cells + p3_cells
    m2 = margins(cells, "abt", expected_clusters=expected, base_feats="at")
    m2n = margins(cells, "abt", expected_clusters=expected, base_feats="atn")
    m2noise = margins(cells, "atn", expected_clusters=expected, base_feats="at")
    m3 = margins(pooled, "at", expected_clusters=expected, base_feats="a")
    m4 = margins(pooled, "c", expected_clusters=expected, base_feats="at")
    m_tb = margins(pooled, "t", expected_clusters=expected, base_feats="b")
    # m4/m_tb pool committed capacities too; keep LINEAR rows only (the P1 grid)
    m3 = [m for m in m3 if m["offset"] in OFFSETS and m["capacity"] == "linear"]
    m4 = [m for m in m4 if m["offset"] in OFFSETS and m["capacity"] == "linear"]
    m_tb = [m for m in m_tb if m["offset"] in OFFSETS and m["capacity"] == "linear"]

    def _git() -> str:
        import subprocess
        try:
            r = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=10)
            d = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, timeout=10)
            return (r.stdout.strip() or "unknown") + ("-dirty" if d.stdout.strip() else "")
        except Exception:
            return "unknown"

    import torch

    payload = {
        "registered": "post-hoc diagnostic P1 (BLUEPRINT, 2026-08-31); "
                      f"NON-CRITERION — cannot amend {args.parent_finding}",
        "n_cells": len(cells),
        "partial": bool(args.only),
        "cells": [{k: v for k, v in c.items() if k != "_clusters"} for c in cells],
        "m2_abt_vs_at": m2,
        "m2n_abt_vs_atn_equal_dims": m2n,
        "m2noise_atn_vs_at_dilution": m2noise,
        "m3_at_vs_a": m3,
        "m4_c_vs_at": m4,
        "descriptive_t_vs_b": m_tb,
        "conclusion": conclusion(m2, m2n, primary_space=names["L1"],
                                 parent=args.parent_finding),
        "phase3_state": str(args.phase3_state),
        "phase3_payload_margins_reproduced": True,  # load-time gate passed
        "provenance": {
            "git_commit": _git(),
            "args": redact_args(vars(args)),
            "harvest_npz_sha256": data.npz_shas,
            "label_space_sha256": {p.name: _sha(p) for p in (
                Path(args.buckets16), Path(args.glue16),
                Path(args.buckets512), Path(args.glue512),
                Path(args.groups)) if p.exists()},
            "feature_dims_recorded": dims_recorded,
            "phase3_state_sha256": _sha(Path(args.phase3_state)),
            "phase3_payload_sha256": _sha(Path(args.phase3_payload)),
            "slot_shift": SLOT_SHIFT,
            "torch_version": torch.__version__,
        },
        "runtime_s": round(time.time() - t0, 1),
    }
    Path(args.out).write_text(json.dumps(payload, indent=1))
    print(f"[posthoc-P1] conclusion: {payload['conclusion'].get('label')} -> {args.out}")


if __name__ == "__main__":
    main()
