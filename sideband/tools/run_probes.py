#!/usr/bin/env python3
"""Phase-3 probe runner: executes the registered grid (BLUEPRINT Phase 3,
2026-08-30) on the S1 shadow harvest and emits the K-2 readout.

Registered grid (anything else is post-hoc and must say so):
  L1 concept_k16:  features {a,b,c} x {linear, mlp256} + {h} x {linear},
                   offsets 1..4, train seeds {0,1,2}
  L2 concept_k512: features {a,b,c} x {linear}, offsets 1..4, seeds {0,1,2}
  L3 concept_groups_v1: same economy as L2
Riders: R2 label-shuffle null (L1 linear (a),(c) at offsets 2,3,4; +17
        circular, seed 0; relative band, runs first, halts on fail)
        R3 split integrity (HarvestData.row_split aborts on violation)
R1 (harvest fidelity) is a separate GPU tool: sideband.real.fidelity_rider.

Estimand: pooled test top-1 accuracy per cell; MARGIN(j) = acc(c) - acc(a)
paired per anchor, prompt-cluster bootstrap over the 30 test prompts
(sideband.stats.paired_cluster_delta_ci, n_boot 2000, seed 0). Decision rule
applied mechanically at the end; the verdict text mirrors the registration.

Crash-resume: each completed cell is appended to <out>.state.jsonl and
skipped on restart (identity = space/offset/features/capacity/seed).
The state file's first line is a header binding it to the loaded
harvest's npz shas (registered 2026-08-31, critic round): resuming from
a state file checkpointed against a different harvest — or one with no
header — is refused, so a stale checkpoint can never masquerade as a
fresh run's cells. Registered runs' state files are committed evidence
(per-prompt cluster counts reproduce the bootstrap); smoke-run state
files are scratch.

Run (GPU box):
    python tools/run_probes.py --out results/real/probes_s1.json
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
from sideband.harvest import label_index  # noqa: E402
from sideband.probes import (HarvestData, anchor_table, labels_for,  # noqa: E402
                             load_label_space, slots_multi_hot, train_probe)
from sideband.stats import paired_cluster_delta_ci  # noqa: E402

REAL = Path(__file__).resolve().parent.parent / "results" / "real"
OFFSETS = (1, 2, 3, 4)
SEEDS = (0, 1, 2)
MATERIALITY = 0.005
SHUFFLE_SHIFT = 17


class AnchorBlock:
    """Per-batch view into a [rows, T, ...] harvest array at (row, anchor)
    coordinates — never materializes the per-offset slice."""

    def __init__(self, arr: np.ndarray, rows: np.ndarray, anchors: np.ndarray):
        self.arr, self.rows, self.anchors = arr, rows, anchors
        self._dim = 1 if arr.ndim == 2 else int(np.prod(arr.shape[2:]))

    @property
    def dim(self) -> int:
        return self._dim

    def batch(self, idx: np.ndarray) -> np.ndarray:
        x = self.arr[self.rows[idx], self.anchors[idx]]
        return x.reshape(len(idx), -1).astype(np.float32, copy=False)


class SlotsAnchorBlock:
    def __init__(self, slots: np.ndarray, rows: np.ndarray, anchors: np.ndarray, n_slots: int):
        top = int(slots.max())
        if top >= n_slots:
            # An id >= n_slots would scatter into the NEXT layer's multi-hot
            # segment — silent feature corruption (S3 guard: n_slots must be
            # the harvest's actual alphabet, 512 slots or 64 experts).
            raise SystemExit(f"telemetry id {top} >= n_slots {n_slots}: wrong --n-slots for this harvest")
        self.slots, self.rows, self.anchors, self.n_slots = slots, rows, anchors, n_slots

    @property
    def dim(self) -> int:
        return int(self.slots.shape[2]) * self.n_slots

    def batch(self, idx: np.ndarray) -> np.ndarray:
        return slots_multi_hot(self.slots[self.rows[idx], self.anchors[idx]], self.n_slots)


def bind_spaces_to_harvest(ref_meta: dict, paths: dict[str, str],
                           n_slots: int | None = None) -> None:
    """Refuse label-space files the loaded harvest did not log its masses
    against (critic blocker, 2026-08-31): the CPU probe chain previously
    accepted S1 Llama spaces against an S3 harvest silently — OLMoE token
    ids index a 128256-entry Llama map without error, and a forgotten
    space argument would run the whole registered grid on cross-model
    garbage. This also enforces Phase 2's logged-mass constraint
    mechanically. paths: {"buckets16": path, ...} keyed by the meta's
    buckets{k}_sha256 prefixes; n_slots (when given) must equal the
    harvest's telemetry alphabet (n_experts for S3, n_slots for S1)."""
    import hashlib as _hashlib

    checked = 0
    for name, path in paths.items():
        expect = ref_meta.get(f"{name}_sha256")
        if not expect:
            continue  # meta predates the binding or space not logged
        checked += 1
        got = _hashlib.sha256(Path(path).read_bytes()).hexdigest()
        if got != expect:
            raise SystemExit(
                f"{path} sha {got[:12]}... != harvest meta {name}_sha256 "
                f"{expect[:12]}... — the probe spaces must be the exact files "
                "the harvest logged masses against (wrong --buckets* args?)")
    if paths and not checked:
        # A meta with NO buckets*_sha256 keys would silently disarm this
        # guard (critic advisory) — every known harvester writes them.
        print("[bind] WARNING: harvest meta binds no bucket spaces; "
              "space-file binding is DISARMED for this harvest")
    if n_slots is not None:
        tele = int(ref_meta.get("n_experts") or ref_meta.get("n_slots") or 0)
        if tele and tele != int(n_slots):
            raise SystemExit(f"--n-slots {n_slots} != this harvest's telemetry "
                             f"alphabet {tele} (n_experts/n_slots in the meta)")


