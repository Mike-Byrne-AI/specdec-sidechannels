"""OQ-4 glue identification: pure numpy, CI-safe.

The glue set feeds the disagreement gate's concept-space exclusion (D-7); a
wrong set silently reinstates the F-3 self-cancellation (K-7), so the
identification rule and the remap both get pinned here.
"""

import json

import numpy as np
import pytest

from sideband.glue import glue_remap, identify_glue_buckets, load_glue, top_frequency_tokens


def _counts(pairs):
    return {int(t): int(n) for t, n in pairs}


class TestTopFrequencyTokens:
    def test_sorted_by_count_then_id(self):
        ids, ns = top_frequency_tokens(_counts([(5, 10), (2, 30), (9, 10), (1, 5)]), top_n=3)
        # count 30 first; then the two count-10 tokens, LOWER id first.
        assert ids.tolist() == [2, 5, 9]
        assert ns.tolist() == [30, 10, 10]

    def test_dict_order_irrelevant(self):
        a = _counts([(1, 5), (2, 9), (3, 9)])
        b = dict(reversed(list(a.items())))
        ia, _ = top_frequency_tokens(a, 2)
        ib, _ = top_frequency_tokens(b, 2)
        assert ia.tolist() == ib.tolist() == [2, 3]

    def test_string_keys_accepted(self):
        ids, _ = top_frequency_tokens({"7": 3, "1": 9}, 2)
        assert ids.tolist() == [1, 7]

    def test_negative_count_rejected(self):
        with pytest.raises(ValueError, match="negative"):
            top_frequency_tokens({1: -2}, 1)


class TestIdentifyGlue:
    """80 tokens, 8 buckets (token t -> bucket t // 10)."""

    BUCKETS = np.arange(80) // 10

    def test_concentrated_mass_yields_small_glue(self):
        # bucket 0 holds 70% of top mass, bucket 1 another 20%, rest dust.
        counts = _counts([(t, 700) for t in range(10)]
                         + [(t, 200) for t in range(10, 20)]
                         + [(t, 10) for t in range(20, 40)])
        res = identify_glue_buckets(self.BUCKETS, counts, top_n=100, mass_cover=0.80,
                                    concentration_cap_frac=0.5)  # k=8: default k/8 cap is 1
        assert res["glue_bucket_ids"] == [0, 1]
        assert res["diagnostics"]["covered_mass_share"] >= 0.80
        assert not res["diagnostics"]["concentration_flag"]  # 2 buckets <= cap 4
        per = {d["bucket"]: d for d in res["diagnostics"]["per_bucket"]}
        assert per[0]["n_top_tokens"] == 10
        assert per[0]["top_mass_share"] > per[1]["top_mass_share"]

    def test_mass_cover_monotone(self):
        counts = _counts([(t, 100 - t) for t in range(80)])
        lo = identify_glue_buckets(self.BUCKETS, counts, mass_cover=0.60)["glue_bucket_ids"]
        hi = identify_glue_buckets(self.BUCKETS, counts, mass_cover=0.90)["glue_bucket_ids"]
        assert set(lo) <= set(hi)

    def test_uniform_spread_sets_concentration_flag(self):
        # top-100 mass spread evenly over all 8 buckets: covering 80% needs
        # 7 of 8 buckets > k/8 = 1 -> the K-7 warning flag fires.
        counts = _counts([(t, 10) for t in range(80)])
        res = identify_glue_buckets(self.BUCKETS, counts, mass_cover=0.80)
        assert res["diagnostics"]["concentration_flag"]

    def test_unbucketed_tokens_cannot_vote(self):
        buckets = self.BUCKETS.copy()
        buckets[:10] = -1  # the heaviest tokens are absent from buckets.json
        counts = _counts([(t, 700) for t in range(10)] + [(t, 200) for t in range(10, 20)]
                         + [(t, 1) for t in range(20, 30)])
        res = identify_glue_buckets(buckets, counts, mass_cover=0.80)
        assert res["diagnostics"]["n_top_tokens_unbucketed"] == 10
        assert 0 not in res["glue_bucket_ids"]  # bucket 0 has no bucketed top tokens
        assert 1 in res["glue_bucket_ids"]

    def test_count_rule_crosscheck_reported(self):
        counts = _counts([(t, 50) for t in range(12)])  # 10 tokens b0, 2 tokens b1
        res = identify_glue_buckets(self.BUCKETS, counts, mass_cover=0.80)
        assert res["diagnostics"]["count_rule_ge5_buckets"] == [0]

    def test_out_of_vocab_token_id_rejected(self):
        with pytest.raises(ValueError, match="outside the vocab"):
            identify_glue_buckets(self.BUCKETS, _counts([(200, 5)]))

    def test_deterministic_bucket_tiebreak(self):
        # buckets 2 and 5 tie exactly; the lower id wins the prefix cut.
        counts = _counts([(20, 100), (50, 100)])
        res = identify_glue_buckets(self.BUCKETS, counts, top_n=100, mass_cover=0.5)
        assert res["glue_bucket_ids"] == [2]


