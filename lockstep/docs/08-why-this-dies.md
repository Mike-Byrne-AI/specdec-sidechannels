# Why this dies

The standing adversary. A solo founder's deadliest bug is motivated
reasoning, so this document argues AGAINST the project on purpose. Re-read
it every few packs; answer new objections; strike ones that are truly
retired. If most of these stay unanswered, that is the signal.

## The killers, most-lethal first

1. **The cost model never closes.** If Blueprint A shows that, at [withheld: Blueprint A not in this repository; see WITHHELD.md]
   realistic corpus sizes and GPU prices, lsp1 never beats `zstd -19` on
   total cost once packing GPU-hours are counted, the archival wedge is
   dead and no amount of engineering fixes it. This is the existential
   one — build the calculator before more code. Mitigation: it's a day of
   work and the answer is decision-grade either way.

2. **"Deterministic enough" already exists, cheaper.** A skeptic says:
   just quantize the model to int8, pin the runtime, and accept the
   occasional re-pack; the safeguard-stream machinery is over-engineering
   for a problem most buyers will tolerate. Rebuttal must be empirical
   (E-001 drift numbers) — if real cross-device drift is rare AND the
   failure is a cheap re-pack rather than silent corruption, the value
   proposition thins. Know the number before claiming the layer is needed.

3. **The buyer doesn't feel the pain.** Storage is cheap; compliance
   teams fear *inability to read old data*, not its size. If the pitch is
   "save storage," it loses. The only version that sells is "provably
   restorable forever" (Blueprint E receipts) — a different, narrower [withheld: Blueprint E not in this repository; see WITHHELD.md]
   value prop than compression ratio. If that reframing doesn't land with
   a real prospective user, reconsider.

4. **Throughput makes it impractical.** Pure-Python is ~32 KiB/s; even a
   C port + GPU model may leave lsp1 packing too slow for large corpora,
   and CPU-first decode (D-10) may miss restore-time SLAs (E-005). If both
   the pack side and the CPU decode side are too slow at the model size
   that gives good ratios, the usable envelope may be empty.

5. **Patent exposure constrains the good design.** If TP-5 counsel flags
   the safeguard-stream approach (not just integer networks), the central
   architecture needs a rethink and the timeline slips hard.

6. **Ecosystem moves and eats it.** GPU vendors normalizing
   weights-as-data (NTC) and model-compression tools shipping "lossless +
   exact" claims means a big player could ship a determinism story as a
   feature of an existing product. First-mover on the *spec* is the only
   defense, and only if the spec gets adopted.

7. **Solo-founder bandwidth.** This needs a coder, a spec author, a
   determinism researcher, and eventually a BD/compliance seller. Doing
   the first three is plausible; the fourth is a different job, and the
   product only monetizes when someone does it.

## What would make each killer retreat

- #1 → Blueprint A returns a corpus-size/access-pattern region where [withheld: Blueprint A not in this repository; see WITHHELD.md]
  lsp1 wins with margin. Then the project has a defensible "who this is
  for."
- #2/#3 → E-001 shows drift is real enough that silent-corruption risk is
  non-trivial, AND a real prospect says "provable restore is worth
  paying for."
- #4 → E-005 projects acceptable restore times at a ratio-worthwhile
  model size on commodity CPUs.
- #5 → TP-5 clears the safeguard design.
- #6 → the container + profile spec gets one external implementor.

## Honest current status

None of these are answered yet. The core tech is proven (F-1/F-2/F-3);
the *business* case is entirely unbuilt. That ordering — great engine,
unproven demand — is itself a risk pattern worth naming out loud. The
next unit of work with the highest information-per-hour is Blueprint A, [withheld: Blueprint A not in this repository; see WITHHELD.md]
not more format features.
