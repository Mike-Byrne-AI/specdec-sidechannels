import json,difflib
p="C:/Users/<user>/.claude/projects/c--Users-<user>-Desktop-Research-sideband/12e6097a-8666-465a-b5a3-e76024a56cff.jsonl"
for l in open(p,encoding="utf-8"):
    r=json.loads(l); ts=r.get("timestamp","")
    if ts not in ("2026-10-02T01:38:00.545Z","2026-10-02T01:38:07.993Z"): continue
    for it in r["message"]["content"]:
        if isinstance(it,dict) and it.get("type")=="tool_use":
            o=it["input"]["old_string"].split(); n=it["input"]["new_string"].split()
            sm=difflib.SequenceMatcher(None,o,n,autojunk=False)
            print("=====",ts)
            for op,a1,a2,b1,b2 in sm.get_opcodes():
                if op!="equal": print(op,"| OLD:"," ".join(o[a1:a2]),"\n   NEW:"," ".join(n[b1:b2]))
