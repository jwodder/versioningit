from datetime import datetime, timezone
from typing import Any, Dict
import pytest
from versioningit.basics import basic_format
from versioningit.core import VCSDescription
from versioningit.errors import ConfigError

BUILD_DATE = datetime(2038, 1, 19, 3, 14, 7, tzinfo=timezone.utc)


@pytest.mark.parametrize(
    "description,base_version,next_version,params,r",
    [
        (
            VCSDescription(
                tag="v0.1.0",
                state="distance",
                branch="main",
                fields={
                    "distance": 5,
                    "vcs": "g",
                    "rev": "abcdef0",
                    "build_date": BUILD_DATE,
                },
            ),
            "0.1.0",
            "0.2.0",
            {},
            "0.1.0.post5+gabcdef0",
        ),
        (
            VCSDescription(
                tag="v0.1.0",
                state="dirty",
                branch="main",
                fields={
                    "distance": 0,
                    "vcs": "g",
                    "rev": "abcdef0",
                    "build_date": BUILD_DATE,
                },
            ),
            "0.1.0",
            "0.2.0",
            {},
            "0.1.0+d20380119",
        ),
        (
            VCSDescription(
                tag="v0.1.0",
                state="distance-dirty",
                branch="main",
                fields={
                    "distance": 5,
                    "vcs": "g",
                    "rev": "abcdef0",
                    "build_date": BUILD_DATE,
                },
            ),
            "0.1.0",
            "0.2.0",
            {},
            "0.1.0.post5+gabcdef0.d20380119",
        ),
        (
            VCSDescription(
                tag="v0.1.0",
                state="distance",
                branch="main",
                fields={
                    "distance": 5,
                    "vcs": "g",
                    "rev": "abcdef0",
                    "build_date": BUILD_DATE,
                },
            ),
            "0.1.0",
            "0.2.0",
            {"distance": "{next_version}.dev{distance}+{vcs}{rev}"},
            "0.2.0.dev5+gabcdef0",
        ),
        (
            VCSDescription(
                tag="v0.1.0",
                state="distance",
                branch="feature/acme",
                fields={
                    "distance": 5,
                    "vcs": "g",
                    "rev": "abcdef0",
                    "build_date": BUILD_DATE,
                },
            ),
            "0.1.0",
            "0.2.0",
            {"distance": "{next_version}+{branch}.{rev}"},
            "0.2.0+feature.acme.abcdef0",
        ),
        (
            VCSDescription(
                tag="v0.1.0",
                state="distance",
                branch=None,
                fields={
                    "distance": 5,
                    "vcs": "g",
                    "rev": "abcdef0",
                    "build_date": BUILD_DATE,
                },
            ),
            "0.1.0",
            "0.2.0",
            {"distance": "{next_version}+{branch}.{rev}"},
            "0.2.0+None.abcdef0",
        ),
        (
            VCSDescription(
                tag="v0.1.0",
                state="weird",
                branch="main",
                fields={
                    "distance": 5,
                    "vcs": "g",
                    "rev": "abcdef0",
                    "build_date": BUILD_DATE,
                },
            ),
            "0.1.0",
            "0.2.0",
            {"weird": "{base_version}+{branch}.{build_date:%Y.%m.%d}"},
            "0.1.0+main.2038.01.19",
        ),
    ],
)
def test_basic_format(
    caplog: pytest.LogCaptureFixture,
    description: VCSDescription,
    base_version: str,
    next_version: str,
    params: Dict[str, Any],
    r: str,
) -> None:
    assert (
        basic_format(
            description=description,
            base_version=base_version,
            next_version=next_version,
            params=params,
        )
        == r
    )
    assert caplog.record_tuples == []


def test_basic_format_invalid_state(caplog: pytest.LogCaptureFixture) -> None:
    with pytest.raises(ConfigError) as excinfo:
        basic_format(
            description=VCSDescription(
                tag="v0.1.0",
                state="weird",
                branch="main",
                fields={
                    "distance": 5,
                    "vcs": "g",
                    "rev": "abcdef0",
                    "build_date": BUILD_DATE,
                },
            ),
            base_version="0.1.0",
            next_version="0.2.0",
            params={},
        )
    assert str(excinfo.value) == (
        "No format string for 'weird' state found in tool.versioningit.format"
    )
    assert caplog.record_tuples == []
