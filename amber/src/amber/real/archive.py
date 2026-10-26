"""Real-model amber archives (header kind "hf"): encode with the draft's
teacher-forced logits, decode with the draft alone, replayed incrementally.

    header (JSON, sealed by header_sha):
        kind="hf", model={id, snapshot, dtype}, vocab_size, prompt_ids,
        length, n_corrections, coder/tie_margin/tie_topm/max_rank,
        payload_bits, payload_sha, content_sha, fingerprint
    payload: gamma (v0, default) or rac1 (src/amber/rac_codec.py)

The decoder needs only: the pinned draft, the prompt ids, and a `stepper`
that returns the draft's canonical top-K (value desc, index asc) for the
next position given the tokens appended so far. Byte-exactness is the
contract (D-8: fp32-class replay); content_sha turns any desync that
reaches the end into a typed ValueError instead of a silently wrong file
(lockstep D-9 dual-hash pattern).

Pure core (encode_symbols / decode_core) is torch-free and tested as such;
the torch scorer/stepper are thin adapters.
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import Callable, Protocol

import numpy as np

from ..bits import BitReader, BitWriter, gamma_decode, gamma_encode
from ..codec import (MAGIC, VERSION, _int_field, header_digest, payload_digest)
from ..rac_codec import (CODERS, FLAG_A, FLAG_C, FLAG_T, FLAG_X, CoderParams, PayloadDecoder, PayloadEncoder,
                         classify)

KIND = "hf"
HF_REQUIRED = frozenset({"magic", "version", "kind", "model", "vocab_size", "prompt_ids", "length",
                         "n_corrections", "payload_bits", "fingerprint", "header_sha", "coder", "tie_margin",
                         "tie_topm", "max_rank", "payload_sha", "content_sha"})
MODEL_FIELDS = frozenset({"id", "snapshot", "dtype"})
MAX_PROMPT = 1 << 16
DEFAULT_TOPK = 128


def content_digest(tokens: np.ndarray) -> str:
    return hashlib.sha256(np.asarray(tokens, dtype=np.int32).tobytes()).hexdigest()[:16]


def hf_fingerprint(model: dict, vocab_size: int) -> str:
    """L0 pin: what must match for draft replay to reproduce."""
    blob = json.dumps({"model": model, "vocab_size": vocab_size}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def canonical_topk_row(val: np.ndarray, idx: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Re-sort one top-k row by (value desc, index asc) — the codec's stable order."""
    o = np.lexsort((idx, -val))
    return idx[o], val[o]


# ----------------------------------------------------------------------------
# pure core
# ----------------------------------------------------------------------------

def encode_symbols(ranks: np.ndarray, gaps: np.ndarray, topm_idx: np.ndarray | None, tokens: np.ndarray,
                   p: CoderParams) -> list[tuple[int, int]]:
    """Encoder-side symbol stream. topm_idx[t] = canonical top-m ids at t
    (only needed when tie_margin > 0)."""
    out = []
    for t in range(len(tokens)):
        r = int(ranks[t]); f = classify(r, float(gaps[t]), p)
        if f == FLAG_A:
            out.append((FLAG_A, 0))
        elif f == FLAG_C:
            out.append((FLAG_C, r))
        elif f == FLAG_T:
            s = np.sort(topm_idx[t][:p.tie_topm]); slot = int(np.searchsorted(s, tokens[t]))
            if slot >= len(s) or s[slot] != tokens[t]:
                raise ValueError("tie escape: true token not in the encoder's top-m set")
            out.append((FLAG_T, slot))
        else:
            out.append((FLAG_X, int(tokens[t])))
    return out


def symbols_to_payload(symbols: list[tuple[int, int]], coder: str, p: CoderParams) -> tuple[bytes, int]:
    if coder == "gamma":
        if p.tie_margin != 0:
            raise ValueError("gamma has no tie escape")
        w = BitWriter(); gap = 0
        for f, v in symbols:
            if f == FLAG_A:
                gap += 1; continue
            gamma_encode(w, gap + 1)
            if f == FLAG_C:
                gamma_encode(w, v - 1)
            else:                                   # X: rank beyond max_rank -> escape code 0 then raw id
                gamma_encode(w, p.max_rank); w.write_uint(v, p.vocab_bits)
            gap = 0
        return w.to_bytes(), w.n_bits
    enc = PayloadEncoder(p)
    for t, (f, v) in enumerate(symbols):
        enc.step(t, f, v)
    pay = enc.finish()
    return pay, 8 * len(pay)


