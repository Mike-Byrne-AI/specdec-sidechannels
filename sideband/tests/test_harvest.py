"""Phase-2 harvest: alignment conventions and the summarizer evidence chain
(CI-safe), plus the shadow harvester core (torch tests; skip in CI per the
no-torch rule)."""

import json
import sys
from pathlib import Path

import numpy as np
import pytest

from sideband.harvest import (GAMMA_DEFAULT, label_index, pairs_per_row,
                              split_of_prompt, total_pairs)

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))


def _has(mod: str) -> bool:
    import importlib.util

    return importlib.util.find_spec(mod) is not None


class TestHarvestConventions:
    def test_label_index_offset1_is_anchor_token(self):
        # Offset 1 labels the token sampled FROM p_a — the block-start rule.
        assert label_index(0, 1) == 0
        assert label_index(5, 1) == 5
        assert label_index(5, 4) == 8

    def test_label_index_rejects_bad_args(self):
        with pytest.raises(ValueError):
            label_index(-1, 1)
        with pytest.raises(ValueError):
            label_index(0, 0)

    def test_pairs_per_row_closed_form(self):
        # For length >= gamma: gamma*L - gamma*(gamma-1)/2
        assert pairs_per_row(200, 4) == 4 * 200 - 6 == 794
        assert pairs_per_row(4, 4) == 4 + 3 + 2 + 1
        # Short rows: offsets that run off the end contribute nothing.
        assert pairs_per_row(2, 4) == 2 + 1
        assert pairs_per_row(1, 4) == 1
        assert pairs_per_row(0, 4) == 0
        with pytest.raises(ValueError):
            pairs_per_row(-1, 4)

    def test_total_pairs_sums_rows(self):
        assert total_pairs([200, 2, 0], 4) == 794 + 3 + 0
        assert GAMMA_DEFAULT == 4

    def test_split_rule_pinned(self):
        # prompt_idx % 7: {0..4} train, 5 val, 6 test -> 150/30/30 over 210.
        splits = [split_of_prompt(i) for i in range(210)]
        assert splits.count("train") == 150
        assert splits.count("val") == 30
        assert splits.count("test") == 30
        assert split_of_prompt(0) == "train"
        assert split_of_prompt(5) == "val"
        assert split_of_prompt(6) == "test"
        assert split_of_prompt(209) == "test"  # 209 = 7*29 + 6
        with pytest.raises(ValueError):
            split_of_prompt(-1)


