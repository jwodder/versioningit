import argparse
import logging
import os
import subprocess
import sys
import traceback
from typing import List, Optional
from . import __version__
from .core import get_next_version, get_version
from .errors import Error
from .logging import get_env_loglevel, log
from .util import showcmd


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(
        description="Show the version of a versioningit-enabled project"
    )
    parser.add_argument(
        "-n",
        "--next-version",
        action="store_true",
        help="Show the next version after the current VCS tag",
    )
    parser.add_argument(
        "--traceback", action="store_true", help="Show full traceback on library error"
    )
    parser.add_argument(
        "-v", "--verbose", action="count", default=0, help="Show more log messages"
    )
    parser.add_argument(
        "-w", "--write", action="store_true", help="Write version to configured file"
    )
    parser.add_argument(
        "-V", "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.add_argument("project_dir", nargs="?", default=os.curdir)
    args = parser.parse_args(argv)
    env_loglevel = get_env_loglevel()
    if args.verbose == 0:
        if env_loglevel is None:
            log_level = logging.WARNING
        else:
            log_level = env_loglevel
    else:
        if args.verbose == 1:
            log_level = logging.INFO
        else:
            log_level = logging.DEBUG
        if env_loglevel is not None:
            log_level = min(log_level, env_loglevel)
    logging.basicConfig(
        format="[%(levelname)-8s] %(name)s: %(message)s",
        level=log_level,
    )
    try:
        if args.next_version:
            print(get_next_version(args.project_dir))
        else:
            print(get_version(args.project_dir, write=args.write, fallback=True))
    except Error as e:
        if args.traceback:
            traceback.print_exc()
        else:
            print(f"versioningit: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        if args.traceback:
            traceback.print_exc()
        else:
            if isinstance(e.cmd, list):
                cmd = showcmd(e.cmd)
            else:
                cmd = os.fsdecode(e.cmd)
            log.error("%s: command returned %d", cmd, e.returncode)
        sys.exit(e.returncode)


if __name__ == "__main__":
    main()  # pragma: no cover
