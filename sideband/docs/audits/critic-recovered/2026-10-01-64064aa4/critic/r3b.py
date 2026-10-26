import hashlib, json, re, subprocess
from pathlib import Path
from collections import Counter
ROOT = Path(r"C:\Users\<user>\Desktop\Research\sideband")
tracked = set(p for p in subprocess.run(["git","ls-files","-z"],cwd=ROOT,capture_output=True).stdout.decode().split("\0") if p)
rel = lambda p: p.relative_to(ROOT).as_posix()
smoke = sorted(ROOT.glob("results/smoke/*.json"))
print("results/smoke json on disk:", len(smoke), " tracked:", sum(rel(p) in tracked for p in smoke))
ci = subprocess.run(["git","check-ignore","-v"]+[rel(p) for p in smoke[:4]],cwd=ROOT,capture_output=True,text=True)
print("check-ignore sample:", ci.stdout.strip().splitlines()[:4])
# per-payload citation counts for the untracked resolvable ones
for p in ["results/smoke/fullfree_coarse_s1_smoke.json","results/smoke/fullfree_coarse_s3_smoke.json","results/smoke/fullfree_smoke2_mlp.json","results/smoke/fullfree_smoke2_shuf.json"]:
    d = json.loads((ROOT/p).read_text(encoding="utf-8"))
    ls = d["provenance"].get("label_space_sha256", {})
    print(p, "label_space entries:", len(ls), "->", sorted(ls)[:6])
# tracked-only replication of the test's count
cites=[]
for pl in sorted(ROOT.glob("results/**/*.json")):
    if rel(pl) not in tracked: continue
    d=json.loads(pl.read_text(encoding="utf-8")); prov=d.get("provenance") if isinstance(d,dict) else None
    if not isinstance(prov,dict): continue
    for k,v in prov.items():
        if isinstance(v,dict):
            for n,s in v.items():
                if isinstance(n,str) and isinstance(s,str) and re.fullmatch(r"[0-9a-f]{64}",s) and n.endswith((".json",".jsonl")): cites.append((pl,k,n,s))
def resolve(pl,n):
    for c in (pl.parent/n, ROOT/"results"/"real"/n, ROOT/"results"/n):
        if c.is_file(): return c
res=[(pl,k,n,s,resolve(pl,n)) for pl,k,n,s in cites]
print("TRACKED-ONLY (fresh-clone view): citations", len(res), " resolvable", sum(r[4] is not None for r in res), " -> test asserts >= 118")
# the 20 skipped npz_sha256_verified citations: do they match the tracked subdirectory files?
skipped=[r for r in res if r[4] is None]
print("skipped:", len(skipped), Counter(r[1] for r in skipped), " citing payloads:", sorted(set(rel(r[0]) for r in skipped)))
cands = {p.rsplit('/',1)[-1]: p for p in tracked if p.startswith("results/real/harvest_")}
m=mm=0
for pl,k,n,s,_ in skipped:
    t = cands.get(n)
    if t is None: print("  no tracked file named", n); continue
    h = hashlib.sha256((ROOT/t).read_bytes()).hexdigest()
    if h==s: m+=1
    else:
        mm+=1; print("  MISMATCH", rel(pl), n, t, s[:12], h[:12])
print(f"  skipped citations: match tracked subdir file {m}, mismatch {mm}")
# check where npz_sha256_verified sits and whether its payload names the directory
for pl in sorted(set(r[0] for r in skipped)):
    d=json.loads(pl.read_text(encoding="utf-8")); prov=d["provenance"]
    print("  ", rel(pl), "provenance keys:", sorted(prov)[:12])
