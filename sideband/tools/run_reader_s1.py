#!/usr/bin/env python
"""S1 READER RE-TEST — the S1 word instrument (docs/BLUEPRINT.md, "S1 READER
RE-TEST REGISTRATION", 2026-10-16; lever 1 of the operator's science-lever decisions of that date).

The cells are trained by the FROZEN instrument tools/run_reader_lens.py (its
`s1` stage: `--stage s1 --readers RN,RT,RL --harvest results/real/harvest_shadow
[_r] --out results/real/readers_s1[_r].json`), whose grid, readers, readouts,
labels and licences are the ones F-28 used at S3. That tool's own
--conclude-from on an s1 pair yields the per-reader labels and, by its note, no
word: the K-2 sentence it issues is the S3 block's. This file issues the S1
WORD the registration pins, over the three readers at the S1 gate cell
(L1_concept_k16 / off2 / mlp256), from the frozen labels:

  K-2-INCOMPLETE-AT-S1      iff no valid (non READER-INVALID) reader exists;
  K-2-REOPENED-AT-S1        iff some valid reader is REOPEN-GRADE (the frozen
                            reopen_eligible: SURVIVES-STRONGER with the FULL
                            licence AND Mt firing the triple rule on both
                            harvests); PER SOURCE, no S3 condition; PROVISIONAL
                            until the reader-matched rider passes;
  K-2-ISOLATED-AT-S1        iff some valid reader reads SURVIVES-STRONGER and
                            none is reopen-grade;
  K-2-UNSETTLED-AT-S1       iff some valid reader reads SPLIT and none
                            SURVIVES-STRONGER;
  K-2-NOT-OVERTURNED-AT-S1  iff every valid reader reads ABSORBED or NOT-SHOWN
                            (narrowed where ABSORBED, not where NOT-SHOWN).

The OQ-18 amended-instrument precedent: a NEW file that imports the frozen
instrument by bare name and asserts its raw-byte sha at import and again
before any conclusion, so the six payloads that attest the frozen tool can
still be concluded; nothing here is re-implemented — verify_payload,
recompute_readouts, labels_of_pair, reopen_eligible and the label constants
are the frozen tool's.

  --conclude PRIMARY REPLICATION --out results/real/readers_s1_word.json
    verifies both payloads through the frozen verify_payload (stage s1, the
    role-bound harvest, the registry, the row set, HEAD, n_boot, instrument
    sha, state sha, a clean tree, under results/real), refuses a pair whose
    readers are not exactly the registered (RN, RT, RL) in that order or whose
    launch commits differ, recomputes every readout from the state files (a
    payload whose stored numbers differ is refused), derives the labels, issues
    the word, records the pairing checks (the twin permutation shas against the
    committed F-24 twin payloads; the RN and RT fresh (a) rows, both R-0
    retrainings, identical except runtime) and writes the payload LF. On the
    registered out name the tracked tree must be clean, this file git-tracked,
    the data root the committed one and the out not yet present; any other out
    name under results/ is refused; an out path outside results/ is a scratch
    write (registered false).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_reader_lens as rl  # noqa: E402  (the FROZEN instrument; its chain is asserted by assert_frozen_reader_lens below)

ROOT = Path(__file__).resolve().parent.parent
REAL = rl.REAL
FROZEN_READER_LENS = Path(rl.__file__).resolve()
FROZEN_READER_LENS_SHA256 = "d1125670be056b4824ebfcd734379f40e44db994308c10accb731839d2a4a624"
REGISTRATION = "S1 READER RE-TEST REGISTRATION (docs/BLUEPRINT.md, 2026-10-16; pre-run; the frozen run_reader_lens s1 stage trains the cells; this file issues the S1 word)"
REGISTERED_OUT = "readers_s1_word.json"
S1_SPACE = rl.SPACE_L1["concept"]
S1_OUTS = rl.REGISTERED_OUTS["s1"]                           # ("readers_s1.json", "readers_s1_r.json")
S1_READERS = ("RN", "RT", "RL")                               # the registered readers, in the registered grid order; R0 is NOT re-run
TWIN_PAYLOAD_OF_HARVEST = {"harvest_shadow": "fullfree_s1_twin.json", "harvest_shadow_r": "fullfree_s1_r_twin.json"}
WORD_INCOMPLETE = "K-2-INCOMPLETE-AT-S1"
WORD_REOPENED = "K-2-REOPENED-AT-S1"
WORD_ISOLATED = "K-2-ISOLATED-AT-S1"
WORD_UNSETTLED = "K-2-UNSETTLED-AT-S1"
WORD_NOT_OVERTURNED = "K-2-NOT-OVERTURNED-AT-S1"
WORDS = (WORD_INCOMPLETE, WORD_REOPENED, WORD_ISOLATED, WORD_UNSETTLED, WORD_NOT_OVERTURNED)
RULE = ("over the valid readers at S1 L1 (READER-INVALID readers VOID, named): INCOMPLETE iff no valid reader; "
        "REOPENED iff some valid reader is reopen-grade (SURVIVES-STRONGER, FULL licence, Mt firing the triple rule on "
        "both harvests), per source, PROVISIONAL until the reader-matched rider passes; ISOLATED iff some "
        "SURVIVES-STRONGER and no reopen-grade reader; UNSETTLED iff some SPLIT and no SURVIVES-STRONGER; "
        "NOT-OVERTURNED iff every valid reader reads ABSORBED or NOT-SHOWN (narrowed where ABSORBED, not where "
        "NOT-SHOWN); precedence INCOMPLETE, REOPENED, ISOLATED, UNSETTLED, NOT-OVERTURNED; the S3 word does not move")
RIDER_RULE = ("a REOPENED word is PROVISIONAL until a reader-matched rider (the four amended-rider shuffled cells under "
              "that reader at mlp256, off2, seed 0, on both S1 harvests, run_oq18_rider_diag's amended rule through a new "
              "instrument that may not relax the bands) passes under its own dated registration; the landing's K-2 STATUS "
              "line carries the word with the qualifier PROVISIONAL and the sentence that S1's FIRED status of 2026-09-06 "
              "stands until the rider lands; no K-2 status word changes before then")
KNOWN_LABELS = (rl.LABEL_STRONGER, rl.LABEL_SPLIT, rl.LABEL_ABSORBED, rl.LABEL_NOT_SHOWN, rl.LABEL_READER_INVALID)


def _sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def assert_frozen_reader_lens() -> dict:
    """The frozen reader-lens instrument on disk is the one this file was written
    against (raw bytes; the file is -text, so disk equals blob), and its own
    parent chain holds."""
    got = _sha(FROZEN_READER_LENS)
    if got != FROZEN_READER_LENS_SHA256:
        raise SystemExit(f"the frozen reader-lens instrument hashes to {got[:12]}, not {FROZEN_READER_LENS_SHA256[:12]} — refusing")
    chain = rl.assert_frozen_chain()
    chain["reader_lens_sha256"] = got
    return chain


FROZEN_CHAIN_AT_IMPORT = assert_frozen_reader_lens()          # fail closed at import; asserted again in conclude()


# ---------------------------------------------------------------------------
# The S1 word (pure; the registration's rules over the frozen labels)
# ---------------------------------------------------------------------------

def s1_word(labels: dict[str, dict]) -> dict:
    """labels: {"<READER>|L1_concept_k16": pair_label dict} from the frozen
    labels_of_pair over an s1 pair. Every key must sit at the S1 gate space and
    carry a frozen label word."""
    for key, v in labels.items():
        _, _, space = key.partition("|")
        if space != S1_SPACE:
            raise SystemExit(f"{key}: not the S1 gate space {S1_SPACE} — refusing")
        if v.get("label") not in KNOWN_LABELS:
            raise SystemExit(f"{key}: unknown label {v.get('label')!r} — refusing")
    valid = {k: v for k, v in labels.items() if v["label"] != rl.LABEL_READER_INVALID}
    void = sorted(k for k, v in labels.items() if v["label"] == rl.LABEL_READER_INVALID)
    reopen = sorted(k for k, v in valid.items() if rl.reopen_eligible(v))
    surv = sorted(k for k, v in valid.items() if v["label"] == rl.LABEL_STRONGER)
    split = sorted(k for k, v in valid.items() if v["label"] == rl.LABEL_SPLIT)
    if not valid:
        word = WORD_INCOMPLETE
    elif reopen:
        word = WORD_REOPENED
    elif surv:
        word = WORD_ISOLATED
    elif split:
        word = WORD_UNSETTLED
    else:
        word = WORD_NOT_OVERTURNED
    return {"word": word, "per_source": "S1; no S3 condition attaches and the S3 word (K-2-ISOLATED, final) does not move",
            "over_valid_cells_only": bool(void), "void_cells": void,
            "reopened": reopen, "provisional": bool(reopen), "reader_matched_rider_rule": RIDER_RULE if reopen else None,
            "survives_stronger": {k: {"licence": valid[k]["licence"], "licence_reason": valid[k]["licence_reason"]} for k in surv},
            "split": split,
            "narrowed_cells": sorted(k for k, v in valid.items() if v["label"] == rl.LABEL_ABSORBED),
            "not_narrowed_cells": sorted(k for k, v in valid.items() if v["label"] == rl.LABEL_NOT_SHOWN),
            "rule": RULE}


# ---------------------------------------------------------------------------
# conclude
# ---------------------------------------------------------------------------

def _git(strict: bool) -> tuple[str, list[str]]:
    return rl._git(strict=strict)


def _tool_tracked() -> bool:
    t = subprocess.run(["git", "ls-files", "--error-unmatch", str(Path(__file__).resolve())], cwd=ROOT,
                       capture_output=True, text=True, timeout=10)
    return t.returncode == 0


def _state_path(payload_path: Path, p: dict) -> Path:
    return payload_path.parent / p["provenance"]["state_file"]


def conclude(primary: Path, replication: Path, data_root: Path = REAL) -> dict:
    """The S1 word from a verified s1 pair: every number re-derived from the
    state files through the frozen rules (a stored number that differs is a
    refusal), the labels through the frozen labels_of_pair, the word through
    s1_word."""
    chain = assert_frozen_reader_lens()
    primary, replication = Path(primary), Path(replication)
    pp, pc = rl.verify_payload(primary, "primary", expect_stage="s1")
    rp, rc = rl.verify_payload(replication, "replication", expect_stage="s1")
    if pp["provenance"]["harvest_npz_sha256"] == rp["provenance"]["harvest_npz_sha256"]:
        raise SystemExit("the two payloads bind the SAME harvest — not a primary / replication pair")
    for role, p in (("primary", pp), ("replication", rp)):
        if tuple(p["readers"]) != S1_READERS:
            raise SystemExit(f"the {role} payload names readers {list(p['readers'])}; the registered s1 stage runs exactly "
                             f"{list(S1_READERS)} in that order (R0 is not re-run) — refusing")
        if list(p["spaces"]) != [S1_SPACE]:
            raise SystemExit(f"an s1 payload carries the one space {S1_SPACE}; the {role} payload has {p['spaces']} — refusing")
    if pp["provenance"]["git_commit"] != rp["provenance"]["git_commit"]:
        raise SystemExit(f"the two payloads were launched at different commits ({str(pp['provenance']['git_commit'])[:12]} / "
                         f"{str(rp['provenance']['git_commit'])[:12]}) — one registration, one launch HEAD; refusing")
    rl.recompute_readouts(pp, pc, data_root)
    rl.recompute_readouts(rp, rc, data_root)
    labels = rl.labels_of_pair(pp, rp, (rl.GATE_OFFSET,), stronger=True)
    word = s1_word(labels)
    inputs = {"data_root": str(Path(data_root).resolve())}
    for role, path, p, cells in (("primary", primary, pp, pc), ("replication", replication, rp, rc)):
        inputs[role] = {"payload": path.name, "payload_sha256": _sha(path),
                        "state_file": p["provenance"]["state_file"], "state_sha256": _sha(_state_path(path, p)),
                        "harvest": p["harvest"], "git_commit": p["provenance"]["git_commit"],
                        "instrument_sha256": p["provenance"]["instrument_sha256"], "n_rows": len(cells),
                        "resumed_cells": p.get("resumed_cells"), "runtime_s": p.get("runtime_s"),
                        "torn_bytes_dropped_on_resume": p["provenance"].get("torn_bytes_dropped_on_resume")}
    diagnostics = {k: {"reader_valid": {"primary": pp["per_reader_space"][k]["reader_valid"],
                                        "replication": rp["per_reader_space"][k]["reader_valid"]},
                       "best_epochs": v["best_epochs"],
                       "rescale": {"primary": pp["per_reader_space"][k].get("rescale"),
                                   "replication": rp["per_reader_space"][k].get("rescale")}}
                   for k, v in labels.items()}
    pairing = {"primary": pairing_checks(pp, pc, Path(data_root)), "replication": pairing_checks(rp, rc, Path(data_root))}
    return {"registration": REGISTRATION, "stage": "s1", "readers": list(pp["readers"]), "space": S1_SPACE,
            "materiality_floor": rl.MATERIALITY, "labels": labels, "diagnostics": diagnostics, "word": word,
            "pairing": pairing, "rule": RULE, "inputs": inputs, "frozen_chain": chain}


def pairing_checks(p: dict, cells: list[dict], data_root: Path) -> dict:
    """Descriptive, never a refusal; the landing test pins them. (1) The twin
    permutation shas of this payload against the committed F-24 twin payload of
    the same harvest (the same construction, derangement_by_prompt at the same
    seeds). (2) The fresh (a) mlp256 rows under RN and RT, both R-0 retrainings
    of the same cell on CPU, identical except runtime_s (a free determinism
    check; RL's (a) rows train at 60 epochs and are not compared)."""
    harvest = Path(p["harvest"]).name
    twin_name = TWIN_PAYLOAD_OF_HARVEST.get(harvest)
    twin_path = data_root / twin_name if twin_name else None
    perms_here = (p.get("twin") or {}).get("perm_sha256")
    perms_committed = None
    if twin_path is not None and twin_path.exists():
        tw = json.loads(twin_path.read_text(encoding="utf-8"))
        perms_committed = (tw.get("twin") or {}).get("perm_sha256") or tw.get("perm_sha256")
    perm_equal = (perms_here is not None and perms_committed is not None
                  and {str(k): v for k, v in perms_here.items()} == {str(k): v for k, v in perms_committed.items()})
    a_rows = {}
    for c in cells:
        if c.get("features") == rl.BASE_ARM and c.get("capacity") == rl.GATE_CAPACITY and not c.get("shuffled") \
                and c.get("reader") in ("RN", "RT") and c.get("offset") == rl.GATE_OFFSET:
            a_rows.setdefault(int(c["seed"]), {})[c["reader"]] = c
    a_identity = {}
    for seed, by_reader in sorted(a_rows.items()):
        if "RN" in by_reader and "RT" in by_reader:
            a, b = by_reader["RN"], by_reader["RT"]
            diff = sorted(k for k in set(a) | set(b) if k not in ("runtime_s", "reader", "reader_params")
                          and json.dumps(a.get(k), sort_keys=True, default=str) != json.dumps(b.get(k), sort_keys=True, default=str))
            a_identity[str(seed)] = {"identical_except_runtime": not diff, "differing_fields": diff}
    return {"twin_perm_sha256_equal_to_committed": bool(perm_equal), "committed_twin_payload": twin_name,
            "perm_sha256_here": perms_here, "perm_sha256_committed": perms_committed,
            "rn_rt_fresh_a_rows": a_identity,
            "rn_rt_fresh_a_rows_all_identical": bool(a_identity) and all(v["identical_except_runtime"] for v in a_identity.values())}


def write_word(out_path: Path, payload: dict) -> Path:
    """The word payload: the registered out name under results/real with a clean
    tracked tree and this file git-tracked; any other name under results/ is
    refused; outside results/ a scratch write."""
    out_path = Path(out_path).resolve()
    registered = out_path == (REAL / REGISTERED_OUT).resolve()
    if rl._under_results(out_path) and not registered:
        raise SystemExit(f"{out_path.name} is not the registered out {REGISTERED_OUT} — an unregistered name may not be written under results/")
    head, porcelain = _git(strict=registered)
    if registered:
        if porcelain:
            raise SystemExit("the tracked tree is not clean — the registered word refuses to write:\n" + "\n".join(porcelain))
        if not _tool_tracked():
            raise SystemExit("the instrument is not git-tracked — commit the registration first")
        if out_path.exists():
            raise SystemExit(f"{out_path.name} exists — the registered word is written once; a rewrite needs a dated reason and a removal by hand")
        if Path(payload["inputs"]["data_root"]).resolve() != REAL.resolve():
            raise SystemExit(f"the registered word reads the committed companions under {REAL}, not {payload['inputs']['data_root']} — refusing")
    payload = dict(payload)
    payload["registered"] = registered
    payload["provenance"] = {
        "instrument_sha256": _sha(Path(__file__)), "reader_lens_sha256": payload["frozen_chain"]["reader_lens_sha256"],
        "git_commit": head, "git_status_tracked": porcelain,
        "numpy_version": np.__version__, "python_version": platform.python_version(), "platform": platform.platform(),
        "out": out_path.name,
    }
    rl._write_lf(out_path, json.dumps(payload, indent=1) + "\n")
    return out_path


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--conclude", nargs=2, required=True, metavar=("PRIMARY", "REPLICATION"),
                    help="the two s1 payloads of the frozen instrument (readers_s1.json then readers_s1_r.json)")
    ap.add_argument("--out", required=True, help=f"the word payload; the registered name is results/real/{REGISTERED_OUT}")
    ap.add_argument("--data-root", default=str(REAL), help="where the Phase-3 companions live (tests override)")
    return ap


def main() -> None:
    args = build_parser().parse_args()
    out = conclude(Path(args.conclude[0]), Path(args.conclude[1]), Path(args.data_root))
    path = write_word(Path(args.out), out)
    print(json.dumps({"word": out["word"]["word"], "labels": {k: (v["label"], v["licence"]) for k, v in out["labels"].items()},
                      "void": out["word"]["void_cells"], "written": str(path)}, indent=1))


if __name__ == "__main__":
    main()
