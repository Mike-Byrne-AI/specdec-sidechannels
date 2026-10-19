import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

from lint_findings import git_tracked_paths, lint_text, parse_entries, source_paths  # noqa: E402


def _has(mod: str) -> bool:
    import importlib.util

    return importlib.util.find_spec(mod) is not None


VALID = """# Findings

## F-1 — something measured
- date: 2026-08-28
- regime: synthetic concept-HMM v0 (C=4)
- source: tests/test_specdec.py
- finding: it works.

## F-2 — something else
- regime: synthetic concept-HMM v0
- source: hand analysis (no artifact)
- finding: also fine; free-text sources are allowed.
"""

MISSING_REGIME = """## F-3 — sloppy
- source: tests/test_specdec.py
- finding: number without a regime.
"""

BAD_PATH = """## F-4 — broken evidence
- regime: synthetic
- source: results/does_not_exist.json
- finding: cites a ghost file.
"""

# The cited state file is committed; withholding it from the tracked set models
# the git-ignored case (a registered run's state file before its .gitignore
# negation line lands) without writing anything under results/.
UNTRACKED_EVIDENCE = """## F-5 — evidence that never reached git
- regime: real
- source: results/real/prefetch_s3.json.state.jsonl
- finding: exists on disk; whether git tracks it is the question.
"""


class TestLintFindings:
    def test_valid_passes(self):
        assert lint_text(VALID, REPO) == []

    def test_parse_finds_all_entries(self):
        assert [e for e, _ in parse_entries(VALID)] == ["F-1", "F-2"]

    def test_missing_regime_fails(self):
        errors = lint_text(MISSING_REGIME, REPO)
        assert any("regime" in e for e in errors)

    def test_missing_evidence_path_fails(self):
        errors = lint_text(BAD_PATH, REPO)
        assert any("does not exist" in e for e in errors)

    # committed-evidence check (closed 2026-10-01; docs/SHARP_EDGES.md)
    def test_existing_but_untracked_path_fails(self):
        errors = lint_text(UNTRACKED_EVIDENCE, REPO, tracked={"FINDINGS.md"})
        assert any("not committed evidence" in e and "prefetch_s3.json.state.jsonl" in e
                   for e in errors)

    def test_git_default_accepts_the_committed_state_file(self):
        assert lint_text(UNTRACKED_EVIDENCE, REPO) == []

    def test_tracked_set_accepts_file_and_directory_tokens(self):
        text = "## F-6 — ok\n- regime: r\n- source: tests/test_specdec.py, results/real/harvest_moe\n"
        tracked = {"tests/test_specdec.py", "results/real/harvest_moe/moe_s0.meta.json"}
        assert lint_text(text, REPO, tracked=tracked) == []

    def test_missing_path_is_reported_as_missing_not_untracked(self):
        errors = lint_text(BAD_PATH, REPO, tracked=set())
        assert any("does not exist" in e for e in errors)
        assert not any("not committed evidence" in e for e in errors)

    def test_git_tracked_paths_lists_the_repo(self):
        tracked = git_tracked_paths(REPO)
        assert tracked is not None
        assert {"FINDINGS.md", "tools/lint_findings.py"} <= tracked

    def test_git_unavailable_falls_back_to_existence(self, monkeypatch):
        import lint_findings as lf

        def _no_git(*args, **kwargs):
            raise OSError("no git on PATH")

        monkeypatch.setattr(lf.subprocess, "run", _no_git)
        assert lf.git_tracked_paths(REPO) is None
        assert lf.lint_text(VALID, REPO) == []

    def test_dead_tools_path_fails(self):
        # tools/ and data/ joined the checked prefixes on 2026-10-01
        text = "## F-7 — t\n- regime: r\n- source: tools/run_nope.py, data/does_not_exist.jsonl\n"
        errors = lint_text(text, REPO, tracked=set())
        assert any("does not exist" in e and "tools/run_nope.py" in e for e in errors)
        assert any("does not exist" in e and "data/does_not_exist.jsonl" in e for e in errors)

    def test_separators_are_normalised_before_the_lookup(self):
        text = "## F-9 — t\n- regime: r\n- source: tests\\test_specdec.py, tests//test_stats.py\n"
        tracked = {"tests/test_specdec.py", "tests/test_stats.py"}
        assert lint_text(text, REPO, tracked=tracked) == []

    # the citation forms FINDINGS.md actually uses (resolved since 2026-10-01)
    def test_brace_shorthand_expands_to_each_file(self):
        text = "## F-10 — t\n- regime: r\n- source: results/real/prefetch_s3{,_r}.json\n"
        both = {"results/real/prefetch_s3.json", "results/real/prefetch_s3_r.json"}
        assert lint_text(text, REPO, tracked=both) == []
        assert lint_text(text, REPO, tracked={"results/real/prefetch_s3.json"}) != []

    def test_bare_name_resolves_against_the_last_prefixed_token_then_the_root(self):
        line = "results/real/prefetch_s3.json, prefetch_s3.json.state.jsonl, README.md"
        assert source_paths(line, REPO) == [
            "results/real/prefetch_s3.json", "results/real/prefetch_s3.json.state.jsonl", "README.md"]
        text = "## F-11 — t\n- regime: r\n- source: " + line + "\n"
        errors = lint_text(text, REPO, tracked={"results/real/prefetch_s3.json", "README.md"})
        assert any("prefetch_s3.json.state.jsonl" in e and "not committed evidence" in e for e in errors)

    def test_parenthesised_brace_token_is_resolved(self):
        # F-25 cites four state files this way; both named here are committed
        text = "## F-12 — t\n- regime: r\n- source: x (results/real/probes_s1{,_replication}.json.state.jsonl)\n"
        assert lint_text(text, REPO) == []

    def test_directory_tokens_with_and_without_trailing_slash(self):
        text = "## F-13 — t\n- regime: r\n- source: results/real/harvest_moe/, results/real/harvest_moe_r\n"
        tracked = {"results/real/harvest_moe/moe_s0.meta.json", "results/real/harvest_moe_r/moe_s8.meta.json"}
        assert lint_text(text, REPO, tracked=tracked) == []
        errors = lint_text(text, REPO, tracked={"results/real/harvest_moe/moe_s0.meta.json"})
        assert any("harvest_moe_r" in e and "not committed evidence" in e for e in errors)

    def test_missing_directory_is_reported_as_missing(self):
        text = "## F-14 — t\n- regime: r\n- source: results/real/no_such_dir/\n"
        assert any("does not exist" in e for e in lint_text(text, REPO, tracked=set()))

    def test_not_a_checkout_returns_none(self, tmp_path):
        assert git_tracked_paths(tmp_path) is None

    def test_ci_requires_git(self, monkeypatch):
        import lint_findings as lf

        monkeypatch.setenv("CI", "1")
        assert lf.git_required()
        monkeypatch.delenv("CI")
        assert not lf.git_required()

    def test_wrong_case_is_named_as_a_case_mismatch_or_missing(self):
        text = "## F-15 — t\n- regime: r\n- source: tests/Test_Specdec.py\n"
        errors = lint_text(text, REPO, tracked={"tests/test_specdec.py"})
        assert errors and ("case differs" in errors[0] or "does not exist" in errors[0])

    def test_backticks_quotes_and_markdown_links_are_resolved(self):
        line = "`tests/test_specdec.py`, \"tests/test_stats.py\", [the glue test](tests/test_glue.py)"
        assert source_paths(line, REPO) == ["tests/test_specdec.py", "tests/test_stats.py", "tests/test_glue.py"]

    def test_every_source_line_of_an_entry_is_read(self):
        text = "## F-16 — t\n- regime: r\n- source: tests/test_specdec.py\n- source: results/does_not_exist.json\n"
        assert any("does not exist" in e for e in lint_text(text, REPO, tracked=set()))

    def test_repo_findings_file_passes_lint(self):
        """The committed FINDINGS.md must itself satisfy the lint."""
        proc = subprocess.run(
            [sys.executable, str(REPO / "tools" / "lint_findings.py")],
            capture_output=True, text=True,
        )
        assert proc.returncode == 0, proc.stdout + proc.stderr


