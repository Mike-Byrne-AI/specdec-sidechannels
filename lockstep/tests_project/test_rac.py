"""Fuzz and edge tests for the integer range coder in isolation."""

import unittest

from . import _SRC  # noqa  (path shim)
from lockstep.cdf import Cdf
from lockstep.drbg import deterministic_ints
from lockstep.rac import (CoderError, RangeDecoder, RangeEncoder,
                          TOTAL_MAX)


def _roundtrip(symbols, cdfs):
    enc = RangeEncoder()
    for s, cdf in zip(symbols, cdfs):
        lo, hi, total = cdf.interval(s)
        enc.encode(lo, hi, total)
    payload = enc.finish()
    dec = RangeDecoder(payload)
    out = []
    for cdf in cdfs:
        target = dec.decode_target(cdf.total)
        sym = cdf.find(target)
        lo, hi, total = cdf.interval(sym)
        dec.update(lo, hi, total)
        out.append(sym)
    return out, payload


class TestRangeCoder(unittest.TestCase):
    def test_empty_stream(self):
        enc = RangeEncoder()
        payload = enc.finish()
        self.assertLessEqual(len(payload), 1)

    def test_single_symbol_alphabet(self):
        cdf = Cdf.from_freqs([1])
        out, payload = _roundtrip([0] * 50, [cdf] * 50)
        self.assertEqual(out, [0] * 50)
        # a certain symbol should cost ~0 bits
        self.assertLessEqual(len(payload), 2)

    def test_extreme_skew(self):
        cdf = Cdf.from_freqs([1, TOTAL_MAX - 1])
        syms = [1] * 300 + [0] + [1] * 300
        out, _ = _roundtrip(syms, [cdf] * len(syms))
        self.assertEqual(out, syms)

    def test_total_at_max(self):
        n = 16
        cdf = Cdf.from_freqs([TOTAL_MAX // n] * n)
        self.assertEqual(cdf.total, TOTAL_MAX)
        syms = deterministic_ints("total-max", 500, 0, n - 1)
        out, _ = _roundtrip(syms, [cdf] * len(syms))
        self.assertEqual(out, syms)

    def test_fuzz_varied_alphabets(self):
        for case in range(60):
            v = deterministic_ints(f"fuzz-v-{case}", 1, 2, 40)[0]
            freqs = deterministic_ints(f"fuzz-f-{case}", v, 1, 900)
            cdf = Cdf.from_freqs(freqs)
            n = deterministic_ints(f"fuzz-n-{case}", 1, 1, 400)[0]
            syms = deterministic_ints(f"fuzz-s-{case}", n, 0, v - 1)
            out, _ = _roundtrip(syms, [cdf] * n)
            self.assertEqual(out, syms, f"fuzz case {case} desynced")

    def test_fuzz_changing_cdfs(self):
        for case in range(20):
            n = 200
            cdfs, syms = [], []
            for i in range(n):
                v = 2 + (i % 17)
                freqs = deterministic_ints(f"chg-{case}-{i}", v, 1, 200)
                cdfs.append(Cdf.from_freqs(freqs))
                syms.append(deterministic_ints(f"chgs-{case}-{i}", 1, 0, v - 1)[0])
            out, _ = _roundtrip(syms, cdfs)
            self.assertEqual(out, syms)

    def test_determinism_repeat(self):
        cdf = Cdf.from_freqs(deterministic_ints("det", 32, 1, 99))
        syms = deterministic_ints("det-s", 512, 0, 31)
        _, p1 = _roundtrip(syms, [cdf] * len(syms))
        _, p2 = _roundtrip(syms, [cdf] * len(syms))
        self.assertEqual(p1, p2)

    def test_invalid_interval_raises(self):
        enc = RangeEncoder()
        with self.assertRaises(CoderError):
            enc.encode(5, 5, 10)
        with self.assertRaises(CoderError):
            enc.encode(0, 11, 10)
        with self.assertRaises(CoderError):
            enc.encode(0, 1, TOTAL_MAX + 1)

    def test_encode_after_finish_raises(self):
        enc = RangeEncoder()
        enc.finish()
        with self.assertRaises(CoderError):
            enc.encode(0, 1, 2)


if __name__ == "__main__":
    unittest.main()
