from __future__ import annotations
from datetime import datetime, timezone
import logging
from typing import Any, Optional
import pytest
from versioningit.basics import basic_template_fields
from versioningit.core import VCSDescription
from versioningit.errors import ConfigError, InvalidVersionError

BUILD_DATE = datetime(2038, 1, 19, 3, 14, 7, tzinfo=timezone.utc)

DESCRIPTION = VCSDescription(
    tag="v0.1.0",
    state="distance",
    branch="main",
    fields={
        "distance": 5,
        "vcs": "g",
        "rev": "abcdef0",
        "build_date": BUILD_DATE,
    },
)


@pytest.mark.parametrize(
    "version,params,version_tuple,warnings",
    [
        ("0.1.0.post5+gabcdef0", {}, '(0, 1, 0, "post5", "gabcdef0")', []),
        (
            "0.1.0.post5+gabcdef0",
            {"version-tuple": {"double-quote": False}},
            "(0, 1, 0, 'post5', 'gabcdef0')",
            [],
        ),
        (
            "0.1.0.post5+gabcdef0",
            {"version-tuple": {"split-on": "[.]"}},
            '(0, 1, 0, "post5+gabcdef0")',
            [],
        ),
        (
            "0.1.0.post5+gabcdef0",
            {"version-tuple": {"epoch": True}},
            '(0, 1, 0, "post5", "gabcdef0")',
            [
                "tool.versioningit.template-fields.version-tuple.epoch is"
                " ignored when pep440 is false"
            ],
        ),
        (
            "0.1.0.post5+gabcdef0",
            {"version-tuple": {"pep440": True}},
            '(0, 1, 0, "post5", "+gabcdef0")',
            [],
        ),
        (
            "0.1.0.post5+gabcdef0",
            {"version-tuple": {"pep440": True, "epoch": True}},
            '(0, 0, 1, 0, "post5", "+gabcdef0")',
            [],
        ),
        (
            "0.1.0.post5+gabcdef0",
            {"version-tuple": {"pep440": True, "double-quote": False}},
            "(0, 1, 0, 'post5', '+gabcdef0')",
            [],
        ),
        (
            "0.1.0.post5+gabcdef0",
            {"version-tuple": {"pep440": True, "split-on": "[.]"}},
            '(0, 1, 0, "post5", "+gabcdef0")',
            [
                "tool.versioningit.template-fields.version-tuple.split-on is"
                " ignored when pep440 is true"
            ],
        ),
        ("1.2.3j", {}, '(1, 2, "3j")', []),
    ],
)
def test_basic_template_fields(
    caplog: pytest.LogCaptureFixture,
    version: str,
    params: dict[str, Any],
    version_tuple: str,
    warnings: list[str],
) -> None:
    assert basic_template_fields(
        version=version,
        description=DESCRIPTION,
        base_version="0.1.0",
        next_version="0.2.0",
        params=params,
    ) == {
        "distance": 5,
        "vcs": "g",
        "rev": "abcdef0",
        "build_date": BUILD_DATE,
        "branch": "main",
        "version": version,
        "version_tuple": version_tuple,
        "base_version": "0.1.0",
        "next_version": "0.2.0",
    }
    assert caplog.record_tuples == [
        ("versioningit", logging.WARNING, msg) for msg in warnings
    ]


@pytest.mark.parametrize("cfg", [True, "1.2.3", [1, 2, 3]])
def test_basic_template_fields_bad_version_tuple(cfg: Any) -> None:
    with pytest.raises(ConfigError) as excinfo:
        basic_template_fields(
            version="0.1.0.post1",
            description=DESCRIPTION,
            base_version="0.1.0",
            next_version="0.2.0",
            params={"version-tuple": cfg},
        )
    assert (
        str(excinfo.value)
        == "tool.versioningit.template-fields.version-tuple must be a table"
    )


def test_basic_template_fields_bad_pep440_version() -> None:
    with pytest.raises(InvalidVersionError) as excinfo:
        basic_template_fields(
            version="1.2.3j",
            description=DESCRIPTION,
            base_version="1.2.3",
            next_version="1.3.0",
            params={"version-tuple": {"pep440": True}},
        )
    assert str(excinfo.value) == "'1.2.3j' is not a valid PEP 440 version"


@pytest.mark.parametrize(
    "description,base_version,next_version,fields",
    [
        (
            None,
            None,
            None,
            {"version": "1.2.3.post5", "version_tuple": '(1, 2, 3, "post5")'},
        ),
        (
            DESCRIPTION,
            None,
            None,
            {
                "version": "1.2.3.post5",
                "version_tuple": '(1, 2, 3, "post5")',
                "distance": 5,
                "vcs": "g",
                "rev": "abcdef0",
                "build_date": BUILD_DATE,
                "branch": "main",
            },
        ),
        (
            DESCRIPTION,
            "1.2.3",
            None,
            {
                "version": "1.2.3.post5",
                "version_tuple": '(1, 2, 3, "post5")',
                "distance": 5,
                "vcs": "g",
                "rev": "abcdef0",
                "build_date": BUILD_DATE,
                "branch": "main",
                "base_version": "1.2.3",
            },
        ),
    ],
)
def test_basic_template_fields_none_inputs(
    description: Optional[VCSDescription],
    base_version: Optional[str],
    next_version: Optional[str],
    fields: dict[str, Any],
) -> None:
    assert (
        basic_template_fields(
            version="1.2.3.post5",
            description=description,
            base_version=base_version,
            next_version=next_version,
            params={},
        )
        == fields
    )
