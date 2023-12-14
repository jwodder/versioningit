from __future__ import annotations
from datetime import datetime, timezone
import os
from pathlib import Path
from shutil import copytree
from typing import TYPE_CHECKING, Any
import pytest
from versioningit.errors import ConfigError
from versioningit.onbuild import (
    HatchFileProvider,
    OnbuildFileProvider,
    SetuptoolsFileProvider,
    replace_version_onbuild,
)

if TYPE_CHECKING:
    from typing_extensions import Literal

DATA_DIR = Path(__file__).parent.with_name("data")


@pytest.mark.parametrize(
    "outfile,is_source,params",
    [
        (
            "source.py",
            True,
            {"source-file": "source_file.py", "build-file": "wheel_file.py"},
        ),
        (
            "not-source.py",
            False,
            {"source-file": "source_file.py", "build-file": "wheel_file.py"},
        ),
        (
            "replacement.py",
            True,
            {
                "source-file": "source_file.py",
                "build-file": "wheel_file.py",
                "replacement": 'importlib.metadata.version("mypackage")',
            },
        ),
        (
            "with-date.py",
            True,
            {
                "source-file": "source_file.py",
                "build-file": "wheel_file.py",
                "replacement": (
                    '"{version}"\n__build_date__ = "{build_date:%Y%m%dT%H%M%SZ}"'
                ),
            },
        ),
        (
            "line2block.py",
            True,
            {
                "source-file": "source_file.py",
                "build-file": "wheel_file.py",
                "regex": r"^__version__ =.*\s*$",
                "replacement": (
                    "try:\n    from importlib.metadata import version\n"
                    "except ImportError:\n"
                    "    from importlib_metadata import version\n\n"
                    '__version__ = version("mypackage")\n'
                ),
            },
        ),
        (
            "nomatch.py",
            True,
            {
                "source-file": "source_file.py",
                "build-file": "wheel_file.py",
                "regex": r"^does-not-match",
            },
        ),
        (
            "append.py",
            True,
            {
                "source-file": "source_file.py",
                "build-file": "wheel_file.py",
                "regex": r"^does-not-match",
                "append-line": "VERSION = '{version}'",
            },
        ),
        (
            "append-with-date.py",
            True,
            {
                "source-file": "source_file.py",
                "build-file": "wheel_file.py",
                "regex": r"^does-not-match",
                "append-line": (
                    "VERSION = '{version}'\n"
                    "BUILD_DATE = '{build_date:%Y-%m-%dT%H:%M:%SZ}'"
                ),
            },
        ),
        (
            "append-newline.py",
            True,
            {
                "source-file": "source_file.py",
                "build-file": "wheel_file.py",
                "regex": r"^does-not-match",
                "append-line": "VERSION = '{version}'\n",
            },
        ),
        (
            "multi-matches.py",
            True,
            {"source-file": "repeats.py", "build-file": "wheel_file.py"},
        ),
        (
            "latin1-edited.txt",
            True,
            {
                "source-file": "latin1.txt",
                "build-file": "wheel_file.py",
                "encoding": "iso-8859-1",
                "regex": "«»",
                "replacement": "{version}",
            },
        ),
        (
            "still-empty.py",
            True,
            {"source-file": "empty.py", "build-file": "wheel_file.py"},
        ),
        (
            "set-line.py",
            True,
            {
                "source-file": "empty.py",
                "build-file": "wheel_file.py",
                "append-line": '__version__ = "{version}"',
            },
        ),
        (
            "replace-nonl.py",
            True,
            {
                "source-file": "comment.py",
                "build-file": "wheel_file.py",
                "regex": r"^(\s*#+)(?s:.*)",
                "replacement": r"\1 {version}",
            },
        ),
        (
            "nl-append.txt",
            True,
            {
                "source-file": "no-eof-nl.dat",
                "build-file": "wheel_file.py",
                "append-line": "{version}",
            },
        ),
        (
            "line-sepped.py",
            True,
            {
                "source-file": "line-sep.py",
                "build-file": "wheel_file.py",
                "regex": r"^\s*__version__\s*=\s+(?P<version>.+?)\s+",
            },
        ),
    ],
)
def test_replace_version_onbuild(
    outfile: str, is_source: bool, params: dict[str, Any], tmp_path: Path
) -> None:
    src_dir = DATA_DIR / "replace-version" / "base"
    tmp_path /= "tmp"  # copytree() can't copy to a dir that already exists
    copytree(src_dir, tmp_path)
    replace_version_onbuild(
        file_provider=SetuptoolsFileProvider(build_dir=tmp_path),
        is_source=is_source,
        template_fields={
            "version": "1.2.3",
            "build_date": datetime(2038, 1, 19, 3, 14, 7, tzinfo=timezone.utc),
        },
        params=params,
    )
    modfile = params["source-file" if is_source else "build-file"]
    encoding = params.get("encoding", "utf-8")
    for p in tmp_path.iterdir():
        if p.name == modfile:
            assert p.read_text(encoding=encoding) == (
                DATA_DIR / "replace-version" / outfile
            ).read_text(encoding=encoding)
        else:
            assert p.read_bytes() == (src_dir / p.name).read_bytes()


