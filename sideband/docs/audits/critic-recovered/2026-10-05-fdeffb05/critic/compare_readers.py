import os
for v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ[v] = "4"
import sys, json, io, contextlib
sys.path.insert(0, "src"); sys.path.insert(0, "tools")
from pathlib import Path
import run_reader_lens as rl
mine = json.load(open(sys.argv[1]))
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    tool = rl.conclude_from(Path("results/real/readers_s3.json"), Path("results/real/readers_s3_r.json"),
                            lens_pair=(Path("results/real/lens_s3.json"), Path("results/real/lens_s3_r.json")))
saved = json.load(open(sys.argv[2]))
norm = lambda o: json.loads(json.dumps(o, default=str))
print("tool == saved conclude_readers.json:", norm(tool) == norm(saved))
k = tool["k2"]
print("tool K-2", k["word"], "| surv", k["survives_stronger"], "| split", k["split"], "| void", k["void_cells"], "| narrowed", k["narrowed_cells"], "| not", k["not_narrowed_cells"], "| s1 trig", k["s1_trigger_readers"], "| pending", k["s1_pending"], "| reopened", k["reopened"], "| rl_runs", tool["readers_long_runs"])
print("mine K-2", mine["word"])
keymap = {"D": "d_fplus_b_vs_fplus_r", "Mt": "mt_fplus_b_vs_fplus", "Mn_r": "mn_r_fplus_r_vs_fplus", "Mf": "mf_fplus_vs_a", "Mfx": "mfx_fplus_vs_linear_a", "Mc": "mc_fplus_vs_c"}
pays = {r: json.load(open("results/real/" + f)) for r, f in (("primary", "readers_s3.json"), ("replication", "readers_s3_r.json"))}
maxd, n = 0.0, 0
for role in ("primary", "replication"):
    for rs, x in mine["R"][role].items():
        prs = pays[role]["per_reader_space"][rs]
        for kk, r in x["R"].items():
            if r is None:
                rows = [m for m in prs[keymap[kk]] if m["offset"] == 2 and m["capacity"] == "mlp256"]
                if rows: print("tool has", kk, "where critic has none", rs)
                continue
            row = next(m for m in prs[keymap[kk]] if m["offset"] == 2 and m["capacity"] == "mlp256")
            vals = [(r["m"], row["margin"]), (r["ci"][0], row["ci95"][0]), (r["ci"][1], row["ci95"][1])] + [(r["per"][str(s)], row["per_seed_margin"][str(s)]) for s in (0, 1, 2)]
            for a, b in vals:
                maxd = max(maxd, abs(a - b)); n += 1
            if row["n_clusters"] != 30 or row["n_seeds"] != 3: print("structural", role, rs, kk)
        rv = prs["reader_valid"]
        for a, b in ((x["rv"]["mf_up"], rv["mf_gate_ci_upper"]), (x["rv"]["mfx_up"], rv["mfx_gate_ci_upper"]), (x["rv"]["min_gap"], rv["min_acc_minus_floor"])):
            maxd = max(maxd, abs(a - b)); n += 1
        if bool(rv["ok"]) != bool(x["rv"]["ok"]) or prs["best_epochs"] != x["best"]: print("mismatch rv/best", role, rs)
for rs, v in mine["labels"].items():
    t = tool["labels"][rs]
    same = (t["label"] == v["label"] and t["licence"] == v["licence"] and t["mt_fires_triple"]["primary"] == v["mt_triple"][0] and t["mt_fires_triple"]["replication"] == v["mt_triple"][1])
    print(rs, "tool", t["label"], t["licence"], t["licence_reason"], "| mine", v["label"], v["licence"], "| agree", same)
print("rerun identity", {r: tool["r0_linear_a_rerun"][r]["all_identical"] for r in ("primary", "replication")})
rsc = {r: sorted({round(c["reader_params"]["rescale"]["c_hz"], 6) for c in pays[r]["cells"] if c.get("reader") == "RN" and (c.get("reader_params") or {}).get("rescale", {}).get("c_hz")}) for r in pays}
mhz = {r: sorted({(round(c["reader_params"]["rescale"]["m_hz"], 1), round(c["reader_params"]["rescale"]["m_slots_aligned"], 3)) for c in pays[r]["cells"] if c.get("reader") == "RN" and (c.get("reader_params") or {}).get("rescale", {}).get("c_hz")}) for r in pays}
tw = {r: sorted({json.dumps(c["reader_params"]["towers"]) for c in pays[r]["cells"] if c.get("reader") == "RT"}) for r in pays}
print("c_hz", rsc, "| m_hz, m_slots", mhz)
print("towers", tw)
print("max |tool - critic| over %d numbers: %.3g" % (n, maxd))
