---
paths:
  - "tests/**/*"
---
# Test work rules

- Tests should verify behavior, not merely the existence of a file, function, or command.
- Use `python -m pytest -q` as the default full-suite command.
- Keep failure messages actionable: say what is wrong and what kind of fix is needed.
- Prefer small fixtures and deterministic local inputs.
- Do not require network access, paid APIs, GPUs, or long-running jobs for harness tests.
