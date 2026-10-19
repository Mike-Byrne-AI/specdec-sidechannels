# Why This Dies

- **K-1 — FTO.** [withheld: the kill's text: a patent's claims and the counsel step (plan 10.3; 15.1 call 2); the criterion stays as structure under its name; see WITHHELD.md]
  Dated note (2026-10-18): not checked before publication; the owner waived
  the gate (OQ-6 and BLUEPRINT's gate carry dated notes of this day), so the
  record goes public with K-1 unfired and unchecked.
- **K-2 — Real divergence rates are bad.** [checked 2026-08-29, F-8: did NOT fire on Llama-3.2-3B->1B; 0.47 vs zstd 3.62 bits/token. Remaining exposure: the tie with AC-under-draft means no rate edge over a draft-side arithmetic coder until the coder upgrade lands.] Aligned pairs disagree on greedy
  argmax too often, and divergence bits lose to zstd even on
  target-generated text (OQ-1). Salvage: the attestation primitive alone
  ([withheld: a private repository's name (plan section 3); see WITHHELD.md]) — it needs no compression win.
- **K-3 — Rank stability is expensive.** If order-preserving replay across
  hardware needs bitwise-determinism-grade machinery anyway (OQ-2), the
  lightweight-decoder story weakens to wherever lockstep already runs.
  Salvage: amber becomes lockstep's flagship workload instead of a light
  dependent. [Status 2026-08-30, F-10/D-8: does not fire in this form. Order
  stability to rank 64 is free at fp32 across CPU/GPU/batch and NOT
  achievable at bf16 by any top-1 escape; the cost is a dtype pin (3.65x
  replay time), not determinism machinery.]
- **K-4 — Serving incompatibility.** Archive-compatible serving modes cost
  too much speed (OQ-5), packing becomes a separate pass again, and the
  determinism-layer cost model's zstd verdict returns. Salvage: archives
  for content you were generating deterministically anyway.
- **K-5 — Nobody wants draft-decodable archives.** The asymmetry (encode
  heavy, decode light) has no buyer: storage people use zstd, ML people
  keep the target around. This is a market kill, not a technical one — the
  Phase-4 memo must name a user.
