#!/usr/bin/env python3
"""Critic, third batch, row E18: independent recompute of results/errata_recompute_3.json rows.E18.

Standalone: no imports from experiments/errata_* or amber. Raw np.load of the P1 shards, the `tokenizers`
library on the cached tokenizer.json (decode with skip_special_tokens=False, which must reproduce P5's
recorded all-row zstd figures exactly, else the text is not P5's), my own Elias-gamma bit count for
amber v0. Dictionaries are retrained (twice, to test determinism) and their sha256 / dict_id compared.
Also: the harvest's text (tokenizers' default skip_special_tokens=True, as its spot6.py/spot7.py decode)
to test the attribution of its 6.251 to the special-token literals, and the dictionary effect without them.
torch is blocked; no network.
"""
import sys

sys.modules["torch"] = None
import glob  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import zstandard  # noqa: E402
from tokenizers import Tokenizer  # noqa: E402

REPO = Path(__file__).resolve().parents[2]; RES = REPO / "results"
SIZES = (4096, 16384, 65536, 262144); SPLIT = 100


def jl(p):
    return json.loads((REPO / p).read_text(encoding="utf-8"))


def gamma_len(n):
    return 2 * int(n).bit_length() - 1


def amber_bits(ranks):
    bits = 0; gap = 0
    for r in ranks:
        if r == 1:
            gap += 1; continue
        bits += gamma_len(gap + 1) + gamma_len(int(r) - 1); gap = 0
    return bits


def rep_share(g):
    num = 0; seen = set(); a = [int(x) for x in g]
    for i in range(3, len(a)):
        k = tuple(a[i - 3:i + 1]); num += k in seen; seen.add(k)
    den = max(len(a) - 3, 0)
    return num / den if den else 0.0


def flatten(x, p=""):
    if isinstance(x, dict):
        for k, v in x.items():
            yield from flatten(v, f"{p}/{k}")
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from flatten(v, f"{p}[{i}]")
    else:
        yield p, x


