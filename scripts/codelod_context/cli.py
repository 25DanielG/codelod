"""cli entrypoint for codelod."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from codelod_context.pipeline import RepositoryContextBuilder

def main(argv: list[str] | None = None) -> int:
    """parse args, kick off build. return exit code."""

    parser = argparse.ArgumentParser(description="Build CodeLOD context artifacts.")
    parser.add_argument(
        "root",
        nargs="?",
        default=".",
        help="Repository root to scan. Defaults to the current working directory.",
    )
    args = parser.parse_args(argv)

    try:
        builder = RepositoryContextBuilder(Path(args.root).resolve())
        builder.build()
        return 0
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
