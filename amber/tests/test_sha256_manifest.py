"""tools/sha256_manifest.py: a manifest round-trips, and any byte change or missing file is loud."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import sha256_manifest as sm  # noqa: E402


def _populate(root: Path) -> None:
    (root / "d" / "sub").mkdir(parents=True)
    (root / "d" / "a.bin").write_bytes(b"\x00\x01\x02")
    (root / "d" / "sub" / "b.txt").write_bytes(b"line\r\nline\n")


def test_write_then_check_ok(tmp_path):
    _populate(tmp_path)
    out = tmp_path / "m.sha256"
    assert sm.main(["--root", str(tmp_path), "write", "--out", str(out), str(tmp_path / "d")]) == 0
    text = out.read_bytes()
    assert b"\r" not in text, "manifest must be LF"
    assert text.endswith(b"\n")
    rows = sm.parse_manifest(text.decode())
    assert [r for _, r in rows] == ["d/a.bin", "d/sub/b.txt"], "sorted, forward-slash, root-relative"
    assert sm.main(["--root", str(tmp_path), "check", str(out)]) == 0


def test_check_fails_on_byte_change_and_missing(tmp_path, capsys):
    _populate(tmp_path)
    out = tmp_path / "m.sha256"
    sm.main(["--root", str(tmp_path), "write", "--out", str(out), str(tmp_path / "d")])
    (tmp_path / "d" / "a.bin").write_bytes(b"\x00\x01\x03")
    (tmp_path / "d" / "sub" / "b.txt").unlink()
    assert sm.main(["--root", str(tmp_path), "check", str(out)]) == 1
    text = capsys.readouterr().out
    assert "MISMATCH d/a.bin" in text and "MISSING  d/sub/b.txt" in text


def test_malformed_line_is_typed_error(tmp_path):
    bad = tmp_path / "bad.sha256"
    bad.write_text("notahash  d/x\n")
    try:
        sm.check(bad, tmp_path)
    except ValueError as e:
        assert "malformed" in str(e)
    else:
        raise AssertionError("malformed manifest must raise ValueError")
