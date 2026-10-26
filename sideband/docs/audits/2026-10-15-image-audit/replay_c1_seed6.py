# Read-only refuter check for S5a-C-1 (image audit 2026-10-15, section B item 3; the S5a
# refuter's script made tree-relative). Needs the per-prompt byproduct arrays under
# results/real/*.jsonl.byproduct/, which are gitignored: runs only on a box holding the raws.
# Pinned 2026-10-16 before the lane-B rerun, asserted below: the OQ-20 seed-6 arms 6 / 7 replay
# 17,157 / 17,602 consulted decisions to their logged values and a counterfactual TRAIN-support
# clip changes 42 / 47 of them. This is replay_c1.py over the seed-6 stems (oq15c_seed6_arm6 and
# oq15c_seed6_arm7, committed with the F-27 STAGE REPLAY line); the output records the numpy version.
# Replays the live Stage-C head decisions
# from the gitignored verdict byproducts, verifies the replay matches the logged
# stop_pos/extend, then measures |z| extremes, raw-a_hat-outside-[0,1] on the
# decision path, and a counterfactual TRAIN-support clip (DR-1 style).
import sys, json
from pathlib import Path
import numpy as np

REPLAY_PINS = {'oq15c_seed6_arm6': (17157, 42), 'oq15c_seed6_arm7': (17602, 47)}

REPO = Path(__file__).resolve().parents[3]  # docs/audits/<folder>/ -> the repository root
sys.path.insert(0, str(REPO / "src"))
from sideband.outcome_head import (HeadScorer, block_core_features, stage1_split,
                                   prompt_index_map, offset_rows, qsig_cols)

ROOT = REPO / "results" / "real"
NPZ = ROOT / "oq15_head_weights.npz"
GATE = ("k3_verdict_arm1", "k3_verdict_s1_arm1")
EXTRA = ("k3_val_arm1", "k3_tapcal_arm1")
OFF5 = ("k3_verdict_arm5", "k3_verdict_s1_arm5")


def run_files(stem):
    files = sorted((ROOT / f"{stem}.jsonl.byproduct").glob("p*.npz"))
    if not (ROOT / f"{stem}.jsonl.byproduct").is_dir():
        raise SystemExit(f"missing {stem}.jsonl.byproduct/: the per-prompt raws are gitignored (docs/DATA.md); "
                         "this replay runs only on a box that holds them")
    idx = prompt_index_map(ROOT / f"{stem}.gen.jsonl")
    return [(idx[int(f.stem[1:])], f) for f in files]


def support(fam):
    """TRAIN [min,max] + moments per offset, reproducing pipeline's TRAIN rows."""
    split = stage1_split(210)
    tr = set(int(i) for i in split["train"])
    lo = {}; hi = {}; s1 = {}; s2 = {}; n = {}
    def upd(off, x):
        if off not in lo:
            lo[off] = x.min(0); hi[off] = x.max(0)
            s1[off] = x.sum(0); s2[off] = (x * x).sum(0); n[off] = len(x)
        else:
            lo[off] = np.minimum(lo[off], x.min(0)); hi[off] = np.maximum(hi[off], x.max(0))
            s1[off] += x.sum(0); s2[off] += (x * x).sum(0); n[off] += len(x)
    rows = []
    for st in GATE:
        rows += [f for pid, f in run_files(st) if pid in tr]
    for st in EXTRA:
        rows += [f for pid, f in run_files(st)]
    for f in rows:
        z = dict(np.load(f))
        core = block_core_features(z, fam)
        for off in (1, 2, 3, 4):
            m = offset_rows(z, off)
            x = np.hstack([core, qsig_cols(z, off)])[m]
            if len(x):
                upd(off, x)
    split5 = stage1_split(len(run_files(OFF5[0])))
    tr5 = set(int(i) for i in split5["train"])
    for st in OFF5:
        for pid, f in run_files(st):
            if pid not in tr5:
                continue
            z = dict(np.load(f))
            core = block_core_features(z, fam)
            m = offset_rows(z, 5)
            x = np.hstack([core, qsig_cols(z, 5)])[m]
            if len(x):
                upd(5, x)
    return lo, hi, s1, s2, n


def ahat(params, off, x, clip_lohi=None):
    mu, sd, w = params[off]
    if clip_lohi is not None:
        x = np.clip(x, clip_lohi[0][off], clip_lohi[1][off])
    zz = (x - mu) / sd
    raw = float((np.concatenate([[1.0], zz]) @ w))  # scalar; tiny order diffs ok
    # exact op as HeadScorer for the decision:
    a = float(np.clip(np.hstack([np.ones((1, 1)), zz[None, :]]) @ w, 0.0, 1.0)[0])
    return a, raw, float(np.abs(zz).max())


def replay(params, thr, core, q, clip_lohi=None):
    """Returns (stop_pos, extend, path_info list of (off, raw, maxz))."""
    path = []
    a_list = []
    def get(off):
        k = min(off, 2)
        x = np.concatenate([core, q[:k].astype(np.float64)])
        a, raw, mz = ahat(params, off, x, clip_lohi)
        path.append((off, raw, mz))
        a_list.append(a)
        return a
    a1 = get(1)
    if a1 < thr["stop"][0]:
        return 1, 0, path
    if np.isnan(q[1]):
        return None, None, path  # inconsistent with logged trajectory
    a2 = get(2)
    if a1 * a2 < thr["stop"][1]:
        return 2, 0, path
    s = a1 * a2
    for off in (3, 4, 5):
        s *= get(off)
    return 0, int(s >= thr["extend"]), path


