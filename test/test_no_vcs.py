from pathlib import Path
import shutil
import pytest
from versioningit.errors import NotVCSError
from versioningit.git import GitRepo
from versioningit.hg import HGRepo


@pytest.mark.skipif(shutil.which("git") is not None, reason="Git must not be installed")
def test_ensure_is_git_repo_not_installed(tmp_path: Path) -> None:
    with pytest.raises(NotVCSError) as excinfo:
        GitRepo(tmp_path).ensure_is_repo()
    assert (
        str(excinfo.value) == "Git not installed; assuming this isn't a Git repository"
    )


@pytest.mark.skipif(
    shutil.which("hg") is not None, reason="Mercurial must not be installed"
)
def test_ensure_is_hg_repo_not_installed(tmp_path: Path) -> None:
    with pytest.raises(NotVCSError) as excinfo:
        HGRepo(tmp_path).ensure_is_repo()
    assert (
        str(excinfo.value)
        == "hg not installed; assuming this isn't a Mercurial repository"
    )
