### TODO: Support epochs!
import re
from typing import Any, Tuple
from .logging import warn_extra_fields


def get_version_parts(version: str) -> Tuple[int, ...]:
    m = re.match(r"v?[0-9]+(?:\.[0-9]+)*", version)
    if m is None:
        raise RuntimeError(f"Cannot parse version {version!r}")
    return tuple(map(int, m.group().split(".")))


def next_minor_version(version: str, **kwargs: Any) -> str:
    warn_extra_fields(kwargs, "tool.versioningit.next_version")
    v1, v2, *_ = get_version_parts(version) + (0, 0)
    return f"{v1}.{v2+1}.0"


def next_smallest_version(version: str, **kwargs: Any) -> str:
    warn_extra_fields(kwargs, "tool.versioningit.next_version")
    vparts = get_version_parts(version)
    vparts = vparts[:-1] + (vparts[-1] + 1,)
    return ".".join(map(str, vparts))
