"""amber v0 codec: verified archives over the sideband synthetic world.

Regime A (flagship): the content is TARGET-GENERATED under deterministic
decode (greedy here; seeded sampling is the designed extension — see
BLUEPRINT). The archive stores only where a deterministic DRAFT replay
diverges from the target's output:

    payload = n_corrections x ( gamma(gap+1), gamma(rank-1) )

where gap is the run of agreeing positions since the last correction and
rank is the true token's position in the draft distribution's stable order
(rank 1 == draft argmax == agreement, so corrections always have rank >= 2).

Decode needs ONLY the draft: replay it deterministically, emit its argmax on
agreement, emit the recorded rank's token on correction. The target never
exists at decode time — that asymmetry is the whole point, and byte-exact
draft replay is why the determinism runtime (lockstep) is the enabling
dependency. In this synthetic testbed, determinism is stood in for by seeds
carried in the header (D-5).

Decoder-reproducibility constraint (D-2): everything that shapes the code —
the draft distribution, its stable ordering, any steering — must be a
function of decoder-available state (header, decoded prefix, explicit
hints). Encoder-only signals (the target's p) may decide WHAT to correct or
hint, never silently reshape q. This is why serve-time steered traces are
not automatically archives; see BLUEPRINT "serving-compatibility".

Rank coding's stable order: probabilities descending, token index ascending
on ties — the same lexsort convention as sideband's HashSketch. Note the
consequence (measured in a02): the codec is INVARIANT to any monotone
recalibration of the draft (e.g. temperature), which is robustness and an
attestation blind spot at once.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass

import numpy as np

from sideband.synthetic import World, WorldConfig

from .bits import BitReader, BitWriter, gamma_decode, gamma_encode
from .rac_codec import (CODERS, FLAG_A, FLAG_C, FLAG_T, FLAG_X, CoderParams, PayloadDecoder,
                        PayloadEncoder, classify)

MAGIC = "AMBR"
VERSION = 2                         # v2: coder field, tie escape, payload digest (P3)
MAX_HEADER_BYTES = 1 << 20          # 1 MiB; a v0 header is ~400 B
DEFAULT_MAX_LENGTH = 1 << 24        # 16M positions; caller-tunable (bomb guard)
MAX_TIE_TOPM = 1 << 10
REQUIRED_FIELDS = frozenset({"magic", "version", "cfg", "path_seed", "draft_seed",
                             "length", "n_corrections", "payload_bits", "fingerprint",
                             "header_sha", "coder", "tie_margin", "tie_topm", "max_rank",
                             "payload_sha"})


def payload_digest(payload: bytes) -> str:
    """Damage detection for the payload (D-7's open item). Essential for the
    rac coder: an adaptive arithmetic decoder turns one flipped byte into a
    plausible-looking wrong tail, so corruption must be caught BEFORE replay."""
    return hashlib.sha256(payload).hexdigest()[:16]


def coder_params(h: dict) -> CoderParams:
    return CoderParams(tie_margin=float(h["tie_margin"]), tie_topm=h["tie_topm"], max_rank=h["max_rank"],
                       vocab_bits=max(1, (WorldConfig(**h["cfg"]).vocab_size - 1).bit_length()))


def stable_order(q: np.ndarray) -> np.ndarray:
    """Token indices by probability descending, index ascending on ties."""
    return np.lexsort((np.arange(q.shape[0]), -q))


def fingerprint(cfg: WorldConfig, path_seed: int, draft_seed: int) -> str:
    """L0 model/config pin: what must match for draft replay to reproduce."""
    blob = json.dumps({"cfg": asdict(cfg), "path_seed": path_seed,
                       "draft_seed": draft_seed}, sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def header_digest(header: dict) -> str:
    """Integrity seal over EVERY other header field (canonical JSON). The
    fingerprint pins the model; this catches corruption of the fields the
    fingerprint does not cover (length, n_corrections, payload_bits) — found
    by the seeded mutation sweep: a one-bit flip in the length digits decoded
    'successfully' to a longer sequence. No key, so this is damage detection,
    not forgery resistance (same posture as lockstep D-9)."""
    body = {k: v for k, v in header.items() if k != "header_sha"}
    blob = json.dumps(body, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def reseal(header: dict) -> dict:
    """Return a copy with fingerprint and header_sha recomputed from the other
    fields. Tests and experiments use this to build DELIBERATE substitutions
    (L0 bypassed on purpose); it is never called on the decode path."""
    h = dict(header)
    h["fingerprint"] = fingerprint(WorldConfig(**h["cfg"]), h["path_seed"], h["draft_seed"])
    h["header_sha"] = header_digest(h)
    return h


@dataclass
class Archive:
    header: dict
    payload: bytes

    def to_bytes(self) -> bytes:
        hj = json.dumps(self.header, sort_keys=True).encode()
        return MAGIC.encode() + len(hj).to_bytes(4, "big") + hj + self.payload

    @staticmethod
    def from_bytes(data: bytes, max_length: int = DEFAULT_MAX_LENGTH) -> "Archive":
        """Strict, typed parse of an UNTRUSTED archive (lockstep D-11 pattern:
        one choke point, every failure a ValueError, declared sizes bounded
        BEFORE any replay work is done)."""
        if not isinstance(data, (bytes, bytearray)):
            raise ValueError("archive must be bytes")
        data = bytes(data)
        if len(data) < 8 or data[:4] != MAGIC.encode():
            raise ValueError("not an amber archive (bad magic or truncated framing)")
        hlen = int.from_bytes(data[4:8], "big")
        if hlen > MAX_HEADER_BYTES:
            raise ValueError(f"header length {hlen} exceeds MAX_HEADER_BYTES {MAX_HEADER_BYTES}")
        if 8 + hlen > len(data):
            raise ValueError("truncated archive (header extends past end of data)")
        header = _parse_header(data[8 : 8 + hlen])
        payload = data[8 + hlen :]
        validate_header(header, payload_len=len(payload), max_length=max_length, payload=payload)
        return Archive(header=header, payload=payload)


def _no_duplicate_keys(pairs):
    d = {}
    for k, v in pairs:
        if k in d:
            raise ValueError(f"duplicate header key {k!r}")
        d[k] = v
    return d


def _reject_nonfinite(s: str):
    raise ValueError(f"non-finite number {s!r} in header")


def _parse_header(raw: bytes) -> dict:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"header is not UTF-8: {exc}") from None
    try:
        header = json.loads(text, object_pairs_hook=_no_duplicate_keys,
                            parse_constant=_reject_nonfinite)
    except ValueError as exc:  # json.JSONDecodeError is a ValueError subclass
        raise ValueError(f"header is not valid JSON: {exc}") from None
    except RecursionError:
        raise ValueError("header JSON nesting too deep") from None
    if not isinstance(header, dict):
        raise ValueError("header must be a JSON object")
    return header


def _int_field(h: dict, key: str, lo: int, hi: int) -> int:
    v = h.get(key)
    if not isinstance(v, int) or isinstance(v, bool):
        raise ValueError(f"header field {key!r} must be an integer")
    if not (lo <= v <= hi):
        raise ValueError(f"header field {key!r}={v} outside [{lo}, {hi}]")
    return v


def validate_header(h: dict, payload_len: int, max_length: int = DEFAULT_MAX_LENGTH,
                    payload: bytes | None = None) -> None:
    """Exact schema check. Everything decode() will trust is verified here;
    with `payload` given, its digest is checked too."""
    if not isinstance(max_length, int) or isinstance(max_length, bool) or max_length < 0:
        raise ValueError("max_length must be a non-negative integer")
    missing = REQUIRED_FIELDS - set(h)
    if missing:
        raise ValueError(f"header missing fields {sorted(missing)}")
    extra = set(h) - REQUIRED_FIELDS
    if extra:
        raise ValueError(f"header has unknown fields {sorted(extra)}")
    if h["magic"] != MAGIC:
        raise ValueError("header magic mismatch")
    if h["version"] != VERSION or isinstance(h["version"], bool):
        raise ValueError(f"unsupported archive version {h['version']!r}")
    length = _int_field(h, "length", 0, max_length)
    _int_field(h, "n_corrections", 0, length)
    _int_field(h, "payload_bits", 0, 8 * payload_len)
    _int_field(h, "path_seed", 0, 2**63 - 1)
    _int_field(h, "draft_seed", 0, 2**63 - 1)
    for key in ("fingerprint", "header_sha", "payload_sha"):
        fp = h[key]
        if not (isinstance(fp, str) and len(fp) == 16 and all(c in "0123456789abcdef" for c in fp)):
            raise ValueError(f"header {key} must be 16 lowercase hex chars")
    if h["header_sha"] != header_digest(h):
        raise ValueError("header_sha mismatch (corrupt or tampered header)")
    if payload is not None and h["payload_sha"] != payload_digest(payload):
        raise ValueError("payload_sha mismatch (corrupt payload)")
    if h["coder"] not in CODERS:
        raise ValueError(f"unknown coder {h['coder']!r}")
    tm = h["tie_margin"]
    if isinstance(tm, bool) or not isinstance(tm, (int, float)) or not math.isfinite(tm) or tm < 0:
        raise ValueError("header tie_margin must be a finite number >= 0")
    if h["coder"] == "gamma" and tm != 0:
        raise ValueError("gamma coder has no tie escape (tie_margin must be 0)")
    _int_field(h, "tie_topm", 2, MAX_TIE_TOPM)
    cfg = h["cfg"]
    if not isinstance(cfg, dict):
        raise ValueError("header cfg must be an object")
    allowed = set(WorldConfig.__dataclass_fields__)
    if set(cfg) != allowed:
        raise ValueError(f"header cfg fields must be exactly {sorted(allowed)}")
    for k, v in cfg.items():
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            raise ValueError(f"header cfg field {k!r} must be numeric")
        if isinstance(v, float) and not math.isfinite(v):
            raise ValueError(f"header cfg field {k!r} is non-finite")
    try:
        wc = WorldConfig(**cfg)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"header cfg does not build a WorldConfig: {exc}") from None
    _int_field(h, "max_rank", 2, max(2, int(wc.vocab_size)))


def _replay(cfg: WorldConfig, path_seed: int, draft_seed: int, length: int):
    """Deterministic joint replay: latent path, target greedy token, draft
    distribution per position. Used identically by encode and decode."""
    world = World(cfg)
    path = world.sample_concept_path(np.random.default_rng(path_seed), length)
    gen_draft = np.random.default_rng(draft_seed)
    for t in range(length):
        c = int(path[t])
        x = int(np.argmax(world.P[c]))          # target greedy = the content
        q = world.draft_dist(world.draft_concept(gen_draft, c))
        yield t, x, q


def top2_gap(q: np.ndarray, order: np.ndarray) -> float:
    """Encoder-side near-tie measure in LOGIT units (log q), matching the raw
    logit gap the real pipeline records; inf when the runner-up has q == 0."""
    with np.errstate(divide="ignore"):
        lq = np.log(q)
    return float(lq[order[0]] - lq[order[1]]) if q.shape[0] > 1 else float("inf")


def encode(cfg: WorldConfig, path_seed: int, draft_seed: int, length: int, coder: str = "gamma",
           tie_margin: float = 0.0, tie_topm: int = 2, max_rank: int = 64) -> tuple[Archive, np.ndarray]:
    """Compress the target's greedy sequence; returns (archive, tokens).
    coder="gamma" is the v0 payload, byte-for-byte; "rac1" is the P3 coder
    with the optional tie escape (tie_margin > 0)."""
    if coder not in CODERS:
        raise ValueError(f"unknown coder {coder!r}")
    if coder == "gamma" and tie_margin != 0:
        raise ValueError("tie escape needs coder='rac1'")
    max_rank = min(max_rank, cfg.vocab_size)
    tokens = np.empty(length, dtype=np.int64)
    n_div = 0
    if coder == "gamma":
        w = BitWriter(); gap = 0
        for t, x, q in _replay(cfg, path_seed, draft_seed, length):
            tokens[t] = x
            order = stable_order(q)
            if int(order[0]) == x:
                gap += 1
                continue
            rank = int(np.flatnonzero(order == x)[0]) + 1  # >= 2 by construction
            gamma_encode(w, gap + 1)
            gamma_encode(w, rank - 1)
            n_div += 1
            gap = 0
        payload, payload_bits = w.to_bytes(), w.n_bits
    else:
        p = CoderParams(tie_margin=tie_margin, tie_topm=min(tie_topm, cfg.vocab_size), max_rank=max_rank,
                        vocab_bits=max(1, (cfg.vocab_size - 1).bit_length()))
        enc = PayloadEncoder(p)
        for t, x, q in _replay(cfg, path_seed, draft_seed, length):
            tokens[t] = x
            order = stable_order(q)
            rank = int(np.flatnonzero(order == x)[0]) + 1
            n_div += int(rank != 1)
            flag = classify(rank, top2_gap(q, order), p)
            if flag == FLAG_A:
                enc.step(t, FLAG_A)
            elif flag == FLAG_C:
                enc.step(t, FLAG_C, rank)
            elif flag == FLAG_T:
                enc.step(t, FLAG_T, int(np.searchsorted(np.sort(order[:p.tie_topm]), x)))
            else:
                enc.step(t, FLAG_X, x)
        payload = enc.finish(); payload_bits = 8 * len(payload)
        tie_topm = p.tie_topm
    header = {
        "magic": MAGIC, "version": VERSION,
        "cfg": asdict(cfg), "path_seed": path_seed, "draft_seed": draft_seed,
        "length": length, "n_corrections": n_div, "payload_bits": payload_bits,
        "fingerprint": fingerprint(cfg, path_seed, draft_seed),
        "coder": coder, "tie_margin": float(tie_margin), "tie_topm": int(tie_topm), "max_rank": int(max_rank),
        "payload_sha": payload_digest(payload),
    }
    header["header_sha"] = header_digest(header)
    return Archive(header=header, payload=payload), tokens


def decode(archive: Archive, expected_fingerprint: str | None = None, perturb=None) -> np.ndarray:
    """Draft-only reconstruction. Byte-exact iff the replayed draft matches
    the encoding draft — the determinism contract. `perturb(t, q) -> q'` is a
    TEST hook that stands in for decoder-side draft drift (D-2: every
    decoder-visible mechanism gets a decode-side reproduction test)."""
    h = archive.header
    # Archives built in-process (encode()) skip from_bytes; validate here too so
    # every decode sees the same schema check regardless of construction path.
    validate_header(h, payload_len=len(archive.payload), payload=archive.payload)
    cfg = WorldConfig(**h["cfg"])
    if h["fingerprint"] != fingerprint(cfg, h["path_seed"], h["draft_seed"]):
        raise ValueError("header fingerprint mismatch (tampered or corrupt header)")
    if expected_fingerprint is not None and h["fingerprint"] != expected_fingerprint:
        raise ValueError("archive is not pinned to the expected model/config")
    vocab = cfg.vocab_size
    out = np.empty(h["length"], dtype=np.int64)

    if h["coder"] == "gamma":
        r = BitReader(archive.payload, h["payload_bits"])
        corrections: list[tuple[int, int]] = []
        pos = -1
        for _ in range(h["n_corrections"]):
            gap = gamma_decode(r) - 1
            rank = gamma_decode(r) + 1
            pos += gap + 1
            if pos >= h["length"]:
                raise ValueError("correction position beyond sequence length (corrupt payload)")
            if not (2 <= rank <= vocab):
                raise ValueError("correction rank out of range (corrupt payload)")
            corrections.append((pos, rank))
        corr = dict(corrections)
        if len(corr) != h["n_corrections"]:
            raise ValueError("duplicate correction positions (corrupt payload)")
        for t, _x_unused, q in _replay(cfg, h["path_seed"], h["draft_seed"], h["length"]):
            if perturb is not None:
                q = perturb(t, q)
            order = stable_order(q)
            out[t] = int(order[corr[t] - 1]) if t in corr else int(order[0])
        return out

    p = coder_params(h)
    dec = PayloadDecoder(archive.payload, p)
    for t, _x_unused, q in _replay(cfg, h["path_seed"], h["draft_seed"], h["length"]):
        if perturb is not None:
            q = perturb(t, q)
        order = stable_order(q)
        flag, value = dec.step(t)
        if flag == FLAG_A:
            out[t] = int(order[0])
        elif flag == FLAG_C:
            out[t] = int(order[value - 1])            # value <= max_rank <= vocab by validation
        elif flag == FLAG_T:
            out[t] = int(np.sort(order[:p.tie_topm])[value])
        else:
            if value >= vocab:
                raise ValueError("raw token id beyond vocabulary (corrupt payload)")
            out[t] = value
    return out


def attest_with_target(archive: Archive, tokens: np.ndarray) -> dict:
    """L1 attestation: with the TARGET available, recompute the divergence
    set and check it matches the recorded corrections exactly. L0 (draft-only)
    is the header fingerprint check inside decode()."""
    h = archive.header
    cfg = WorldConfig(**h["cfg"])
    n_div, mism = 0, 0
    for t, x, q in _replay(cfg, h["path_seed"], h["draft_seed"], h["length"]):
        div = int(stable_order(q)[0]) != x
        n_div += int(div)
        mism += int(x != int(tokens[t]))
    return {
        "recorded_corrections": h["n_corrections"],
        "recomputed_divergences": n_div,
        "token_mismatches_vs_target": mism,
        "attested": (n_div == h["n_corrections"]) and (mism == 0),
    }
