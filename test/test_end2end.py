import logging
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Iterator, List, Optional, Tuple, Union, cast
from _pytest.mark.structures import ParameterSet
from pydantic import BaseModel, Field
import pytest
from versioningit.core import get_next_version, get_version, get_version_from_pkg_info
from versioningit.errors import Error, NotVersioningitError
from versioningit.util import parse_version_from_metadata, readcmd

DATA_DIR = Path(__file__).with_name("data")

needs_git = pytest.mark.skipif(shutil.which("git") is None, reason="Git not installed")

needs_hg = pytest.mark.skipif(
    shutil.which("hg") is None, reason="Mercurial not installed"
)


class File(BaseModel):
    sdist_path: Optional[str]
    wheel_path: Optional[str]
    contents: str
    encoding: str = "utf-8"
    in_project: bool = True

    def check(self, dirpath: Path, mode: str) -> None:
        if mode == "project" or mode == "sdist":
            if self.sdist_path is None:
                return
            path = dirpath / self.sdist_path
        elif self.wheel_path is None:
            return
        else:
            path = dirpath / self.wheel_path
        if self.in_project or mode != "project":
            assert path.read_text(encoding=self.encoding) == self.contents
        else:
            try:
                assert path.read_text(encoding=self.encoding) != self.contents
            except FileNotFoundError:
                pass


class LogMsg(BaseModel):
    level: str
    message: str

    def as_tuple(self) -> Tuple[str, int, str]:
        return ("versioningit", getattr(logging, self.level), self.message)


class ErrorDetails(BaseModel):
    type: str
    message: str


class CaseDetails(BaseModel):
    version: str
    next_version: Union[str, ErrorDetails]
    local_modules: List[str] = Field(default_factory=list)
    files: List[File] = Field(default_factory=list)
    logmsgs: List[LogMsg] = Field(default_factory=list)


def mkcases() -> Iterator[ParameterSet]:
    for subdir, marks in [
        ("git", [needs_git]),
        ("hg", [needs_hg]),
        ("archives", cast(List[pytest.MarkDecorator], [])),
    ]:
        for repozip in sorted((DATA_DIR / "repos" / subdir).glob("*.zip")):
            details = CaseDetails.parse_file(repozip.with_suffix(".json"))
            try:
                marknames = repozip.with_suffix(".marks").read_text().splitlines()
            except FileNotFoundError:
                marknames = []
            yield pytest.param(
                repozip,
                details,
                marks=marks + [getattr(pytest.mark, m) for m in marknames],
                id=f"{subdir}/{repozip.stem}",
            )


@pytest.mark.parametrize("repozip,details", mkcases())
def test_end2end(
    caplog: pytest.LogCaptureFixture,
    repozip: Path,
    details: CaseDetails,
    tmp_path: Path,
) -> None:
    srcdir = tmp_path / "src"
    shutil.unpack_archive(str(repozip), str(srcdir))
    status = get_repo_status(srcdir)
    assert (
        get_version(project_dir=srcdir, write=False, fallback=False) == details.version
    )
    if isinstance(details.next_version, str):
        assert get_next_version(srcdir) == details.next_version
    else:
        with pytest.raises(Error) as excinfo:
            get_next_version(srcdir)
        assert type(excinfo.value).__name__ == details.next_version.type
        assert str(excinfo.value) == details.next_version.message
    for lm in details.logmsgs:
        assert lm.as_tuple() in caplog.record_tuples
    for modname in details.local_modules:
        # So that we can do multiple tests that load different modules with the
        # same name
        del sys.modules[modname]

    subprocess.run(
        [sys.executable, "-m", "build", "--no-isolation", str(srcdir)],
        check=True,
        env={**os.environ, "VERSIONINGIT_LOG_LEVEL": "DEBUG"},
    )
    assert get_repo_status(srcdir) == status
    for f in details.files:
        f.check(srcdir, "project")

    sdist_src = unpack_sdist(srcdir / "dist", tmp_path)
    assert get_version_from_pkg_info(sdist_src) == details.version
    for f in details.files:
        f.check(sdist_src, "sdist")

    wheel_src, wheel_dist_info = unpack_wheel(srcdir / "dist", tmp_path)
    metadata = (wheel_dist_info / "METADATA").read_text(encoding="utf-8")
    assert parse_version_from_metadata(metadata) == details.version
    for f in details.files:
        f.check(wheel_src, "wheel")


