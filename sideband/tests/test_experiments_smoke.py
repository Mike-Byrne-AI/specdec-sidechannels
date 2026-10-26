"""tests/test_experiments_smoke.py: a `--smoke` run never writes over committed evidence
(written 2026-10-16, lane C of the 2026-10-15 image audit, item S8-C-7; no torch).

The audit reproduced, in a clone, that `python experiments/e04_staleness_decay.py --smoke` wrote its
smoke-sized payload over the committed results/e04_staleness_decay.json: only run_all.py redirected
the results directory under --smoke. The root fix is experiments/_util.py's smoke_results(), called
first by every script's main(smoke=True) (so a programmatic call is covered, not only the command
line) and by run_all.py; e06's partial files live in the same directory. Three checks: every
script's main() opens with the redirect and the runner calls it (read from the source text); the
helper is idempotent; one script run with --smoke from a copy of experiments/ in a temporary
directory writes results/smoke/<name>.json there, nothing at results/<name>.json, and writes LF
bytes (save_json passes newline="\\n" since the same lane; the bytes no longer depend on the
writing box, and the two committed payloads stored CRLF today, e01 and e07, flip when next
regenerated).
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXP = ROOT / "experiments"
SCRIPTS = sorted(EXP.glob("e0*.py"))
# main(smoke: bool = False, ...) -> dict:, an optional docstring, then the redirect as the first statement
MAIN_OPENS_WITH_REDIRECT = re.compile(
    r'^def main\(smoke: bool = False[^\n]*\n(?:\s+"""(?:.|\n)*?"""\n)?\s+if smoke:\n\s+smoke_results\(\)', re.M)


def test_every_script_and_the_runner_route_smoke_through_the_helper():
    assert len(SCRIPTS) == 7, [s.name for s in SCRIPTS]
    for s in SCRIPTS:
        text = s.read_text(encoding="utf-8")
        assert re.search(r"^from _util import .*\bsmoke_results\b", text, re.M), s.name
        assert MAIN_OPENS_WITH_REDIRECT.search(text), s.name
        assert text.count("smoke_results()") == 1, s.name   # the redirect sits in main(), nowhere else
        main_block = text.split('if __name__ == "__main__":', 1)[1]
        assert "main(**vars(ap.parse_args()))" in main_block, s.name
    e06 = (EXP / "e06_posterior_mechanism.py").read_text(encoding="utf-8")
    assert 'PARTIAL_A = "_e06_part_a.json"' in e06 and "_util.RESULTS / PARTIAL_A" in e06
    assert '_util.RESULTS.glob("_e06_part_b_*.json")' in e06 and 'results/_e06' not in e06
    run_all = (EXP / "run_all.py").read_text(encoding="utf-8")
    assert "smoke_results()" in run_all and "_util.RESULTS = " not in run_all


def _fresh_util():
    spec = importlib.util.spec_from_file_location("_util_under_test", EXP / "_util.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_smoke_results_is_idempotent_and_leaves_the_root_alone():
    u = _fresh_util()
    root = u.RESULTS_ROOT
    assert u.RESULTS == root and root.name == "results"
    first = u.smoke_results()
    second = u.smoke_results()
    assert first == second == root / "smoke" and u.RESULTS == root / "smoke"
    assert u.RESULTS_ROOT == root


def test_a_script_run_with_smoke_writes_under_results_smoke_only(tmp_path):
    exp = tmp_path / "experiments"
    shutil.copytree(EXP, exp, ignore=shutil.ignore_patterns("__pycache__"))
    env = {**os.environ, "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1"}
    r = subprocess.run([sys.executable, str(exp / "e01_verifier_exactness.py"), "--smoke"],
                       cwd=tmp_path, capture_output=True, text=True, env=env)
    assert r.returncode == 0, r.stderr
    smoke = tmp_path / "results" / "smoke" / "e01_verifier_exactness.json"
    assert smoke.exists(), r.stdout
    assert not (tmp_path / "results" / "e01_verifier_exactness.json").exists()
    b = smoke.read_bytes()
    assert b"\r\n" not in b and b.endswith(b"}")
    payload = json.loads(b)
    assert payload["_experiment"] == "e01_verifier_exactness.json"