class TestSummarizeAudit:
    """summarize_audit is pure numpy — testable without torch."""

    @staticmethod
    def _rec(prompt_idx, offset, pb, eb, mass=0.5, glue_mass=None):
        from sideband.real.hf_specdec import AuditRecord

        return AuditRecord(prompt_idx=prompt_idx, position=0, offset=offset,
                           proposed=0, emitted=1, proposed_bucket=pb, emitted_bucket=eb,
                           cross_bucket_residual_mass=mass, residual_mass_glue=glue_mass)

    def test_fraction_and_ci_fields(self):
        from sideband.real.hf_specdec import summarize_audit

        # 3 prompts, 10 rejections, 7 cross-bucket.
        recs = (
            [self._rec(0, 1, 0, 1)] * 3 + [self._rec(0, 2, 0, 0)] * 1
            + [self._rec(1, 1, 2, 3)] * 2 + [self._rec(1, 1, 2, 2)] * 2
            + [self._rec(2, 3, 4, 5)] * 2
        )
        s = summarize_audit(recs)
        assert s["n_rejections"] == 10
        assert s["n_prompts_with_rejections"] == 3
        assert s["n_negative_bucket_records"] == 0
        assert s["cross_bucket_fraction"] == pytest.approx(0.7)
        lo, hi = s["cross_bucket_fraction_ci95_binomial"]
        assert lo <= 0.7 <= hi
        blo, bhi = s["cross_bucket_fraction_ci95_prompt_bootstrap"]
        assert 0.0 <= blo <= bhi <= 1.0
        assert s["cross_bucket_residual_mass"] == pytest.approx(0.5)
        mlo, mhi = s["cross_bucket_residual_mass_ci95_prompt_bootstrap"]
        assert mlo <= 0.5 <= mhi  # constant masses: CI still brackets the mean
        off1 = s["cross_bucket_fraction_by_offset"][1]
        assert off1["n"] == 7 and off1["fraction"] == pytest.approx(5 / 7)

    def test_negative_bucket_records_counted(self):
        from sideband.real.hf_specdec import summarize_audit

        s = summarize_audit([self._rec(0, 1, -1, 3), self._rec(1, 1, 2, -1),
                             self._rec(1, 2, -1, -1)])
        assert s["n_negative_bucket_records"] == 3
        # two -1s compare equal: counted same-bucket by the sampled estimator,
        # which is exactly why the field exists as a sanity check.
        assert s["cross_bucket_fraction"] == pytest.approx(2 / 3)

    def test_single_prompt_has_no_bootstrap(self):
        from sideband.real.hf_specdec import summarize_audit

        s = summarize_audit([self._rec(0, 1, 0, 1), self._rec(0, 2, 1, 1)])
        assert s["cross_bucket_fraction_ci95_prompt_bootstrap"] is None
        assert s["cross_bucket_fraction_ci95_binomial"] is not None

    def test_no_glue_arg_means_no_glue_section(self):
        from sideband.real.hf_specdec import summarize_audit

        assert "glue" not in summarize_audit([self._rec(0, 1, 0, 1)])

    def test_glue_section_fractions_and_mass_arithmetic(self):
        """Glue buckets {9}. Four records across 2 prompts:
        r1: concept 0 -> concept 1  (concept-cross; mass split 0.8 cross / 0.3 glue)
        r2: concept 0 -> glue 9     (not concept-cross)
        r3: glue 9    -> concept 2  (concept-cross; proposed in glue)
        r4: concept 3 -> concept 3  (same bucket, not cross at all)
        """
        from sideband.real.hf_specdec import summarize_audit

        recs = [
            self._rec(0, 1, 0, 1, mass=0.8, glue_mass=0.3),
            self._rec(0, 2, 0, 9, mass=0.9, glue_mass=0.6),
            self._rec(1, 1, 9, 2, mass=0.7, glue_mass=0.2),
            self._rec(1, 2, 3, 3, mass=0.4, glue_mass=0.1),
        ]
        g = summarize_audit(recs, glue_bucket_ids=[9])["glue"]
        assert g["n_glue_buckets"] == 1
        assert g["proposed_in_glue_fraction"] == pytest.approx(1 / 4)
        assert g["emitted_in_glue_fraction"] == pytest.approx(1 / 4)
        assert g["glue_involved_fraction"] == pytest.approx(2 / 4)
        assert g["concept_cross_fraction"] == pytest.approx(2 / 4)
        lo, hi = g["concept_cross_fraction_ci95_binomial"]
        assert lo <= 0.5 <= hi
        # mass derivation (AuditRecord docstring):
        # r1 proposed in concept: 0.8 - 0.3 = 0.5
        # r2 proposed in concept: 0.9 - 0.6 = 0.3
        # r3 proposed in glue:    1 - 0.2   = 0.8
        # r4 proposed in concept: 0.4 - 0.1 = 0.3
        assert g["residual_mass_concept_other"] == pytest.approx((0.5 + 0.3 + 0.8 + 0.3) / 4)
        assert g["n_records_with_glue_mass"] == 4

    def test_glue_mass_skips_records_without_field(self):
        from sideband.real.hf_specdec import summarize_audit

        recs = [self._rec(0, 1, 0, 1, mass=0.8, glue_mass=None),
                self._rec(1, 1, 0, 1, mass=0.6, glue_mass=0.1)]
        g = summarize_audit(recs, glue_bucket_ids=[9])["glue"]
        assert g["n_records_with_glue_mass"] == 1
        assert g["residual_mass_concept_other"] == pytest.approx(0.5)