def space_names(tag: str = "concept") -> dict[str, str]:
    """Registered space names; the default tag reproduces the S1 names
    byte-identically. The S3 run passes its own tag so payloads from the
    two sources can never be confused."""
    return {"L1": f"L1_{tag}_k16", "L2": f"L2_{tag}_k512",
            "L3": f"L3_{tag}_groups_v1"}


def build_spaces(data: HarvestData, tag: str = "concept",
                 buckets16=None, glue16=None, buckets512=None, glue512=None,
                 groups_path=None) -> dict:
    """Label maps per registered label space. (a)-features are UNIFORM
    across spaces per the amended registration (all logged free summaries),
    so spaces carry labels only. Default paths/tag = the S1 instrument,
    byte-identical."""
    buckets16 = Path(buckets16 or REAL / "buckets_k16.json")
    glue16 = Path(glue16 or REAL / "glue_k16.json")
    buckets512 = Path(buckets512 or REAL / "buckets_k512.json")
    glue512 = Path(glue512 or REAL / "glue_k512.json")
    groups_path = Path(groups_path or REAL / "concept_groups_v1.json")
    names = space_names(tag)
    if groups_path.exists():
        # The L3 lens is only meaningful over the exact k512 bucketization
        # it was built from (same failure class as the glue binding).
        import hashlib as _hashlib

        rec = json.loads(groups_path.read_text()).get("provenance", {}).get("buckets_k512_sha256")
        got = _hashlib.sha256(buckets512.read_bytes()).hexdigest()
        if rec and rec != got:
            raise SystemExit(f"{groups_path.name} was built over a DIFFERENT k512 "
                             "bucketization than the loaded buckets512 file — refusing")
    l1_map, l1_n = load_label_space(buckets16, glue16)
    l2_map, l2_n = load_label_space(buckets512, glue512)
    spaces = {
        names["L1"]: {"label_map": l1_map, "n_classes": l1_n},
        names["L2"]: {"label_map": l2_map, "n_classes": l2_n},
    }
    if groups_path.exists():
        gdata = json.loads(groups_path.read_text())
        groups = np.asarray(gdata["group_of_concept"], dtype=np.int64)
        n_groups = int(gdata["n_groups"])
        # token -> group label (glue/unbucketed -> class n_groups), through
        # the k512 concept ids the grouping was built over.
        import hashlib

        from sideband.glue import glue_remap, load_glue
        bdata = json.loads(buckets512.read_text())
        raw = np.full(int(bdata["n_tokens"]), -1, dtype=np.int64)
        for tok, b in bdata["bucket_of_token"].items():
            raw[int(tok)] = int(b)
        glue_ids, _ = load_glue(str(glue512),
                                expect_buckets_sha256=hashlib.sha256(buckets512.read_bytes()).hexdigest())
        steer512, _m, _C512 = glue_remap(raw, glue_ids)
        l3_map = np.where(steer512 >= 0, groups[np.clip(steer512, 0, None)], n_groups)
        spaces[names["L3"]] = {
            "label_map": l3_map.astype(np.int64), "n_classes": n_groups + 1,
            "groups_provenance": {k: gdata[k] for k in ("construction", "provenance")},
        }
    return spaces


