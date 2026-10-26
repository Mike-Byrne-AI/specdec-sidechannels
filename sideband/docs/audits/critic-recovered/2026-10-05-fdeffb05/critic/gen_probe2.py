"""Generate every landing text for STAGE READERS-LONG of the reader-and-lens registration: the two committed payloads,
the conclusion over the readers pair WITH the lens pair and the long pair (the ONE K-2 sentence over both reader
stages), the RL clean-clone rerun, and the R0 linear (a) identity of the long payloads against the lens rows, through a
number registry; every K-2 / per-cell branch written from the block's pinned words. Writes LF texts + numbers.json to
OUT."""
import datetime
import json
import statistics
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\<user>\Desktop\Research\sideband")
sys.path.insert(0, str(ROOT / "tools"))
import landing_text as lt  # noqa: E402
import run_reader_lens as rl  # noqa: E402

S = Path(r"C:/Users/<user>/AppData/Local/Temp/claude/c--Users-<user>-Desktop-Research-sideband/fdeffb05-309a-409b-9a03-d56ff41b9815/scratchpad")
OUT = Path(r"C:/Users/<user>/AppData/Local/Temp/claude/c--Users-<user>-Desktop-Research-sideband/fdeffb05-309a-409b-9a03-d56ff41b9815/scratchpad/critic/probe_out2")
LAUNCH, FREEZE, READERS_LANDING, TODAY = "f050574", "b128fda", "34078d1", datetime.date.today().isoformat()
TOOL_SHA12 = "d1125670be05"
L1, LOP, BAL = "L1_olmoe_k16", "L3_olmoe_groups_v1", "L3_olmoe_balanced_v1"
SPACES = (L1, LOP, BAL)
SPACE_WORD = {L1: "L1", LOP: "the lopsided L3", BAL: "the balanced L3"}
READER_WORD = {"RN": "R-N (hz-rescaled)", "RT": "R-T (two-tower)", "RL": "R-L (longer budget)"}
ROLE = {"p": "primary", "r": "replication"}
P = {"p": json.loads((ROOT / "results/real/readers_long_s3.json").read_text(encoding="utf-8")),
     "r": json.loads((ROOT / "results/real/readers_long_s3_r.json").read_text(encoding="utf-8"))}
C = json.loads((S / "conclude_readers_long.json").read_text(encoding="utf-8"))
for s, pl in P.items():
    pv = pl["provenance"]
    assert pl["stage"] == "readers_long" and not pl["partial"] and pl["smoke_cell"] is None and pl["resumed_cells"] == 0
    assert pv["git_commit"].startswith(LAUNCH) and pv["git_status_tracked"] == [] and pv["instrument_sha256"].startswith(TOOL_SHA12)
    assert pv["threads"] == 6 and pv["cuda_visible_devices"] == "" and pv["torn_bytes_dropped_on_resume"] == 0
    assert pl["riders"] == {} and pl["balanced_admission"]["ok"] and len(pl["cells"]) == 39 and list(pl["readers"]) == ["RL"]
assert C["stage"] == "readers" and set(C["labels_readers_long"]) == {f"RL|{sp}" for sp in SPACES}
K2 = C["k2"]
LAB = {sp: C["labels_readers_long"][f"RL|{sp}"] for sp in SPACES}
LABR = {k: v for k, v in C["labels"].items()}                              # the readers stage's six labels, for the one sentence
INTERIM_WORD = "K-2-ISOLATED"                                               # the word the READERS landing issued
word = K2["word"]
assert not K2["void_cells"] or True

NUMS: set[str] = set()
PAIRS: list[str] = []


def n(x, fmt="{:+.4f}"):
    s = fmt.format(x)
    NUMS.add(s.lstrip("+"))
    return s


def bound(x):
    """Six decimals wherever a D value sits near the +0.005 floor or near zero (a four-decimal print would land ON the
    floor or hide the sign); four decimals otherwise."""
    if abs(x - 0.005) < 0.0005 or abs(x) < 0.0005:
        return n(x, "{:+.6f}")
    return n(x)


def ci(row):
    return f"{bound(row['margin'])} [{bound(row['ci95'][0])}, {bound(row['ci95'][1])}]"


def pair_ci(rp, rr):
    s = f"{ci(rp)} / {ci(rr)}"
    PAIRS.append(s)
    return s


def pp(a, b, fmt="{:+.4f}"):
    s = f"{n(a, fmt)} / {n(b, fmt)}"
    PAIRS.append(s)
    return s


def rs(s, sp):
    return P[s]["per_reader_space"][f"RL|{sp}"]


def row(s, sp, key):
    return next(m for m in rs(s, sp)[key] if m["offset"] == 2 and m["capacity"] == "mlp256")


def seeds(rowd):
    return ", ".join(n(v) for v in rowd["per_seed_margin"].values())


CELL: dict = {}
for sp in SPACES:
    lab = LAB[sp]
    d = {s: row(s, sp, "d_fplus_b_vs_fplus_r") for s in P}
    mt = {s: row(s, sp, "mt_fplus_b_vs_fplus") for s in P}
    mn = {s: row(s, sp, "mn_r_fplus_r_vs_fplus") for s in P}
    mf = {s: row(s, sp, "mf_fplus_vs_a") for s in P}
    mfx = {s: row(s, sp, "mfx_fplus_vs_linear_a") for s in P}
    mc_rows = {s: [m for m in rs(s, sp)["mc_fplus_vs_c"] if m["offset"] == 2] for s in P}
    rv = {s: rs(s, sp)["reader_valid"] for s in P}
    be = {s: rs(s, sp)["best_epochs"] for s in P}
    assert lab["gate"]["primary"]["margin"] == d["p"]["margin"] and lab["gate"]["replication"]["margin"] == d["r"]["margin"]
    ha = {s: [e for arm in ("fplus", "fplus_b", "fplus_r") for e in be[s][arm]] for s in P}
    CELL[sp] = {
        "label": lab["label"], "licence": lab["licence"], "reason": lab["licence_reason"],
        "d": pair_ci(d["p"], d["r"]), "d_seeds": {s: seeds(d[s]) for s in P},
        "mt": pair_ci(mt["p"], mt["r"]), "mn": pair_ci(mn["p"], mn["r"]),
        "mf": pair_ci(mf["p"], mf["r"]), "mfx": pair_ci(mfx["p"], mfx["r"]),
        "mc": (pair_ci(mc_rows["p"][0], mc_rows["r"][0]) if mc_rows["p"] and mc_rows["r"] else None),
        "minfloor": pp(rv["p"]["min_acc_minus_floor"], rv["r"]["min_acc_minus_floor"]),
        "mfup": pp(rv["p"]["mf_gate_ci_upper"], rv["r"]["mf_gate_ci_upper"]),
        "mfxup": pp(rv["p"]["mfx_gate_ci_upper"], rv["r"]["mfx_gate_ci_upper"]),
        "valid": (rv["p"]["ok"], rv["r"]["ok"]),
        "be": {s: {arm: ", ".join(str(e) for e in be[s][arm]) for arm in ("fplus", "fplus_b", "fplus_r", "a")} for s in P},
        "med_ha": {s: statistics.median(ha[s]) for s in P}, "max_ha": {s: max(ha[s]) for s in P},
        "d_raw": {s: d[s]["margin"] for s in P}, "mt_raw": {s: mt[s]["margin"] for s in P}, "mn_raw": {s: mn[s]["margin"] for s in P},
        "d_hi": {s: d[s]["ci95"][1] for s in P}, "d_lo": {s: d[s]["ci95"][0] for s in P},
        "mt_hi": {s: mt[s]["ci95"][1] for s in P}, "mn_hi": {s: mn[s]["ci95"][1] for s in P}, "mt_fires": lab["mt_fires_triple"],
    }
    for s in P:
        for arm in be[s]:
            NUMS.update(str(e) for e in be[s][arm])
        NUMS.add(str(CELL[sp]["med_ha"][s]).rstrip("0").rstrip(".") if isinstance(CELL[sp]["med_ha"][s], float) else str(CELL[sp]["med_ha"][s]))


