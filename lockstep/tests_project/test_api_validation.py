"""Strict trust-boundary validation for direct coder APIs."""

import io
import math
import unittest

from . import _SRC  # noqa
from lockstep.cdf import Cdf, quantize_probs, quantize_weights
from lockstep.codec import decode_bytes, decode_stream, encode_stream
from lockstep.drbg import deterministic_bytes, deterministic_ints
from lockstep.errors import CoderError
from lockstep.models import MODEL_PROFILES, MODEL_REGISTRY, make_model
from lockstep.rac import RangeDecoder, RangeEncoder


class TestApiValidation(unittest.TestCase):
    def test_cdf_rejects_noninteger_values_and_bool(self):
        for bad in ([0, 1.5], [0, True], [0, "1"]):
            with self.subTest(bad=bad):
                with self.assertRaises(CoderError):
                    Cdf(bad)
        for bad in ([1.0, 2], [True, 2]):
            with self.assertRaises(CoderError):
                Cdf.from_freqs(bad)

    def test_cdf_is_actually_immutable(self):
        cdf = Cdf.from_freqs([1, 2])
        with self.assertRaises(AttributeError):
            cdf.total = 99
        with self.assertRaises(AttributeError):
            cdf.cum = (0, 99)
        self.assertEqual(cdf.cum, (0, 1, 3))
        self.assertEqual(cdf.total, 3)

    def test_cdf_bounds_are_typed_errors(self):
        cdf = Cdf.from_freqs([1, 2])
        for symbol in (-1, 2, True, 1.0):
            with self.assertRaises(CoderError):
                cdf.interval(symbol)
        for target in (-1, cdf.total, True, 1.0):
            with self.assertRaises(CoderError):
                cdf.find(target)

    def test_integer_quantizer_rejects_coercion(self):
        for weights in ([1.0, 2], [True, 2], ["1", 2]):
            with self.assertRaises(CoderError):
                quantize_weights(weights)
        with self.assertRaises(CoderError):
            quantize_weights([1, 2], total=True)

    def test_float_quantizer_rejects_nonfinite_values(self):
        for value in (math.nan, math.inf, -math.inf):
            with self.assertRaises(CoderError):
                quantize_probs([value, 1.0])
        with self.assertRaises(CoderError):
            quantize_probs([True, 1.0])

    def test_range_coder_rejects_float_and_bool_intervals(self):
        encoder = RangeEncoder()
        for args in ((0.0, 1, 2), (0, True, 2), (0, 1, 2.0)):
            with self.assertRaises(CoderError):
                encoder.encode(*args)
        decoder = RangeDecoder(b"")
        for total in (1.0, True):
            with self.assertRaises(CoderError):
                decoder.decode_target(total)

    def test_decode_length_must_be_nonnegative_integer(self):
        for bad in (-1, True, 1.0):
            with self.assertRaises(CoderError):
                decode_bytes(b"", bad, make_model("uniform"))

    def test_streams_must_be_binary_and_report_valid_progress(self):
        with self.assertRaises(CoderError):
            encode_stream(io.StringIO("text"), io.BytesIO(), make_model("uniform"))
        with self.assertRaises(CoderError):
            encode_stream(io.BytesIO(b"x"), io.StringIO(), make_model("uniform"))

        class StalledSink:
            def write(self, data):
                return 0

        class OverreportingSink:
            def write(self, data):
                return len(data) + 1

        with self.assertRaises(CoderError):
            encode_stream(io.BytesIO(b"x"), StalledSink(), make_model("uniform"))
        with self.assertRaises(CoderError):
            encode_stream(
                io.BytesIO(b"x"), OverreportingSink(), make_model("uniform")
            )
        with self.assertRaises(CoderError):
            decode_stream(io.BytesIO(b""), 0, make_model("uniform"), object())
        with self.assertRaises(CoderError):
            decode_stream(
                io.BytesIO(b""), 1, make_model("uniform"), OverreportingSink()
            )

    def test_profile_tables_are_immutable_runtime_constants(self):
        with self.assertRaises(TypeError):
            MODEL_PROFILES["uniform"]["alphabet"] = 999
        with self.assertRaises(TypeError):
            MODEL_PROFILES["new"] = {"model": "new"}
        with self.assertRaises(TypeError):
            MODEL_REGISTRY["new"] = object
        self.assertEqual(make_model("uniform").profile_fields()["alphabet"], 256)

    def test_drbg_arguments_are_explicit(self):
        with self.assertRaises(CoderError):
            deterministic_bytes("seed", -1)
        with self.assertRaises(CoderError):
            deterministic_bytes(7, 1)
        with self.assertRaises(CoderError):
            deterministic_bytes("\ud800", 1)
        with self.assertRaises(CoderError):
            deterministic_ints("seed", 1, 2, 1)
        with self.assertRaises(CoderError):
            deterministic_ints("seed", True, 0, 1)


if __name__ == "__main__":
    unittest.main()