def payload_to_symbols(payload: bytes, payload_bits: int, n: int, n_corr: int, coder: str, p: CoderParams) -> list[tuple[int, int]]:
    """Decode the symbol stream WITHOUT a model (self-check and gamma path)."""
    if coder == "gamma":
        r = BitReader(payload, payload_bits); out = [(FLAG_A, 0)] * n; pos = -1
        for _ in range(n_corr):
            gap = gamma_decode(r) - 1; code = gamma_decode(r); pos += gap + 1
            if pos >= n:
                raise ValueError("correction position beyond sequence length (corrupt payload)")
            if code == p.max_rank:
                out[pos] = (FLAG_X, r.read_uint(p.vocab_bits))
            elif 1 <= code < p.max_rank:
                out[pos] = (FLAG_C, code + 1)
            else:
                raise ValueError("correction rank out of range (corrupt payload)")
        return out
    dec = PayloadDecoder(payload, p)
    return [dec.step(t) for t in range(n)]


class Stepper(Protocol):
    def __call__(self, new_ids: list[int]) -> tuple[np.ndarray, np.ndarray]:
        """Append new_ids to the context; return canonical (idx, val) top-K for the NEXT token."""


def decode_core(symbols: list[tuple[int, int]], prompt_ids: list[int], stepper: Stepper, p: CoderParams,
                vocab_size: int, truth: np.ndarray | None = None) -> tuple[np.ndarray, int]:
    """Resolve symbols against the replayed draft. Returns (tokens, first_mismatch)
    where first_mismatch = -1 unless `truth` is given and a mismatch occurred
    (decoding then stops there: the context is already wrong)."""
    n = len(symbols); out = np.full(n, -1, dtype=np.int64)
    idx, val = stepper(list(prompt_ids))
    for t, (f, v) in enumerate(symbols):
        if f == FLAG_A:
            tok = int(idx[0])
        elif f == FLAG_C:
            if v - 1 >= len(idx):
                raise ValueError("rank beyond the stepper's top-K (raise DEFAULT_TOPK)")
            tok = int(idx[v - 1])
        elif f == FLAG_T:
            tok = int(np.sort(idx[:p.tie_topm])[v])
        else:
            if v >= vocab_size:
                raise ValueError("raw token id beyond vocabulary (corrupt payload)")
            tok = v
        out[t] = tok
        if truth is not None and tok != int(truth[t]):
            return out, t
        if t + 1 < n:
            idx, val = stepper([tok])
    return out, -1


# ----------------------------------------------------------------------------
# archive build / parse
# ----------------------------------------------------------------------------

def build_archive(model: dict, vocab_size: int, prompt_ids, tokens: np.ndarray, symbols, coder: str,
                  p: CoderParams) -> bytes:
    if coder not in CODERS:
        raise ValueError(f"unknown coder {coder!r}")
    payload, payload_bits = symbols_to_payload(symbols, coder, p)
    header = {
        "magic": MAGIC, "version": VERSION, "kind": KIND,
        "model": {k: model[k] for k in ("id", "snapshot", "dtype")}, "vocab_size": int(vocab_size),
        "prompt_ids": [int(x) for x in prompt_ids], "length": int(len(tokens)),
        "n_corrections": int(sum(1 for f, _ in symbols if f != FLAG_A)),
        "payload_bits": int(payload_bits), "coder": coder, "tie_margin": float(p.tie_margin),
        "tie_topm": int(p.tie_topm), "max_rank": int(p.max_rank),
        "payload_sha": payload_digest(payload), "content_sha": content_digest(tokens),
        "fingerprint": hf_fingerprint({k: model[k] for k in ("id", "snapshot", "dtype")}, vocab_size),
    }
    header["header_sha"] = header_digest(header)
    hj = json.dumps(header, sort_keys=True).encode()
    return MAGIC.encode() + len(hj).to_bytes(4, "big") + hj + payload


