import logging
import os
import shlex
from typing import List, Optional

log = logging.getLogger(__package__)

LOG_LEVEL_ENVVAR = "VERSIONINGIT_LOG_LEVEL"


def init_logging(level: Optional[int] = None) -> None:
    if level is None:
        try:
            level = parse_log_level(os.environ[LOG_LEVEL_ENVVAR])
        except (KeyError, ValueError):
            level = logging.WARNING
    log.setLevel(level)


def parse_log_level(level: str) -> int:
    """
    Convert a log level name (case-insensitive) or number to its numeric value
    """
    try:
        lv = int(level)
    except ValueError:
        levelup = level.upper()
        if levelup in {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"}:
            ll = getattr(logging, levelup)
            assert isinstance(ll, int)
            return ll
        else:
            raise ValueError(f"Invalid log level: {level!r}")
    else:
        return lv


def logcmd(args: List[str]) -> None:
    log.debug("Running: %s", " ".join(map(shlex.quote, args)))


def warn_extra_fields(fields: dict, fieldname: str) -> None:
    if fields:
        log.warning(
            "Ignoring extra fields in %s: %s", fieldname, ", ".join(fields.keys())
        )