def twin_phrase(mts):
    """The equal-dims-only fire's shape from Mt's sign on both harvests (D = Mt - Mn_r): Mt positive on both -> the fire is
    INFLATED by the twin's own cost (F-25's case; the instrument's own words, run_reader_lens.py); Mt at most zero on
    both -> the twin's cost is the larger of two costs (R-N's case); mixed -> neither shape named."""
    mts = list(mts)                                   # a generator would be spent by the first all()
    assert len(mts) == 2
    if all(m > 0 for m in mts):
        return "inflated by the twin's own cost"
    if all(m <= 0 for m in mts):
        return "the twin's larger cost"
    return "the twin's cost, Mt's sign differing across harvests"


def short_label(sp):
    i = CELL[sp]
    if i["label"] == "SURVIVES-STRONGER" and i["licence"] == "equal-dims-only":
        return f"SURVIVES-STRONGER (EQUAL-DIMS-ONLY, {twin_phrase(i['mt_raw'].values())})"
    if i["label"] == "SURVIVES-STRONGER":
        return f"SURVIVES-STRONGER ({i['licence'].upper()} licence)"
    return i["label"]


def long_label(sp):
    i = CELL[sp]
    if i["label"] == "SURVIVES-STRONGER" and i["licence"] == "equal-dims-only":
        return f"SURVIVES-STRONGER (EQUAL-DIMS-ONLY: Mt {i['mt']}, Mn_r {i['mn']}; the fire is {twin_phrase(i['mt_raw'].values())})"
    return short_label(sp)


def readers_short(key):
    v = LABR[key]
    if v["label"] == "SURVIVES-STRONGER" and v["licence"] == "equal-dims-only":
        return f"SURVIVES-STRONGER (EQUAL-DIMS-ONLY, {twin_phrase(v['mt'][role]['margin'] for role in ('primary', 'replication'))})"
    if v["label"] == "SURVIVES-STRONGER":
        return f"SURVIVES-STRONGER ({v['licence'].upper()} licence)"
    return v["label"]


def knife(info):
    notes = []
    for s in P:
        hi = info["d_hi"][s]
        if hi < 0.005 and round(hi, 4) >= 0.005:
            notes.append(f"the {ROLE[s]}'s D upper {n(hi, '{:+.6f}')} at six decimals, below the +0.005 floor")
    return ("; " + "; ".join(notes)) if notes else ""


def cell_word(sp):
    info = CELL[sp]
    lab = info["label"]
    twin_cost = (all(info["mn_hi"][s] < 0 for s in P) and all(info["mt_raw"][s] <= 0 for s in P) and all(info["d_lo"][s] > 0 for s in P))
    cost_note = (" — D is CI-clear positive on both harvests only because the corrected twin COSTS (Mn_r CI-clear negative on "
                 "both) while Mt is not positive" if twin_cost else "")
    if lab == "ABSORBED":
        base = (f"narrowed: the stronger-reader residual at {SPACE_WORD[sp]} excludes reader {READER_WORD['RL']} (one D row per "
                f"harvest, every upper below +0.005{knife(info)}){cost_note}")
        if sp != L1:
            base = f"OPEN at the registered reader (F-25's SPLIT stands); ABSORBED under reader {READER_WORD['RL']} beside it — " + base
        return base
    if lab == "NOT-SHOWN":
        return f"not overturned, not narrowed (a straddle never narrows){cost_note}"
    if lab == "SPLIT":
        return "not settled across harvests at this power; no narrowing, no reopen"
    if lab == "SURVIVES-STRONGER":
        lic = f"SURVIVES-STRONGER with the {info['licence'].upper()} licence"
        if info["licence"] == "equal-dims-only":
            reasons = []
            if any(info["mt_hi"][s] < 0 for s in P):
                reasons.append("Mt's CI95 upper below zero on " + " and ".join(ROLE[s] for s in P if info["mt_hi"][s] < 0))
            if any(info["mn_hi"][s] < 0 for s in P):
                reasons.append("Mn_r's CI95 upper below zero on " + ("both harvests" if all(info["mn_hi"][s] < 0 for s in P)
                                                                     else " and ".join(ROLE[s] for s in P if info["mn_hi"][s] < 0)))
            mt_pos = all(info["mt_raw"][s] > 0 for s in P)
            if mt_pos:
                excess = " / ".join(n(info["d_raw"][s] - 0.005, "{:+.6f}") for s in P)
                mt_hi_mat = [ROLE[s] for s in P if info["mt_hi"][s] >= 0.005]
                lic += (f" (Mn_r's CI95 upper below zero on {'both harvests' if all(info['mn_hi'][s] < 0 for s in P) else 'one harvest'}; "
                        f"Mt's is not): D {info['d']} clears the +0.005 floor (by {excess}) only with the twin's own cost — the "
                        f"aligned block adds Mt {info['mt']} over fplus, CI-clear positive on both harvests with the points below "
                        f"+0.005 (the triple rule does not fire"
                        + (f"; the {' and '.join(mt_hi_mat)}'s upper bound does not exclude a material gain" if mt_hi_mat else "")
                        + f"), and the prompt-deranged block costs Mn_r {info['mn']}; since D = Mt - Mn_r the fire is INFLATED by the "
                        f"twin's own cost (F-25's case), unlike R-N's, where both terms were costs; equal-dims evidence that the "
                        f"aligned block beats a same-marginal deranged block at this lens under this reader, NOT a material margin "
                        f"over the free baseline")
            else:
                lic += (f" (pinned reasons: {'; '.join(reasons)}): the fire is PRODUCED by the gap between two costs where Mt is not "
                        f"positive — D = Mt - Mn_r exactly, both terms sharing the fplus base (Mt {info['mt']}; Mn_r {info['mn']}, "
                        f"CI-clear negative on {'both harvests' if all(info['mn_hi'][s] < 0 for s in P) else 'one harvest'}); equal-dims "
                        f"evidence that the aligned stream carries some label-relevant structure compared with noise, NOT that "
                        f"telemetry adds over the free baseline")
        else:
            lic += (f": Mt {info['mt']} and Mn_r {info['mn']} both with CI95 uppers at or above zero on both harvests; Mt's triple "
                    f"rule {'fires' if info['mt_fires']['primary'] and info['mt_fires']['replication'] else 'does not fire'} on both")
        if sp == LOP:
            bal = CELL[BAL]["label"]
            if bal in ("ABSORBED", "NOT-SHOWN"):
                # D_lop - D_bal = (Mt_lop - Mt_bal) - (Mn_lop - Mn_bal), exactly, per harvest: the twin term and the Mt term
                gap = {s: info["d_raw"][s] - CELL[BAL]["d_raw"][s] for s in P}
                twin_t = {s: CELL[BAL]["mn_raw"][s] - info["mn_raw"][s] for s in P}
                mt_t = {s: info["mt_raw"][s] - CELL[BAL]["mt_raw"][s] for s in P}
                assert all(abs(gap[s] - (mt_t[s] + twin_t[s])) < 1e-12 for s in P)
                assert all(twin_t[s] > mt_t[s] and twin_t[s] > gap[s] / 2 for s in P)       # "most of the gap" is the twin term
                mt_lo = {sp2: {s: row(s, sp2, "mt_fplus_b_vs_fplus")["ci95"][0] for s in P} for sp2 in (LOP, BAL)}
                assert all(mt_lo[sp2][s] > 0 for sp2 in (LOP, BAL) for s in P)                # "all CI-clear"
                assert all(row(s, BAL, "mn_r_fplus_r_vs_fplus")["ci95"][0] <= 0 for s in P)  # balanced Mn_r "not CI-clear"
                assert all(info["mn_hi"][s] < 0 for s in P) and all(CELL[BAL]["mn_raw"][s] >= 0 for s in P)
                six = "{:+.6f}"
                lic += ("; the lopsided lens never decides a reopen, so this cell counts as ISOLATED whatever its licence; read beside "
                        f"the balanced cell under the same reader ({bal}), it is said in the LENS words the block pins — mostly "
                        f"mega-group membership — qualified in the same sentence: under this reader the lopsided-minus-balanced D "
                        f"gap, {pp(gap['p'], gap['r'], six)}, splits exactly into a twin term (balanced Mn_r minus lopsided Mn_r) of "
                        f"{pp(twin_t['p'], twin_t['r'], six)} and an Mt term of {pp(mt_t['p'], mt_t['r'], six)} (all three from the unrounded "
                        f"margins; Mt {info['mt']} "
                        f"lopsided against {CELL[BAL]['mt']} balanced, all CI-clear), so most of the gap is the twin's SIGN, a cost at "
                        f"the lopsided lens ({info['mn']}) against a gain at the balanced one ({CELL[BAL]['mn']}, not CI-clear); the "
                        f"cross-lens difference itself is untested (no paired interval), and the phrase names where the twin's cost "
                        f"falls, not a larger telemetry gain at the lopsided lens")
            else:
                lic += f"; the lopsided lens never decides a reopen (ISOLATED whatever its licence); the balanced cell under the same reader reads {bal}"
        return lic + "; no reopen"
    if lab == "READER-INVALID":
        return "VOID (READER-INVALID; the failing leg named in the readouts)"
    return lab


