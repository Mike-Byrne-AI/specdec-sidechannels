"""Phase 1 tooling tests without torch: stable rank, exact amber bit
accounting vs the codec's own coder, and shard-atomic resume of both stages."""

import numpy as np
import pytest

from amber.codec import stable_order
from amber.real.divergence import (load_generated, load_rank, run_generate, run_rank, shard_ok,
                                   shard_path, stable_rank)


class TestStableRank:
    def test_matches_codec_stable_order(self):
        g = np.random.default_rng(0)
        logits = g.normal(size=(50, 30)).round(1)  # rounding creates ties
        true = g.integers(0, 30, 50)
        ranks = stable_rank(logits, true)
        for t in range(50):
            order = stable_order(logits[t])
            assert ranks[t] == int(np.flatnonzero(order == true[t])[0]) + 1

    def test_argmax_rank_is_one_and_ties_break_by_index(self):
        logits = np.array([[1.0, 3.0, 3.0, 0.0]])
        assert stable_rank(logits, np.array([1]))[0] == 1
        assert stable_rank(logits, np.array([2]))[0] == 2
        assert stable_rank(logits, np.array([0]))[0] == 3


def _amber_bits(ranks):
    from amber.bits import BitWriter, gamma_encode
    w = BitWriter(); gap = 0
    for r in ranks:
        if r == 1:
            gap += 1; continue
        gamma_encode(w, gap + 1); gamma_encode(w, int(r) - 1); gap = 0
    return w.n_bits


def test_amber_bits_roundtrip_reconstructs_ranks():
    from amber.bits import BitReader, BitWriter, gamma_decode, gamma_encode
    ranks = np.array([1, 1, 3, 1, 2, 7, 1, 1, 1, 4])
    w = BitWriter(); gap = 0; n_corr = 0
    for r in ranks:
        if r == 1:
            gap += 1; continue
        gamma_encode(w, gap + 1); gamma_encode(w, int(r) - 1); gap = 0; n_corr += 1
    assert w.n_bits == _amber_bits(ranks)
    rd = BitReader(w.to_bytes(), w.n_bits); out = np.ones(len(ranks), dtype=int); pos = -1
    for _ in range(n_corr):
        g = gamma_decode(rd) - 1; r = gamma_decode(rd) + 1; pos += g + 1; out[pos] = r
    np.testing.assert_array_equal(out, ranks)


class TestResume:
    def test_generate_and_rank_resume(self, tmp_path):
        prompts = [{"prompt": f"p{i}", "family": "f"} for i in range(6)]
        enc = lambda s: [1, 100 + int(s[1:])]  # noqa: E731
        calls = []
        def gen(ids):
            calls.append(ids[-1]);
            if len(calls) == 4:
                raise RuntimeError("drop")
            return [ids[-1] + 1, ids[-1] + 2, 2]
        with pytest.raises(RuntimeError):
            run_generate(prompts, enc, gen, tmp_path, shard_size=2, log=lambda *_: None)
        assert shard_ok(shard_path(tmp_path / "generate", 0), ("ids",)) and not shard_path(tmp_path / "generate", 1).exists()
        calls.clear()
        def gen2(ids): calls.append(ids[-1]); return [ids[-1] + 1, ids[-1] + 2, 2]
        run_generate(prompts, enc, gen2, tmp_path, shard_size=2, log=lambda *_: None)
        assert calls == [102, 103, 104, 105]  # shard 0 not recomputed
        seqs = load_generated(tmp_path)
        assert [r for r, _, _ in seqs] == list(range(6))
        assert seqs[3][1].tolist() == [1, 103, 104, 105, 2] and seqs[3][2] == 2

        scored = []
        def scorer(ids, plen):
            scored.append(len(scored))
            if len(scored) == 5:
                raise RuntimeError("drop")
            k = len(ids) - plen
            return {"rank": np.arange(1, k + 1, dtype=np.int32), "log2q": -np.ones(k, np.float32), "log2qmax": -np.zeros(k, np.float32),
                    "gap": np.full(k, 0.5, np.float32), "argmax_is_true": np.zeros(k, bool)}
        with pytest.raises(RuntimeError):
            run_rank(seqs, scorer, tmp_path, "draft", shard_size=2, log=lambda *_: None)
        scored.clear()
        def scorer2(ids, plen):
            scored.append(1); k = len(ids) - plen
            return {"rank": np.arange(1, k + 1, dtype=np.int32), "log2q": -np.ones(k, np.float32), "log2qmax": -np.zeros(k, np.float32),
                    "gap": np.full(k, 0.5, np.float32), "argmax_is_true": np.zeros(k, bool)}
        run_rank(seqs, scorer2, tmp_path, "draft", shard_size=2, log=lambda *_: None)
        assert len(scored) == 2  # only the crashed shard (2 prompts) recomputed
        d = load_rank(tmp_path, "draft")
        assert len(d["per_prompt"]) == 6 and d["per_prompt"][5]["rank"].tolist() == [1, 2, 3]
