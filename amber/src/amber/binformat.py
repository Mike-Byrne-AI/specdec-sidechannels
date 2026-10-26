"""amber v3 binary framing ("hfb"): the self-description cost of an archive,
minimised and itemised. Strict typed pack/unpack; every failure a ValueError.

Layout (see experiments/P5_PROTOCOL.md):
    AMBR | ver u8 | kind u8 | coder u8 | dtype u8 | flags u8
    varint(len)+utf8 model_id | [snapshot 20 B if FLAG_SNAPSHOT]
    fingerprint 8 B | varint vocab, max_rank, tie_topm
    [f32 tie_margin if coder == rac1]
    varint first_token, prompt_len, length, n_corrections, payload_bits
    payload_sha 8 B | content_sha 8 B | header_sha 8 B (sha256[:8] of ALL
    preceding bytes) | payload

One payload stream, two segments (prompt tokens 1..P-1, then content), both
coded with the same {A, C, X} grammar against the draft. Digests are damage
detection, not forgery resistance (lockstep D-9 posture; no key).
"""

from __future__ import annotations

import hashlib
import struct

from .rac_codec import CoderParams

MAGIC = b"AMBR"
VERSION3 = 3
KIND_HFB = 2
KIND_SESSION = 3
CTX_RESET, CTX_SHARED = 0, 1
MAX_TURNS = 1 << 12
CODER_CODES = {"gamma": 0, "rac1": 1}
CODER_NAMES = {v: k for k, v in CODER_CODES.items()}
DTYPE_CODES = {"fp32": 0, "bf16": 1, "fp16": 2}
DTYPE_NAMES = {v: k for k, v in DTYPE_CODES.items()}
FLAG_SNAPSHOT = 1
MAX_MODEL_ID = 256
MAX_VARINT_BYTES = 5


def write_varint(out: bytearray, v: int) -> None:
    if not isinstance(v, int) or isinstance(v, bool) or v < 0 or v >= 1 << 35:
        raise ValueError(f"varint out of range: {v!r}")
    while True:
        b = v & 0x7F
        v >>= 7
        out.append(b | (0x80 if v else 0))
        if not v:
            return


def read_varint(data: bytes, pos: int) -> tuple[int, int]:
    v = 0
    for i in range(MAX_VARINT_BYTES):
        if pos + i >= len(data):
            raise ValueError("truncated varint")
        b = data[pos + i]
        v |= (b & 0x7F) << (7 * i)
        if not (b & 0x80):
            return v, pos + i + 1
    raise ValueError("varint too long")


def _d8(blob: bytes) -> bytes:
    return hashlib.sha256(blob).digest()[:8]


def pack(*, model_id: str, snapshot: str | None, dtype: str, fingerprint8: bytes, vocab_size: int,
         coder: str, p: CoderParams, first_token: int, prompt_len: int, length: int,
         n_corrections: int, payload: bytes, content_sha8: bytes) -> bytes:
    if coder not in CODER_CODES:
        raise ValueError(f"unknown coder {coder!r}")
    if dtype not in DTYPE_CODES:
        raise ValueError(f"unknown dtype {dtype!r}")
    mid = model_id.encode("utf-8")
    if not (0 < len(mid) <= MAX_MODEL_ID):
        raise ValueError("model_id length out of range")
    if len(fingerprint8) != 8 or len(content_sha8) != 8:
        raise ValueError("fingerprint/content digests must be 8 bytes")
    snap = bytes.fromhex(snapshot) if snapshot else b""
    if snapshot and len(snap) != 20:
        raise ValueError("snapshot must be 40 hex chars (20 bytes)")
    out = bytearray()
    out += MAGIC
    out += bytes([VERSION3, KIND_HFB, CODER_CODES[coder], DTYPE_CODES[dtype], FLAG_SNAPSHOT if snapshot else 0])
    write_varint(out, len(mid)); out += mid
    out += snap
    out += fingerprint8
    write_varint(out, vocab_size); write_varint(out, p.max_rank); write_varint(out, p.tie_topm)
    if coder == "rac1":
        out += struct.pack("<f", float(p.tie_margin))
    elif p.tie_margin != 0:
        raise ValueError("gamma has no tie escape")
    write_varint(out, first_token); write_varint(out, prompt_len); write_varint(out, length)
    write_varint(out, n_corrections)
    write_varint(out, 8 * len(payload))          # payload_bits (byte-aligned streams)
    out += _d8(payload)
    out += content_sha8
    out += _d8(bytes(out))                        # header_sha over everything so far
    return bytes(out) + payload