WORDS = {sp: cell_word(sp) for sp in SPACES}
reopen_grade = {sp: (CELL[sp]["label"] == "SURVIVES-STRONGER" and CELL[sp]["licence"] == "full"
                     and CELL[sp]["mt_fires"]["primary"] and CELL[sp]["mt_fires"]["replication"]) for sp in SPACES}
S1_TRIG = list(K2["s1_trigger_readers"])
K2_QUAL = "under readers R-N, R-T and R-L at S3; one more family of readers, not K-2's universal"


def cells_at_all(sp):
    parts = [f"{READER_WORD[r]} {readers_short(f'{r}|{sp}')} (D {ci(LABR[f'{r}|{sp}']['gate']['primary'])} / {ci(LABR[f'{r}|{sp}']['gate']['replication'])})"
             for r in ("RN", "RT")]
    parts.append(f"{READER_WORD['RL']} {long_label(sp)} (D {CELL[sp]['d']})")
    return "; ".join(parts)


def survivor_tag(cell):
    r, sp = cell.split("|", 1)
    if r == "RL":
        i = CELL[sp]
        if i["licence"] == "equal-dims-only":
            return f"{cell} (EQUAL-DIMS-ONLY, {'inflated by the twin' + chr(39) + 's own cost' if all(i['mt_raw'][s] > 0 for s in P) else 'two costs'})"
        return f"{cell} ({i['licence'].upper()} licence)"
    v = LABR[cell]
    if v["licence"] == "equal-dims-only":
        mt_pos = all(v["mt"][role]["margin"] > 0 for role in ("primary", "replication"))
        return f"{cell} (EQUAL-DIMS-ONLY, {'inflated by the twin' + chr(39) + 's own cost' if mt_pos else 'two costs'})"
    return f"{cell} ({(v['licence'] or 'no').upper()} licence)"


survivors = ", ".join(survivor_tag(c) for c in K2["survives_stronger"])
iso_l3 = any(c.split("|", 1)[1] != L1 for c in K2["survives_stronger"])
all_lop = all(c.split("|", 1)[1] == LOP for c in K2["survives_stronger"])
if word == "K-2-ISOLATED":
    k2_text = (f"K-2-ISOLATED, FINAL — the one sentence over STAGE READERS and STAGE READERS-LONG ({K2_QUAL}): the SURVIVES-STRONGER "
               f"cells {survivors}" + (", both at the lopsided lens, which never decides a reopen" if all_lop else "")
               + "; no reopen-grade cell anywhere; " + ("S1 not run (final)" if not S1_TRIG else f"S1 pending under {', '.join(S1_TRIG)}")
               + "; the S3 L1 kill stands at the registered reader"
               + ("; S3 L3 stays OPEN at the registered reader (F-25's SPLIT)" if iso_l3 else "")
               + "; not settled across readers / harvests at this power; no reopen"
               + f"; narrowed at {', '.join(K2['narrowed_cells'])}, not narrowed at {', '.join(K2['not_narrowed_cells']) or 'none'}"
               + f"; the cells: at L1 {cells_at_all(L1)}; at the lopsided L3 {cells_at_all(LOP)}; at the balanced L3 {cells_at_all(BAL)}")
elif word == "K-2-REOPENED-AT":
    k2_text = (f"K-2-REOPENED-AT {', '.join(K2['reopened'])} — PROVISIONAL until the reader-matched rider passes under its own dated "
               f"registration; the registered-reader kill stands as a statement about that reader; the next registered steps are "
               f"the reader-matched rider and then a reader-matched conversion attempt, not a claim of conversion; the cells: at L1 "
               f"{cells_at_all(L1)}; at the lopsided L3 {cells_at_all(LOP)}; at the balanced L3 {cells_at_all(BAL)}")
elif word == "K-2-UNSETTLED":
    k2_text = (f"K-2-UNSETTLED, FINAL ({K2_QUAL}): the SPLIT cell(s) {', '.join(K2['split'])} named with their numbers; the S3 L1 "
               f"kill stands at the registered reader; not settled across readers / harvests at this power; no reopen; the cells: "
               f"at L1 {cells_at_all(L1)}; at the lopsided L3 {cells_at_all(LOP)}; at the balanced L3 {cells_at_all(BAL)}")
