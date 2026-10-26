"""Command-line interface for Lockstep containers and conformance checks."""

from __future__ import annotations

import argparse
import json
import re
import sys
from typing import Optional

from . import __version__, container, envprobe
from .conformance import run_vectors
from .errors import CoderError, ContainerError
from .models import MODEL_REGISTRY, make_model

CLI_DEFAULT_LIMIT = 1 * 1024 * 1024 * 1024
_SIZE_RE = re.compile(r"\A([0-9]+)\s*([kmgt]?i?b?)?\Z", re.IGNORECASE)
_SIZE_UNITS = {
    "": 1,
    "b": 1,
    "k": 1024,
    "kb": 1024,
    "kib": 1024,
    "m": 1024 ** 2,
    "mb": 1024 ** 2,
    "mib": 1024 ** 2,
    "g": 1024 ** 3,
    "gb": 1024 ** 3,
    "gib": 1024 ** 3,
    "t": 1024 ** 4,
    "tb": 1024 ** 4,
    "tib": 1024 ** 4,
}


def _byte_size(text: str) -> int:
    match = _SIZE_RE.fullmatch(text.strip())
    if match is None:
        raise argparse.ArgumentTypeError(
            "size must be a non-negative integer with optional KiB/MiB/GiB/TiB suffix"
        )
    value = int(match.group(1))
    suffix = (match.group(2) or "").lower()
    try:
        return value * _SIZE_UNITS[suffix]
    except KeyError as exc:
        raise argparse.ArgumentTypeError(f"unsupported size suffix {suffix!r}") from exc


def _add_reader_limits(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--max-output-size",
        type=_byte_size,
        default=CLI_DEFAULT_LIMIT,
        metavar="SIZE",
        help="refuse archives declaring more decoded bytes (default: 1GiB)",
    )
    parser.add_argument(
        "--max-payload-size",
        type=_byte_size,
        default=CLI_DEFAULT_LIMIT,
        metavar="SIZE",
        help="refuse payloads larger than this (default: 1GiB)",
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lockstep", description=__doc__)
    parser.add_argument("--version", action="version", version=f"lockstep {__version__}")
    sub = parser.add_subparsers(dest="cmd", required=True)

    pack_parser = sub.add_parser("pack", help="compress a file into a .lsa container")
    pack_parser.add_argument("src")
    pack_parser.add_argument("dst")
    pack_parser.add_argument(
        "--model", default="adaptive-order1", choices=sorted(MODEL_REGISTRY)
    )
    pack_parser.add_argument(
        "--max-input-size",
        type=_byte_size,
        default=CLI_DEFAULT_LIMIT,
        metavar="SIZE",
        help="refuse inputs larger than this (default: 1GiB)",
    )
    pack_parser.add_argument(
        "--max-payload-size",
        type=_byte_size,
        default=CLI_DEFAULT_LIMIT,
        metavar="SIZE",
        help="stop if compressed payload grows beyond this (default: 1GiB)",
    )

    unpack_parser = sub.add_parser("unpack", help="restore original bytes")
    unpack_parser.add_argument("src")
    unpack_parser.add_argument("dst")
    _add_reader_limits(unpack_parser)

    verify_parser = sub.add_parser("verify", help="decode and hash-check without output")
    verify_parser.add_argument("src")
    _add_reader_limits(verify_parser)

    info_parser = sub.add_parser("info", help="print the validated container manifest")
    info_parser.add_argument("src")
    _add_reader_limits(info_parser)

    sub.add_parser("env", help="print this machine's determinism fingerprint")
    sub.add_parser("models", help="list registered models and pinned profile fields")
    sub.add_parser("self-check", help="run packaged lsp0 vectors and print env digest")
    return parser


def _self_check() -> int:
    results = run_vectors()
    failed = 0
    for result in results:
        print(f"  [{'OK' if result.ok else 'FAIL'}] {result.name}")
        if not result.ok:
            print(f"       {result.detail}")
            failed += 1
    digest = envprobe.fingerprint()["digest"]
    print(f"env fingerprint: {digest}")
    if failed:
        print(f"self-check: {failed} vector(s) FAILED — this build does not conform to lsp0")
        return 1
    print(f"self-check: all {len(results)} vectors reproduced; profile lsp0 OK")
    return 0


def _dispatch(args: argparse.Namespace) -> int:
    if args.cmd == "pack":
        stats = container.pack_file(
            args.src,
            args.dst,
            args.model,
            max_original_size=args.max_input_size,
            max_payload_size=args.max_payload_size,
        )
        print(json.dumps(stats, sort_keys=True))
        return 0
    if args.cmd == "unpack":
        stats = container.unpack_file(
            args.src,
            args.dst,
            max_original_size=args.max_output_size,
            max_payload_size=args.max_payload_size,
        )
        print(json.dumps(stats, sort_keys=True))
        return 0
    if args.cmd == "verify":
        container.verify_file(
            args.src,
            max_original_size=args.max_output_size,
            max_payload_size=args.max_payload_size,
        )
        print("OK: payload hash, decode, and original hash all verified")
        return 0
    if args.cmd == "info":
        manifest = container.read_manifest_file(
            args.src,
            max_original_size=args.max_output_size,
            max_payload_size=args.max_payload_size,
        )
        print(json.dumps(manifest, indent=2, sort_keys=True))
        return 0
    if args.cmd == "env":
        return envprobe.main()
    if args.cmd == "models":
        for name in sorted(MODEL_REGISTRY):
            print(name, "->", json.dumps(make_model(name).profile_fields(), sort_keys=True))
        return 0
    if args.cmd == "self-check":
        return _self_check()
    return 2


def main(argv: Optional[list[str]] = None) -> int:
    args = _parser().parse_args(argv)
    try:
        return _dispatch(args)
    except (ContainerError, CoderError, OSError, ValueError) as exc:
        print(f"lockstep: error: {exc}", file=sys.stderr)
        return 1