def validate_hf_header(h: dict, payload: bytes, max_length: int = 1 << 24) -> CoderParams:
    missing = HF_REQUIRED - set(h)
    if missing:
        raise ValueError(f"hf header missing fields {sorted(missing)}")
    extra = set(h) - HF_REQUIRED
    if extra:
        raise ValueError(f"hf header has unknown fields {sorted(extra)}")
    if h["magic"] != MAGIC or h["version"] != VERSION or isinstance(h["version"], bool) or h["kind"] != KIND:
        raise ValueError("hf header magic/version/kind mismatch")
    m = h["model"]
    if not isinstance(m, dict) or set(m) != MODEL_FIELDS or not isinstance(m["id"], str) or not isinstance(m["dtype"], str) \
            or not (m["snapshot"] is None or isinstance(m["snapshot"], str)):
        raise ValueError("hf header model must be {id: str, snapshot: str|null, dtype: str}")
    vocab = _int_field(h, "vocab_size", 2, 1 << 24)
    length = _int_field(h, "length", 0, max_length)
    _int_field(h, "n_corrections", 0, length)
    _int_field(h, "payload_bits", 0, 8 * len(payload))
    _int_field(h, "tie_topm", 2, 1 << 10); _int_field(h, "max_rank", 2, vocab)
    pids = h["prompt_ids"]
    if not isinstance(pids, list) or len(pids) > MAX_PROMPT or any(isinstance(x, bool) or not isinstance(x, int) or not (0 <= x < vocab) for x in pids):
        raise ValueError("hf header prompt_ids must be a list of token ids within the vocabulary")
    for key in ("fingerprint", "header_sha", "payload_sha", "content_sha"):
        fp = h[key]
        if not (isinstance(fp, str) and len(fp) == 16 and all(c in "0123456789abcdef" for c in fp)):
            raise ValueError(f"header {key} must be 16 lowercase hex chars")
    if h["header_sha"] != header_digest(h):
        raise ValueError("header_sha mismatch (corrupt or tampered header)")
    if h["payload_sha"] != payload_digest(payload):
        raise ValueError("payload_sha mismatch (corrupt payload)")
    if h["fingerprint"] != hf_fingerprint(m, vocab):
        raise ValueError("header fingerprint mismatch (tampered or corrupt header)")
    if h["coder"] not in CODERS:
        raise ValueError(f"unknown coder {h['coder']!r}")
    tm = h["tie_margin"]
    if isinstance(tm, bool) or not isinstance(tm, (int, float)) or not math.isfinite(tm) or tm < 0 or (h["coder"] == "gamma" and tm != 0):
        raise ValueError("bad tie_margin")
    return CoderParams(tie_margin=float(tm), tie_topm=h["tie_topm"], max_rank=h["max_rank"],
                       vocab_bits=max(1, (vocab - 1).bit_length()))


def parse_archive(data: bytes) -> tuple[dict, bytes, CoderParams]:
    from ..codec import MAX_HEADER_BYTES, _parse_header
    if not isinstance(data, (bytes, bytearray)):
        raise ValueError("archive must be bytes")
    data = bytes(data)
    if len(data) < 8 or data[:4] != MAGIC.encode():
        raise ValueError("not an amber archive (bad magic or truncated framing)")
    hlen = int.from_bytes(data[4:8], "big")
    if hlen > MAX_HEADER_BYTES or 8 + hlen > len(data):
        raise ValueError("bad header length")
    header = _parse_header(data[8:8 + hlen]); payload = data[8 + hlen:]
    if header.get("kind") != KIND:
        raise ValueError("not an hf-kind archive")
    p = validate_hf_header(header, payload)
    return header, payload, p


def decode_archive(data: bytes, make_stepper: Callable[[], Stepper], expected_fingerprint: str | None = None,
                   truth: np.ndarray | None = None) -> tuple[np.ndarray, int, list[tuple[int, int]]]:
    """Draft-only decode. Verifies content_sha at the end (ValueError on any
    desync) unless `truth` is given (experiment mode: stop at first mismatch)."""
    h, payload, p = parse_archive(data)
    if expected_fingerprint is not None and h["fingerprint"] != expected_fingerprint:
        raise ValueError("archive is not pinned to the expected draft")
    symbols = payload_to_symbols(payload, h["payload_bits"], h["length"], h["n_corrections"], h["coder"], p)
    tokens, first = decode_core(symbols, h["prompt_ids"], make_stepper(), p, h["vocab_size"], truth)
    if truth is None and content_digest(tokens) != h["content_sha"]:
        raise ValueError("content_sha mismatch: draft replay did not reproduce the archived content (desync)")
    return tokens, first, symbols