def main():
    row = jl("results/errata_recompute_3.json")["rows"]["E18"]; pay = row["value"]
    tj = Path(pay["instrument_check"]["tokenizer_json"]); tj_sha = hashlib.sha256(tj.read_bytes()).hexdigest()
    tok = Tokenizer.from_file(str(tj))
    gm = jl("results/p1/generate/meta.json"); ids_by = {}; pl_by = {}
    for f in sorted(glob.glob(str(RES / "p1/generate/shard_*.npz"))):
        with np.load(f) as z:
            for i, r in enumerate(z["row"]):
                ids = z["ids"][i]; ids_by[int(r)] = ids[ids >= 0].astype(np.int64); pl_by[int(r)] = int(z["prompt_len"][i])
    rows = sorted(ids_by)
    full = {r: tok.decode(ids_by[r].tolist(), skip_special_tokens=False).encode("utf-8") for r in rows}
    gen = {r: tok.decode(ids_by[r][pl_by[r]:].tolist(), skip_special_tokens=False).encode("utf-8") for r in rows}
    full_h = {r: tok.decode(ids_by[r].tolist()).encode("utf-8") for r in rows}          # tokenizers default: skip_special_tokens=True
    glen = {r: len(ids_by[r]) - pl_by[r] for r in rows}
    train = [r for r in rows if r < SPLIT]; held = [r for r in rows if r >= SPLIT]; G = sum(glen[r] for r in held); Nall = sum(glen.values())
    p5 = jl("results/p5_binformat.json")["report"]; c0 = zstandard.ZstdCompressor(level=19)
    text_check = {"all_rows_per_archive": 8 * sum(len(c0.compress(full[r])) for r in rows) / Nall,
                  "p5_json_per_archive": p5["zstd19_full_text_per_archive_bits_per_generated_token"],
                  "all_rows_concat": 8 * len(c0.compress(b"".join(full[r] for r in rows))) / Nall,
                  "p5_json_concat": p5["zstd19_full_text_concatenated_bits_per_generated_token"]}
    text_check["exact"] = (text_check["all_rows_per_archive"] == text_check["p5_json_per_archive"] and text_check["all_rows_concat"] == text_check["p5_json_concat"])
    # dictionaries, twice
    def train_all(src):
        out = {}
        for s in SIZES:
            d = zstandard.train_dictionary(s, [src[r] for r in train], level=19); out[str(s)] = d
        return out
    D1 = train_all(full); D2 = train_all(full)
    dg1 = zstandard.train_dictionary(16384, [gen[r] for r in train], level=19); dg2 = zstandard.train_dictionary(16384, [gen[r] for r in train], level=19)
    info = {k: {"bytes": len(d.as_bytes()), "dict_id": d.dict_id(), "sha256": hashlib.sha256(d.as_bytes()).hexdigest()} for k, d in D1.items()}
    info["gen_16384"] = {"bytes": len(dg1.as_bytes()), "dict_id": dg1.dict_id(), "sha256": hashlib.sha256(dg1.as_bytes()).hexdigest()}
    determinism = {k: D1[k].as_bytes() == D2[k].as_bytes() for k in D1}; determinism["gen_16384"] = dg1.as_bytes() == dg2.as_bytes()
    comp = {"none": c0, **{k: zstandard.ZstdCompressor(level=19, dict_data=d) for k, d in D1.items()}}
    cg = zstandard.ZstdCompressor(level=19, dict_data=dg1)
    bpt = lambda b, n: 8.0 * b / n  # noqa: E731
    em = jl("results/p5/encode_meta.json")["per_row"]; fixed = p5["fixed_header_bytes"]
    arch = {k: bpt(sum(len(c.compress(full[r])) for r in held), G) for k, c in comp.items()}
    amber_arch = bpt(sum(em[str(r)]["bytes"] for r in held), G)
    concat = {k: bpt(len(comp[k].compress(b"".join(full[r] for r in held))), G) for k in ("none", "16384")}
    cm = p5["curve_model"]
    cross = {k: cm["per_archive_const_bits"] / (v - cm["payload_gen_rate"]) for k, v in concat.items()}
    cross_all_rows_printed_formula = cm["per_archive_const_bits"] / (p5["zstd19_full_text_concatenated_bits_per_generated_token"] - cm["payload_gen_rate"])
    # amber v0 content
    ranks = {}
    for f in sorted(glob.glob(str(RES / "p1/draft/shard_*.npz"))):
        with np.load(f) as z:
            off = z["offsets"]
            for i, r in enumerate(z["row"]):
                ranks[int(r)] = z["ranks"][off[i]:off[i + 1]].astype(np.int64)
    allr = np.concatenate([ranks[r] for r in rows]); p1 = jl("results/p1_divergence.json")["row"]
    amber_all = amber_bits(allr) / allr.size
    amber_held = amber_bits(np.concatenate([ranks[r] for r in held])) / G
    gconc = {"none": bpt(len(c0.compress(b"".join(gen[r] for r in held))), G), "gen_16384": bpt(len(cg.compress(b"".join(gen[r] for r in held))), G)}
    # sessions
    sess = {}
    for k in (8, 16):
        meta = jl(f"results/p6/k{k}_m0/meta.json")["sessions"]; sel = [s for s in meta.values() if min(s["rows"]) >= SPLIT]
        gt = sum(s["gen_tokens"] for s in sel)
        zn = bpt(sum(len(c0.compress(b"".join(full[r] for r in s["rows"]))) for s in sel), gt)
        zd = bpt(sum(len(comp["16384"].compress(b"".join(full[r] for r in s["rows"]))) for s in sel), gt)
        a = bpt(sum(s["bytes"] for s in sel), gt)
        sess[f"k{k}"] = {"sessions": len(sel), "gen_tokens": gt, "gen_tokens_match_rows": gt == sum(glen[r] for s in sel for r in s["rows"]),
                         "amber_v4_reset": a, "zstd_none": zn, "zstd_16384": zd, "multiple_none": zn / a, "multiple_16384": zd / a, "effect": (zn - zd) / zn,
                         "printed_all_rows": jl("results/p6_sessions.json")["report"]["by_k_mode"][f"k{k}_m0"]}
    rep_rows = [r for r in held if rep_share(ids_by[r][pl_by[r]:]) < 0.5]; Gr = sum(glen[r] for r in rep_rows)
    rep = {"rows": len(rep_rows), "gen_tokens": Gr, "amber_v3_arch": bpt(sum(em[str(r)]["bytes"] for r in rep_rows), Gr),
           "zstd_arch_16384": bpt(sum(len(comp["16384"].compress(full[r])) for r in rep_rows), Gr),
           "zstd_arch_none": bpt(sum(len(c0.compress(full[r])) for r in rep_rows), Gr)}
    eff = {"arch": (arch["none"] - arch["16384"]) / arch["none"], "session16": sess["k16"]["effect"], "session8": sess["k8"]["effect"],
           "concat": (concat["none"] - concat["16384"]) / concat["none"], "gen_concat": (gconc["none"] - gconc["gen_16384"]) / gconc["none"]}
    mine = {"instrument_check": {"G": G, "N": int(allr.size), "amber_v0_json": p1["amber_v0_bits_per_token"], "amber_v0_recomputed": amber_all,
                                 "ok": amber_all == p1["amber_v0_bits_per_token"] and allr.size == p1["positions"], "rows_held": len(held), "rows_train": len(train),
                                 "tokenizer_json": str(tj), "tokenizer_json_sha256": tj_sha, "zstandard_version": zstandard.__version__},
            "split": {"G": G, "held_rows": [held[0], held[-1]], "train_rows": [train[0], train[-1]]}, "dictionaries": info,
            "per_archive": {"zstd": arch, "amber_v3": amber_arch, "amber_v3_payload_only": bpt(sum(em[str(r)]["bytes"] - fixed for r in held), G),
                            "fixed_header_bytes": fixed, "zstd_16384_amortised": arch["16384"] + bpt(info["16384"]["bytes"], G),
                            "ratio_zstd_over_amber": {k: v / amber_arch for k, v in arch.items()},
                            "printed_all_rows": {"zstd19_full_text_per_archive": p5["zstd19_full_text_per_archive_bits_per_generated_token"], "amber_v3": p5["v3_total_bits_per_generated_token"]}},
            "concatenated_full_text": {"zstd": concat, "crossover_L": cross, "curve_model": cm,
                                       "printed_all_rows": {"zstd19_full_text_concatenated": p5["zstd19_full_text_concatenated_bits_per_generated_token"]}},
            "content": {"amber_v0_held": amber_held, "zstd_gen_concat": gconc, "multiple": {k: v / amber_held for k, v in gconc.items()},
                        "printed_all_rows": {"amber_v0": p1["amber_v0_bits_per_token"], "zstd19": p1["zstd19_bits_per_token"]}},
            "sessions": sess, "repetition_split": rep, "effects": eff, "threshold": 0.1, "amber_v3_arch": amber_arch, "zstd_arch_none": arch["none"],
            **{f"zstd_arch_{s}": arch[str(s)] for s in SIZES}, "rep_below_half_amber_v3_arch": rep["amber_v3_arch"], "rep_below_half_zstd_arch_16384": rep["zstd_arch_16384"],
            "effect_arch": eff["arch"], "prediction_sources": pay["prediction_sources"], "pinned_rule_sites": ["DECISIONS.md:39-44", "FINDINGS.md:94"]}
    st = lambda e: "CORRECTED" if e > 0.10 else "CONFIRMED"  # noqa: E731
    my_status = {"status": st(eff["arch"]), "status_by_claim_site": {
        "DECISIONS.md:39-44 (D-6, per archive)": st(eff["arch"]), "FINDINGS.md:94 (F-12, zstd per archive)": st(eff["arch"]),
        "FINDINGS.md:101, README.md:46, OPEN_QUESTIONS.md:31, DECISIONS.md:132 (3.4x per session, k=16)": st(eff["session16"]),
        "FINDINGS.md:91, README.md:45, docs/BLUEPRINT.md:81, OPEN_QUESTIONS.md:32 (crossover vs zstd concatenated)": st(eff["concat"]),
        "FINDINGS.md:58, FINDINGS.md:62, README.md:31, docs/BLUEPRINT.md:50 (7.6x, concatenated generated text)": st(eff["gen_concat"])}}
    fa, fb = dict(flatten(mine)), dict(flatten(pay)); maxd = 0.0; worst = None; neq = []
    for k in set(fa) & set(fb):
        x, y = fa[k], fb[k]
        if isinstance(x, (str, bool)) or isinstance(y, (str, bool)) or x is None or y is None:
            if x != y:
                neq.append((k, x, y))
            continue
        d = abs(float(x) - float(y))
        if d > maxd:
            maxd, worst = d, k
    # audit: the harvest's text (special tokens skipped) and the effect without the literals
    Dh = {s: zstandard.train_dictionary(s, [full_h[r] for r in train], level=19) for s in (4096, 16384, 65536)}
    harvest = {"none": bpt(sum(len(c0.compress(full_h[r])) for r in held), G),
               **{str(s): bpt(sum(len(zstandard.ZstdCompressor(level=19, dict_data=d).compress(full_h[r])) for r in held), G) for s, d in Dh.items()},
               "dict_bytes": {str(s): len(d.as_bytes()) for s, d in Dh.items()}}
    harvest["effect_16384"] = (harvest["none"] - harvest["16384"]) / harvest["none"]
    lit = {"literal_bytes_held": sum(len(full[r]) - len(full_h[r]) for r in held),
           "n_bot": sum(full[r].count(b"<|begin_of_text|>") for r in held), "n_eot": sum(full[r].count(b"<|end_of_text|>") for r in held)}
    # unstripped text compressed with the dictionary trained on unstripped text vs stripped/stripped: does the dictionary absorb the literals?
    lit["dict16_unstripped"] = arch["16384"]; lit["dict16_stripped"] = harvest["16384"]
    # the harvest's repetition split as its spot7.py computes it (denominator len(g), not len(g) - 3; text with special tokens skipped)
    def rep_frac_spot7(g):
        seen = set(); m = 0; a = [int(x) for x in g]
        for t in range(3, len(a)):
            k = tuple(a[t - 3:t + 1]); m += k in seen; seen.add(k)
        return m / max(1, len(a))
    sel7 = [r for r in held if rep_frac_spot7(ids_by[r][pl_by[r]:]) < 0.5]; G7 = sum(glen[r] for r in sel7)
    harvest["rep_below_half_spot7"] = {"rows": len(sel7), "amber_v3_arch": bpt(sum(em[str(r)]["bytes"] for r in sel7), G7),
                                       "zstd_arch_16384": bpt(sum(len(zstandard.ZstdCompressor(level=19, dict_data=Dh[16384]).compress(full_h[r])) for r in sel7), G7)}
    # effects at every scale on text without the special-token literals (the dictionary trained on the same stripped text)
    ch = zstandard.ZstdCompressor(level=19, dict_data=Dh[16384]); strip = {}
    for k in (8, 16):
        meta = jl(f"results/p6/k{k}_m0/meta.json")["sessions"]; sel = [s for s in meta.values() if min(s["rows"]) >= SPLIT]
        zn = sum(len(c0.compress(b"".join(full_h[r] for r in s["rows"]))) for s in sel); zd = sum(len(ch.compress(b"".join(full_h[r] for r in s["rows"]))) for s in sel)
        strip[f"session{k}"] = (zn - zd) / zn
    cn = len(c0.compress(b"".join(full_h[r] for r in held))); cd = len(ch.compress(b"".join(full_h[r] for r in held)))
    strip["concat"] = (cn - cd) / cn; strip["arch"] = harvest["effect_16384"]
    harvest["effects_without_literals"] = strip
    out = {"text_matches_p5": text_check, "dict_training_deterministic": determinism, "compare_value": {"n": len(set(fa) & set(fb)), "max_abs_diff": maxd, "worst": worst,
           "nonnumeric_unequal": neq, "only_in_payload": sorted(set(fb) - set(fa)), "only_in_mine": sorted(set(fa) - set(fb))},
           "status_mine": my_status, "status_payload": {"status": row["status"], "status_by_claim_site": row["status_by_claim_site"]},
           "cross_all_rows_printed_formula": cross_all_rows_printed_formula, "harvest_text_skip_special": harvest, "literals": lit,
           "prediction": row["prediction"]}
    text = json.dumps(out, indent=1, default=float) + "\n"
    Path(__file__).with_suffix(".out.json").write_text(text, encoding="utf-8", newline="\n")
    print(text, end="")


if __name__ == "__main__":
    main()
