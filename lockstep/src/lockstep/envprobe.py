"""Environment fingerprint: the first tool you run on every new machine.

Cross-machine decode failures come from somewhere. This probe captures
the usual suspects in one JSON blob with a stable digest, so two machines
can be diffed in seconds instead of debugged for days:

* interpreter identity (CPython version, build, compiler)
* platform triple
* libm behaviour — repr() of exp/log/tanh/sin on canary inputs. If two
  machines disagree here, ANY float on the coding path is unsafe there.
* float formatting mode

The v0 reference codec is integer-only precisely so that a libm diff
does NOT break it — run `python -m lockstep env` on both machines, diff
the digests, then run the conformance suite to prove the integer path
still agrees. The LLM adapter (TP-1/TP-2) extends this probe with GPU
name, driver, cuBLAS workspace config, and canary-logit digests; see
experiments/E-001.
"""

from __future__ import annotations

import hashlib
import json
import math
import platform
import struct
import sys

_CANARIES = [1e-8, 0.1, 0.5, 1.0, 2.0, math.pi, 10.0, 1e8]


def _libm_signature() -> dict:
    sig = {}
    for name, fn in (("exp", math.exp), ("log", math.log),
                     ("tanh", math.tanh), ("sin", math.sin)):
        vals = []
        for x in _CANARIES:
            try:
                v = fn(x)
            except (OverflowError, ValueError):
                v = None
            # struct-pack the exact bits, not the repr, to catch 1-ulp drift
            vals.append(None if v is None else struct.pack(">d", v).hex())
        sig[name] = vals
    return sig


def fingerprint() -> dict:
    fp = {
        "python": {
            "version": sys.version,
            "implementation": platform.python_implementation(),
            "compiler": platform.python_compiler(),
        },
        "platform": {
            "machine": platform.machine(),
            "system": platform.system(),
            "release": platform.release(),
        },
        "float": {
            "repr_style": sys.float_repr_style,
            "mant_dig": sys.float_info.mant_dig,
        },
        "libm": _libm_signature(),
    }
    canon = json.dumps(fp, sort_keys=True, separators=(",", ":")).encode("utf-8")
    fp["digest"] = hashlib.sha256(canon).hexdigest()
    return fp


def main() -> int:
    print(json.dumps(fingerprint(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
