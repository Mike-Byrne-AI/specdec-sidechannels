"""Fast deterministic mutation smoke tests for the untrusted container surface."""

import random
import struct
import unittest

from . import _SRC  # noqa
from lockstep.container import pack, unpack
from lockstep.errors import LockstepError


class TestDeterministicContainerFuzz(unittest.TestCase):
    SEED = 0x10C57E9
    CASES = 768

    def test_mutations_never_leak_builtin_exceptions(self):
        rng = random.Random(self.SEED)
        seeds = [
            pack(b""),
            pack(b"manifest and payload mutation" * 20),
            pack(bytes(range(256)) * 2, "uniform"),
        ]

        for index in range(self.CASES):
            mode = index % 6
            base = bytearray(rng.choice(seeds))
            if mode == 0 and base:
                del base[rng.randrange(len(base)) :]
            elif mode == 1 and base:
                position = rng.randrange(len(base))
                base[position] ^= 1 << rng.randrange(8)
            elif mode == 2:
                position = rng.randrange(len(base) + 1)
                base[position:position] = rng.randbytes(rng.randrange(1, 17))
            elif mode == 3:
                base = bytearray(
                    b"LSA0"
                    + struct.pack(">I", rng.randrange(0, 513))
                    + rng.randbytes(rng.randrange(0, 640))
                )
            elif mode == 4:
                base = bytearray(rng.randbytes(rng.randrange(0, 640)))
            elif len(base) >= 8:
                base[4:8] = struct.pack(">I", rng.randrange(0, 513))

            try:
                unpack(
                    bytes(base),
                    max_manifest_size=512,
                    max_original_size=4096,
                    max_payload_size=4096,
                )
            except LockstepError:
                pass
            except Exception as exc:  # pragma: no cover - the assertion is the test
                self.fail(
                    f"case {index} seed {self.SEED:#x} leaked "
                    f"{type(exc).__name__}: {exc}"
                )


if __name__ == "__main__":
    unittest.main()
