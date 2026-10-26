"""Capture-tool tests without torch: corpus windowing, shard-atomic resume,
top-k census equivalence with the full-logit census. The resume test kills
the run mid-shard and proves the rerun neither recomputes finished shards
nor accepts the partial one (tokenizer-lab H-1/H-2 pattern)."""

import json
from pathlib import Path

import numpy as np
import pytest

from amber.rankcensus import (calibrate_tau, calibrate_tau_topk, rank_census, rank_census_topk,
                              stable_topk)
from amber.real.capture import (Arm, atomic_savez, corpus_sha, load_arm, make_windows, run_arm,
                                shard_ok, shard_path)


class TestCorpus:
    def test_windows_are_bos_prefixed_nonoverlapping_and_seeded(self):
        ids = np.arange(1000, 2000)
        w = make_windows(ids, bos=7, seq_len=8, n_seqs=5, seed=1)
        assert w.shape == (5, 8) and (w[:, 0] == 7).all()
        bodies = [tuple(r[1:]) for r in w]
        assert len(set(bodies)) == 5
        for b in bodies:
            assert (b[0] - 1000) % 7 == 0 and list(b) == list(range(b[0], b[0] + 7))  # aligned windows
        w2 = make_windows(ids, bos=7, seq_len=8, n_seqs=5, seed=1)
        np.testing.assert_array_equal(w, w2)
        assert not np.array_equal(w, make_windows(ids, 7, 8, 5, seed=2))

    def test_too_small_corpus_rejected(self):
        with pytest.raises(ValueError):
            make_windows(np.arange(20), 0, 8, 5)

    def test_sha_is_content_bound(self):
        a = make_windows(np.arange(500), 0, 8, 4, 0)
        assert corpus_sha(a) == corpus_sha(a.copy())
        b = a.copy(); b[0, 1] += 1
        assert corpus_sha(a) != corpus_sha(b)


def _stub_forward(seed_offset=0, k=6, vocab=20):
    calls = []

    def fwd(batch):
        calls.append(batch.shape[0])
        b, L = batch.shape
        out_idx = np.empty((b, L, k), np.int32); out_val = np.empty((b, L, k), np.float32)
        for i in range(b):
            g = np.random.default_rng(int(batch[i, 1]) + seed_offset)
            logits = g.normal(size=(L, vocab))
            top = stable_topk(logits, k)
            out_idx[i] = top
            out_val[i] = np.take_along_axis(logits, top, 1)
        return out_idx, out_val
    fwd.calls = calls
    return fwd


