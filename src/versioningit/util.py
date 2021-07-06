from datetime import datetime, timezone
import os
from pathlib import Path
import re
import shlex
import subprocess
from typing import Any, List, Union
from .errors import ConfigError
from .logging import log


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
    # <https://reproducible-builds.org/specs/source-date-epoch/>
    try:
        source_date_epoch = int(os.environ["SOURCE_DATE_EPOCH"])
    except (KeyError, ValueError):
        return datetime.now(timezone.utc)
    else:
        return fromtimestamp(source_date_epoch)


def fromtimestamp(ts: int) -> datetime:
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
    for line in metadata.splitlines():
        m = re.match(r"Version\s*:\s*", line)
        if m:
            return line[m.end() :].strip()
        elif not line:
            break
    raise ValueError("Metadata does not contain a Version field")


def showcmd(args: list) -> str:
    return " ".join(shlex.quote(str(a)) for a in args)