class TestSummarizeHarvest:
    """The summarizer IS the evidence chain (sha binding, cross-seed identity,
    count recomputation) — an unverified verifier is not a chain. CI-safe:
    synthetic npz+meta fixtures, no torch."""

    P, T, L, TOP_N, N_SLOTS = 7, 5, 2, 4, 8

    _BASE_META = {
        "model": "test-model", "layer_regex": r"mlp\.down_proj$", "layers": "0,1",
        "n_slots": 8, "top_n": 4, "sketch_seed": 0, "prompts": "data/prompts.jsonl",
        "n_prompts": 7, "n_prompts_used": 7, "max_new": 5, "temperature": 1.0,
        "top_m": 4, "buckets16": "b16.json", "buckets32": "b32.json",
        "buckets64": "b64.json", "buckets512": "b512.json", "load_4bit": True,
        "no_chat_template": False, "chat_template_used": True,
        "date_string_pinned": "26 Jul 2024", "target_load": "nf4",
        "alignment": "block-start", "split_rule": "prompt_idx % 7",
        "layer_names": ["la", "lb"], "sketch_layer_seeds": {"la": 1, "lb": 2},
        "row_seed_convention": "spawn", "prompts_sha256": "x",
        "buckets16_sha256": "x", "buckets32_sha256": "x",
        "buckets64_sha256": "x", "buckets512_sha256": "x", "gamma": 4,
        "torch_version": "t", "transformers_version": "tf",
    }

    def _write_seed(self, d, seed, lengths, meta_over=None, pidx=None, drop_mass=None):
        import hashlib

        lengths = np.asarray(lengths, np.int32)
        P, T, L, top_n = len(lengths), self.T, self.L, self.TOP_N
        rng = np.random.default_rng(seed + 1)
        valid = np.arange(T)[None, :] < lengths[:, None]
        tokens = np.where(valid, rng.integers(1, 64, (P, T)), 0).astype(np.int32)
        slots = np.full((P, T, L, top_n), -1, np.int16)
        for pi in range(P):
            for ai in range(int(lengths[pi])):
                for li in range(L):
                    slots[pi, ai, li, :3] = np.sort(
                        rng.choice(self.N_SLOTS, 3, replace=False)).astype(np.int16)
        mass = np.zeros((P, T, 4), np.float16)
        mass[valid] = 0.25  # exact in f16; sums to exactly 1 on valid anchors
        entropy = np.where(valid, 0.5, 0.0).astype(np.float32)
        hidden = np.zeros((P, T, 3), np.float16)
        hidden[valid] = 1.0
        npz = d / f"shadow_s{seed}.npz"
        arrays = dict(tokens=tokens, lengths=lengths,
                      prompt_idx=(pidx if pidx is not None else np.arange(P, dtype=np.int32)),
                      slots=slots, entropy=entropy, hidden=hidden,
                      mass16=mass, mass32=mass, mass64=mass, mass512=mass)
        for k in drop_mass or ():
            del arrays[k]
        np.savez(npz, **arrays)
        meta = {**self._BASE_META, "seed": seed, "npz_file": npz.name,
                "npz_sha256": hashlib.sha256(npz.read_bytes()).hexdigest(),
                "n_anchors": int(lengths.sum()),
                "n_pairs": int(total_pairs(lengths, GAMMA_DEFAULT))}
        if meta_over:
            meta.update(meta_over)
        (d / f"shadow_s{seed}.meta.json").write_text(json.dumps(meta))
        return npz

    def test_counts_splits_and_verdict(self, tmp_path):
        from summarize_harvest import summarize

        l0, l1 = [3, 1, 4, 2, 5, 2, 3], [2] * 7
        self._write_seed(tmp_path, 0, l0)
        self._write_seed(tmp_path, 1, l1)
        s = summarize(tmp_path)
        assert s["n_pairs_total"] == total_pairs(l0) + total_pairs(l1)
        assert s["pairs_by_offset"]["offset_1"] == sum(l0) + sum(l1)
        assert s["pairs_by_offset"]["offset_4"] == sum(max(0, n - 3) for n in l0 + l1)
        # prompts 0..6 hit each residue once: train {0..4}, val {5}, test {6}
        assert s["prompts_by_split"] == {"train": 5, "val": 1, "test": 1}
        assert s["pairs_by_split"]["val"] == pairs_per_row(l0[5]) + pairs_per_row(l1[5])
        assert s["pairs_by_split"]["test"] == pairs_per_row(l0[6]) + pairs_per_row(l1[6])
        assert s["exit_met"] is False and s["verdict"] == "EXIT_BAR_NOT_MET"
        assert s["problems"] == []
        assert len(s["slot_diagnostics"]["occupancy_entropy_bits"]) == self.L
        assert s["slot_diagnostics"]["mean_unique_slots_per_anchor"] == [3.0, 3.0]
        assert s["sanity"]["mass_sum_max_abs_err"]["mass16"] < 1e-6

    def test_sha_mismatch_refused(self, tmp_path):
        from summarize_harvest import summarize

        npz = self._write_seed(tmp_path, 0, [2] * 7)
        with npz.open("ab") as f:
            f.write(b"x")
        with pytest.raises(SystemExit, match="sha mismatch"):
            summarize(tmp_path)

    def test_identity_mismatch_refused(self, tmp_path):
        from summarize_harvest import summarize

        self._write_seed(tmp_path, 0, [2] * 7)
        self._write_seed(tmp_path, 1, [2] * 7, meta_over={"n_slots": 999})
        with pytest.raises(SystemExit, match="disagrees"):
            summarize(tmp_path)

    def test_prompt_idx_mismatch_refused(self, tmp_path):
        from summarize_harvest import summarize

        self._write_seed(tmp_path, 0, [2] * 7)
        self._write_seed(tmp_path, 1, [2] * 7, pidx=np.arange(1, 8, dtype=np.int32))
        with pytest.raises(SystemExit, match="prompt_idx"):
            summarize(tmp_path)

    def test_meta_count_lie_flagged(self, tmp_path):
        from summarize_harvest import summarize

        self._write_seed(tmp_path, 0, [2] * 7, meta_over={"n_pairs": 999})
        s = summarize(tmp_path)
        assert any("n_pairs" in p for p in s["problems"])
        assert s["verdict"] == "PROBLEMS"

    def test_missing_mass_space_flagged(self, tmp_path):
        from summarize_harvest import summarize

        self._write_seed(tmp_path, 0, [2] * 7, drop_mass=["mass512"])
        s = summarize(tmp_path)
        assert any("mass512" in p for p in s["problems"])
        assert s["verdict"] == "PROBLEMS"


