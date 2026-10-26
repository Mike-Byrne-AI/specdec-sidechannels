import json,re
p="C:/Users/<user>/.claude/projects/c--Users-<user>-Desktop-Research-sideband/12e6097a-8666-465a-b5a3-e76024a56cff.jsonl"
pat=re.compile(r"\d+ failed, \d+ passed in [0-9.]+s|\d+ passed in [0-9.]+s")
for l in open(p,encoding="utf-8"):
    r=json.loads(l); ts=r.get("timestamp","")
    if not("2026-10-02T01:12"<=ts<="2026-10-02T01:50"): continue
    c=r.get("message",{}).get("content")
    if isinstance(c,list):
        for it in c:
            if isinstance(it,dict) and it.get("type")=="tool_result":
                s=json.dumps(it.get("content"))
                for m in pat.finditer(s): print(ts,m.group(0))
                if "AssertionError" in s:
                    i=s.find("assert "); print(ts,"ASSERT:",s[i:i+260])
