"""CLI smoke tests, in-process."""

import contextlib
import io
import os
import tempfile
import unittest

from . import _SRC  # noqa
from lockstep.cli import main


class TestCli(unittest.TestCase):
    def test_pack_unpack_verify_info_env(self):
        with tempfile.TemporaryDirectory() as d:
            src = os.path.join(d, "in.txt")
            lsa = os.path.join(d, "in.lsa")
            out = os.path.join(d, "out.txt")
            with open(src, "wb") as f:
                f.write(b"determinism or it didn't happen\n" * 64)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                self.assertEqual(main(["pack", src, lsa]), 0)
                self.assertEqual(main(["verify", lsa]), 0)
                self.assertEqual(main(["info", lsa]), 0)
                self.assertEqual(main(["unpack", lsa, out]), 0)
                self.assertEqual(main(["env"]), 0)
                self.assertEqual(main(["models"]), 0)
                self.assertEqual(main(["self-check"]), 0)
            with open(src, "rb") as a, open(out, "rb") as b:
                self.assertEqual(a.read(), b.read())
            out_text = buf.getvalue()
            self.assertIn("OK: payload hash", out_text)
            self.assertIn("profile lsp0 OK", out_text)


if __name__ == "__main__":
    unittest.main()