# ----------------------------------------------------------------------------
# v3 binary archives (one stream: prompt segment + content segment)
# ----------------------------------------------------------------------------

def build_binary_archive(model: dict, vocab_size: int, all_ids: np.ndarray, prompt_len: int,
                         symbols, coder: str, p: CoderParams) -> bytes:
    """all_ids = prompt + generated; symbols cover positions 1..len(all_ids)-1
    (the prompt's tail then the content), each scored against the draft."""
    from ..binformat import pack
    if len(symbols) != len(all_ids) - 1:
        raise ValueError("symbols must cover every position after the first token")
    payload, _bits = symbols_to_payload(symbols, coder, p)
    return pack(model_id=model["id"], snapshot=model["snapshot"], dtype=model["dtype"],
                fingerprint8=bytes.fromhex(hf_fingerprint({k: model[k] for k in ("id", "snapshot", "dtype")}, vocab_size)),
                vocab_size=vocab_size, coder=coder, p=p, first_token=int(all_ids[0]), prompt_len=int(prompt_len),
                length=int(len(all_ids) - prompt_len), n_corrections=sum(1 for f, _ in symbols if f != FLAG_A),
                payload=payload, content_sha8=bytes.fromhex(content_digest(all_ids)))


def decode_binary_archive(data: bytes, make_stepper: Callable[[], Stepper], expected_fingerprint: str | None = None,
                          truth: np.ndarray | None = None) -> tuple[np.ndarray, int, list[tuple[int, int]]]:
    """Draft-only decode of a v3 archive: the prompt segment is DECODED (from
    the first token on), not fed. `truth`, when given (experiment mode), is
    the full sequence including the first token; decoding stops at the first
    mismatch. Returns (all_ids, first_mismatch_pos_in_stream, symbols)."""
    from ..binformat import unpack
    h, payload, p = unpack(data)
    if h["fingerprint8"] != bytes.fromhex(hf_fingerprint(h["model"], h["vocab_size"])):
        raise ValueError("header fingerprint mismatch (tampered or corrupt header)")
    if expected_fingerprint is not None and h["fingerprint8"] != bytes.fromhex(expected_fingerprint):
        raise ValueError("archive is not pinned to the expected draft")
    n = (h["prompt_len"] - 1) + h["length"]
    symbols = payload_to_symbols(payload, h["payload_bits"], n, h["n_corrections"], h["coder"], p)
    rest, first = decode_core(symbols, [h["first_token"]], make_stepper(), p, h["vocab_size"],
                              None if truth is None else np.asarray(truth)[1:])
    all_ids = np.concatenate([[h["first_token"]], rest])
    if truth is None and bytes.fromhex(content_digest(all_ids)) != h["content_sha8"]:
        raise ValueError("content_sha mismatch: draft replay did not reproduce the archived content (desync)")
    return all_ids, first, symbols


# ----------------------------------------------------------------------------
# v4 session archives (one pin/digest set, k turns; see P6_PROTOCOL.md)
# ----------------------------------------------------------------------------

def session_symbol_count(turns: list[dict], ctx_mode: int) -> int:
    return sum(t["prompt_len"] + t["gen_len"] - (1 if (ctx_mode == 0 or i == 0) else 0)
               for i, t in enumerate(turns))


