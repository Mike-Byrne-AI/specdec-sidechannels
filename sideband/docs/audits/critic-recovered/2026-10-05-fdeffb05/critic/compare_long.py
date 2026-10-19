import os
for v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ[v] = "4"
import sys, json, io, contextlib
sys.path.insert(0, "src"); sys.path.insert(0, "tools")
from pathlib import Path
import run_reader_lens as rl
mine = json.load(open(sys.argv[1]))
R = Path("results/real")
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    tool = rl.conclude_from(R / "readers_s3.json", R / "readers_s3_r.json", long_pair=(R / "readers_long_s3.json", R / "readers_long_s3_r.json"),
                            lens_pair=(R / "lens_s3.json", R / "lens_s3_r.json"))
saved = json.load(open(sys.argv[2]))
norm = lambda o: json.loads(json.dumps(o, default=str))
print("tool == saved conclude_readers_long.json:", norm(tool) == norm(saved))
k = tool["k2"]
print("tool K-2", k["word"], "| surv", k["survives_stronger"], "| split", k["split"], "| void", k["void_cells"], "| narrowed", k["narrowed_cells"], "| not", k["not_narrowed_cells"], "| s1 trig", k["s1_trigger_readers"], "| pending", k["s1_pending"], "| reopened", k["reopened"], "| rl_runs(readers labels)", tool["readers_long_runs"])
print("mine K-2", mine["word"])
keymap = {"D": "d_fplus_b_vs_fplus_r", "Mt": "mt_fplus_b_vs_fplus", "Mn_r": "mn_r_fplus_r_vs_fplus", "Mf": "mf_fplus_vs_a", "Mfx": "mfx_fplus_vs_linear_a", "Mc": "mc_fplus_vs_c"}
pays = {}
for role, suf in (("primary", ""), ("replication", "_r")):
    p1 = json.load(open(R / ("readers_s3" + suf + ".json"))); p2 = json.load(open(R / ("readers_long_s3" + suf + ".json")))
    pays[role] = {**p1["per_reader_space"], **p2["per_reader_space"]}
maxd, n = 0.0, 0
for role in ("primary", "replication"):
    for rs, x in mine["R"][role].items():
        prs = pays[role][rs]
        for kk, r in x["R"].items():
            if r is None:
                continue
            row = next(m for m in prs[keymap[kk]] if m["offset"] == 2 and m["capacity"] == "mlp256")
            vals = [(r["m"], row["margin"]), (r["ci"][0], row["ci95"][0]), (r["ci"][1], row["ci95"][1])] + [(r["per"][str(s)], row["per_seed_margin"][str(s)]) for s in (0, 1, 2)]
            for a, b in vals:
                maxd = max(maxd, abs(a - b)); n += 1
        rv = prs["reader_valid"]
        for a, b in ((x["rv"]["mf_up"], rv["mf_gate_ci_upper"]), (x["rv"]["mfx_up"], rv["mfx_gate_ci_upper"]), (x["rv"]["min_gap"], rv["min_acc_minus_floor"])):
            maxd = max(maxd, abs(a - b)); n += 1
        if bool(rv["ok"]) != bool(x["rv"]["ok"]) or prs["best_epochs"] != x["best"]: print("mismatch rv/best", role, rs)
alltool = {**tool["labels"], **tool.get("labels_readers_long", {})}
for rs, v in mine["labels"].items():
    t = alltool[rs]
    same = t["label"] == v["label"] and t["licence"] == v["licence"] and (t["mt_fires_triple"]["primary"], t["mt_fires_triple"]["replication"]) == tuple(v["mt_triple"])
    if rs.startswith("RL") or not same:
        print(rs, "tool", t["label"], t["licence"], t["licence_reason"], "| mine", v["label"], v["licence"], v["reasons"], "| agree", same)
print("all nine agree:", all(alltool[rs]["label"] == v["label"] and alltool[rs]["licence"] == v["licence"] for rs, v in mine["labels"].items()))
print("rerun identity (readers vs lens):", {r: tool["r0_linear_a_rerun"][r]["all_identical"] for r in ("primary", "replication")})
print("max |tool - critic| over %d numbers: %.3g" % (n, maxd))
