"""Packaged conformance-vector loading and execution."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from importlib import resources
from typing import Optional

from .codec import decode_bytes, encode_bytes
from .drbg import deterministic_bytes
from .errors import CoderError
from .models import make_model

VECTORS_V0_SHA256 = "c452e20b01344a9d4b1e0c0f42b17da97572de7ac52746a3c9ef6e91934b4861"


@dataclass(frozen=True)
class VectorResult:
    name: str
    ok: bool
    detail: str


def load_vectors() -> dict:
    resource = resources.files("lockstep.data").joinpath("vectors_v0.json")
    try:
        raw = resource.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if digest != VECTORS_V0_SHA256:
            raise CoderError(
                "packaged conformance-vector bytes do not match the pinned lsp0 digest"
            )
        text = raw.decode("utf-8")
        spec = json.loads(text)
    except CoderError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CoderError(f"cannot load packaged conformance vectors: {exc}") from exc
    if not isinstance(spec, dict) or spec.get("profile") != "lsp0":
        raise CoderError("packaged conformance vectors do not describe profile lsp0")
    if not isinstance(spec.get("cases"), list):
        raise CoderError("packaged conformance vectors have no cases list")
    return spec


def materialize_input(spec: dict) -> bytes:
    if not isinstance(spec, dict):
        raise CoderError("vector input must be an object")
    kind = spec.get("kind")
    if kind == "literal-utf8":
        text = spec.get("text")
        if not isinstance(text, str):
            raise CoderError("literal-utf8 vector requires string text")
        try:
            return text.encode("utf-8")
        except UnicodeEncodeError as exc:
            raise CoderError(
                "literal-utf8 vector contains an invalid Unicode surrogate"
            ) from exc
    if kind == "drbg":
        return deterministic_bytes(spec.get("seed"), spec.get("n"))
    if kind == "byte-ramp":
        repeat = spec.get("repeat")
        if not isinstance(repeat, int) or isinstance(repeat, bool) or repeat < 0:
            raise CoderError("byte-ramp repeat must be a non-negative integer")
        return bytes(range(256)) * repeat
    raise CoderError(f"unknown vector input kind {kind!r}")


def run_vectors(spec: Optional[dict] = None) -> list[VectorResult]:
    vectors = load_vectors() if spec is None else spec
    results = []
    for case in vectors["cases"]:
        name = case.get("name", "<unnamed>")
        try:
            data = materialize_input(case["input"])
            original_digest = hashlib.sha256(data).hexdigest()
            if len(data) != case["n_bytes"] or original_digest != case["original_sha256"]:
                results.append(VectorResult(name, False, "input materialization drifted"))
                continue
            payload = encode_bytes(data, make_model(case["model"]))
            payload_digest = hashlib.sha256(payload).hexdigest()
            if len(payload) != case["payload_size"] or payload_digest != case["payload_sha256"]:
                results.append(VectorResult(name, False, "encoder payload does not conform"))
                continue
            decoded = decode_bytes(payload, len(data), make_model(case["model"]))
            if decoded != data:
                results.append(VectorResult(name, False, "decoder desynchronised"))
                continue
            results.append(VectorResult(name, True, "ok"))
        except (KeyError, TypeError, CoderError) as exc:
            results.append(VectorResult(name, False, str(exc)))
    return results