def feature_blocks(data: HarvestData, feats: str,
                   rows: np.ndarray, anchors: np.ndarray,
                   n_slots: int = 512) -> list:
    """Registered feature sets (amended 2026-08-30): (a) = ALL logged free
    summaries of p_a — mass16+mass32+mass64+mass512 + entropy + top-32
    sorted probs (657 dims on S1; ids excluded as non-ordinal) — identical
    at every label space; (b) = telemetry multi-hot over n_slots per layer
    (S1: 512 HashSketch slots; S3: 64 experts); (c) = (a)+(b); (h) = h_a."""
    if feats not in ("a", "b", "c", "h"):
        raise ValueError(f"unknown feature set {feats!r}")
    blocks = []
    if feats in ("a", "c"):
        for key in ("mass16", "mass32", "mass64", "mass512"):
            blocks.append(AnchorBlock(data.array(key), rows, anchors))
        blocks.append(AnchorBlock(data.array("entropy"), rows, anchors))
        blocks.append(AnchorBlock(data.array("top_p"), rows, anchors))
    if feats in ("b", "c"):
        blocks.append(SlotsAnchorBlock(data.array("slots"), rows, anchors, n_slots=n_slots))
    if feats == "h":
        blocks.append(AnchorBlock(data.array("hidden"), rows, anchors))
    return blocks


def cell_id(space: str, offset: int, feats: str, cap: str, seed: int, shuffled: bool = False) -> str:
    return f"{space}|off{offset}|{feats}|{cap}|s{seed}" + ("|SHUFFLED" if shuffled else "")


def run_cell(data: HarvestData, spaces: dict, space_name: str, offset: int,
             feats: str | None, cap: str, seed: int, device: str,
             shuffled: bool = False, extra_factory=None,
             feats_label: str | None = None, n_slots: int = 512) -> dict:
    """One probe cell. feats None + extra_factory = extra-only features;
    extra_factory(rows, anchors) -> list of blocks appended after the
    registered ones (post-hoc P1 uses this for the prefix-topic block).
    Default call (extra_factory=None, feats_label=None, n_slots=512) is
    byte-identical to the registered Phase-3 S1 instrument."""
    sp = spaces[space_name]
    rows, anchors = anchor_table(data.lengths, offset, data.tokens.shape[1])
    labels = labels_for(data.tokens, rows, anchors, offset, sp["label_map"],
                        shuffle_shift=(SHUFFLE_SHIFT if shuffled else 0),
                        lengths=data.lengths if shuffled else None)
    split = data.row_split()[rows]
    blocks = [] if feats is None else feature_blocks(data, feats, rows, anchors, n_slots=n_slots)
    if extra_factory is not None:
        blocks = blocks + list(extra_factory(rows, anchors))
    if not blocks:
        raise ValueError("no feature blocks (feats=None requires extra_factory)")
    label = feats_label if feats_label is not None else feats
    t0 = time.time()
    res = train_probe(blocks, labels, split, sp["n_classes"], cap, seed, device=device)
    te_idx = np.nonzero(split == "test")[0]
    prompts_of_test = data.prompt_idx[rows[te_idx]]
    y_test = labels[te_idx]
    maj_label = np.bincount(labels[split == "train"]).argmax()
    out = {
        "cell": cell_id(space_name, offset, label, cap, seed, shuffled),
        "space": space_name, "offset": offset, "features": label,
        "capacity": cap, "seed": seed, "shuffled": shuffled,
        "test_acc": res["test_acc"], "val_acc_best": res["val_acc_best"],
        "best_epoch": res["best_epoch"],
        "n_train": res["n_train"], "n_val": res["n_val"], "n_test": res["n_test"],
        "majority_rate_test": float((y_test == maj_label).mean()),
        "runtime_s": round(time.time() - t0, 1),
        # per-prompt aggregates for the paired bootstrap (compact, ordered)
        "_clusters": {int(p): [int(res["test_correct"][prompts_of_test == p].sum()),
                               int((prompts_of_test == p).sum())]
                      for p in np.unique(prompts_of_test)},
    }
    return out


