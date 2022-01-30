from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
from typing import Any, List, Union
import pytest
from versioningit.errors import ConfigError
from versioningit.util import (
    fromtimestamp,
    get_build_date,
    list_str_guard,
    optional_str_guard,
    parse_version_from_metadata,
    showcmd,
    str_guard,
    strip_prefix,
    strip_suffix,
)

DATA_DIR = Path(__file__).with_name("data")


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


def test_str_guard_str() -> None:
    s = str_guard("", "test")
    assert s == ""
    assert isinstance(s, str)


def test_str_guard_not_str() -> None:
    with pytest.raises(ConfigError) as excinfo:
        str_guard(["foo"], "test")
    assert str(excinfo.value) == "test must be a string"


@pytest.mark.parametrize("value", ["", None])
def test_optional_str_guard_good(value: Any) -> None:
    s = optional_str_guard(value, "test")
    assert s == value
    assert s is None or isinstance(s, str)


def test_optional_str_guard_not_bad() -> None:
    with pytest.raises(ConfigError) as excinfo:
        optional_str_guard(["foo"], "test")
    assert str(excinfo.value) == "test must be a string"


@pytest.mark.parametrize("xs", [[], ["foo"], ["foo", "bar"]])
def test_list_str_guard_good(xs: Any) -> None:
    lst = list_str_guard(xs, "test")
    assert lst == xs


@pytest.mark.parametrize("x", ["foo", [42], ["foo", 42], [42, "foo"]])
def test_list_str_guard_bad(x: Any) -> None:
    with pytest.raises(ConfigError) as excinfo:
        list_str_guard(x, "test")
    assert str(excinfo.value) == "test must be a list of strings"


@pytest.mark.parametrize(
    "ts,dt",
    [
        (1234567890, datetime(2009, 2, 13, 23, 31, 30, tzinfo=timezone.utc)),
        (1625686098, datetime(2021, 7, 7, 19, 28, 18, tzinfo=timezone.utc)),
        (2147483647, datetime(2038, 1, 19, 3, 14, 7, tzinfo=timezone.utc)),
    ],
)
def test_fromtimestamp(ts: int, dt: datetime) -> None:
    r = fromtimestamp(ts)
    assert r == dt
    assert r.tzinfo is timezone.utc


@pytest.mark.parametrize(
    "cmd,s",
    [
        (["git", "commit"], "git commit"),
        (
            ["git", "commit", "-m", "The commit message"],
            "git commit -m 'The commit message'",
        ),
        pytest.param(
            ["git", "add", Path("dir/file.txt")],
            "git add dir/file.txt",
            marks=pytest.mark.skipif(os.name != "posix", reason="POSIX only"),
        ),
        pytest.param(
            ["git", "add", Path("dir/file.txt")],
            "git add 'dir\\file.txt'",
            marks=pytest.mark.skipif(os.name != "nt", reason="Windows only"),
        ),
    ],
)
def test_showcmd(cmd: List[Union[str, Path]], s: str) -> None:
    assert showcmd(cmd) == s


@pytest.mark.parametrize(
    "filename,version",
    [
        ("desc-in-header.eml", "0.1.0.post2+g4d891e7"),
        ("desc-in-payload.eml", "0.1.0.post2+g4d891e7"),
        ("version-after-desc.eml", "0.1.0.post2+g4d891e7"),
    ],
)
def test_parse_version_from_metadata(filename: str, version: str) -> None:
    assert (
        parse_version_from_metadata(
            (DATA_DIR / "metadata" / filename).read_text(encoding="utf-8")
        )
        == version
    )


@pytest.mark.parametrize(
    "filename",
    [
        "no-version.eml",
        "no-version-payload.eml",
        "version-in-desc.eml",
    ],
)
def test_parse_version_from_metadata_bad(filename: str) -> None:
    with pytest.raises(ValueError) as excinfo:
        parse_version_from_metadata(
            (DATA_DIR / "metadata" / filename).read_text(encoding="utf-8")
        )
    assert str(excinfo.value) == "Metadata does not contain a Version field"
