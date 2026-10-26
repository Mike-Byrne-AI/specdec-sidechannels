import re
D = r"C:\Users\<user>\AppData\Local\Temp\claude\c--Users-<user>-Desktop-Research-sideband\12e6097a-8666-465a-b5a3-e76024a56cff\scratchpad\strat"
norm = lambda s: re.sub(r"\s+", " ", s).strip()
old = norm(open(D + r"\block.md", encoding="utf-8").read())
v2 = norm(open(D + r"\block_v2.md", encoding="utf-8").read())
bp = open(r"C:\Users\<user>\Desktop\Research\sideband\docs\BLUEPRINT.md", encoding="utf-8").read()
i0 = bp.index("OQ-9 STAGE-1 STRATIFIED COVERAGE READ REGISTRATION (2026-10-01, pre-run"); nb = norm(bp[i0:bp.index("## Eval protocol", i0)])
k = old.index("(8) D_pt on ALL"); print("OLD (8):", old[k:k+330]); print()
k = nb.index("(8) D_pt on ALL"); print("NOW (8):", nb[k:k+260]); print()
k = old.index("(5) Q1 modal"); print("OLD (5):", old[k:k+120]); print()
k = old.index("HONEST PREDICTIONS"); print("OLD HONEST header:", old[k:k+420]); print()
k = old.find("SURPRISE"); print("OLD SURPRISE:", old[k-40:k+520]); print()
k = v2.index("(8) D_pt on ALL"); print("V2 (8):", v2[k:k+260]); print()
print("v2 HONEST == now:", v2[v2.index("- HONEST PREDICTIONS"):v2.index("- DISCLOSURES")] == nb[nb.index("- HONEST PREDICTIONS"):nb.index("- DISCLOSURES")])
for tag in ("- LABELS", "- CONSEQUENCES", "- READOUTS", "- STRATA", "- THE p_t BLOCK", "- DESIGN", "- TWO QUESTIONS", "- PROVENANCE"):
    pass
# any section of v2 that differs from now, before the PRE-FREEZE ROUND
a = v2[:v2.index("- PRE-FREEZE ROUND")]; b = nb[:nb.index("- PRE-FREEZE ROUND")]
print("v2 pre-PRE-FREEZE == now:", a == b)
if a != b:
    import difflib
    for op in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op[0] != "equal": print("  ", op[0], repr(a[op[1]:op[2]][:300]), "->", repr(b[op[3]:op[4]][:300]))
