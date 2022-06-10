from datetime import datetime, timezone
import os
from pathlib import Path
import re
import shlex
import subprocess
from typing import Any, List, Optional, Union
from .errors import ConfigError
from .logging import log


def str_guard(v: Any, fieldname: str) -> str:
    """
    If ``v`` is a `str`, return it; otherwise, raise a `ConfigError`.
    ``fieldname`` is an identifier for ``v`` to include in the error message.
    """
    if isinstance(v, str):
        return v
    else:
        raise ConfigError(f"{fieldname} must be set to a string")


def optional_str_guard(v: Any, fieldname: str) -> Optional[str]:
    """
    If ``v`` is a `str` or `None`, return it; otherwise, raise a `ConfigError`.
    ``fieldname`` is an identifier for ``v`` to include in the error message.
    """
    if v is None or isinstance(v, str):
        return v
    else:
        raise ConfigError(f"{fieldname} must be a string")


def list_str_guard(v: Any, fieldname: str) -> List[str]:
    """
    If ``v`` is a `list` of `str`\\s, return it; otherwise, raise a
    `ConfigError`.  ``fieldname`` is an identifier for ``v`` to include in the
    error message.
    """
    if isinstance(v, list) and all(isinstance(e, str) for e in v):
        return v
    else:
        raise ConfigError(f"{fieldname} must be a list of strings")


def bool_guard(v: Any, fieldname: str) -> bool:
    """
    If ``v`` is a `bool`, return it; otherwise, raise a `ConfigError`.
    ``fieldname`` is an identifier for ``v`` to include in the error message.
    """
    if isinstance(v, bool):
        return v
    else:
        raise ConfigError(f"{fieldname} must be set to a boolean")


def runcmd(*args: Union[str, Path], **kwargs: Any) -> subprocess.CompletedProcess:
    """Run and log a given command"""
    arglist = [str(a) for a in args]
    log.debug("Running: %s", showcmd(arglist))
    kwargs.setdefault("check", True)
    return subprocess.run(arglist, **kwargs)


def readcmd(*args: Union[str, Path], **kwargs: Any) -> str:
    """Run a command, capturing & returning its stdout"""
    s = runcmd(*args, stdout=subprocess.PIPE, universal_newlines=True, **kwargs).stdout
    assert isinstance(s, str)
    return s.strip()


def get_build_date() -> datetime:
    """
    Return the current date & time as an aware UTC `~datetime.datetime`.  If
    :envvar:`SOURCE_DATE_EPOCH` is set, use that value instead (See
    <https://reproducible-builds.org/specs/source-date-epoch/>).
    """
    try:
        source_date_epoch = int(os.environ["SOURCE_DATE_EPOCH"])
    except (KeyError, ValueError):
        return datetime.now(timezone.utc)
    else:
        return fromtimestamp(source_date_epoch)


def fromtimestamp(ts: int) -> datetime:
    """
    Convert an integer number of seconds since the epoch to an aware UTC
    `~datetime.datetime`
    """
    return datetime.fromtimestamp(ts, tz=timezone.utc)


def strip_prefix(s: str, prefix: str) -> str:
    """
    If ``s`` starts with ``prefix``, return the rest of ``s`` after ``prefix``;
    otherwise, return ``s`` unchanged.
    """
    # cf. str.removeprefix, introduced in Python 3.9
    n = len(prefix)
    return s[n:] if s[:n] == prefix else s


def strip_suffix(s: str, suffix: str) -> str:
    """
    If ``s`` ends with ``suffix``, return the rest of ``s`` before ``suffix``;
    otherwise, return ``s`` unchanged.
    """
    # cf. str.removesuffix, introduced in Python 3.9
    n = len(suffix)
    return s[:-n] if s[-n:] == suffix else s


def parse_version_from_metadata(metadata: str) -> str:
    """
    Given a string containing Python packaging metadata, return the value of
    the :mailheader:`Version` field

    :raises ValueError: if there is no :mailheader:`Version` field
    """
    for line in metadata.splitlines():
        m = re.match(r"Version\s*:\s*", line)
        if m:
            return line[m.end() :].strip()
        elif not line:
            break
    raise ValueError("Metadata does not contain a Version field")


def showcmd(args: list) -> str:
    """
    Stringify the elements of ``args``, shell-quote them, and join the results
    with a space
    """
    return " ".join(shlex.quote(str(a)) for a in args)


def is_sdist(project_dir: Union[str, Path]) -> bool:
    """
    Performs a simplistic check whether ``project_dir`` (which presumably is
    not under version control) is an unpacked sdist by testing whether
    :file:`PKG-INFO` exists
    """
    if Path(project_dir, "PKG-INFO").exists():
        log.info(
            "Directory is not under version control, and PKG-INFO is present;"
            " assuming this is an sdist"
        )
        return True
    else:
        return False
