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
    tool = rl.conclude_from(Path("results/real/lens_s3.json"), Path("results/real/lens_s3_r.json"))
saved = json.load(open(sys.argv[2]))
def norm(o):
    return json.loads(json.dumps(o, default=str))
print("tool conclude == coordinator saved conclude_lens.json:", norm(tool) == norm(saved))
lab = tool["labels"]["R0|" + rl.SPACE_L3_BAL]
print("tool label", lab["label"], "licence", lab["licence"], "horizons", lab["horizons"], "reader_valid", lab["reader_valid"])
print("mine label", mine["label"], "horizons", mine["horizons"])
maxd = 0.0; n = 0
pays = {r: json.load(open("results/real/" + f)) for r, f in (("primary", "lens_s3.json"), ("replication", "lens_s3_r.json"))}
keymap = {"D": "d_fplus_b_vs_fplus_r", "Mt": "mt_fplus_b_vs_fplus", "Mn_r": "mn_r_fplus_r_vs_fplus", "Mf": "mf_fplus_vs_a",
          "Mfx": "mfx_fplus_vs_linear_a", "Mc": "mc_fplus_vs_c"}
for role in ("primary", "replication"):
    prs = pays[role]["per_reader_space"]["R0|" + rl.SPACE_L3_BAL]
    for k, r in mine["harvests"][role]["R"].items():
        kind, off, cap = k.split("|")
        if kind == "P":
            row = pays[role]["proxy"]["row"]
        else:
            row = next(m for m in prs[keymap[kind]] if m["offset"] == int(off) and m["capacity"] == cap)
        vals = [(r["m"], row["margin"]), (r["ci"][0], row["ci95"][0]), (r["ci"][1], row["ci95"][1])]
        vals += [(r["per"][str(s)] if str(s) in r["per"] else r["per"][s], row["per_seed_margin"][str(s)] if str(s) in row["per_seed_margin"] else row["per_seed_margin"][s]) for s in (0, 1, 2)]
        for a, b in vals:
            maxd = max(maxd, abs(a - b)); n += 1
        if row.get("n_clusters") != 30 or row.get("n_seeds") != 3:
            print("structural mismatch", role, k, row.get("n_clusters"), row.get("n_seeds"))
    rv = prs["reader_valid"]; mrv = mine["harvests"][role]["rv"]
    for a, b in ((mrv["mf_upper"], rv["mf_gate_ci_upper"]), (mrv["mfx_upper"], rv["mfx_gate_ci_upper"]), (mrv["min_gap"], rv["min_acc_minus_floor"])):
        maxd = max(maxd, abs(a - b)); n += 1
    print(role, "tool reader_valid ok", rv["ok"], "legs", rv["floor_ok"], rv["mf_ok"], rv["mfx_ok"], "| mine", mrv["ok"], "| best epochs tool", prs["best_epochs"], "mine", mine["harvests"][role]["best"])
    rid = pays[role]["riders"][rl.SPACE_L3_BAL]; me = mine["harvests"][role]["E"]
    for a, b in ((me["dE"], rid["amended_leg2"]["d_E"]), (me["ciE"][0], rid["amended_leg2"]["ci95_d_E"][0]), (me["ciE"][1], rid["amended_leg2"]["ci95_d_E"][1]),
                 (me["x_raw"], rid["x_raw_seed0"]), (mine["harvests"][role]["raw2"], rid["registered_leg2_raw"]["excess"])):
        maxd = max(maxd, abs(a - b)); n += 1
    for arm, e in me["E"].items():
        maxd = max(maxd, abs(e - rid["E"][arm])); n += 1
    print(role, "tool rider pass", rid["pass"], "leg1", rid["leg1_pass"], "leg2", rid["leg2_pass"], "raw leg2 note", rid["registered_leg2_raw"], "| x_raw sentence:", rid["x_raw_sentence"])
    tp = tool["lens"]["proxy"][role]
    print(role, "tool P fires", tp["fires"], "floors", tp["acc_minus_floor_per_seed"], "| mine", mine["harvests"][role]["P_fires"], mine["harvests"][role]["floors"])
    maxd = max(maxd, abs(tool["lens"]["ratio_to_f17"][role] - mine["harvests"][role]["ratio"]), abs(tool["lens"]["committed_l2_margin"][role] - mine["harvests"][role]["l2"])); n += 2
print("tool lens", tool["lens"]["proxy_label"], tool["lens"]["growth_over_l2"], "ratios", tool["lens"]["ratio_to_f17"], "L2", tool["lens"]["committed_l2_margin"])
print("mine lens", mine["lens"], mine["growth"])
print("max |tool - critic| over %d compared numbers: %.3g" % (n, maxd))
