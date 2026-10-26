import sys, json, subprocess, hashlib
sys.path.insert(0, "src"); sys.path.insert(0, "tools")
import numpy as np
import run_seed_replay as sr, e6_gate as e6
def git(*a): return subprocess.run(["git", *a], capture_output=True, text=True).stdout.strip()
# blobs of the instrument
for c in ("HEAD", "92fa9cb", "46ab439", "9e8fa4a", "89b38ef", "89b38ef~1"):
    print("run_k3_arms blob at", c, git("rev-parse", f"{c}:tools/run_k3_arms.py"))
# bound files and reference files blobs
for f in ("results/real/buckets_k16.json", "results/real/glue_k16.json"):
    print(f, "HEAD", git("rev-parse", f"HEAD:{f}"), "92fa9cb", git("rev-parse", f"92fa9cb:{f}"))
for s in ("k3_verdict_s1_arm1", "k3_verdict_s1_arm4", "oq15c_verdict_s3_arm1", "oq15c_verdict_s3_arm7"):
    print(s, "gen", git("rev-parse", f"HEAD:results/real/{s}.gen.jsonl"), "stats", git("rev-parse", f"HEAD:results/real/{s}.stats.jsonl"))
# git log over the seven-file closure
files = ["tools/run_k3_arms.py", "src/sideband/real/hf_specdec.py", "src/sideband/real/k3_live.py", "src/sideband/scheduler.py",
         "src/sideband/stats.py", "src/sideband/outcome_head.py", "src/sideband/provenance.py"]
print(git("log", "--format=%h %s", "92fa9cb..HEAD", "--", *files))
print("89b38ef files:", git("show", "--stat", "--format=", "89b38ef", "--", *files))
print("outcome_head added in:", git("log", "--diff-filter=A", "--format=%h", "--", "src/sideband/outcome_head.py"))
# F-27 provenance summaries
for k in ("k3", "oq15"):
    p = json.load(open(f"results/real/noise_floor_{k}.json", encoding="utf-8"))
    prov = p["provenance"]
    print(k, "provenance keys", sorted(prov.keys())[:20])
    print("  summaries", {st: (v.get("sha256", "")[:12], (v.get("meta_sha256") or "")[:12]) for st, v in prov.get("summaries", {}).items()})
    print("  prompts", prov.get("prompts"))
    for st in prov.get("summaries", {}):
        print("  disk", st, hashlib.sha256(open(f"results/real/{st}.summary.json", "rb").read()).hexdigest()[:12],
              hashlib.sha256(open(f"results/real/{st}.meta.json", "rb").read()).hexdigest()[:12])
# precondition on a fake 'new' pair = the verdict pair copied, to exercise the F-27 binding on real data
for key in ("k3", "oq15"):
    pop = sr.load_pop(key)
    print(key, "missing", pop["missing"])
    # mimic presence: alias the new runs to the verdict runs, metas with seed 6 + launch commit
    import copy
    pop["runs"]["new_vanilla"] = pop["runs"]["verdict_vanilla"]; pop["runs"]["new_tel"] = pop["runs"]["verdict_tel"]
    for t, b in (("new_vanilla", "verdict_vanilla"), ("new_tel", "verdict_tel")):
        m = copy.deepcopy(pop["metas"][b]); m["seed"] = 6; m["git_commit"] = "L"; pop["metas"][t] = m
    pop["missing"] = []
    prec = sr.precondition(pop, "L")
    print("  holds", prec["holds"], "failed", [k for k, v in prec["checks"].items() if v is False])
    print("  nf binding", prec["checks"].get("noise_floor_inputs_are_the_loaded_vanilla_runs"), prec["checks"].get("noise_floor_prompts_are_this_file"))
    # leg equality with e6
    l1 = sr.leg(pop["runs"]["verdict_tel"], pop["runs"]["verdict_vanilla"]); l2 = e6.pair(sr.as_e6(pop["runs"]["verdict_tel"]) if hasattr(sr, "as_e6") else None, None) if False else None
    a = e6.per_prompt(pop["stems"]["verdict_tel"]); b = e6.per_prompt(pop["stems"]["verdict_vanilla"])
    print("  leg == e6.pair:", l1 == e6.pair(a, b))
    vv, vt = pop["runs"]["verdict_vanilla"], pop["runs"]["verdict_tel"]
    print("  hw", round((l1["ci_upper"] - l1["ci_lower"]) / 2, 6))
