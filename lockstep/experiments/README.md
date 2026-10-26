# Experiments

Protocols for measurements this container cannot run (GPUs, big
corpora, wall-clock benchmarks that mean anything). Each file is a
recipe an operator executes on real hardware; results land as a row in
trellis-docs/trellis-runs.md and, if they clear the bar, a Finding.

Rules of the house:
- Never simulate a result an experiment was supposed to measure.
- Every number reported carries: machine fingerprint digest
  (`python -m lockstep env`), corpus identity (hash), and exact command.
- Negative results are findings too — "the grid did NOT absorb H100↔A100
  drift at 2^15" would be the most valuable sentence in the repo.

Index:
- E-001 cross-device logit drift census
- E-002 quantization grid sweep (ratio cost vs drift absorption)
- E-003 batch-invariance audit of candidate runtimes
- E-004 safeguard-stream overhead vs drift rate
- E-005 CPU integer decode throughput ceiling
