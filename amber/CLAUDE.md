# CLAUDE.md — amber conventions

Read FINDINGS.md, DECISIONS.md, OPEN_QUESTIONS.md first; docs/BLUEPRINT.md
is the plan of record. House rules mirror sideband's:
- make test green before commits; findings need regime + source (make lint).
- D-1/D-7: import sideband and lockstep primitives (sibling editable
  installs: ../../Research/sideband, ../lockstep-ultimate-repo on this box), never re-implement;
  sampling-mode archives use sideband.specdec verbatim; the AC upgrade uses
  lockstep.rac. Protocols/test batteries may be copied WITH provenance lines.
- D-2 is load-bearing: nothing decoder-invisible may shape the code. Any new
  steering/hint feature gets a decode-side reproduction test before merge.
- D-6: every rate table carries all four baselines (own bound, AC-under-q,
  zlib/zstd on content, raw). No strawman-only comparisons.
- Byte-exactness is the contract: every codec change adds a roundtrip test
  and a corruption test. Failures must be loud and typed (ValueError).
- D-8: coder contexts depend only on coded-symbol history and position.
  Never add a logit-value-derived context to the format (decoder-visible is
  not decoder-stable); measure such gains only as labelled UNSAFE variants.
- This repo shares a container/history with sideband; keep cross-repo
  changes in separate commits per repo.