elif word == "K-2-NOT-OVERTURNED-AT-S3":
    k2_text = (f"K-2-NOT-OVERTURNED-AT-S3, FINAL ({K2_QUAL}): no cell overturned the registered reader's label; the cells: at L1 "
               f"{cells_at_all(L1)}; at the lopsided L3 {cells_at_all(LOP)}; at the balanced L3 {cells_at_all(BAL)}; narrowed at "
               f"{', '.join(K2['narrowed_cells']) or 'none'}, not narrowed at {', '.join(K2['not_narrowed_cells']) or 'none'}")
else:
    k2_text = f"{word}: no valid cell; VOID cells {', '.join(K2['void_cells'])}"
if K2["over_valid_cells_only"]:
    k2_text += f" — over the valid cells; {', '.join(K2['void_cells'])} VOID"
changed = ("the word is unchanged from the READERS landing's interim K-2-ISOLATED" if word == INTERIM_WORD
           else f"the word CHANGED from the READERS landing's interim {INTERIM_WORD} to {word}")

# ---- landing condition: the RL gate cell rerun (clean clone) and the R0 linear (a) identity against the lens rows ----
state_rows = [json.loads(ln) for ln in (ROOT / "results/real/readers_long_s3.json.state.jsonl").read_text(encoding="utf-8").splitlines()][1:]
gate = next(x for x in state_rows if x["cell"] == f"{L1}|off2|fplus_b|mlp256|s0" and x.get("reader") == "RL")
rr_state = [json.loads(ln) for ln in Path(str(S / "rerun/rerun_RL_L1_fplus_b.json") + ".state.jsonl").read_text(encoding="utf-8").splitlines()][1:]
rr = next(x for x in rr_state if x["cell"] == gate["cell"])
diff = sorted(k for k in set(gate) | set(rr) if k != "runtime_s" and json.dumps(gate.get(k), sort_keys=True) != json.dumps(rr.get(k), sort_keys=True))
RERUN = {"identical": diff == [], "diff": diff, "acc": pp(gate["test_acc"], rr["test_acc"], "{:.6f}"), "rt": pp(gate["runtime_s"], rr["runtime_s"], "{:.1f}")}
R0_IDENT = {}
for s, name, lens_name in (("p", "readers_long_s3.json", "lens_s3.json"), ("r", "readers_long_s3_r.json", "lens_s3_r.json")):
    _, long_cells = rl.verify_payload(ROOT / "results/real" / name, ROLE[s], expect_stage="readers_long")
    _, lens_cells = rl.verify_payload(ROOT / "results/real" / lens_name, ROLE[s], expect_stage="lens")
    R0_IDENT[s] = rl.rerun_identity(long_cells, lens_cells)["all_identical"]
runtime = pp(P["p"]["runtime_s"], P["r"]["runtime_s"], "{:,.1f}")
hours = pp(P["p"]["runtime_s"] / 3600, P["r"]["runtime_s"] / 3600, "{:.2f}")
FIRST_LAUNCH_LOG = S / "readers_long_s3_first_launch_memoryerror.log"
assert FIRST_LAUNCH_LOG.exists() and "MemoryError" in FIRST_LAUNCH_LOG.read_text(encoding="utf-8")
CARRIED = ("0.0030", "0.0032", "0.0016", "0.0045", "0.004951", "0.0006", "0.0007", "-0.0002", "0.0014", "0.0015", "0.0080", "0.0130",
           "0.0062", "0.0097", "0.0095", "0.0169", "-0.0041", "-0.0015", "-0.0063", "-0.0018", "-0.0055", "0.0029", "-0.0121",
           "-0.0144", "-0.0141", "-0.0100", "-0.0173", "-0.0116", "0.0012", "0.0008", "-0.0003", "0.0026", "-0.0006", "0.0023",
           "0.0040", "0.0025", "0.0054", "0.0027", "0.0061", "0.0003", "0.0028", "0.0013", "0.0019", "0.0004", "-0.0011",
           "0.0018", "0.0221", "0.0195", "0.0721", "0.0730", "0.0206", "0.0207", "0.0147", "0.0173", "-0.0031", "-0.0067",
           "0.0041", "0.0053", "0.0132", "165", "455", "268", "193", "461", "510", "20", "657", "4753", "5777", "1024", "2048",
           "128", "0.25", "0.24999", "0.7", "0.6", "0.5", "0.35", "0.1", "0.03", "0.05", "0.65", "0.75", "0.4", "0.2", "0.02",
           "0.55", "0.85", "0.45", "0.15", "3e-3", "1.0", "256", "210", "294,146", "148,276", "16", "31", "32", "15", "5", "10",
           "2026", "05", "06", "04", "09", "24", "25", "27", "28", "29", "0.008", "0.0081", "0.0141", "0.0203", "0.044", "0.0652",
           "0.0792", "0.41", "0.59", "3.1", "-0.0007", "-0.0009", "0.0133", "0.0182", "-0.0000", "-0.0013", "0.01", "0.0866",
           "0.0870", "0.0875", "0.0882", "0.0011", "-0.0001", "-0.0046", "-0.0037", "-0.0071", "-0.0033", "0.0001", "-0.0022",
           "-0.0052", "-0.0020", "-0.0062", "-0.0047", "-0.0087", "-0.0056", "0.0009", "0.0020", "0.0005", "0.0035", "0.0002",
           "-0.0019", "-0.0034", "-0.0004", "-0.0027", "-0.0045", "0.0010", "-0.0005", "0.0011", "0.0024", "0.0021", "0.0042",
           "-0.0000", "23,314.0", "11,799.0", "6.48", "3.28", "15,302.5", "7,808.9", "4.25", "2.17", "75", "72", "49", "12",
           "0.0063", "-0.0028", "0.0022", "0.0017", "0.0038", "-0.0026", "0.0043", "0.0052", "0.0058", "0.0048", "0.0050", "0.0036",
           "0.0044", "0.0046", "0.0033", "0.0034", "0.0039", "0.0047", "0.0049", "0.0051", "0.0056", "0.0057", "0.0059", "0.0064",
           "0.0066", "0.0069", "0.0072", "0.0074", "0.0078")
# CARRIED_ROWS (2026-10-09): literals already in the HEAD cells the applier extends in place (F-24 / F-25 / F-28 status
# cells, README's existence row, REPORT's and FINDINGS_INDEX's F-28 rows); `check --added` sees each re-emitted row whole.
# Each was verified to sit once in the removed line and once in the added line, every rewritten line being its HEAD line
# plus one inserted span; none is a READERS-LONG number.
CARRIED_ROWS = ("-0.0012", "-0.0016", "0.003", "0.0160", "0.0187", "0.0232", "0.0258", "0.267", "0.307", "0.0113", "0.0055",
                "0.0091")

