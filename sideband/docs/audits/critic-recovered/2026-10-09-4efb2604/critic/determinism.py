import json, numpy as np
from pathlib import Path
R = Path("results/real")
def gen(stem):
    return {json.loads(l)["prompt_idx"]: json.loads(l)["generated_ids"] for l in open(R/f"{stem}.gen.jsonl") if l.strip()}
def pp(stem):
    return {p["prompt_idx"]: p for p in json.load(open(R/f"{stem}.summary.json"))["per_prompt_stats"]}
keys = ("n_emitted","n_blocks","n_drafted","n_accepted","n_stop_blocks","n_extend_blocks")
for van, tel in (("k3_verdict_s1_arm1","k3_verdict_s1_arm4"),("oq15c_verdict_s3_arm1","oq15c_verdict_s3_arm7"),("k3_verdict_s1_arm1","k3_verdict_s1_arm3"),("oq15c_verdict_s3_arm1","oq15c_verdict_s3_arm6")):
    gv, gt, pv, pt = gen(van), gen(tel), pp(van), pp(tel)
    nofire = [i for i in pt if pt[i]["n_stop_blocks"]==0 and pt[i]["n_extend_blocks"]==0]
    same_ids = sum(gv[i]==gt[i] for i in nofire); same_rows = sum(all(pv[i][k]==pt[i][k] for k in keys) for i in nofire)
    fire = [i for i in pt if i not in nofire]
    rows_eq_fire = sum(all(pv[i][k]==pt[i][k] for k in ("n_emitted","n_blocks","n_drafted","n_accepted")) for i in fire)
    ids_eq_fire = sum(gv[i]==gt[i] for i in fire)
    print(f"{tel} vs {van}: no-fire prompts {len(nofire)}, ids identical {same_ids}, rows identical {same_rows}; firing prompts {len(fire)}, ids identical {ids_eq_fire}, 4-counter rows equal {rows_eq_fire}")
g = gen("k3_verdict_s1_arm1")
print("k3 s1 arm1 prompt0 vs prompt1 ids equal:", g[0]==g[1], len(g[0]), len(g[1]))
# prompts 0,1 texts
lines = [json.loads(l) for l in open("data/prompts_k3_verdict.jsonl") if l.strip()]
print(repr(lines[0]["prompt"][:120])); print(repr(lines[1]["prompt"][:120])); print(lines[0].get("family"), lines[1].get("family"))
# how many prompt pairs in arm1 share identical 4-counter rows (coincidence base rate)
p = pp("k3_verdict_s1_arm1"); rows = [tuple(p[i][k] for k in keys[:4]) for i in range(210)]
from collections import Counter
c = Counter(rows); print("duplicate row tuples in k3 s1 arm1:", sum(v for v in c.values() if v>1), "max multiplicity", max(c.values()))
# stats keys
s = json.loads(open(R/"k3_verdict_s1_arm4.stats.jsonl").readline()); print(sorted(s.keys()))