def unpack(data: bytes) -> tuple[dict, bytes, CoderParams]:
    if not isinstance(data, (bytes, bytearray)):
        raise ValueError("archive must be bytes")
    data = bytes(data)
    if len(data) < 12 or data[:4] != MAGIC:
        raise ValueError("not an amber archive (bad magic or truncated)")
    ver, kind, coder_c, dtype_c, flags = data[4:9]
    if ver != VERSION3 or kind != KIND_HFB:
        raise ValueError(f"unsupported version/kind {ver}/{kind}")
    if coder_c not in CODER_NAMES or dtype_c not in DTYPE_NAMES or flags not in (0, FLAG_SNAPSHOT):
        raise ValueError("bad coder/dtype/flags byte")
    coder = CODER_NAMES[coder_c]
    pos = 9
    mlen, pos = read_varint(data, pos)
    if not (0 < mlen <= MAX_MODEL_ID) or pos + mlen > len(data):
        raise ValueError("bad model_id length")
    try:
        model_id = data[pos:pos + mlen].decode("utf-8")
    except UnicodeDecodeError:
        raise ValueError("model_id is not UTF-8") from None
    pos += mlen
    snapshot = None
    if flags & FLAG_SNAPSHOT:
        if pos + 20 > len(data):
            raise ValueError("truncated snapshot")
        snapshot = data[pos:pos + 20].hex(); pos += 20
    if pos + 8 > len(data):
        raise ValueError("truncated fingerprint")
    fingerprint8 = data[pos:pos + 8]; pos += 8
    vocab, pos = read_varint(data, pos)
    max_rank, pos = read_varint(data, pos)
    tie_topm, pos = read_varint(data, pos)
    tie_margin = 0.0
    if coder == "rac1":
        if pos + 4 > len(data):
            raise ValueError("truncated tie_margin")
        tie_margin = struct.unpack("<f", data[pos:pos + 4])[0]; pos += 4
        if not (tie_margin >= 0):                 # rejects NaN and negatives
            raise ValueError("bad tie_margin")
    first_token, pos = read_varint(data, pos)
    prompt_len, pos = read_varint(data, pos)
    length, pos = read_varint(data, pos)
    n_corr, pos = read_varint(data, pos)
    payload_bits, pos = read_varint(data, pos)
    if pos + 24 > len(data):
        raise ValueError("truncated digests")
    payload_sha8 = data[pos:pos + 8]; content_sha8 = data[pos + 8:pos + 16]
    header_sha8 = data[pos + 16:pos + 24]
    if _d8(data[:pos + 16]) != header_sha8:
        raise ValueError("header_sha mismatch (corrupt or tampered header)")
    payload = data[pos + 24:]
    if _d8(payload) != payload_sha8:
        raise ValueError("payload_sha mismatch (corrupt payload)")
    # semantic checks (after integrity: a clean digest with bad fields is a format bug, not damage)
    if not (2 <= vocab <= 1 << 24) or not (2 <= max_rank <= vocab) or not (2 <= tie_topm <= 1 << 10):
        raise ValueError("vocab/max_rank/tie_topm out of range")
    if not (0 <= first_token < vocab) or prompt_len < 1 or length < 0:
        raise ValueError("first_token/prompt_len/length out of range")
    n_symbols = (prompt_len - 1) + length
    if not (0 <= n_corr <= n_symbols) or payload_bits != 8 * len(payload):
        raise ValueError("n_corrections/payload_bits inconsistent with payload")
    header = {"model": {"id": model_id, "snapshot": snapshot, "dtype": DTYPE_NAMES[dtype_c]},
              "vocab_size": vocab, "coder": coder, "first_token": first_token, "prompt_len": prompt_len,
              "length": length, "n_corrections": n_corr, "payload_bits": payload_bits,
              "fingerprint8": fingerprint8, "content_sha8": content_sha8}
    p = CoderParams(tie_margin=float(tie_margin), tie_topm=tie_topm, max_rank=max_rank,
                    vocab_bits=max(1, (vocab - 1).bit_length()))
    return header, payload, p


