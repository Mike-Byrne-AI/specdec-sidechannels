"""experiments/errata_lib.py: the pinned rules of ERRATA_PROTOCOL.md on synthetic inputs."""

import sys
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "experiments"))
import errata_lib as L  # noqa: E402
from amber.real import archive as ARCHIVE  # noqa: E402
from amber.real.longhorizon import distinct_ngram_ratio, loop_fraction  # noqa: E402


def test_rounds_to_uses_printed_precision():
    assert L.rounds_to(32.84, "32.8", 1) and not L.rounds_to(32.85, "32.8", 1)
    assert L.rounds_to(990.6, "991", 0) and L.rounds_to(7.284, "7.28", 2)


def test_loop_flags_and_grid_on_periodic_rows():
    looped = np.array(list(range(100, 110)) + [7, 8, 9] * 90)  # 280 tokens, period-3 tail covering exactly 270
    clean = np.arange(300)
    r = L.loop_flags([looped, clean], loop_fraction, 128, 64, 0.5)
    assert r["flags"] == [True, False] and r["periods"][0] == 3 and r["n_looped"] == 1
    assert r["tokens_in_loop"][0] == 270 and r["tokens_in_loop"][1] == 0
    grid = L.loop_grid([looped, clean], loop_fraction)
    assert all(g["P"] < g["W"] for g in grid) and len(grid) == 13 * 3
    assert all(g["n_looped"] == 1 for g in grid), "a 270/280 period-3 tail is looped under every grid setting"


def test_repeat_4gram_share_and_distinct_stats():
    row = np.array([1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4])          # 9 4-gram positions, 4 distinct, 5 repeats
    num, den = L.repeat_4gram_share([row])
    assert (num, den) == (5, 9)
    d = L.distinct_ngram_stats([row, np.array([1, 2])], distinct_ngram_ratio, 4)
    assert d["rows"] == 1 and d["pooled_distinct"] == 4 and d["pooled_total"] == 9


def test_stratified_rates_recovers_pooled_identity():
    def amber_bits(ranks):                       # a stand-in: 1 bit per correction
        return int((np.asarray(ranks) != 1).sum())
    rows = [(np.array([1, 1, 2]), np.array([-0.5, -0.5, -2.0]), False), (np.array([3, 1]), np.array([-3.0, -0.25]), True)]
    s = L.stratified_rates(rows, amber_bits)
    assert s["all"]["N"] == 5 and s["nonlooped"]["N"] == 3 and s["looped"]["N"] == 2
    assert abs(s["nonlooped"]["amber_concat"] - 1 / 3) < 1e-12 and abs(s["nonlooped"]["ac"] - 1.0) < 1e-12
    assert abs(s["all"]["delta_concat"] - (2 / 5 - 1.25)) < 1e-12


def test_rate_stats_weighted_vs_unweighted():
    s = L.rate_stats([100, 1000], [10, 10])       # 10 tok/s and 100 tok/s
    assert s["weighted"] == 55.0 and s["unweighted"] == 55.0 and s["median"] == 55.0
    s = L.rate_stats([100, 1000], [10, 1])        # 10 and 1000 -> weighted 100, unweighted 505
    assert s["weighted"] == 100.0 and s["unweighted"] == 505.0


def test_stall_split_pinned_rule():
    lengths = [100] * 10; seconds = [0.1] * 8 + [2.0, 3.0]
    s = L.stall_split(lengths, seconds, 0.25)
    assert s["n_stalled"] == 2 and s["stalled_rows"] == [8, 9] and abs(s["seconds_stalled"] - 5.0) < 1e-12
    assert abs(s["clean"] - 1000.0) < 1e-9 and s["aggregate"] < s["clean"]


def test_depth_table_denominators():
    row = {"n": 1000, "desync_total": 13, "desyncs": {"A": 3, "C": 10, "T": 0, "X": 0}, "symbol_counts": {"A": 600, "C": 300, "T": 0, "X": 100},
           "C_desync_by_rank": {**{str(r): {"n": 10, "desync": 0} for r in range(2, 65)}, "2": {"n": 100, "desync": 6}, "20": {"n": 10, "desync": 4}}}
    t = L.depth_table(row)
    assert t["primary"]["1"] == 3 / 600 and t["alt"]["1"] == 3 / 1000
    assert t["primary"]["2"] == 0.06 and t["buckets"]["17-64"]["primary"] == 4 / (48 * 10)   # ranks 17..64 = 48 ranks
    assert t["overall"] == 0.013


