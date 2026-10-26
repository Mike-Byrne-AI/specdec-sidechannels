"""Pure helpers for experiments/errata_recompute.py (experiments/ERRATA_PROTOCOL.md).

No side effects at import, no torch, no file writes: every function here takes
its inputs as arguments so tests/test_errata_recompute.py can exercise it on
synthetic data. The protocol pins which amber function each row uses; the
helpers wrap those functions (passed in as callables) and apply the pinned
rules exactly as written.
"""

from __future__ import annotations

import hashlib
import re
import subprocess
from pathlib import Path

import numpy as np

# ----------------------------------------------------------------------------
# git / provenance
# ----------------------------------------------------------------------------


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args]).decode().strip()


def blob_id(repo: Path, head: str, path: str) -> str:
    """Blob/tree id of `path` at `head`; raises CalledProcessError (quietly) for paths not in that commit."""
    return subprocess.check_output(["git", "-C", str(repo), "rev-parse", f"{head}:{path}"],
                                   stderr=subprocess.DEVNULL).decode().strip()


def dirty_tracked(repo: Path) -> list[str]:
    """Porcelain lines for tracked files that differ from HEAD (untracked excluded)."""
    out = git(repo, "status", "--porcelain", "--untracked-files=no")
    return [ln for ln in out.splitlines() if ln.strip()]


