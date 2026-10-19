import re, difflib
D = r"C:\Users\<user>\AppData\Local\Temp\claude\c--Users-<user>-Desktop-Research-sideband\12e6097a-8666-465a-b5a3-e76024a56cff\scratchpad\strat"
norm = lambda s: re.sub(r"\s+", " ", s).strip()
old = norm(open(D + r"\block.md", encoding="utf-8").read())
bp = open(r"C:\Users\<user>\Desktop\Research\sideband\docs\BLUEPRINT.md", encoding="utf-8").read()
i0 = bp.index("OQ-9 STAGE-1 STRATIFIED COVERAGE READ REGISTRATION (2026-10-01, pre-run"); nb = norm(bp[i0:bp.index("## Eval protocol", i0)])
# compare only up to the PRE-FREEZE ROUND (the registered body), word level
a = old[:old.index("- PRE-FREEZE")] if "- PRE-FREEZE" in old else old
b = nb[:nb.index("- PRE-FREEZE ROUND")]
aw, bw = a.split(" "), b.split(" ")
sm = difflib.SequenceMatcher(None, aw, bw, autojunk=False)
n = 0
for tag, i1, i2, j1, j2 in sm.get_opcodes():
    if tag == "equal": continue
    new = " ".join(bw[j1:j2]); ctx = " ".join(bw[max(0, j1-12):j2+12])
    marked = "(c" in new or "(c)" in ctx or "(c:" in ctx
    if not marked:
        n += 1
        print("UNMARKED", tag, "| OLD:", " ".join(aw[i1:i2])[:220], "| NEW:", new[:220])
        print("     ctx:", ctx[:300]); print()
print("unmarked hunks:", n)