# ---- scoring: the clauses READERS-LONG decides ----
A = [
    ("(7) if READERS-LONG runs, every label ABSORBED or NOT-SHOWN (modal, about 0.8) [NEW: PENDING at the READERS landing]", all(CELL[sp]["label"] in ("ABSORBED", "NOT-SHOWN") for sp in SPACES)),
    ("(8) STAGE S1 does not run (modal: 0.95) [FINALISED: HELD provisionally at the READERS landing]", not S1_TRIG),
    ("(9) no READER-INVALID anywhere [FINALISED over LENS, READERS and READERS-LONG: HELD through LENS and READERS at the READERS landing]", all(CELL[sp]["label"] != "READER-INVALID" for sp in SPACES)),
    ("(6) K-2-NOT-OVERTURNED-AT-S3 (modal word) [RESTATED: scored FAILED at the READERS landing; the word now FINAL over both reader stages]", word == "K-2-NOT-OVERTURNED-AT-S3"),
]
A_held, A_lines = lt.score(A)
K = [("(6) K-2-UNSETTLED (modal word under the round-one definitions) [RESTATED: scored FAILED at the READERS landing; the word now FINAL over both reader stages]", word == "K-2-UNSETTLED")]
K_held, K_lines = lt.score(K)
# The READERS landing's tallies (docs/BLUEPRINT.md, that stage's OUTCOME): these clauses overlap them, so no sum is formed.
READERS_TALLY = "the READERS landing's 9 of 14 (assistant) and 4 of 8 (critic)"
full_any = any(CELL[sp]["label"] == "SURVIVES-STRONGER" and CELL[sp]["licence"] == "full" for sp in SPACES) or \
    any(v["label"] == "SURVIVES-STRONGER" and v["licence"] == "full" for v in LABR.values())
reopen_any = any(reopen_grade.values()) or bool(K2.get("reopened"))
crit5_rl = CELL[LOP]["label"] == "SPLIT" or (CELL[LOP]["label"] == "SURVIVES-STRONGER" and CELL[LOP]["licence"] == "equal-dims-only")
CALIB_NOTE = (f"CALIBRATION-ONLY clauses now final: the assistant's (6) SURVIVES-STRONGER with the FULL licence at any cell, about "
              f"0.1 ({'occurred' if full_any else 'did not occur'}, final over both reader stages); (6) a reopen-grade cell, about 0.05 "
              f"({'occurred' if reopen_any else 'did not occur'}, final); the critic's (5) SPLIT or equal-dims-only SURVIVES at the "
              f"lopsided L3, together 0.5 (occurred at the READERS landing{', and again under R-L' if crit5_rl else '; not under R-L'})")
TALLY_NOTE = (f"these tallies are NOT additive to {READERS_TALLY}: one clause is new here ((7)'s second half), two are finalised "
              f"((8), (9)) and one is restated per side ((6))")
BUDGET_NOTE = (f"READERS-LONG measured {hours} hours elapsed on CPU against the estimate of about 6.7-7.6 on the primary and half on "
               f"the replication (a description; no clause of either prediction priced this stage)")
a_failed = [ln for ln in A_lines if ln.endswith("FAILED")]
k_failed = [ln for ln in K_lines if ln.endswith("FAILED")]
surprises = {
    "a reader reading SURVIVES-STRONGER at the lopsided lens and ABSORBED at the balanced one": CELL[LOP]["label"] == "SURVIVES-STRONGER" and CELL[BAL]["label"] == "ABSORBED",
    "a reopen-grade cell at L1 under this reader": reopen_grade[L1],
    "a READER-INVALID under R-L": any(CELL[sp]["label"] == "READER-INVALID" for sp in SPACES),
    f"Mn_r non-negative at the balanced lens on both harvests (Mn_r {CELL[BAL]['mn']}, "
    f"{'neither' if all(row(s, BAL, 'mn_r_fplus_r_vs_fplus')['ci95'][0] <= 0 for s in P) else 'not both'} CI-clear)":
        all(CELL[BAL]["mn_raw"][s] >= 0 for s in P),
}
fired = [k for k, v in surprises.items() if v]
SURPRISE_NOTE = (f" SURPRISES (pre-registered) that OCCURRED under R-L: {'; '.join(fired)}" if fired else " SURPRISES (pre-registered): none occurred under R-L") + "."


def cell_para(sp):
    i = CELL[sp]
    lic = (f" licence {i['licence'].upper()}" + (f" ({i['reason']})" if i["reason"] else "")) if i["licence"] else ""
    return (f"{READER_WORD['RL']} at {SPACE_WORD[sp]}: {i['label']}{lic} — D {i['d']} (per seed {i['d_seeds']['p']} / {i['d_seeds']['r']}); "
            f"Mt {i['mt']}; Mn_r {i['mn']}; Mf {i['mf']}; Mf_x {i['mfx']}" + (f"; Mc {i['mc']}" if i["mc"] else "") +
            f"; reader validity {'three of three legs on both' if all(i['valid']) else 'FAILED on ' + ' / '.join(ROLE[s] for s in P if not i['valid'][{'p': 0, 'r': 1}[s]])} "
            f"(min gate-cell accuracy minus floor {i['minfloor']}; Mf gate CI upper {i['mfup']}; Mf_x gate CI upper {i['mfxup']}); "
            f"best VAL epochs of 60 fplus [{i['be']['p']['fplus']}] / [{i['be']['r']['fplus']}], fplus_b [{i['be']['p']['fplus_b']}] / "
            f"[{i['be']['r']['fplus_b']}], fplus_r [{i['be']['p']['fplus_r']}] / [{i['be']['r']['fplus_r']}], (a) [{i['be']['p']['a']}] / "
            f"[{i['be']['r']['a']}] (median over the nine h_a-arm cells {i['med_ha']['p']} / {i['med_ha']['r']}); consequence: {WORDS[sp]}.")


cells_text = " ".join(cell_para(sp) for sp in SPACES)
labels_short = "; ".join(f"{READER_WORD['RL']} at {SPACE_WORD[sp]} {short_label(sp)}" for sp in SPACES)
s1_sentence = ("STAGE S1 " + (f"is TRIGGERED under {', '.join(S1_TRIG)} (a reopen-grade cell at L1 or the balanced L3) and is the next registered stage"
               if S1_TRIG else "does NOT run (no reopen-grade cell at L1 or the balanced L3 under any reader) — FINAL"))
rerun_sentence = (f"{READER_WORD['RL']} gate cell at L1 (seed 0, fplus_b) re-run from a clean clone at {LAUNCH}: "
                  f"{'identical except runtime_s' if RERUN['identical'] else 'NOT identical: differing ' + ', '.join(RERUN['diff'])} "
                  f"(test_acc {RERUN['acc']}; runtime {RERUN['rt']} s)")
r0_sentence = (f"the three R-0 linear (a) cells at the balanced lens, re-trained in this stage, are "
               f"{'identical' if all(R0_IDENT.values()) else 'NOT identical'} to STAGE LENS's proxy (a) rows except runtime_s on "
               f"{'both harvests' if all(R0_IDENT.values()) else ' / '.join(ROLE[s] + (' yes' if R0_IDENT[s] else ' no') for s in P)}")
launch_note = (f"LAUNCH RECORD: the primary's FIRST launch (2026-10-05 14:44) died at data load with a numpy MemoryError (1.64 GiB "
               f"for the hidden array) BEFORE any state header or row was written (the traceback stops at data.array, ahead of the "
               f"header write, so the FRESH-STATE pin was never bypassed) — free RAM read 6.4 GB of 31.8 GB at about 14:45 with "
               f"python holding under 2 GB, the rest held outside this lane (session readouts, not committed); the probable, not "
               f"shown, cause is both harvests loading at once, the replication having started at about 14:45 — and was relaunched "
               f"at 14:47 once the replication had loaded, a fresh registered run from the same HEAD (resumed_cells 0); the two runs "
               f"then ran concurrently (the primary about 14:48 to 21:47, the replication about 14:45 to 18:31), free RAM read 3.9 GB "
               f"at about 14:51 and 4.1 GB at about 18:32 (two session readouts, not committed); the first launch's log is kept in "
               f"the session scratchpad")
