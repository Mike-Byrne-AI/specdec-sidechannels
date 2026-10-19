import sys, json
sys.path.insert(0, "src")
import numpy as np
from sideband.stats import paired_cluster_delta_ci as lib_delta, cluster_bootstrap_ci as lib_ci
S = r"C:\Users\<user>\AppData\Local\Temp\claude\c--Users-<user>-Desktop-Research-sideband\12e6097a-8666-465a-b5a3-e76024a56cff\scratchpad\strat\smoke"
OUT = r"C:\Users\<user>\AppData\Local\Temp\claude\c--Users-<user>-Desktop-Research-sideband\12e6097a-8666-465a-b5a3-e76024a56cff\scratchpad\strat\critic2"
print("numpy", np.__version__)
def load_state(p):
    lines = open(p, encoding="utf-8").read().splitlines()
    h = json.loads(lines[0]); assert h["state_header"] is True
    return h, [json.loads(l) for l in lines[1:] if l.strip()]
hdr, rows = load_state(S + r"\strat_smoke2.json.state.jsonl")
payload = json.load(open(S + r"\strat_smoke2.json", encoding="utf-8"))
meta = json.load(open(S + r"\strat_smoke2.meta.json", encoding="utf-8"))
C = payload["conclusion"]; LAB = C["labels"]
print("rows", len(rows), "payload n_state_rows", payload["n_state_rows"], "header twin", hdr["twin"], "smoke", hdr["smoke"])
print("meta == payload provenance:", meta == payload["provenance"])
STRATA = ["covered_1", "covered_2_4", "covered_5p", "cur_unseen", "prev_unseen", "both_unseen"]
UN = {"covered": STRATA[:3], "fallback": STRATA[3:], "all": STRATA}
SCOPES = STRATA + ["covered", "fallback", "all"]
ARMS = ["history","free_tok","history_tok","free_bigram_b","free_bigram_a","history_bigram_b","history_bigram_a",
        "free_all","history_all","pt_only","free_bigram_pt","history_tok_pt","history_bigram_pt"]
BUD = [8, 16, 32]; MAT = 0.05; NB = 2000
enc = hdr["encoding"]; suf = {"prev_table": "b", "cur_table_at_prev": "a"}[enc]
FREE, HIST = "free_bigram_" + suf, "history_bigram_" + suf
print("encoding", enc, FREE, HIST)
cell = {}
for r in rows:
    assert set(r) == {"arm","budget","key","depth","gate","prompt_idx","stratum","hits","needed"}, r
    assert r["key"] == 1 and r["depth"] is None and r["stratum"] in STRATA and r["arm"] in ARMS and r["budget"] in BUD
    k = (r["arm"], r["budget"], r["stratum"]); g = (r["gate"], r["prompt_idx"])
    assert g not in cell.setdefault(k, {}), ("dup", k, g)
    assert 0 <= r["hits"] <= r["needed"] and r["needed"] > 0 and r["needed"] % 8 == 0
    cell[k][g] = (r["hits"], r["needed"])
prompts = sorted({r["prompt_idx"] for r in rows}); P = len(prompts)
gates = sorted({r["gate"] for r in rows})
print("prompts", P, "gates", len(gates), "arms", len({r["arm"] for r in rows}), "cells", len(cell))
