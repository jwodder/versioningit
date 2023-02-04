from __future__ import annotations
import logging
import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--oldsetup",
        action="store_true",
        default=False,
        help="Run tests that require older setuptools",
    )


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    if not config.getoption("--oldsetup"):
        skipper = pytest.mark.skip(reason="Only run when --oldsetup is given")
        for item in items:
            if "oldsetup" in item.keywords:
                item.add_marker(skipper)


@pytest.fixture(autouse=True)
def capture_all_logs(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.DEBUG, logger="versioningit")


@pytest.fixture(autouse=True)
def source_date_epoch(monkeypatch: pytest.MonkeyPatch) -> None:
    # 2038-01-19T03:14:07Z
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "2147483647")
