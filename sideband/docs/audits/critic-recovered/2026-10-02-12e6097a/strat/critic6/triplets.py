import sys, re, json
sys.path.insert(0,".")
from load import *
idx={}
for h in "pr":
    c=P[h]["conclusion"]
    for k,x in c["deltas"].items():
        idx.setdefault((f4(x["delta"]),f4(x["lo"]),f4(x["hi"])),[]).append(h+":"+k)
    for k,x in c["tables"].items():
        a=x["all"]; idx.setdefault((f4(a["point"]),f4(a["ci_lo"]),f4(a["ci_hi"])),[]).append(h+":T:"+k)
    for k in ["gate_eq","address_beyond_bigram","bigram_gain","address_beyond_token_re"]:
        pass
    tl=T[h]["conclusion"]["labels"] if "conclusion" in T[h] else {}
    for k,v in T[h]["conclusion"].get("deltas",{}).items() if isinstance(T[h]["conclusion"].get("deltas"),dict) else []:
        idx.setdefault((f4(v["delta"]),f4(v["lo"]),f4(v["hi"])),[]).append(h+":TWIN:"+k)
src=sys.argv[1]
txt=open(src,encoding="utf-8").read().replace("\n"," ")
txt=re.sub(r"\s*docs/BLUEPRINT\.md:\+\s*"," ",txt)
pat=re.compile(r"([+-]\d\.\d{4}) \[([+-]\d\.\d{4}), ([+-]\d\.\d{4})\]")
n=0; bad=0
for m in pat.finditer(txt):
    n+=1
    key=m.groups()
    hit=idx.get(key)
    ctx=txt[max(0,m.start()-60):m.start()].strip()
    if not hit: bad+=1; print("NOMATCH",key,"|",ctx)
    else:
        print(" ".join(key), "->", ",".join(hit[:4]), "|", ctx[-55:])
print("triplets",n,"nomatch",bad)
