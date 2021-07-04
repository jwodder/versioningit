import argparse
import logging
import os
from typing import List, Optional
from . import __version__
from .core import get_version
from .logging import parse_log_level


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(
        description="Show the version of a versioningit-enabled project"
    )
    parser.add_argument(
        "-l",
        "--log-level",
        choices=["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"],
        default="WARNING",
        help="Set logging level  [default: WARNING]",
    )
    parser.add_argument(
        "-w", "--write", action="store_true", help="Write version to configured file"
    )
    parser.add_argument(
        "-V", "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.add_argument("project_dir", nargs="?", default=os.curdir)
    args = parser.parse_args(argv)
    logging.basicConfig(
        format="[%(levelname)-8s] %(name)s: %(message)s",
        level=parse_log_level(args.log_level),
    )
    print(get_version(args.project_dir, write=args.write, fallback=True))


if __name__ == "__main__":
    main()  # pragma: no cover
