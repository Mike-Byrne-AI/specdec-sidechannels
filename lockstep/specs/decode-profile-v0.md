# Decode profile `lsp0` — normative

A decode profile is the exact arithmetic of decompression, written down. Two
independent implementations of `lsp0` MUST produce bit-identical payloads for
identical inputs and MUST reproduce `conformance/vectors_v0.json`.

## Integer and byte-input contract

All coder, CDF, symbol, count, size, and quantizer-total inputs described as
integers MUST be exact integers; booleans and floating-point values are not
accepted as integer substitutes. Symbols are integers in the selected
alphabet. Byte inputs are one-dimensional byte sequences.

A malformed API input or impossible coder state MUST fail explicitly rather
than being silently coerced. This strictness is part of the reference API trust
boundary; it does not alter any conforming payload bitstream.

## Coder (`rac.py`)

Witten–Neal–Cleary binary arithmetic coder:

- `CODE_BITS = 32`; `HALF = 2^31`; `QUARTER = 2^30`;
  `THREE_QUARTERS = 3*2^30`.
- For cumulative interval `[c_lo, c_hi)` with total `total`, require
  `0 <= c_lo < c_hi <= total` and `0 < total <= 2^16`.
- Interval update, in this order, on unbounded exact integers:
  `span = high - low + 1`;
  `high' = low + floor(span*c_hi/total) - 1`;
  `low' = low + floor(span*c_lo/total)`.
- Renormalisation: emit `0` while `high < HALF`; emit `1` and subtract
  `HALF` from `low/high` while `low >= HALF`; increment pending bits and
  subtract `QUARTER` while
  `QUARTER <= low && high < THREE_QUARTERS`. After each case,
  `low <<= 1` and `high = (high << 1) | 1`. Emitting bit `b` flushes every
  pending bit as `1-b`.
- `finish()` increments pending bits, then emits `0` when `low < QUARTER`,
  otherwise `1`, including the pending-bit flush. The final physical byte is
  zero-padded in its unused least-significant positions.
- The decoder initialises `value` from the first 32 bits, reading zero bits
  past physical end-of-stream. It computes
  `target = floor((((value-low)+1)*total - 1)/span)` and mirrors the encoder's
  renormalisation, additionally transforming `value` and pulling one bit per
  shift.
- Every symbol frequency is at least 1.

An implementation MAY buffer or stream input and output. For a given byte
sequence and fresh model state, streaming and in-memory encoding MUST produce
identical payload bytes. Streaming decode MUST produce the same exact symbol
sequence as in-memory decode.

## Alphabet and framing

Symbols are raw bytes `0..255`. There is no EOF symbol. The symbol count comes
from the container's validated `original.size` field.

## Models

### `adaptive-order1`

The exact model profile is:

```json
{"alphabet":256,"increment":24,"model":"adaptive-order1","rescale_limit":32768}
```

Maintain one count row for each previous-byte context `0..255`. The initial
context is byte `0`. Every one of the 256 counts in every row starts at `1`.
At coding time, the CDF is the running prefix sum of the current context row.
After coding symbol `s` in context `c`, increment `count[c][s]` by `24`. If the
row total then exceeds `32768`, replace every count in that row by
`max(1, (count + 1) >> 1)` and recompute the total. Finally, set the context to
`s`.

Encoder and decoder MUST update at the identical point: after encoding or
decoding each symbol.

### `uniform`

The exact model profile is:

```json
{"alphabet":256,"model":"uniform"}
```

Every byte has static frequency `1`, so total is `256`. `update` has no effect.

## Integer weight quantizer

`quantize_weights(weights, total)` reserves one unit per symbol. It distributes
`budget = total - n` as
`floor(weights[i] * budget / sum(weights))`, then gives one extra unit to the
`budget - sum(floors)` largest exact remainders
`(weights[i] * budget) mod sum(weights)`, breaking ties by lowest symbol index.
It uses exact integer arithmetic only. Zero-sum weights are treated as equal
unit weights. Require `n <= total <= 2^16`, non-negative integer weights, and
at least one symbol.

`quantize_probs` is a research convenience, not a source of cross-platform
model probabilities for `lsp0`. It rejects booleans, negative values, and all
non-finite inputs; callers remain responsible for supplying identical finite
floating-point values.

## Conformance

An implementation claims `lsp0` only when, for every case in
`conformance/vectors_v0.json`, it reproduces the exact `payload_size` and
`payload_sha256` while encoding and reproduces the exact original bytes and
`original_sha256` while decoding. Vector replacement is a format break; see
`specs/conformance-v0.md`.
