
H = {}
for role, name, p3name in (("primary", "readers_s3.json", "probes_s3.json.state.jsonl"), ("replication", "readers_s3_r.json", "probes_s3_replication.json.state.jsonl")):
    hdr, rows = rows_of(REAL + "/" + name + ".state.jsonl")
    _, p3 = rows_of(REAL + "/" + p3name)
    p3 = [c for c in p3 if "cell" in c and "_clusters" in c]
    H[role] = {"rows": rows}
    for reader in ("RN", "RT"):
        for sp in SPACES:
            R, rv, best, resc = readouts(rows, p3, reader, sp)
            H[role][(reader, sp)] = {"R": R, "rv": rv, "best": best, "resc": resc}
    _, lens = rows_of(REAL + "/" + ("lens_s3.json" if role == "primary" else "lens_s3_r.json") + ".state.jsonl")
    ident = {}
    for s in (0, 1, 2):
        a = pick(rows, "R0", BAL, "a", "linear", s); b = pick(lens, "R0", BAL, "a", "linear", s)
        ident[s] = [k for k in sorted(set(a) | set(b)) if k != "runtime_s" and json.dumps(a.get(k), sort_keys=True) != json.dumps(b.get(k), sort_keys=True)]
    H[role]["ident"] = ident
    H[role]["runtime"] = sum(r["runtime_s"] for r in rows)
