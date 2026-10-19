"""Strict schema and model-profile validation for untrusted manifests."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from .errors import (
    ManifestError,
    ManifestResourceLimitError,
    UnsupportedProfileError,
)
from .rac import CODE_BITS, PROB_BITS_MAX

FORMAT_NAME = "lockstep-container"
FORMAT_VERSION = 0
PROFILE_ID = "lsp0"

_SHA256_RE = re.compile(r"\A[0-9a-f]{64}\Z")

DEFAULT_MAX_ORIGINAL_SIZE = 8 * 1024 * 1024 * 1024
DEFAULT_MAX_PAYLOAD_SIZE = 8 * 1024 * 1024 * 1024


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ManifestError(message)


def _dict(obj: Any, path: str) -> dict:
    _require(isinstance(obj, dict), f"{path} must be an object")
    return obj


def _int(obj: Any, path: str) -> int:
    _require(
        isinstance(obj, int) and not isinstance(obj, bool),
        f"{path} must be an integer",
    )
    return obj


def _str(obj: Any, path: str) -> str:
    _require(isinstance(obj, str), f"{path} must be a string")
    return obj


def _sha256(obj: Any, path: str) -> str:
    value = _str(obj, path)
    _require(bool(_SHA256_RE.fullmatch(value)), f"{path} must be 64 lowercase hex chars")
    return value


def _limit(value: Any, path: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{path} must be a non-negative integer (not bool)")
    return value


def _validate_expected_profile(actual: dict, expected: Mapping[str, Any]) -> None:
    for key, expected_value in expected.items():
        path = f"profile.model.{key}"
        if key not in actual:
            raise UnsupportedProfileError(f"{path} is required by profile {PROFILE_ID}")
        actual_value = actual[key]
        if type(actual_value) is not type(expected_value) or actual_value != expected_value:
            raise UnsupportedProfileError(
                f"{path} pins {actual_value!r}; this runtime requires {expected_value!r}"
            )


def validate_manifest(
    manifest: Any,
    *,
    max_original_size: int = DEFAULT_MAX_ORIGINAL_SIZE,
    max_payload_size: int = DEFAULT_MAX_PAYLOAD_SIZE,
    known_models: Any = None,
    expected_model_profiles: Any = None,
) -> dict:
    """Validate a parsed manifest against the exact ``lsp0`` reader contract.

    Unknown extension keys are ignored, but all required fields and all known
    model-profile parameters must be present with exact JSON types and values.
    """
    max_original_size = _limit(max_original_size, "max_original_size")
    max_payload_size = _limit(max_payload_size, "max_payload_size")

    root = _dict(manifest, "manifest")
    _require(root.get("format") == FORMAT_NAME, f"manifest.format must be {FORMAT_NAME!r}")
    format_version = _int(root.get("format_version"), "manifest.format_version")
    if format_version != FORMAT_VERSION:
        raise UnsupportedProfileError(
            f"unsupported format_version {format_version!r} (need {FORMAT_VERSION})"
        )

    profile = _dict(root.get("profile"), "manifest.profile")
    profile_id = _str(profile.get("id"), "profile.id")
    if profile_id != PROFILE_ID:
        raise UnsupportedProfileError(
            f"unsupported profile id {profile_id!r} (need {PROFILE_ID!r})"
        )

    coder = _dict(profile.get("coder"), "profile.coder")
    code_bits = _int(coder.get("code_bits"), "profile.coder.code_bits")
    if code_bits != CODE_BITS:
        raise UnsupportedProfileError(
            f"profile pins code_bits {code_bits!r}; this runtime requires {CODE_BITS}"
        )
    prob_bits_max = _int(
        coder.get("prob_bits_max"), "profile.coder.prob_bits_max"
    )
    if prob_bits_max != PROB_BITS_MAX:
        raise UnsupportedProfileError(
            "profile pins prob_bits_max "
            f"{prob_bits_max!r}; this runtime requires {PROB_BITS_MAX}"
        )

    model = _dict(profile.get("model"), "profile.model")
    model_name = _str(model.get("model"), "profile.model.model")
    if known_models is not None and model_name not in known_models:
        raise UnsupportedProfileError(
            f"container pins model {model_name!r} not provided by this runtime"
        )
    if expected_model_profiles is not None:
        try:
            expected = expected_model_profiles[model_name]
        except (KeyError, TypeError):
            raise UnsupportedProfileError(
                f"container pins model {model_name!r} without a supported profile definition"
            ) from None
        _require(isinstance(expected, Mapping), "runtime model profile definition is invalid")
        _validate_expected_profile(model, expected)

    original = _dict(root.get("original"), "manifest.original")
    original_size = _int(original.get("size"), "original.size")
    _require(original_size >= 0, "original.size must be non-negative")
    if original_size > max_original_size:
        raise ManifestResourceLimitError(
            f"original.size {original_size} exceeds max_original_size {max_original_size} "
            "(refusing potential decompression bomb)"
        )
    _sha256(original.get("sha256"), "original.sha256")

    payload = _dict(root.get("payload"), "manifest.payload")
    payload_size = _int(payload.get("size"), "payload.size")
    _require(payload_size >= 0, "payload.size must be non-negative")
    if payload_size > max_payload_size:
        raise ManifestResourceLimitError(
            f"payload.size {payload_size} exceeds max_payload_size {max_payload_size}"
        )
    _sha256(payload.get("sha256"), "payload.sha256")

    writer = root.get("writer")
    if writer is not None:
        writer_obj = _dict(writer, "manifest.writer")
        _str(writer_obj.get("tool"), "writer.tool")
        _str(writer_obj.get("version"), "writer.version")

    return root