class TestResume:
    def test_interrupt_then_resume_skips_done_and_redoes_partial(self, tmp_path):
        tokens = make_windows(np.arange(10_000), 0, 16, 10, 0)
        arm = Arm("stub", "cpu", "fp32", "none", batch=2)
        fwd = _stub_forward()

        # first run: crash during shard 2 (after shards 0 and 1 are written)
        n_seen = {"n": 0}
        def crashing(batch):
            n_seen["n"] += 1
            if n_seen["n"] == 5:  # shard_size 4, batch 2 -> 2 calls/shard; 5th call = shard 2
                raise RuntimeError("simulated connection drop")
            return fwd(batch)
        with pytest.raises(RuntimeError):
            run_arm(arm, tokens, tmp_path, crashing, topk=6, shard_size=4)
        assert shard_ok(shard_path(tmp_path / "stub", 0), 4, 6)
        assert shard_ok(shard_path(tmp_path / "stub", 1), 4, 6)
        assert not shard_path(tmp_path / "stub", 2).exists()
        assert not (tmp_path / "stub" / "DONE").exists()
        # leave a truncated/partial shard file behind: must NOT count as done
        (tmp_path / "stub" / "shard_0002.npz").write_bytes(b"garbage")
        assert not shard_ok(shard_path(tmp_path / "stub", 2), 2, 6)

        # resume: only shard 2 (2 rows -> 1 batch call) is computed
        fwd2 = _stub_forward()
        meta = run_arm(arm, tokens, tmp_path, fwd2, topk=6, shard_size=4)
        assert fwd2.calls == [2]
        assert meta["done"] is True and (tmp_path / "stub" / "DONE").exists()
        assert set(meta["shards"]) == {"0", "1", "2"}

        idx, val, m = load_arm(tmp_path, "stub")
        assert idx.shape == (10 * 16, 6) and val.shape == idx.shape
        # the resumed output equals a clean single run
        clean = tmp_path / "clean"
        run_arm(arm, tokens, clean, _stub_forward(), topk=6, shard_size=4)
        idx2, val2, _ = load_arm(clean, "stub")
        np.testing.assert_array_equal(idx, idx2); np.testing.assert_array_equal(val, val2)

    def test_batch_size_does_not_change_output(self, tmp_path):
        """Row-independent stub: batch 1 and batch 4 must produce identical
        dumps. On a real model this is the XB-3 batch-invariance check."""
        tokens = make_windows(np.arange(10_000), 0, 16, 8, 0)
        for b in (1, 4):
            run_arm(Arm(f"b{b}", "cpu", "fp32", "none", batch=b), tokens, tmp_path, _stub_forward(), topk=6, shard_size=4)
        i1, v1, _ = load_arm(tmp_path, "b1"); i4, v4, _ = load_arm(tmp_path, "b4")
        np.testing.assert_array_equal(i1, i4); np.testing.assert_array_equal(v1, v4)

    def test_nonfinite_logits_refused(self, tmp_path):
        tokens = make_windows(np.arange(1000), 0, 8, 2, 0)
        def bad(batch):
            b, L = batch.shape
            return np.zeros((b, L, 3), np.int32), np.full((b, L, 3), np.nan, np.float32)
        with pytest.raises(ValueError, match="non-finite"):
            run_arm(Arm("bad", "cpu", "fp32", "none", 1), tokens, tmp_path, bad, topk=3, shard_size=2)
        assert not shard_path(tmp_path / "bad", 0).exists()


class TestTopkCensusEquivalence:
    def test_matches_full_logit_census_when_dump_covers_flips(self):
        g = np.random.default_rng(0)
        n, v, k = 300, 40, 12
        ref = g.normal(size=(n, v)); ref[:, 0] += 2.0
        alt = ref + g.normal(scale=0.3, size=ref.shape)
        full = rank_census(ref, alt, ks=(1, 4, 8), tau=0.5)
        ri = stable_topk(ref, k); rv = np.take_along_axis(ref, ri, 1)
        ai = stable_topk(alt, k); av = np.take_along_axis(alt, ai, 1)
        top = rank_census_topk(ri, rv, ai, av, ks=(1, 4, 8), tau=0.5)
        assert top.top1_flips == full.top1_flips
        assert top.topk_set_flip_rate == full.topk_set_flip_rate
        assert top.topk_order_flip_rate == full.topk_order_flip_rate
        assert top.flips_beyond_tau == full.flips_beyond_tau
        assert top.flip_gap_median == pytest.approx(full.flip_gap_median)
        assert top.dispersion_index == pytest.approx(full.dispersion_index)
        assert 0.8 < top.delta_coverage <= 1.0  # k=12 of 40 under sigma=0.3 noise

    def test_tie_order_in_dump_is_not_a_flip(self):
        ri = np.array([[5, 9, 2]]); rv = np.array([[1.0, 0.5, 0.5]])
        ai = np.array([[5, 2, 9]]); av = np.array([[1.0, 0.5, 0.5]])  # torch.topk tie order differs
        c = rank_census_topk(ri, rv, ai, av, ks=(1, 2, 3))
        assert c.top1_flips == 0 and c.topk_order_flip_rate["3"] == 0.0

    def test_calibration_topk_matches_full(self):
        g = np.random.default_rng(1)
        ref = g.normal(size=(500, 30)); ben = ref + g.normal(scale=1e-3, size=ref.shape)
        ri = stable_topk(ref, 30); rv = np.take_along_axis(ref, ri, 1)
        bi = stable_topk(ben, 30); bv = np.take_along_axis(ben, bi, 1)
        assert calibrate_tau_topk(ri, rv, bi, bv) == pytest.approx(calibrate_tau(ref, ben))
