# Independent R3: walk payload provenance recursively (any depth), not just depth-2, and split tracked/untracked.
import hashlib, json, re, subprocess, os
from pathlib import Path
from collections import Counter, defaultdict
ROOT = Path(r"C:\Users\<user>\Desktop\Research\sideband")
HEX = re.compile(r"^[0-9a-fA-F]{64}$")
tracked = set(p for p in subprocess.run(["git","ls-files","-z"],cwd=ROOT,capture_output=True).stdout.decode().split("\0") if p)
def rel(p): return p.relative_to(ROOT).as_posix()
def walk(o, path):
    if isinstance(o, dict):
        for k,v in o.items(): yield from walk(v, path+[k])
    elif isinstance(o, list):
        for i,v in enumerate(o): yield from walk(v, path+[i])
    else: yield path, o
payloads = sorted(ROOT.glob("results/**/*.json"))
parse_fail = []
depth2 = []   # the test's definition: prov[key][name]=sha, name endswith .json/.jsonl
anydepth = [] # any 64-hex value anywhere in provenance whose immediate key ends .json/.jsonl
nonname = Counter()  # 64-hex values in provenance keyed by something else
for pl in payloads:
    try: d = json.loads(pl.read_text(encoding="utf-8"))
    except Exception as e: parse_fail.append((rel(pl), type(e).__name__)); continue
    prov = d.get("provenance") if isinstance(d, dict) else None
    if not isinstance(prov, dict): continue
    for key,val in prov.items():
        if isinstance(val, dict):
            for name, sha in val.items():
                if isinstance(name,str) and isinstance(sha,str) and re.fullmatch(r"[0-9a-f]{64}",sha) and name.endswith((".json",".jsonl")):
                    depth2.append((pl,key,name,sha))
    for path, v in walk(prov, []):
        if isinstance(v,str) and HEX.match(v):
            last = path[-1] if path else None
            if isinstance(last,str) and last.endswith((".json",".jsonl")):
                anydepth.append((pl, "/".join(map(str,path)), last, v))
            else:
                nonname["/".join(map(str,path[:1]))+"/.../"+str(last)] += 1
def resolve(pl, name):
    for c in (pl.parent/name, ROOT/"results"/"real"/name, ROOT/"results"/name):
        if c.is_file(): return c
print("payload json files on disk:", len(payloads), " tracked:", sum(rel(p) in tracked for p in payloads), " parse failures:", len(parse_fail), parse_fail[:5])
for label, cites in (("depth2(test def)", depth2), ("anydepth", anydepth)):
    res = [(pl,k,n,s,resolve(pl,n)) for pl,k,n,s in cites]
    ok = [r for r in res if r[4] is not None]
    bad = [r for r in ok if hashlib.sha256(r[4].read_bytes()).hexdigest() != r[3].lower()]
    t_pl = [r for r in ok if rel(r[0]) in tracked]
    t_both = [r for r in ok if rel(r[0]) in tracked and rel(r[4]) in tracked]
    print(f"[{label}] citations: {len(res)}  resolvable: {len(ok)}  sha mismatch: {len(bad)}  unresolvable: {len(res)-len(ok)}")
    print(f"   resolvable w/ tracked payload: {len(t_pl)}  w/ tracked payload AND tracked target: {len(t_both)}")
    print(f"   keys: {Counter(k.split('/')[0] for _,k,_,_,_ in res)}")
    print(f"   payloads untracked among resolvable: {sorted(set(rel(r[0]) for r in ok if rel(r[0]) not in tracked))}")
    print(f"   targets untracked among resolvable: {sorted(set(rel(r[4]) for r in ok if rel(r[4]) not in tracked))}")
    if bad: print("   BAD:", [(rel(a),k,n) for a,k,n,_,_ in bad][:10])
    unres = Counter(n for pl,k,n,s,t in res if t is None)
    print(f"   unresolvable names: {dict(unres)}")
    # are any unresolvable names actually tracked somewhere else in the repo by basename?
    base = defaultdict(list)
    for p in tracked: base[p.rsplit('/',1)[-1]].append(p)
    print(f"   unresolvable names that exist (tracked) elsewhere: { {n: base[n] for n in unres if n in base} }")
    # basename ambiguity among resolvable targets
    amb = {n: base[n] for n in set(r[2] for r in ok) if len(base.get(n,[]))>1}
    print(f"   resolvable names with >1 tracked file of that basename: {amb}")
print("non-filename-keyed 64-hex values in provenance (top 25):", nonname.most_common(25))
