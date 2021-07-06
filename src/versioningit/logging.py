import logging
import os
import shlex
from typing import List, Optional
from packaging.version import Version

log = logging.getLogger(__package__)


def init_logging(level: Optional[int] = None) -> None:
    if level is None:
        try:
            level = parse_log_level(os.environ["VERSIONINGIT_LOG_LEVEL"])
        except (KeyError, ValueError):
            level = logging.WARNING
    log.setLevel(level)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(levelname)-8s] %(name)s: %(message)s"))
    log.addHandler(handler)


def parse_log_level(level: str) -> int:
    """
    Convert a log level name (case-insensitive) or number to its numeric value
    """
    try:
        return int(level)
    except ValueError:
        levelup = level.upper()
        if levelup in {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"}:
            ll = getattr(logging, levelup)
            assert isinstance(ll, int)
            return ll
        else:
            raise ValueError(f"Invalid log level: {level!r}")


def logcmd(args: List[str]) -> None:
    log.debug("Running: %s", showcmd(args))


def warn_extra_fields(fields: dict, fieldname: str) -> None:
    if fields:
        log.info("Ignoring extra fields in %s: %s", fieldname, ", ".join(fields.keys()))


def warn_bad_version(version: str, desc: str) -> None:
    try:
        Version(version)
    except ValueError:
        log.warning("%s: %s is not PEP 440-compliant", version, desc)


def showcmd(args: list) -> str:
    return " ".join(shlex.quote(str(a)) for a in args)
