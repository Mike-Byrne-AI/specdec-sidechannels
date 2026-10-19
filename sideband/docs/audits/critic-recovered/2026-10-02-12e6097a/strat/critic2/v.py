import re, json, sys
D = r"C:\Users\<user>\AppData\Local\Temp\claude\c--Users-<user>-Desktop-Research-sideband\12e6097a-8666-465a-b5a3-e76024a56cff\scratchpad\strat"
bp = open(r"C:\Users\<user>\Desktop\Research\sideband\docs\BLUEPRINT.md", encoding="utf-8").read()
i0 = bp.index("OQ-9 STAGE-1 STRATIFIED COVERAGE READ REGISTRATION (2026-10-01, pre-run")
i1 = bp.index("## Eval protocol (non-negotiable)", i0)
block = bp[i0:i1]
norm = lambda s: re.sub(r"\s+", " ", s).strip()
rep = open(D + r"\critic2\round1_report.txt", encoding="utf-8").read()
q_orig = rep[rep.index("(1) REPRODUCE EXACT on both harvests"):]
q_orig = q_orig[:q_orig.index("a Q2 disagreement between harvests.") + len("a Q2 disagreement between harvests.")]
nb = norm(block)
j = nb.index("(1) REPRODUCE EXACT on both harvests")
q_blk = nb[j: nb.index("a Q2 disagreement between harvests.", j) + len("a Q2 disagreement between harvests.")]
print("critic prediction verbatim (whitespace-normalised):", norm(q_orig) == q_blk)
if norm(q_orig) != q_blk:
    a, b = norm(q_orig), q_blk
    k = next(i for i in range(min(len(a), len(b))) if a[i] != b[i]); print("first diff at", k, repr(a[k-40:k+60]), "|||", repr(b[k-40:k+60]))
pre_o = rep[rep.index("THE CRITIC"):rep.index("(1) REPRODUCE EXACT")]
print("orig preamble:", norm(pre_o))
k2 = nb.index("THE CRITIC'S (2026-10-01, design round")
print("block preamble:", nb[k2:j])
# the assistant predictions AS FIRST WRITTEN vs block.md (19:47)
old = norm(open(D + r"\block.md", encoding="utf-8").read())
a0 = old.index("(1) REPRODUCE holds"); a1 = old.index("(11) the replication agrees on both labels.") + len("(11) the replication agrees on both labels.")
b0 = nb.index("(1) REPRODUCE holds"); b1 = nb.index("(11) the replication agrees on both labels.") + len("(11) the replication agrees on both labels.")
oa, ob = old[a0:a1], nb[b0:b1]
print("assistant predictions (1)-(11) identical to the 19:47 draft:", oa == ob)
if oa != ob:
    import difflib
    for op in difflib.SequenceMatcher(None, oa, ob).get_opcodes():
        if op[0] != "equal": print("  ", op[0], repr(oa[op[1]:op[2]]), "->", repr(ob[op[3]:op[4]]))
w0 = old.index("WHAT WOULD SURPRISE THE ASSISTANT"); print("old surprise:", old[w0:w0+420])
# block_v2 (21:05): does it carry prediction (12) and the (c) amendments?
v2 = norm(open(D + r"\block_v2.md", encoding="utf-8").read())
print("block_v2 has (12):", "(12) the covered split by occurrences" in v2)
k12 = nb.index("(12) the covered split by occurrences"); print("block (12):", nb[k12:k12+170])
k12b = v2.index("(12) the covered split by occurrences") if "(12) the covered split by occurrences" in v2 else -1
print("v2 (12):", v2[k12b:k12b+170] if k12b >= 0 else None)
# whole HONEST PREDICTIONS section identical between block_v2 and worktree?
def sect(s, a, b): return s[s.index(a):s.index(b, s.index(a))]
print("HONEST PREDICTIONS v2 == worktree:", sect(v2, "HONEST PREDICTIONS", "- DISCLOSURES") == sect(nb, "HONEST PREDICTIONS", "- DISCLOSURES"))
for name in ("- LABELS", "- CONSEQUENCES", "- READOUTS", "- STRATA", "- THE p_t BLOCK"):
    pass
print("v2 == worktree up to PRE-FREEZE (d):", v2[:v2.index("(d) TESTS AFTER")] == nb[:nb.index("(d) TESTS AFTER")] if "(d) TESTS AFTER" in v2 else "v2 has no (d)")
