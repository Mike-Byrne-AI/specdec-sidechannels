import json,difflib
S="C:/Users/<user>/AppData/Local/Temp/claude/c--Users-<user>-Desktop-Research-sideband/12e6097a-8666-465a-b5a3-e76024a56cff/scratchpad/strat/"
p="C:/Users/<user>/.claude/projects/c--Users-<user>-Desktop-Research-sideband/12e6097a-8666-465a-b5a3-e76024a56cff.jsonl"
writes={}
for l in open(p,encoding="utf-8"):
    r=json.loads(l); ts=r.get("timestamp","")
    c=r.get("message",{}).get("content")
    if isinstance(c,list):
        for it in c:
            if isinstance(it,dict) and it.get("type")=="tool_use" and it["name"]=="Write":
                fp=it["input"]["file_path"]
                for k in ("prefreeze_c","prefreeze_d"):
                    if k in fp: writes.setdefault(k,[]).append((ts,it["input"]["content"]))
for k,ws in writes.items():
    print("==",k,[w[0] for w in ws])
    old=ws[-2][1]; new=open(S+k+".md",encoding="utf-8").read()
    print(" current == last write:", new.rstrip("\n")==ws[-1][1].rstrip("\n") or "(differs; maybe substitution)")
    sm=difflib.SequenceMatcher(None,old.split(),new.split(),autojunk=False)
    for op,a1,a2,b1,b2 in sm.get_opcodes():
        if op!="equal":
            print(" ",op,"| OLD:"," ".join(old.split()[a1:a2])[:600]); print("     NEW:"," ".join(new.split()[b1:b2])[:1500])