def sha256_lf(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


# ----------------------------------------------------------------------------
# rules
# ----------------------------------------------------------------------------


def rounds_to(x: float, text: str, nd: int) -> bool:
    """`x` printed with `nd` decimals equals `text` (the claim at its printed precision)."""
    return f"{float(x):.{nd}f}" == text


def status(ok: bool) -> str:
    return "CONFIRMED" if ok else "CORRECTED"


# ----------------------------------------------------------------------------
# E3: loops and repetition
# ----------------------------------------------------------------------------


def loop_flags(gen_rows: list[np.ndarray], loop_fraction, W: int, P: int, t: float) -> dict:
    """Pinned loop rule: row LOOPED iff loop_fraction(row, W, P)[0] >= t."""
    fracs, periods, tokens_in = [], [], []
    for g in gen_rows:
        frac, per = loop_fraction(g, window=W, max_period=P)
        fracs.append(float(frac)); periods.append(int(per)); tokens_in.append(int(round(frac * len(g))))
    flags = [f >= t for f in fracs]
    return {"W": W, "P": P, "t": t, "flags": flags, "fracs": fracs, "periods": periods,
            "tokens_in_loop": tokens_in, "n_looped": int(sum(flags)), "tokens_in_loop_total": int(sum(tokens_in))}


def grid_settings(Ws=(64, 128, 192, 256), Ps=(16, 32, 64, 128), ts=(0.25, 0.5, 0.75)) -> list[tuple[int, int, float]]:
    return [(W, P, t) for W in Ws for P in Ps if P < W for t in ts]


def loop_grid(gen_rows, loop_fraction) -> list[dict]:
    out = []
    for W, P, t in grid_settings():
        r = loop_flags(gen_rows, loop_fraction, W, P, t)
        out.append({"W": W, "P": P, "t": t, "n_looped": r["n_looped"], "tokens_in_loop": r["tokens_in_loop_total"]})
    return out


def repeat_4gram_share(gen_rows: list[np.ndarray], n: int = 4) -> tuple[int, int]:
    """Harvest definition: positions i >= n-1 whose n-gram ending at i also ends at some j < i
    in the same row; denominator sum_r max(len_r - (n-1), 0)."""
    num = den = 0
    for g in gen_rows:
        a = [int(x) for x in g]
        seen: set[tuple[int, ...]] = set()
        for i in range(n - 1, len(a)):
            key = tuple(a[i - n + 1:i + 1])
            if key in seen:
                num += 1
            seen.add(key)
        den += max(len(a) - (n - 1), 0)
    return num, den


def distinct_ngram_stats(gen_rows: list[np.ndarray], distinct_ngram_ratio, n: int = 4) -> dict:
    ratios, distinct, total = [], 0, 0
    for g in gen_rows:
        tot = max(len(g) - n + 1, 0)
        if tot == 0:
            continue
        r = float(distinct_ngram_ratio(g, n)); ratios.append(r)
        distinct += int(round(r * tot)); total += tot
    return {"rows": len(ratios), "unweighted_mean_ratio": float(np.mean(ratios)) if ratios else None,
            "pooled_distinct": distinct, "pooled_total": total,
            "pooled_ratio": distinct / total if total else None}


# ----------------------------------------------------------------------------
# E4: stratified rates
# ----------------------------------------------------------------------------


def stratified_rates(rows: list[tuple[np.ndarray, np.ndarray, bool]], amber_bits) -> dict:
    """rows = [(ranks_r, log2q_r, looped_r)] in row order. Per stratum: concatenated amber,
    per-archive amber, AC-under-draft, and the pinned deltas."""
    out = {}
    for name, flag in (("all", None), ("looped", True), ("nonlooped", False)):
        sel = [(r, q) for r, q, f in rows if flag is None or f == flag]
        if not sel:
            out[name] = {"N": 0, "rows": 0}; continue
        ranks = np.concatenate([r for r, _ in sel]); q = np.concatenate([q for _, q in sel])
        N = int(ranks.size)
        concat = amber_bits(ranks) / N
        per_archive = sum(amber_bits(r) for r, _ in sel) / N
        ac = float(-q.astype(np.float64).mean())
        out[name] = {"N": N, "rows": len(sel), "amber_concat": float(concat), "amber_perarchive": float(per_archive),
                     "ac": ac, "delta_concat": float(concat - ac), "rel_perarchive": float(per_archive / ac - 1)}
    return out


# ----------------------------------------------------------------------------
# E5 / E10: throughput definitions
# ----------------------------------------------------------------------------


def rate_stats(units: list[float], seconds: list[float]) -> dict:
    units = np.asarray(units, float); seconds = np.asarray(seconds, float)
    per = units / seconds
    return {"n": int(units.size), "weighted": float(units.sum() / seconds.sum()), "unweighted": float(per.mean()),
            "median": float(np.median(per)), "min": float(per.min()), "max": float(per.max()),
            "units_total": float(units.sum()), "seconds_total": float(seconds.sum())}


# ----------------------------------------------------------------------------
# E6: stall rule
# ----------------------------------------------------------------------------


def stall_split(lengths: list[float], seconds: list[float], f: float) -> dict:
    L = np.asarray(lengths, float); S = np.asarray(seconds, float)
    v = L / S; med = float(np.median(v)); stalled = v < f * med
    clean_L, clean_S = L[~stalled].sum(), S[~stalled].sum()
    return {"f": f, "aggregate": float(L.sum() / S.sum()), "median_v": med, "n_rows": int(L.size),
            "n_stalled": int(stalled.sum()), "seconds_stalled": float(S[stalled].sum()), "seconds_total": float(S.sum()),
            "clean": float(clean_L / clean_S) if clean_S else None,
            "stalled_rows": [int(i) for i in np.flatnonzero(stalled)]}


# ----------------------------------------------------------------------------
# E9: depth table from a P2b row
# ----------------------------------------------------------------------------

BUCKETS = ((2, 2), (3, 8), (9, 16), (17, 64))


def depth_table(row: dict) -> dict:
    """Primary definition: per symbol class / per rank denominators. Alternative: all positions."""
    n = int(row["n"]); sc = row["symbol_counts"]; byr = row["C_desync_by_rank"]
    d1 = row["desyncs"]["A"]; nA = int(sc["A"]); nC = int(sc["C"])
    primary = {"1": (d1 / nA) if nA else None}
    alt = {"1": d1 / n}
    alt_c = {}                                   # desync_r / all C symbols: informational, for matching printed figures
    for r in range(2, 65):
        e = byr.get(str(r))
        if e is None:
            continue
        primary[str(r)] = (e["desync"] / e["n"]) if e["n"] else None
        alt[str(r)] = e["desync"] / n
        alt_c[str(r)] = (e["desync"] / nC) if nC else None
    buckets = {}
    for lo, hi in BUCKETS:
        ds = sum(byr[str(r)]["desync"] for r in range(lo, hi + 1) if str(r) in byr)
        ns = sum(byr[str(r)]["n"] for r in range(lo, hi + 1) if str(r) in byr)
        buckets[f"{lo}-{hi}"] = {"desync": int(ds), "n": int(ns), "primary": (ds / ns) if ns else None, "alt": ds / n}
    return {"n": n, "symbol_counts": {k: int(v) for k, v in sc.items()}, "overall": row["desync_total"] / n, "desyncs_A": int(d1),
            "primary": primary, "alt": alt, "alt_c": alt_c, "buckets": buckets}


# ----------------------------------------------------------------------------
# E11: crafted archives and the sentinel probe
# ----------------------------------------------------------------------------


class WorkStarted(Exception):
    """Raised by the patched symbol expansion / stepper: work proportional to the declared length began."""


ERRATA_MODEL = {"id": "errata-test", "snapshot": None, "dtype": "fp32"}
ERRATA_VOCAB = 128256


def _params():
    from amber.rac_codec import CoderParams
    return CoderParams(tie_margin=0.0, tie_topm=2, max_rank=64, vocab_bits=max(1, (ERRATA_VOCAB - 1).bit_length()))


def craft_hf_json(length: int) -> bytes:
    """An hf-kind JSON archive framed exactly as build_archive frames it, valid except for `length`."""
    import json as _json

    from amber.codec import MAGIC, VERSION, header_digest, payload_digest
    from amber.real.archive import KIND, content_digest, hf_fingerprint
    payload = b""
    header = {
        "magic": MAGIC, "version": VERSION, "kind": KIND, "model": dict(ERRATA_MODEL), "vocab_size": ERRATA_VOCAB,
        "prompt_ids": [1], "length": int(length), "n_corrections": 0, "payload_bits": 0, "coder": "gamma",
        "tie_margin": 0.0, "tie_topm": 2, "max_rank": 64, "payload_sha": payload_digest(payload),
        "content_sha": content_digest(np.asarray([1], np.int32)), "fingerprint": hf_fingerprint(dict(ERRATA_MODEL), ERRATA_VOCAB),
    }
    header["header_sha"] = header_digest(header)
    hj = _json.dumps(header, sort_keys=True).encode()
    return MAGIC.encode() + len(hj).to_bytes(4, "big") + hj + payload


def craft_v3(length: int) -> bytes:
    from amber.binformat import pack
    from amber.real.archive import hf_fingerprint
    return pack(model_id=ERRATA_MODEL["id"], snapshot=None, dtype="fp32",
                fingerprint8=bytes.fromhex(hf_fingerprint(dict(ERRATA_MODEL), ERRATA_VOCAB)), vocab_size=ERRATA_VOCAB,
                coder="gamma", p=_params(), first_token=1, prompt_len=1, length=int(length), n_corrections=0,
                payload=b"", content_sha8=bytes(8))


def craft_v4(length: int) -> bytes:
    from amber.binformat import CTX_RESET, pack_session
    from amber.real.archive import hf_fingerprint
    return pack_session(model_id=ERRATA_MODEL["id"], snapshot=None, dtype="fp32",
                        fingerprint8=bytes.fromhex(hf_fingerprint(dict(ERRATA_MODEL), ERRATA_VOCAB)), vocab_size=ERRATA_VOCAB,
                        coder="gamma", p=_params(), ctx_mode=CTX_RESET,
                        turns=[{"prompt_len": 1, "gen_len": int(length), "first_token": 1}], n_corrections=0,
                        payload=b"", content_sha8=bytes(8))


def probe(decoder, blob: bytes, archive_module) -> dict:
    """Call `decoder(blob, make_stepper)` with payload_to_symbols and the stepper both raising WorkStarted.
    Outcome: 'refused' (ValueError first), 'work_started', or the exception type name."""
    def raiser(*a, **k):
        raise WorkStarted()

    def make_stepper():
        return raiser
    orig = archive_module.payload_to_symbols
    archive_module.payload_to_symbols = raiser
    try:
        decoder(blob, make_stepper)
        return {"outcome": "returned", "message": None}
    except WorkStarted:
        return {"outcome": "work_started", "message": None}
    except ValueError as e:
        return {"outcome": "refused", "message": str(e)}
    except Exception as e:  # noqa: BLE001 — any other type is recorded, never hidden
        return {"outcome": type(e).__name__, "message": str(e)}
    finally:
        archive_module.payload_to_symbols = orig


# ----------------------------------------------------------------------------
# E12 / E13: text helpers
# ----------------------------------------------------------------------------


def count_lines_containing(paths: list[Path], needle: str) -> int:
    n = 0
    for p in paths:
        n += sum(1 for ln in p.read_text(encoding="utf-8").splitlines() if needle in ln)
    return n


def parse_arxiv_meta(html: str) -> dict:
    import html as _html

    def metas(name: str) -> list[str]:
        return [_html.unescape(m.group(1)) for m in re.finditer(rf'<meta\s+name="{name}"\s+content="([^"]*)"', html)]
    titles = metas("citation_title"); abstracts = metas("citation_abstract")
    return {"title": titles[0] if titles else None, "authors": metas("citation_author"),
            "abstract": abstracts[0] if abstracts else None,
            "pmatic_count_in_page": len(re.findall("pmatic", html, flags=re.I))}


# ----------------------------------------------------------------------------
# E15 (second batch): expected desync rates from a rank histogram and a P2b row
# ----------------------------------------------------------------------------

R_MAX = 64          # = experiments/p2b_escape_robustness.R_MAX and the P4 archives' max_rank; the recompute checks both
C_RANKS = tuple(str(r) for r in range(2, R_MAX + 1))


def rank_histogram(ranks, r_max: int = R_MAX) -> dict:
    """Counts by coded rank: '1' (A), '2'..'<r_max>' (C), 'X' (above r_max), and 'N' (total)."""
    r = np.asarray(ranks).astype(np.int64)
    h = {str(k): int((r == k).sum()) for k in range(1, r_max + 1)}
    h["X"] = int((r > r_max).sum()); h["N"] = int(r.size)
    return h


def rank_rates(row: dict, r_max: int = R_MAX) -> dict:
    """Per-rank desync probabilities of a P2b (theta, m) row: '1' = desyncs.A / symbol_counts.A,
    '2'..'<r_max>' = C_desync_by_rank[r].desync / .n, 'X' = desyncs.X / symbol_counts.X; None where the denominator is 0."""
    sc = row["symbol_counts"]; byr = row["C_desync_by_rank"]; d = row["desyncs"]
    p = {"1": (d["A"] / sc["A"]) if sc["A"] else None}
    for r in range(2, r_max + 1):
        e = byr.get(str(r)); p[str(r)] = (e["desync"] / e["n"]) if (e and e["n"]) else None
    p["X"] = (d["X"] / sc["X"]) if sc["X"] else None
    return p


def setcoded_rates(row: dict, r_max: int = R_MAX) -> dict:
    """Per-rank rates under P2b's set-coded C variant: rank r takes its bucket's desync / n,
    bucket b = floor(log2(r - 1)) (ranks 2^b + 1 .. 2^(b + 1)). '1' and 'X' carry no rate."""
    by = row["setcoded_C"]["by_bucket"]; p = {"1": None, "X": None}
    for r in range(2, r_max + 1):
        e = by.get(str(int(np.floor(np.log2(r - 1))))); p[str(r)] = (e["desync"] / e["n"]) if (e and e["n"]) else None
    return p


def _class_keys(classes) -> list[str]:
    keys = []
    if "1" in classes:
        keys.append("1")
    if "C" in classes:
        keys += list(C_RANKS)
    if "X" in classes:
        keys.append("X")
    return keys


def expected_rate(h: dict, p: dict, classes=("1", "C", "X")) -> dict:
    """sum_r h(r) p(r) / N over the chosen classes ('1' = A, 'C' = ranks 2..64, 'X'). A rank with
    h(r) > 0 and no rate raises ValueError (the row is then UNRECOMPUTABLE)."""
    num = 0.0; by = {}
    for k in _class_keys(classes):
        if not h.get(k):
            continue
        if p.get(k) is None:
            raise ValueError(f"no desync rate at rank {k} (h = {h[k]})")
        by[k] = h[k] * p[k]; num += by[k]
    return {"rate": num / h["N"], "one_in": (h["N"] / num) if num else None, "expected_desyncs": num, "N": h["N"], "by_rank": by}


def _hazard_table(p: dict, classes, r_max: int = R_MAX) -> np.ndarray:
    tab = np.zeros(r_max + 2)                      # index r for r in 1..r_max, index r_max + 1 for X
    for k in _class_keys(classes):
        if p.get(k) is not None:
            tab[r_max + 1 if k == "X" else int(k)] = p[k]
    return tab


def fail_rate_exact(rank_rows: list, p: dict, classes=("1", "C", "X"), r_max: int = R_MAX) -> dict:
    """1 - mean_a prod_(t in a) (1 - p(r_t)) over archives' own rank sequences (no approximation).
    Ranks outside `classes` contribute no hazard; a rank with no rate in a used class raises."""
    for ranks in rank_rows:
        r = np.asarray(ranks).astype(np.int64)
        for k in _class_keys(classes):
            sel = (r > r_max) if k == "X" else (r == int(k))
            if sel.any() and p.get(k) is None:
                raise ValueError(f"no desync rate at rank {k}")
    tab = _hazard_table(p, classes, r_max); surv = []
    for ranks in rank_rows:
        r = np.minimum(np.asarray(ranks).astype(np.int64), r_max + 1)
        surv.append(float(np.prod(1.0 - tab[r])))
    surv = np.asarray(surv)
    return {"fail_rate": float(1.0 - surv.mean()), "expected_fails": float((1.0 - surv).sum()), "archives": int(surv.size)}


def fail_rate_poisson(mean_len: float, rate: float) -> float:
    """1 - exp(-L * rate): the constant-hazard approximation at the mean archive length."""
    return float(1.0 - np.exp(-mean_len * rate))


def class_bucket(key: str) -> str:
    """Group a rank key ('1', '2'.., 'X') or a P4 class name ('A', 'C2'.., 'X') into A, C2, C3, C4, C5, C6-64, X."""
    if key in ("1", "A"):
        return "A"
    if key == "X":
        return "X"
    r = int(key[1:]) if key.startswith("C") else int(key)
    return f"C{r}" if r <= 5 else "C6-64"


def shares_by_class(weights: dict) -> dict:
    """{bucket: share} from {rank key or class name: weight}, buckets as class_bucket."""
    tot = {}
    for k, w in weights.items():
        tot[class_bucket(k)] = tot.get(class_bucket(k), 0.0) + float(w)
    s = sum(tot.values())
    return {k: (v / s if s else None) for k, v in sorted(tot.items())}


# ----------------------------------------------------------------------------
# E16 (second batch): order differences at depth and the near-tie gap against a budget
# ----------------------------------------------------------------------------

SLOT_BUCKETS = ((0, 0), (1, 1), (2, 7), (8, 15), (16, 63))


def order_diff_events(enc_idx, enc_val, dec_idx, R: int = R_MAX) -> dict:
    """Positions where the decoder's top-R order differs from the encoder's (E8c's definition). At each: the first
    differing slot j (0-based), the decoder's token there, its encoder slot k over the full dump width (-1 if absent)
    and g = |enc_val[j] - enc_val[k]| (nan if absent): the encoder gap between the two tokens competing for slot j."""
    neq = enc_idx[:, :R] != dec_idx[:, :R]; diff = neq.any(1); pos = np.flatnonzero(diff)
    if pos.size == 0:
        z = np.zeros(0, int)
        return {"pos": z, "j": z, "k": z, "tok": z, "g": np.zeros(0)}
    j = neq[pos].argmax(1); tok = dec_idx[pos, j]
    hit = enc_idx[pos] == tok[:, None]; found = hit.any(1); k = np.where(found, hit.argmax(1), -1)
    g = np.where(found, np.abs(enc_val[pos, j] - enc_val[pos, np.maximum(k, 0)]), np.nan)
    return {"pos": pos, "j": j, "k": k, "tok": tok, "g": g}


def gap_summary(ev: dict, budget: float, two_tau: float | None) -> dict:
    g = np.asarray(ev["g"], float); fin = np.isfinite(g); gf = g[fin]; j = np.asarray(ev["j"]); k = np.asarray(ev["k"])
    q = (lambda x: float(np.quantile(gf, x))) if gf.size else (lambda x: None)
    buckets = {}
    for lo, hi in SLOT_BUCKETS:
        sel = (j >= lo) & (j <= hi); gs = g[sel & fin]
        buckets[f"{lo}-{hi}" if lo != hi else str(lo)] = {"n": int(sel.sum()), "max_g": float(gs.max()) if gs.size else None,
                                                            "above_budget": int((gs > budget).sum())}
    return {"n_diff": int(np.asarray(ev["pos"]).size), "n_absent": int((~fin).sum()),
            "n_nonadjacent": int((fin & (k != j + 1)).sum()),
            "g_quantiles": {"min": q(0.0), "p50": q(0.5), "p90": q(0.9), "p99": q(0.99), "max": q(1.0)},
            "by_slot_bucket": buckets, "budget": budget, "count_above_budget": int((gf > budget).sum()),
            "two_tau_census": two_tau, "count_above_two_tau_census": int((gf > two_tau).sum()) if two_tau is not None else None}


# ----------------------------------------------------------------------------
# second batch, post-critic fields (amendment of 2026-10-11 UTC)
# ----------------------------------------------------------------------------

CLASSES = ("A", "C", "X")


def _class_masks(r: np.ndarray, r_max: int = R_MAX) -> dict:
    return {"A": r == 1, "C": (r >= 2) & (r <= r_max), "X": r > r_max}


def compensator(exposures: list, p: dict, observed: dict, r_max: int = R_MAX) -> dict:
    """Observed first desyncs by class against the expected count over the positions actually decoded:
    E_c = sum over the exposures of p(r_t) at positions of class c (A rank 1, C ranks 2..r_max, X above).
    Per class and all-class: observed, expected, ratio O/E, z = (O - E) / sqrt(E); plus the like-for-like
    predicted first-desync shares E_c / E_total."""
    tab = _hazard_table(p, ("1", "C", "X"), r_max); E = {c: 0.0 for c in CLASSES}
    for ranks in exposures:
        r = np.minimum(np.asarray(ranks).astype(np.int64), r_max + 1); h = tab[r]
        for c, m in _class_masks(r, r_max).items():
            E[c] += float(h[m].sum())
    out = {}
    for c in CLASSES:
        O = float(observed.get(c, 0)); e = E[c]
        out[c] = {"observed": O, "expected": e, "ratio": (O / e) if e else None, "z": float((O - e) / np.sqrt(e)) if e else None}
    O_all = sum(float(observed.get(c, 0)) for c in CLASSES); E_all = sum(E.values())
    out["all"] = {"observed": O_all, "expected": E_all, "ratio": (O_all / E_all) if E_all else None,
                  "z": float((O_all - E_all) / np.sqrt(E_all)) if E_all else None}
    out["predicted_first_desync_shares"] = {c: (E[c] / E_all if E_all else None) for c in CLASSES}
    return out


def observed_by_class(first_desync_class_counts: dict) -> dict:
    """P4's first-desync class keys ('A', 'C2'.., 'X') summed into A, C, X."""
    out = {c: 0 for c in CLASSES}
    for k, n in first_desync_class_counts.items():
        out["C" if k.startswith("C") else k] += int(n)
    return out


def gap_share_below(gaps, thresholds: dict) -> dict:
    g = np.asarray(gaps, float)
    return {k: {"threshold": float(t), "share": float((g < t).mean()) if g.size else None, "n": int(g.size)} for k, t in thresholds.items()}


def aligned_deltas(enc_idx, enc_val, dec_idx, dec_val, R: int = R_MAX, chunk: int = 2048) -> np.ndarray:
    """delta[t, s] = the decoder's value of the encoder's slot-s token minus that token's encoder value, the token
    found over the full decoder dump width; nan where absent."""
    n = enc_idx.shape[0]; out = np.full((n, R), np.nan)
    for a in range(0, n, chunk):
        b = min(a + chunk, n)
        hit = enc_idx[a:b, :R, None] == dec_idx[a:b, None, :]
        found = hit.any(2); pos = hit.argmax(2)
        dv = np.take_along_axis(dec_val[a:b], pos, axis=1)
        out[a:b] = np.where(found, dv - enc_val[a:b, :R], np.nan)
    return out


DELTA_BUCKETS = ((0, 0), (1, 7), (8, 15), (16, 63))


def drift_summary(delta: np.ndarray, budget: float, q: float = 0.999) -> dict:
    """The q-quantile of |delta| by slot bucket, and the adjacent-pair drift |delta[j] - delta[j + 1]| (the change of
    the pair's gap from encoder to decoder) counted above the budget, against the number of pairs."""
    ad = np.abs(delta); by = {}
    for lo, hi in DELTA_BUCKETS:
        x = ad[:, lo:hi + 1]; x = x[np.isfinite(x)]
        by[f"{lo}-{hi}" if lo != hi else str(lo)] = {"n": int(x.size), "q": float(np.quantile(x, q)) if x.size else None}
    pd = np.abs(delta[:, :-1] - delta[:, 1:]); fin = np.isfinite(pd)
    return {"quantile": q, "abs_delta_q_by_slot_bucket": by, "absent": int((~np.isfinite(delta)).sum()), "budget": float(budget),
            "adjacent_pairs": int(fin.sum()), "adjacent_pairs_drift_above_budget": int((pd[fin] > budget).sum())}


def distinct_prefixes(tokens: np.ndarray, positions, seq_len_minus_1: int) -> int:
    """Distinct token prefixes (through the position's offset) among kept positions t = seq * (L - 1) + offset."""
    seen = set()
    for t in np.asarray(positions, dtype=np.int64):
        s, o = int(t // seq_len_minus_1), int(t % seq_len_minus_1)
        seen.add(tuple(int(x) for x in tokens[s, :o + 1]))
    return len(seen)


# ----------------------------------------------------------------------------
# third batch (E17, E18, E19)
# ----------------------------------------------------------------------------


def label_multiple(label: float, tau: float) -> int:
    """The printed threshold as a multiple of the calibrated tau, rounded to the nearest integer."""
    return int(round(label / tau))


def bits_per_token(total_bytes: float, tokens: int) -> float:
    return 8.0 * total_bytes / tokens


def dictionary_effect(none: float, with_dict: float) -> float:
    """Relative reduction of a comparator's rate by the dictionary: (none - dict) / none."""
    return (none - with_dict) / none


def crossover_length(const_bits: float, comparator_rate: float, payload_rate: float):
    """F-12's rate law const/L + payload meets a flat comparator at L* = const / (comparator - payload); None if never."""
    return (const_bits / (comparator_rate - payload_rate)) if comparator_rate > payload_rate else None


def gap_edges_equal_count(gaps, n_bins: int) -> np.ndarray:
    """Interior edges at the quantiles 1/n .. (n-1)/n of the gaps (values outside the extremes fall in the end bins)."""
    q = np.arange(1, n_bins) / n_bins
    return np.quantile(np.asarray(gaps, float), q)


def gap_edges_log(gaps, n_bins: int) -> np.ndarray:
    """Interior edges log-spaced from the smallest positive gap to the largest."""
    g = np.asarray(gaps, float); lo = float(g[g > 0].min()); hi = float(g.max())
    return np.logspace(np.log10(lo), np.log10(hi), n_bins + 1)[1:-1]


def bin_index(x, edges) -> np.ndarray:
    return np.searchsorted(np.asarray(edges, float), np.asarray(x, float), side="right")


def binned_rates(gaps, desync, edges) -> dict:
    """Per bin: positions, desyncs and rate (None where the bin is empty)."""
    b = bin_index(gaps, edges); nb = len(edges) + 1; d = np.asarray(desync, bool)
    n = np.bincount(b, minlength=nb); k = np.bincount(b, weights=d.astype(float), minlength=nb)
    return {"n": [int(x) for x in n], "desync": [int(x) for x in k], "rate": [(float(k[i] / n[i]) if n[i] else None) for i in range(nb)]}


def poisson_ratio_interval(observed: float, expected: float, level: float = 0.95) -> dict:
    """Exact (Garwood) Poisson interval for the mean given `observed` events, divided by `expected`: the O/E interval."""
    from scipy.stats import chi2
    a = (1 - level) / 2; o = float(observed)
    lo = chi2.ppf(a, 2 * o) / 2 if o > 0 else 0.0; hi = chi2.ppf(1 - a, 2 * (o + 1)) / 2
    return {"ratio": o / expected, "low": float(lo / expected), "high": float(hi / expected), "level": level}


def apply_rates(gaps, edges, rates: dict) -> tuple[np.ndarray, int]:
    """Hazard per gap from its bin's rate; a gap in an empty bin takes the nearest non-empty bin's rate. Returns (hazard, n_in_empty)."""
    r = np.array([np.nan if x is None else x for x in rates["rate"]], float); filled = np.flatnonzero(~np.isnan(r))
    b = bin_index(gaps, edges); empty = np.isnan(r[b])
    if empty.any():
        nearest = filled[np.abs(filled[None, :] - b[empty][:, None]).argmin(1)]
        out = r[b].copy(); out[empty] = r[nearest]
    else:
        out = r[b]
    return out, int(empty.sum())
