
H = {}
STAGES = (("readers", ("RN", "RT")), ("readers_long", ("RL",)))
for role, suffix, p3name in (("primary", "", "probes_s3.json.state.jsonl"), ("replication", "_r", "probes_s3_replication.json.state.jsonl")):
    _, p3 = rows_of(REAL + "/" + p3name)
    p3 = [c for c in p3 if "cell" in c and "_clusters" in c]
    _, lens = rows_of(REAL + "/lens_s3" + suffix + ".json.state.jsonl")
    H[role] = {}
    for stage, readers in STAGES:
        hdr, rows = rows_of(REAL + "/" + stage + "_s3" + suffix + ".json.state.jsonl")
        for reader in readers:
            for sp in SPACES:
                R, rv, best, resc = readouts(rows, p3, reader, sp)
                H[role][(reader, sp)] = {"R": R, "rv": rv, "best": best}
        ident = {}
        for s in (0, 1, 2):
            a = pick(rows, "R0", BAL, "a", "linear", s); b = pick(lens, "R0", BAL, "a", "linear", s)
            ident[s] = [k for k in sorted(set(a) | set(b)) if k != "runtime_s" and json.dumps(a.get(k), sort_keys=True) != json.dumps(b.get(k), sort_keys=True)]
        H[role]["ident_" + stage] = ident
