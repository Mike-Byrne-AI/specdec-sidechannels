"""Real-model adapters (GPU box only).

Everything in this subpackage needs `pip install -e ".[real]"` and a CUDA box.
The verifier math is imported from `sideband.specdec` — the exact same code
proven correct by the CPU test suite. Only the logit sources change.

Import style: torch/transformers are imported lazily inside functions so the
rest of the package works without them.
"""

from __future__ import annotations


def require_real_deps():
    """Import and return (torch, transformers) or raise a helpful error."""
    try:
        import torch  # noqa: F401
        import transformers  # noqa: F401
    except ImportError as e:  # pragma: no cover - exercised only without deps
        raise ImportError(
            "sideband.real needs the GPU extras: pip install -e '.[real]'"
        ) from e
    import torch
    import transformers

    return torch, transformers