class TestAuditHarvest:
    """The pre-probe audit's numbers become the Phase-3 registration's
    baselines — same standard as the summarizer: verify the verifier.
    CI-safe: synthetic npz/meta/bucket/glue fixtures."""

    def _write_rows(self, d, seed, rows_tokens, pidx=None):
        import hashlib

        rows_tokens = [list(map(int, r)) for r in rows_tokens]
        P = len(rows_tokens)
        T = max(len(r) for r in rows_tokens)
        tokens = np.zeros((P, T), np.int32)
        lengths = np.zeros(P, np.int32)
        for i, r in enumerate(rows_tokens):
            tokens[i, : len(r)] = r
            lengths[i] = len(r)
        npz = d / f"shadow_s{seed}.npz"
        np.savez(npz, tokens=tokens, lengths=lengths,
                 prompt_idx=(pidx if pidx is not None else np.arange(P, dtype=np.int32)))
        (d / f"shadow_s{seed}.meta.json").write_text(
            json.dumps({"seed": seed, "npz_file": npz.name,
                        "npz_sha256": hashlib.sha256(npz.read_bytes()).hexdigest()}))

    def _write_space(self, d, buckets, glue_ids):
        import hashlib

        bpath = d / "buckets.json"
        bpath.write_text(json.dumps({
            "n_tokens": len(buckets),
            "bucket_of_token": {str(i): int(b) for i, b in enumerate(buckets)},
        }))
        gpath = d / "glue.json"
        gpath.write_text(json.dumps({
            "glue_bucket_ids": glue_ids,
            "buckets_sha256": hashlib.sha256(bpath.read_bytes()).hexdigest(),
        }))
        return ("tiny", bpath, gpath)

    def test_contamination_detects_replay(self, tmp_path):
        from audit_harvest import audit

        space = self._write_space(tmp_path, [0, 0, 1, 1, 2, 2, 2, 2, 2, 2], [0])
        shared = list(range(1, 9))  # one 8-gram
        # prompt 0 -> train, prompt 6 -> test; test row replays train's gram
        self._write_rows(tmp_path, 0, [shared, [2] * 4, [3] * 4, [4] * 4, [5] * 4,
                                       [6] * 4, shared],
                         pidx=np.arange(7, dtype=np.int32))
        rep = audit(tmp_path, space_files=[space])
        assert rep["contamination"]["test_in_train"]["distinct_frac"] == 1.0
        assert rep["contamination"]["test_in_train"]["occurrence_frac"] == 1.0

    def test_contamination_direction_is_test_in_train(self, tmp_path):
        """Asymmetric fixture: train holds MANY distinct grams, test holds
        exactly one (shared) gram. test_in_train must read 1.0; a swapped
        overlap('train','test') would read 1/many (critic-demonstrated
        surviving mutant, now pinned)."""
        from audit_harvest import audit

        space = self._write_space(tmp_path, [0, 1] * 40, [])
        shared = list(range(8))
        train_long = list(range(8, 28))  # 13 distinct grams, none shared
        self._write_rows(tmp_path, 0,
                         [shared + train_long, [2] * 4, [3] * 4, [4] * 4, [5] * 4,
                          [6] * 4, shared],
                         pidx=np.arange(7, dtype=np.int32))
        rep = audit(tmp_path, space_files=[space])
        got = rep["contamination"]["test_in_train"]
        assert got["distinct_frac"] == 1.0
        assert got["n_distinct"] == 1  # the TEST split's gram count, not train's

    def test_sha_mismatch_refused(self, tmp_path):
        from audit_harvest import audit

        space = self._write_space(tmp_path, [0, 1] * 5, [])
        self._write_rows(tmp_path, 0, [[1, 2, 3], [4, 5, 6]], pidx=np.array([0, 1], np.int32))
        with (tmp_path / "shadow_s0.npz").open("ab") as f:
            f.write(b"x")
        with pytest.raises(SystemExit, match="sha mismatch"):
            audit(tmp_path, space_files=[space])

    def test_contamination_zero_when_disjoint(self, tmp_path):
        from audit_harvest import audit

        space = self._write_space(tmp_path, list(range(3)) * 34, [0])
        self._write_rows(tmp_path, 0,
                         [list(range(10, 20)), [2] * 4, [3] * 4, [4] * 4, [5] * 4,
                          [6] * 4, list(range(40, 50))],
                         pidx=np.arange(7, dtype=np.int32))
        rep = audit(tmp_path, space_files=[space])
        assert rep["contamination"]["test_in_train"]["distinct_frac"] == 0.0

    def test_loopy_row_detected(self, tmp_path):
        from audit_harvest import audit

        space = self._write_space(tmp_path, [0, 1] * 5, [])
        loop = (list(range(8)) * 4) + [9]  # the 8-gram (0..7) occurs 4 times
        self._write_rows(tmp_path, 0, [loop, [1, 2, 3]], pidx=np.array([0, 1], np.int32))
        rep = audit(tmp_path, space_files=[space])
        assert rep["duplication"]["loopy_row_fraction"] == pytest.approx(0.5)

    def test_label_marginals_hand_computed(self, tmp_path):
        from audit_harvest import audit

        # vocab 6: buckets [0,0,1,1,2,2], glue bucket = 2 -> concept ids
        # {0->0, 1->1}, glue class = 2. Row (train, pidx 0): tokens
        # [0, 2, 4, 3] -> labels [0, 1, GLUE, 1].
        space = self._write_space(tmp_path, [0, 0, 1, 1, 2, 2], [2])
        self._write_rows(tmp_path, 0, [[0, 2, 4, 3]], pidx=np.array([0], np.int32))
        rep = audit(tmp_path, space_files=[space])
        sp = rep["label_marginals"]["tiny"]
        assert sp["C_concept"] == 2 and sp["n_classes"] == 3 and sp["glue_class_id"] == 2
        o1 = sp["per_offset"]["offset_1"]["train"]
        # offset 1 labels = the tokens' own classes: [0, 1, 2, 1]
        assert o1["n_pairs"] == 4
        assert o1["majority_class"] == 1 and o1["majority_rate"] == pytest.approx(0.5)
        assert o1["glue_class_rate"] == pytest.approx(0.25)
        o2 = sp["per_offset"]["offset_2"]["train"]
        # offset 2 labels = classes of tokens[1:]: [1, 2, 1]
        assert o2["n_pairs"] == 3
        assert o2["majority_rate"] == pytest.approx(2 / 3)
        o4 = sp["per_offset"]["offset_4"]["train"]
        assert o4["n_pairs"] == 1 and o4["majority_class"] == 1

    def test_glue_binding_refused_on_mismatch(self, tmp_path):
        from audit_harvest import audit

        space = self._write_space(tmp_path, [0, 0, 1, 1, 2, 2], [2])
        # Tamper the buckets file after the glue binding was computed.
        space[1].write_text(json.dumps({
            "n_tokens": 6,
            "bucket_of_token": {str(i): int(b) for i, b in enumerate([0, 1, 1, 1, 2, 2])},
        }))
        self._write_rows(tmp_path, 0, [[0, 2, 4, 3]], pidx=np.array([0], np.int32))
        with pytest.raises(SystemExit, match="refusing glue"):
            audit(tmp_path, space_files=[space])