def normalize_clusters(cell: dict) -> dict:
    """State-file JSON round-trips turn _clusters' int prompt keys into
    strings; a mixed fresh+resumed run would then intersect int-key and
    string-key sets to EMPTY (critic-demonstrated). Normalize on every
    ingest path so cluster identity is type-stable."""
    if "_clusters" in cell:
        cell["_clusters"] = {int(k): v for k, v in cell["_clusters"].items()}
    return cell


def state_header(npz_shas: dict[str, str]) -> dict:
    return {"kind": "state_header", "harvest_npz_sha256": dict(npz_shas)}


def parse_state(text: str, npz_shas: dict[str, str]) -> dict[str, dict]:
    """Parse a state file for resume, enforcing the harvest-binding header
    (registered 2026-08-31, critic round): line 1 must be a header whose
    npz shas equal the loaded harvest's — a stale checkpoint from a
    different harvest silently resuming under fresh provenance would
    fabricate a replication. A torn FINAL line is dropped (crash
    mid-append); any other corrupt line aborts."""
    lines = text.splitlines()
    if not lines or not lines[0].strip():
        raise SystemExit("state file exists but is empty/headerless — delete it and rerun")
    try:
        header = json.loads(lines[0])
    except json.JSONDecodeError:
        raise SystemExit("corrupt state-file header line (crash during header "
                         "write?) — no cells were checkpointed; delete the "
                         "state file and rerun")
    if not isinstance(header, dict) or header.get("kind") != "state_header":
        raise SystemExit(
            "state file lacks the harvest-binding header (pre-header-era "
            "checkpoint). If its run is COMPLETE (the payload json exists), do "
            "not rerun against it; otherwise delete the state file and restart")
    if header.get("harvest_npz_sha256") != npz_shas:
        raise SystemExit(
            "state file was checkpointed against a DIFFERENT harvest (npz shas "
            "differ) — refusing to resume; delete it or use a different --out")
    done: dict[str, dict] = {}
    for i, line in enumerate(lines[1:], start=2):
        if not line.strip():
            continue
        try:
            c = json.loads(line)
        except json.JSONDecodeError:
            if i == len(lines):
                print("[resume] dropping torn final state line (crash mid-append)")
                continue
            raise SystemExit(f"corrupt state line {i}")
        done[c["cell"]] = normalize_clusters(c)  # JSON stringified the prompt keys
    return done