mt_all = [CELL[sp]["mt_raw"][s] for sp in SPACES for s in P]
mt_rng = f"{n(min(mt_all))}..{n(max(mt_all))}"
mt_clear = all(CELL[sp]["mt_raw"][s] > 0 and row(s, sp, "mt_fplus_b_vs_fplus")["ci95"][0] > 0 for sp in SPACES for s in P)
d_clear_p = [SPACE_WORD[sp] for sp in (L1, BAL) if CELL[sp]["d_lo"]["p"] > 0]
d_strad_r = [SPACE_WORD[sp] for sp in (L1, BAL) if CELL[sp]["d_lo"]["r"] <= 0]
mt_pts_below = all(v < 0.005 for v in mt_all)
mt_hi_mat = [(sp, s) for sp in SPACES for s in P if CELL[sp]["mt_hi"][s] >= 0.005]
mt_hi_words = "; ".join(f"the {ROLE[s]}'s upper bound at {SPACE_WORD[sp]}, {n(CELL[sp]['mt_hi'][s])}" for sp, s in mt_hi_mat)
# the largest gate-cell (off2, mlp256) Mt point in the lane: STAGE LENS's R-0, STAGE READERS's R-N / R-T, this stage's R-L
LENS = {"p": json.loads((ROOT / "results/real/lens_s3.json").read_text(encoding="utf-8")),
        "r": json.loads((ROOT / "results/real/lens_s3_r.json").read_text(encoding="utf-8"))}
RDR = {"p": json.loads((ROOT / "results/real/readers_s3.json").read_text(encoding="utf-8")),
       "r": json.loads((ROOT / "results/real/readers_s3_r.json").read_text(encoding="utf-8"))}


def gate_mt(pl, key):
    return next(m for m in pl["per_reader_space"][key]["mt_fplus_b_vs_fplus"] if m["offset"] == 2 and m["capacity"] == "mlp256")


lane_mt = [(gate_mt(src[s], key)["margin"], key, s, src) for src in (LENS, RDR, P) for s in P for key in src[s]["per_reader_space"]]
top_pt, top_key, _, top_src = max(lane_mt, key=lambda t: t[0])
top_r, top_sp = top_key.split("|", 1)
top_name = {"R0": "STAGE LENS's R-0", "RN": "STAGE READERS's R-N", "RT": "STAGE READERS's R-T", "RL": "R-L"}[top_r]
top_pair = pair_ci(gate_mt(top_src["p"], top_key), gate_mt(top_src["r"], top_key))
mn_gain = {sp: all(CELL[sp]["mn_raw"][s] > 0 for s in P) for sp in (L1, BAL)}
mn_clear = [(sp, s) for sp in (L1, BAL) for s in P if row(s, sp, "mn_r_fplus_r_vs_fplus")["ci95"][0] > 0]
assert all(mn_gain.values()) and all(CELL[sp]["mt_raw"][s] > CELL[sp]["mn_raw"][s] for sp in (L1, BAL) for s in P)
mn_pts = {sp: f"{bound(CELL[sp]['mn_raw']['p'])} / {bound(CELL[sp]['mn_raw']['r'])}" for sp in (L1, BAL)}
PAIRS.extend(mn_pts.values())
rl_words = (f"SAID IN WORDS for R-L: at twice the epochs and a third of the learning rate the h_a arms' best VAL epochs at the "
            f"gate cells are fplus [{CELL[L1]['be']['p']['fplus']}] / [{CELL[L1]['be']['r']['fplus']}] at L1 against (a) "
            f"[{CELL[L1]['be']['p']['a']}] / [{CELL[L1]['be']['r']['a']}] — the early-epoch pattern F-24 named persists under the "
            f"longer budget too (one reader; untested beyond that). Under R-L the aligned block adds a "
            f"{'CI-clear ' if mt_clear else ''}gain over fplus at every space on both harvests ({mt_rng}), "
            f"{'every point below +0.005' if mt_pts_below else 'not every point below +0.005'}"
            + (f" ({mt_hi_words}, does not exclude a material gain)" if mt_hi_mat else "")
            + f"; it is not the lane's largest: the largest gate-cell Mt point in the lane is {top_name} at "
            f"{SPACE_WORD[top_sp] if top_sp in SPACE_WORD else top_sp}, {top_pair}"
            + (", also below +0.005 at the point" if top_pt < 0.005 else "")
            + f". At L1 and the balanced L3 the twin also gains, by less (Mn_r {mn_pts[L1]} at L1, {mn_pts[BAL]} at the balanced "
            f"L3, {'none' if not mn_clear else 'not all'} CI-clear), so D is positive there (CI-clear on the primary at "
            f"{' and '.join(d_clear_p) or 'neither space'}, straddling on the replication at {' and '.join(d_strad_r) or 'neither space'}) "
            f"while every D upper bound sits below +0.005 — which is what ABSORBED records; K-2 asks for a MATERIAL margin and none "
            f"is shown that is not bought by the twin's cost")
COND = "one of the block's two pinned conditional stages (READERS-LONG and S1)"
L1_ALL = [READER_WORD[r] for r in ("RN", "RT") if LABR[f"{r}|{L1}"]["label"] == "ABSORBED"] + ([READER_WORD["RL"]] if CELL[L1]["label"] == "ABSORBED" else [])
SURV_READERS = [READER_WORD[c.split("|", 1)[0]] for c in K2["survives_stronger"]]
K2_SCOPE = ((f"from the {' and '.join(SURV_READERS)} cell{'s' if len(SURV_READERS) > 1 else ''} at the lopsided L3; " if all_lop and SURV_READERS else "")
            + ("L1 itself ABSORBED under all three readers" if len(L1_ALL) == 3 else f"L1 ABSORBED under {', '.join(L1_ALL) or 'no reader'}"))
CNT_WORD = {1: "one", 2: "two", 3: "three", 4: "four"}
n_surv = len(K2["survives_stronger"])
SURV_SENT = (f"the {CNT_WORD[n_surv]} isolated survival{'s' if n_surv > 1 else ''} ({survivors}"
             + (", both at the lopsided L3" if all_lop and n_surv == 2 else (", at the lopsided L3" if all_lop else ""))
             + f") {'are' if n_surv > 1 else 'is'} equal-dims evidence against a same-marginal prompt-deranged block, not telemetry over "
             f"the free baseline") if n_surv else "no isolated survival"


def lr_word(x):
    return {0.001: "1e-3", 0.003: "3e-3"}[x]


def reader_regime(cfg, name):
    extra = f", towers {cfg['tower_a']} / {cfg['tower_b']}" if cfg["kind"] == "two_tower" else ""
    NUMS.update((str(cfg["epochs"]), lr_word(cfg["lr"])) + ((str(cfg["tower_a"]), str(cfg["tower_b"])) if extra else ()))
    return f"{READER_WORD[name]} ({cfg['capacity']}{extra}, {cfg['epochs']} epochs, lr {lr_word(cfg['lr'])})"


