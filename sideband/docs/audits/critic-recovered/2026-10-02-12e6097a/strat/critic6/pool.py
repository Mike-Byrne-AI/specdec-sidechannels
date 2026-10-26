import sys, json, re
sys.path.insert(0,".")
from load import *
R="C:/Users/<user>/Desktop/Research/sideband/"
pool={}
def add(v,name):
    if isinstance(v,bool) or v is None: return
    if isinstance(v,(int,float)):
        for s in ("%+.4f"%v, "%.4f"%v, "%.4f"%abs(v), "%+.3f"%v, "%.3f"%abs(v), "%.2f"%abs(v), "%.1f"%abs(v), str(v), "{:,}".format(v) if isinstance(v,int) else "", "%.6f"%abs(v), "%.5f"%abs(v)):
            if s: pool.setdefault(s.lstrip("+-"),set()).add(name)
def walk(x,p):
    if isinstance(x,dict):
        for k,v in x.items(): walk(v,p+"."+str(k))
    elif isinstance(x,list):
        for i,v in enumerate(x): walk(v,p+"[%d]"%i)
    else: add(x,p)
for h,s in (("p",""),("r","_r")):
    walk(P[h],"strat"+h)
    walk(json.load(open(R+"results/real/prefetch_strat_s3%s.meta.json"%s,encoding="utf-8")),"smeta"+h)
    walk(T[h],"twin"+h)
    walk(json.load(open(R+"results/real/prefetch_bigram_s3%s.meta.json"%s,encoding="utf-8")),"tmeta"+h)
    walk(json.load(open(R+"results/real/prefetch_s3%s.json"%s,encoding="utf-8")),"st1"+h)
    # derived: half widths, sums
for h in "pr":
    for nm in ["gate_eq"]:
        for sc in ["covered"]:
            d,lo,hi=D(h,nm,16,sc); add((hi-lo)/2,"halfwidth_%s_%s"%(h,sc))
    sh=P[h]["conclusion"]["labels"]["scopes"]
    add(sh["covered_1"]["share"]+sh["covered_2_4"]["share"],"sparse_share_"+h)
json.dump({k:sorted(v)[:3] for k,v in pool.items()},open("pool.json","w"))
print(len(pool))
