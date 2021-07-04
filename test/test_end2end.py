from operator import attrgetter
from pathlib import Path
import shutil
import subprocess
from pydantic import BaseModel
import pytest
from versioningit.core import get_version, get_version_from_pkg_info
from versioningit.util import parse_version_from_metadata

DATA_DIR = Path(__file__).with_name("data")


class CaseDetails(BaseModel):
    version: str
    # More to be added later


@pytest.mark.skipif(shutil.which("git") is None, reason="Git not installed")
@pytest.mark.parametrize(
    "repozip",
    sorted((DATA_DIR / "repos" / "git").glob("*.zip")),
    ids=attrgetter("name"),
)
def test_end2end_git(repozip: Path, tmp_path: Path) -> None:
    details = CaseDetails.parse_file(repozip.with_suffix(".json"))
    srcdir = tmp_path / "src"
    shutil.unpack_archive(str(repozip), str(srcdir))
    assert (
        get_version(project_dir=srcdir, write=False, fallback=False) == details.version
    )
    subprocess.run(
        ["python", "-m", "build", "--no-isolation", str(srcdir)],
        check=True,
    )

    (sdist,) = (srcdir / "dist").glob("*.tar.gz")
    shutil.unpack_archive(str(sdist), str(tmp_path / "sdist"))
    (sdist_src,) = (tmp_path / "sdist").iterdir()
    assert get_version_from_pkg_info(sdist_src) == details.version

    (wheel,) = (srcdir / "dist").glob("*.whl")
    shutil.unpack_archive(str(wheel), str(tmp_path / "wheel"), "zip")
    (wheel_dist_info,) = (tmp_path / "wheel").glob("*.dist-info")
    metadata = (wheel_dist_info / "METADATA").read_text(encoding="utf-8")
    assert parse_version_from_metadata(metadata) == details.version
