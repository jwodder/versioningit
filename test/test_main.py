import logging
import os
from pathlib import Path
import subprocess
import sys
from _pytest.capture import CaptureFixture
import pytest
from pytest_mock import MockerFixture
from versioningit.__main__ import main
from versioningit.errors import Error


def test_command(
    capsys: CaptureFixture[str], mocker: MockerFixture, monkeypatch: pytest.MonkeyPatch
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
    capsys: CaptureFixture[str], mocker: MockerFixture, tmp_path: Path
) -> None:
    m = mocker.patch("versioningit.__main__.get_version", return_value="THE VERSION")
    main([str(tmp_path)])
    m.assert_called_once_with(str(tmp_path), write=False, fallback=True)
    out, err = capsys.readouterr()
    assert out == "THE VERSION\n"
    assert err == ""


def test_command_write(capsys: CaptureFixture[str], mocker: MockerFixture) -> None:
    m = mocker.patch("versioningit.__main__.get_version", return_value="THE VERSION")
    main(["--write"])
    m.assert_called_once_with(os.curdir, write=True, fallback=True)
    out, err = capsys.readouterr()
    assert out == "THE VERSION\n"
    assert err == ""


def test_command_next_version(
    capsys: CaptureFixture[str], mocker: MockerFixture
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
    capsys: CaptureFixture[str], mocker: MockerFixture, tmp_path: Path
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
    "arg,log_level",
    [
        ("-v", logging.INFO),
        ("-vv", logging.DEBUG),
        ("-vvv", logging.DEBUG),
    ],
)
def test_command_verbose(
    capsys: CaptureFixture[str], mocker: MockerFixture, arg: str, log_level: int
) -> None:
    m = mocker.patch("versioningit.__main__.get_version", return_value="THE VERSION")
    spy = mocker.spy(logging, "basicConfig")
    main([arg])
    m.assert_called_once_with(os.curdir, write=False, fallback=True)
    spy.assert_called_once_with(
        format="[%(levelname)-8s] %(name)s: %(message)s",
        level=log_level,
    )
    out, err = capsys.readouterr()
    assert out == "THE VERSION\n"
    assert err == ""


def test_command_error(
    capsys: CaptureFixture[str], mocker: MockerFixture, monkeypatch: pytest.MonkeyPatch
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


def test_command_subprocess_error(
    caplog: pytest.LogCaptureFixture,
    capsys: CaptureFixture[str],
    mocker: MockerFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "argv", ["versioningit"])
    m = mocker.patch(
        "versioningit.__main__.get_version",
        side_effect=subprocess.CalledProcessError(
            returncode=42, cmd=["git", "-C", ".", "get details"], output=b"", stderr=b""
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
        ("versioningit", logging.ERROR, "git -C . 'get details': command returned 42")
    ]
