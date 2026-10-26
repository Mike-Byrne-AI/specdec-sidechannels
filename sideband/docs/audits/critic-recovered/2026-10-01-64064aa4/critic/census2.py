import json, subprocess, os, re
from pathlib import Path
ROOT = Path(r"C:\Users\<user>\Desktop\Research\sideband")
SP = Path(r"C:\Users\<user>\AppData\Local\Temp\claude\c--Users-<user>-Desktop-Research-sideband\64064aa4-b9c8-45b6-9f59-46838015656c\scratchpad")
per = json.load(open(SP/"critic"/"staged84.json"))
cited = set(t for *_,t in json.load(open(SP/"critic"/"census_hits.json")))
print("cited set:", sorted(cited))
# 1) 12-hex prefix search in tracked files for the uncited 81
lf12 = {v["lf_sha"][:12]: p for p,v in per.items()}
cr12 = {v["crlf_sha"][:12]: p for p,v in per.items()}
pat = SP/"critic"/"pats12.txt"; pat.write_text("\n".join(list(lf12)+list(cr12))+"\n")
out = subprocess.run(["git","grep","-I","-o","-n","-F","-f",str(pat)], cwd=ROOT, capture_output=True).stdout.decode("utf-8","replace")
rows = [l.split(":",2) for l in out.splitlines()]
from collections import Counter
c = Counter(("LF" if h in lf12 else "CRLF", (lf12.get(h) or cr12.get(h))) for f,ln,h in rows)
print("12-hex prefix hits (tracked):", len(rows), " kinds:", Counter(k for (k,_) in c.elements()))
print(" targets via prefix:", sorted(set(t for (_,t) in c)))
# 2) untracked files on disk under results/ (text-ish, < 50MB) for full shas
lf = {v["lf_sha"]: p for p,v in per.items()}; cr = {v["crlf_sha"]: p for p,v in per.items()}
tracked = set(p for p in subprocess.run(["git","ls-files","-z"],cwd=ROOT,capture_output=True).stdout.decode().split("\0") if p)
hits = Counter(); files_hit = Counter(); scanned = 0; skipped_big = 0
rx = re.compile(rb"[0-9a-f]{64}")
for dp, dns, fs in os.walk(ROOT):
    if ".git" in Path(dp).parts: continue
    for f in fs:
        fp = Path(dp, f); rel = str(fp.relative_to(ROOT)).replace("\\","/")
        if rel in tracked: continue
        try:
            if fp.stat().st_size > 50_000_000: skipped_big += 1; continue
            b = fp.read_bytes()
        except OSError: continue
        scanned += 1
        for m in set(rx.findall(b)):
            h = m.decode()
            if h in lf: hits[("LF", lf[h])] += 1; files_hit[rel] += 1
            elif h in cr: hits[("CRLF", cr[h])] += 1; files_hit[rel] += 1
print("untracked files scanned:", scanned, " skipped >50MB:", skipped_big)
print(" untracked citing hits:", sum(hits.values()), " by kind:", Counter(k for (k,_) in hits.elements()))
print(" targets:", sorted(set(t for (_,t) in hits)))
print(" LF-cited targets in untracked:", sorted(set(t for (k,t) in hits if k=="LF")))
print(" files:", files_hit.most_common(15))
