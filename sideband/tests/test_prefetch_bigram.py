"""tests/test_prefetch_bigram.py (OQ-9 stage-1 FREE-BIGRAM TWIN, the post-hoc
diagnostic of F-26's ADDRESS-BEYOND-TOKEN reading): the CI-safe layer — the
tool refuses a modified frozen instrument; its TABLE_CUR, pair tables and
marginal equal the frozen Stage1.fit's to the integer; a routing rule driven
by the PREVIOUS token is recovered by the target-aligned prev table (and the
val selection picks that encoding) while the current-token arm stays at
chance; the current-token rule loses nothing to the extra block; the
address-only shift rule reads SURVIVES; independent random routing leaves
every arm at chance (no leak through either table); the prev table is read
leave-one-prompt-out at train rows; every arm shares the bigram positions
(t >= 1) and pairing violations are refused; labels are mechanical for all
six outcomes; smoke / grid / committed-cell / overwrite guards; --conclude-
from reproduces a smoke payload and refuses a tampered row; the encoding
selection is recorded in payload and state header; arm dims; no torch.

Fixtures are IMPORTED from tests/test_prefetch_readouts.py (the frozen
instrument's tests), not copied; the one new rule (routing driven by the
token two back) patches the slots of a fixture harvest in place."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests"))
import run_prefetch_readouts as pr  # noqa: E402  (the frozen instrument)
import run_prefetch_bigram as bg  # noqa: E402
import test_prefetch_readouts as tpr  # noqa: E402  (its fixtures)
from sideband.probes import load_label_space  # noqa: E402

E, L, K = pr.N_EXPERTS, pr.N_GATES, pr.TOP_K
ONE = "100"
FAST = "1,100"


def _args(d, b, g, out, **kw):
    base = dict(harvest=str(d), out=str(out), buckets=str(b), glue=str(g), committed="none",
                only_seeds=None, smoke_split_val=False, lambdas=ONE, conclude_from=None)
    base.update(kw)
    return argparse.Namespace(**base)


def _point(c, arm, B):
    return c["tables"][f"{arm}|B={B}"]["all"]["point"]


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _prev2_harvest(tmp_path, R=24, T=16, vocab=12, seed=3):
    """A fixture harvest whose slots are re-ruled: S[t, l] = {(7 * tokens[t-2] +
    3 l + 9 i) mod 64}, so the TARGET S[t+1] is a function of the PREVIOUS token
    tokens[t-1] and of nothing the current token or the current routing hold."""
    d, b, g = tpr.make_fake_harvest(tmp_path, rule="random", R=R, T=T, vocab=vocab, seed=seed)
    for npz in sorted(d.glob("*.npz")):
        z = dict(np.load(npz))
        tokens, lengths = z["tokens"], z["lengths"]
        slots = np.full((R, T, L, K), -1, dtype=np.int16)
        for r in range(R):
            for t in range(int(lengths[r])):
                tin = int(tokens[r, t - 2]) if t >= 2 else 0
                for l in range(L):
                    slots[r, t, l] = np.sort((7 * tin + 3 * l + 9 * np.arange(K)) % E)
        z["slots"] = slots
        np.savez(npz, **z)
        mp = d / npz.name.replace(".npz", ".meta.json")
        meta = json.loads(mp.read_text())
        meta["npz_sha256"] = _sha(npz)
        mp.write_text(json.dumps(meta))
    return d, b, g


# ---------------------------------------------------------------------------
# the frozen instrument is asserted, and its tables are reproduced exactly
# ---------------------------------------------------------------------------

def test_frozen_instrument_sha_is_asserted(tmp_path):
    assert bg.assert_frozen_instrument() == bg.FROZEN_INSTRUMENT_SHA256
    tampered = tmp_path / "run_prefetch_readouts.py"
    tampered.write_bytes(Path(pr.__file__).read_bytes() + b"\n# touched\n")
    with pytest.raises(SystemExit, match="refusing"):
        bg.assert_frozen_instrument(tampered)
    # a CRLF copy of the frozen bytes still passes (the sha is LF-normalised)
    crlf = tmp_path / "crlf.py"
    crlf.write_bytes(Path(pr.__file__).read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
    assert bg.assert_frozen_instrument(crlf) == bg.FROZEN_INSTRUMENT_SHA256


def test_tables_equal_the_frozen_instruments(tmp_path):
    d, b, g = tpr.make_fake_harvest(tmp_path, rule="token", R=21, T=14)
    data = pr.S3Data(d)
    lab, nc = load_label_space(b, g)
    st = pr.Stage1(data, lab, nc, horizons=(1,), leads=(1,), lambdas=(1.0,))
    st.fit()
    bb = bg.Bigram(data, lab, nc, lambdas=(1.0,))
    bb.fit_tables()
    assert np.array_equal(bb.token_table, st.token_table)
    assert np.array_equal(bb.pair_keys, st.pair_keys) and np.array_equal(bb.pair_counts, st.pair_counts)
    assert np.array_equal(bb.marginal_freq, st.marginal_freq)
    assert bb.n_positions["horizon1/train"] == st.n_positions["horizon1/train"]
    # the frozen table read (TABLE_CUR at tokens[t]) is the frozen instrument's, byte for byte
    rows, anchors = pr.restrict(*bg.bigram_positions(data.lengths, data.T), bb.masks["train"])
    tok, prompt = data.tokens[rows, anchors], data.prompt_idx[rows]
    assert np.array_equal(bb.table_vec(tok, prompt), st.table_vec(tok, prompt))
    assert np.array_equal(bb.table_vec(tok), st.table_vec(tok))
    # the prev table counts the bigram positions only, and sums to its pair table
    assert bb.prev_table.sum() == bb.n_positions["bigram/train"] * L * K
    assert bb.prev_table.sum() < bb.token_table.sum()


# ---------------------------------------------------------------------------
# rules the arms must recover (and must not)
# ---------------------------------------------------------------------------

def test_prev_token_rule_is_recovered_by_the_prev_table_and_selected(tmp_path):
    d, b, g = _prev2_harvest(tmp_path)
    out = tmp_path / "prev2.json"
    payload = bg.run(_args(d, b, g, out, lambdas=FAST))
    c, prov, lab = payload["conclusion"], payload["provenance"], payload["conclusion"]["labels"]
    assert _point(c, "free_bigram_b", 8) > 0.95                    # TABLE_PREV(tokens[t-1]) IS the target
    assert _point(c, "free_tok", 8) < 0.35                          # tokens[t] says nothing about S[t+1]
    assert _point(c, "history", 8) < 0.35                           # S[t] = f(tokens[t-2]) says nothing either
    # encoding (a), TABLE_CUR read at tokens[t-1], is NOT at chance here: with 12 tokens the frozen table's
    # per-key vectors are distinct, so a linear reader decodes the previous token's identity from them
    # (a free fingerprint, the same channel free_tok has). The val selection still prefers the
    # target-aligned table, ties to it.
    vb, va = prov["val_table"]["free_bigram_b"], prov["val_table"]["free_bigram_a"]
    assert max(vb.values()) >= max(va.values())
    assert prov["encoding_selected"] == "prev_table" and lab["encoding"] == "prev_table"
    assert lab["free_bigram_arm"] == "free_bigram_b" and lab["history_bigram_arm"] == "history_bigram_b"
    assert lab["gate_eq_reading"] == "NEGATIVE"                     # the free bigram block beats the address block
    assert lab["bigram_gain_reading"] == "SIGNAL"
    assert lab["label"] == "FREE-HISTORY" and lab["sentence"].startswith("no material margin")
    assert "no material margin of the address stream over the free bigram is shown" in lab["sentence"]
    assert lab["remeasure_ok"] is None                              # committed 'none': not applicable
    header, rows = pr.load_state(Path(str(out) + ".state.jsonl"))
    assert header["encoding"] == "prev_table" and header["committed_cell"] is None


def test_current_token_rule_loses_nothing_to_the_bigram_block(tmp_path):
    d, b, g = tpr.make_fake_harvest(tmp_path, rule="token", R=24, T=16, vocab=12, seed=5)
    c = bg.run(_args(d, b, g, tmp_path / "token.json", lambdas=FAST))["conclusion"]
    lab = c["labels"]
    free = lab["free_bigram_arm"]
    assert _point(c, "free_tok", 16) > 0.95 and _point(c, "history_tok", 16) > 0.95
    assert _point(c, free, 16) >= _point(c, "free_tok", 16) - 0.02
    assert lab["gate_eq_reading"] != "SIGNAL" and lab["address_beyond_bigram_reading"] != "SIGNAL"
    assert lab["label"] == "FREE-HISTORY"


def test_shift_rule_reads_survives(tmp_path):
    d, b, g = tpr.make_fake_harvest(tmp_path, rule="shift", R=24, T=16, seed=7)
    c = bg.run(_args(d, b, g, tmp_path / "shift.json", lambdas=FAST))["conclusion"]
    lab = c["labels"]
    assert _point(c, "history", 16) > 0.95
    assert _point(c, "free_tok", 16) < 0.5 and _point(c, lab["free_bigram_arm"], 16) < 0.5
    assert lab["gate_eq_reading"] == "SIGNAL" and lab["address_beyond_bigram_reading"] == "SIGNAL"
    assert lab["label"] == "SURVIVES" and "adds a material margin over an equal-dims free bigram block" in lab["sentence"]
    assert "(B = 16, j = 1)" in lab["sentence"]


def test_independent_random_routing_leaves_every_arm_at_chance(tmp_path):
    d, b, g = tpr.make_fake_harvest(tmp_path, rule="random", R=28, T=16, seed=11)
    c = bg.run(_args(d, b, g, tmp_path / "random.json"))["conclusion"]
    chance = K / E
    for arm in bg.ARMS_REQUIRED:
        p = _point(c, arm, 8)
        assert abs(p - chance) < 0.06, (arm, p)
    assert c["labels"]["label"] == "FREE-HISTORY"


# ---------------------------------------------------------------------------
# leave-one-prompt-out on the prev table; positions; pairing
# ---------------------------------------------------------------------------

def test_prev_table_is_read_leave_one_prompt_out_at_train_rows(tmp_path):
    d, b, g = tpr.make_fake_harvest(tmp_path, rule="random", R=21, T=14, seed=2)
    data = pr.S3Data(d)
    lab, nc = load_label_space(b, g)
    bb = bg.Bigram(data, lab, nc, lambdas=(1.0,))
    bb.fit_tables()
    rows, anchors = pr.restrict(*bg.bigram_positions(data.lengths, data.T), bb.masks["train"])
    r, a = int(rows[5]), int(anchors[5])
    pid, tokp = int(data.prompt_idx[r]), int(data.tokens[r, a - 1])
    # the table built from every bigram train position of every OTHER prompt
    keep = data.prompt_idx[rows] != pid
    rr, aa = rows[keep], anchors[keep]
    sel = data.tokens[rr, aa - 1] == tokp
    cnt = np.zeros((L, E))
    for row, anc in zip(rr[sel], aa[sel]):
        for l in range(L):
            cnt[l, data.slots[row, anc + 1, l]] += 1
    tot = cnt.sum(axis=1, keepdims=True)
    want = np.where(tot > 0, cnt / np.maximum(tot, 1.0), bb.marginal_freq).reshape(1, L * E)
    got = bb.prev_table_vec(np.array([tokp]), np.array([pid]))
    assert np.allclose(got, want)
    # without the prompt argument the full table is read
    full = bb.prev_table[tokp].astype(np.float64)
    ft = full.sum(axis=1, keepdims=True)
    assert np.allclose(bb.prev_table_vec(np.array([tokp])),
                       np.where(ft > 0, full / np.maximum(ft, 1.0), bb.marginal_freq).reshape(1, L * E))
    # a prompt that never contributed under this key is refused (an internal check, not a silent read)
    with pytest.raises(SystemExit, match="missing from the prev pair table"):
        bb.prev_table_vec(np.array([tokp]), np.array([10 ** 6]))


def test_bigram_positions_are_shared_and_pairing_is_refused(tmp_path):
    lengths = np.array([1, 2, 3, 6])
    rows, anchors = bg.bigram_positions(lengths, 6)
    assert anchors.min() == 1
    assert sorted(zip(rows.tolist(), anchors.tolist())) == [(2, 1), (3, 1), (3, 2), (3, 3), (3, 4)]
    d, b, g = tpr.make_fake_harvest(tmp_path, rule="random", R=21, T=14, seed=4)
    out = tmp_path / "pos.json"
    payload = bg.run(_args(d, b, g, out))
    _, state_rows = pr.load_state(Path(str(out) + ".state.jsonl"))
    needed = {}
    for r in state_rows:
        needed.setdefault((r["budget"], r["gate"], r["prompt_idx"]), set()).add(r["needed"])
    assert all(len(v) == 1 for v in needed.values())
    assert {r["key"] for r in state_rows} == {1} and {r["depth"] for r in state_rows} == {None}
    assert payload["provenance"]["n_positions"]["bigram/train"] < payload["provenance"]["n_positions"]["horizon1/train"]
    bad = [{"arm": "history_tok", "budget": 16, "key": 1, "depth": None, "gate": 0, "prompt_idx": 0, "hits": 1, "needed": 8},
           {"arm": "history_tok", "budget": 16, "key": 1, "depth": None, "gate": 0, "prompt_idx": 1, "hits": 1, "needed": 8},
           {"arm": "free_tok", "budget": 16, "key": 1, "depth": None, "gate": 0, "prompt_idx": 0, "hits": 1, "needed": 8},
           {"arm": "free_tok", "budget": 16, "key": 1, "depth": None, "gate": 0, "prompt_idx": 1, "hits": 1, "needed": 16}]
    with pytest.raises(SystemExit, match="pairing violated"):
        bg.conclude(bad, "prev_table", None, n_boot=50, budgets=(16,))


# ---------------------------------------------------------------------------
# labels are mechanical
# ---------------------------------------------------------------------------

def _rows(rates: dict, per: int = 100, prompts=(0, 1)):
    rows = []
    for arm, rate in rates.items():
        for p in prompts:
            for g in range(L):
                rows.append({"arm": arm, "budget": 16, "key": 1, "depth": None, "gate": g, "prompt_idx": p,
                             "hits": int(round(per * rate)), "needed": per})
    return rows


BASE = {"history": 0.80, "free_tok": 0.81, "history_tok": 0.91, "free_bigram_b": 0.85, "free_bigram_a": 0.83,
        "history_bigram_b": 0.92, "history_bigram_a": 0.915, "free_all": 0.86, "history_all": 0.925}


def test_labels_are_mechanical():
    kw = dict(n_boot=200, budgets=(16,))
    # SURVIVES: D_eq = 0.91 - 0.85 = +0.06, D_add = 0.92 - 0.85 = +0.07, both at the floor or above
    lab = bg.conclude(_rows(BASE), "prev_table", 0.10, **kw)["labels"]
    assert lab["label"] == "SURVIVES" and lab["remeasure_ok"] is True
    assert abs(lab["address_beyond_token_re"]["delta"] - 0.10) < 1e-9 and abs(lab["remeasure_gap"]) < 1e-9
    assert lab["free_bigram_arm"] == "free_bigram_b" and lab["gate_eq_reading"] == "SIGNAL"
    assert abs(lab["gate_eq"]["delta"] - 0.06) < 1e-9 and abs(lab["address_beyond_bigram"]["delta"] - 0.07) < 1e-9
    # the other encoding flips the arms the deltas read
    lab = bg.conclude(_rows(BASE), "cur_table_at_prev", 0.10, **kw)["labels"]
    assert lab["free_bigram_arm"] == "free_bigram_a" and abs(lab["gate_eq"]["delta"] - 0.08) < 1e-9
    # COMPLEMENTARY: the free bigram block ties the address block, the union still adds
    r = dict(BASE, free_bigram_b=0.90, history_bigram_b=0.96)
    lab = bg.conclude(_rows(r), "prev_table", 0.10, **kw)["labels"]
    assert lab["gate_eq_reading"] == "NOT-SHOWN" and lab["address_beyond_bigram_reading"] == "SIGNAL"
    assert lab["label"] == "COMPLEMENTARY"
    # FREE-HISTORY: neither fires (D_eq +0.02 CI-positive below the floor is NOT-SHOWN by the rule)
    r = dict(BASE, free_bigram_b=0.89, history_bigram_b=0.92)
    lab = bg.conclude(_rows(r), "prev_table", 0.10, **kw)["labels"]
    assert lab["gate_eq_reading"] == "NOT-SHOWN" and lab["address_beyond_bigram_reading"] == "NOT-SHOWN"
    assert lab["label"] == "FREE-HISTORY"
    # the pinned sentence never says "no better" or "reproduced": these deltas are CI-positive below the floor
    assert lab["sentence"].startswith("no material margin (at or above +0.05)")
    assert "no better" not in lab["sentence"] and "reproduced" not in lab["sentence"]
    assert lab["gate_eq"]["lo"] > 0 and lab["address_beyond_bigram"]["lo"] > 0
    # ... and with the free block CI-clear ABOVE the address block
    r = dict(BASE, free_bigram_b=0.95, history_bigram_b=0.96)
    lab = bg.conclude(_rows(r), "prev_table", 0.10, **kw)["labels"]
    assert lab["gate_eq_reading"] == "NEGATIVE" and lab["label"] == "FREE-HISTORY"
    # READER-INCONSISTENT: the equal-dims comparison fires, the union does not
    r = dict(BASE, free_bigram_b=0.85, history_bigram_b=0.87)
    lab = bg.conclude(_rows(r), "prev_table", 0.10, **kw)["labels"]
    assert lab["gate_eq_reading"] == "SIGNAL" and lab["address_beyond_bigram_reading"] == "NOT-SHOWN"
    assert lab["label"] == "READER-INCONSISTENT"
    # REMEASURE-INVALID: the re-measured cell is far from the committed one; readings still reported
    lab = bg.conclude(_rows(BASE), "prev_table", 0.15, **kw)["labels"]
    assert lab["remeasure_ok"] is False and lab["label"] == "REMEASURE-INVALID"
    assert lab["gate_eq_reading"] == "SIGNAL"
    assert abs(lab["remeasure_gap"] + 0.05) < 1e-9
    # inside the tolerance passes
    assert bg.conclude(_rows(BASE), "prev_table", 0.10 + 0.0095, **kw)["labels"]["remeasure_ok"] is True
    # no committed cell (smoke / test): not applicable, never INVALID
    lab = bg.conclude(_rows(BASE), "prev_table", None, **kw)["labels"]
    assert lab["remeasure_ok"] is None and lab["label"] == "SURVIVES"
    # a missing registered arm is INCOMPLETE
    rows = [x for x in _rows(BASE) if x["arm"] != "free_all"]
    lab = bg.conclude(rows, "prev_table", 0.10, **kw)["labels"]
    assert lab["label"] == "INCOMPLETE" and lab["missing_arms"] == ["free_all"]
    with pytest.raises(SystemExit, match="unknown encoding"):
        bg.conclude(_rows(BASE), "trigram", 0.10, **kw)


def test_per_gate_gain_names_the_largest_gate():
    rates = dict(BASE)
    rows = _rows(rates)
    # raise the free bigram arm at gate 3 only
    for r in rows:
        if r["arm"] == "free_bigram_b" and r["gate"] == 3:
            r["hits"] = 99
    lab = bg.conclude(rows, "prev_table", 0.10, n_boot=100, budgets=(16,))["labels"]
    assert lab["largest_gain_gate"] == 3 and lab["driven_by_gate0"] is False
    assert abs(lab["per_gate_bigram_gain"]["3"] - (0.99 - 0.81)) < 1e-9
    assert abs(lab["per_gate_bigram_gain"]["0"] - (0.85 - 0.81)) < 1e-9
    # gate 0's share of the summed per-gate gain, and the cap on what gate 0 alone can add to the pooled gain
    total = 15 * (0.85 - 0.81) + (0.99 - 0.81)
    assert abs(lab["gate0_gain_share"] - (0.85 - 0.81) / total) < 1e-9
    assert abs(lab["gate0_gain_cap"] - (1.0 - 0.81) / L) < 1e-9
    # no gain anywhere: the share is undefined, not a division error
    flat = bg.conclude(_rows(dict(BASE, free_bigram_b=0.81)), "prev_table", 0.10, n_boot=100, budgets=(16,))["labels"]
    assert flat["gate0_gain_share"] is None


def test_pairing_is_checked_for_every_arm_including_the_unselected_ones():
    rows = [r for r in _rows(BASE) if not (r["arm"] == "history_bigram_a" and r["prompt_idx"] == 1)]
    with pytest.raises(SystemExit, match="pairing violated: history_bigram_a"):
        bg.conclude(rows, "prev_table", 0.10, n_boot=50, budgets=(16,))


def test_out_path_and_overwrite_guards_under_results(tmp_path, monkeypatch):
    d, b, g = tpr.make_fake_harvest(tmp_path, rule="random", R=21, seed=12)
    monkeypatch.setattr(bg.pr, "_under_results", lambda p: True)        # results/ membership stubbed; nothing written there
    # the fixture directory is named harvest_moe, so only results/real/prefetch_bigram_s3.json is admissible
    with pytest.raises(SystemExit, match="must be results/real/prefetch_bigram_s3.json"):
        bg.run(_args(d, b, g, tmp_path / "wrong_name.json", lambdas=None))
    # an existing state file or meta file refuses the run, not only an existing payload
    out = tmp_path / "prefetch_bigram_s3.json"
    state = Path(str(out) + ".state.jsonl"); state.write_text("x")
    with pytest.raises(SystemExit, match="state.jsonl exists: a registered payload is never overwritten"):
        bg.run(_args(d, b, g, out, lambdas=None))
    state.unlink()
    meta = tmp_path / "prefetch_bigram_s3.meta.json"; meta.write_text("x")
    with pytest.raises(SystemExit, match="meta.json exists: a registered payload is never overwritten"):
        bg.run(_args(d, b, g, out, lambdas=None))
    assert bg.OUT_OF_HARVEST == {"harvest_moe": "prefetch_bigram_s3.json", "harvest_moe_r": "prefetch_bigram_s3_r.json"}


def test_explicit_committed_path_must_exist_and_a_relative_one_resolves(tmp_path, monkeypatch):
    with pytest.raises(SystemExit, match="not found"):
        bg.committed_cell(tmp_path / "harvest_moe", str(tmp_path / "nope.json"), smoke=False, out_under_results=False)
    fake = tmp_path / "prefetch_fake.json"
    fake.write_text(json.dumps({"registered": pr.REGISTERED,
                                "provenance": {"git_commit": "abc", "instrument_sha256": "0" * 64},
                                "conclusion": {"deltas": {bg.COMMITTED_KEY: {"delta": 0.1, "lo": 0.09, "hi": 0.11}}}}))
    monkeypatch.chdir(tmp_path)
    cell = bg.committed_cell(tmp_path / "harvest_moe", "prefetch_fake.json", smoke=False, out_under_results=False)
    assert cell["delta"] == 0.1 and cell["path"].endswith("prefetch_fake.json") and "\\" not in cell["path"]


def test_conclude_from_rederives_the_encoding_and_rereads_the_committed_cell(tmp_path):
    d, b, g = _prev2_harvest(tmp_path, seed=6)
    fake = tmp_path / "prefetch_fake.json"
    fake.write_text(json.dumps({"registered": pr.REGISTERED,
                                "provenance": {"git_commit": "abc", "instrument_sha256": "0" * 64},
                                "conclusion": {"deltas": {bg.COMMITTED_KEY: {"delta": 0.1, "lo": 0.09, "hi": 0.11}}}}))
    out = tmp_path / "rederive.json"
    payload = bg.run(_args(d, b, g, out, lambdas=FAST, committed=str(fake)))
    assert payload["provenance"]["committed_cell"]["sha256"] == _sha(fake)
    bg.conclude_from(out)                                           # clean
    state = Path(str(out) + ".state.jsonl")
    # (1) a CONSISTENT flip of the encoding in header and provenance is refused: the val table re-selects it
    enc = payload["provenance"]["encoding_selected"]; other = bg.other_encoding(enc)
    lines = state.read_text(encoding="utf-8").splitlines()
    header = json.loads(lines[0]); header["encoding"] = other; lines[0] = json.dumps(header)
    state.write_text("\n".join(lines) + "\n", encoding="utf-8")
    p2 = json.loads(out.read_text(encoding="utf-8")); p2["provenance"]["encoding_selected"] = other
    out.write_text(json.dumps(p2), encoding="utf-8")
    with pytest.raises(SystemExit, match="not the one the payload's val table selects"):
        bg.conclude_from(out)
    # restore
    header["encoding"] = enc; lines[0] = json.dumps(header); state.write_text("\n".join(lines) + "\n", encoding="utf-8")
    out.write_text(json.dumps(payload), encoding="utf-8")
    # (2) the committed payload on disk is re-read: a changed delta (new bytes) is refused ...
    fake.write_text(json.dumps({"registered": pr.REGISTERED,
                                "provenance": {"git_commit": "abc", "instrument_sha256": "0" * 64},
                                "conclusion": {"deltas": {bg.COMMITTED_KEY: {"delta": 0.2, "lo": 0.19, "hi": 0.21}}}}))
    with pytest.raises(SystemExit, match="is not the one this run read"):
        bg.conclude_from(out)
    # ... and an absent committed payload falls back to the header's cell with a note, not a refusal
    fake.unlink()
    assert bg.conclude_from(out)["labels"]["label"] == payload["conclusion"]["labels"]["label"]


# ---------------------------------------------------------------------------
# guards, smoke, exact recompute, provenance
# ---------------------------------------------------------------------------

def test_guards_smoke_and_conclude_from(tmp_path, monkeypatch):
    d, b, g = tpr.make_fake_harvest(tmp_path, rule="random", R=42, seed=9)
    with pytest.raises(SystemExit, match="may not write under results/"):
        bg.run(_args(d, b, g, ROOT / "results" / "smoke" / "x.json", only_seeds="0"))
    with pytest.raises(SystemExit, match="lambda grid"):
        bg.run(_args(d, b, g, ROOT / "results" / "smoke" / "y.json", lambdas=FAST))
    # the committed-cell refusal: reached only at the registered out path for this (fixture-named) harvest,
    # so ROOT is pointed at a scratch tree where that path does not exist yet (the real one holds the landed
    # payload, whose overwrite refusal would fire first); the refusal raises before any data is loaded or written
    monkeypatch.setattr(bg, "ROOT", tmp_path / "scratch_root")
    monkeypatch.setattr(bg.pr, "_under_results", lambda p: True)
    with pytest.raises(SystemExit, match="committed none is refused"):
        bg.run(_args(d, b, g, tmp_path / "scratch_root" / "results" / "real" / "prefetch_bigram_s3.json", lambdas=None))
    monkeypatch.undo()
    # an existing registered payload is never overwritten (results/ membership stubbed, nothing written there)
    existing = tmp_path / "existing.json"
    existing.write_text("{}")
    monkeypatch.setattr(bg.pr, "_under_results", lambda p: True)
    with pytest.raises(SystemExit, match="never overwritten"):
        bg.run(_args(d, b, g, existing, lambdas=None))
    monkeypatch.undo()
    # the smoke path: one shard, val prompts re-split; the committed cell is not applicable
    out = tmp_path / "smoke.json"
    payload = bg.run(_args(d, b, g, out, only_seeds="1", smoke_split_val=True, committed=None))
    prov = payload["provenance"]
    assert prov["smoke"] is True and prov["seeds"] == [1] and prov["committed_cell"] is None
    assert prov["frozen_instrument"]["sha256_lf"] == bg.FROZEN_INSTRUMENT_SHA256
    assert prov["constants"]["arm_dims"]["history_tok"] == 2049
    assert payload["conclusion"]["labels"]["remeasure_ok"] is None
    # evidence files are LF on every platform
    for p in (out, Path(str(out) + ".state.jsonl"), tmp_path / "smoke.meta.json"):
        assert b"\r\n" not in p.read_bytes()
    # exact recompute from the state file ...
    got = bg.conclude_from(out)
    assert got["labels"]["label"] == payload["conclusion"]["labels"]["label"]
    # ... and a tampered row is refused
    state = Path(str(out) + ".state.jsonl")
    lines = state.read_text(encoding="utf-8").splitlines()
    row = json.loads(lines[1]); row["hits"] = max(0, row["hits"] - 1)
    lines[1] = json.dumps(row)
    state.write_text("\n".join(lines) + "\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="RECOMPUTE MISMATCH"):
        bg.conclude_from(out)


def test_committed_cell_is_read_from_a_stage1_payload(tmp_path):
    d, b, g = tpr.make_fake_harvest(tmp_path, rule="random", R=21, seed=1)
    # a fake committed stage-1 payload carrying the cell the precondition reads
    fake = tmp_path / "prefetch_fake.json"
    fake.write_text(json.dumps({"registered": pr.REGISTERED,
                                "provenance": {"git_commit": "abc", "instrument_sha256": "0" * 64},
                                "conclusion": {"deltas": {bg.COMMITTED_KEY: {"delta": 0.1032, "lo": 0.09, "hi": 0.11}}}}))
    cell = bg.committed_cell(d, str(fake), smoke=False, out_under_results=False)
    assert cell["delta"] == 0.1032 and cell["git_commit"] == "abc" and cell["key"] == bg.COMMITTED_KEY
    assert cell["sha256"] == _sha(fake)
    with pytest.raises(SystemExit, match="not an OQ-9 stage-1 payload"):
        other = tmp_path / "other.json"; other.write_text(json.dumps({"registered": "x"}))
        bg.committed_cell(d, str(other), smoke=False, out_under_results=False)
    # outside results/ an unknown harvest without --committed reads no cell; under results/ it is refused;
    # a smoke never reads one
    unknown = tmp_path / "harvest_other"
    assert bg.committed_cell(unknown, None, smoke=False, out_under_results=False) is None
    with pytest.raises(SystemExit, match="no committed stage-1 payload is known"):
        bg.committed_cell(unknown, None, smoke=False, out_under_results=True)
    assert bg.committed_cell(d, str(fake), smoke=True, out_under_results=False) is None
    # the registered mapping names the committed payloads
    assert bg.COMMITTED_OF_HARVEST == {"harvest_moe": "prefetch_s3.json", "harvest_moe_r": "prefetch_s3_r.json"}
    # a run that reads the fake cell applies the precondition (far from a random-routing re-measure)
    payload = bg.run(_args(d, b, g, tmp_path / "pre.json", committed=str(fake)))
    lab = payload["conclusion"]["labels"]
    assert payload["provenance"]["committed_cell"]["delta"] == 0.1032
    assert lab["remeasure_ok"] is False and lab["label"] == "REMEASURE-INVALID"


def test_encoding_selection_rule_ties_keep_the_prev_table():
    """select_encoding: the better val-best wins; an exact tie keeps (b) prev_table (the registered rule)."""
    lam = {"free_bigram_b": 10.0, "free_bigram_a": 10.0}
    assert bg.select_encoding({"free_bigram_b": {"10.0": 0.80}, "free_bigram_a": {"10.0": 0.80}}, lam) == "prev_table"
    assert bg.select_encoding({"free_bigram_b": {"10.0": 0.79}, "free_bigram_a": {"10.0": 0.80}}, lam) == "cur_table_at_prev"
    assert bg.select_encoding({"free_bigram_b": {"10.0": 0.81}, "free_bigram_a": {"10.0": 0.80}}, lam) == "prev_table"
    # each arm is read at ITS OWN selected lambda
    lam2 = {"free_bigram_b": 1.0, "free_bigram_a": 100.0}
    vt = {"free_bigram_b": {"1.0": 0.70, "100.0": 0.90}, "free_bigram_a": {"1.0": 0.95, "100.0": 0.75}}
    assert bg.select_encoding(vt, lam2) == "cur_table_at_prev"


def test_conclude_from_refuses_a_header_that_disagrees_with_the_payload(tmp_path):
    d, b, g = tpr.make_fake_harvest(tmp_path, rule="random", R=21, seed=13)
    out = tmp_path / "hdr.json"
    payload = bg.run(_args(d, b, g, out))
    state = Path(str(out) + ".state.jsonl")
    lines = state.read_text(encoding="utf-8").splitlines()
    header = json.loads(lines[0])
    # the header's encoding flipped ALONE (the payload still says the other): refused before any recompute
    h2 = dict(header, encoding=bg.other_encoding(payload["provenance"]["encoding_selected"]))
    state.write_text("\n".join([json.dumps(h2)] + lines[1:]) + "\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="encoding differs from the payload's"):
        bg.conclude_from(out)
    # a harvest sha changed in the header alone
    h3 = dict(header); h3["harvest_npz_sha256"] = {k: "0" * 64 for k in header["harvest_npz_sha256"]}
    state.write_text("\n".join([json.dumps(h3)] + lines[1:]) + "\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="harvest shas differ"):
        bg.conclude_from(out)
    # a row dropped: the count refusal
    state.write_text("\n".join([json.dumps(header)] + lines[1:-1]) + "\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="row count differs"):
        bg.conclude_from(out)


def test_arm_dims_and_blocks():
    assert bg.arm_dims("history_tok") == bg.arm_dims("free_bigram_b") == bg.arm_dims("free_bigram_a") == 2049
    assert bg.arm_dims("history_bigram_b") == bg.arm_dims("history_bigram_a") == bg.arm_dims("free_all") == 3073
    assert bg.arm_dims("history_all") == 4097 and bg.arm_dims("history") == bg.arm_dims("free_tok") == 1025
    assert bg.arm_cols("history_tok")[-1] == bg.D_X - 1
    assert np.array_equal(bg.arm_cols("free_bigram_a")[:-1], np.r_[np.arange(bg.D, 2 * bg.D), np.arange(3 * bg.D, 4 * bg.D)])
    assert bg.ENCODINGS[0] == "prev_table" and bg.free_arm_of("prev_table") == "free_bigram_b"
    assert bg.other_encoding("prev_table") == "cur_table_at_prev"


def test_tool_imports_no_torch():
    code = ("import sys; sys.path.insert(0, r'%s'); import run_prefetch_bigram; "
            "print('torch' in sys.modules)" % str(ROOT / "tools"))
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)
    assert out.stdout.strip() == "False"
