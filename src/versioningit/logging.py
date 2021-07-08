import logging
import os
from typing import Optional
from packaging.version import Version

log = logging.getLogger(__package__)


def init_logging(level: Optional[int] = None) -> None:
    """
    Configure the `versioningit` logger and set its level to ``level``.  If
    ``level`` is not specified, the value is taken from the
    :envvar:`VERSIONINGIT_LOG_LEVEL` environment variable, with a default of
    ``WARNING``.
    """
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
        if levelup in {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"}:
            ll = getattr(logging, levelup)
            assert isinstance(ll, int)
            return ll
        else:
            raise ValueError(f"Invalid log level: {level!r}")


def warn_extra_fields(params: dict, fieldname: str) -> None:
    """
    If ``params`` is not empty, emit a log message indicating that the
    parameters within are ignored.  ``fieldname`` is the name of the table in
    which ``params`` were found.
    """
    if params:
        log.info(
            "Ignoring extra parameters in %s: %s", fieldname, ", ".join(params.keys())
        )


def warn_bad_version(version: str, desc: str) -> None:
    """
    If ``version`` is not :pep:`440`-compliant, log a warning.  ``desc`` is a
    description of the version's provenance.
    """
    try:
        Version(version)
    except ValueError:
        log.warning("%s %r is not PEP 440-compliant", desc, version)