def test_end2end_no_versioningit(tmp_path: Path) -> None:
    srcdir = tmp_path / "src"
    shutil.unpack_archive(str(DATA_DIR / "repos" / "no-versioningit.zip"), str(srcdir))
    with pytest.raises(NotVersioningitError) as excinfo:
        get_version(project_dir=srcdir, write=False, fallback=True)
    assert str(excinfo.value) == "versioningit not enabled in pyproject.toml"
    with pytest.raises(NotVersioningitError) as excinfo:
        get_next_version(srcdir)
    assert str(excinfo.value) == "versioningit not enabled in pyproject.toml"

    out = readcmd(
        sys.executable,
        "-m",
        "build",
        "--no-isolation",
        srcdir,
        env={**os.environ, "VERSIONINGIT_LOG_LEVEL": "DEBUG"},
        stderr=subprocess.STDOUT,
    )
    assert (
        "[INFO    ] versioningit: versioningit not enabled in pyproject.toml;"
        " doing nothing" in out.splitlines()
    )

    sdist_src = unpack_sdist(srcdir / "dist", tmp_path)
    assert get_version_from_pkg_info(sdist_src) == "0.0.0"

    _, wheel_dist_info = unpack_wheel(srcdir / "dist", tmp_path)
    metadata = (wheel_dist_info / "METADATA").read_text(encoding="utf-8")
    assert parse_version_from_metadata(metadata) == "0.0.0"


def test_end2end_no_pyproject(tmp_path: Path) -> None:
    srcdir = tmp_path / "src"
    shutil.unpack_archive(str(DATA_DIR / "repos" / "no-pyproject.zip"), str(srcdir))
    with pytest.raises(NotVersioningitError) as excinfo:
        get_version(project_dir=srcdir, write=False, fallback=True)
    assert str(excinfo.value) == f"No pyproject.toml file in {srcdir}"
    with pytest.raises(NotVersioningitError) as excinfo:
        get_next_version(srcdir)
    assert str(excinfo.value) == f"No pyproject.toml file in {srcdir}"

    out = readcmd(
        sys.executable,
        "-m",
        "build",
        "--no-isolation",
        srcdir,
        env={**os.environ, "VERSIONINGIT_LOG_LEVEL": "DEBUG"},
        stderr=subprocess.STDOUT,
    )
    assert (
        "[INFO    ] versioningit: versioningit not enabled in pyproject.toml;"
        " doing nothing" in out.splitlines()
    )

    sdist_src = unpack_sdist(srcdir / "dist", tmp_path)
    assert get_version_from_pkg_info(sdist_src) == "0.0.0"

    _, wheel_dist_info = unpack_wheel(srcdir / "dist", tmp_path)
    metadata = (wheel_dist_info / "METADATA").read_text(encoding="utf-8")
    assert parse_version_from_metadata(metadata) == "0.0.0"


@needs_git
@pytest.mark.parametrize(
    "zipname,version",
    [
        ("no-versioningit.zip", "0.1.0.post1+g1300c65"),
        ("no-pyproject.zip", "0.1.0.post1+g6bedd1f"),
    ],
)
def test_get_version_config_only(tmp_path: Path, zipname: str, version: str) -> None:
    shutil.unpack_archive(str(DATA_DIR / "repos" / zipname), str(tmp_path))
    assert (
        get_version(project_dir=tmp_path, config={}, write=False, fallback=True)
        == version
    )


