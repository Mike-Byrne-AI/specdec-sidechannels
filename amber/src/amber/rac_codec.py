"""amber v2 payload coder: adaptive integer arithmetic coding of the
(flag, rank) stream over lockstep's range coder (D-7 import: lockstep.rac is
the coder, lockstep.cdf the table; only the symbol grammar and a small-
alphabet adaptive frequency model live here).

Symbol grammar, one flag per position (see experiments/P3_PROTOCOL.md):

    A  agree          rank 1, encoder top-2 gap >= tie_margin      -> nothing
    C  correction     2 <= rank <= max_rank                         -> rank
    T  tie escape     gap < tie_margin and rank <= tie_topm         -> slot among
                      the top-m tokens sorted by INDEX (uniform bits)
    X  raw            rank > max_rank                               -> token id

Determinism posture (PMATIC's warning, D-2, D-5): every probability the coder
uses is a function of the CODED SYMBOL HISTORY and the position — never of a
logit value — so a decoder whose draft is merely rank-stable reproduces the
coder state exactly. The tie escape is decided by the ENCODER's gap and read
by the decoder as a symbol; the decoder never evaluates a threshold. It makes
the archive robust to any reordering inside the top-m set at escaped
positions, which is the whole of F-5/F-7's bf16 drift at top-1. Ranks 2..R
still rely on order stability at that depth (measured in p2b), and X is
robust by construction.

`extra_ctx` is a research-only hook (P3 variant `rac1_qctx`) that lets an
experiment add a value-derived context to the flag model to MEASURE its gain;
a decoder cannot reproduce such a context under drift, so the codec itself
never sets it (codec.py always passes 0).
"""

from __future__ import annotations

from dataclasses import dataclass

from lockstep.cdf import Cdf
from lockstep.errors import CoderError
from lockstep.rac import RangeDecoder, RangeEncoder

FLAG_A, FLAG_C, FLAG_T, FLAG_X = 0, 1, 2, 3
N_FLAGS = 4
FLAG_NAMES = ("A", "C", "T", "X")
N_POS_BUCKETS = 4            # position bucket = min(t >> 6, 3): F-8's front-loading
MANTISSA_ADAPTIVE_BITS = 4   # rank mantissas of <= 4 bits get their own adaptive model
CODERS = ("gamma", "rac1")


@dataclass(frozen=True)
class CoderParams:
    tie_margin: float = 0.0      # 0 => no tie escape (T never emitted)
    tie_topm: int = 2            # size of the index-sorted set a T slot indexes
    max_rank: int = 64           # ranks beyond this are X (raw id)
    vocab_bits: int = 17         # ceil(log2 V) for X symbols
    increment: int = 32          # adaptive model step
    rescale_limit: int = 1 << 15 # halve counts when total exceeds this
    n_extra_ctx: int = 1         # research hook (see module docstring)

    def __post_init__(self):
        if not (isinstance(self.tie_margin, (int, float)) and self.tie_margin >= 0):
            raise ValueError("tie_margin must be >= 0")
        if self.tie_topm < 2 or self.max_rank < 2 or self.vocab_bits < 1:
            raise ValueError("tie_topm, max_rank must be >= 2; vocab_bits >= 1")
        if self.increment < 1 or not (N_FLAGS <= self.rescale_limit <= (1 << 16)):
            raise ValueError("increment >= 1; rescale_limit in [4, 2^16]")
        if self.n_extra_ctx < 1:
            raise ValueError("n_extra_ctx >= 1")

    @property
    def n_buckets(self) -> int:
        return (self.max_rank - 1).bit_length()


def classify(rank: int, gap: float, p: CoderParams) -> int:
    """Encoder-side flag decision. `gap` is the encoder draft's top-2 logit
    gap at this position; the decoder never sees it."""
    if rank < 1:
        raise ValueError("rank is 1-based")
    if p.tie_margin > 0 and gap < p.tie_margin and rank <= p.tie_topm:
        return FLAG_T
    if rank == 1:
        return FLAG_A
    if rank <= p.max_rank:
        return FLAG_C
    return FLAG_X


class AdaptiveModel:
    """Order-0 adaptive frequency model over a small alphabet, all-integer
    (the same count/halve scheme as lockstep's AdaptiveByteModel, which is
    fixed to a 256-symbol alphabet and so cannot be used directly)."""

    __slots__ = ("_f", "_total", "_inc", "_limit", "_cdf")

    def __init__(self, n: int, increment: int, rescale_limit: int):
        if n < 1 or n > rescale_limit:
            raise ValueError("alphabet must fit under rescale_limit")
        self._f = [1] * n
        self._total = n
        self._inc = increment
        self._limit = rescale_limit
        self._cdf: Cdf | None = None

    def cdf(self) -> Cdf:
        if self._cdf is None:
            self._cdf = Cdf.from_freqs(self._f)
        return self._cdf

    def update(self, sym: int) -> None:
        self._f[sym] += self._inc
        self._total += self._inc
        if self._total > self._limit:
            self._f = [max(1, (v + 1) >> 1) for v in self._f]
            self._total = sum(self._f)
        self._cdf = None


class _Models:
    def __init__(self, p: CoderParams):
        mk = lambda n: AdaptiveModel(n, p.increment, p.rescale_limit)  # noqa: E731
        self.flag = [mk(N_FLAGS) for _ in range(N_FLAGS * N_POS_BUCKETS * p.n_extra_ctx)]
        self.bucket = mk(p.n_buckets)
        self.mantissa = {b: mk(1 << b) for b in range(1, min(MANTISSA_ADAPTIVE_BITS, p.n_buckets - 1) + 1)}

    @staticmethod
    def flag_ctx(prev: int, t: int, extra: int, p: CoderParams) -> int:
        if not (0 <= extra < p.n_extra_ctx):
            raise ValueError("extra_ctx out of range")
        return (prev * N_POS_BUCKETS + min(t >> 6, N_POS_BUCKETS - 1)) * p.n_extra_ctx + extra