def test_probe_control_reaches_work_on_every_path_and_distinguishes_refusal():
    for craft, dec in ((L.craft_hf_json, ARCHIVE.decode_archive), (L.craft_v3, ARCHIVE.decode_binary_archive),
                       (L.craft_v4, ARCHIVE.decode_session_archive)):
        assert L.probe(dec, craft(3), ARCHIVE)["outcome"] == "work_started"
    assert ARCHIVE.payload_to_symbols.__name__ == "payload_to_symbols", "probe must restore the patched function"

    def refusing(blob, make_stepper):
        raise ValueError("declared length over ceiling")
    assert L.probe(refusing, b"", ARCHIVE) == {"outcome": "refused", "message": "declared length over ceiling"}


def test_parse_arxiv_meta():
    html = ('<meta name="citation_title" content="Synchronizing Probabilities" />\n'
            '<meta name="citation_author" content="Adler, A" />\n<meta name="citation_author" content="Tang, B" />\n'
            '<meta name="citation_abstract" content="We propose PMATIC, an algorithm that &quot;tolerates&quot;\nmismatch." />')
    m = L.parse_arxiv_meta(html)
    assert m["title"] == "Synchronizing Probabilities" and m["authors"] == ["Adler, A", "Tang, B"]
    assert m["abstract"] == 'We propose PMATIC, an algorithm that "tolerates"\nmismatch.' and m["pmatic_count_in_page"] == 1
    assert L.parse_arxiv_meta("<html></html>") == {"title": None, "authors": [], "abstract": None, "pmatic_count_in_page": 0}


# ----------------------------------------------------------------------------
# second batch: E15 / E16 helpers
# ----------------------------------------------------------------------------

P2B_ROW = {"n": 100, "desync_total": 4, "desyncs": {"A": 1, "C": 3, "T": 0, "X": 0}, "symbol_counts": {"A": 10, "C": 15, "T": 0, "X": 4},
           "C_desync_by_rank": {"2": {"n": 10, "desync": 2}, "3": {"n": 5, "desync": 1}},
           "setcoded_C": {"by_bucket": {"0": {"K": 2, "n": 10, "desync": 1}, "1": {"K": 4, "n": 10, "desync": 2}}}}


def test_rank_histogram_rates_and_expected_rate():
    h = L.rank_histogram([1, 1, 2, 2, 3, 100])
    assert (h["1"], h["2"], h["3"], h["X"], h["N"]) == (2, 2, 1, 1, 6) and h["64"] == 0
    p = L.rank_rates(P2B_ROW)
    assert p["1"] == 0.1 and p["2"] == 0.2 and p["3"] == 0.2 and p["X"] == 0.0 and p["4"] is None
    c = L.expected_rate(h, p, ("C",))
    assert abs(c["rate"] - 0.1) < 1e-12 and abs(c["one_in"] - 10) < 1e-9 and c["by_rank"] == {"2": 0.4, "3": 0.2}
    a = L.expected_rate(h, p)
    assert abs(a["rate"] - 0.8 / 6) < 1e-12 and abs(a["one_in"] - 7.5) < 1e-9 and a["by_rank"]["1"] == 0.2 and a["by_rank"]["X"] == 0.0


def test_expected_rate_raises_where_a_needed_rank_has_no_rate():
    h = L.rank_histogram([1, 5]); p = L.rank_rates(P2B_ROW)
    with pytest.raises(ValueError, match="rank 5"):
        L.expected_rate(h, p)
    assert L.expected_rate(L.rank_histogram([1, 2]), p)["rate"] == (0.1 + 0.2) / 2   # rank 5 absent: no raise


