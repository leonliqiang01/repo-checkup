"""Command-line entry point."""

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from repo_checkup import __version__
from repo_checkup.core import Context, GitError
from repo_checkup.registry import discover
from repo_checkup.report import render_json, render_text, run_checks

EXIT_OK = 0
EXIT_FAILED = 1  # at least one check failed
EXIT_ERROR = 2  # bad usage, or the path cannot be checked at all


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="repo-checkup",
        description="Check a local Git repository against common engineering conventions.",
    )
    parser.add_argument(
        "path", nargs="?", default=".", help="repository to check (default: current directory)"
    )
    parser.add_argument(
        "--format", choices=["text", "json"], default="text", help="output format (default: text)"
    )
    parser.add_argument("--list", action="store_true", help="list available checks and exit")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    checks = discover()

    if args.list:
        width = max((len(c.id) for c in checks), default=0)
        for check in checks:
            print(f"{check.id:<{width}}  {check.title}")
        return EXIT_OK

    path = Path(args.path)
    if not path.is_dir():
        print(f"repo-checkup: error: not a directory: {path}", file=sys.stderr)
        return EXIT_ERROR
    try:
        ctx = Context.for_path(path)
    except GitError as exc:
        print(f"repo-checkup: error: cannot check {path}: {exc}", file=sys.stderr)
        return EXIT_ERROR

    report = run_checks(ctx, checks)
    print(render_json(report) if args.format == "json" else render_text(report))
    return EXIT_FAILED if report.failed else EXIT_OK
