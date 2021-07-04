import logging
import pytest


@pytest.fixture(autouse=True)
def capture_all_logs(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.DEBUG, logger="versioningit")


@pytest.fixture(autouse=True)
def source_date_epoch(monkeypatch: pytest.MonkeyPatch) -> None:
    # 2038-01-19T03:14:07Z
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "2147483647")
