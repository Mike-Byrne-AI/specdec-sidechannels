# Emergent synthesis — findings only visible by comparing findings

No new experiments. Everything here comes from crossing existing findings,
decisions, prior art, and task packs against each other. Four of the joins
are load-bearing enough to change the project's plan; one closes an open
question for free; one is a methodology lesson worth keeping.

## The chain, in one paragraph

The v0 trust base was measured on a **256-symbol byte alphabet with a 2^15
grid** (F-1, F-2). TP-1 plans to drive it with an **LLM vocabulary of
32k–256k tokens**. Those two facts have never been in the same room. Put
them there and the coder's `TOTAL_MAX = 2^16` turns out to *forbid* modern
vocabularies outright (F-5). Fix that constant and a deeper problem
appears: the grid resolution needed for ratio and the grid coarseness
needed to absorb drift are **mutually exclusive** at LLM scale (F-6) —
F-2's drift sponge only worked because 128 symbols is not 128,256. That
kills the probability-space grid, which answers OQ-4 by elimination and
forces a logit-space, top-k design whose correction rate obeys a clean law
(F-7). Meanwhile, pricing the cost model to honor the project's own
CPU-decode decision (D-10) reveals that **packing is 92% of all cost** and
needs a ~100x throughput miracle to break even — which no lever in the repo
provides, but which vanishes entirely if packing is a byproduct of
inference someone is already running (F-8).

## EF-1 → F-5. The coder ceiling forbids the product

`TOTAL_MAX = 2^16 = 65,536`, and `quantize_weights` must give every symbol
≥1 unit. Therefore:

| vocab | fits 2^16? | units/symbol | floor mass forced onto tail |
|---|---|---|---|
| 256 (v0 bytes) | yes | 256 | 0.4% |
| 32,768 (Mistral) | barely | **2.0** | **50.0%** |
| 50,257 (GPT-2) | barely | 1.3 | 76.7% |
| 128,256 (Llama-3) | **no — hard CoderError** | — | — |
| 151,936 / 256,128 | **no** | — | — |

Half the probability mass of a 32k-vocab model is consumed by the mandatory
≥1 floor before the model says anything. Measured excess: **0.999 bits/token
wasted on a distribution whose entire entropy is 3.03 bits** — a ~33% ratio
loss, on the vocab that *fits*. The rest don't build a CDF at all.

The good news: the constant is **not load-bearing**. The WNC invariant
guarantees range > QUARTER = 2^30 after renormalization, so total ≤ 2^30 is
safe at CODE_BITS=32 — verified by round-tripping at 2^16, 2^20, 2^24, 2^28,
2^30. `PROB_BITS_MAX` is conservative by 14 bits. The fix is a constant; the
cost is that it is a **format break** (D-9), which is cheap today and
expensive the moment anyone else holds a vector file.

## EF-2 → F-6. The drift sponge does not scale (the squeeze)

F-2's headline — "the grid absorbs drift" — was measured at V=128. Re-run at
LLM scale with PA-3's drift class (ε≈1e-7):

| V | grid | CDF identical under drift | excess bits (% of entropy) |
|---|---|---|---|
| 32,768 | 2^15 | **24/24 absorbs** | 11.97 (**394%**) |
| 32,768 | 2^20 | 0/24 | 0.046 (1.5%) |
| 128,256 | 2^20 | 0/24 | 0.188 (6.2%) |
| 128,256 | 2^24 | 0/24 | 0.011 (0.4%) |

The one configuration that absorbs drift does so **by lobotomy** — the grid
is so coarse it has already destroyed 394% of the distribution's entropy, so
of course perturbation can't change it. Every configuration that preserves
ratio desyncs on **every token**.

- Ratio needs T ≥ 2^24 at LLM vocab.
- Absorbing 1e-7 drift needs step >> 1e-7, i.e. T << 2^23.
- **The windows do not overlap.**

Consequences: D-8's safeguard side-stream is not a sparse backstop for edge
cases — under the current design it would fire on ~100% of tokens, which
means transmitting the model's decisions and defeating the entire purpose.
E-004's "stop if overhead > 10%" would trip on token one. And **OQ-4 is
answered by elimination: the grid cannot live in probability space.**

## EF-3 → F-7. The correction-rate law (the constructive way out)

The squeeze exists because the probability CDF is a *global* function of all
V logits — every one of 128k remainders is a chance to flip. Move the
quantization into **logit space** and truncate to **top-k**, and the drift
surface collapses from V to k, gated by the logit step δ:

**correction_rate ≈ k · ε / δ**

Measured against theory (fresh continuous logits per trial, ε=1e-7, k=64):

| logit step δ | measured | predicted |
|---|---|---|
| 1e-2 | 0/1500 = 0.00% | 0.06% |
| 1e-3 | 10/1500 = **0.67%** | **0.64%** |
| 1e-4 | 77/1500 = 5.13% | 6.40% |