@needs_git
@pytest.mark.describe_exclude
def test_end2end_error(tmp_path: Path) -> None:
    shutil.unpack_archive(str(DATA_DIR / "repos" / "error.zip"), str(tmp_path))
    with pytest.raises(Error) as excinfo:
        get_version(project_dir=tmp_path, write=False, fallback=True)
    errdata = ErrorDetails.parse_file(DATA_DIR / "repos" / "error.json")
    assert type(excinfo.value).__name__ == errdata.type
    assert str(excinfo.value) == errdata.message
    r = subprocess.run(
        [sys.executable, "-m", "build", "--no-isolation", str(tmp_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    )
    assert r.returncode != 0
    out = r.stdout
    assert isinstance(out, str)
    assert errdata.message in out


@needs_git
@pytest.mark.parametrize("zipname", ["no-git.zip", "shallow.zip"])
def test_end2end_version_not_found(tmp_path: Path, zipname: str) -> None:
    shutil.unpack_archive(str(DATA_DIR / "repos" / zipname), str(tmp_path))
    r = subprocess.run(
        [sys.executable, "-m", "build", "--no-isolation", str(tmp_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    )
    assert r.returncode != 0
    out = r.stdout
    assert isinstance(out, str)
    assert (
        "\nversioningit could not find a version for the project in"
        f" {tmp_path}!\n\n"
        "You may be installing from a shallow clone, in which case you"
        " need to unshallow it first.\n\n"
        "Alternatively, you may be installing from a Git archive, which is"
        " not supported by default.  Install from a git+https://... URL instead.\n\n"
    ) in out


def test_build_from_sdist(tmp_path: Path) -> None:
    # This test is used to check that building from an sdist succeeds even when
    # a VCS is not installed, though it passes when one is installed as well.
    srcdir = tmp_path / "sdist"
    shutil.unpack_archive(str(DATA_DIR / "mypackage-0.1.0.tar.gz"), str(srcdir))
    (sdist_src,) = srcdir.iterdir()
    assert get_version(project_dir=sdist_src, write=False, fallback=True) == "0.1.0"
    subprocess.run(
        [sys.executable, "-m", "build", "--no-isolation", "--wheel", str(sdist_src)],
        check=True,
    )
    _, wheel_dist_info = unpack_wheel(sdist_src / "dist", tmp_path)
    metadata = (wheel_dist_info / "METADATA").read_text(encoding="utf-8")
    assert parse_version_from_metadata(metadata) == "0.1.0"


@needs_git
def test_build_wheel_directly(tmp_path: Path) -> None:
    repozip = DATA_DIR / "repos" / "git" / "onbuild-write.zip"
    details = CaseDetails.parse_file(repozip.with_suffix(".json"))
    srcdir = tmp_path / "src"
    shutil.unpack_archive(str(repozip), str(srcdir))

    subprocess.run(
        [sys.executable, "-m", "build", "--no-isolation", "--wheel", str(srcdir)],
        check=True,
    )
    for f in details.files:
        f.check(srcdir, "project")

    wheel_src, wheel_dist_info = unpack_wheel(srcdir / "dist", tmp_path)
    metadata = (wheel_dist_info / "METADATA").read_text(encoding="utf-8")
    assert parse_version_from_metadata(metadata) == details.version
    for f in details.files:
        f.check(wheel_src, "wheel")


@needs_git
@pytest.mark.parametrize(
    "cmd",
    [
        ["-m", "pip", "install", "--no-build-isolation", "-e", "."],
        ["setup.py", "develop"],
    ],
)
def test_editable_mode(cmd: List[str], tmp_path: Path) -> None:
    repozip = DATA_DIR / "repos" / "git" / "onbuild-write.zip"
    details = CaseDetails.parse_file(repozip.with_suffix(".json"))
    srcdir = tmp_path / "src"
    shutil.unpack_archive(str(repozip), str(srcdir))
    status = get_repo_status(srcdir)
    subprocess.run([sys.executable, *cmd], cwd=str(srcdir), check=True)
    try:
        assert get_repo_status(srcdir) == status
        info = readcmd(sys.executable, "-m", "pip", "show", "mypackage")
        assert parse_version_from_metadata(info) == details.version
        for f in details.files:
            f.check(srcdir, "project")
    finally:
        subprocess.run(
            [sys.executable, "-m", "pip", "uninstall", "--yes", "mypackage"], check=True
        )


@needs_git
def test_setup_py(tmp_path: Path) -> None:
    repozip = DATA_DIR / "repos" / "git" / "onbuild-write.zip"
    details = CaseDetails.parse_file(repozip.with_suffix(".json"))
    srcdir = tmp_path / "src"
    shutil.unpack_archive(str(repozip), str(srcdir))
    status = get_repo_status(srcdir)

    subprocess.run(
        [sys.executable, "setup.py", "sdist", "bdist_wheel"],
        cwd=str(srcdir),
        check=True,
        env={**os.environ, "VERSIONINGIT_LOG_LEVEL": "DEBUG"},
    )
    assert get_repo_status(srcdir) == status
    for f in details.files:
        f.check(srcdir, "project")

    sdist_src = unpack_sdist(srcdir / "dist", tmp_path)
    assert get_version_from_pkg_info(sdist_src) == details.version
    for f in details.files:
        f.check(sdist_src, "sdist")

    wheel_src, wheel_dist_info = unpack_wheel(srcdir / "dist", tmp_path)
    metadata = (wheel_dist_info / "METADATA").read_text(encoding="utf-8")
    assert parse_version_from_metadata(metadata) == details.version
    for f in details.files:
        f.check(wheel_src, "wheel")


def get_repo_status(repodir: Path) -> str:
    if (repodir / ".git").exists():
        return readcmd("git", "status", "--porcelain", cwd=str(repodir))
    elif (repodir / ".hg").exists():
        return readcmd(
            "hg", "--cwd", repodir, "status", env={**os.environ, "HGPLAIN": "1"}
        )
    else:
        return ""


def unpack_sdist(dist_dir: Path, tmp_path: Path) -> Path:
    (sdist,) = dist_dir.glob("*.tar.gz")
    shutil.unpack_archive(str(sdist), str(tmp_path / "sdist"))
    (sdist_src,) = (tmp_path / "sdist").iterdir()
    return sdist_src


def unpack_wheel(dist_dir: Path, tmp_path: Path) -> Tuple[Path, Path]:
    (wheel,) = dist_dir.glob("*.whl")
    wheel_src = tmp_path / "wheel"
    shutil.unpack_archive(str(wheel), str(wheel_src), "zip")
    (wheel_dist_info,) = wheel_src.glob("*.dist-info")
    return (wheel_src, wheel_dist_info)
