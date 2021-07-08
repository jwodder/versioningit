import logging
import pytest
from versioningit.logging import parse_log_level, warn_bad_version, warn_extra_fields


@pytest.mark.parametrize(
    "name,level",
    [
        ("CRITICAL", logging.CRITICAL),
        ("critical", logging.CRITICAL),
        ("cRiTiCaL", logging.CRITICAL),
        (str(logging.CRITICAL), logging.CRITICAL),
        ("ERROR", logging.ERROR),
        ("error", logging.ERROR),
        ("ErRoR", logging.ERROR),
        (str(logging.ERROR), logging.ERROR),
        ("WARNING", logging.WARNING),
        ("warning", logging.WARNING),
        ("WaRnInG", logging.WARNING),
        (str(logging.WARNING), logging.WARNING),
        ("INFO", logging.INFO),
        ("info", logging.INFO),
        ("iNfO", logging.INFO),
        (str(logging.INFO), logging.INFO),
        ("DEBUG", logging.DEBUG),
        ("debug", logging.DEBUG),
        ("dEbUg", logging.DEBUG),
        (str(logging.DEBUG), logging.DEBUG),
        ("NOTSET", logging.NOTSET),
        ("notset", logging.NOTSET),
        ("NoTsEt", logging.NOTSET),
        (str(logging.NOTSET), logging.NOTSET),
        ("42", 42),
        (" 42 ", 42),
    ],
)
def test_parse_log_level(name: str, level: int) -> None:
    assert parse_log_level(name) == level


@pytest.mark.parametrize("value", ["x", "logging.INFO", "VERBOSE"])
def test_parse_log_level_bad(value: str) -> None:
    with pytest.raises(ValueError) as excinfo:
        parse_log_level(value)
    assert str(excinfo.value) == f"Invalid log level: {value!r}"


def test_warn_extra_fields_empty(caplog: pytest.LogCaptureFixture) -> None:
    warn_extra_fields({}, "test")
    assert caplog.record_tuples == []


def test_warn_extra_fields_some(caplog: pytest.LogCaptureFixture) -> None:
    warn_extra_fields(
        {"mispelled": 42, "extra": ["foo", "bar"]}, "test", ["misspelled"]
    )
    assert caplog.record_tuples == [
        (
            "versioningit",
            logging.WARNING,
            "Ignoring unknown parameter 'mispelled' in test (Did you mean:"
            " misspelled?)",
        ),
        (
            "versioningit",
            logging.WARNING,
            "Ignoring unknown parameter 'extra' in test",
        ),
    ]


@pytest.mark.parametrize("v", ["0.1.0", "0.1.0a", "01.02.03", "v0.1.0"])
def test_warn_bad_version_good(caplog: pytest.LogCaptureFixture, v: str) -> None:
    warn_bad_version(v, "test")
    assert caplog.record_tuples == []


@pytest.mark.parametrize(
    "v",
    [
        "",
        "0.1.",
        "1!",
        "0.1.0j",
        "0.1.0-extra",
        "rel-0.1.0",
        "1!v1.2.3",
        "1!2!3",
    ],
)
def test_warn_bad_version_bad(caplog: pytest.LogCaptureFixture, v: str) -> None:
    warn_bad_version(v, "Test version")
    assert caplog.record_tuples == [
        (
            "versioningit",
            logging.WARNING,
            f"Test version {v!r} is not PEP 440-compliant",
        )
    ]
