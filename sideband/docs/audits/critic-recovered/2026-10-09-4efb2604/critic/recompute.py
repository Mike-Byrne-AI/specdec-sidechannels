import sys, json, hashlib
sys.path.insert(0, "src"); sys.path.insert(0, "tools")
import numpy as np
import e6_gate as e6
from pathlib import Path
R = Path("results/real")
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
for pop in ("k3_s1", "oq15c_s3"):
    res = e6.evaluate(pop)
    print("==", pop, "win", res["win"])
    for k, a in res["arms"].items():
        print(f"  arm {k} t/c {a['tokens_per_call']:.6f} dpe {a['drafted_per_emitted']:.6f}")
    for name, leg in res["legs"].items():
        print(f"  {name} {leg['delta']:+.6f} [{leg['ci_lower']:+.6f}, {leg['ci_upper']:+.6f}] guard {leg['budget_guard_margin']:+.6f} holds {leg['guard_holds']}")
for stem in ("k3_verdict_arm1", "oq15c_verdict_arm1"):
    s = json.load(open(R / f"{stem}.summary.json"))
    print(stem, f"t/c {s['tokens_per_call']:.6f}")
# guard gaps
for v, t in (("k3_verdict_s1_arm1","k3_verdict_s1_arm4"),("oq15c_verdict_s3_arm1","oq15c_verdict_s3_arm7")):
    a = json.load(open(R/f"{v}.summary.json"))["drafted_per_emitted"]; b = json.load(open(R/f"{t}.summary.json"))["drafted_per_emitted"]
    print(v, t, f"dpe gap {a-b:.6f} headroom {a-b+0.01:.6f}")
# per prompt rows
keys = ("n_emitted","n_blocks","n_drafted","n_accepted","n_stop_blocks","n_extend_blocks")
for stem, n in (("k3_verdict_s1_arm1",6),("k3_verdict_s1_arm4",6),("oq15c_verdict_s3_arm1",1),("oq15c_verdict_s3_arm7",1)):
    pp = sorted(json.load(open(R/f"{stem}.summary.json"))["per_prompt_stats"], key=lambda d: d["prompt_idx"])
    for p in pp[:n]:
        print(stem, p["prompt_idx"], [p[k] for k in keys])
# first stop/extend prompts arm4
pp = sorted(json.load(open(R/"k3_verdict_s1_arm4.summary.json"))["per_prompt_stats"], key=lambda d: d["prompt_idx"])
fs = [p["prompt_idx"] for p in pp if p["n_stop_blocks"]>0][:3]; fe=[p["prompt_idx"] for p in pp if p["n_extend_blocks"]>0][:3]
print("arm4 first stops", fs, "first extends", fe)
# metas: thresholds and git stamps
for stem in ("k3_verdict_s1_arm1","k3_verdict_s1_arm4","oq15c_verdict_s3_arm1","oq15c_verdict_s3_arm7","k3_verdict_arm1","oq15c_verdict_arm1"):
    m = json.load(open(R/f"{stem}.meta.json"))
    th = m.get("thresholds")
    print(stem, "seed", m["seed"], "git", m["git_commit"], "thr_sha", m.get("thresholds_sha256"), "probe_w", m.get("probe_weights_sha256"), "head_w", m.get("head_weights_sha256"), "prompts", m.get("prompts"), m.get("prompts_sha256"))
    if th: print("   thr", th.get("kind"), th.get("selection_label"), [f"{x:.6f}" for x in th["stop"]], th["stop_level"], f"{th['extend']:.6f}", th["extend_level"])
for f in ("data/prompts_k3_verdict.jsonl","data/prompts_oq15_verdict.jsonl","results/real/k3_thresholds_arm4_v2.json","results/real/k3_probe_weights.npz","results/real/oq15c_thresholds_arm7_v2.json","results/real/oq15_head_weights.npz","tools/run_k3_arms.py"):
    print(f, sha(f))
# file thresholds content
for f in ("results/real/k3_thresholds_arm4_v2.json","results/real/oq15c_thresholds_arm7_v2.json"):
    d = json.load(open(f)); print(f, d["kind"], d.get("selection_label"), d["stop"], d["stop_level"], d["extend"], d["extend_level"])
# F-27 payloads
for k in ("k3","oq15"):
    p = json.load(open(R/f"noise_floor_{k}.json"))
    rel = p["readouts"]["reliability"]
    print("nf", k, f"r {rel['r']:.4f} [{rel['ci_lower']:.4f}, {rel['ci_upper']:.4f}]", "hw210", p["readouts"]["per_n"]["210"]["half_width"])
    print("   single", p["readouts"]["per_n"]["210"].get("single"))
# seconds per prompt
for stem in ("k3_verdict_s1_arm1","k3_verdict_s1_arm4","oq15c_verdict_s3_arm1","oq15c_verdict_s3_arm7","k3_verdict_arm1","oq15c_verdict_arm1"):
    pp = json.load(open(R/f"{stem}.summary.json"))["per_prompt_stats"]
    s = np.array([p["seconds"] for p in pp])
    print(stem, f"sec/prompt mean {s.mean():.2f} median {np.median(s):.2f} total_min {s.sum()/60:.1f} n {len(s)}")