class TestGlueRemap:
    def test_compact_order_preserving(self):
        bot = np.array([0, 1, 2, 3, 2, -1])
        smap, gmask, C = glue_remap(bot, [1, 3])
        assert C == 2
        # concept buckets 0,2 -> compact 0,1; glue and unbucketed -> -1
        assert smap.tolist() == [0, -1, 1, -1, 1, -1]
        assert gmask.tolist() == [False, True, False, True, False, False]

    def test_empty_glue_is_identity_compaction(self):
        bot = np.array([0, 1, 2])
        smap, gmask, C = glue_remap(bot, [])
        assert smap.tolist() == [0, 1, 2] and C == 3 and not gmask.any()

    def test_errors(self):
        bot = np.array([0, 1, 2])
        with pytest.raises(ValueError, match="outside"):
            glue_remap(bot, [5])
        with pytest.raises(ValueError, match="duplicate"):
            glue_remap(bot, [1, 1])
        with pytest.raises(ValueError, match=">= 2"):
            glue_remap(bot, [0, 1])  # leaves one concept bucket


class TestRejectionMasses:
    """Hand-computed residual decomposition (kills the inverted-glue-mask
    mutation: glue mass must be exactly r on GLUE tokens, nothing else).
    6 tokens, buckets [0,0,1,1,2,2], glue = bucket 2.
    p-q clipped = [.2, 0, .1, 0, .1, 0] -> r = [.5, 0, .25, 0, .25, 0]."""

    BOT = np.array([0, 0, 1, 1, 2, 2])
    GMASK = np.array([False, False, False, False, True, True])
    P = np.array([0.3, 0.1, 0.2, 0.1, 0.2, 0.1])
    Q = np.array([0.1, 0.1, 0.1, 0.3, 0.1, 0.3])

    def test_proposed_in_concept_bucket(self):
        from sideband.glue import rejection_masses

        cross, glue = rejection_masses(self.P, self.Q, self.BOT, proposed=0,
                                       glue_mask=self.GMASK)
        assert cross == pytest.approx(0.5, abs=1e-15)   # r outside bucket 0
        assert glue == pytest.approx(0.25, abs=1e-15)   # r on tokens 4,5
        # derived concept-other (AuditRecord docstring): cross - glue
        assert cross - glue == pytest.approx(0.25, abs=1e-15)

    def test_proposed_in_glue_bucket(self):
        from sideband.glue import rejection_masses

        cross, glue = rejection_masses(self.P, self.Q, self.BOT, proposed=4,
                                       glue_mask=self.GMASK)
        assert cross == pytest.approx(0.75, abs=1e-15)  # r outside bucket 2
        assert glue == pytest.approx(0.25, abs=1e-15)   # incl. proposed's own bucket
        # derived concept-other for proposed-in-glue: 1 - glue
        assert 1.0 - glue == pytest.approx(0.75, abs=1e-15)

    def test_no_mask_returns_none_glue(self):
        from sideband.glue import rejection_masses

        cross, glue = rejection_masses(self.P, self.Q, self.BOT, proposed=0)
        assert cross == pytest.approx(0.5, abs=1e-15) and glue is None

    def test_delegates_to_residual_distribution(self):
        """p == q -> residual falls back to p itself (specdec semantics)."""
        from sideband.glue import rejection_masses

        cross, glue = rejection_masses(self.P, self.P, self.BOT, proposed=2,
                                       glue_mask=self.GMASK)
        assert cross == pytest.approx(1.0 - 0.3, abs=1e-15)  # p outside bucket 1
        assert glue == pytest.approx(0.3, abs=1e-15)


class TestLoadGlue:
    @staticmethod
    def _write(tmp_path, **fields):
        d = {"glue_bucket_ids": [0, 3], "k": 8, "buckets_sha256": "abc" * 20}
        d.update(fields)
        p = tmp_path / "glue.json"
        p.write_text(json.dumps(d))
        return str(p)

    def test_matching_sha_loads(self, tmp_path):
        ids, data = load_glue(self._write(tmp_path), expect_buckets_sha256="abc" * 20)
        assert ids == [0, 3] and data["k"] == 8

    def test_sha_mismatch_refused(self, tmp_path):
        with pytest.raises(SystemExit, match="derived from buckets sha"):
            load_glue(self._write(tmp_path), expect_buckets_sha256="def" * 20)

    def test_override_allows_mismatch(self, tmp_path):
        ids, _ = load_glue(self._write(tmp_path), expect_buckets_sha256="def" * 20,
                           allow_mismatch=True)
        assert ids == [0, 3]

    def test_none_path(self):
        assert load_glue(None) == (None, None)
