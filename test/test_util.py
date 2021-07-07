from datetime import datetime, timedelta, timezone
import pytest
from versioningit.util import get_build_date, strip_prefix, strip_suffix


@pytest.mark.parametrize(
    "s,prefix,r",
    [
        ("foobar", "foo", "bar"),
        ("foobar", "bar", "foobar"),
        ("foobar", "", "foobar"),
        ("foobar", "foobar", ""),
        ("foobar", "foobarx", "foobar"),
        ("foobar", "xfoobar", "foobar"),
    ],
)
def test_strip_prefix(s: str, prefix: str, r: str) -> None:
    assert strip_prefix(s, prefix) == r


@pytest.mark.parametrize(
    "s,suffix,r",
    [
        ("foobar", "bar", "foo"),
        ("foobar", "foo", "foobar"),
        ("foobar", "", "foobar"),
        ("foobar", "foobar", ""),
        ("foobar", "foobarx", "foobar"),
        ("foobar", "xfoobar", "foobar"),
    ],
)
def test_strip_suffix(s: str, suffix: str, r: str) -> None:
    assert strip_suffix(s, suffix) == r


def test_get_build_date_envvar(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1234567890")
    dt = get_build_date()
    assert dt == datetime(2009, 2, 13, 23, 31, 30, tzinfo=timezone.utc)
    assert dt.tzinfo is timezone.utc


def test_get_build_date_now(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)
    dt = get_build_date()
    now = datetime.now(timezone.utc)
    assert timedelta(seconds=0) <= (now - dt) <= timedelta(seconds=2)


def test_get_build_date_bad_epoch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "2009-02-13T23:31:30Z")
    dt = get_build_date()
    now = datetime.now(timezone.utc)
    assert timedelta(seconds=0) <= (now - dt) <= timedelta(seconds=2)
