from pathlib import Path
from shutil import copytree
from typing import Any, Dict
import pytest
from versioningit.errors import ConfigError
from versioningit.onbuild import replace_version_onbuild

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
    outfile: str, is_source: bool, params: Dict[str, Any], tmp_path: Path
) -> None:
    tmp_path /= "tmp"  # copytree() can't copy to a dir that already exists
    copytree(DATA_DIR / "replace-version" / "base", tmp_path)
    replace_version_onbuild(
        build_dir=tmp_path,
        is_source=is_source,
        template_fields={"version": "1.2.3"},
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
            assert (
                p.read_bytes()
                == (DATA_DIR / "replace-version" / "base" / p.name).read_bytes()
            )


def test_replace_version_onbuild_require_match(tmp_path: Path) -> None:
    tmp_path /= "tmp"  # copytree() can't copy to a dir that already exists
    copytree(DATA_DIR / "replace-version" / "base", tmp_path)
    with pytest.raises(RuntimeError) as excinfo:
        replace_version_onbuild(
            build_dir=tmp_path,
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
        str(excinfo.value)
        == f"onbuild.regex did not match any lines in {tmp_path / 'source_file.py'}"
    )
    for p in tmp_path.iterdir():
        assert (
            p.read_bytes()
            == (DATA_DIR / "replace-version" / "base" / p.name).read_bytes()
        )


def test_replace_version_onbuild_bad_regex(tmp_path: Path) -> None:
    tmp_path /= "tmp"  # copytree() can't copy to a dir that already exists
    copytree(DATA_DIR / "replace-version" / "base", tmp_path)
    with pytest.raises(
        ConfigError, match=r"^tool\.versioningit\.onbuild\.regex: Invalid regex: .+"
    ):
        replace_version_onbuild(
            build_dir=tmp_path,
            is_source=True,
            template_fields={"version": "1.2.3"},
            params={
                "source-file": "source_file.py",
                "build-file": "wheel_file.py",
                "regex": "(?<foo>)",
            },
        )
    for p in tmp_path.iterdir():
        assert (
            p.read_bytes()
            == (DATA_DIR / "replace-version" / "base" / p.name).read_bytes()
        )


def test_replace_version_onbuild_version_not_captured(tmp_path: Path) -> None:
    tmp_path /= "tmp"  # copytree() can't copy to a dir that already exists
    copytree(DATA_DIR / "replace-version" / "base", tmp_path)
    with pytest.raises(RuntimeError) as excinfo:
        replace_version_onbuild(
            build_dir=tmp_path,
            is_source=True,
            template_fields={"version": "1.2.3"},
            params={
                "source-file": "comment.py",
                "build-file": "wheel_file.py",
                "regex": "__version__ = (?P<version>.*)|# Replace me",
            },
        )
    assert str(excinfo.value) == (
        "'version' group in tool.versioningit.onbuild.regex did"
        " not participate in match"
    )
    for p in tmp_path.iterdir():
        assert (
            p.read_bytes()
            == (DATA_DIR / "replace-version" / "base" / p.name).read_bytes()
        )