class TestLoadBuckets:
    """load_buckets is pure json+numpy — testable without torch. The binding
    checks exist because a buckets file built on the DRAFT (same tokenizer,
    same vocab size) would otherwise load silently and poison K-1."""

    @staticmethod
    def _write(tmp_path, **fields):
        d = {"model": "org/target", "n_tokens": 8, "k": 2,
             "bucket_of_token": {str(i): i % 2 for i in range(8)}}
        d.update(fields)
        p = tmp_path / "buckets.json"
        p.write_text(json.dumps(d))
        return str(p)

    def test_matching_file_loads(self, tmp_path):
        from sideband.real.hf_specdec import load_buckets

        arr = load_buckets(self._write(tmp_path), 8, expect_model="org/target")
        assert arr.shape == (8,) and arr[3] == 1

    def test_wrong_model_refused(self, tmp_path):
        from sideband.real.hf_specdec import load_buckets

        with pytest.raises(SystemExit, match="built on"):
            load_buckets(self._write(tmp_path, model="org/draft"), 8, expect_model="org/target")

    def test_wrong_n_tokens_refused(self, tmp_path):
        from sideband.real.hf_specdec import load_buckets

        with pytest.raises(SystemExit, match="covers"):
            load_buckets(self._write(tmp_path, n_tokens=99), 8, expect_model="org/target")

    def test_override_flag_loads_anyway(self, tmp_path):
        from sideband.real.hf_specdec import load_buckets

        arr = load_buckets(self._write(tmp_path, model="org/draft"), 8,
                           expect_model="org/target", allow_mismatch=True)
        assert arr is not None

    def test_legacy_file_without_fields_tolerated(self, tmp_path):
        from sideband.real.hf_specdec import load_buckets

        p = tmp_path / "old.json"
        p.write_text(json.dumps({"bucket_of_token": {"0": 0, "1": 1}}))
        assert load_buckets(str(p), 4, expect_model="org/target") is not None

    def test_none_path_returns_none(self):
        from sideband.real.hf_specdec import load_buckets

        assert load_buckets(None, 8) is None


class TestRedactArgs:
    def test_credential_shaped_keys_dropped(self):
        from sideband.real.hf_specdec import redact_args

        out = redact_args({"target": "m", "hf_token": "SECRET", "api_key": "K",
                           "client_secret": "S", "token": "T", "seed": 0})
        assert out == {"target": "m", "seed": 0}

    def test_word_boundaries_not_substrings(self):
        from sideband.real.hf_specdec import redact_args

        out = redact_args({"tokenizer_revision": "abc", "tokens_per_call": 4})
        assert out == {"tokenizer_revision": "abc", "tokens_per_call": 4}

    def test_resume_identity_args_survive_redaction(self):
        """A key both identity-checked and redacted would make every resume
        compare None against a value — enforce the sets are disjoint."""
        from sideband.real.hf_specdec import RESUME_IDENTITY_ARGS, redact_args

        fake = {k: "v" for k in RESUME_IDENTITY_ARGS}
        assert set(redact_args(fake)) == set(RESUME_IDENTITY_ARGS)


