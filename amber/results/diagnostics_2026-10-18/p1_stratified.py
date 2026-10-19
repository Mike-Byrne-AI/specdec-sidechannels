"""P1 stratified by the E3 loop rule: greedy divergence, amber and AC bits per token, and zstd-19
bits per token on each stratum (diagnostic of 2026-10-18, after the cold read of that date).

The headline figures of F-8 (6.78% divergence, 0.4738 amber bits per token, 3.618 zstd-19 bits per
token) are mixtures over 200 greedy generations of which 125 end in an exact periodic tail (F-14
row E3). F-14 row E4 already splits the amber and AC rates by that rule. This script adds the two
figures E4 did not report: the greedy divergence of the rows without loops, and zstd-19 on the
text of those rows alone, so the "7.6x below zstd-19" multiple can be read per stratum.

Definitions are the P1 instrument's (experiments/p1_divergence.py): divergence is the share of
positions whose draft rank is not 1; amber bits are P1.amber_bits over the rank sequence; AC bits
are -mean(log2 q) under the draft; zstd-19 bits per token are 8 x compressed bytes of the decoded
generated text, concatenated in shard order, divided by the stratum's positions. The loop rule is
E3's pinned setting (errata_lib.loop_flags with W=128, P=64, t=0.5). Every all-rows figure is
cross-checked against results/p1_divergence.json and the per-stratum amber/AC deltas against the
E4 payload's grid entry at that setting; a failed cross-check exits 2 and writes nothing.

Reads: results/p1/generate, results/p1/draft, results/p1_divergence.json, results/errata_recompute.json,
the draft tokenizer from the local Hugging Face cache (offline). CPU only (torch is blocked as in
the errata protocol). Writes p1_stratified.json beside this file, deterministic (no timestamps).
Run from the repository root: python results/diagnostics_2026-10-18/p1_stratified.py
EXPECTED (below) was pinned from the first run of 2026-10-18 and is asserted on every run since
(exit 1 on a mismatch).
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.modules["torch"] = None  # type: ignore[assignment]  # CPU-only guard, as experiments/errata_recompute.py line 17

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "experiments"))

import errata_lib as L  # noqa: E402
import p1_divergence as P1  # noqa: E402  (amber_bits)
from amber.real.divergence import load_generated, load_rank  # noqa: E402
from amber.real.longhorizon import loop_fraction  # noqa: E402

RESULTS = ROOT / "results"
OUT = Path(__file__).with_suffix(".json")
LOOP_W, LOOP_P, LOOP_T = 128, 64, 0.5   # E3's pinned setting (experiments/errata_recompute.py line 77)
STRATA = (("all", None), ("looped", True), ("nonlooped", False))

EXPECTED: dict | None = {   # pinned 2026-10-18 from the first run's print (six decimals; multiples to three)
    "n_looped": 125,
    "divergence_all": 0.067834, "divergence_nonlooped": 0.133978, "divergence_looped": 0.032781,
    "amber_nonlooped": 0.892912, "ac_nonlooped": 0.809391,
    "zstd19_all": 3.618122, "zstd19_nonlooped": 7.491921, "zstd19_looped": 1.7465,
    "zstd19_over_amber_all": 7.636, "zstd19_over_amber_nonlooped": 8.39,
}


def _tokenizer(model_id: str):
    try:
        from transformers import AutoTokenizer
        return AutoTokenizer.from_pretrained(model_id, local_files_only=True), "AutoTokenizer.from_pretrained(local_files_only=True)"
    except Exception:  # the errata run's offline fallback (E7 amendment): the cached snapshot directory
        from huggingface_hub import try_to_load_from_cache

        from amber.real.capture import _load_tokenizer
        tj = try_to_load_from_cache(model_id, "tokenizer.json")
        tj_path = Path(tj) if isinstance(tj, str) else None
        if tj_path is None or not tj_path.exists():
            raise FileNotFoundError(f"tokenizer.json for {model_id} is not in the local HF cache")
        return _load_tokenizer(str(tj_path.parent)), "amber.real.capture._load_tokenizer(cached snapshot dir)"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True, check=True).stdout.strip()


def _version(module: str) -> str:
    from importlib.metadata import PackageNotFoundError, version
    try:
        return version(module)
    except PackageNotFoundError:
        return "not installed"


def main() -> int:
    seqs = load_generated(RESULTS / "p1")                      # [(row, ids, prompt_len)]
    gen = {r: ids[pl:] for r, ids, pl in seqs}
    draft = load_rank(RESULTS / "p1", "draft")
    per = draft["per_prompt"]                                   # shard order, as the instrument concatenates
    gen_rows = [gen[p["row"]] for p in per]
    flags = L.loop_flags(gen_rows, loop_fraction, LOOP_W, LOOP_P, LOOP_T)
    rows = [(p["rank"], p["log2q"], f) for p, f in zip(per, flags["flags"])]

    rates = L.stratified_rates(rows, P1.amber_bits)             # amber_concat, amber_perarchive, ac (float64), deltas
    div: dict = {}
    for name, flag in STRATA:
        sel = [r for r, _, f in rows if flag is None or f == flag]
        rk = np.concatenate(sel)
        div[name] = {"rows": len(sel), "positions": int(rk.size), "divergence_rate": float((rk != 1).mean())}

    tok, tok_how = _tokenizer(draft["meta"]["model"])
    import zstandard
    zs: dict = {}
    for name, flag in STRATA:
        text = "".join(tok.decode(gen[p["row"]]) for p, f in zip(per, flags["flags"]) if flag is None or f == flag)
        b = text.encode("utf-8")
        zb = len(zstandard.ZstdCompressor(level=19).compress(b))
        n = div[name]["positions"]
        zs[name] = {"utf8_bytes": len(b), "zstd19_bytes": zb, "zstd19_bits_per_token": 8 * zb / n,
                    "zstd19_over_amber_concat": (8 * zb / n) / rates[name]["amber_concat"],
                    "zstd19_over_ac": (8 * zb / n) / rates[name]["ac"]}

    # cross-checks against the committed record
    p1 = json.loads((RESULTS / "p1_divergence.json").read_text(encoding="utf-8"))["row"]
    errata = json.loads((RESULTS / "errata_recompute.json").read_text(encoding="utf-8"))["rows"]
    e3 = errata["E3"]["value"]
    e4grid = [g for g in errata["E4"]["value"]["grid"] if g["W"] == LOOP_W and g["P"] == LOOP_P and g["t"] == LOOP_T]
    log2q_all = np.concatenate([q for _, q, _ in rows])
    checks = {
        "positions_equal_p1_json": div["all"]["positions"] == p1["positions"],
        "divergence_all_equals_p1_json": abs(div["all"]["divergence_rate"] - p1["divergence_rate"]) < 1e-12,
        "amber_all_equals_p1_json": abs(rates["all"]["amber_concat"] - p1["amber_v0_bits_per_token"]) < 1e-9,
        "ac_all_f32_equals_p1_json": abs(float(-log2q_all.mean()) - p1["ac_under_draft_bits_per_token"]) < 1e-9,
        "zstd19_all_equals_p1_json": abs(zs["all"]["zstd19_bits_per_token"] - p1["zstd19_bits_per_token"]) < 1e-9,
        "n_looped_equals_e3": flags["n_looped"] == e3["n_looped"],
        "tokens_in_loop_equals_e3": flags["tokens_in_loop_total"] == e3["tokens_in_loop"],
        "e4_grid_entry_found": len(e4grid) == 1,
        "delta_nonlooped_equals_e4": bool(e4grid) and abs(rates["nonlooped"]["delta_concat"] - e4grid[0]["delta_concat_nonlooped"]) < 1e-9,
        "delta_looped_equals_e4": bool(e4grid) and abs(rates["looped"]["delta_concat"] - e4grid[0]["delta_concat_looped"]) < 1e-9,
    }
    if not all(checks.values()):
        print("CROSS-CHECK FAILED:", {k: v for k, v in checks.items() if not v}, file=sys.stderr)
        return 2

    out = {
        "diagnostic": "P1 stratified by the E3 loop rule (2026-10-18)",
        "loop_rule": {"W": LOOP_W, "P": LOOP_P, "t": LOOP_T, "n_rows": len(rows), "n_looped": flags["n_looped"],
                      "tokens_in_loop_total": flags["tokens_in_loop_total"]},
        "divergence": div,
        "rates": rates,
        "zstd19": zs,
        "headline_vs_nonlooped": {
            "divergence_rate": [div["all"]["divergence_rate"], div["nonlooped"]["divergence_rate"]],
            "amber_concat_bits_per_token": [rates["all"]["amber_concat"], rates["nonlooped"]["amber_concat"]],
            "ac_bits_per_token": [rates["all"]["ac"], rates["nonlooped"]["ac"]],
            "zstd19_bits_per_token": [zs["all"]["zstd19_bits_per_token"], zs["nonlooped"]["zstd19_bits_per_token"]],
            "zstd19_over_amber_concat": [zs["all"]["zstd19_over_amber_concat"], zs["nonlooped"]["zstd19_over_amber_concat"]],
        },
        "cross_checks": checks,
        "tokenizer": {"model": draft["meta"]["model"], "loaded_by": tok_how, "decode": "tok.decode(generated ids), no skip_special_tokens, as p1_divergence.py"},
        "inputs": {
            "results/p1_divergence.json": _sha256(RESULTS / "p1_divergence.json"),
            "results/errata_recompute.json": _sha256(RESULTS / "errata_recompute.json"),
            "results/p1/generate": sorted(p.name for p in (RESULTS / "p1" / "generate").glob("*.npz")),
            "results/p1/draft": sorted(p.name for p in (RESULTS / "p1" / "draft").glob("*.npz")),
        },
        "provenance": {"git_head_at_run": _git("rev-parse", "HEAD"), "script": Path(__file__).name,
                       "numpy": np.__version__, "python": sys.version.split()[0],
                       "zstandard": zstandard.__version__, "transformers": _version("transformers"),
                       "tokenizers": _version("tokenizers")},
    }
    OUT.write_bytes((json.dumps(out, indent=1, sort_keys=True) + "\n").encode("utf-8"))

    summary = {
        "n_looped": out["loop_rule"]["n_looped"],
        "divergence_all": round(div["all"]["divergence_rate"], 6), "divergence_nonlooped": round(div["nonlooped"]["divergence_rate"], 6),
        "divergence_looped": round(div["looped"]["divergence_rate"], 6),
        "amber_nonlooped": round(rates["nonlooped"]["amber_concat"], 6), "ac_nonlooped": round(rates["nonlooped"]["ac"], 6),
        "zstd19_all": round(zs["all"]["zstd19_bits_per_token"], 6), "zstd19_nonlooped": round(zs["nonlooped"]["zstd19_bits_per_token"], 6),
        "zstd19_looped": round(zs["looped"]["zstd19_bits_per_token"], 6),
        "zstd19_over_amber_all": round(zs["all"]["zstd19_over_amber_concat"], 3),
        "zstd19_over_amber_nonlooped": round(zs["nonlooped"]["zstd19_over_amber_concat"], 3),
    }
    for k, v in summary.items():
        print(f"{k}: {v}")
    print("wrote", OUT.relative_to(ROOT).as_posix())
    if EXPECTED is not None and summary != EXPECTED:
        print("MISMATCH against the pinned EXPECTED:", {k: (summary.get(k), EXPECTED.get(k)) for k in set(summary) | set(EXPECTED) if summary.get(k) != EXPECTED.get(k)}, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