def pack_session(*, model_id: str, snapshot: str | None, dtype: str, fingerprint8: bytes, vocab_size: int,
                 coder: str, p: CoderParams, ctx_mode: int, turns: list[dict], n_corrections: int,
                 payload: bytes, content_sha8: bytes) -> bytes:
    """v4 session archive: one pin/digest set, k turns. turns = [{prompt_len,
    gen_len, first_token}] — first_token is required per turn for ctx_mode 0,
    and only turn 0's is used (the session opener) for ctx_mode 1."""
    if coder not in CODER_CODES:
        raise ValueError(f"unknown coder {coder!r}")
    if dtype not in DTYPE_CODES:
        raise ValueError(f"unknown dtype {dtype!r}")
    if ctx_mode not in (CTX_RESET, CTX_SHARED):
        raise ValueError("ctx_mode must be 0 (reset) or 1 (shared)")
    if not (0 < len(turns) <= MAX_TURNS):
        raise ValueError("n_turns out of range")
    if coder == "gamma" and p.tie_margin != 0:
        raise ValueError("gamma has no tie escape")
    mid = model_id.encode("utf-8")
    if not (0 < len(mid) <= MAX_MODEL_ID):
        raise ValueError("model_id length out of range")
    if len(fingerprint8) != 8 or len(content_sha8) != 8:
        raise ValueError("fingerprint/content digests must be 8 bytes")
    snap = bytes.fromhex(snapshot) if snapshot else b""
    if snapshot and len(snap) != 20:
        raise ValueError("snapshot must be 40 hex chars (20 bytes)")
    out = bytearray()
    out += MAGIC
    out += bytes([VERSION3, KIND_SESSION, CODER_CODES[coder], DTYPE_CODES[dtype], FLAG_SNAPSHOT if snapshot else 0])
    write_varint(out, len(mid)); out += mid
    out += snap
    out += fingerprint8
    write_varint(out, vocab_size); write_varint(out, p.max_rank); write_varint(out, p.tie_topm)
    if coder == "rac1":
        out += struct.pack("<f", float(p.tie_margin))
    out.append(ctx_mode)
    write_varint(out, len(turns))
    for i, t in enumerate(turns):
        write_varint(out, t["prompt_len"]); write_varint(out, t["gen_len"])
        if ctx_mode == CTX_RESET or i == 0:
            write_varint(out, t["first_token"])
    write_varint(out, n_corrections)
    write_varint(out, 8 * len(payload))
    out += _d8(payload)
    out += content_sha8
    out += _d8(bytes(out))
    return bytes(out) + payload