class TestRepairPartialOutputs:
    """Torn-tail repair after a hard kill: keep records only for prompts with
    a completed stats line; drop torn lines; atomic rewrites."""

    def test_repair_drops_in_flight_and_torn(self, tmp_path):
        from sideband.real.hf_specdec import repair_partial_outputs

        out = tmp_path / "audit.jsonl"
        stats = tmp_path / "audit.stats.jsonl"
        rec = lambda i: json.dumps({"prompt_idx": i, "offset": 1, "proposed": 1, "emitted": 2})
        out.write_text("\n".join([rec(0), rec(0), rec(1), rec(2), '{"prompt_idx": 2, "trunc']) + "\n")
        stats.write_text("\n".join([
            json.dumps({"prompt_idx": 0, "acceptance_rate": 0.5}),
            json.dumps({"prompt_idx": 1, "acceptance_rate": 0.6}),
            '{"prompt_idx": 2, "acce',  # torn stats tail: prompt 2 incomplete
        ]) + "\n")
        completed, dropped = repair_partial_outputs(out, stats)
        assert completed == {0, 1}
        assert dropped == 2  # prompt-2 record + torn line
        kept = [json.loads(l) for l in out.read_text().splitlines()]
        assert [k["prompt_idx"] for k in kept] == [0, 0, 1]
        stats_kept = [json.loads(l) for l in stats.read_text().splitlines()]
        assert [s["prompt_idx"] for s in stats_kept] == [0, 1]

    def test_repair_of_clean_files_is_identity(self, tmp_path):
        from sideband.real.hf_specdec import repair_partial_outputs

        out = tmp_path / "audit.jsonl"
        stats = tmp_path / "audit.stats.jsonl"
        out.write_text(json.dumps({"prompt_idx": 0}) + "\n")
        stats.write_text(json.dumps({"prompt_idx": 0}) + "\n")
        completed, dropped = repair_partial_outputs(out, stats)
        assert completed == {0} and dropped == 0

    def test_missing_files_yield_empty(self, tmp_path):
        from sideband.real.hf_specdec import repair_partial_outputs

        completed, dropped = repair_partial_outputs(tmp_path / "a.jsonl", tmp_path / "s.jsonl")
        assert completed == set() and dropped == 0

    def test_gen_file_repaired_alongside(self, tmp_path):
        """--log-generated sidecar: keep one line per completed prompt, drop
        torn lines and in-flight debris."""
        from sideband.real.hf_specdec import repair_partial_outputs

        out = tmp_path / "audit.jsonl"
        stats = tmp_path / "audit.stats.jsonl"
        gen = tmp_path / "audit.gen.jsonl"
        out.write_text("")
        stats.write_text(json.dumps({"prompt_idx": 0, "acceptance_rate": 0.5}) + "\n")
        gen.write_text("\n".join([
            json.dumps({"prompt_idx": 0, "generated_ids": [1, 2]}),
            json.dumps({"prompt_idx": 1, "generated_ids": [3]}),  # in-flight
            '{"prompt_idx": 2, "gener',  # torn
        ]) + "\n")
        completed, _ = repair_partial_outputs(out, stats, gen_path=gen)
        assert completed == {0}
        kept = [json.loads(l) for l in gen.read_text().splitlines()]
        assert [k["prompt_idx"] for k in kept] == [0]

    def test_records_expected_demotes_count_mismatch(self, tmp_path):
        """With buckets on, a 'completed' prompt whose record count disagrees
        with n_proposed - n_accepted lost records to a torn write: it must be
        demoted to incomplete (records dropped, prompt re-runs)."""
        from sideband.real.hf_specdec import repair_partial_outputs

        out = tmp_path / "audit.jsonl"
        stats = tmp_path / "audit.stats.jsonl"
        rec = lambda i: json.dumps({"prompt_idx": i})
        # prompt 0: expects 2 rejections, has 2 -> kept.
        # prompt 1: expects 2, has 1 (one record lost) -> demoted.
        out.write_text("\n".join([rec(0), rec(0), rec(1)]) + "\n")
        stats.write_text("\n".join([
            json.dumps({"prompt_idx": 0, "n_proposed": 10, "n_accepted": 8}),
            json.dumps({"prompt_idx": 1, "n_proposed": 10, "n_accepted": 8}),
        ]) + "\n")
        completed, dropped = repair_partial_outputs(out, stats, records_expected=True)
        assert completed == {0}
        assert dropped == 1
        assert [json.loads(l)["prompt_idx"] for l in out.read_text().splitlines()] == [0, 0]
        assert [json.loads(l)["prompt_idx"] for l in stats.read_text().splitlines()] == [0]


class TestRealSubpackage:
    def test_import_guard_message_without_deps(self):
        from sideband.real import require_real_deps

        try:
            import torch  # noqa: F401

            pytest.skip("torch installed; guard path not exercised here")
        except ImportError:
            with pytest.raises(ImportError, match=r"\[real\]"):
                require_real_deps()

    def test_real_modules_import_lazily(self):
        """Importing the modules must not require torch (lazy imports)."""
        import sideband.real.bucketize_vocab  # noqa: F401
        import sideband.real.hf_specdec  # noqa: F401
        import sideband.real.moe_telemetry  # noqa: F401
        import sideband.real.shadow_telemetry  # noqa: F401

    @pytest.mark.skipif("torch" not in sys.modules and not _has("torch"), reason="needs [real] extras")
    def test_with_torch_smoke(self):  # pragma: no cover - GPU box only
        from sideband.real import require_real_deps

        torch, transformers = require_real_deps()
        assert torch and transformers


