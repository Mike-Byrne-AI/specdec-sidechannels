import sys, json, hashlib, subprocess
sys.path.insert(0, "src"); sys.path.insert(0, "tools")
import numpy as np
import e6_gate as e6, run_seed_replay as sr, run_noise_floor as nf
R = "results/real/"
def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()
def git(*a): return subprocess.run(["git", *a], capture_output=True, text=True).stdout.strip()
for f in ("k3_thresholds_arm3.json", "oq15c_thresholds_arm6.json"):
    d = json.load(open(R + f)); print(f, sha(R + f), d.get("kind"), d.get("arm"), d.get("selection_label"), [round(x, 6) for x in d["stop"]], d["stop_level"], round(d["extend"], 6), d["extend_level"], "blob", git("rev-parse", f"HEAD:{R}{f}"))
for s in ("k3_verdict_arm3", "k3_verdict_s1_arm3", "oq15c_verdict_arm6", "oq15c_verdict_s3_arm6"):
    m = json.load(open(R + s + ".meta.json", encoding="utf-8"))
    print(s, "seed", m["seed"], "thr", (m.get("thresholds_sha256") or "")[:12], "probe_arm", m.get("probe_arm"), "head_family", m.get("head_family"), "head_w", (m.get("head_weights_sha256") or "")[:12], "git", m["git_commit"][:12])
for pop in ("k3_s1", "oq15c_s3"):
    r = e6.evaluate(pop)
    for k, l in r["legs"].items(): print(pop, k, f"{l['delta']:+.6f} [{l['ci_lower']:+.6f}, {l['ci_upper']:+.6f}] gm {l['budget_guard_margin']:+.6f} holds {l['leg_holds']}")
    if pop == "k3_s1": print("   arm3 vs arm1", e6.pair(e6.per_prompt("k3_verdict_s1_arm3"), e6.per_prompt("k3_verdict_s1_arm1")))
    else: print("   arm6 vs arm1", e6.pair(e6.per_prompt("oq15c_verdict_s3_arm6"), e6.per_prompt("oq15c_verdict_s3_arm1")))
print("seed0 arm3 vs arm1", e6.pair(e6.per_prompt("k3_verdict_arm3"), e6.per_prompt("k3_verdict_arm1")))
print("seed2 arm6 vs arm1", e6.pair(e6.per_prompt("oq15c_verdict_arm6"), e6.per_prompt("oq15c_verdict_arm1")))
for s in ("k3_verdict_s1_arm3", "oq15c_verdict_s3_arm6"):
    pp = sorted(json.load(open(R + s + ".summary.json"))["per_prompt_stats"], key=lambda d: d["prompt_idx"])
    sec = np.array([p["seconds"] for p in pp])
    fire = [p["prompt_idx"] for p in pp if p["n_stop_blocks"] or p["n_extend_blocks"]]
    print(s, f"sec mean {sec.mean():.2f} total {sec.sum()/60:.1f} min", "firing prompts", fire[:5], len(fire), "row0", {k: pp[0][k] for k in ("n_emitted","n_blocks","n_drafted","n_accepted","n_stop_blocks","n_extend_blocks")})
    print("   blobs gen", git("rev-parse", f"HEAD:{R}{s}.gen.jsonl"), "stats", git("rev-parse", f"HEAD:{R}{s}.stats.jsonl"))
# degenerate R8 K3 scenario: arm 3 never fires at seed 6 -> new arm3 == new arm1
pop = sr.load_pop("k3")
vv, vf = pop["runs"]["verdict_vanilla"], pop["runs"]["verdict_free"]
leg_new, diff = sr.cross_seed_leg(vf, vv, vv, vv, sr.N_BOOT)
print("R8 K3 if arm 3 never fires at seed 6:", diff["label"], diff["reading"], "verdict CI", diff["verdict_leg"]["ci_lower"], diff["verdict_leg"]["ci_upper"], "new CI", leg_new["ci_lower"], leg_new["ci_upper"])
print("verdict arm3-arm1 CI upper is exactly 0.0:", diff["verdict_leg"]["ci_upper"] == 0.0)
