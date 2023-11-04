from __future__ import annotations
from difflib import get_close_matches
import logging
import os
from typing import Iterable, Optional
from packaging.version import Version

log = logging.getLogger("versioningit")


def get_env_loglevel() -> Optional[int]:
    """
    Return the logging level specified in the :envvar:`VERSIONINGIT_LOG_LEVEL`
    environment variable, if any
    """
    try:
        return parse_log_level(os.environ["VERSIONINGIT_LOG_LEVEL"])
    except (KeyError, ValueError):
        return None


def init_logging(level: Optional[int] = None) -> None:
    """
    Configure the `versioningit` logger and set its level to ``level``.  If
    ``level`` is not specified, the value is taken from the
    :envvar:`VERSIONINGIT_LOG_LEVEL` environment variable, with a default of
    ``WARNING``.
    """
    if log.handlers:
        return
    if level is None:
        level = get_env_loglevel()
    if level is None:
        level = logging.WARNING
    log.setLevel(level)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(levelname)-8s] %(name)s: %(message)s"))
    log.addHandler(handler)
    log.propagate = False


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


def warn_extra_fields(
    params: dict, fieldname: str | None, valid: Optional[list[str]] = None
) -> None:
    """
    For each key in ``params``, emit a log message indicating that the given
    parameter is ignored, along with a "Did you mean?" message if ``valid`` is
    set and the key resembles any elements of ``valid``.  ``fieldname`` is the
    name of the table in which ``params`` were found relative to the root of
    the versioningit config; `None` means that the params were found at the top
    of the config.
    """
    if fieldname is None:
        where = "versioningit configuration"
    else:
        where = f"versioningit's {fieldname}"
    for p in params.keys():
        suggestions = didyoumean(p, valid) if valid is not None else ""
        log.warning("Ignoring unknown parameter %r in %s%s", p, where, suggestions)


def warn_bad_version(version: str, desc: str) -> None:
    """
    If ``version`` is not :pep:`440`-compliant, log a warning.  ``desc`` is a
    description of the version's provenance.
    """
    try:
        Version(version)
    except ValueError:
        log.warning("%s %r is not PEP 440-compliant", desc, version)


def didyoumean(mistake: str, valid: Iterable[str]) -> str:
    """
    If ``mistake`` resembles any elements of ``valid``, return a "Did you
    mean?" message enclosed in parentheses and starting with a space.  If
    ``mistake`` is not similar to any elements of ``valid``, return an empty
    string.
    """
    candidates = get_close_matches(mistake, valid)
    if candidates:
        return " (Did you mean:" + "".join(f" {c}?" for c in candidates) + ")"
    else:
        return ""
