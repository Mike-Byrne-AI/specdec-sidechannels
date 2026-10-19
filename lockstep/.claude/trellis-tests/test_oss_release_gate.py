from __future__ import annotations

from tools import trellis_oss_release_gate
from tools.trellis_oss_release_gate import StepResult


def test_release_gate_reports_source_failure(monkeypatch, repo_root):
    calls = []

    def fake_run_step(step, **_kwargs):
        calls.append(step.label)
        return StepResult(step.label, step.label != "source-refs", 1 if step.label == "source-refs" else 0, "")

    monkeypatch.setattr(trellis_oss_release_gate, "run_step", fake_run_step)
    results = trellis_oss_release_gate.run_release_gate(repo_root)
    assert [r.label for r in results][-1] == "source-refs"
    assert not results[-1].ok
    assert "installer-dry-run" not in calls


def test_release_gate_orchestrates_install_and_manifest(monkeypatch, repo_root):
    calls = []

    def fake_run_step(step, **_kwargs):
        calls.append(step.label)
        if step.label == "installer-dry-run":
            # Do not create the dry-run target; the gate asserts that it remains absent.
            pass
        if step.label == "fresh-install":
            step.command[-1] and None
        return StepResult(step.label, True, 0, "")

    def fake_verify_manifest(project_root):
        calls.append("installed-manifest")
        return StepResult("installed-manifest", True, 0, "")

    monkeypatch.setattr(trellis_oss_release_gate, "run_step", fake_run_step)
    monkeypatch.setattr(trellis_oss_release_gate, "verify_manifest", fake_verify_manifest)
    results = trellis_oss_release_gate.run_release_gate(repo_root)
    assert all(result.ok for result in results)
    assert "installer-dry-run" in calls
    assert "fresh-install" in calls
    assert "installed-bootstrap" in calls
    assert "installed-manifest" in calls
    assert "installed-repair-gate" in calls
    assert "source-pytest-module" not in calls


def test_release_gate_can_include_source_final_checks(monkeypatch, repo_root):
    calls = []

    def fake_run_step(step, **_kwargs):
        calls.append(step.label)
        return StepResult(step.label, True, 0, "")

    def fake_verify_manifest(project_root):
        calls.append("installed-manifest")
        return StepResult("installed-manifest", True, 0, "")

    monkeypatch.setattr(trellis_oss_release_gate, "run_step", fake_run_step)
    monkeypatch.setattr(trellis_oss_release_gate, "verify_manifest", fake_verify_manifest)
    results = trellis_oss_release_gate.run_release_gate(repo_root, include_source_tests=True)
    assert all(result.ok for result in results)
    assert calls[-3:] == ["source-pytest-module", "source-pytest-console", "source-repair-gate"]