def test_setcoded_rates_follow_the_bucket_rule():
    p = L.setcoded_rates(P2B_ROW)
    assert p["2"] == 0.1 and p["3"] == 0.2 and p["4"] == 0.2 and p["5"] is None and p["1"] is None and p["X"] is None


def test_fail_rate_exact_and_poisson():
    p = {"1": 0.0, "2": 0.5, "X": 0.0, **{str(r): None for r in range(3, 65)}}
    f = L.fail_rate_exact([np.array([1, 1]), np.array([2, 2])], p)
    assert abs(f["fail_rate"] - 0.375) < 1e-12 and f["archives"] == 2 and abs(f["expected_fails"] - 0.75) < 1e-12
    assert abs(L.fail_rate_exact([np.array([2, 2])], p, ("1", "X"))["fail_rate"]) < 1e-12   # C excluded: no hazard
    with pytest.raises(ValueError):
        L.fail_rate_exact([np.array([3])], p)
    assert abs(L.fail_rate_poisson(2.0, 0.5) - (1 - np.exp(-1))) < 1e-12


def test_class_buckets_and_shares():
    assert [L.class_bucket(k) for k in ("1", "A", "2", "C2", "5", "6", "C40", "X")] == ["A", "A", "C2", "C2", "C5", "C6-64", "C6-64", "X"]
    s = L.shares_by_class({"A": 1, "C2": 1, "C7": 1, "C9": 1})
    assert s == {"A": 0.25, "C2": 0.25, "C6-64": 0.5}


def test_order_diff_events_and_gap_summary():
    enc_idx = np.array([[5, 6, 7, 8]] * 3); enc_val = np.array([[4.0, 3.0, 2.0, 1.0]] * 3)
    dec_idx = np.array([[5, 6, 7, 8], [6, 5, 7, 8], [5, 6, 9, 8]])        # identical; swap at slot 0; absent token at slot 2
    ev = L.order_diff_events(enc_idx, enc_val, dec_idx, R=4)
    assert ev["pos"].tolist() == [1, 2] and ev["j"].tolist() == [0, 2] and ev["k"].tolist() == [1, -1]
    assert ev["g"][0] == 1.0 and np.isnan(ev["g"][1])
    s = L.gap_summary(ev, budget=0.5, two_tau=2.0)
    assert s["n_diff"] == 2 and s["n_absent"] == 1 and s["n_nonadjacent"] == 0 and s["count_above_budget"] == 1 and s["count_above_two_tau_census"] == 0
    assert s["by_slot_bucket"]["0"] == {"n": 1, "max_g": 1.0, "above_budget": 1} and s["by_slot_bucket"]["2-7"]["n"] == 1
    assert s["g_quantiles"]["max"] == 1.0
    empty = L.order_diff_events(enc_idx, enc_val, enc_idx, R=4)
    assert L.gap_summary(empty, 0.5, None)["n_diff"] == 0


def test_compensator_by_class_and_observed_grouping():
    p = {"1": 0.1, "2": 0.5, "X": 0.0, **{str(r): 0.0 for r in range(3, 65)}}
    exposures = [np.array([1, 1, 2]), np.array([1, 100])]              # A exposure 3 x 0.1, C exposure 1 x 0.5, X 0
    obs = L.observed_by_class({"A": 1, "C2": 1, "C7": 1})
    assert obs == {"A": 1, "C": 2, "X": 0}
    c = L.compensator(exposures, p, obs)
    assert abs(c["A"]["expected"] - 0.3) < 1e-12 and abs(c["C"]["expected"] - 0.5) < 1e-12 and c["X"]["expected"] == 0.0
    assert abs(c["A"]["ratio"] - 1 / 0.3) < 1e-9 and c["C"]["ratio"] == 4.0 and c["X"]["ratio"] is None
    assert abs(c["all"]["expected"] - 0.8) < 1e-12 and c["all"]["observed"] == 3.0 and abs(c["C"]["z"] - (2 - 0.5) / np.sqrt(0.5)) < 1e-12
    assert abs(c["predicted_first_desync_shares"]["A"] - 0.3 / 0.8) < 1e-12