class TestFidelityCalibrationConsistency:
    """The R1 tolerances were derived from committed calibration evidence
    (recalibration amendment, cycle one). A silent constant edit must break
    this derivation chain loudly. CI-safe: reads committed jsons only."""

    def test_rider_constants_match_committed_calibration(self):
        cal_path = REPO / "results" / "real" / "fidelity_calibration.json"
        if not cal_path.exists():
            pytest.skip("calibration evidence not present")
        from sideband.real.fidelity_rider import (ARGMAX_GAP, ENTROPY_ABS_MAX,
                                                  MASS_LINF_MAX, SLOT_OVERLAP_MIN)

        cal = json.loads(cal_path.read_text())
        aligned, mis = cal["aligned"], cal["misaligned_control"]
        # The separation that justifies the tolerances:
        assert mis["min_overlap"]["max"] < SLOT_OVERLAP_MIN < aligned["min_overlap"]["min"]
        assert MASS_LINF_MAX >= aligned["mass_linf"]["max"]
        assert MASS_LINF_MAX < mis["mass_linf"]["p50"]
        # Entropy's calibration undercovered the real tail (amendment): the
        # tolerance must clear the OBSERVED audit-triple band too.
        assert ENTROPY_ABS_MAX >= aligned["ent_abs"]["max"]
        assert ENTROPY_ABS_MAX < mis["ent_abs"]["p50"]
        rp = REPO / "results" / "real" / "harvest_fidelity_rider.json"
        if rp.exists():
            rider = json.loads(rp.read_text())
            ent_seen = max(t["entropy_abs_delta"] for t in rider["triples"])
            assert ENTROPY_ABS_MAX >= ent_seen  # the observed real-data band
        assert ARGMAX_GAP > 0
        assert ARGMAX_GAP >= 2 * aligned["mass_linf"]["max"]  # a flip needs > gap/2


