"""Text round (READERS-LONG landing): registered-text integrity of `git diff HEAD` on the eight record files, and the
twelve CARRIED_ROWS literals against the NEW spans only. Read-only on the repo."""
import subprocess, sys, re, difflib
from pathlib import Path
ROOT = Path(r"C:\Users\<user>\Desktop\Research\sideband")
FILES = ["CHANGELOG.md", "FINDINGS.md", "OPEN_QUESTIONS.md", "README.md", "docs/BLUEPRINT.md", "docs/FINDINGS_INDEX.md",
         "docs/REPORT.md", "docs/WHY_THIS_DIES.md"]
CARRIED_ROWS = ("-0.0012", "-0.0016", "0.003", "0.0160", "0.0187", "0.0232", "0.0258", "0.267", "0.307", "0.0113", "0.0055", "0.0091")
NUM = re.compile(r"(?<![\w.])[-+]?\d[\d,]*\.?\d*(?:e-?\d+)?")
def toks(s):
    return [m.group(0).lstrip("+") for m in NUM.finditer(s)]
tot_removed = 0
new_spans = []
for f in FILES:
    head = subprocess.run(["git", "show", f"HEAD:{f}"], cwd=ROOT, capture_output=True).stdout.decode("utf-8").replace("\r\n", "\n").split("\n")
    work = (ROOT / f).read_bytes().decode("utf-8").replace("\r\n", "\n").split("\n")
    sm = difflib.SequenceMatcher(a=head, b=work, autojunk=False)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            continue
        if op == "insert":
            new_spans.append((f, "insert", "\n".join(work[j1:j2])))
            continue
        if op == "delete":
            print("DELETE", f, i1, head[i1:i2]); tot_removed += i2 - i1; continue
        # replace: require 1:1 line pairs each = old + one inserted span
        if i2 - i1 != j2 - j1:
            print("REPLACE-UNEQUAL", f, i1, i2, j1, j2); 
            for x in head[i1:i2]: print("   -", x[:200])
            for x in work[j1:j2]: print("   +", x[:200])
            continue
        for a, b in zip(head[i1:i2], work[j1:j2]):
            tot_removed += 1
            m = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
            ops = [o for o in m.get_opcodes() if o[0] != "equal"]
            ok = len(ops) == 1 and ops[0][0] == "insert"
            span = b[ops[0][3]:ops[0][4]] if ok else None
            print(f"{f}: line pair old {len(a)} new {len(b)} -> single insertion: {ok}; insertion at char {ops[0][1] if ops else None} of {len(a)}; ends-with-old-tail: {b.endswith(a[ops[0][1]:]) if ok else None}")
            if not ok:
                for o in ops: print("    op", o, repr(a[o[1]:o[2]][:120]), "->", repr(b[o[3]:o[4]][:120]))
            else:
                new_spans.append((f, "inline", span))
                # carried literals: count in old vs new line
                for lit in CARRIED_ROWS:
                    co, cn = toks(a).count(lit), toks(b).count(lit)
                    if co or cn:
                        print(f"    carried {lit}: old {co} new {cn} in-span {toks(span).count(lit)}")
print("removed-or-rewritten lines:", tot_removed)
hits = []
for f, kind, span in new_spans:
    t = toks(span)
    for lit in CARRIED_ROWS:
        if lit in t:
            hits.append((f, kind, lit, t.count(lit)))
print("CARRIED_ROWS literals inside NEW spans:", hits or "none")
print("new spans:", [(f, k, len(s)) for f, k, s in new_spans])