assert P["p"]["readers"] == P["r"]["readers"] and RDR["p"]["readers"] == RDR["r"]["readers"]
EVID_LONG = ["results/real/readers_long_s3.json", "results/real/readers_long_s3.json.state.jsonl", "results/real/readers_long_s3_r.json",
             "results/real/readers_long_s3_r.json.state.jsonl", "tests/test_reader_lens_readers_long_landing.py"]
EVID_READERS = ["results/real/readers_s3.json", "results/real/readers_s3.json.state.jsonl", "results/real/readers_s3_r.json",
                "results/real/readers_s3_r.json.state.jsonl", "tests/test_reader_lens_readers_landing.py"]
for f in EVID_LONG + EVID_READERS + ["tools/run_reader_lens.py"]:
    assert (ROOT / f).exists(), f
REGIME_EVID = (f"REGIME AND EVIDENCE (this line and the STAGE READERS line above; F-28's regime and source lines name STAGE LENS's "
               f"only): F-28's regime with readers {reader_regime(RDR['p']['readers']['RN'], 'RN')} and "
               f"{reader_regime(RDR['p']['readers']['RT'], 'RT')} at STAGE READERS and {reader_regime(P['p']['readers']['RL'], 'RL')} "
               f"here, each read at its best VAL epoch, CPU at six threads, CUDA hidden; evidence: {', '.join(EVID_LONG)}; for the "
               f"STAGE READERS line {', '.join(EVID_READERS)}; the instrument tools/run_reader_lens.py ({TOOL_SHA12} as frozen)")
pending_final = ("the K-2 word is FINAL for this registration" if not S1_TRIG else
                 f"the K-2 word stays provisional until STAGE S1 lands under {', '.join(S1_TRIG)}")

f28_long = (f"- STAGE READERS-LONG ({TODAY}, appended at its landing; {COND}, run because STAGE READERS read "
            f"no SURVIVES-STRONGER or SPLIT at L1 or the balanced L3; both registered runs from the clean tree at {LAUNCH}, the "
            f"handoff commit after the READERS landing {READERS_LANDING}; 39 / 39 state rows, {runtime} s elapsed ({hours} hours "
            f"elapsed on CPU at six threads, CUDA hidden); the balanced space admitted on both verified lens payloads): THE ONE "
            f"K-2 SENTENCE over STAGE READERS and STAGE READERS-LONG, issued from the readers pair with the lens and long "
            f"payloads: {k2_text}; {changed}; {pending_final}. PER (R-L, SPACE), the frozen rules per cell: {cells_text} "
            f"{s1_sentence}. LANDING CONDITION: {rerun_sentence}; {r0_sentence}. {launch_note}. {rl_words}. PREDICTIONS "
            f"(the clauses this stage decides; the OUTCOME carries the list): the assistant's {A_held} of {len(A)} HELD "
            f"(FAILED: {'; '.join(ln.split(' -> ')[0] for ln in a_failed) if a_failed else 'none'}); the critic's {K_held} of {len(K)} "
            f"HELD (FAILED: {'; '.join(ln.split(' -> ')[0] for ln in k_failed) if k_failed else 'none'}); {TALLY_NOTE}; {CALIB_NOTE}; "
            f"{BUDGET_NOTE}.{SURPRISE_NOTE} "
            f"ABSORBED under a reader rests on one D row per harvest; four readers are one more family, not K-2's universal. "
            f"{REGIME_EVID}.")
f28_status = (f"; STAGE READERS-LONG landed {TODAY}: the FINAL K-2 word over both reader stages {word} ({K2_SCOPE}); under the "
              f"longer-budget reader {labels_short}; {'S1 triggered under ' + ', '.join(S1_TRIG) if S1_TRIG else 'S1 not run (final)'}")
f24_note = (f"; DATED NOTE {TODAY} (F-28, STAGE READERS-LONG): the S3 L1 kill re-tested under the longer-budget reader — "
            f"{READER_WORD['RL']} {long_label(L1)} (D {CELL[L1]['d']}; Mt {CELL[L1]['mt']}; Mn_r {CELL[L1]['mn']}); the FINAL K-2 word "
            f"at S3 over both reader stages {word} ({K2_SCOPE}); the registered-reader kill stands as a statement about that reader")
f25_note = (f"; DATED NOTE {TODAY} (F-28, STAGE READERS-LONG): the S3 L3 cell under the longer-budget reader — at the lopsided lens "
            f"{READER_WORD['RL']} {long_label(LOP)} (D {CELL[LOP]['d']}); at the balanced lens {READER_WORD['RL']} {long_label(BAL)} "
            f"(D {CELL[BAL]['d']}; Mn_r {CELL[BAL]['mn']}); K-2 at S3 L3 stays OPEN at the registered reader (the SPLIT stands as "
            f"registered); the FINAL K-2 word at S3 over both reader stages {word}")
wtd_status = (f"STATUS ({TODAY}, appended; F-28, READER-AND-LENS RE-TEST AT S3, STAGE READERS-LONG — {COND}, "
              f"the longer-budget reader R-L at the same gate cells; this block carries the ONE K-2 sentence over STAGE READERS and "
              f"STAGE READERS-LONG and supersedes the interim word of the READERS landing above):\n"
              f"S3: {k2_text}. {changed[0].upper() + changed[1:]}; {pending_final}. {s1_sentence}. The S3 L1 kill of 2026-09-06 stands as a statement about "
              f"the registered reader; S3 L3 stays OPEN (SPLIT) at the registered reader; one more family of readers, not K-2's "
              f"universal. Numbers and licences: FINDINGS.md F-28 (the STAGE READERS and STAGE READERS-LONG lines) and the block's "
              f"OUTCOME in docs/BLUEPRINT.md.")
oq17_note = (f"({TODAY} OUTCOME, STAGE READERS-LONG (F-28): the longer-budget reader at the same cells reads {labels_short}; the ONE "
             f"K-2 sentence over both reader stages: {word} ({changed}); {pending_final}; the stronger-reader residual at L1 is "
             f"narrowed under R-L as under R-N and R-T (ABSORBED narrows, not closes; NOT-SHOWN neither overturns nor narrows); "
             f"{s1_sentence}.)")
oq18_note = (f"({TODAY} OUTCOME, STAGE READERS-LONG (F-28): the S3 L3 cell under the longer-budget reader reads, at the lopsided "
             f"lens, {READER_WORD['RL']} {short_label(LOP)} and at the balanced lens {short_label(BAL)} (D rows in F-28); K-2 at S3 "
             f"L3 stays OPEN at the registered reader; the FINAL K-2 word at S3 {word}.)")
readme_note = (f"; DATED NOTE {TODAY} (F-28, STAGE READERS-LONG): under the longer-budget reader at the S3 gate cells {labels_short}; "
               f"the FINAL K-2 word at S3 over both reader stages {word} ({K2_QUAL}); {'S1 triggered' if S1_TRIG else 'S1 not run'}")
