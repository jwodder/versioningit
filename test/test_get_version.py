from pathlib import Path
import shutil
import pytest
from versioningit.core import get_version
from versioningit.errors import NotSdistError, NotVCSError

DATA_DIR = Path(__file__).with_name("data")


@pytest.mark.skipif(shutil.which("git") is None, reason="Git not installed")
def test_get_version_no_git_fallback(tmp_path: Path) -> None:
    shutil.unpack_archive(str(DATA_DIR / "repos" / "no-git.zip"), str(tmp_path))
    with pytest.raises(NotSdistError) as excinfo:
        get_version(project_dir=tmp_path, write=False, fallback=True)
    assert str(excinfo.value) == f"{tmp_path} does not contain a PKG-INFO file"


@pytest.mark.skipif(shutil.which("git") is None, reason="Git not installed")
def test_get_version_no_git_no_fallback(tmp_path: Path) -> None:
    shutil.unpack_archive(str(DATA_DIR / "repos" / "no-git.zip"), str(tmp_path))
    with pytest.raises(NotVCSError) as excinfo:
        get_version(project_dir=tmp_path, write=False, fallback=False)
    assert str(excinfo.value) == f"{tmp_path} is not in a Git repository"
