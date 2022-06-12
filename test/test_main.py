import logging
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Optional
import pytest
from pytest_mock import MockerFixture
from versioningit.__main__ import main
from versioningit.errors import Error


def test_command(
    capsys: pytest.CaptureFixture[str],
    mocker: MockerFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "argv", ["versioningit"])
    m = mocker.patch("versioningit.__main__.get_version", return_value="THE VERSION")
    spy = mocker.spy(logging, "basicConfig")
    main()
    m.assert_called_once_with(os.curdir, write=False, fallback=True)
    spy.assert_called_once_with(
        format="[%(levelname)-8s] %(name)s: %(message)s",
        level=logging.WARNING,
    )
    out, err = capsys.readouterr()
    assert out == "THE VERSION\n"
    assert err == ""


def test_command_arg(
    capsys: pytest.CaptureFixture[str], mocker: MockerFixture, tmp_path: Path
) -> None:
    m = mocker.patch("versioningit.__main__.get_version", return_value="THE VERSION")
    main([str(tmp_path)])
    m.assert_called_once_with(str(tmp_path), write=False, fallback=True)
    out, err = capsys.readouterr()
    assert out == "THE VERSION\n"
    assert err == ""


def test_command_write(
    capsys: pytest.CaptureFixture[str], mocker: MockerFixture
) -> None:
    m = mocker.patch("versioningit.__main__.get_version", return_value="THE VERSION")
    main(["--write"])
    m.assert_called_once_with(os.curdir, write=True, fallback=True)
    out, err = capsys.readouterr()
    assert out == "THE VERSION\n"
    assert err == ""


def test_command_next_version(
    capsys: pytest.CaptureFixture[str], mocker: MockerFixture
) -> None:
    m = mocker.patch(
        "versioningit.__main__.get_next_version", return_value="THE NEXT VERSION"
    )
    main(["--next-version"])
    m.assert_called_once_with(os.curdir)
    out, err = capsys.readouterr()
    assert out == "THE NEXT VERSION\n"
    assert err == ""


def test_command_next_version_arg(
    capsys: pytest.CaptureFixture[str], mocker: MockerFixture, tmp_path: Path
) -> None:
    m = mocker.patch(
        "versioningit.__main__.get_next_version", return_value="THE NEXT VERSION"
    )
    main(["-n", str(tmp_path)])
    m.assert_called_once_with(str(tmp_path))
    out, err = capsys.readouterr()
    assert out == "THE NEXT VERSION\n"
    assert err == ""


@pytest.mark.parametrize(
    "arg,logenv,log_level",
    [
        ("-v", None, logging.INFO),
        ("-vv", None, logging.DEBUG),
        ("-vvv", None, logging.DEBUG),
        (None, None, logging.WARNING),
        (None, "ERROR", logging.ERROR),
        (None, "WARNING", logging.WARNING),
        (None, "INFO", logging.INFO),
        (None, "DEBUG", logging.DEBUG),
        ("-v", "ERROR", logging.INFO),
        ("-v", "WARNING", logging.INFO),
        ("-v", "DEBUG", logging.DEBUG),
        ("-vv", "INFO", logging.DEBUG),
        ("-vv", "5", 5),
        ("-vvv", "DEBUG", logging.DEBUG),
    ],
)
def test_command_verbose(
    capsys: pytest.CaptureFixture[str],
    mocker: MockerFixture,
    monkeypatch: pytest.MonkeyPatch,
    arg: Optional[str],
    logenv: Optional[str],
    log_level: int,
) -> None:
    if logenv is None:
        monkeypatch.delenv("VERSIONINGIT_LOG_LEVEL", raising=False)
    else:
        monkeypatch.setenv("VERSIONINGIT_LOG_LEVEL", logenv)
    m = mocker.patch("versioningit.__main__.get_version", return_value="THE VERSION")
    spy = mocker.spy(logging, "basicConfig")
    main([arg] if arg is not None else [])
    m.assert_called_once_with(os.curdir, write=False, fallback=True)
    spy.assert_called_once_with(
        format="[%(levelname)-8s] %(name)s: %(message)s",
        level=log_level,
    )
    out, err = capsys.readouterr()
    assert out == "THE VERSION\n"
    assert err == ""


def test_command_error(
    capsys: pytest.CaptureFixture[str],
    mocker: MockerFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "argv", ["versioningit"])
    m = mocker.patch(
        "versioningit.__main__.get_version", side_effect=Error("Something broke")
    )
    with pytest.raises(SystemExit) as excinfo:
        main()
    assert excinfo.value.args == (1,)
    m.assert_called_once_with(os.curdir, write=False, fallback=True)
    out, err = capsys.readouterr()
    assert out == ""
    assert err == "versioningit: Error: Something broke\n"


@pytest.mark.parametrize(
    "argv,cmd",
    [
        (["git", "get details"], "git 'get details'"),
        ([b"git", b"get details"], "git 'get details'"),
        (["git", "-C", Path("foo"), "gitify"], "git -C foo gitify"),
        ("git 'get details'", "git 'get details'"),
        (b"git 'get details'", "git 'get details'"),
        (Path("git-get-details"), "git-get-details"),
    ],
)
def test_command_subprocess_error(
    caplog: pytest.LogCaptureFixture,
    capsys: pytest.CaptureFixture[str],
    mocker: MockerFixture,
    monkeypatch: pytest.MonkeyPatch,
    argv: Any,
    cmd: str,
) -> None:
    monkeypatch.setattr(sys, "argv", ["versioningit"])
    m = mocker.patch(
        "versioningit.__main__.get_version",
        side_effect=subprocess.CalledProcessError(
            returncode=42, cmd=argv, output=b"", stderr=b""
        ),
    )
    with pytest.raises(SystemExit) as excinfo:
        main()
    assert excinfo.value.args == (42,)
    m.assert_called_once_with(os.curdir, write=False, fallback=True)
    out, err = capsys.readouterr()
    assert out == ""
    assert err == ""
    assert caplog.record_tuples == [
        ("versioningit", logging.ERROR, f"{cmd}: command returned 42")
    ]
