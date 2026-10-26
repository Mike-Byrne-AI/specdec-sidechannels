"""Programmatically reproduce empirical findings.

Each finding in trellis-docs/trellis-findings.md should ideally have a check here that re-runs
the empirical observation supporting the original claim. Findings become
testable claims rather than asserted narratives — if a finding is later
invalidated, this script tells you that, with numbers.

This file ships as a framework with NO project-specific checks. Add
verify_FN functions for your project's findings as they accumulate.

Usage:
    python tools/trellis_verify_finding.py --list           # list available checks
    python tools/trellis_verify_finding.py F1 --checkpoint <path>
"""

import argparse
import sys
from pathlib import Path
from typing import Callable, Dict

# Make `from src.X import Y` work regardless of cwd.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


# ----------------------------------------------------------------------
# Verdict helpers — keep these unchanged
# ----------------------------------------------------------------------

class Verdict:
    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    INCONCLUSIVE = "INCONCLUSIVE"


def _banner(finding_id: str, claim: str):
    print()
    print("=" * 72)
    print(f"Verifying {finding_id}")
    print("=" * 72)
    print(f"Original claim: {claim}")
    print()


def _result(verdict: str, summary: str):
    print()
    print(f"Verdict: {verdict}")
    print(f"Summary: {summary}")
    print()
    return verdict


# ----------------------------------------------------------------------
# Per-finding checks
# ----------------------------------------------------------------------
#
# To add a verifier for a new finding:
#
# 1. Write a function `verify_FN(args) -> str` that returns one of the
#    Verdict constants.
# 2. The function should:
#    - Call _banner(finding_id, claim) at the start
#    - Print the measurements it makes
#    - Call _result(verdict, summary) at the end
# 3. Register the function in the CHECKS dict below.
# 4. Test by running: python tools/trellis_verify_finding.py F-N --checkpoint <path>
#
# Template:
#
# def verify_F1(args) -> str:
#     """F1: <one-line claim>."""
#     _banner("F1", "<full claim text from trellis-docs/trellis-findings.md>")
#
#     # ... measurements ...
#     print(f"  Metric X: {value}")
#
#     if <SUPPORTS condition>:
#         return _result(Verdict.SUPPORTS, "<one-line summary>")
#     elif <CONTRADICTS condition>:
#         return _result(Verdict.CONTRADICTS, "<one-line summary>")
#     else:
#         return _result(Verdict.INCONCLUSIVE, "<why we can't tell>")


# ----------------------------------------------------------------------
# Registry — add new verifiers here
# ----------------------------------------------------------------------

CHECKS: Dict[str, Callable] = {
    # "F1": verify_F1,
    # "F2": verify_F2,
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("finding", nargs="?", help="Finding ID (e.g., F1, F2)")
    parser.add_argument("--checkpoint", type=str, help="Path to checkpoint (project-specific)")
    parser.add_argument("--data", type=str, help="Path to data file (project-specific)")
    parser.add_argument("--list", action="store_true", help="List available checks and exit")
    args = parser.parse_args()

    if args.list or not args.finding:
        print("\nAvailable finding checks:")
        if not CHECKS:
            print("  (no verifiers registered yet)")
            print()
            print("To add one, edit tools/trellis_verify_finding.py — see the template comment.")
        else:
            for fid in sorted(CHECKS):
                doc = (CHECKS[fid].__doc__ or "").strip().split("\n")[0]
                print(f"  {fid}: {doc}")
        print()
        print("Findings not in the list don't have programmatic checks yet — see trellis-docs/trellis-findings.md")
        return 0

    fid = args.finding.upper()
    if fid not in CHECKS:
        print(f"No verifier for {fid}. Available: {sorted(CHECKS)}")
        print("Findings without verifiers exist in trellis-docs/trellis-findings.md but aren't programmatically checkable yet.")
        return 1

    verdict = CHECKS[fid](args)
    return 0 if verdict in (Verdict.SUPPORTS, Verdict.INCONCLUSIVE) else 1


if __name__ == "__main__":
    sys.exit(main())
