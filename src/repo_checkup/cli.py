"""Command-line entry point."""

import argparse
from collections.abc import Sequence

from repo_checkup import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="repo-checkup",
        description="Check a local Git repository against common engineering conventions.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    build_parser().parse_args(argv)
    return 0