def unpack_session(data: bytes) -> tuple[dict, bytes, CoderParams]:
    if not isinstance(data, (bytes, bytearray)):
        raise ValueError("archive must be bytes")
    data = bytes(data)
    if len(data) < 12 or data[:4] != MAGIC:
        raise ValueError("not an amber archive (bad magic or truncated)")
    ver, kind, coder_c, dtype_c, flags = data[4:9]
    if ver != VERSION3 or kind != KIND_SESSION:
        raise ValueError(f"unsupported version/kind {ver}/{kind}")
    if coder_c not in CODER_NAMES or dtype_c not in DTYPE_NAMES or flags not in (0, FLAG_SNAPSHOT):
        raise ValueError("bad coder/dtype/flags byte")
    coder = CODER_NAMES[coder_c]
    pos = 9
    mlen, pos = read_varint(data, pos)
    if not (0 < mlen <= MAX_MODEL_ID) or pos + mlen > len(data):
        raise ValueError("bad model_id length")
    try:
        model_id = data[pos:pos + mlen].decode("utf-8")
    except UnicodeDecodeError:
        raise ValueError("model_id is not UTF-8") from None
    pos += mlen
    snapshot = None
    if flags & FLAG_SNAPSHOT:
        if pos + 20 > len(data):
            raise ValueError("truncated snapshot")
        snapshot = data[pos:pos + 20].hex(); pos += 20
    if pos + 8 > len(data):
        raise ValueError("truncated fingerprint")
    fingerprint8 = data[pos:pos + 8]; pos += 8
    vocab, pos = read_varint(data, pos)
    max_rank, pos = read_varint(data, pos)
    tie_topm, pos = read_varint(data, pos)
    tie_margin = 0.0
    if coder == "rac1":
        if pos + 4 > len(data):
            raise ValueError("truncated tie_margin")
        tie_margin = struct.unpack("<f", data[pos:pos + 4])[0]; pos += 4
        if not (tie_margin >= 0):
            raise ValueError("bad tie_margin")
    if pos >= len(data):
        raise ValueError("truncated ctx_mode")
    ctx_mode = data[pos]; pos += 1
    if ctx_mode not in (CTX_RESET, CTX_SHARED):
        raise ValueError("bad ctx_mode")
    n_turns, pos = read_varint(data, pos)
    if not (0 < n_turns <= MAX_TURNS):
        raise ValueError("n_turns out of range")
    turns = []
    for i in range(n_turns):
        pl, pos = read_varint(data, pos)
        gl, pos = read_varint(data, pos)
        ft = None
        if ctx_mode == CTX_RESET or i == 0:
            ft, pos = read_varint(data, pos)
        turns.append({"prompt_len": pl, "gen_len": gl, "first_token": ft})
    n_corr, pos = read_varint(data, pos)
    payload_bits, pos = read_varint(data, pos)
    if pos + 24 > len(data):
        raise ValueError("truncated digests")
    payload_sha8 = data[pos:pos + 8]; content_sha8 = data[pos + 8:pos + 16]
    header_sha8 = data[pos + 16:pos + 24]
    if _d8(data[:pos + 16]) != header_sha8:
        raise ValueError("header_sha mismatch (corrupt or tampered header)")
    payload = data[pos + 24:]
    if _d8(payload) != payload_sha8:
        raise ValueError("payload_sha mismatch (corrupt payload)")
    if not (2 <= vocab <= 1 << 24) or not (2 <= max_rank <= vocab) or not (2 <= tie_topm <= 1 << 10):
        raise ValueError("vocab/max_rank/tie_topm out of range")
    n_symbols = 0
    for i, t in enumerate(turns):
        if t["prompt_len"] < 1 or t["gen_len"] < 0:
            raise ValueError("bad turn table")
        if t["first_token"] is not None and not (0 <= t["first_token"] < vocab):
            raise ValueError("turn first_token out of range")
        n_symbols += t["prompt_len"] + t["gen_len"] - (1 if (ctx_mode == CTX_RESET or i == 0) else 0)
    if not (0 <= n_corr <= n_symbols) or payload_bits != 8 * len(payload):
        raise ValueError("n_corrections/payload_bits inconsistent with payload")
    header = {"model": {"id": model_id, "snapshot": snapshot, "dtype": DTYPE_NAMES[dtype_c]},
              "vocab_size": vocab, "coder": coder, "ctx_mode": ctx_mode, "turns": turns,
              "n_symbols": n_symbols, "n_corrections": n_corr, "payload_bits": payload_bits,
              "fingerprint8": fingerprint8, "content_sha8": content_sha8}
    p = CoderParams(tie_margin=float(tie_margin), tie_topm=tie_topm, max_rank=max_rank,
                    vocab_bits=max(1, (vocab - 1).bit_length()))
    return header, payload, p


def fixed_overhead_bytes(model_id: str, with_snapshot: bool) -> int:
    """The self-description floor of this design, itemised in the report."""
    return (4 + 5) + (1 + len(model_id.encode())) + (20 if with_snapshot else 0) + 8 + 24 + 12
