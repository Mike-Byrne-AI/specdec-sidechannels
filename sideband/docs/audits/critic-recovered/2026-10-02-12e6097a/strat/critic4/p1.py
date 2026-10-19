# Independent recompute of the OQ-9 stratified coverage read (critic round 4). numpy + stdlib only.
# Does not import sideband or the repo tools. Reads only the state files and payloads.
import json, sys, hashlib
import numpy as np

ROOT = "C:/Users/<user>/Desktop/Research/sideband"
STRATA = ["covered_1", "covered_2_4", "covered_5p", "cur_unseen", "prev_unseen", "both_unseen"]
UNIONS = {"covered": STRATA[:3], "fallback": STRATA[3:], "all": STRATA}
SCOPES = STRATA + list(UNIONS)
ARMS = ["history", "free_tok", "history_tok", "free_bigram_b", "free_bigram_a", "history_bigram_b",
        "history_bigram_a", "free_all", "history_all", "pt_only", "free_bigram_pt", "history_tok_pt", "history_bigram_pt"]
TWIN_ARMS = ARMS[:9]
DIMS = {"history": 1025, "free_tok": 1025, "history_tok": 2049, "free_bigram_b": 2049, "free_bigram_a": 2049,
        "history_bigram_b": 3073, "history_bigram_a": 3073, "free_all": 3073, "history_all": 4097,
        "pt_only": 82, "free_bigram_pt": 2130, "history_tok_pt": 2130, "history_bigram_pt": 3154}
BUDGETS = [8, 16, 32]
NG = 16
K = 8
FLOOR = 0.05
PAIRS = [("address_beyond_token", "history_tok", "free_tok"), ("gate_eq", "history_tok", "FREE"),
         ("address_beyond_bigram", "HIST", "FREE"), ("bigram_gain", "FREE", "free_tok"),
         ("pt_gain", "free_bigram_pt", "FREE"), ("d_pt", "history_tok", "free_bigram_pt"),
         ("d_eq_pt", "history_tok_pt", "free_bigram_pt"), ("d_add_pt", "history_bigram_pt", "free_bigram_pt"),
         ("pt_only-free_tok", "pt_only", "free_tok"), ("history_tok_pt-history_tok", "history_tok_pt", "history_tok"),
         ("history_bigram_pt-history_tok_pt", "history_bigram_pt", "history_tok_pt")]
CR = bytes([13])
NL = chr(10)

def read_jsonl(path):
    with open(path, "rb") as fh:
        raw = fh.read()
    assert CR not in raw, path
    lines = raw.decode("utf-8").split(NL)
    assert lines[-1] == ""
    lines = lines[:-1]
    hdr = json.loads(lines[0])
    rows = [json.loads(x) for x in lines[1:]]
    return hdr, rows, hashlib.sha256(raw).hexdigest()

BOOT_IDX = np.random.default_rng(0).integers(0, 30, size=(2000, 30))

def ratio_ci(h, n):
    s = h[BOOT_IDX].sum(axis=1); t = n[BOOT_IDX].sum(axis=1)
    v = t > 0
    lo, hi = np.percentile(s[v] / t[v], [2.5, 97.5])
    return float(lo), float(hi), int((~v).sum())

def delta_ci(ha, hb, n):
    d = float((ha - hb).sum() / n.sum())
    dd = (ha - hb)[BOOT_IDX].sum(axis=1); t = n[BOOT_IDX].sum(axis=1)
    v = t > 0
    lo, hi = np.percentile(dd[v] / t[v], [2.5, 97.5])
    return d, float(lo), float(hi), int((~v).sum())

def reading(d, lo, hi):
    if lo > 0 and d >= FLOOR:
        return "SIGNAL"
    if hi < 0:
        return "NEGATIVE"
    return "NOT-SHOWN"

def straddle(lo, hi):
    return bool(lo <= FLOOR <= hi)