class PayloadEncoder:
    def __init__(self, p: CoderParams):
        self.p = p
        self._enc = RangeEncoder()
        self._m = _Models(p)
        self._prev = FLAG_A
        self.n_symbols = 0
        self.ideal_bits = 0.0     # sum of -log2 p over coded symbols (cost attribution)
        self._finished = False

    # -- primitives ---------------------------------------------------------
    def _sym(self, model: AdaptiveModel, sym: int) -> None:
        import math
        lo, hi, tot = model.cdf().interval(sym)
        self._enc.encode(lo, hi, tot)
        self.ideal_bits += math.log2(tot / (hi - lo))
        model.update(sym)

    def _bits(self, value: int, width: int) -> None:
        for i in range(width - 1, -1, -1):
            b = (value >> i) & 1
            self._enc.encode(b, b + 1, 2)
        self.ideal_bits += width

    # -- grammar ------------------------------------------------------------
    def step(self, t: int, flag: int, value: int = 0, extra_ctx: int = 0) -> None:
        """Code position t (document position; used only as context). value =
        rank (C), index slot (T), token id (X)."""
        if self._finished:
            raise ValueError("step() after finish()")
        if not isinstance(t, int) or t < 0:
            raise ValueError("position must be a non-negative int (a context value both sides supply)")
        p = self.p
        if flag not in (FLAG_A, FLAG_C, FLAG_T, FLAG_X):
            raise ValueError("bad flag")
        self._sym(self._m.flag[_Models.flag_ctx(self._prev, t, extra_ctx, p)], flag)
        if flag == FLAG_C:
            if not (2 <= value <= p.max_rank):
                raise ValueError("C rank must be in [2, max_rank]")
            u = value - 1
            b = u.bit_length() - 1
            self._sym(self._m.bucket, b)
            if b in self._m.mantissa:
                self._sym(self._m.mantissa[b], u - (1 << b))
            elif b > 0:
                self._bits(u - (1 << b), b)
        elif flag == FLAG_T:
            if p.tie_margin <= 0:
                raise ValueError("T emitted with tie_margin 0")
            if not (0 <= value < p.tie_topm):
                raise ValueError("T slot out of range")
            self._bits(value, (p.tie_topm - 1).bit_length())
        elif flag == FLAG_X:
            if not (0 <= value < (1 << p.vocab_bits)):
                raise ValueError("X token id does not fit vocab_bits")
            self._bits(value, p.vocab_bits)
        self._prev = flag
        self.n_symbols += 1

    def finish(self) -> bytes:
        self._finished = True
        return self._enc.finish()


class PayloadDecoder:
    def __init__(self, payload: bytes, p: CoderParams):
        self.p = p
        try:
            self._dec = RangeDecoder(payload)
        except CoderError as exc:
            raise ValueError(f"payload unreadable: {exc}") from None
        self._m = _Models(p)
        self._prev = FLAG_A

    def _sym(self, model: AdaptiveModel) -> int:
        cdf = model.cdf()
        tgt = self._dec.decode_target(cdf.total)
        sym = cdf.find(tgt)
        self._dec.update(*cdf.interval(sym))
        model.update(sym)
        return sym

    def _bits(self, width: int) -> int:
        v = 0
        for _ in range(width):
            b = self._dec.decode_target(2)
            self._dec.update(b, b + 1, 2)
            v = (v << 1) | b
        return v

    def step(self, t: int, extra_ctx: int = 0) -> tuple[int, int]:
        """Returns (flag, value) for position t. Every coder-level failure
        surfaces as ValueError (typed, loud)."""
        if not isinstance(t, int) or t < 0:
            raise ValueError("position must be a non-negative int (a context value both sides supply)")
        p = self.p
        try:
            flag = self._sym(self._m.flag[_Models.flag_ctx(self._prev, t, extra_ctx, p)])
            value = 0
            if flag == FLAG_C:
                b = self._sym(self._m.bucket)
                if b in self._m.mantissa:
                    man = self._sym(self._m.mantissa[b])
                elif b > 0:
                    man = self._bits(b)
                else:
                    man = 0
                value = (1 << b) + man + 1
                if value > p.max_rank:
                    raise ValueError("decoded rank beyond max_rank (corrupt payload)")
            elif flag == FLAG_T:
                if p.tie_margin <= 0:
                    raise ValueError("T symbol in an archive without tie escapes (corrupt payload)")
                value = self._bits((p.tie_topm - 1).bit_length())
                if value >= p.tie_topm:
                    raise ValueError("T slot out of range (corrupt payload)")
            elif flag == FLAG_X:
                value = self._bits(p.vocab_bits)
        except CoderError as exc:
            raise ValueError(f"range decoder failure (corrupt payload): {exc}") from None
        self._prev = flag
        return flag, value


def encode_stream(symbols, p: CoderParams, extra_ctx=None) -> tuple[bytes, float]:
    """Convenience: symbols = iterable of (flag, value); returns (payload, ideal_bits)."""
    enc = PayloadEncoder(p)
    for t, (flag, value) in enumerate(symbols):
        enc.step(t, flag, value, 0 if extra_ctx is None else int(extra_ctx[t]))
    return enc.finish(), enc.ideal_bits


def decode_stream(payload: bytes, n: int, p: CoderParams, extra_ctx=None) -> list[tuple[int, int]]:
    dec = PayloadDecoder(payload, p)
    return [dec.step(t, 0 if extra_ctx is None else int(extra_ctx[t])) for t in range(n)]
