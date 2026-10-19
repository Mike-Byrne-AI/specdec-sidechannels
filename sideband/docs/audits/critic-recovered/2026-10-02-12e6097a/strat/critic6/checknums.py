import json, re
pool=json.load(open("pool.json"))
txt=open("added.txt",encoding="utf-8").read()
# only lines whose content is new strat-related: skip pure count edits; we check all
nums=re.finditer(r"(?<![\w.])([+-]?\d[\d,]*\.\d+|[+-]?\d{1,3}(?:,\d{3})+|\d+)(?![\w])", txt)
unm=[]; tot=0; dec=0
for m in nums:
    s=m.group(1); core=s.lstrip("+-")
    if "." not in core and "," not in core: continue  # skip plain integers (dates, counts) here
    tot+=1
    if core in pool: continue
    unm.append((s, txt[max(0,m.start()-70):m.end()+30].replace("\n"," ")))
print("decimal/comma numbers:",tot,"unmatched:",len(unm))
for s,c in unm: print(repr(s),"|",c)