@pytest.mark.skipif(not _has("torch") or not _has("transformers"), reason="needs [real] extras")
class TestKVCachePath:  # pragma: no cover - runs where torch is installed (GPU box), skips in CI
    """The cached path must reproduce the exact-recompute reference on a tiny
    fp32 CPU model, where kernel numerics are shape-stable — this pins the
    delta-feeding and crop arithmetic (off-by-ones would show instantly)."""

    @staticmethod
    def _tiny_pair():
        import torch
        from transformers import LlamaConfig, LlamaForCausalLM

        cfg = LlamaConfig(vocab_size=64, hidden_size=32, intermediate_size=64,
                          num_hidden_layers=2, num_attention_heads=4,
                          num_key_value_heads=2, max_position_embeddings=256,
                          attn_implementation="eager")
        torch.manual_seed(0)
        target = LlamaForCausalLM(cfg).eval()
        torch.manual_seed(1)
        draft = LlamaForCausalLM(cfg).eval()
        ids = torch.randint(3, 64, (1, 5))
        return target, draft, ids

    @staticmethod
    def _assert_stats_close(a, b):
        """Int fields (counts, gate stats) must match exactly; the analytic
        float sums inherit the same fp32-reduction-order jitter as the
        residual-mass field (~1e-8 between cache paths) and get a tolerance."""
        float_keys = {"acceptance_rate", "analytic_acc_drafted_sum",
                      "analytic_acceptance_drafted", "analytic_acc_verified_sum"}
        assert set(a) == set(b)
        for k in a:
            if k == "analytic_acc_drafted_by_offset":
                assert set(a[k]) == set(b[k])
                for j in a[k]:
                    assert a[k][j][1] == b[k][j][1], f"offset {j} n"
                    assert a[k][j][0] == pytest.approx(b[k][j][0], abs=1e-6)
            elif k in float_keys:
                assert a[k] == pytest.approx(b[k], abs=1e-6), k
            else:
                assert a[k] == b[k], k

    @staticmethod
    def _assert_mixed_acceptance(st, gamma):
        """The equivalence claim is only tested if the trajectory hits the
        cases where the crop actually truncates. Low temperature on two
        random-init models produces mixed outcomes; at temperature 1.0 both
        models are near-uniform and EVERYTHING accepts, making every crop a
        no-op (caught by critic mutation-testing: an off-by-one crop mutant
        survived the old tests)."""
        assert 0 < st["n_accepted"] < st["n_proposed"], "need both accepts and rejects"
        # full-accept (bonus) blocks: each non-full block contributes exactly
        # one more proposal than acceptance; full blocks contribute gamma each.
        n_full = st["n_blocks"] - (st["n_proposed"] - st["n_accepted"])
        assert n_full >= 1, "need at least one full-accept (bonus) block"

    def test_cached_matches_reference_unsteered(self):
        import torch

        from sideband.dists import rng
        from sideband.real.hf_specdec import spec_decode_prompt

        target, draft, ids = self._tiny_pair()
        kw = dict(gamma=4, max_new=40, temperature=0.2)
        ids_a, rec_a, st_a = spec_decode_prompt(target, draft, ids, gen=rng(3),
                                                use_kv_cache=True, **kw)
        ids_b, rec_b, st_b = spec_decode_prompt(target, draft, ids, gen=rng(3),
                                                use_kv_cache=False, **kw)
        assert torch.equal(ids_a, ids_b)
        self._assert_stats_close(st_a, st_b)
        self._assert_mixed_acceptance(st_a, gamma=4)
        # unsteered: analytic estimands populated, gate counters untouched
        assert st_a["analytic_acc_drafted_n"] == st_a["n_blocks"] * 4
        assert st_a["analytic_acc_verified_n"] == st_a["n_proposed"]
        assert 0.0 < st_a["analytic_acceptance_drafted"] <= 1.0
        assert st_a["n_steerable"] == 0 and st_a["n_gate_open"] == 0

    def test_cached_matches_reference_steered_with_buckets(self):
        import numpy as np
        import torch

        from sideband.dists import rng
        from sideband.real.hf_specdec import spec_decode_prompt

        target, draft, ids = self._tiny_pair()
        buckets = np.arange(64) % 4
        kw = dict(gamma=4, max_new=40, temperature=0.2, bucket_of_token=buckets,
                  steer_beta=1.5, steer_source="free_lastp",
                  steer_gate="disagree", steer_mech="posterior")
        ids_a, rec_a, st_a = spec_decode_prompt(target, draft, ids, gen=rng(3),
                                                use_kv_cache=True, **kw)
        ids_b, rec_b, st_b = spec_decode_prompt(target, draft, ids, gen=rng(3),
                                                use_kv_cache=False, **kw)
        assert torch.equal(ids_a, ids_b)
        self._assert_stats_close(st_a, st_b)
        self._assert_mixed_acceptance(st_a, gamma=4)
        assert st_a["n_steerable"] > 0 and st_a["n_gate_open"] > 0
        # the audit-record path must be non-vacuously identical, and the
        # trajectory must contain BOTH an offset-1 rejection (a block with
        # n_acc == 0) and a deeper one (0 < n_acc < gamma).
        assert len(rec_a) > 0
        assert any(r.offset == 1 for r in rec_a)
        assert any(r.offset > 1 for r in rec_a)
        self._assert_records_close(rec_a, rec_b)

    @staticmethod
    def _assert_records_close(rec_a, rec_b):
        """Discrete fields must match EXACTLY; the residual-mass floats differ
        at fp32-reduction-order level between the two paths (measured ~4e-8
        here) — that jitter is inherent to shape-dependent kernels, not an
        indexing bug, so they get a tolerance instead of equality."""
        assert len(rec_a) == len(rec_b)
        for a, b in zip(rec_a, rec_b):
            da, db = dict(a.__dict__), dict(b.__dict__)
            for key in ("cross_bucket_residual_mass", "residual_mass_glue"):
                ma, mb = da.pop(key), db.pop(key)
                if ma is None or mb is None:
                    assert ma is None and mb is None
                else:
                    assert ma == pytest.approx(mb, abs=1e-6)
            assert da == db

    def test_cached_matches_reference_sharp_variant_with_glue(self, monkeypatch):
        """The Phase 0b production configuration: concept-space steering with
        a glue exclusion (OQ-4/D-7) and the D-11 sharpened free variant. Pins
        the glue-aware record fields and the concept-gate path on both cache
        paths, and SPIES on the steering call site: the array handed to
        apply_concept_steering must be the compact concept map (not the raw
        buckets — the critic's M3 mutation) and the posterior must be one-hot
        (sharp actually selected — the M1 mutation)."""
        import numpy as np
        import torch  # noqa: F401  (availability probe: the spied call site runs on torch tensors)

        import sideband.real.hf_specdec as hs
        from sideband.dists import rng
        from sideband.glue import glue_remap
        from sideband.real.hf_specdec import spec_decode_prompt
        from sideband.steering import apply_concept_steering as real_apply

        target, draft, ids = self._tiny_pair()
        buckets = np.arange(64) % 4
        steer_map, glue_mask, C = glue_remap(buckets, [0])  # bucket 0 = glue
        assert C == 3 and glue_mask.sum() == 16

        captured = []

        def spy(q, sbot, C_arg, post, beta, gate="disagree", mech="posterior"):
            captured.append((sbot, C_arg, post))
            return real_apply(q, sbot, C_arg, post, beta, gate=gate, mech=mech)

        monkeypatch.setattr(hs, "apply_concept_steering", spy)

        from sideband.glue import rejection_masses as real_masses

        mask_args = []

        def mass_spy(p, q, bot, proposed, gm=None):
            mask_args.append(gm)
            return real_masses(p, q, bot, proposed, gm)

        monkeypatch.setattr(hs, "rejection_masses", mass_spy)

        kw = dict(gamma=4, max_new=40, temperature=0.2, bucket_of_token=buckets,
                  steer_beta=1.5, steer_source="free_lastp_sharp",
                  steer_gate="disagree", steer_mech="posterior",
                  steer_bucket_of_token=steer_map, glue_mask=glue_mask)
        # rng(0), not rng(3): this steered trajectory needs a full-accept
        # block for the draft-cache 2-token-delta path, which the rng(3)
        # trajectory never produces under the sharp variant.
        ids_a, rec_a, st_a = spec_decode_prompt(target, draft, ids, gen=rng(0),
                                                use_kv_cache=True, **kw)
        ids_b, rec_b, st_b = spec_decode_prompt(target, draft, ids, gen=rng(0),
                                                use_kv_cache=False, **kw)
        # the test's name: the cached path reproduces the uncached reference. These asserts were
        # dropped at 910522b / 7d46466 (2026-08-30) and restored on 2026-10-16 (lane C of the
        # 2026-10-15 image audit, item S6b-C-2); without them the two trajectories were computed
        # and never compared.
        assert torch.equal(ids_a, ids_b)
        self._assert_stats_close(st_a, st_b)
        self._assert_mixed_acceptance(st_a, gamma=4)
        assert st_a["n_steerable"] > 0 and st_a["n_gate_open"] > 0
        assert len(rec_a) > 0
        self._assert_records_close(rec_a, rec_b)
        for r in rec_a:   # the glue decomposition yields a valid concept-other mass (dropped at 7d46466)
            assert r.residual_mass_glue is not None
            assert -1e-9 <= r.residual_mass_glue <= 1.0 + 1e-9
            if r.proposed_bucket == 0:  # proposed in glue
                concept_other = 1.0 - r.residual_mass_glue
            else:
                concept_other = r.cross_bucket_residual_mass - r.residual_mass_glue
            assert -1e-6 <= concept_other <= 1.0 + 1e-6
        assert captured
        for sbot, C_arg, post in captured:
            assert sbot is steer_map, "steering must receive the COMPACT concept map"
            assert C_arg == C
            assert post.shape == (C,) and post.max() == 1.0 and post.sum() == 1.0, \
                "free_lastp_sharp must hand a one-hot posterior to the mechanism"
        assert mask_args and all(g is glue_mask for g in mask_args), \
            "record decomposition must receive the glue mask itself (not a rebuild)"

    def test_oracle_mode_beta0_matches_standard(self):
        """The oracle path's only mechanical difference is per-step target
        feeding; at beta=0 (steering no-op) its trajectories must reproduce
        the standard batched-forward path exactly — the implementation gate
        the BLUEPRINT attribution rider requires before any oracle run."""
        import numpy as np
        import torch

        from sideband.dists import rng
        from sideband.glue import glue_remap
        from sideband.real.hf_specdec import spec_decode_prompt

        target, draft, ids = self._tiny_pair()
        buckets = np.arange(64) % 4
        steer_map, glue_mask, C = glue_remap(buckets, [0])
        kw = dict(gamma=4, max_new=40, temperature=0.2, bucket_of_token=buckets,
                  steer_beta=0.0, steer_gate="disagree", steer_mech="posterior",
                  steer_bucket_of_token=steer_map, glue_mask=glue_mask)
        for seed in (0, 1, 2):
            for cache in (True, False):
                a, ra, sa = spec_decode_prompt(target, draft, ids, gen=rng(seed),
                                               steer_source="oracle_nextp",
                                               use_kv_cache=cache, **kw)
                b, rb, sb = spec_decode_prompt(target, draft, ids, gen=rng(seed),
                                               steer_source="free_lastp",
                                               use_kv_cache=cache, **kw)
                assert torch.equal(a, b), f"seed={seed} cache={cache}"
                self._assert_stats_close(sa, sb)
                self._assert_records_close(ra, rb)
                assert sa["n_steerable"] == 0 and sa["n_gate_open"] == 0

    def test_cached_matches_reference_oracle(self, monkeypatch):
        """The attribution rider's arm: oracle_nextp cached vs uncached must
        agree, with full crop-path coverage, and the SPY must see FRESH
        per-position posteriors (a block-held mutant would repeat the same
        posterior across a block's positions)."""
        import numpy as np
        import torch

        import sideband.real.hf_specdec as hs
        from sideband.dists import rng
        from sideband.glue import glue_remap
        from sideband.real.hf_specdec import spec_decode_prompt
        from sideband.steering import apply_concept_steering as real_apply

        target, draft, ids = self._tiny_pair()
        buckets = np.arange(64) % 4
        steer_map, glue_mask, C = glue_remap(buckets, [0])

        posts = []

        def spy(q, sbot, C_arg, post, beta, gate="disagree", mech="posterior"):
            posts.append(tuple(np.round(post, 12)))
            return real_apply(q, sbot, C_arg, post, beta, gate=gate, mech=mech)

        monkeypatch.setattr(hs, "apply_concept_steering", spy)

        # Identity pinning (kills the stale-oracle mutant: steering with
        # p_{j-1} while verifying with p_j): every distribution the verifier
        # consumes must be the SAME OBJECT some steering posterior was
        # computed from. References are retained, so ids cannot be reused.
        from sideband.real.hf_specdec import spec_step as real_spec_step
        from sideband.steering import concept_posterior as real_cp

        cp_inputs, verify_ps = [], []

        def cp_spy(p, sbot, C_arg, sharp=False):
            cp_inputs.append(p)
            return real_cp(p, sbot, C_arg, sharp=sharp)

        def ss_spy(gen, p, q, proposed=None):
            verify_ps.append(p)
            return real_spec_step(gen, p, q, proposed=proposed)

        monkeypatch.setattr(hs, "concept_posterior", cp_spy)
        monkeypatch.setattr(hs, "spec_step", ss_spy)

        kw = dict(gamma=4, max_new=40, temperature=0.2, bucket_of_token=buckets,
                  steer_beta=3.0, steer_source="oracle_nextp",
                  steer_gate="disagree", steer_mech="posterior",
                  steer_bucket_of_token=steer_map, glue_mask=glue_mask)
        ids_a, rec_a, st_a = spec_decode_prompt(target, draft, ids, gen=rng(1),
                                                use_kv_cache=True, **kw)
        ids_b, rec_b, st_b = spec_decode_prompt(target, draft, ids, gen=rng(1),
                                                use_kv_cache=False, **kw)
        assert torch.equal(ids_a, ids_b)
        self._assert_stats_close(st_a, st_b)
        self._assert_mixed_acceptance(st_a, gamma=4)
        assert st_a["n_steerable"] > 0 and st_a["n_gate_open"] > 0
        assert len(rec_a) > 0
        assert any(r.offset == 1 for r in rec_a)
        assert any(r.offset > 1 for r in rec_a)
        self._assert_records_close(rec_a, rec_b)
        # fresh per-position posteriors: many distinct values, all valid
        assert len(set(posts)) > len(posts) // 4, "posteriors look block-held"
        for p in posts:
            assert len(p) == C and abs(sum(p) - 1.0) < 1e-9
        # identity pinning: each verified p must be an object some steering
        # posterior consumed (a shifted/stale oracle breaks this at every
        # full-accept block, whose last position's p was never steered from).
        assert verify_ps and cp_inputs
        for vp in verify_ps:
            assert any(vp is ci for ci in cp_inputs), \
                "a verified p was never a steering-posterior input (stale oracle?)"
        # glue mass populated, bounded, and consistent with the derivation
        # documented on AuditRecord (concept-other mass must be a valid mass).
        for r in rec_a:
            assert r.residual_mass_glue is not None
            assert -1e-9 <= r.residual_mass_glue <= 1.0 + 1e-9


