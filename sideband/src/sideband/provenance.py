"""Provenance helpers shared by every tool that writes a committed meta
file. torch-free on purpose: CPU tools (run_probes, run_posthoc_topic,
k3_threshold_search, run_error_predictor) import it at module level.

redact_args: vars(args) headed for a committed meta, minus anything
credential-shaped (standing guard: no --token arg exists today, but the
day one is added it must not land in git). Word/suffix matching, not
substring: 'tokenizer_revision' must survive; 'hf_token' must not.
"""

from __future__ import annotations

_REDACT_STEMS = ("token", "secret", "password", "api_key", "apikey")


def redact_args(args_dict: dict) -> dict:
    def _is_secret(k: str) -> bool:
        k = k.lower()
        return any(k == s or k.endswith("_" + s) for s in _REDACT_STEMS)

    return {k: v for k, v in args_dict.items() if not _is_secret(k)}
