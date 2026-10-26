"""Lockstep: deterministic arithmetic coding and model-pinned archives."""

from __future__ import annotations

__version__ = "0.2.0"

from .cdf import Cdf, quantize_probs, quantize_weights  # noqa: E402
from .codec import (  # noqa: E402
    EncodeStreamStats,
    decode_bytes,
    decode_stream,
    encode_bytes,
    encode_stream,
    roundtrip_ok,
)
from .container import (  # noqa: E402
    MAX_MANIFEST_SIZE,
    pack,
    pack_file,
    read_manifest,
    read_manifest_file,
    unpack,
    unpack_file,
    verify_file,
)
from .errors import (  # noqa: E402
    CoderError,
    ContainerError,
    DesyncError,
    IntegrityError,
    LockstepError,
    ManifestError,
    ManifestResourceLimitError,
    ResourceLimitError,
    UnsupportedProfileError,
)
from .models import (  # noqa: E402
    MODEL_PROFILES,
    AdaptiveByteModel,
    StaticModel,
    UniformModel,
    expected_model_profile,
    make_model,
)
from .rac import RangeDecoder, RangeEncoder  # noqa: E402

# The package's public surface, listed so the re-exports above read as intentional (2026-10-18;
# the cold read of that date counted 34 unused-import hits here that were all re-exports).
__all__ = [
    "__version__",
    "Cdf", "quantize_probs", "quantize_weights",
    "EncodeStreamStats", "decode_bytes", "decode_stream", "encode_bytes", "encode_stream", "roundtrip_ok",
    "MAX_MANIFEST_SIZE", "pack", "pack_file", "read_manifest", "read_manifest_file", "unpack", "unpack_file",
    "verify_file",
    "CoderError", "ContainerError", "DesyncError", "IntegrityError", "LockstepError", "ManifestError",
    "ManifestResourceLimitError", "ResourceLimitError", "UnsupportedProfileError",
    "MODEL_PROFILES", "AdaptiveByteModel", "StaticModel", "UniformModel", "expected_model_profile", "make_model",
    "RangeDecoder", "RangeEncoder",
]
