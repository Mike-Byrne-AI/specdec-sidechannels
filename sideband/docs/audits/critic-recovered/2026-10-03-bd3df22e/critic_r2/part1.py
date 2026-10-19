# Independent recompute of the R2 payloads from their state files (critic, recompute mode).
import sys, json, math
sys.path.insert(0, "src")
import numpy as np
from sideband.stats import paired_cluster_delta_ci, cluster_bootstrap_ci
from sideband.harvest import split_of_prompt

STRATA = ["covered_1", "covered_2_4", "covered_5p", "cur_unseen", "prev_unseen", "both_unseen"]
UNIONS = {"covered": STRATA[:3], "fallback": STRATA[3:], "all": STRATA}
SCOPES = STRATA + list(UNIONS)
BUDGETS = [8, 16, 32]
LB = 16; MAT = 0.05; NB = 2000; SEED = 0; L = 16; K = 8
TWIN = ["history", "free_tok", "history_tok", "free_bigram_b", "free_bigram_a", "history_bigram_b", "history_bigram_a", "free_all", "history_all"]
R2 = ["free_r2", "history_tok_r2", "history_bigram_r2", "free_backoff", "free_replay", "replay_cur", "replay_zerofit", "h_only", "free_h", "history_all_h"]
RIDGE_R2 = [a for a in R2 if a != "replay_zerofit"]
LAMS = [0.1, 1.0, 10.0, 100.0, 1000.0, 10000.0, 100000.0]
KTAGS = ["0", "2", "8", "32", "128", "512", "inf"]
FREE, HIST = "free_bigram_b", "history_bigram_b"
PAIRS = [("address_beyond_token", "history_tok", "free_tok"), ("gate_eq", "history_tok", FREE), ("address_beyond_bigram", HIST, FREE),
         ("bigram_gain", FREE, "free_tok"), ("shrinkage", "free_r2", FREE), ("gate_eq_r2", "history_tok_r2", "free_r2"),
         ("gate_eq_r2_twinarm", "history_tok", "free_r2"), ("d_add_r2", "history_bigram_r2", "free_r2"),
         ("backoff-free_bigram", "free_backoff", FREE), ("replay-free_bigram", "free_replay", FREE),
         ("free_r2-free_backoff", "free_r2", "free_backoff"), ("free_r2-free_replay", "free_r2", "free_replay"),
         ("replay_cur-free_tok", "replay_cur", "free_tok"), ("replay_zerofit-free_tok", "replay_zerofit", "free_tok"),
         ("history_tok_r2-history_tok", "history_tok_r2", "history_tok"), ("h_only-free_tok", "h_only", "free_tok"),
         ("h_only-history_tok", "h_only", "history_tok"), ("free_h-free_r2", "free_h", "free_r2"),
         ("d_eq_h", "history_bigram_r2", "free_h"), ("d_add_h", "history_all_h", "free_h"),
         ("history_all_h-history_bigram_r2", "history_all_h", "history_bigram_r2")]


def load(path):
    lines = open(path, encoding="utf-8").read().splitlines()
    return json.loads(lines[0]), [json.loads(x) for x in lines[1:] if x.strip()]


def reading(d):
    if d["lo"] > 0 and d["delta"] >= MAT:
        return "SIGNAL"
    if d["hi"] < 0:
        return "NEGATIVE"
    return "NOT-SHOWN"


def straddle(d):
    return d["lo"] <= MAT <= d["hi"]