def test_replace_version_onbuild_require_match(tmp_path: Path) -> None:
    src_dir = DATA_DIR / "replace-version" / "base"
    tmp_path /= "tmp"  # copytree() can't copy to a dir that already exists
    copytree(src_dir, tmp_path)
    with pytest.raises(RuntimeError) as excinfo:
        replace_version_onbuild(
            file_provider=SetuptoolsFileProvider(build_dir=tmp_path),
            is_source=True,
            template_fields={"version": "1.2.3"},
            params={
                "source-file": "source_file.py",
                "build-file": "wheel_file.py",
                "regex": "^does-not-match",
                "require-match": True,
            },
        )
    assert (
        str(excinfo.value) == "onbuild.regex did not match any lines in source_file.py"
    )
    for p in tmp_path.iterdir():
        assert p.read_bytes() == (src_dir / p.name).read_bytes()


def test_replace_version_onbuild_bad_regex(tmp_path: Path) -> None:
    src_dir = DATA_DIR / "replace-version" / "base"
    tmp_path /= "tmp"  # copytree() can't copy to a dir that already exists
    copytree(src_dir, tmp_path)
    with pytest.raises(
        ConfigError, match=r"^versioningit: onbuild\.regex: Invalid regex: .+"
    ):
        replace_version_onbuild(
            file_provider=SetuptoolsFileProvider(build_dir=tmp_path),
            is_source=True,
            template_fields={"version": "1.2.3"},
            params={
                "source-file": "source_file.py",
                "build-file": "wheel_file.py",
                "regex": "(?<foo>)",
            },
        )
    for p in tmp_path.iterdir():
        assert p.read_bytes() == (src_dir / p.name).read_bytes()


def test_replace_version_onbuild_version_not_captured(tmp_path: Path) -> None:
    src_dir = DATA_DIR / "replace-version" / "base"
    tmp_path /= "tmp"  # copytree() can't copy to a dir that already exists
    copytree(src_dir, tmp_path)
    with pytest.raises(RuntimeError) as excinfo:
        replace_version_onbuild(
            file_provider=SetuptoolsFileProvider(build_dir=tmp_path),
            is_source=True,
            template_fields={"version": "1.2.3"},
            params={
                "source-file": "comment.py",
                "build-file": "wheel_file.py",
                "regex": "__version__ = (?P<version>.*)|# Replace me",
            },
        )
    assert str(excinfo.value) == (
        "'version' group in versioningit's onbuild.regex did"
        " not participate in match"
    )
    for p in tmp_path.iterdir():
        assert p.read_bytes() == (src_dir / p.name).read_bytes()


@pytest.mark.parametrize("is_source", [False, True])
@pytest.mark.parametrize(
    "mode,after",
    [
        ("w", "Coconut\n"),
        ("a", "{contents}Coconut\n"),
    ],
)
def test_setuptools_file_provider_read_write_read(
    is_source: bool, mode: Literal["w", "a"], after: str, tmp_path: Path
) -> None:
    (tmp_path / "apple.txt").write_text("Apple\n")
    (tmp_path / "banana.txt").write_text("Banana\n")
    provider = SetuptoolsFileProvider(build_dir=tmp_path)
    file = provider.get_file(
        source_path="apple.txt", install_path="banana.txt", is_source=is_source
    )
    with file.open() as fp:
        contents = fp.read()
    if is_source:
        assert contents == "Apple\n"
    else:
        assert contents == "Banana\n"
    with file.open(mode) as fp:
        fp.write("Coconut\n")
    with file.open() as fp:
        contents2 = fp.read()
    assert contents2 == after.format(contents=contents)
    if is_source:
        assert (tmp_path / "apple.txt").read_text() == contents2
        assert (tmp_path / "banana.txt").read_text() == "Banana\n"
    else:
        assert (tmp_path / "apple.txt").read_text() == "Apple\n"
        assert (tmp_path / "banana.txt").read_text() == contents2