def margins(cells: list[dict], top_feats: str = "c",
            expected_clusters: int | None = None, base_feats: str = "a") -> list[dict]:
    """Seed-combined paired (top_feats)-(base_feats) margins per (space,
    offset, capacity): per-prompt successes are SUMMED over the three train
    seeds before the bootstrap (the pinned estimand — one margin + one CI
    per triple); per-seed point margins are recorded as diagnostics only.
    expected_clusters: when set, refuse if the paired prompt set is any
    other size (catches upstream label/split drift). base_feats defaults to
    "a" (the registered Phase-3 pairing); the post-hoc P1 diagnostic passes
    other bases (e.g. "at") — behavior at the default is unchanged."""
    cells = [normalize_clusters(dict(c)) for c in cells]
    by_id = {c["cell"]: c for c in cells if not c["shuffled"]}
    triples: dict[tuple, dict[int, tuple[dict, dict]]] = {}
    for c in cells:
        if c["shuffled"] or c["features"] != top_feats:
            continue
        a = by_id.get(cell_id(c["space"], c["offset"], base_feats, c["capacity"], c["seed"]))
        if a is None:
            continue
        triples.setdefault((c["space"], c["offset"], c["capacity"]), {})[c["seed"]] = (c, a)
    out = []
    for (space, offset, cap), seeds in sorted(triples.items()):
        prompts = sorted(set.intersection(*(set(c["_clusters"]) for c, _ in seeds.values())))
        if expected_clusters is not None and len(prompts) != expected_clusters:
            raise SystemExit(f"{space} off{offset} {cap}: paired prompt set has "
                             f"{len(prompts)} clusters, expected {expected_clusters}")
        sc = np.zeros(len(prompts))
        sa = np.zeros(len(prompts))
        n = np.zeros(len(prompts))
        per_seed = {}
        for seed, (c, a) in sorted(seeds.items()):
            cs = np.array([c["_clusters"][p][0] for p in prompts], dtype=np.float64)
            as_ = np.array([a["_clusters"][p][0] for p in prompts], dtype=np.float64)
            cn = np.array([c["_clusters"][p][1] for p in prompts], dtype=np.float64)
            an = np.array([a["_clusters"][p][1] for p in prompts], dtype=np.float64)
            if not np.array_equal(cn, an):
                raise SystemExit(f"pairing broken at {space} off{offset} {cap} s{seed}")
            sc += cs
            sa += as_
            n += cn
            per_seed[seed] = float((cs - as_).sum() / cn.sum())
        delta, lo, hi = paired_cluster_delta_ci(sc, sa, n)
        out.append({"space": space, "offset": offset, "capacity": cap,
                    "pair": f"{top_feats}-{base_feats}",
                    "margin": delta, "ci95": [lo, hi],
                    "per_seed_margin": per_seed,
                    "n_seeds": len(seeds), "n_clusters": len(prompts)})
    return out


def r2_summary(cells: list[dict]) -> dict | None:
    """R2 pass/fail from the shuffled cells, fresh or resumed alike: at each
    shuffled offset, shuffled-(c) must be <= shuffled-(a) + 0.01. None when
    no shuffled pair exists (which itself blocks any verdict downstream)."""
    r2_cells = [c for c in cells if c["shuffled"]]
    per_off = {}
    for off in sorted({c["offset"] for c in r2_cells}):
        sa = next((c for c in r2_cells if c["offset"] == off and c["features"] == "a"), None)
        sc = next((c for c in r2_cells if c["offset"] == off and c["features"] == "c"), None)
        if sa and sc:
            per_off[off] = {"shuffled_a": sa["test_acc"], "shuffled_c": sc["test_acc"],
                            "pass": bool(sc["test_acc"] <= sa["test_acc"] + 0.01)}
    if not per_off:
        return None
    return {"per_offset": per_off, "pass": all(v["pass"] for v in per_off.values())}


def oq6_survival(margin_c: list[dict], margin_h: list[dict]) -> list[dict]:
    """Survival fraction margin(c-a)/margin(h-a) at offsets >= 2, defined
    only where the h-a margin's CI lower > 0 (registered OQ-6 readout —
    reported, never a criterion; an ACCURACY-margin ratio, never an
    SD^2-acceptance percentage)."""
    hmap = {(m["space"], m["offset"], m["capacity"]): m for m in margin_h}
    out = []
    for m in margin_c:
        if m["offset"] < 2:
            continue
        h = hmap.get((m["space"], m["offset"], m["capacity"]))
        if h is None:
            continue
        defined = h["ci95"][0] > 0
        out.append({"space": m["space"], "offset": m["offset"],
                    "capacity": m["capacity"],
                    "margin_c_a": m["margin"], "margin_h_a": h["margin"],
                    "survival_fraction": (m["margin"] / h["margin"]) if defined else None,
                    "defined": bool(defined)})
    return out


