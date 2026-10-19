
def rows_for(key, A, B, R):
    lines = (REAL / ("noise_floor_" + key + ".json.state.jsonl")).read_text(encoding="utf-8").splitlines()
    header, rows = json.loads(lines[0]), [json.loads(x) for x in lines[1:]]
    gen1 = np.random.default_rng(1)
    gen2 = np.random.default_rng(2)
    subs, masks = {}, {}
    for n in SIZES:
        if n == 210:
            subs[n] = [np.arange(210)] * M
        else:
            subs[n] = [np.sort(gen1.choice(210, size=n, replace=False)) for _ in range(M)]
    for n in SIZES:
        masks[n] = gen2.integers(0, 2, size=(M, n)).astype(bool)
    disc, nrows, sub_ok, mask_ok = 0.0, 0, True, True
    byn = {n: [] for n in SIZES}
    for row in rows:
        n, k = row["n"], row["idx"]
        ix = subs[n][k]
        got = np.arange(210) if row["prompts"] == "all" else np.array(row["prompts"])
        sub_ok = sub_ok and np.array_equal(ix, got)
        nbits, hx = row["swap"].split(":")
        bits = bin(int(hx, 16))[2:].zfill(int(nbits))[-int(nbits):]
        mk = np.array([c == "1" for c in bits])
        mask_ok = mask_ok and np.array_equal(mk, masks[n][k])
        d, lo, hi = boot(A["e"][ix], A["b"][ix], B["e"][ix], B["b"][ix])
        ea2 = np.where(mk, B["e"][ix], A["e"][ix])
        ba2 = np.where(mk, B["b"][ix], A["b"][ix])
        eb2 = np.where(mk, A["e"][ix], B["e"][ix])
        bb2 = np.where(mk, A["b"][ix], B["b"][ix])
        d2, lo2, hi2 = boot(ea2, ba2, eb2, bb2)
        dpa = A["d"][ix].sum() / A["e"][ix].sum()
        dpb = B["d"][ix].sum() / B["e"][ix].sum()
        pairs = ((d, row["delta"]), (lo, row["lo"]), (hi, row["hi"]), ((hi - lo) / 2, row["hw"]), (d2, row["delta_sw"]),
                 (lo2, row["lo_sw"]), (hi2, row["hi_sw"]), ((hi2 - lo2) / 2, row["hw_sw"]), (dpa, row["dpe_a"]), (dpb, row["dpe_b"]))
        disc = max(disc, max(abs(a - b) for a, b in pairs))
        byn[n].append(dict(d=d, l=lo, h=hi, hw=(hi - lo) / 2, d2=d2, l2=lo2, h2=hi2, hw2=(hi2 - lo2) / 2, dpa=dpa, dpb=dpb, k=k))
        nrows += 1
    R["row_maxdisc"], R["nrows"] = disc, nrows
    R["subsets_regenerated"], R["masks_regenerated"] = bool(sub_ok), bool(mask_ok)
    R["header_constants"] = header["constants"]
    return byn