@pytest.mark.skipif(not _has("torch") or not _has("transformers"), reason="needs [real] extras")
class TestK3SpecDecode:  # pragma: no cover - runs where torch is installed, skips in CI
    """K-3 stage-E integration on the tiny fp32 pair (E11's promised CPU
    coverage; critic blocker 2026-09-02): the k3 execution path with the
    scheduler inert must reproduce the legacy trajectory, forced
    stop/extend policies must produce the registered block shapes and E6
    arithmetic, and the recorder's anchor bookkeeping must satisfy the
    structural position invariants (which also document the E12 prefill
    offset skew)."""

    @staticmethod
    def _tiny_pair():
        return TestKVCachePath._tiny_pair()

    @staticmethod
    def _k3(policy_kind="fixed", thresholds=None, reader=None, recorder=None,
            gamma_base=4, gamma_max=None):
        from sideband.real.k3_live import K3Config
        from sideband.scheduler import SchedulerPolicy

        if gamma_max is None:
            gamma_max = gamma_base if policy_kind == "fixed" else 6
        pol = SchedulerPolicy(policy_kind, gamma_base=gamma_base,
                              gamma_max=gamma_max, thresholds=thresholds)
        return K3Config(policy=pol, reader=reader, recorder=recorder)

    def _k3_stats_invariants(self, st):
        assert st["n_emitted"] == st["n_accepted"] + st["n_blocks"]
        assert st["tokens_per_call"] == pytest.approx(
            st["n_emitted"] / st["n_blocks"])
        assert st["drafted_per_emitted"] == pytest.approx(
            st["n_drafted"] / st["n_emitted"])

    def test_k3_off_config_matches_legacy(self):
        import torch

        from sideband.dists import rng
        from sideband.real.hf_specdec import spec_decode_prompt

        target, draft, ids = self._tiny_pair()
        kw = dict(gamma=4, max_new=40, temperature=0.2)
        ids_a, _, st_a = spec_decode_prompt(target, draft, ids, gen=rng(3),
                                            use_kv_cache=True, **kw)
        ids_b, _, st_b = spec_decode_prompt(target, draft, ids, gen=rng(3),
                                            use_kv_cache=True, k3=self._k3(),
                                            **kw)
        # Same trajectory: the prefill + crop-one changes forward SHAPES
        # but not exact-arithmetic content; the tiny fp32 CPU pair is
        # shape-stable (same property the cached-vs-reference test rests
        # on), so tokens must match exactly and legacy stats must agree.
        assert torch.equal(ids_a, ids_b)
        TestKVCachePath._assert_stats_close(st_a, {k: st_b[k] for k in st_a})
        TestKVCachePath._assert_mixed_acceptance(st_b, gamma=4)
        # scheduler inert: k3 extras present with fixed-arm values
        assert st_b["n_stop_blocks"] == 0 and st_b["n_extend_blocks"] == 0
        assert st_b["n_drafted"] == 4 * st_b["n_blocks"]
        self._k3_stats_invariants(st_b)

    def test_k3_forced_stop_skips_block_one(self):
        from sideband.dists import rng
        from sideband.real.hf_specdec import spec_decode_prompt
        from sideband.scheduler import Thresholds

        target, draft, ids = self._tiny_pair()
        # stop threshold above any probability: every CONSULTING block
        # stops at drafted position 1; block 1 never consults (E12).
        thr = Thresholds(kind="draft_conf", stop_level=0.5, extend_level=0.5,
                         stop=(1.1, 1.1), extend=2.0)
        _, _, st = spec_decode_prompt(
            target, draft, ids, gamma=4, max_new=30, temperature=0.2,
            gen=rng(3), use_kv_cache=True,
            k3=self._k3("draft_conf", thresholds=thr))
        assert st["n_blocks"] >= 2
        assert st["n_stop_blocks"] == st["n_blocks"] - 1  # E12 exclusion
        assert st["n_extend_blocks"] == 0
        assert st["n_drafted"] == 4 + (st["n_blocks"] - 1) * 1
        self._k3_stats_invariants(st)
        # analytic-by-offset ns reflect the truncation: offset 1 counted
        # in every block, offsets 2-4 only in block 1.
        by_off = st["analytic_acc_drafted_by_offset"]
        assert by_off["1"][1] == st["n_blocks"]
        for off in ("2", "3", "4"):
            assert by_off[off][1] == 1

    def test_k3_forced_extend_skips_block_one(self):
        from sideband.dists import rng
        from sideband.real.hf_specdec import spec_decode_prompt
        from sideband.scheduler import Thresholds

        target, draft, ids = self._tiny_pair()
        # stop never fires (threshold below any probability); extend
        # always fires (min signal >= -1): consulting blocks draft 6.
        thr = Thresholds(kind="draft_conf", stop_level=0.5, extend_level=0.5,
                         stop=(-1.0, -1.0), extend=-1.0)
        _, _, st = spec_decode_prompt(
            target, draft, ids, gamma=4, max_new=30, temperature=0.2,
            gen=rng(3), use_kv_cache=True,
            k3=self._k3("draft_conf", thresholds=thr, gamma_max=6))
        assert st["n_blocks"] >= 2
        assert st["n_extend_blocks"] == st["n_blocks"] - 1  # E12 exclusion
        assert st["n_stop_blocks"] == 0
        assert st["n_drafted"] == 4 + (st["n_blocks"] - 1) * 6
        self._k3_stats_invariants(st)
        by_off = st["analytic_acc_drafted_by_offset"]
        assert by_off["5"][1] == st["n_blocks"] - 1
        assert by_off["6"][1] == st["n_blocks"] - 1

    def _reader_and_recorder(self, target):
        import numpy as np

        from sideband.real.k3_live import (ByproductRecorder, LiveNormCatch,
                                           LiveReader, LiveShadowTap)
        from sideband.scheduler import LinearProbe

        maps = {name: (np.arange(64) % n).astype(np.int64)
                for name, n in (("16", 4), ("32", 5), ("64", 6), ("512", 7))}
        label_map = (np.arange(64) % 5).astype(np.int64)  # glue class 4
        d_a = 4 + 5 + 6 + 7 + 1 + 32
        d_c = d_a + 2 * 8  # two down_proj layers, n_slots 8
        probes = {}
        for arm, d in (("a", d_a), ("c", d_c)):
            for off in (2, 3):
                probes[(arm, off)] = LinearProbe(
                    np.zeros((5, d), np.float32), np.zeros(5, np.float32))
        tap = LiveShadowTap(target, r"mlp\.down_proj$", None, n_slots=8,
                            top_n=4, seed=0)
        nc = LiveNormCatch(target.model.norm)
        reader = LiveReader(tap, nc, maps, label_map, 5, probes, n_slots=8)
        return reader, ByproductRecorder(6)

    def test_k3_recorder_anchor_invariants(self):
        import numpy as np

        from sideband.dists import rng
        from sideband.real.hf_specdec import spec_decode_prompt

        target, draft, ids = self._tiny_pair()
        reader, recorder = self._reader_and_recorder(target)
        try:
            _, _, st = spec_decode_prompt(
                target, draft, ids, gamma=4, max_new=30, temperature=0.2,
                gen=rng(3), use_kv_cache=True,
                k3=self._k3(reader=reader, recorder=recorder))
        finally:
            reader.close()
        out = recorder.finalize()
        n = int(out["n_blocks"])
        assert n == st["n_blocks"]
        TestKVCachePath._assert_mixed_acceptance(st, gamma=4)
        pos = out["anchor_pos"].astype(int)
        acc = out["accepted"].astype(int)
        # Row 0 consults the PREFILL anchor: the prompt's last token.
        assert pos[0] == ids.shape[1] - 1
        # Structural position invariants (critic 2026-09-02; documents the
        # E12 offset skew): the prefill->block-1 gap lacks the +1 every
        # mid-run gap carries — which is WHY block 1 never consults.
        assert pos[1] - pos[0] == acc[0]
        for r in range(2, n):
            assert pos[r] - pos[r - 1] == acc[r - 1] + 1
        # Recorder wiring: both signal families logged; all-zero probes
        # give argmax 0 with confidence 1/5 (stored float32 per E8).
        assert not np.isnan(out["q_sig"][:, 0]).any()
        np.testing.assert_array_equal(out["probe_pred_a"], 0)
        np.testing.assert_allclose(out["probe_conf_c"].astype(np.float64),
                                   0.2, atol=1e-7)
        # STOP/EXTEND mutual exclusion holds row-wise (vacuous for fixed,
        # structural for all policies).
        assert not ((out["stop_pos"] > 0) & (out["extend"] == 1)).any()
        # accepted-flag semantics (E8): 1 for accepted, 0 at the rejected
        # position, -1 for unreached-and-padding.
        for r in range(n):
            g = int(out["gamma_used"][r])
            flags = out["acc_flags"][r]
            k = acc[r]
            assert (flags[:k] == 1).all()
            if k < g:
                assert flags[k] == 0
                assert (flags[k + 1:] == -1).all()
            else:
                assert (flags[:g] == 1).all() and (flags[g:] == -1).all()


def test_every_meta_args_writer_redacts():
    """Every tool/adapter that stores vars(args) in a committed meta must
    route it through sideband.provenance.redact_args (release audit)."""
    import re
    root = Path(__file__).resolve().parents[1]
    offenders = []
    files = list((root / "tools").glob("*.py")) +         list((root / "src" / "sideband" / "real").glob("*.py"))
    for f in files:
        for line in f.read_text(encoding="utf-8").splitlines():
            if re.search(r"vars\(args\)", line) and "redact_args(" not in line                     and "parse_args" not in line and "main(**" not in line:
                offenders.append(f"{f.name}: {line.strip()}")
    assert not offenders, offenders