@pytest.mark.skipif(not _has("torch") or not _has("transformers"), reason="needs [real] extras")
class TestShadowHarvest:  # pragma: no cover - runs where torch is installed, skips in CI
    """CPU fp32 tiny model: pins the tap's numpy-reference equivalence, the
    left-padding arithmetic, determinism, EOS truncation, and the block-start
    feature alignment."""

    N_SLOTS, TOP_N, N16, N512 = 16, 8, 4, 8

    @staticmethod
    def _tiny_model():
        import torch
        from transformers import LlamaConfig, LlamaForCausalLM

        cfg = LlamaConfig(vocab_size=64, hidden_size=32, intermediate_size=64,
                          num_hidden_layers=2, num_attention_heads=4,
                          num_key_value_heads=2, max_position_embeddings=256,
                          attn_implementation="eager")
        torch.manual_seed(0)
        return LlamaForCausalLM(cfg).eval()

    def _buckets(self):
        import torch

        rng = np.random.default_rng(7)
        b16 = rng.integers(0, self.N16, size=64).astype(np.int64)
        b512 = rng.integers(0, self.N512, size=64).astype(np.int64)
        return torch.from_numpy(b16), torch.from_numpy(b512), b16, b512

    @staticmethod
    def _padded_batch(model, rows):
        """Left-pad variable-length rows (pad id 0) with an attention mask."""
        import torch

        w = max(len(r) for r in rows)
        ids = torch.zeros((len(rows), w), dtype=torch.long)
        mask = torch.zeros((len(rows), w), dtype=torch.long)
        for i, r in enumerate(rows):
            ids[i, w - len(r):] = torch.tensor(r)
            mask[i, w - len(r):] = 1
        return ids, mask

    def _run(self, model, tap, rows, row_seeds, eos_set=frozenset(), max_new=6):
        from sideband.real.shadow_telemetry import NormCatch, harvest_batch

        b16_t, b512_t, _, _ = self._buckets()
        ids, mask = self._padded_batch(model, rows)
        nc = NormCatch(model.model.norm)
        try:
            return harvest_batch(model, tap, nc, ids, mask, row_seeds, set(eos_set),
                                 max_new, 1.0, {"16": b16_t, "512": b512_t}, top_m=8)
        finally:
            nc.close()

    @staticmethod
    def _independent_slots(name, activation_row, module, n_slots, top_n):
        """Reference slot set built WITHOUT the tap object: the registered
        layer-seed formula + a fresh HashSketch + raw column norms."""
        import zlib

        from sideband.sketch import HashSketch

        col = module.weight.detach().float().norm(dim=0).numpy()
        imp = np.abs(activation_row) * col
        sk = HashSketch(len(imp), n_slots, seed=0 + zlib.crc32(name.encode()) % 100_000)
        return sk.slots_for(imp, top_n)

    def test_tap_matches_numpy_reference(self):
        import torch

        from sideband.real.shadow_telemetry import ShadowTap

        model = self._tiny_model()
        raw: dict[str, object] = {}

        def keep_raw(name):
            def hook(_m, inputs):
                raw[name] = inputs[0][:, -1, :].detach().float().numpy().copy()
            return hook

        handles = [m.register_forward_pre_hook(keep_raw(n))
                   for n, m in model.named_modules() if n.endswith("mlp.down_proj")]
        tap = ShadowTap(model, r"mlp\.down_proj$", None, self.N_SLOTS, self.TOP_N, seed=0)
        try:
            ids = torch.randint(3, 64, (3, 5))
            with torch.no_grad():
                model(ids)
            got = tap.collect(3)  # (3, L, TOP_N)
            assert got.shape == (3, len(tap.layer_names), self.TOP_N)
            for li, name in enumerate(tap.layer_names):
                module = model.get_submodule(name)
                for b in range(3):
                    imp = np.abs(raw[name][b]) * module.weight.detach().float().norm(dim=0).numpy()
                    assert len(np.unique(imp)) == imp.size, "test needs tie-free scores"
                    # Reference constructed WITHOUT the tap: pins the layer-seed
                    # convention itself, not just internal consistency.
                    expect = self._independent_slots(name, raw[name][b], module,
                                                     self.N_SLOTS, self.TOP_N)
                    have = got[b, li]
                    have = have[have >= 0]
                    np.testing.assert_array_equal(have, expect)
                    # padded region is exactly the -1 tail
                    assert (got[b, li, len(have):] == -1).all()
        finally:
            tap.close()
            for h in handles:
                h.remove()

    def test_deterministic_and_padding_correct(self):
        import torch  # noqa: F401

        from sideband.real.shadow_telemetry import ShadowTap, row_generator_seeds

        model = self._tiny_model()
        tap = ShadowTap(model, r"mlp\.down_proj$", None, self.N_SLOTS, self.TOP_N, seed=0)
        rows = [[5, 9, 11, 3], [7, 4, 22, 13, 8, 30], [12, 6, 19, 40, 2]]
        seeds = row_generator_seeds(0, 3)
        # Frozen constants of the registered spawn convention: a change to
        # numpy's SeedSequence or to the derivation silently re-seeds every
        # future harvest — this must be a loud failure, not a drift.
        np.testing.assert_array_equal(
            seeds, [8668861027912758289, 4881901421217228719, 7229315352737646090])
        try:
            r1 = self._run(model, tap, rows, seeds)
            r2 = self._run(model, tap, rows, seeds)
            for k in r1:
                np.testing.assert_array_equal(r1[k], r2[k])

            # Anchor 0 (prefill) must match unbatched, unpadded runs: the
            # left-padding + position-id arithmetic is what this pins.
            for b in range(3):
                single = self._run(model, tap, [rows[b]], seeds[b: b + 1])
                np.testing.assert_array_equal(r1["slots"][b, 0], single["slots"][0, 0])
                assert r1["argmax"][b, 0] == single["argmax"][0, 0]
                np.testing.assert_allclose(r1["mass16"][b, 0].astype(np.float32),
                                           single["mass16"][0, 0].astype(np.float32), atol=1e-3)
                np.testing.assert_allclose(r1["mass512"][b, 0].astype(np.float32),
                                           single["mass512"][0, 0].astype(np.float32), atol=1e-3)
                assert abs(r1["entropy"][b, 0] - single["entropy"][0, 0]) < 1e-3
                np.testing.assert_allclose(r1["hidden"][b, 0].astype(np.float32),
                                           single["hidden"][0, 0].astype(np.float32), atol=2e-2)
                # Same generator seed -> same sampled first token.
                assert r1["tokens"][b, 0] == single["tokens"][0, 0]
        finally:
            tap.close()

    def test_features_match_recomputed_forward(self):
        import torch

        from sideband.real.shadow_telemetry import ShadowTap, row_generator_seeds

        model = self._tiny_model()
        tap = ShadowTap(model, r"mlp\.down_proj$", None, self.N_SLOTS, self.TOP_N, seed=0)
        layer_names = list(tap.layer_names)
        rows = [[5, 9, 11, 3], [7, 4, 22, 13, 8, 30], [12, 6, 19, 40, 2]]
        _, _, b16, b512 = self._buckets()
        try:
            res = self._run(model, tap, rows, row_generator_seeds(0, 3))
        finally:
            tap.close()

        # Independent recompute of the prefill forward, with raw-capture
        # hooks so the ANCHOR-0 SLOTS are pinned to the same forward that
        # produced p_0 (a slots[:, a-1] misbinding must fail here).
        raw: dict[str, object] = {}

        def keep_raw(name):
            def hook(_m, inputs):
                raw[name] = inputs[0][:, -1, :].detach().float().numpy().copy()
            return hook

        handles = [m.register_forward_pre_hook(keep_raw(n))
                   for n, m in model.named_modules() if n.endswith("mlp.down_proj")]
        ids, mask = self._padded_batch(model, rows)
        pos = (mask.cumsum(-1) - 1).clamp(min=0)
        try:
            with torch.no_grad():
                logits = model(input_ids=ids, attention_mask=mask, position_ids=pos).logits[:, -1]
        finally:
            for h in handles:
                h.remove()
        p = torch.softmax(logits.float(), dim=-1).numpy()  # (3, 64)
        for b in range(3):
            for li, name in enumerate(layer_names):
                expect = self._independent_slots(name, raw[name][b], model.get_submodule(name),
                                                 self.N_SLOTS, self.TOP_N)
                have = res["slots"][b, 0, li]
                np.testing.assert_array_equal(have[have >= 0], expect)
            m16 = np.zeros(self.N16)
            np.add.at(m16, b16, p[b])
            np.testing.assert_allclose(res["mass16"][b, 0].astype(np.float32), m16, atol=1e-3)
            m512 = np.zeros(self.N512)
            np.add.at(m512, b512, p[b])
            np.testing.assert_allclose(res["mass512"][b, 0].astype(np.float32), m512, atol=1e-3)
            assert np.abs(res["mass16"][b, 0].astype(np.float32).sum() - 1) < 1e-2
            ent = -(p[b][p[b] > 0] * np.log(p[b][p[b] > 0])).sum()
            assert abs(res["entropy"][b, 0] - ent) < 1e-3
            assert res["argmax"][b, 0] == int(p[b].argmax())
            assert res["top_ids"][b, 0, 0] == res["argmax"][b, 0]
            tp = res["top_p"][b, 0].astype(np.float32)
            assert (np.diff(tp) <= 1e-6).all(), "top_p must be descending"
            # The stored hidden state is the vector that produced p_a.
            h = res["hidden"][b, 0].astype(np.float32)
            lg = h @ model.lm_head.weight.detach().numpy().T
            gap = np.sort(lg)[-1] - np.sort(lg)[-2]
            if gap > 0.05:
                assert int(lg.argmax()) == res["argmax"][b, 0]

    def test_anchor1_matches_teacher_forced(self):
        """Decode-step features (anchor 1) must equal an independent
        teacher-forced full forward over [prompt + x_0] — this pins the KV
        cache use, the mask append, and the position-id arithmetic (a
        dropped '-1' in pos_next, or telemetry bound to the wrong forward,
        must fail here)."""
        import torch

        from sideband.real.shadow_telemetry import ShadowTap, row_generator_seeds

        model = self._tiny_model()
        tap = ShadowTap(model, r"mlp\.down_proj$", None, self.N_SLOTS, self.TOP_N, seed=0)
        layer_names = list(tap.layer_names)
        rows = [[5, 9, 11, 3], [7, 4, 22, 13, 8, 30], [12, 6, 19, 40, 2]]
        _, _, b16, b512 = self._buckets()
        try:
            res = self._run(model, tap, rows, row_generator_seeds(0, 3), max_new=3)
        finally:
            tap.close()

        raw: dict[str, object] = {}
        norm_out: dict[str, object] = {}

        def keep_raw(name):
            def hook(_m, inputs):
                raw[name] = inputs[0][:, -1, :].detach().float().numpy().copy()
            return hook

        handles = [m.register_forward_pre_hook(keep_raw(n))
                   for n, m in model.named_modules() if n.endswith("mlp.down_proj")]
        handles.append(model.model.norm.register_forward_hook(
            lambda _m, _i, o: norm_out.__setitem__("h", o[:, -1, :].detach().float().numpy().copy())))
        try:
            for b in range(3):
                ids = torch.tensor([rows[b] + [int(res["tokens"][b, 0])]])
                with torch.no_grad():
                    logits = model(ids).logits[0, -1]  # unpadded, cache-free reference
                p = torch.softmax(logits.float(), dim=-1).numpy()
                m16 = np.zeros(self.N16)
                np.add.at(m16, b16, p)
                np.testing.assert_allclose(res["mass16"][b, 1].astype(np.float32), m16, atol=1e-3)
                m512 = np.zeros(self.N512)
                np.add.at(m512, b512, p)
                np.testing.assert_allclose(res["mass512"][b, 1].astype(np.float32), m512, atol=1e-3)
                ent = -(p[p > 0] * np.log(p[p > 0])).sum()
                assert abs(res["entropy"][b, 1] - ent) < 1e-3
                gap = np.sort(p)[-1] - np.sort(p)[-2]
                if gap > 1e-3:
                    assert res["argmax"][b, 1] == int(p.argmax())
                np.testing.assert_allclose(res["hidden"][b, 1].astype(np.float32),
                                           norm_out["h"][0], atol=2e-2)
                for li, name in enumerate(layer_names):
                    expect = self._independent_slots(name, raw[name][0], model.get_submodule(name),
                                                     self.N_SLOTS, self.TOP_N)
                    have = res["slots"][b, 1, li]
                    np.testing.assert_array_equal(have[have >= 0], expect)
        finally:
            for h in handles:
                h.remove()

    def test_position_id_arithmetic_spied(self):
        """The pos_next/prefill position arithmetic, pinned by a forward spy.

        Why a spy and not values: a +1 position shift changes tiny-model
        logits by only ~5e-4 (measured) — real, but under the f16-storage
        tolerance the value tests must allow, so an off-by-one mutant slips
        through them. The spy asserts the exact position ids handed to every
        forward (left-padded rows included); the teacher-forced value test
        above covers cache/mask/binding at value level."""
        from sideband.real.shadow_telemetry import ShadowTap, row_generator_seeds

        model = self._tiny_model()
        tap = ShadowTap(model, r"mlp\.down_proj$", None, self.N_SLOTS, self.TOP_N, seed=0)
        rows = [[5, 9, 11, 3], [7, 4, 22, 13, 8, 30], [12, 6, 19, 40, 2]]
        captured = []
        orig_forward = model.forward

        def spy(*a, **kw):
            assert kw.get("position_ids") is not None, "harvest must pass explicit position_ids"
            captured.append(kw["position_ids"].detach().clone())
            return orig_forward(*a, **kw)

        model.forward = spy
        try:
            self._run(model, tap, rows, row_generator_seeds(0, 3), max_new=3)
        finally:
            model.forward = orig_forward
            tap.close()

        w = max(len(r) for r in rows)
        assert len(captured) == 3  # prefill + 2 decode steps at max_new=3
        for b, r in enumerate(rows):
            n_pad = w - len(r)
            expect_prefill = [0] * n_pad + list(range(len(r)))
            assert captured[0][b].tolist() == expect_prefill
            for k in (1, 2):  # decode step k consumes x_{k-1}, sitting at len(r)+k-1
                assert captured[k][b].tolist() == [len(r) + k - 1]

    def test_eos_truncation_and_label_alignment(self):
        from sideband.harvest import label_index
        from sideband.real.shadow_telemetry import ShadowTap, row_generator_seeds

        model = self._tiny_model()
        tap = ShadowTap(model, r"mlp\.down_proj$", None, self.N_SLOTS, self.TOP_N, seed=0)
        rows = [[5, 9, 11, 3], [7, 4, 22, 13, 8, 30], [12, 6, 19, 40, 2]]
        seeds = row_generator_seeds(0, 3)
        try:
            free = self._run(model, tap, rows, seeds, max_new=8)
            # Pick an "EOS" that first occurs mid-row-0 (not at position 0);
            # trajectories are identical across the rerun (finished rows keep
            # sampling), so lengths must equal first-occurrence + 1 per row.
            eos_pos = next(i for i in range(1, free["tokens"].shape[1])
                           if free["tokens"][0, i] not in free["tokens"][0, :i])
            eos = int(free["tokens"][0, eos_pos])
            trunc = self._run(model, tap, rows, seeds, eos_set={eos}, max_new=8)
        finally:
            tap.close()

        for b in range(3):
            n = int(trunc["lengths"][b])
            np.testing.assert_array_equal(trunc["tokens"][b, :n], free["tokens"][b, :n])
            hits = np.nonzero(free["tokens"][b, : trunc["tokens"].shape[1]] == eos)[0]
            if hits.size and hits[0] < trunc["tokens"].shape[1]:
                assert n == int(hits[0]) + 1  # EOS included in length
                # The terminal anchor's offset-1 label is the EOS itself.
                assert trunc["tokens"][b, label_index(n - 1, 1)] == eos
            # Hygiene: nothing beyond the length is data — every array.
            assert (trunc["slots"][b, n:] == -1).all()
            assert (trunc["mass512"][b, n:] == 0).all()
            assert (trunc["mass16"][b, n:] == 0).all()
            assert (trunc["hidden"][b, n:] == 0).all()
            assert (trunc["tokens"][b, n:] == 0).all()
            assert (trunc["argmax"][b, n:] == 0).all()
            assert (trunc["entropy"][b, n:] == 0).all()
            assert (trunc["top_p"][b, n:] == 0).all()
        assert int(trunc["lengths"][0]) == eos_pos + 1
        assert bool(trunc["finished"][0])
        # n_rec invariants: the anchor axis must extend exactly to the longest
        # row, and with no EOS in play every row records exactly max_new
        # anchors — an n_rec off-by-one drops each batch's final anchor while
        # keeping lengths self-consistently wrong, so the absolute count is
        # the only reliable detector.
        assert trunc["tokens"].shape[1] == int(trunc["lengths"].max())
        assert free["tokens"].shape[1] == 8
        assert (free["lengths"] == 8).all()

    def test_collect_refuses_stale_state(self):
        import torch

        from sideband.real.shadow_telemetry import ShadowTap

        model = self._tiny_model()
        tap = ShadowTap(model, r"mlp\.down_proj$", None, self.N_SLOTS, self.TOP_N, seed=0)
        try:
            with torch.no_grad():
                model(torch.randint(3, 64, (2, 4)))
            tap.collect(2)
            with pytest.raises(RuntimeError):
                tap.collect(2)  # no forward since last collect
        finally:
            tap.close()