report_note = (f"; DATED NOTE {TODAY} (F-28, STAGE READERS-LONG): {labels_short}; the FINAL K-2 word at S3 {word}")
index_status = f"; STAGE READERS-LONG landed {TODAY}: FINAL {word}; {labels_short}; {'S1 triggered' if S1_TRIG else 'S1 not run'}"
index_para = lt.wrap(
    f"Stage READERS-LONG (added {TODAY}): {COND} — the longer-budget reader (60 epochs, lr 1e-3) at the same "
    f"three gate cells, 39 cells per harvest, CPU only, run because the readers stage read no SURVIVES-STRONGER or SPLIT at L1 or "
    f"the balanced L3. {labels_short}. The ONE K-2 sentence over both reader stages: {word} ({changed}). {s1_sentence}. Numbers "
    f"per cell in F-28. Kill-criterion outcome: "
    f"{'K-2 not overturned at S3 under this family of readers; the registered-reader kill stands' if word == 'K-2-NOT-OVERTURNED-AT-S3' else (word + ': the S3 L1 kill stands at the registered reader, S3 L3 stays OPEN; ' + SURV_SENT if word == 'K-2-ISOLATED' else word)}.", "")
HANDOFF_SHA, HANDOFF_SUBJ = subprocess.run(["git", "log", "-1", "--format=%h%x09%s", "HEAD"], cwd=ROOT, capture_output=True,
                                           text=True).stdout.strip().split("\t")
assert HANDOFF_SHA == "1fafdfe" and "READERS-LONG" in HANDOFF_SUBJ     # the mid-landing handoff, dated 2026-10-09
changelog_section = f"## {TODAY} - Reader-and-lens re-test at S3: stage READERS-LONG landed, the K-2 word final (branch espalier-trial)\n\n" + "\n".join(lt.wrap(b, "") for b in (
    f"- (the landing commit; its hash is recorded in the handoff's memory row, since a commit cannot cite itself) "
    f"feat(evidence): land the reader-and-lens stage READERS-LONG - both registered runs from the clean tree at {LAUNCH}, "
    f"results/real/readers_long_s3.json and readers_long_s3_r.json with their state files; {labels_short}; the ONE K-2 sentence "
    f"over both reader stages {word}; F-28's STAGE READERS-LONG line with dated notes on F-24 and F-25; the final K-2 STATUS line "
    f"in docs/WHY_THIS_DIES.md; OUTCOME notes under OQ-17 and OQ-18; pointers in README, docs/REPORT.md, docs/FINDINGS_INDEX.md; "
    f"tests/test_reader_lens_readers_long_landing.py; the block's OUTCOME.",
    f"- {HANDOFF_SHA} {HANDOFF_SUBJ} - the handoff row written between the read of the runs and this landing.",
    f"- {LAUNCH} docs(memory): log the reader-and-lens stage READERS landing - the handoff row; the stage launched from this commit."))
outcome = (f"- OUTCOME, STAGE READERS-LONG ({TODAY}; {COND}, run because STAGE READERS read no SURVIVES-STRONGER "
           f"or SPLIT at L1 or the balanced L3; both registered runs from the clean tree at {LAUNCH} (the handoff commit after the "
           f"READERS landing {READERS_LANDING}; the instrument {TOOL_SHA12} as frozen), 39 / 39 state rows, {runtime} s elapsed "
           f"({hours} hours elapsed on CPU at six threads, CUDA hidden, no resume, no torn bytes); the balanced space admitted on "
           f"both verified lens payloads; --conclude-from on the readers pair with --lens and --long reproduces and verifies all six "
           f"payloads and issues the one sentence; the critic's recompute round is recorded in a dated line below and in the "
           f"landing commit's body): THE ONE K-2 SENTENCE: {k2_text}; {changed}; {pending_final}. PER (R-L, SPACE): {cells_text} "
           f"{s1_sentence}. LANDING CONDITION: {rerun_sentence}; {r0_sentence}. {launch_note}. {rl_words}. {BUDGET_NOTE}. THE "
           f"CRITIC'S RECOMPUTE ROUND ({TODAY}): its own re-derivation from the state files agrees with the tool's combined "
           f"conclusion with a maximum difference of 0 over 630 compared numbers, every label and licence and the final word "
           f"matching; it checked both long payloads' R-0 linear (a) cells against the lens rows directly; its wording "
           f"requirements for this board (the inflated-case sentence, the qualified LENS words, the final ISOLATED sentence with "
           f"both survivors' licences, R-L's positive Mt in words, the six-decimal bounds near the floor and near zero) are in "
           f"this OUTCOME and in F-28. SCORING "
           f"of the clauses this stage decides (the five conventions): the assistant's {'; '.join(A_lines)} — {A_held} of {len(A)} HELD; "
           f"the critic's {'; '.join(K_lines)} — {K_held} of {len(K)} HELD; {TALLY_NOTE}. {CALIB_NOTE}.{SURPRISE_NOTE} "
           f"{REGIME_EVID}. CONSEQUENCES EXECUTED ({TODAY}): F-28's STAGE READERS-LONG "
           f"line and status; dated notes in F-24's and F-25's status cells; the final K-2 STATUS line in docs/WHY_THIS_DIES.md; "
           f"OUTCOME notes under OQ-17 and OQ-18; pointers in README's existence row, docs/REPORT.md, docs/FINDINGS_INDEX.md, "
           f"CHANGELOG.md; tests/test_reader_lens_readers_long_landing.py. "
           f"{'NEXT: STAGE S1 under ' + ', '.join(S1_TRIG) + ' from the landing commit, then the reader-matched rider before any REOPENED word is final.' if S1_TRIG else 'THE LANE CLOSES with this landing: every unconditional stage has landed, the conditional READERS-LONG has landed, and the conditional S1 did not trigger; the next program item is the negative-result report (docs/IDEAS.md rank 4), OQ-19 decided after.'}")

TEXTS = {
    "f28_long.txt": lt.wrap(f28_long, "  ", first_indent=""),
    "f28_status.txt": f28_status, "f24_note.txt": f24_note, "f25_note.txt": f25_note,
    "wtd_status.txt": "\n".join(lt.wrap(para, "") for para in wtd_status.split("\n")),
    "oq17_note.txt": lt.wrap(oq17_note, ""), "oq18_note.txt": lt.wrap(oq18_note, ""),
    "readme_note.txt": readme_note, "report_note.txt": report_note,
    "index_status.txt": index_status, "index_para.txt": index_para,
    "changelog_section.txt": changelog_section, "outcome.txt": lt.wrap(outcome, "  ", first_indent=""),
}
BANNED = ("K-2-STANDS", "overturned K-2", "proves", "kill fires at L3", "signal is rich", "CPU-hours", "no S1;")
lt.assert_banned(TEXTS, BANNED)
OUT.mkdir(parents=True, exist_ok=True)
for name, text in TEXTS.items():
    (OUT / name).write_text(text.rstrip("\n") + "\n", encoding="utf-8", newline="\n")
reg = {"nums": sorted(NUMS), "pairs": list(dict.fromkeys(PAIRS)), "banned": list(BANNED)}
(OUT / "numbers.json").write_text(json.dumps(reg, indent=1), encoding="utf-8", newline="\n")
summary = {"word": word, "changed": changed, "labels": {sp: CELL[sp]["label"] for sp in SPACES}, "licences": {sp: CELL[sp]["licence"] for sp in SPACES},
           "s1": S1_TRIG, "A": A_lines, "K": K_lines, "rerun": RERUN["identical"], "r0_identical": R0_IDENT, "hours": hours}
(OUT / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8", newline="\n")
print(json.dumps(summary, indent=1))
print(f"wrote {len(TEXTS)} texts; {len(NUMS)} numbers, {len(reg['pairs'])} pairs")