def main():
    out = {}
    for tag, stem_fmt in (("s6", "oq15c_seed6_arm{}"),):
        for arm, fam in ((6, "free"), (7, "tel")):
            stem = stem_fmt.format(arm)
            if not (ROOT / f"{stem}.jsonl.byproduct").is_dir():
                raise SystemExit(f"missing {stem}.jsonl.byproduct/: the per-prompt raws are gitignored (docs/DATA.md); "
                                 "this replay runs only on a box that holds them")
            meta = json.loads((ROOT / f"{stem}.meta.json").read_text(encoding="utf-8"))
            thr = meta["thresholds"]
            sc = HeadScorer(NPZ, fam)
            if fam not in SUP:
                SUP[fam] = support(fam)
                lo, hi, s1, s2, n = SUP[fam]
                for off in (1, 2, 3, 4, 5):
                    mu_r = s1[off] / n[off]
                    print(f"  [{fam} off{off}] mu reconstruct max|diff| "
                          f"{np.abs(mu_r - sc.params[off][0]).max():.3e} n_train={n[off]}")
            lo, hi, *_ = SUP[fam]
            c = dict(blocks=0, row0=0, consult=0, match=0, mismatch=0,
                     z100_off1=0, z100_path=0, z1000_path=0, maxz=0.0,
                     raw_out_path=0, raw_out_and_z100=0,
                     cf_changed=0, cf_changed_z100=0, cf_changed_rawout=0,
                     finder_z100=0, finder_raw_out=0, finder_n=0,
                     cf_dir={}, oos_blocks=0)
            for f in sorted((ROOT / f"{stem}.jsonl.byproduct").glob("p*.npz")):
                z = dict(np.load(f))
                nb = int(z["n_blocks"])
                if nb == 0:
                    continue
                core = block_core_features(z, fam)
                q = np.asarray(z["q_sig"], np.float32)
                sp = np.asarray(z["stop_pos"]).astype(int)
                ex = np.asarray(z["extend"]).astype(int)
                # finder's measure (all rows with finite offset-1 x)
                mu1, sdv, w1 = sc.params[1]
                x1 = np.hstack([core, q[:, :1].astype(np.float64)])
                ok = ~np.isnan(x1).any(1)
                zz1 = (x1[ok] - mu1) / sdv
                big = np.abs(zz1).max(1) > 100
                raw1 = np.hstack([np.ones((ok.sum(), 1)), zz1]) @ w1
                c["finder_n"] += int(ok.sum())
                c["finder_z100"] += int(big.sum())
                c["finder_raw_out"] += int(((raw1[big] <= 0) | (raw1[big] >= 1)).sum())
                for b in range(nb):
                    c["blocks"] += 1
                    if b == 0:
                        c["row0"] += 1
                        if sp[b] != 0 or ex[b] != 0:
                            print("ROW0 DECISION?!", f, b)
                        continue
                    c["consult"] += 1
                    s_live, e_live, path = replay(sc.params, thr, core[b], q[b])
                    if (s_live, e_live) == (sp[b], ex[b]):
                        c["match"] += 1
                    else:
                        c["mismatch"] += 1
                    mz = max(p[2] for p in path)
                    c["maxz"] = max(c["maxz"], mz)
                    if path[0][2] > 100:
                        c["z100_off1"] += 1
                    zbig = mz > 100
                    c["z100_path"] += int(zbig)
                    c["z1000_path"] += int(mz > 1000)
                    rawout = any(p[1] < 0 or p[1] > 1 for p in path)
                    c["raw_out_path"] += int(rawout)
                    c["raw_out_and_z100"] += int(rawout and zbig)
                    # out-of-support on any path head?
                    oos = False
                    for off, _, _ in path:
                        k = min(off, 2)
                        x = np.concatenate([core[b], q[b][:k].astype(np.float64)])
                        if (x < lo[off]).any() or (x > hi[off]).any():
                            oos = True
                    c["oos_blocks"] += int(oos)
                    s_cf, e_cf, _ = replay(sc.params, thr, core[b], q[b], (lo, hi))
                    if s_cf is None:
                        # counterfactual continues past a logged stop at j=1:
                        # q_sig[1] never drafted; count as changed (no-stop vs stop)
                        changed = True
                    else:
                        changed = (s_cf, e_cf) != (sp[b], ex[b])
                    if changed:
                        c["cf_changed"] += 1
                        c["cf_changed_z100"] += int(zbig)
                        c["cf_changed_rawout"] += int(rawout)
                        key = f"{(int(sp[b]), int(ex[b]))}->{(s_cf, e_cf)}"
                        c["cf_dir"][key] = c["cf_dir"].get(key, 0) + 1
            print(stem, fam, json.dumps(c))
            out[stem] = c
    failed = [(stem, c['consult'], c['match'], c['cf_changed']) for stem, c in out.items()
              if c['match'] != c['consult'] or (c['consult'], c['cf_changed']) != REPLAY_PINS[stem]]
    if failed:
        print('PIN MISMATCH (stem, consult, match, cf_changed):', failed, '| numpy', np.__version__)
        raise SystemExit(1)
    out = {'numpy': np.__version__, 'arms': out}
    Path(__file__).with_name("replay_c1_seed6.json").write_bytes((json.dumps(out, indent=1) + "\n").encode("utf-8"))
    print('all pins hold; wrote', Path(__file__).with_name("replay_c1_seed6.json").name)


SUP = {}
if __name__ == "__main__":
    main()
