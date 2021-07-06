import logging
import pytest
from versioningit.logging import parse_log_level


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
