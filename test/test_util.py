from __future__ import annotations
from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
from typing import Any, Optional
import pytest
from versioningit.errors import ConfigError, InvalidVersionError
from versioningit.git import DescribeOpts
from versioningit.util import (
    bool_guard,
    ensure_terminated,
    fromtimestamp,
    get_build_date,
    list_str_guard,
    optional_str_guard,
    parse_version_from_metadata,
    qqrepr,
    showcmd,
    split_pep440_version,
    split_version,
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
    assert str(excinfo.value) == "test must be set to a string"


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


@pytest.mark.parametrize("v", [True, False])
def test_bool_guard_bool(v: bool) -> None:
    b = bool_guard(v, "test")
    assert b is v
    assert isinstance(b, bool)


@pytest.mark.parametrize("v", [None, 1, "yes", 0, "no", ["foo"], "bar", 42])
def test_bool_guard_not_bool(v: Any) -> None:
    with pytest.raises(ConfigError) as excinfo:
        bool_guard(v, "test")
    assert str(excinfo.value) == "test must be set to a boolean"


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
def test_showcmd(cmd: list[str | Path], s: str) -> None:
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


@pytest.mark.parametrize(
    "fmt,opts,args",
    [
        ("$Format:%(describe)$", DescribeOpts(tags=False, match=[], exclude=[]), []),
        ("$Format:%(describe:)$", DescribeOpts(tags=False, match=[], exclude=[]), []),
        (
            "$Format:%(describe:tags)$",
            DescribeOpts(tags=True, match=[], exclude=[]),
            ["--tags"],
        ),
        (
            "$Format:%(describe:tags,)$",
            DescribeOpts(tags=True, match=[], exclude=[]),
            ["--tags"],
        ),
        (
            "$Format:%(describe:tags=yes)$",
            DescribeOpts(tags=True, match=[], exclude=[]),
            ["--tags"],
        ),
        (
            "$Format:%(describe:tags=YES)$",
            DescribeOpts(tags=True, match=[], exclude=[]),
            ["--tags"],
        ),
        (
            "$Format:%(describe:tags=Yes)$",
            DescribeOpts(tags=True, match=[], exclude=[]),
            ["--tags"],
        ),
        (
            "$Format:%(describe:tags=on)$",
            DescribeOpts(tags=True, match=[], exclude=[]),
            ["--tags"],
        ),
        (
            "$Format:%(describe:tags=ON)$",
            DescribeOpts(tags=True, match=[], exclude=[]),
            ["--tags"],
        ),
        (
            "$Format:%(describe:tags=true)$",
            DescribeOpts(tags=True, match=[], exclude=[]),
            ["--tags"],
        ),
        (
            "$Format:%(describe:tags=True)$",
            DescribeOpts(tags=True, match=[], exclude=[]),
            ["--tags"],
        ),
        (
            "$Format:%(describe:tags=1)$",
            DescribeOpts(tags=True, match=[], exclude=[]),
            ["--tags"],
        ),
        (
            "$Format:%(describe:tags=no)$",
            DescribeOpts(tags=False, match=[], exclude=[]),
            [],
        ),
        (
            "$Format:%(describe:tags=No)$",
            DescribeOpts(tags=False, match=[], exclude=[]),
            [],
        ),
        (
            "$Format:%(describe:tags=off)$",
            DescribeOpts(tags=False, match=[], exclude=[]),
            [],
        ),
        (
            "$Format:%(describe:tags=OFF)$",
            DescribeOpts(tags=False, match=[], exclude=[]),
            [],
        ),
        (
            "$Format:%(describe:tags=false)$",
            DescribeOpts(tags=False, match=[], exclude=[]),
            [],
        ),
        (
            "$Format:%(describe:tags=fAlsE)$",
            DescribeOpts(tags=False, match=[], exclude=[]),
            [],
        ),
        (
            "$Format:%(describe:tags=0)$",
            DescribeOpts(tags=False, match=[], exclude=[]),
            [],
        ),
        (
            "$Format:%(describe:tags=)$",
            DescribeOpts(tags=False, match=[], exclude=[]),
            [],
        ),
        (
            "$Format:%(describe:tags=ja)$",
            DescribeOpts(tags=False, match=[], exclude=[]),
            [],
        ),
        (
            "$Format:%(describe:tags=yes,tags=)$",
            DescribeOpts(tags=False, match=[], exclude=[]),
            [],
        ),
        (
            "$Format:%(describe:tags=,tags=yes)$",
            DescribeOpts(tags=True, match=[], exclude=[]),
            ["--tags"],
        ),
        (
            "$Format:%(describe:match=v*)$",
            DescribeOpts(tags=False, match=["v*"], exclude=[]),
            ["--match=v*"],
        ),
        (
            "$Format:%(describe:match=v*,match=rel*)$",
            DescribeOpts(tags=False, match=["v*", "rel*"], exclude=[]),
            ["--match=v*", "--match=rel*"],
        ),
        (
            "$Format:%(describe:match=v*,exclude=*rc,match=rel*)$",
            DescribeOpts(tags=False, match=["v*", "rel*"], exclude=["*rc"]),
            ["--match=v*", "--match=rel*", "--exclude=*rc"],
        ),
        (
            "$Format:%(describe:match=v*,tags,exclude=*rc,match=rel*)$",
            DescribeOpts(tags=True, match=["v*", "rel*"], exclude=["*rc"]),
            ["--tags", "--match=v*", "--match=rel*", "--exclude=*rc"],
        ),
        (
            "$Format:%(describe:exclude=\\,)$",
            DescribeOpts(tags=False, match=[], exclude=["\\"]),
            ["--exclude=\\"],
        ),
        (
            "$Format:%(describe:exclude=\\*,)$",
            DescribeOpts(tags=False, match=[], exclude=["\\*"]),
            ["--exclude=\\*"],
        ),
    ],
)
def test_parse_describe_opts(fmt: str, opts: DescribeOpts, args: list[str]) -> None:
    actual = DescribeOpts.parse_describe_subst(fmt)
    assert actual == opts
    assert actual.as_args() == args


@pytest.mark.parametrize(
    "fmt,errmsg",
    [
        (
            "%(describe)",
            "Expected string in format '$Format:%(describe[:options])$',"
            " got '%(describe)'",
        ),
        (
            "$Format:%(describe=tags)$",
            "Expected string in format '$Format:%(describe[:options])$',"
            " got '$Format:%(describe=tags)$'",
        ),
        (
            "$Format:%(describe,tags)$",
            "Expected string in format '$Format:%(describe[:options])$',"
            " got '$Format:%(describe,tags)$'",
        ),
        ("$Format:%(describe:,)$", "Unknown option: ''"),
        ("$Format:%(describe:,tags)$", "Unknown option: ''"),
        ("$Format:%(describe:tags,,)$", "Unknown option: ''"),
        ("$Format:%(describe:match)$", "Option missing value: 'match'"),
        ("$Format:%(describe:match=)$", "Option missing value: 'match='"),
        ("$Format:%(describe:exclude)$", "Option missing value: 'exclude'"),
        ("$Format:%(describe:exclude=)$", "Option missing value: 'exclude='"),
        ("$Format:%(describe:unknown=value)$", "Unknown option: 'unknown=value'"),
    ],
)
def test_parse_bad_describe_opts(fmt: str, errmsg: str) -> None:
    with pytest.raises(ValueError) as excinfo:
        DescribeOpts.parse_describe_subst(fmt)
    assert str(excinfo.value) == errmsg


@pytest.mark.parametrize(
    "v,split_on,double_quote,vtuple",
    [
        ("1.2.3+local.2022", None, True, '(1, 2, 3, "local", 2022)'),
        ("1.2.3-1", None, True, "(1, 2, 3, 1)"),
        ("1.2.3_r2", None, True, '(1, 2, 3, "r2")'),
        ("1!2.3.4", None, True, "(1, 2, 3, 4)"),
        ("1.2.3+local.2022", r"\.|(\+.+)", True, '(1, 2, 3, "+local.2022")'),
        ("1.2.3_r2", None, False, "(1, 2, 3, 'r2')"),
        ("1.2.3j", None, True, '(1, 2, "3j")'),
    ],
)
def test_split_version(
    v: str, split_on: Optional[str], double_quote: bool, vtuple: str
) -> None:
    assert split_version(v, split_on, double_quote) == vtuple


@pytest.mark.parametrize(
    "v,double_quote,epoch,vtuple",
    [
        ("1.2.3", True, None, "(1, 2, 3)"),
        ("1.2.3", True, True, "(0, 1, 2, 3)"),
        ("1.2.3", True, False, "(1, 2, 3)"),
        ("1!2.3.4", True, None, "(1, 2, 3, 4)"),
        ("1!2.3.4", True, True, "(1, 2, 3, 4)"),
        ("1!2.3.4", True, False, "(2, 3, 4)"),
        ("0.1.0", True, None, "(0, 1, 0)"),
        ("1.0.0.0", True, None, "(1, 0, 0, 0)"),
        ("1.2.3a0", True, None, '(1, 2, 3, "a0")'),
        ("1.2.3a0.dev1", True, None, '(1, 2, 3, "a0", "dev1")'),
        ("1.2.3a0.dev1", False, None, "(1, 2, 3, 'a0', 'dev1')"),
        ("1.2.3a0.post1", True, None, '(1, 2, 3, "a0", "post1")'),
        ("1.2.3-1", True, None, '(1, 2, 3, "post1")'),
        ("1.2.3a0.post1.dev1", True, None, '(1, 2, 3, "a0", "post1", "dev1")'),
        (
            "1.2.3a0.post1.dev1+local",
            True,
            None,
            '(1, 2, 3, "a0", "post1", "dev1", "+local")',
        ),
        ("1.2.3.dev1", True, None, '(1, 2, 3, "dev1")'),
        ("1.2.3+local", True, None, '(1, 2, 3, "+local")'),
    ],
)
def test_split_pep440_version(
    v: str, double_quote: bool, epoch: Optional[bool], vtuple: str
) -> None:
    assert split_pep440_version(v, double_quote, epoch) == vtuple


def test_split_pep440_version_bad_version() -> None:
    with pytest.raises(InvalidVersionError) as excinfo:
        split_pep440_version("1.2.3j")
    assert str(excinfo.value) == "'1.2.3j' is not a valid PEP 440 version"


@pytest.mark.parametrize(
    "ins,outs",
    [
        ("foo", '"foo"'),
        ("they're", '"they\'re"'),
        ('"Beware the Jabberwock, my son!"', '"\\"Beware the Jabberwock, my son!\\""'),
    ],
)
def test_qqrepr(ins: str, outs: str) -> None:
    assert qqrepr(ins) == outs


@pytest.mark.parametrize(
    "s,terminated",
    [
        ("", "\n"),
        ("\n", "\n"),
        ("\u2028", "\u2028"),
        ("foobar", "foobar\n"),
        ("foobar\n", "foobar\n"),
        ("foobar\u2028", "foobar\u2028"),
        ("foobar\r", "foobar\r"),
        ("foobar\r\n", "foobar\r\n"),
        ("foobar\n\r", "foobar\n\r"),
        ("foo\nbar", "foo\nbar\n"),
    ],
)
def test_ensure_terminated(s: str, terminated: str) -> None:
    assert ensure_terminated(s) == terminated
