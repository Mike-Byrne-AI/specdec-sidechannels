"""tools/build_balanced_groups.py: the pinned Fiedler-order quantile lens on synthetic affinities (balanced sizes,
determinism, the sign anchor, the zero-degree rule, the refusal on a disconnected graph) and, where the committed
artifact exists, its recorded construction against the pinned rule."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build_balanced_groups as bb  # noqa: E402

# The builder imports scipy lazily inside fiedler_order; pyproject's `analysis` extra carries it, the
# `dev` extra does not, so the four tests that reach it skip where only `[dev]` is installed (found
# 2026-10-13 by the public cut's fresh-clone proof: 4 failures with ModuleNotFoundError). Where the
# skip must not hide a missing extra (the public cut's CI and proof set SIDEBAND_REQUIRE_ANALYSIS=1
# and install `.[dev,analysis]`), the tests run and fail loudly instead.
needs_scipy = pytest.mark.skipif(importlib.util.find_spec("scipy") is None and os.environ.get("SIDEBAND_REQUIRE_ANALYSIS", "0") in ("", "0"),
                                 reason="scipy is in the analysis extra, not dev; the builder imports it lazily")

ARTIFACT = ROOT / "results" / "real" / "concept_groups_olmoe_balanced_v1.json"


def two_blobs(n_a: int = 40, n_b: int = 50, seed: int = 0, zero: int = 0) -> np.ndarray:
    """A connected two-cluster affinity (dense within, one weak bridge) with `zero` isolated nodes appended."""
    gen = np.random.default_rng(seed)
    n = n_a + n_b
    S = np.zeros((n, n))
    S[:n_a, :n_a] = gen.uniform(0.5, 1.0, (n_a, n_a))
    S[n_a:, n_a:] = gen.uniform(0.5, 1.0, (n_b, n_b))
    S = 0.5 * (S + S.T)
    np.fill_diagonal(S, 0.0)
    S[0, n_a] = S[n_a, 0] = 0.05           # the bridge
    if zero:
        Z = np.zeros((n + zero, n + zero))
        Z[:n, :n] = S
        S = Z
    return S


def test_bin_sizes_spread_the_remainder_over_the_first_bins():
    assert bb.bin_sizes(490, 16) == [31] * 10 + [30] * 6
    assert bb.bin_sizes(32, 16) == [2] * 16
    assert bb.bin_sizes(17, 16) == [2] + [1] * 15


@needs_scipy
def test_fiedler_order_separates_two_blobs_and_is_deterministic():
    S = two_blobs()
    order, info = bb.fiedler_order(S)
    order2, info2 = bb.fiedler_order(S.copy())
    assert np.array_equal(order, order2) and info == info2
    # the first 40 in Fiedler order are one blob, the rest the other (either way round)
    first = set(order[:40].tolist())
    assert first == set(range(40)) or first == set(range(40, 90))
    assert info["fiedler_gap"] > 0 and info["eigenvalues_first_three"][0] == pytest.approx(0.0, abs=1e-8)


@needs_scipy
def test_sign_anchor_makes_the_order_independent_of_eigenvector_sign(monkeypatch):
    S = two_blobs(seed=3)
    order, info = bb.fiedler_order(S)
    real_eigh = np.linalg.eigh

    def flipped(L):
        w, V = real_eigh(L)
        return w, -V                      # an eigensolver returning the opposite sign

    monkeypatch.setattr(np.linalg, "eigh", flipped)
    order_f, info_f = bb.fiedler_order(S)
    assert np.array_equal(order, order_f)
    assert info_f["sign_anchor_degree"] == info["sign_anchor_degree"]


@needs_scipy
def test_balanced_groups_are_balanced_and_assign_zero_degree_to_the_smallest_bins():
    S = two_blobs(n_a=240, n_b=250, zero=20)        # 490 nonzero + 20 zero-degree, the OLMoE shape
    labels, info = bb.balanced_groups(S, 16)
    assert labels.shape == (510,) and labels.min() == 0 and labels.max() == 15
    assert info["bin_sizes_nonzero"] == [31] * 10 + [30] * 6
    assert info["group_sizes_nonzero_only"] == [31] * 10 + [30] * 6
    assert info["n_zero_degree"] == 20 and len(info["zero_degree_assignment"]) == 20
    # the six 30-bins fill first, then round-robin over the lowest ids: fourteen groups of 32, two of 31
    assert sorted(info["group_sizes"]) == [31] * 2 + [32] * 14 and max(info["group_sizes"]) <= 32
    first_six = [g for _, g in info["zero_degree_assignment"][:6]]
    assert first_six == [10, 11, 12, 13, 14, 15]
    assert info["n_connected_components_nonzero"] == 1 and "sign_anchor_concept" in info
    # contiguous bins in Fiedler order: edges tile 0..490
    edges = info["bin_edges_in_fiedler_order"]
    assert edges[0][0] == 0 and edges[-1][1] == 490 and all(a[1] == b[0] for a, b in zip(edges, edges[1:]))


@needs_scipy
def test_disconnected_graph_is_refused_not_fallen_back():
    S = two_blobs()
    S[0, 40] = S[40, 0] = 0.0            # cut the bridge
    with pytest.raises(SystemExit, match="connected components"):
        bb.fiedler_order(S)
    with pytest.raises(SystemExit, match="zero-degree node"):
        bb.fiedler_order(two_blobs(zero=1))


def test_cli_refuses_an_existing_artifact_and_an_unregistered_group_count(tmp_path):
    import subprocess
    out = tmp_path / "x.json"
    out.write_text("{}", encoding="utf-8")
    res = subprocess.run([sys.executable, str(ROOT / "tools" / "build_balanced_groups.py"), "--out-dir", str(tmp_path),
                          "--name", "x"], capture_output=True, text=True, cwd=ROOT)
    assert res.returncode != 0 and "first successful run is the artifact" in (res.stderr + res.stdout)
    res2 = subprocess.run([sys.executable, str(ROOT / "tools" / "build_balanced_groups.py"), "--n-groups", "8",
                           "--name", "unregistered_probe"], capture_output=True, text=True, cwd=ROOT)
    assert res2.returncode != 0 and "unregistered --n-groups" in (res2.stderr + res2.stdout)


def test_committed_artifact_follows_the_pinned_rule():
    """FAILS, never skips, when the committed artifact is missing (the registration's evidence; critic A10 of the
    reader-and-lens design round); pins the values PRE-FREEZE (c) records."""
    assert ARTIFACT.exists(), f"{ARTIFACT} is committed evidence of the reader-and-lens registration and is missing"
    g = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    c = g["construction"]
    assert g["n_groups"] == 16 and g["glue_class_id"] == 16 and g["C_source_concepts"] == 510
    assert len(g["group_of_concept"]) == 510 and max(c["group_sizes"]) <= 32 and min(c["group_sizes"]) >= 30
    assert c["group_sizes"] == [32] * 14 + [31] * 2 and round(c["fiedler_gap"], 4) == 0.0166
    assert round(g["diagnostics"]["persistence_train_glue_dropped"]["balanced_L3"], 4) == 0.1033
    assert round(g["diagnostics"]["persistence_train_glue_dropped"]["k16"], 4) == 0.2293
    assert c["bin_sizes_nonzero"] == bb.bin_sizes(510 - c["n_zero_degree"], 16)
    assert c["n_connected_components_nonzero"] == 1 and c["fiedler_gap"] > 0
    assert sum(c["group_sizes"]) == 510 and len(c["zero_degree_assignment"]) == c["n_zero_degree"]
    assert g["provenance"]["first_run_is_artifact"] is True and "Fiedler" in g["provenance"]["rule"]
    assert set(g["diagnostics"]["persistence_train_glue_dropped"]) >= {"balanced_L3", "k16"}


# ---- the builders' bytes (2026-10-16, lane C of the 2026-10-15 image audit, item S5b-K-6) ----
# docs/BLUEPRINT.md's READER-AND-LENS RE-TEST AT S3 freeze record pins tools/build_balanced_groups.py
# by the 12-hex prefix d6fda8997c65 (its raw LF bytes; the file is `-text` in .gitattributes), but the
# builder imports its math from tools/build_concept_groups.py, which nothing pinned: an edit there
# changed what the pinned file computes while the pin held. Both digests (sha256 of the bytes with
# CRLF folded to LF) are held here as found on 2026-10-16; a change to either is a registered act
# with a dated line in the freeze record, and this test moves with it.
BALANCED_BUILDER_SHA256 = "d6fda8997c6516e35ae047c722ad979540052a12dca7d0de3b1ef96d518257b0"
CONCEPT_BUILDER_SHA256 = "72d621b17e99c8a0587a6b0f9a2dc388f0d560081e5e5401301a857d3539de97"


def _sha_lf(path):
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def test_both_lens_builders_are_the_pinned_bytes():
    root = Path(__file__).resolve().parent.parent
    assert _sha_lf(root / "tools" / "build_balanced_groups.py") == BALANCED_BUILDER_SHA256
    assert BALANCED_BUILDER_SHA256.startswith("d6fda8997c65")   # the freeze record's 12-hex pin
    assert _sha_lf(root / "tools" / "build_concept_groups.py") == CONCEPT_BUILDER_SHA256
