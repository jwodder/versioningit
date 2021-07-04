from datetime import datetime, timezone
import os
from pathlib import Path
import subprocess
from typing import Any, List, Union
from .errors import ConfigError
from .logging import logcmd


def str_guard(v: Any, fieldname: str) -> str:
    if isinstance(v, str):
        return v
    else:
        raise ConfigError(f"{fieldname} must be a string")


def list_str_guard(v: Any, fieldname: str) -> List[str]:
    if isinstance(v, list) and all(isinstance(e, str) for e in v):
        return v
    else:
        raise ConfigError(f"{fieldname} must be a list of strings")


def readcmd(*args: Union[str, Path], **kwargs: Any) -> str:
    argstrs = [str(a) for a in args]
    logcmd(argstrs)
    s = subprocess.check_output(argstrs, universal_newlines=True, **kwargs).strip()
    assert isinstance(s, str)
    return s


def get_build_date() -> datetime:
    # <https://reproducible-builds.org/specs/source-date-epoch/>
    try:
        source_date_epoch = int(os.environ["SOURCE_DATE_EPOCH"])
    except (KeyError, ValueError):
        return datetime.now(timezone.utc)
    else:
        return datetime.fromtimestamp(source_date_epoch, tz=timezone.utc)


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