def test_gap_share_below():
    s = L.gap_share_below([0.01, 0.1, 1.0, 2.0], {"bf16": 0.5, "fp16": 0.05})
    assert s["bf16"] == {"threshold": 0.5, "share": 0.5, "n": 4} and s["fp16"]["share"] == 0.25


def test_aligned_deltas_and_drift_summary():
    enc_idx = np.array([[5, 6, 7, 8]]); enc_val = np.array([[4.0, 3.0, 2.0, 1.0]])
    dec_idx = np.array([[6, 5, 9, 7]]); dec_val = np.array([[3.5, 3.9, 2.5, 2.2]])        # token 8 absent from the decoder dump
    d = L.aligned_deltas(enc_idx, enc_val, dec_idx, dec_val, R=4, chunk=1)
    assert np.allclose(d[0, :3], [-0.1, 0.5, 0.2]) and np.isnan(d[0, 3])
    s = L.drift_summary(d, budget=0.5)
    assert s["absent"] == 1 and s["adjacent_pairs"] == 2 and s["adjacent_pairs_drift_above_budget"] == 1       # |−0.1−0.5| = 0.6 > 0.5; |0.5−0.2| = 0.3
    assert s["abs_delta_q_by_slot_bucket"]["0"]["n"] == 1 and abs(s["abs_delta_q_by_slot_bucket"]["0"]["q"] - 0.1) < 1e-12


def test_third_batch_scalar_helpers():
    assert L.label_multiple(0.142, 0.03554) == 4 and L.label_multiple(0.066, 0.0331) == 2 and L.label_multiple(12.3, 3.0752) == 4
    assert L.bits_per_token(100, 50) == 16.0 and abs(L.dictionary_effect(6.0, 4.5) - 0.25) < 1e-12
    assert abs(L.crossover_length(916.685, 3.9372523387393277, 0.45473671310102537) - 263.2) < 0.1 and L.crossover_length(900, 0.4, 0.45) is None


def test_poisson_ratio_interval_matches_the_garwood_bounds():
    iv = L.poisson_ratio_interval(28, 33.282)
    assert abs(iv["ratio"] - 28 / 33.282) < 1e-12 and abs(iv["low"] - 0.56) < 0.01 and abs(iv["high"] - 1.22) < 0.01   # the critic's 0.56-1.22
    z = L.poisson_ratio_interval(0, 10.0)
    assert z["low"] == 0.0 and 0.36 < z["high"] < 0.38                                                              # 3.69 / 10 for zero events


def test_gap_binning_rates_and_apply():
    gaps = np.array([0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10]); desync = gaps < 0.025     # 2 desyncs in the lowest fifth
    e = L.gap_edges_equal_count(gaps, 5); assert len(e) == 4 and np.all(np.diff(e) > 0)
    r = L.binned_rates(gaps, desync, e); assert sum(r["n"]) == 10 and sum(r["desync"]) == 2 and r["rate"][0] == 1.0 and r["rate"][-1] == 0.0
    hz, n_empty = L.apply_rates(np.array([0.0, 0.015, 5.0]), e, r); assert hz.tolist() == [1.0, 1.0, 0.0] and n_empty == 0
    e2 = L.gap_edges_log(gaps, 4); assert len(e2) == 3 and e2[0] > 0.01 and e2[-1] < 0.10
    r2 = {"n": [1, 0, 1], "desync": [1, 0, 0], "rate": [1.0, None, 0.0]}
    hz, n_empty = L.apply_rates(np.array([0.5, 1.5, 2.5]), np.array([1.0, 2.0]), r2); assert hz.tolist() == [1.0, 1.0, 0.0] and n_empty == 1   # empty bin -> nearest


def test_distinct_prefixes_counts_shared_contexts_once():
    tokens = np.array([[1, 2, 3], [1, 2, 9], [1, 5, 3]])             # L = 3, kept positions per sequence L - 1 = 2
    assert L.distinct_prefixes(tokens, [0, 2, 4], 2) == 1             # offset 0 of each sequence: the prefix (1,) three times
    assert L.distinct_prefixes(tokens, [1, 3, 5], 2) == 2             # offset 1: (1, 2), (1, 2), (1, 5)
