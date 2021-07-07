from dataclasses import dataclass
import re
from typing import Any, List, Optional
from packaging.version import Version
from .errors import InvalidVersionError
from .logging import warn_extra_fields


@dataclass
class BasicVersion:
    epoch: int
    release: List[int]

    @classmethod
    def parse(cls, version: str) -> "BasicVersion":
        m = re.match(
            r"v?(?:(?P<epoch>[0-9]+)!)?(?P<release>[0-9]+(?:\.[0-9]+)*)(?!!)", version
        )
        if not m:
            raise InvalidVersionError(f"Cannot parse version {version!r}")
        sepoch = m["epoch"]
        if sepoch is None:
            epoch = 0  # type: ignore[unreachable]
        else:
            assert isinstance(sepoch, str)
            epoch = int(sepoch)
        release = m["release"]
        assert isinstance(release, str)
        return cls(epoch, list(map(int, release.split("."))))

    def __str__(self) -> str:
        s = ""
        if self.epoch > 0:
            s += f"{self.epoch}!"
        s += ".".join(map(str, self.release))
        return s


def next_minor_version(
    *,
    version: str,
    branch: Optional[str],  # noqa: U100
    **kwargs: Any,
) -> str:
    warn_extra_fields(kwargs, "tool.versioningit.next-version")
    bv = BasicVersion.parse(version)
    bv.release = (bv.release + [0, 0])[:2]
    bv.release[1] += 1
    bv.release.append(0)
    return str(bv)


def next_smallest_version(
    *,
    version: str,
    branch: Optional[str],  # noqa: U100
    **kwargs: Any,
) -> str:
    warn_extra_fields(kwargs, "tool.versioningit.next-version")
    bv = BasicVersion.parse(version)
    bv.release[-1] += 1
    return str(bv)


def null_next_version(
    *,
    version: str,
    branch: Optional[str],  # noqa: U100
    **kwargs: Any,
) -> str:
    warn_extra_fields(kwargs, "tool.versioningit.next-version")
    return version


def next_minor_release_version(
    *,
    version: str,
    branch: Optional[str],  # noqa: U100
    **kwargs: Any,
) -> str:
    """
    If ``version`` is a prerelease version, returns the base version.
    Otherwise, returns the next minor version after the base version.
    """
    warn_extra_fields(kwargs, "tool.versioningit.next-version")
    try:
        v = Version(version)
    except ValueError:
        raise InvalidVersionError(f"Cannot parse version {version!r}")
    if v.is_prerelease:
        return str(v.base_version)
    vs = list(v.release) + [0, 0]
    vs[1] += 1
    vs[2:] = [0]
    s = ".".join(map(str, vs))
    if v.epoch:
        s = f"{v.epoch}!{s}"
    return s


def next_smallest_release_version(
    *,
    version: str,
    branch: Optional[str],  # noqa: U100
    **kwargs: Any,
) -> str:
    """
    If ``version`` is a prerelease version, returns the base version.
    Otherwise, returns the next smallest version after the base version.
    """
    warn_extra_fields(kwargs, "tool.versioningit.next-version")
    try:
        v = Version(version)
    except ValueError:
        raise InvalidVersionError(f"Cannot parse version {version!r}")
    if v.is_prerelease:
        return str(v.base_version)
    vs = list(v.release)
    vs[-1] += 1
    s = ".".join(map(str, vs))
    if v.epoch:
        s = f"{v.epoch}!{s}"
    return s