EXPECTED_OFF2_TRIPLES = 12  # (L1-linear, L1-mlp256, L2, L3) x offsets {2,3,4}


def verdict(margin_rows: list[dict], r2_pass: bool | None = None) -> dict:
    """The registered K-2/S1 decision rule (amended 2026-08-30), mechanical:
    EXISTENCE iff some (space, offset>=2, capacity) triple has (i)
    seed-combined margin CI95 lower > 0, (ii) positive per-seed point
    margins at all three seeds, (iii) seed-combined point margin >=
    +0.005. NEGATIVE iff no such triple and the best offset>=2 CI upper <
    +0.005. Else OPEN. An EXISTENCE verdict is PROVISIONAL pending the
    registered fresh-harvest-seed replication.

    Guards (critic round 4): a kill verdict is unreachable on a partial
    grid — anything short of the full 12 offset->=2 triples at 3 seeds
    each returns INCOMPLETE; a failed (or missing) R2 poisons the verdict
    outright."""
    if r2_pass is not True:
        return {"verdict": "R2_FAILED_OR_MISSING",
                "note": "label-shuffle null did not pass; no margin is citable"}
    off2 = [m for m in margin_rows if m["offset"] >= 2]
    if len(off2) != EXPECTED_OFF2_TRIPLES or any(m["n_seeds"] != len(SEEDS) for m in off2):
        return {"verdict": "INCOMPLETE",
                "n_off2_triples": len(off2), "expected": EXPECTED_OFF2_TRIPLES,
                "note": "partial grid — no registered verdict can issue from it"}
    existence = []
    for m in off2:
        if (m["n_seeds"] == len(SEEDS)
                and m["ci95"][0] > 0
                and all(v > 0 for v in m["per_seed_margin"].values())
                and m["margin"] >= MATERIALITY):
            existence.append(m)
    best_upper = max((m["ci95"][1] for m in off2), default=float("-inf"))
    if existence:
        v = "EXISTENCE (provisional: replication on fresh harvest seeds required)"
    elif best_upper < MATERIALITY:
        v = "NEGATIVE"
    else:
        v = "OPEN"
    return {"verdict": v, "existence_triples": existence,
            "best_offset_ge2_ci_upper": best_upper, "materiality_floor": MATERIALITY,
            "multiplicity_note": ("12 uncorrected offset>=2 triples; family-wise "
                                  "false-EXISTENCE ~26% under a global null before the "
                                  "materiality floor and replication requirement"),
            "rule": ("registered 2026-08-30, amended same day on critic review "
                     "before any probe ran; see BLUEPRINT Phase 3")}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--harvest", default="results/real/harvest_shadow")
    ap.add_argument("--fidelity", default="results/real/harvest_fidelity_rider.json",
                    help="R1 rider payload whose npz shas must match --harvest "
                         "(replication runs pass their own rider file)")
    ap.add_argument("--out", default="results/real/probes_s1.json")
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--only", default=None, help="substring filter on cell ids (smoke)")
    # Source parametrization (S3 registration 2026-08-31). Defaults = the S1
    # instrument, byte-identical; the S3 run passes its own spaces + widths.
    ap.add_argument("--space-tag", default="concept",
                    help="space names L1_{tag}_k16 / L2_{tag}_k512 / L3_{tag}_groups_v1")
    ap.add_argument("--n-slots", type=int, default=512,
                    help="telemetry alphabet per layer (S1 slots 512; S3 experts 64)")
    ap.add_argument("--buckets16", default=str(REAL / "buckets_k16.json"))
    ap.add_argument("--glue16", default=str(REAL / "glue_k16.json"))
    ap.add_argument("--buckets32", default=str(REAL / "buckets_k32.json"),
                    help="provenance sha only (masses were logged at harvest)")
    ap.add_argument("--buckets64", default=str(REAL / "buckets_k64.json"),
                    help="provenance sha only (masses were logged at harvest)")
    ap.add_argument("--buckets512", default=str(REAL / "buckets_k512.json"))
    ap.add_argument("--glue512", default=str(REAL / "glue_k512.json"))
    ap.add_argument("--groups", default=str(REAL / "concept_groups_v1.json"))
    args = ap.parse_args()

    REGISTERED_OUTS = ("results/real/probes_s1.json",
                       "results/real/probes_s1_replication.json",
                       "results/real/probes_s3.json",
                       "results/real/probes_s3_replication.json")
    if args.only and Path(args.out).resolve() in {(REAL.parent.parent / p).resolve()
                                                  for p in REGISTERED_OUTS}:
        raise SystemExit("--only produces a PARTIAL post-hoc run; it may not write a "
                         "registered out path — pass an explicit non-default --out")

    data = HarvestData(args.harvest)
    data.row_split()  # R3 abort-on-violation, before anything trains
    bind_spaces_to_harvest(data.ref_meta,
                           {"buckets16": args.buckets16, "buckets32": args.buckets32,
                            "buckets64": args.buckets64, "buckets512": args.buckets512},
                           n_slots=args.n_slots)

    fid = Path(args.fidelity)
    if not fid.exists():
        raise SystemExit("R1 harvest-fidelity rider missing — run "
                         "sideband.real.fidelity_rider first (registered gate)")
    rider = json.loads(fid.read_text())
    if rider.get("verdict") != "PASS":
        raise SystemExit("R1 rider verdict is not PASS — harvest quarantined")
    if rider.get("npz_sha256_validated") != data.npz_shas:
        raise SystemExit("R1 rider validated a DIFFERENT harvest version (npz shas "
                         "differ) — rerun sideband.real.fidelity_rider on this data")

    names = space_names(args.space_tag)
    spaces = build_spaces(data, tag=args.space_tag,
                          buckets16=args.buckets16, glue16=args.glue16,
                          buckets512=args.buckets512, glue512=args.glue512,
                          groups_path=args.groups)
    if names["L3"] not in spaces:
        raise SystemExit(f"{args.groups} missing — run tools/build_concept_groups.py first")

    # R2 leak detector runs FIRST: a pipeline leak must halt the grid, not
    # be discovered after 5 GPU-hours. Sharpened rule (registered): the
    # null band is RELATIVE — shuffled-(c) <= shuffled-(a) + 0.01 at each
    # of offsets 2..4 (both see per-prompt label composition; only a
    # pipeline leak separates them).
    grid: list[tuple] = []
    for off in (2, 3, 4):
        grid.append((names["L1"], off, "a", "linear", 0, True))
        grid.append((names["L1"], off, "c", "linear", 0, True))
    for off in OFFSETS:
        for seed in SEEDS:
            for feats in ("a", "b", "c"):
                for cap in ("linear", "mlp256"):
                    grid.append((names["L1"], off, feats, cap, seed, False))
                grid.append((names["L2"], off, feats, "linear", seed, False))
                grid.append((names["L3"], off, feats, "linear", seed, False))
            grid.append((names["L1"], off, "h", "linear", seed, False))

    state_path = Path(args.out + ".state.jsonl")
    done: dict[str, dict] = {}
    if state_path.exists():
        done = parse_state(state_path.read_text(), data.npz_shas)
        print(f"[resume] {len(done)} cells already done")
    else:
        with state_path.open("w") as f:
            f.write(json.dumps(state_header(data.npz_shas)) + "\n")

    t0 = time.time()
    cells = []
    for i, (space, off, feats, cap, seed, shuffled) in enumerate(grid):
        cid = cell_id(space, off, feats, cap, seed, shuffled)
        if args.only and args.only not in cid:
            continue
        if cid in done:
            res = done[cid]
            cells.append(res)
        else:
            res = run_cell(data, spaces, space, off, feats, cap, seed, args.device, shuffled,
                           n_slots=args.n_slots)
            cells.append(res)
            with state_path.open("a") as f:
                f.write(json.dumps(res) + "\n")
            print(f"[{i + 1}/{len(grid)}] {cid}: test_acc={res['test_acc']:.4f} "
                  f"(maj {res['majority_rate_test']:.4f}) {res['runtime_s']}s "
                  f"total {time.time() - t0:.0f}s", flush=True)
        # The R2 halt fires on RESUMED cells too (critic round 4: a halt
        # that a Ctrl-C disarms is not a halt).
        if shuffled and feats == "c":
            a_cell = next((c for c in cells
                           if c["shuffled"] and c["features"] == "a" and c["offset"] == off), None)
            if a_cell is None:
                raise SystemExit(f"R2 shuffled-(c) at offset {off} has no shuffled-(a) "
                                 "partner in this run (--only filter too narrow?)")
            if res["test_acc"] > a_cell["test_acc"] + 0.01:
                raise SystemExit(
                    f"R2 LABEL-SHUFFLE NULL FAILED at offset {off}: shuffled-(c) "
                    f"{res['test_acc']:.4f} > shuffled-(a) {a_cell['test_acc']:.4f} + 0.01 "
                    "— pipeline leak; halting per registration")

    r2_result = r2_summary(cells)
    r2_ok = bool(r2_result and r2_result["pass"])
    expected = None if args.only else 30
    margin_rows = margins(cells, "c", expected_clusters=expected) if r2_ok else []
    margin_h = margins(cells, "h", expected_clusters=expected) if r2_ok else []
    margin_b = margins(cells, "b", expected_clusters=expected) if r2_ok else []

    import hashlib
    import subprocess

    def _sha(p: Path) -> str:
        return hashlib.sha256(p.read_bytes()).hexdigest()

    def _git() -> str:
        try:
            r = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=10)
            d = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, timeout=10)
            return (r.stdout.strip() or "unknown") + ("-dirty" if d.stdout.strip() else "")
        except Exception:
            return "unknown"

    import torch

    provenance = {
        "git_commit": _git(),
        "args": redact_args(vars(args)),
        "harvest_npz_sha256": data.npz_shas,
        "label_space_sha256": {p.name: _sha(p) for p in (
            Path(args.buckets16), Path(args.glue16),
            Path(args.buckets32), Path(args.buckets64),
            Path(args.buckets512), Path(args.glue512),
            Path(args.groups)) if p.exists()},
        "torch_version": torch.__version__,
        "device": args.device,
        "determinism_note": ("CUDA probe training uses atomics; per-cell results are "
                             "evidenced by the recorded state file, not rerun-exactness"),
    }

    payload = {
        "registered": ("BLUEPRINT Phase 3 protocol (2026-08-30, amended same day)"
                       if args.space_tag == "concept" else
                       "BLUEPRINT Phase 3 protocol run verbatim under the S3 "
                       "registration block (2026-08-31)"),
        "harvest": args.harvest,
        "partial": bool(args.only),
        "provenance": provenance,
        "n_cells": len([c for c in cells if not c["shuffled"]]),
        "cells": [{k: v for k, v in c.items() if k != "_clusters"} for c in cells],
        "margins": margin_rows,
        "margins_h_vs_a": margin_h,
        "margins_b_vs_a": margin_b,
        "oq6_survival": oq6_survival(margin_rows, margin_h),
        "r2_label_shuffle": r2_result,
        "l3_provenance": spaces.get(names["L3"], {}).get("groups_provenance"),
        "decision": verdict(margin_rows, r2_pass=(r2_result or {}).get("pass")),
        "runtime_s": round(time.time() - t0, 1),
    }
    Path(args.out).write_text(json.dumps(payload, indent=1, sort_keys=True))
    print(json.dumps({"decision": payload["decision"]["verdict"],
                      "r2": r2_result,
                      "n_margins": len(margin_rows)}, indent=2))


if __name__ == "__main__":
    main()
