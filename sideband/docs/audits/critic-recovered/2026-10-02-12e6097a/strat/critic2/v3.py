import json, hashlib, datetime, sys
sys.path.insert(0, "src")
D = r"C:\Users\<user>\AppData\Local\Temp\claude\c--Users-<user>-Desktop-Research-sideband\12e6097a-8666-465a-b5a3-e76024a56cff\scratchpad\strat\smoke"
for nm in ("strat_smoke.meta.json", "strat_smoke2.meta.json"):
    m = json.load(open(D + "\\" + nm, encoding="utf-8"))
    print("==", nm)
    print(" instrument", m["instrument_sha256"][:12], "git", m["git_commit"], "tracked", m.get("git_status_tracked"))
    print(" started", datetime.datetime.fromtimestamp(m["started_unix"]).strftime("%H:%M:%S"), "runtime_s %.1f" % m["runtime_s"])
    print(" n_positions", m["n_positions"])
    print(" table_coverage test", {k: round(v, 4) if isinstance(v, float) else v for k, v in m["table_coverage"]["test"].items()})
    print(" encoding", m["encoding_selected"], m["encoding_source"])
    vt = m["val_table"]; ls = m["lambda_selected"]
    for a in ("free_bigram_b", "free_bigram_a"): print("  val-best", a, round(vt[a][str(ls[a])], 4), "lam", ls[a])
    print(" lambdas PT", {a: ls[a] for a in ("pt_only", "free_bigram_pt", "history_tok_pt", "history_bigram_pt")})
    print(" grid_edge", m["lambda_grid_edge"])
    print(" blas", m.get("blas"), "numpy", m["numpy_version"])
    print(" frozen", m["frozen_twin"], m["frozen_instrument"])
cur = open(r"C:\Users\<user>\Desktop\Research\sideband\tools\run_prefetch_strat.py", "rb").read()
print("current tool sha (raw)", hashlib.sha256(cur).hexdigest()[:12], "LF", hashlib.sha256(cur.replace(b"\r\n", b"\n")).hexdigest()[:12], "has CRLF", b"\r\n" in cur)
R = r"C:\Users\<user>\Desktop\Research\sideband\results\real"
for nm in ("prefetch_bigram_s3.json", "prefetch_bigram_s3_r.json"):
    p = json.load(open(R + "\\" + nm, encoding="utf-8")); pv = p["provenance"]
    print("==", nm, "instrument", pv["instrument_sha256"][:12], "enc", pv["encoding_selected"], "n_state_rows", p["n_state_rows"])
    print(" n_positions", pv["n_positions"])
    tc = pv["table_coverage"]
    print(" table_coverage test", {k: round(v, 4) if isinstance(v, float) else v for k, v in tc["test"].items()})
    print(" table_coverage train", {k: round(v, 4) if isinstance(v, float) else v for k, v in tc["train"].items()})
    de = p["conclusion"]["deltas"]
    for k in ("gate_eq|B=16", "address_beyond_bigram|B=16"):
        d = de[k]; print(" ", k, "%+.4f [%+.4f, %+.4f]" % (d["delta"], d["lo"], d["hi"]), "needed", d["needed"], "-> positions", d["needed"] / 128)
    print(" lambdas", pv["lambda_selected"])