At δ=1e-3, k=64: **0.67% of tokens need a correction** — sparse again, and
E-004's overhead budget survives. Top-k is nearly free on peaky
distributions (tail mass beyond top-64 ≈ 1e-9). This is the lsp1 design the
squeeze forces, and it is PA-3's actual proposal — we arrived at it
independently by finding out why the alternative can't work.

Two probes were thrown away getting here (a decimal-alignment artifact in
synthetic jitter; a trial loop that resampled signs but not logits). Both
produced confident, wrong numbers that agreed with no theory. Recorded
because E-006 must not repeat them on real hardware.

## EF-4 → F-8. Pack is 92% of cost, and only free packing saves it

F-4 priced lsp1 decode at GPU rates — contradicting **D-10**, the project's
own CPU-first decode decision. Fix that and the cost structure snaps into
focus (1 TB, 84 mo, 2 reads):

| | storage | pack | decode | egress | TOTAL |
|---|---|---|---|---|---|
| zstd -19 | $96.00 | $0.93 | $0.06 | $51.43 | **$148.41** |
| lsp1 (F-4 pricing) | $56.00 | $1,388.89 | $694.44 | $30.00 | $2,169.33 |
| lsp1 honoring D-10 | $56.00 | $1,388.89 | $27.78 | $30.00 | **$1,502.67** |

Pack becomes **92% of all cost**. Break-even demands **20.1 MB/s pack ≈ 5M
tokens/sec on one GPU** vs ~10–50k tok/s realistic — a **100–500x gap**. No
lever in the repo closes it:

- Hybrid chunk-routing (from F-1's 0.93x expansion on incompressible bytes —
  send only text-like chunks to the LLM) helps **5x** and still loses at
  every text fraction: 20% text → $441, even 5% text → $242, vs zstd's $148.
- Ratio is nearly free to give away: 15% ratio loss ≈ **0.5% of TCO**. E-002
  is trading a currency that doesn't matter.

**But set pack cost to zero and lsp1 wins by 23% ($113.78 vs $148.41).** So
the thesis survives in exactly one economic shape: a corpus whose logits are
*already being computed* for some other reason — RAG ingestion, embedding,
indexing, training-data curation, moderation. Lockstep is not a compressor
anyone buys. It is a **byproduct harvested from a pass already paid for**.

Dated note (2026-10-18): the table and the bold figures above rest on the cost
model's placeholder inputs, the 2 MB/s decode rate among them
(docs/audits/2026-10-18-image-audit/README.md, item B3). With any decode rate
the record measured in that placeholder's place, lsp1 costs more than zstd -19
even with packing free, so the free-packing branch does not survive measured
inputs; the verdict that the standalone thesis loses survives every input set
the audit's refuters tried, and the reason given for it, the 92% share, does
not. The section stands as written.

## EF-5. OQ-11 closes itself

The ~457 B manifest floor (F-3) only matters for small inputs; F-4/F-8
exclude the small-input regime entirely. **OQ-11 resolved: no compact binary
header.** One open question retired by crossing two findings, at zero cost.

## EF-6. The experiment portfolio measures the wrong axes

Cross F-8's cost structure against the E-index and every protocol is aimed
at a cheap term:

| experiment | measures | share of TCO |
|---|---|---|
| E-002 grid sweep | ratio | ~4% (storage) |
| E-004 safeguard | **bytes** of overhead | ~4% |
| E-005 CPU decode throughput | decode | **2%** |
| *(nothing)* | **pack throughput / amortization** | **92%** |

E-001's stop threshold is worse than mis-aimed: it is computed against a
2^15 grid that F-5 proves lsp1 can never use. The portfolio needs
re-scoping before any of it runs on rented hardware.

## EF-7. Methodology lesson (worth exporting to Trellis itself)

F-2 was measured at V=128 and silently generalized to a project about
128k-token models. The finding was never wrong — it was **cited outside the
regime it was measured in**, and nothing in the harness noticed for two
sessions. Findings should carry an explicit *regime* (the parameter ranges
they were measured over), and citing one outside its regime should be a lint
error, not a matter of memory. That is a cheap, general improvement to
Trellis, not just to Lockstep.

## What this changes, ordered

1. **TP-1 and TP-2 are blocked** until the profile constants land (D-12) and
   the grid moves to logit space (D-13).
2. **Build the profile advisor** (`tools/lockstep_profile_advisor.py`) so
   this class of error is caught by a command, not a session.
3. **Re-scope E-002/E-004/E-005; add E-006** (real-logit crossing rate — the
   one number the whole lsp1 design now rests on).
4. **Test the byproduct thesis with a human** before writing more format
   code. The cheapest experiment in the project is a conversation.
