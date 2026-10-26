"""Phase-2 harvest conventions: alignment, pair counting, probe split.

Single source of truth for the BLOCK-START ALIGNMENT registered in
docs/BLUEPRINT.md Phase 2 (2026-08-30). Both the GPU harvester
(sideband.real.shadow_telemetry) and every Phase-3 probe reader import these
functions; nothing may re-implement them (D-3 spirit).

The convention: anchor `a` carries what a spec-decode block start would have
when its last verified position is the one that produced p_a — telemetry
captured DURING the forward that output p_a, plus free-information summaries
OF p_a. The label at offset j is the token the target itself emitted j-1
positions later:

    label_index(a, j) = a + j - 1

so offset 1 is the token sampled FROM p_a (available-by-construction free
information — the probe-(a) home turf) and K-2's registered kill reads
offsets >= 2 only.
"""

from __future__ import annotations

GAMMA_DEFAULT = 4

# Probe split by PROMPT, pinned 2026-08-30 before any probe existed.
# prompt_idx % 7: {0..4} -> train, 5 -> val, 6 -> test  (210 -> 150/30/30).
_SPLIT_MOD = 7
_VAL_RESIDUE = 5
_TEST_RESIDUE = 6


def label_index(anchor: int, offset: int) -> int:
    """Token index labeling (anchor, offset). Offset is 1-based; offset 1 is
    the token sampled from the anchor's own p_a."""
    if anchor < 0:
        raise ValueError(f"anchor must be >= 0, got {anchor}")
    if offset < 1:
        raise ValueError(f"offset is 1-based, got {offset}")
    return anchor + offset - 1


def pairs_per_row(length: int, gamma: int = GAMMA_DEFAULT) -> int:
    """Number of (anchor, offset) pairs a continuation of `length` tokens
    yields: anchor a in [0, length), offset j in [1, gamma], label in range.
    For length >= gamma this is gamma*length - gamma*(gamma-1)/2."""
    if length < 0:
        raise ValueError(f"length must be >= 0, got {length}")
    return sum(max(0, length - (j - 1)) for j in range(1, gamma + 1))


def total_pairs(lengths, gamma: int = GAMMA_DEFAULT) -> int:
    return sum(pairs_per_row(int(n), gamma) for n in lengths)


def split_of_prompt(prompt_idx: int) -> str:
    """'train' | 'val' | 'test' for a prompt index, per the pinned rule."""
    if prompt_idx < 0:
        raise ValueError(f"prompt_idx must be >= 0, got {prompt_idx}")
    r = prompt_idx % _SPLIT_MOD
    if r == _VAL_RESIDUE:
        return "val"
    if r == _TEST_RESIDUE:
        return "test"
    return "train"


def verified_seed_files(harvest_dir) -> list[tuple[dict, "object"]]:
    """(meta, npz_path) per seed, with every npz verified against its
    committed meta sha256 — the ONLY sanctioned way for a Phase-3 consumer
    to open harvest data (evidence-chain standard: numbers that feed a K-2
    verdict must bind to the data version they were computed on)."""
    import hashlib
    import json
    from pathlib import Path

    harvest_dir = Path(harvest_dir)
    out = []
    prefixes = set()
    for mp in sorted(harvest_dir.glob("*_s*.meta.json")):
        prefixes.add(mp.name.split("_s")[0])
        meta = json.loads(mp.read_text())
        npz_path = harvest_dir / meta["npz_file"]
        sha = hashlib.sha256(npz_path.read_bytes()).hexdigest()
        if sha != meta["npz_sha256"]:
            raise SystemExit(f"{mp.name}: npz sha mismatch — refusing unbound harvest data")
        out.append((meta, npz_path))
    if not out:
        raise SystemExit(f"no harvest metas in {harvest_dir}")
    if len(prefixes) > 1:
        # A dir holding metas from two sources (e.g. shadow_s* and moe_s*)
        # would silently pool cross-source data into one "harvest".
        raise SystemExit(f"mixed harvest prefixes in {harvest_dir}: {sorted(prefixes)} — "
                         "one source per directory (S3 registration, 2026-08-31)")
    return out