def build_session_archive(model: dict, vocab_size: int, turns: list[dict], all_ids: np.ndarray,
                          symbols, coder: str, p: CoderParams, ctx_mode: int) -> bytes:
    """turns = [{prompt_len, gen_len, first_token}] in session order; all_ids =
    the full session token sequence (for content_sha); symbols = flat coded
    stream (per-turn positions 1.. for ctx_mode 0; session positions 1.. for
    ctx_mode 1, where turns >= 2 have their first token coded from history)."""
    from ..binformat import pack_session
    if len(symbols) != session_symbol_count(turns, ctx_mode):
        raise ValueError("symbol count does not match the turn table")
    if len(all_ids) != sum(t["prompt_len"] + t["gen_len"] for t in turns):
        raise ValueError("all_ids length does not match the turn table")
    payload, _bits = symbols_to_payload(symbols, coder, p)
    return pack_session(model_id=model["id"], snapshot=model["snapshot"], dtype=model["dtype"],
                        fingerprint8=bytes.fromhex(hf_fingerprint({k: model[k] for k in ("id", "snapshot", "dtype")}, vocab_size)),
                        vocab_size=vocab_size, coder=coder, p=p, ctx_mode=ctx_mode, turns=turns,
                        n_corrections=sum(1 for f, _ in symbols if f != FLAG_A),
                        payload=payload, content_sha8=bytes.fromhex(content_digest(all_ids)))


def decode_session_archive(data: bytes, make_stepper: Callable[[], Stepper],
                           expected_fingerprint: str | None = None,
                           truth: np.ndarray | None = None) -> tuple[np.ndarray, int, list[tuple[int, int]]]:
    """Draft-only session decode. ctx_mode 0 replays each turn from its own
    first token with a FRESH stepper (a desync is confined to its turn);
    ctx_mode 1 replays the whole session in one context. Returns (all_ids,
    first_mismatch_coded_pos, symbols); truth (full session ids) stops at the
    first mismatch, else content_sha is verified at the end."""
    from ..binformat import CTX_RESET, unpack_session
    h, payload, p = unpack_session(data)
    if h["fingerprint8"] != bytes.fromhex(hf_fingerprint(h["model"], h["vocab_size"])):
        raise ValueError("header fingerprint mismatch (tampered or corrupt header)")
    if expected_fingerprint is not None and h["fingerprint8"] != bytes.fromhex(expected_fingerprint):
        raise ValueError("archive is not pinned to the expected draft")
    symbols = payload_to_symbols(payload, h["payload_bits"], h["n_symbols"], h["n_corrections"], h["coder"], p)
    truth = None if truth is None else np.asarray(truth)
    if h["ctx_mode"] != CTX_RESET:
        # shared context: the turn table is metadata; replay is one stream
        ft = h["turns"][0]["first_token"]
        toks, first = decode_core(symbols, [ft], make_stepper(), p, h["vocab_size"],
                                  None if truth is None else truth[1:])
        all_out = np.concatenate([[ft], toks[:len(symbols) if first < 0 else first + 1]])
    else:
        out_parts: list[np.ndarray] = []
        spos = 0                                  # position in the symbol stream
        tpos = 0                                  # position in the session token sequence
        first = -1
        for t in h["turns"]:
            n_here = t["prompt_len"] + t["gen_len"] - 1
            seg = symbols[spos:spos + n_here]
            tr = None if truth is None else truth[tpos + 1:tpos + 1 + n_here]
            toks, f = decode_core(seg, [t["first_token"]], make_stepper(), p, h["vocab_size"], tr)
            out_parts.append(np.concatenate([[t["first_token"]], toks[:n_here if f < 0 else f + 1]]))
            if f >= 0:
                first = spos + f
                break
            spos += n_here
            tpos += n_here + 1
        all_out = np.concatenate(out_parts) if out_parts else np.zeros(0, np.int64)
    if truth is None and first < 0 and bytes.fromhex(content_digest(all_out)) != h["content_sha8"]:
        raise ValueError("content_sha mismatch: draft replay did not reproduce the archived session (desync)")
    return all_out, first, symbols


# ----------------------------------------------------------------------------
# torch adapters
# ----------------------------------------------------------------------------

