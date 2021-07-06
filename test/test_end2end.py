from operator import attrgetter
from pathlib import Path
import shutil
import subprocess
import sys
from typing import List, Optional
from pydantic import BaseModel, Field
import pytest
from versioningit.core import get_version, get_version_from_pkg_info
from versioningit.util import parse_version_from_metadata

DATA_DIR = Path(__file__).with_name("data")


class WriteFile(BaseModel):
    sdist_path: str
    wheel_path: str
    contents: str
    encoding: str = "utf-8"


class CaseDetails(BaseModel):
    version: str
    local_modules: List[str] = Field(default_factory=list)
    write_file: Optional[WriteFile] = None


@pytest.mark.skipif(shutil.which("git") is None, reason="Git not installed")
@pytest.mark.parametrize(
    "repozip",
    sorted((DATA_DIR / "repos" / "git").glob("*.zip")),
    ids=attrgetter("stem"),
)
def test_end2end_git(repozip: Path, tmp_path: Path) -> None:
    details = CaseDetails.parse_file(repozip.with_suffix(".json"))
    srcdir = tmp_path / "src"
    shutil.unpack_archive(str(repozip), str(srcdir))
    assert (
        get_version(project_dir=srcdir, write=False, fallback=False) == details.version
    )
    for modname in details.local_modules:
        # So that we can do multiple tests that load different modules with the
        # same name
        del sys.modules[modname]

    subprocess.run(
        [sys.executable, "-m", "build", "--no-isolation", str(srcdir)],
        check=True,
    )

    (sdist,) = (srcdir / "dist").glob("*.tar.gz")
    shutil.unpack_archive(str(sdist), str(tmp_path / "sdist"))
    (sdist_src,) = (tmp_path / "sdist").iterdir()
    assert get_version_from_pkg_info(sdist_src) == details.version
    if details.write_file is not None:
        assert (sdist_src / details.write_file.sdist_path).read_text(
            encoding=details.write_file.encoding
        ) == details.write_file.contents

    (wheel,) = (srcdir / "dist").glob("*.whl")
    shutil.unpack_archive(str(wheel), str(tmp_path / "wheel"), "zip")
    (wheel_dist_info,) = (tmp_path / "wheel").glob("*.dist-info")
    metadata = (wheel_dist_info / "METADATA").read_text(encoding="utf-8")
    assert parse_version_from_metadata(metadata) == details.version
    if details.write_file is not None:
        assert (tmp_path / "wheel" / details.write_file.wheel_path).read_text(
            encoding=details.write_file.encoding
        ) == details.write_file.contents
