from dataclasses import dataclass
import re
from typing import Any, List, Optional
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
