"""Keep the source-visible and installed conformance resources identical."""

import hashlib
import json
import os
import unittest
from importlib import resources

from . import _SRC  # noqa
from lockstep.conformance import VECTORS_V0_SHA256, load_vectors, run_vectors


class TestPackagedConformanceData(unittest.TestCase):
    def test_packaged_vectors_match_repo_copy(self):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(root, "conformance", "vectors_v0.json"), "rb") as f:
            repo_bytes = f.read()
        packaged_bytes = resources.files("lockstep.data").joinpath(
            "vectors_v0.json"
        ).read_bytes()
        self.assertEqual(packaged_bytes, repo_bytes)
        self.assertEqual(hashlib.sha256(repo_bytes).hexdigest(), VECTORS_V0_SHA256)
        repo_spec = json.loads(repo_bytes)
        self.assertEqual(load_vectors(), repo_spec)

    def test_packaged_vectors_all_pass(self):
        results = run_vectors()
        self.assertTrue(results)
        self.assertTrue(all(result.ok for result in results), results)


if __name__ == "__main__":
    unittest.main()
