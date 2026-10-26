import json
p="C:/Users/<user>/.claude/projects/c--Users-<user>-Desktop-Research-sideband/12e6097a-8666-465a-b5a3-e76024a56cff/subagents/agent-a5e30bf876c037546.jsonl"
rows=[json.loads(l) for l in open(p,encoding="utf-8")]
# last assistant text
last=None
for r in rows:
    m=r.get("message",{})
    if m.get("role")=="assistant":
        c=m.get("content")
        if isinstance(c,list):
            t="".join(it.get("text","") for it in c if isinstance(it,dict) and it.get("type")=="text")
            if t.strip(): last=t
open("C:/Users/<user>/AppData/Local/Temp/claude/c--Users-<user>-Desktop-Research-sideband/12e6097a-8666-465a-b5a3-e76024a56cff/scratchpad/strat/critic3/round2_report.txt","w",encoding="utf-8").write(last)
print(len(last))
