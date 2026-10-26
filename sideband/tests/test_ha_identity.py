"""tools/ha_identity_check.py: the closed-form recovery arithmetic behind
F-23, on a synthetic unembedding (no model weights, no torch): the
top-k (id, log-prob) system recovers h exactly once k >= d + 1 rows are
used, and the committed result file (when present) carries the pinned
row count and the identity-level numbers."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import ha_identity_check as hic  # noqa: E402


def test_topk_recovery_is_exact_above_d_plus_one_and_degrades_below():
    rng = np.random.default_rng(0)
    V, d = 3000, 24
    W = rng.normal(0, 1, (V, d)).astype(np.float32)
    h = rng.normal(0, 3, d).astype(np.float32)
    logits = W @ h
    full = hic.topk_recover(W, logits, d + 1)
    assert np.allclose(full, h, atol=1e-3, rtol=1e-4)
    r2 = lambda hh: 1 - ((hh - h) ** 2).sum() / ((h - h.mean()) ** 2).sum()
    assert r2(hic.topk_recover(W, logits, 200)) > 0.999
    partial = r2(hic.topk_recover(W, logits, 8))
    assert partial < 0.9          # underdetermined: minimum-norm, not exact
    assert hic.TOPK == (4097, 2048, 512, 128, 32)
    assert hic.N_PROMPTS == 3 and hic.ROWS_PER_PROMPT == 4
    assert hic.MODEL == "meta-llama/Llama-3.1-8B-Instruct"


@pytest.mark.skipif(not (ROOT / "results" / "real" / "oq16_ha_identity.json").exists(),
                    reason="committed identity check not present")
def test_committed_identity_result_shape_and_numbers():
    d = json.loads((ROOT / "results" / "real" / "oq16_ha_identity.json").read_text())
    assert d["n_rows"] == 48 and len(d["provenance"]) == 12
    assert d["lm_head"]["tie_word_embeddings"] is False
    assert d["lm_head"]["vocab"] == 128256 and d["lm_head"]["d"] == 4096
    assert d["forward"]["argmax_match_rate"] == 1.0
    assert d["forward"]["top32_overlap_mean"] > 0.99
    assert d["inverse_full_logits"]["rel_err_max"] < 1e-6
    assert d["inverse_full_logits"]["f64_logits_rel_err_max"] < 1e-12   # the identity itself
    c = d["conditioning"]
    assert c["numerical_rank"] == 4096 and c["sigma_min"] > 1.0          # full column rank
    assert 0.9 < c["ones_vector_fraction_in_col"] < 1.0                   # the direction that could hurt
    assert c["sigma_min_augmented_W_minus_ones"] > 0.99 * c["sigma_min"]  # ... and does not
    pr = d["precision"]
    assert pr["from_bf16_logprobs_logZ_unknown_rel_err_max"] < 1e-2       # p alone at bf16 precision
    tk = d["topk_closed_form"]
    assert tk["4097"]["r2_median"] > 0.999999
    assert tk["32"]["r2_median"] < 0.05
    # monotone in k, as the identity implies
    meds = [tk[str(k)]["r2_median"] for k in hic.TOPK]
    assert meds == sorted(meds, reverse=True)
