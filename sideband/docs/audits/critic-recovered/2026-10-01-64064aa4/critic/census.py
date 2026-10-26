import json, subprocess, re, os
from pathlib import Path
ROOT = Path(r"C:\Users\<user>\Desktop\Research\sideband")
SP = Path(r"C:\Users\<user>\AppData\Local\Temp\claude\c--Users-<user>-Desktop-Research-sideband\64064aa4-b9c8-45b6-9f59-46838015656c\scratchpad")
per = json.load(open(SP/"critic"/"staged84.json"))
lf = {v["lf_sha"]: p for p,v in per.items()}
crlf = {v["crlf_sha"]: p for p,v in per.items()}
pat = SP/"critic"/"pats.txt"
pat.write_text("\n".join(list(lf)+list(crlf))+"\n")
# tracked files (worktree content), all text
out = subprocess.run(["git","grep","-I","-o","-n","-F","-f",str(pat)], cwd=ROOT, capture_output=True).stdout.decode("utf-8","replace")
hits = []
for line in out.splitlines():
    f, ln, h = line.split(":",2)
    kind = "LF" if h in lf else "CRLF"
    target = lf.get(h) or crlf.get(h)
    hits.append((f, int(ln), kind, target))
print("tracked-file citations of the 84 files' shas:", len(hits))
from collections import Counter
print(" by version:", Counter(k for _,_,k,_ in hits))
print(" by citing file:", Counter(f for f,_,_,_ in hits).most_common(40))
print(" distinct targets cited:", len(set(t for *_,t in hits)))
byt = {}
for f,ln,k,t in hits: byt.setdefault(t, set()).add(k)
print(" targets cited as LF only:", sorted(t for t,ks in byt.items() if ks=={"LF"}))
print(" targets cited as CRLF only:", len([t for t,ks in byt.items() if ks=={"CRLF"}]))
print(" targets cited both:", sorted(t for t,ks in byt.items() if len(ks)==2))
print(" staged targets never cited (tracked tree):", sorted(set(per)-set(byt)))
json.dump(hits, open(SP/"critic"/"census_hits.json","w"), indent=0)