@pytest.mark.parametrize("is_source", [False, True])
@pytest.mark.parametrize(
    "mode,after",
    [
        ("w", "Coconut\n"),
        ("a", "Apple\nCoconut\n"),
    ],
)
def test_setuptools_file_provider_read_write_read_hard_link(
    is_source: bool, mode: Literal["w", "a"], after: str, tmp_path: Path
) -> None:
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    build_dir = tmp_path / "build"
    build_dir.mkdir()
    (src_dir / "apple.txt").write_text("Apple\n")
    if is_source:
        os.link(src_dir / "apple.txt", build_dir / "apple.txt")
    else:
        os.link(src_dir / "apple.txt", build_dir / "banana.txt")
    provider = SetuptoolsFileProvider(build_dir=build_dir)
    file = provider.get_file(
        source_path="apple.txt", install_path="banana.txt", is_source=is_source
    )
    with file.open() as fp:
        contents = fp.read()
    assert contents == "Apple\n"
    with file.open(mode) as fp:
        fp.write("Coconut\n")
    with file.open() as fp:
        contents = fp.read()
    assert contents == after
    assert (src_dir / "apple.txt").read_text() == "Apple\n"
    if is_source:
        assert (build_dir / "apple.txt").read_text() == after
        assert not (build_dir / "banana.txt").exists()
    else:
        assert not (build_dir / "apple.txt").exists()
        assert (build_dir / "banana.txt").read_text() == after


@pytest.mark.parametrize("is_source", [False, True])
@pytest.mark.parametrize(
    "mode,after",
    [
        ("w", "Banana\n"),
        ("a", "Apple\nBanana\n"),
    ],
)
def test_hatch_file_provider_read_write_read(
    is_source: bool, mode: Literal["w", "a"], after: str, tmp_path: Path
) -> None:
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    tmp_dir = tmp_path / "tmp"
    tmp_dir.mkdir()
    (src_dir / "apple.txt").write_text("Apple\n")
    provider = HatchFileProvider(src_dir=src_dir, tmp_dir=tmp_dir)
    file = provider.get_file(
        source_path="apple.txt", install_path="banana.txt", is_source=is_source
    )
    with file.open() as fp:
        contents = fp.read()
    assert contents == "Apple\n"
    with file.open(mode) as fp:
        fp.write("Banana\n")
    with file.open() as fp:
        contents = fp.read()
    assert contents == after
    assert (src_dir / "apple.txt").read_text() == "Apple\n"
    if is_source:
        assert (tmp_dir / "apple.txt").read_text() == after
        assert not (tmp_dir / "banana.txt").exists()
    else:
        assert not (tmp_dir / "apple.txt").exists()
        assert (tmp_dir / "banana.txt").read_text() == after


@pytest.mark.parametrize("backend", ["setuptools", "hatch"])
@pytest.mark.parametrize("is_source", [False, True])
@pytest.mark.parametrize("mode", ["w", "a"])
def test_file_provider_write_new_file(
    backend: str, is_source: bool, mode: Literal["w", "a"], tmp_path: Path
) -> None:
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    build_dir = tmp_path / "build"
    build_dir.mkdir()
    provider: OnbuildFileProvider
    if backend == "setuptools":
        provider = SetuptoolsFileProvider(build_dir=build_dir)
    else:
        assert backend == "hatch"
        provider = HatchFileProvider(src_dir=src_dir, tmp_dir=build_dir)
    file = provider.get_file(
        source_path="green/apple.txt",
        install_path="yellow/banana.txt",
        is_source=is_source,
    )
    with file.open(mode) as fp:
        fp.write("Coconut\n")
    with file.open() as fp:
        contents = fp.read()
    assert contents == "Coconut\n"
    assert not (src_dir / "green" / "apple.txt").exists()
    if is_source:
        assert (build_dir / "green" / "apple.txt").read_text() == "Coconut\n"
        assert not (build_dir / "yellow" / "banana.txt").exists()
    else:
        assert not (build_dir / "green" / "apple.txt").exists()
        assert (build_dir / "yellow" / "banana.txt").read_text() == "Coconut\n"
