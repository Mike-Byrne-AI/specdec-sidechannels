#!/usr/bin/env python3
"""OQ-17 POST-HOC TWIN-INERTNESS DIAGNOSTIC (registered 2026-09-06 in
docs/BLUEPRINT.md "OQ-17 POST-HOC TWIN-INERTNESS DIAGNOSTIC", after the S1
payloads and the S1 critic recompute were read and BEFORE any REGISTERED
twin cell ran; one scratch smoke cell is disclosed in the block;
NON-CRITERION: it cannot change a registered per-source label — it pins
which qualifier the pinned consequence text carries).

WHY. The registered equal-dims twin fplus_n reads the slot vector of anchor
(a + SLOT_SHIFT) mod row-length of the SAME row. For every anchor whose row
extends that far, that position's forward pass has already consumed the
label token (the offset-2 label is the token at a + 1, label_index =
anchor + offset - 1), so the "alignment-destroyed" block can carry label
information through a channel F-16 named only as one that "could only make
M2n an UNDERestimate" — under a null label that bias runs TOWARD the null.
The S1 critic recompute (2026-09-06) found the twin is not inert: Mn =
acc(fplus_n) - acc(fplus) is CI-clear positive at the primary gate cell,
and the ABSORBED-vs-NOT-SHOWN call on the replication harvest rides on D
specifically (its Mt CI95 upper sits above the +0.005 floor).

ARM. fplus_r = fplus ++ the slot vector of the SAME-GENERATION-INDEX ROW OF
A DIFFERENT PROMPT of the same split at the same anchor index (anchor mod
that row's length): per-position slot statistics preserved; prompt
identity, row identity and the future-context channel destroyed (a
row-level derangement was the first draft; the pre-run critic showed it
reads a sibling generation of the same prompt for 3-6% of test anchors,
which look like aligned telemetry — replaced before any registered cell).
The other prompt is pi_seed(prompt), a within-split derangement of PROMPT
ids (no fixed points; train / val / test preserved; every prompt carries
the same number of rows, asserted) drawn from numpy
default_rng(TWIN_SEED_BASE + train seed); row k of prompt p maps to row k
of pi_seed(p). Equal dims to fplus_b by construction (refused otherwise).
Block order TOK, hz, slots — as fplus_b; TOK and hz are byte-identical to
fplus's (the hz moments sha must equal the registered payload's).
CELLS per harvest: the gate cell only — L1 / off2 / mlp256 x train seeds
{0,1,2} x fplus_r = 3 cells. The committed fplus / fplus_b / fplus_n cells
are reused from the registered fullfree state file (sha-header bound to the
harvest; the registered payload's D / Mt / Mn gate rows must reproduce from
them at 1e-12 and the hz moments sha must match, or the run refuses).
READOUTS (paired cluster bootstrap, the registered estimand):
  D_r  = acc(fplus_b) - acc(fplus_r)   the aligned margin at the corrected twin
  Mn_r = acc(fplus_r) - acc(fplus)     the corrected twin's own effect
  T    = acc(fplus_n) - acc(fplus_r)   what the registered twin carried beyond
                                       a prompt-independent slot block
  By the paired-trials identity D_r = Mt - Mn_r at the point, so D_r can
  clear the +0.005 floor through the corrected twin's own COST; a fire
  counts as CLEAN only when Mn_r's CI95 upper >= 0 on that harvest.
PINNED READING per source from both harvests (--conclude-from):
  TWIN-ROBUST     D_r CI95 upper < +0.005 on both harvests (rows carrying
                  n_seeds 3, n_clusters 30, the fplus_b-fplus_r pairing) —
                  the registered null does not depend on the shift twin
  TWIN-MASKED     D_r fires the Phase-3 triple rule CLEANLY on both
                  harvests — the registered twin masked a material margin
  TWIN-SPLIT      D_r fires cleanly on exactly one harvest
  TWIN-DEPENDENT  otherwise — the null is NOT SHOWN at the corrected twin
                  (a fire through a CI-clear-harmful corrected twin lands
                  here, written with the dilution wording)
  TWIN-INCOMPLETE a row is missing or structurally short
  plus T: TWIN-INFORMATIVE iff T CI95 lower > 0 on both harvests, else
  TWIN-INFORMATION-NOT-SHOWN (descriptive; T does not separate the
  future-context channel from same-row content redundancy).

Run (GPU box), after the registered fullfree payload of the harvest exists:
    python tools/run_fullfree_twin.py --out results/real/fullfree_s1_twin.json
    python tools/run_fullfree_twin.py --harvest results/real/harvest_shadow_r \
        --fidelity results/real/harvest_fidelity_rider_r.json \
        --fullfree-payload results/real/fullfree_s1_r.json \
        --out results/real/fullfree_s1_r_twin.json
    (S3: --space-tag olmoe --n-slots 64 and the olmoe buckets / glue /
     groups / rider paths, --fullfree-payload results/real/fullfree_s3{,_r}.json)
    python tools/run_fullfree_twin.py --conclude-from \
        results/real/fullfree_s1_twin.json results/real/fullfree_s1_r_twin.json
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
from sideband.provenance import redact_args  # noqa: E402
from sideband.recon import FREETOK_BINS  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))
from sideband.probes import HarvestData, anchor_table  # noqa: E402
from run_posthoc_topic import SLOT_SHIFT  # noqa: E402
from run_probes import (REAL, MATERIALITY, SlotsAnchorBlock,  # noqa: E402
                        bind_spaces_to_harvest, build_spaces, cell_id,
                        feature_blocks, margins, normalize_clusters,
                        parse_state, run_cell, space_names, state_header)
from run_fullfree import (GATE_CAPACITY, GATE_OFFSET, SEEDS, HARVESTS_OF_SPACE,  # noqa: E402
                          HiddenZBlock, TokAnchorBlock, _same_path, gate_row,
                          train_moments)

ARM = "fplus_r"
TWIN_SEED_BASE = 1000
PAIR_DR = f"fplus_b-{ARM}"
PAIR_MNR = f"{ARM}-fplus"
PAIR_T = f"fplus_n-{ARM}"
REGISTERED_OUTS = ("fullfree_s1_twin.json", "fullfree_s1_r_twin.json",
                   "fullfree_s3_twin.json", "fullfree_s3_r_twin.json")
FULLFREE_OF_OUT = {"fullfree_s1_twin.json": "fullfree_s1.json",
                   "fullfree_s1_r_twin.json": "fullfree_s1_r.json",
                   "fullfree_s3_twin.json": "fullfree_s3.json",
                   "fullfree_s3_r_twin.json": "fullfree_s3_r.json"}
BRANCH_ROBUST = "TWIN-ROBUST"
BRANCH_MASKED = "TWIN-MASKED"
BRANCH_SPLIT = "TWIN-SPLIT"
BRANCH_DEPENDENT = "TWIN-DEPENDENT"
BRANCH_INCOMPLETE = "TWIN-INCOMPLETE"
T_INFORMATIVE = "TWIN-INFORMATIVE"
T_NOT_SHOWN = "TWIN-INFORMATION-NOT-SHOWN"
CONSTRUCTION = ("slots of row k of pi_seed(prompt) at anchor mod that row's length, where row k is "
                "the row's generation index within its prompt and pi_seed is a within-split "
                "derangement of PROMPT ids from default_rng(seed_base + train seed)")


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
# The corrected twin
# ---------------------------------------------------------------------------

def derangement_by_prompt(prompt_idx: np.ndarray, split_names: np.ndarray, seed: int,
                          seed_base: int = TWIN_SEED_BASE) -> np.ndarray:
    """Row -> row k of a DIFFERENT PROMPT of the SAME split, k being the
    row's generation index within its prompt (rows of a prompt in row
    order). One random cyclic order of the prompt ids per split, so no
    prompt maps to itself; seeded by the train seed."""
    prompt_idx = np.asarray(prompt_idx, dtype=np.int64)
    split_names = np.asarray(split_names)
    if len(prompt_idx) != len(split_names):
        raise SystemExit("prompt_idx / split length mismatch")
    rng = np.random.default_rng(seed_base + int(seed))
    rows_of = {int(p): np.nonzero(prompt_idx == p)[0] for p in np.unique(prompt_idx)}
    if len({len(v) for v in rows_of.values()}) != 1:
        raise SystemExit("prompts carry unequal row counts — the same-generation-index map is undefined")
    for p, rows in rows_of.items():
        if len(set(split_names[rows].tolist())) != 1:
            raise SystemExit(f"prompt {p} spans splits — refusing")
    perm = np.full(len(prompt_idx), -1, np.int64)
    for name in sorted(set(split_names.tolist())):
        prompts = np.array(sorted({int(p) for p in prompt_idx[split_names == name]}), dtype=np.int64)
        if len(prompts) < 2:
            raise SystemExit(f"split {name!r} has {len(prompts)} prompt(s): no derangement exists")
        order = rng.permutation(prompts)
        for p, q in zip(order, np.roll(order, -1)):
            perm[rows_of[int(p)]] = rows_of[int(q)]
    if np.any(perm < 0) or sorted(perm.tolist()) != list(range(len(perm))):
        raise SystemExit("derangement is not a permutation — refusing")
    if np.any(perm == np.arange(len(perm))):
        raise SystemExit("derangement has a fixed point — refusing")
    if np.any(prompt_idx[perm] == prompt_idx):
        raise SystemExit("derangement maps a row to its own prompt — refusing")
    if not np.array_equal(split_names[perm], split_names):
        raise SystemExit("derangement crosses splits — refusing")
    return perm


class OtherRowSlotsBlock:
    """The slot vector of pi(row) at anchor mod length[pi(row)] — the same
    class the registered arms read slots through, at prompt-independent
    coordinates."""

    def __init__(self, slots: np.ndarray, rows: np.ndarray, anchors: np.ndarray,
                 lengths: np.ndarray, perm: np.ndarray, n_slots: int):
        other = perm[rows]
        self.other_anchors = anchors % lengths[other]
        self.wrapped = int(np.sum(self.other_anchors != anchors))
        self.inner = SlotsAnchorBlock(slots, other, self.other_anchors, n_slots)

    @property
    def dim(self) -> int:
        return self.inner.dim

    def batch(self, idx: np.ndarray) -> np.ndarray:
        return self.inner.batch(idx)


def make_twin_factory(top_ids: np.ndarray, hidden: np.ndarray, slots: np.ndarray,
                      lengths: np.ndarray, n_slots: int, moments: dict, perm: np.ndarray,
                      n_bins: int = FREETOK_BINS):
    """fplus_r's EXTRA blocks (appended after the registered (a) blocks by
    run_cell): TOK, hz, then the corrected-twin slots block last — the
    registered fplus_b / fplus_n order."""

    def fplus_r(rows, anchors):
        return [TokAnchorBlock(top_ids, rows, anchors, n_bins),
                HiddenZBlock(hidden, rows, anchors, moments),
                OtherRowSlotsBlock(slots, rows, anchors, lengths, perm, n_slots)]

    return fplus_r


def twin_geometry(lengths: np.ndarray, perm: np.ndarray, offset: int, T: int,
                  prompt_idx: np.ndarray | None = None) -> dict:
    """Descriptive, over the offset's anchor table: how many corrected-twin
    reads wrap (anchor >= the other row's length), how many registered
    shift-twin reads land beyond the label position (a + SLOT_SHIFT < row
    length: a real future position of the same row), and — when prompt_idx
    is given — how many corrected-twin reads land on the same prompt
    (must be zero under the prompt-level derangement)."""
    rows, anchors = anchor_table(lengths, offset, T)
    other = perm[rows]
    wrapped = anchors >= lengths[other]
    future = (anchors + SLOT_SHIFT) < lengths[rows]
    out = {"n_anchors": int(len(rows)),
           "corrected_twin_wrapped_frac": float(wrapped.mean()),
           "shift_twin_future_frac": float(future.mean()),
           "shift": int(SLOT_SHIFT)}
    if prompt_idx is not None:
        out["corrected_twin_same_prompt_frac"] = float(np.mean(prompt_idx[other] == prompt_idx[rows]))
    return out


# ---------------------------------------------------------------------------
# Committed fullfree cells, reproduction gate, readouts
# ---------------------------------------------------------------------------

def load_fullfree_cells(state_path: Path, npz_shas: dict[str, str]) -> list[dict]:
    """The registered fullfree state file's cells, harvest-bound through its
    sha header (every registered fullfree state file carries one)."""
    lines = state_path.read_text().splitlines()
    if not lines:
        raise SystemExit(f"empty fullfree state file {state_path}")
    first = json.loads(lines[0])
    if not (isinstance(first, dict) and first.get("kind") == "state_header"):
        raise SystemExit("fullfree state file lacks the harvest-binding header")
    if first.get("harvest_npz_sha256") != npz_shas:
        raise SystemExit("fullfree state header binds a DIFFERENT harvest")
    return [normalize_clusters(json.loads(ln)) for ln in lines[1:] if ln.strip()]


def reproduce_gate_rows(cells: list[dict], payload: dict, space: str,
                        tol: float = 1e-12) -> dict:
    """The registered payload's gate-cell D / Mt / Mn rows must reproduce
    from the state-file cells before anything trains."""
    got = {"D": gate_row(margins(cells, "fplus_b", expected_clusters=30, base_feats="fplus_n"), space),
           "Mt": gate_row(margins(cells, "fplus_b", expected_clusters=30, base_feats="fplus"), space),
           "Mn": gate_row(margins(cells, "fplus_n", expected_clusters=30, base_feats="fplus"), space)}
    want = {"D": gate_row(payload["d_fplus_b_vs_fplus_n"], space),
            "Mt": gate_row(payload["mt_fplus_b_vs_fplus"], space),
            "Mn": gate_row(payload["mn_fplus_n_vs_fplus_dilution"], space)}
    for k in ("D", "Mt", "Mn"):
        g, w = got[k], want[k]
        if g is None or w is None:
            raise SystemExit(f"registered fullfree payload / state file lack the {k} gate row")
        if abs(g["margin"] - w["margin"]) > tol or \
                max(abs(a - b) for a, b in zip(g["ci95"], w["ci95"])) > tol:
            raise SystemExit(f"fullfree state file does not reproduce its payload's {k} gate row")
    return got


def per_cluster_corr(cells: list[dict], space: str, top_a: str, top_b: str, base: str = "fplus",
                     offset: int = GATE_OFFSET, capacity: str = GATE_CAPACITY) -> dict | None:
    """Descriptive: Pearson correlation over the 30 test clusters between the
    seed-summed per-cluster accuracy deltas (top_a - base) and (top_b -
    base) at the gate cell — 'the twin gains where the aligned block
    gains' as a recorded number rather than a recollected one."""
    cells = [normalize_clusters(dict(c)) for c in cells]
    by_id = {c["cell"]: c for c in cells if not c["shuffled"]}
    trip = {}
    for seed in SEEDS:
        ids = [cell_id(space, offset, f, capacity, seed) for f in (top_a, top_b, base)]
        if not all(i in by_id for i in ids):
            return None
        trip[seed] = [by_id[i] for i in ids]
    prompts = sorted(set.intersection(*(set(c["_clusters"]) for cs in trip.values() for c in cs)))
    da = np.zeros(len(prompts))
    db = np.zeros(len(prompts))
    n = np.zeros(len(prompts))
    for seed, (ca, cb, cbase) in trip.items():
        for j, p in enumerate(prompts):
            da[j] += ca["_clusters"][p][0] - cbase["_clusters"][p][0]
            db[j] += cb["_clusters"][p][0] - cbase["_clusters"][p][0]
            n[j] += cbase["_clusters"][p][1]
    da, db = da / n, db / n
    if da.std() == 0 or db.std() == 0:
        return {"pearson": None, "n_clusters": len(prompts)}
    return {"pearson": float(np.corrcoef(da, db)[0, 1]), "n_clusters": len(prompts),
            "pairs": [f"{top_a}-{base}", f"{top_b}-{base}"]}


def _structural(row: dict | None, pair: str) -> bool:
    return (row is not None and row.get("pair") == pair
            and row.get("n_seeds") == len(SEEDS) and row.get("n_clusters") == 30)


def fires(row: dict | None, pair: str = PAIR_DR) -> bool:
    """The Phase-3 triple rule on one D_r row, with the structural guards."""
    if not _structural(row, pair):
        return False
    return bool(row["ci95"][0] > 0
                and all(v > 0 for v in row["per_seed_margin"].values())
                and row["margin"] >= MATERIALITY)


def fires_clean(dr: dict | None, mnr: dict | None) -> bool:
    """A fire counts only when the corrected twin is not CI-clear harmful on
    that harvest (D_r = Mt - Mn_r at the point: a fire bought by the twin's
    own cost is dilution, never a masked margin)."""
    return bool(fires(dr) and _structural(mnr, PAIR_MNR) and mnr["ci95"][1] >= 0)


def twin_branch(dr_primary: dict | None, dr_replication: dict | None,
                mnr_primary: dict | None = None, mnr_replication: dict | None = None) -> str:
    if not (_structural(dr_primary, PAIR_DR) and _structural(dr_replication, PAIR_DR)):
        return BRANCH_INCOMPLETE
    fp = fires_clean(dr_primary, mnr_primary)
    fr = fires_clean(dr_replication, mnr_replication)
    if fp and fr:
        return BRANCH_MASKED
    if fp != fr:
        return BRANCH_SPLIT
    if dr_primary["ci95"][1] < MATERIALITY and dr_replication["ci95"][1] < MATERIALITY:
        return BRANCH_ROBUST
    return BRANCH_DEPENDENT


def t_reading(t_primary: dict | None, t_replication: dict | None) -> str | None:
    if not (_structural(t_primary, PAIR_T) and _structural(t_replication, PAIR_T)):
        return None
    return T_INFORMATIVE if (t_primary["ci95"][0] > 0 and t_replication["ci95"][0] > 0) else T_NOT_SHOWN


def _check_payload(p: dict, role: str, verify_files: bool = True) -> str:
    sp = p["space"]
    if p.get("partial"):
        raise SystemExit(f"{role} twin payload is PARTIAL (--only run) — no reading may issue")
    if sp not in HARVESTS_OF_SPACE:
        raise SystemExit(f"{role} twin payload's space {sp!r} is not a registered source")
    want = HARVESTS_OF_SPACE[sp][0 if role == "primary" else 1]
    if not _same_path(str(p.get("harvest", "")), want):
        raise SystemExit(f"{role} twin payload's harvest {p.get('harvest')!r} is not the registered "
                         f"{role} harvest {want!r}")
    args = (p.get("provenance") or {}).get("args") or {}
    out_name = Path(str(args.get("out", ""))).name
    tag = "s1" if sp == "L1_concept_k16" else "s3"
    want_out = f"fullfree_{tag}{'' if role == 'primary' else '_r'}_twin.json"
    if out_name != want_out:
        raise SystemExit(f"{role} twin payload was written to {out_name!r}, not the registered "
                         f"{want_out!r} — scratch, no reading may issue")
    if not p.get("reproduced_registered_gate_rows"):
        raise SystemExit(f"{role} twin payload did not reproduce the registered gate rows")
    if p.get("n_cells") != len(SEEDS):
        raise SystemExit(f"{role} twin payload carries {p.get('n_cells')} cells, expected {len(SEEDS)}")
    twin = p.get("twin") or {}
    if twin.get("arm") != ARM or twin.get("seed_base") != TWIN_SEED_BASE:
        raise SystemExit(f"{role} twin payload's twin construction is not the registered one")
    if Path(str(args.get("fullfree_payload", ""))).name != FULLFREE_OF_OUT[want_out]:
        raise SystemExit(f"{role} twin payload pairs with {args.get('fullfree_payload')!r}, not the "
                         f"registered {FULLFREE_OF_OUT[want_out]!r}")
    if verify_files:
        prov = p["provenance"]
        ffp = Path(str(args["fullfree_payload"]))
        ffs = Path(str(args["fullfree_payload"]) + ".state.jsonl")
        if not (ffp.exists() and ffs.exists()):
            raise SystemExit(f"{role} twin payload's paired fullfree payload / state file are missing")
        if _sha(ffp) != prov.get("fullfree_payload_sha256") or _sha(ffs) != prov.get("fullfree_state_sha256"):
            raise SystemExit(f"{role} twin payload's paired fullfree payload / state file changed on disk "
                             "since the twin run — refusing")
    return sp


def conclude(primary: dict, replication: dict, verify_files: bool = True) -> dict:
    sp = _check_payload(primary, "primary", verify_files)
    if _check_payload(replication, "replication", verify_files) != sp:
        raise SystemExit("the two twin payloads are from different sources")
    if primary["provenance"]["harvest_npz_sha256"] == replication["provenance"]["harvest_npz_sha256"]:
        raise SystemExit("the two twin payloads bind the SAME harvest")
    dr = (gate_row(primary["d_r_fplus_b_vs_fplus_r"], sp), gate_row(replication["d_r_fplus_b_vs_fplus_r"], sp))
    mnr = (gate_row(primary["mn_r_fplus_r_vs_fplus"], sp), gate_row(replication["mn_r_fplus_r_vs_fplus"], sp))
    t = (gate_row(primary["t_fplus_n_vs_fplus_r"], sp), gate_row(replication["t_fplus_n_vs_fplus_r"], sp))
    return {
        "space": sp,
        "branch": twin_branch(dr[0], dr[1], mnr[0], mnr[1]),
        "t_reading": t_reading(*t),
        "d_r": {"primary": dr[0], "replication": dr[1]},
        "d_r_fires_raw": {"primary": fires(dr[0]), "replication": fires(dr[1])},
        "d_r_fires_clean": {"primary": fires_clean(dr[0], mnr[0]),
                            "replication": fires_clean(dr[1], mnr[1])},
        "corrected_twin_ci_clear_harmful": {
            "primary": bool(mnr[0] is not None and mnr[0]["ci95"][1] < 0),
            "replication": bool(mnr[1] is not None and mnr[1]["ci95"][1] < 0)},
        "corrected_twin_ci_clear_helpful": {
            "primary": bool(mnr[0] is not None and mnr[0]["ci95"][0] > 0),
            "replication": bool(mnr[1] is not None and mnr[1]["ci95"][0] > 0)},
        "deciding_upper_minus_floor": {
            "primary": (None if dr[0] is None else dr[0]["ci95"][1] - MATERIALITY),
            "replication": (None if dr[1] is None else dr[1]["ci95"][1] - MATERIALITY)},
        "mn_r": {"primary": mnr[0], "replication": mnr[1]},
        "t": {"primary": t[0], "replication": t[1]},
        "registered_d": {"primary": primary["registered_gate_rows"]["D"],
                         "replication": replication["registered_gate_rows"]["D"]},
        "registered_mt": {"primary": primary["registered_gate_rows"]["Mt"],
                          "replication": replication["registered_gate_rows"]["Mt"]},
        "registered_mn": {"primary": primary["registered_gate_rows"]["Mn"],
                          "replication": replication["registered_gate_rows"]["Mn"]},
        "per_cluster_corr": {"primary": primary.get("per_cluster_corr"),
                             "replication": replication.get("per_cluster_corr")},
        "materiality_floor": MATERIALITY,
        "rule": ("OQ-17 POST-HOC TWIN-INERTNESS DIAGNOSTIC (docs/BLUEPRINT.md, 2026-09-06, "
                 "registered before any registered twin cell ran; NON-CRITERION): TWIN-ROBUST iff "
                 "D_r CI95 upper < +0.005 on both harvests; TWIN-MASKED iff D_r fires the triple "
                 "rule CLEANLY (Mn_r CI95 upper >= 0) on both; TWIN-SPLIT iff cleanly on one; else "
                 "TWIN-DEPENDENT; T informative iff CI95 lower > 0 on both"),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    ap.add_argument("--harvest", default="results/real/harvest_shadow")
    ap.add_argument("--fidelity", default="results/real/harvest_fidelity_rider.json")
    ap.add_argument("--fullfree-payload", default="results/real/fullfree_s1.json",
                    help="the registered fullfree payload of this harvest; its .state.jsonl "
                         "supplies the committed fplus / fplus_b / fplus_n cells")
    ap.add_argument("--out", default="results/real/fullfree_s1_twin.json")
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--only", default=None, help="substring filter on cell ids (smoke)")
    ap.add_argument("--resume", action="store_true",
                    help="continue a crashed registered run from its state file (FRESH-STATE PIN "
                         "otherwise refuses an existing registered state file)")
    ap.add_argument("--space-tag", default="concept")
    ap.add_argument("--n-slots", type=int, default=512)
    ap.add_argument("--buckets16", default=str(REAL / "buckets_k16.json"))
    ap.add_argument("--glue16", default=str(REAL / "glue_k16.json"))
    ap.add_argument("--buckets512", default=str(REAL / "buckets_k512.json"))
    ap.add_argument("--glue512", default=str(REAL / "glue_k512.json"))
    ap.add_argument("--groups", default=str(REAL / "concept_groups_v1.json"))
    ap.add_argument("--conclude-from", nargs=2, metavar=("PRIMARY", "REPLICATION"),
                    default=None, help="print the per-source twin reading from two payloads")
    return ap


def main() -> None:
    args = build_parser().parse_args()

    if args.conclude_from:
        pp = json.loads(Path(args.conclude_from[0]).read_text())
        rp = json.loads(Path(args.conclude_from[1]).read_text())
        print(json.dumps(conclude(pp, rp), indent=1))
        return

    registered_outs = {(REAL / n).resolve() for n in REGISTERED_OUTS}
    out_path = Path(args.out).resolve()
    registered = out_path in registered_outs
    if args.only and registered:
        raise SystemExit("--only smoke runs may not write a registered out path")
    if registered:
        want_ff = (REAL / FULLFREE_OF_OUT[out_path.name]).resolve()
        if Path(args.fullfree_payload).resolve() != want_ff:
            raise SystemExit(f"registered out {out_path.name} must pair with {want_ff}, "
                             f"not {Path(args.fullfree_payload).resolve()}")
    state_path = Path(args.out + ".state.jsonl")
    if registered and state_path.exists() and not args.resume:
        raise SystemExit(f"FRESH-STATE PIN: {state_path} exists; pass --resume only to continue a "
                         "crashed registered run")

    data = HarvestData(args.harvest)
    split_names = data.row_split()  # R3 abort-on-violation, before anything trains
    bind_spaces_to_harvest(data.ref_meta,
                           {"buckets16": args.buckets16, "buckets512": args.buckets512},
                           n_slots=args.n_slots)

    fid = Path(args.fidelity)
    if not fid.exists():
        raise SystemExit("R1 harvest-fidelity rider missing (registered gate)")
    rider_payload = json.loads(fid.read_text())
    if rider_payload.get("verdict") != "PASS":
        raise SystemExit("R1 rider verdict is not PASS — harvest quarantined")
    if rider_payload.get("npz_sha256_validated") != data.npz_shas:
        raise SystemExit("R1 rider validated a DIFFERENT harvest version")

    ff_payload_path = Path(args.fullfree_payload)
    ff_state_path = Path(args.fullfree_payload + ".state.jsonl")
    ff_payload = json.loads(ff_payload_path.read_text())
    if ff_payload.get("partial"):
        raise SystemExit("the fullfree payload is PARTIAL — not a registered run")
    if not _same_path(str(ff_payload.get("harvest", "")), args.harvest):
        raise SystemExit("the fullfree payload was run on a DIFFERENT harvest path")
    if ff_payload["provenance"]["harvest_npz_sha256"] != data.npz_shas:
        raise SystemExit("the fullfree payload binds a DIFFERENT harvest")
    ff_cells = load_fullfree_cells(ff_state_path, data.npz_shas)

    names = space_names(args.space_tag)
    spaces = build_spaces(data, tag=args.space_tag,
                          buckets16=args.buckets16, glue16=args.glue16,
                          buckets512=args.buckets512, glue512=args.glue512,
                          groups_path=args.groups)
    space = names["L1"]
    if space not in spaces:
        raise SystemExit(f"label space {space} not built")
    if ff_payload["gate"]["space"] != space:
        raise SystemExit("the fullfree payload's space differs from this run's")
    registered_rows = reproduce_gate_rows(ff_cells, ff_payload, space)
    corr_mt_mn = per_cluster_corr(ff_cells, space, "fplus_b", "fplus_n")

    hidden = data.array("hidden")
    top_ids = data.array("top_ids")
    slots = data.array("slots")
    moments = train_moments(hidden, data.lengths, split_names)
    if moments["sha256"] != ff_payload["standardization"]["moments_sha256"]:
        raise SystemExit("hz moments sha differs from the registered fullfree payload's — "
                         "the corrected twin would not share fplus's blocks")
    print(f"[moments] sha {moments['sha256'][:12]} == registered", flush=True)

    perms = {seed: derangement_by_prompt(data.prompt_idx, split_names, seed) for seed in SEEDS}
    factory_of_seed = {seed: make_twin_factory(top_ids, hidden, slots, data.lengths,
                                               args.n_slots, moments, perms[seed])
                       for seed in SEEDS}
    probe_rows = np.zeros(1, np.int64)
    a_dim = sum(b.dim for b in feature_blocks(data, "a", probe_rows, probe_rows, n_slots=args.n_slots))
    dims_r = [b.dim for b in factory_of_seed[SEEDS[0]](probe_rows, probe_rows)]
    total_r = int(a_dim + sum(dims_r))
    if total_r != ff_payload["provenance"]["arm_dims_total"]["fplus_b"]:
        raise SystemExit(f"fplus_r dims {total_r} != registered fplus_b dims "
                         f"{ff_payload['provenance']['arm_dims_total']['fplus_b']} — refusing")
    geometry = {str(seed): twin_geometry(data.lengths, perms[seed], GATE_OFFSET,
                                         data.tokens.shape[1], data.prompt_idx)
                for seed in SEEDS}
    if any(g["corrected_twin_same_prompt_frac"] != 0.0 for g in geometry.values()):
        raise SystemExit("corrected twin reads its own prompt somewhere — refusing")
    perm_shas = {str(seed): hashlib.sha256(perms[seed].astype(np.int64).tobytes()).hexdigest()
                 for seed in SEEDS}

    grid = [(space, GATE_OFFSET, ARM, GATE_CAPACITY, seed, False) for seed in SEEDS]
    done: dict[str, dict] = {}
    if state_path.exists():
        done = parse_state(state_path.read_text(), data.npz_shas)
        print(f"[resume] {len(done)} cells already done")
    else:
        with state_path.open("w") as f:
            f.write(json.dumps(state_header(data.npz_shas)) + "\n")

    t0 = time.time()
    cells: list[dict] = []
    for i, (sp, off, arm, cap, seed, shuffled) in enumerate(grid):
        cid = cell_id(sp, off, arm, cap, seed, shuffled)
        if args.only and args.only not in cid:
            continue
        if cid in done:
            res = done[cid]
        else:
            res = run_cell(data, spaces, sp, off, "a", cap, seed, args.device,
                           shuffled=shuffled, extra_factory=factory_of_seed[seed],
                           feats_label=arm, n_slots=args.n_slots)
            with state_path.open("a") as f:
                f.write(json.dumps(res) + "\n")
        cells.append(res)
        print(f"[{i + 1}/{len(grid)}] {cid}: test_acc={res['test_acc']:.4f} "
              f"(maj {res['majority_rate_test']:.4f}) {res['runtime_s']}s "
              f"total {time.time() - t0:.0f}s", flush=True)

    expected = None if args.only else 30
    pooled = cells + ff_cells
    d_r = margins(pooled, "fplus_b", expected_clusters=expected, base_feats=ARM)
    mn_r = margins(pooled, ARM, expected_clusters=expected, base_feats="fplus")
    t_rows = margins(pooled, "fplus_n", expected_clusters=expected, base_feats=ARM)
    corr_mt_mnr = per_cluster_corr(pooled, space, "fplus_b", ARM) if not args.only else None

    def _git() -> tuple[str, list[str]]:
        import subprocess
        try:
            r = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=10)
            d = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"],
                               capture_output=True, text=True, timeout=10)
            lines = [ln for ln in d.stdout.splitlines() if ln.strip()]
            return (r.stdout.strip() or "unknown") + ("-dirty" if lines else ""), lines
        except Exception:
            return "unknown", []

    git_commit, git_porcelain = _git()
    import torch

    dr_gate = gate_row(d_r, space)
    mnr_gate = gate_row(mn_r, space)
    payload = {
        "registered": ("OQ-17 POST-HOC TWIN-INERTNESS DIAGNOSTIC (docs/BLUEPRINT.md, 2026-09-06, "
                       "registered before any registered twin cell ran; NON-CRITERION)"),
        "space": space,
        "harvest": args.harvest,
        "n_cells": len(cells),
        "partial": bool(args.only),
        "resumed_cells": int(sum(1 for c in cells if c["cell"] in done)),
        "cells": [{k: v for k, v in c.items() if k != "_clusters"} for c in cells],
        "committed_cells_used": sorted(c["cell"] for c in ff_cells if not c["shuffled"]
                                       and c["offset"] == GATE_OFFSET and c["capacity"] == GATE_CAPACITY),
        "reproduced_registered_gate_rows": True,
        "registered_gate_rows": registered_rows,
        "d_r_fplus_b_vs_fplus_r": d_r,
        "mn_r_fplus_r_vs_fplus": mn_r,
        "t_fplus_n_vs_fplus_r": t_rows,
        "gate": {"space": space, "offset": GATE_OFFSET, "capacity": GATE_CAPACITY,
                 "d_r_row": dr_gate, "d_r_fires_raw": fires(dr_gate),
                 "d_r_fires_clean": fires_clean(dr_gate, mnr_gate)},
        "per_cluster_corr": {"mt_vs_mn": corr_mt_mn, "mt_vs_mn_r": corr_mt_mnr},
        "twin": {"arm": ARM, "seed_base": TWIN_SEED_BASE, "construction": CONSTRUCTION,
                 "perm_sha256": perm_shas, "geometry_at_gate_offset": geometry},
        "standardization": {"moments_sha256": moments["sha256"],
                            "matches_registered": True},
        "provenance": {
            "git_commit": git_commit,
            "git_status_tracked": git_porcelain,
            "instrument_sha256": _sha(Path(__file__)),
            "args": redact_args(vars(args)),
            "harvest_npz_sha256": data.npz_shas,
            "fullfree_payload_sha256": _sha(ff_payload_path),
            "fullfree_state_sha256": _sha(ff_state_path),
            "fullfree_git_commit": ff_payload["provenance"]["git_commit"],
            "arm_dims_total": {ARM: total_r, "fplus_b": ff_payload["provenance"]["arm_dims_total"]["fplus_b"]},
            "feature_dims_recorded": {ARM: dims_r},
            "torch_version": torch.__version__,
            "device": args.device,
            "determinism_note": ("CUDA probe training uses atomics; per-cell results are "
                                 "evidenced by the recorded state file, not rerun-exactness"),
        },
        "runtime_s": round(time.time() - t0, 1),
    }
    Path(args.out).write_text(json.dumps(payload, indent=1))
    print(json.dumps({"d_r": dr_gate, "mn_r": mnr_gate, "t": gate_row(t_rows, space),
                      "d_r_fires_raw": payload["gate"]["d_r_fires_raw"],
                      "d_r_fires_clean": payload["gate"]["d_r_fires_clean"]}, indent=1))


if __name__ == "__main__":
    main()
