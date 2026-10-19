"""CDF construction, integer quantizer, and the drift-absorption property."""

import unittest

from . import _SRC  # noqa
from lockstep.cdf import Cdf, quantize_probs, quantize_weights
from lockstep.drbg import deterministic_ints
from lockstep.rac import CoderError


class TestCdf(unittest.TestCase):
    def test_from_freqs_and_find(self):
        cdf = Cdf.from_freqs([3, 1, 6])
        self.assertEqual(cdf.total, 10)
        self.assertEqual([cdf.find(t) for t in range(10)],
                         [0, 0, 0, 1, 2, 2, 2, 2, 2, 2])

    def test_zero_freq_rejected(self):
        with self.assertRaises(CoderError):
            Cdf.from_freqs([1, 0, 2])

    def test_quantize_weights_exact_total_and_floor(self):
        for case in range(40):
            n = deterministic_ints(f"qw-n-{case}", 1, 2, 300)[0]
            w = deterministic_ints(f"qw-w-{case}", n, 0, 10_000)
            total = max(n, deterministic_ints(f"qw-t-{case}", 1, n, 1 << 15)[0])
            f = quantize_weights(w, total)
            self.assertEqual(sum(f), total)
            self.assertTrue(all(x >= 1 for x in f))

    def test_quantize_weights_deterministic(self):
        w = deterministic_ints("qw-det", 64, 0, 5000)
        self.assertEqual(quantize_weights(w, 1 << 14), quantize_weights(w, 1 << 14))

    def test_quantizer_absorbs_small_drift(self):
        """The grid-as-drift-sponge property: probabilities that differ by
        much less than half a grid step quantize to the SAME integer CDF.
        This is the mechanism TP-2 builds on."""
        total = 1 << 15
        absorbed = diverged = 0
        for case in range(200):
            w = deterministic_ints(f"drift-{case}", 128, 1, 9999)
            s = sum(w)
            probs = [x / s for x in w]
            tiny = 1e-11  # orders below half a grid step; tie-flips vanishingly rare
            perturbed = [p + (tiny if i % 2 else -tiny) for i, p in enumerate(probs)]
            if quantize_probs(probs, total) == quantize_probs(perturbed, total):
                absorbed += 1
            big = 1e-3   # far above a grid step
            perturbed2 = [p + (big if i % 2 else -big) for i, p in enumerate(probs)]
            perturbed2 = [max(p, 0.0) for p in perturbed2]
            if quantize_probs(probs, total) != quantize_probs(perturbed2, total):
                diverged += 1
        self.assertGreaterEqual(absorbed, 198, f"absorbed only {absorbed}/200")
        self.assertGreaterEqual(diverged, 198, f"diverged only {diverged}/200")

    def test_quantize_probs_matches_weights_on_exact_inputs(self):
        w = deterministic_ints("qpw", 32, 1, 100)
        s = sum(w)
        total = 1 << 12
        self.assertEqual(quantize_probs([x / s for x in w], total),
                         quantize_weights(w, total))


if __name__ == "__main__":
    unittest.main()