class TestVerifiedSeedFiles:
    """The single sanctioned harvest reader (S3 registration 2026-08-31):
    prefix-generic glob + mixed-prefix refusal + the sha binding."""

    @staticmethod
    def _write_pair(d: Path, prefix: str, seed: int) -> None:
        import hashlib

        npz_path = d / f"{prefix}_s{seed}.npz"
        np.savez(npz_path,
                 tokens=np.zeros((2, 3), np.int32),
                 lengths=np.array([3, 2], np.int32),
                 prompt_idx=np.arange(2, dtype=np.int32))
        meta = {"seed": seed, "npz_file": npz_path.name,
                "npz_sha256": hashlib.sha256(npz_path.read_bytes()).hexdigest()}
        (d / f"{prefix}_s{seed}.meta.json").write_text(json.dumps(meta))

    def test_shadow_prefix_loads(self, tmp_path):
        from sideband.harvest import verified_seed_files

        self._write_pair(tmp_path, "shadow", 0)
        self._write_pair(tmp_path, "shadow", 1)
        out = verified_seed_files(tmp_path)
        assert [m["seed"] for m, _ in out] == [0, 1]

    def test_moe_prefix_loads(self, tmp_path):
        from sideband.harvest import verified_seed_files

        self._write_pair(tmp_path, "moe", 0)
        out = verified_seed_files(tmp_path)
        assert [m["seed"] for m, _ in out] == [0]

    def test_mixed_prefixes_refused(self, tmp_path):
        from sideband.harvest import verified_seed_files

        self._write_pair(tmp_path, "shadow", 0)
        self._write_pair(tmp_path, "moe", 0)
        with pytest.raises(SystemExit, match="mixed harvest prefixes"):
            verified_seed_files(tmp_path)

    def test_sha_mismatch_refused(self, tmp_path):
        from sideband.harvest import verified_seed_files

        self._write_pair(tmp_path, "moe", 0)
        npz = tmp_path / "moe_s0.npz"
        npz.write_bytes(npz.read_bytes() + b"x")
        with pytest.raises(SystemExit, match="sha mismatch"):
            verified_seed_files(tmp_path)

    def test_summarize_mixed_prefix_refused(self, tmp_path):
        """summarize_harvest keeps its own glob (different error surface);
        its mixed-prefix guard must fire before any meta is trusted."""
        import summarize_harvest

        (tmp_path / "shadow_s0.meta.json").write_text("{}")
        (tmp_path / "moe_s0.meta.json").write_text("{}")
        with pytest.raises(SystemExit, match="mixed harvest prefixes"):
            summarize_harvest.summarize(tmp_path)