def make_hf_scorer(model, device: str, topm: int = 2):
    """Teacher-forced full forward: per generated position -> stable rank,
    top-2 gap, canonical top-m ids. Same math as divergence.make_scorer."""
    import torch

    @torch.inference_mode()
    def score(ids: np.ndarray, prompt_len: int) -> dict:
        x = torch.as_tensor(ids[None, :], dtype=torch.long, device=device)
        logits = model(input_ids=x, use_cache=False).logits[0].float()
        pred = logits[prompt_len - 1:-1]
        if not torch.isfinite(pred).all():
            raise ValueError("non-finite logits (refusing to encode)")
        true = torch.as_tensor(ids[prompt_len:], dtype=torch.long, device=device)
        lt = pred.gather(1, true[:, None])
        greater = (pred > lt).sum(1)
        idx = torch.arange(pred.shape[1], device=device)[None, :]
        tie_before = ((pred == lt) & (idx < true[:, None])).sum(1)
        rank = 1 + greater + tie_before
        k = max(topm, 2) + 8
        val, tid = torch.topk(pred, k, dim=1)
        val = val.cpu().numpy(); tid = tid.cpu().numpy().astype(np.int64)
        topm_idx = np.stack([canonical_topk_row(val[i], tid[i])[0][:topm] for i in range(len(val))]) if len(val) else np.zeros((0, topm), np.int64)
        gap = val[:, 0] - val[:, 1] if len(val) else np.zeros(0, np.float32)
        return {"rank": rank.cpu().numpy().astype(np.int64), "gap": gap.astype(np.float32), "topm_idx": topm_idx}
    return score


def make_hf_scorer_chunked(model, device: str, topm: int = 2, chunk: int = 512, logq: bool = False):
    """Teacher-forced scoring of an ARBITRARILY long sequence in KV chunks
    (caps logit memory at chunk x V). Positions score ids[1:]. Same math as
    make_hf_scorer; the chunked-vs-full kernel split is inside the measured
    fp32 contract (F-11: 0 desyncs across kernel paths). logq=True adds
    log2 q(true) per position: measurement-only output for the
    AC-under-draft baseline (D-6); never read by the format (D-8)."""
    import torch

    @torch.inference_mode()
    def score(ids: np.ndarray) -> dict:
        L = len(ids)
        ranks, gaps, topms, l2qs = [], [], [], []
        past = None
        for start in range(0, L - 1, chunk):
            piece = ids[start:start + chunk]
            out = model(input_ids=torch.as_tensor(piece[None, :], dtype=torch.long, device=device),
                        past_key_values=past, use_cache=True)
            past = out.past_key_values
            pred = out.logits[0].float()
            n_t = min(len(piece), L - 1 - start)
            pred = pred[:n_t]
            if not torch.isfinite(pred).all():
                raise ValueError("non-finite logits (refusing to encode)")
            true = torch.as_tensor(ids[start + 1:start + 1 + n_t], dtype=torch.long, device=device)
            lt = pred.gather(1, true[:, None])
            greater = (pred > lt).sum(1)
            idxr = torch.arange(pred.shape[1], device=device)[None, :]
            tie_before = ((pred == lt) & (idxr < true[:, None])).sum(1)
            ranks.append((1 + greater + tie_before).cpu().numpy().astype(np.int64))
            if logq:
                lsm = torch.log_softmax(pred, dim=1)
                l2qs.append((lsm.gather(1, true[:, None])[:, 0] / np.log(2.0)).cpu().numpy().astype(np.float32))
            k = max(topm, 2) + 8
            val, tid = torch.topk(pred, k, dim=1)
            val = val.cpu().numpy(); tid = tid.cpu().numpy().astype(np.int64)
            gaps.append((val[:, 0] - val[:, 1]).astype(np.float32))
            topms.append(np.stack([canonical_topk_row(val[i], tid[i])[0][:topm] for i in range(len(val))]))
        out = {"rank": np.concatenate(ranks), "gap": np.concatenate(gaps), "topm_idx": np.concatenate(topms)}
        if logq:
            out["log2q"] = np.concatenate(l2qs)
        return out
    return score


def make_torch_stepper(model, device: str, topk: int = DEFAULT_TOPK) -> Callable[[], Stepper]:
    """Factory of incremental (KV-cache) steppers, batch 1, canonical top-K."""
    import torch

    def factory() -> Stepper:
        state = {"past": None}

        @torch.inference_mode()
        def step(new_ids: list[int]):
            x = torch.as_tensor([new_ids], dtype=torch.long, device=device)
            out = model(input_ids=x, past_key_values=state["past"], use_cache=True)
            state["past"] = out.past_key_values
            logits = out.logits[0, -1].float()
            if not torch.isfinite(logits).all():
                raise ValueError("non-finite logits during decode")
            val, idx = torch.topk(logits, topk)
            return canonical_topk_row(val.cpu().numpy(), idx.cpu().numpy().astype(np.int64))
        return step
    return factory