@pytest.mark.skipif(not _has("torch"), reason="needs [real] extras")
class TestRouterTap:  # pragma: no cover - runs where torch is installed
    """S3 tap core: the (B, T, H) -> (B*T, H) flatten contract, the
    softmax-topk selection against an independent numpy reference, sorted-id
    storage, and the refusal guards."""

    @staticmethod
    def _gate_holder(d_in=4, n_exp=6):
        import torch

        class Holder(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.mlp = torch.nn.ModuleDict(
                    {"gate": torch.nn.Linear(d_in, n_exp, bias=False)})

        torch.manual_seed(0)
        return Holder()

    @staticmethod
    def _np_reference(x_last: np.ndarray, W: np.ndarray, top_k: int) -> np.ndarray:
        """Independent selection: softmax over logits of the LAST position,
        top-k by value (ties to lower id via stable argsort), sorted ids."""
        logits = x_last @ W.T
        e = np.exp(logits - logits.max(axis=-1, keepdims=True))
        p = e / e.sum(axis=-1, keepdims=True)
        order = np.argsort(-p, axis=-1, kind="stable")[:, :top_k]
        return np.sort(order, axis=-1)

    def test_prefill_and_decode_shapes(self):
        import torch

        from sideband.real.moe_telemetry import RouterTap

        holder = self._gate_holder()
        tap = RouterTap(holder, r"mlp\.gate$", top_k=3)
        assert tap.layer_names == ["mlp.gate"]
        W = holder.mlp["gate"].weight.detach().numpy()

        rng = np.random.default_rng(1)
        B, T = 4, 5
        x = rng.normal(size=(B, T, 4)).astype(np.float32)
        with torch.no_grad():
            holder.mlp["gate"](torch.from_numpy(x.reshape(-1, 4)))  # Olmoe flatten
        got = tap.collect(B)
        assert got.shape == (B, 1, 3) and got.dtype == np.int16
        np.testing.assert_array_equal(got[:, 0], self._np_reference(x[:, -1], W, 3))

        x1 = rng.normal(size=(B, 1, 4)).astype(np.float32)  # decode step
        with torch.no_grad():
            holder.mlp["gate"](torch.from_numpy(x1.reshape(-1, 4)))
        got1 = tap.collect(B)
        np.testing.assert_array_equal(got1[:, 0], self._np_reference(x1[:, -1], W, 3))
        tap.close()

    def test_refusals(self):
        import torch

        from sideband.real.moe_telemetry import RouterTap

        holder = self._gate_holder()
        tap = RouterTap(holder, r"mlp\.gate$", top_k=3)
        with pytest.raises(RuntimeError, match="did not fire"):
            tap.collect(2)
        with torch.no_grad():
            holder.mlp["gate"](torch.zeros(6, 4))
        with pytest.raises(RuntimeError, match="not a multiple"):
            tap.collect(4)  # 6 captured positions, batch 4
        tap.close()
        with pytest.raises(ValueError, match="no modules matched"):
            RouterTap(holder, r"router\.nothing$", top_k=3)
        with pytest.raises(ValueError, match="experts <= top_k"):
            RouterTap(holder, r"mlp\.gate$", top_k=6)


class TestFidelityCalibrationConsistencyS3:
    """R1-S3 rider constants must match the committed calibration evidence
    under the PINNED derivation mapping (BLUEPRINT S3 tolerance amendment,
    2026-08-31): overlap strictly between the calibrated bands; mass and
    entropy at 3.0x their aligned maxima and below the misaligned medians;
    argmax gap >= 2x the aligned mass max (a kernel-noise flip inside the
    gap cannot fail the check)."""

    def test_rider_constants_match_committed_calibration(self):
        cp = REPO / "results" / "real" / "fidelity_calibration_olmoe.json"
        if not cp.exists():
            pytest.skip("no committed S3 calibration evidence")
        from sideband.real.fidelity_rider_moe import (ARGMAX_GAP, ENTROPY_ABS_MAX,
                                                      MASS_LINF_MAX, SLOT_OVERLAP_MIN)

        cal = json.loads(cp.read_text())
        aligned, mis = cal["aligned"], cal["misaligned_control"]
        assert None not in (SLOT_OVERLAP_MIN, MASS_LINF_MAX, ENTROPY_ABS_MAX, ARGMAX_GAP)
        assert mis["min_overlap"]["max"] < SLOT_OVERLAP_MIN < aligned["min_overlap"]["min"]
        assert MASS_LINF_MAX >= aligned["mass_linf"]["max"]
        assert MASS_LINF_MAX < mis["mass_linf"]["p50"]
        assert ENTROPY_ABS_MAX >= aligned["ent_abs"]["max"]
        assert ENTROPY_ABS_MAX < mis["ent_abs"]["p50"]
        assert ARGMAX_GAP >= 2 * aligned["mass_linf"]["max"]
        # the 3.0x mapping itself, within rounding of the pinned constants
        assert abs(MASS_LINF_MAX - 3.0 * aligned["mass_linf"]["max"]) < 0.01
        assert abs(ENTROPY_ABS_MAX - 3.0 * aligned["ent_abs"]["max"]) < 0.01
