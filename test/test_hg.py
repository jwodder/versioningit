from datetime import datetime, timezone
import json
import logging
from operator import attrgetter
from pathlib import Path
import shutil
import subprocess
from typing import Any, Dict
import pytest
from versioningit.core import VCSDescription
from versioningit.errors import NoTagError, NotVCSError
from versioningit.hg import HGRepo, describe_hg, parse_hg_archival

needs_hg = pytest.mark.skipif(
    shutil.which("hg") is None, reason="Mercurial not installed"
)

BUILD_DATE = datetime(2038, 1, 19, 3, 14, 7, tzinfo=timezone.utc)

DATA_DIR = Path(__file__).with_name("data")


@needs_hg
@pytest.mark.parametrize(
    "repo,params,description",
    [
        (
            "exact",
            {},
            VCSDescription(
                tag="v0.1.0",
                state="exact",
                branch="default",
                fields={
                    "distance": 0,
                    "rev": "9eaa2ff36144",
                    "revision": "9eaa2ff36144315dcaea2a1eff0a1a340f0bc30a",
                    "build_date": BUILD_DATE,
                    "vcs": "h",
                    "vcs_name": "hg",
                },
            ),
        ),
        (
            "distance",
            {},
            VCSDescription(
                tag="v0.1.0",
                state="distance",
                branch="default",
                fields={
                    "distance": 1,
                    "rev": "42ab202e999a",
                    "revision": "42ab202e999a827488efaf13ba0e9acc2ff04c86",
                    "build_date": BUILD_DATE,
                    "vcs": "h",
                    "vcs_name": "hg",
                },
            ),
        ),
        (
            "distance-dirty",
            {},
            VCSDescription(
                tag="v0.1.0",
                state="distance-dirty",
                branch="default",
                fields={
                    "distance": 1,
                    "rev": "42ab202e999a",
                    "revision": "42ab202e999a827488efaf13ba0e9acc2ff04c86",
                    "build_date": BUILD_DATE,
                    "vcs": "h",
                    "vcs_name": "hg",
                },
            ),
        ),
        (
            "default-tag",
            {"default-tag": "v0.0.0"},
            VCSDescription(
                tag="v0.0.0",
                state="distance",
                branch="default",
                fields={
                    "distance": 1,
                    "rev": "0234348fd175",
                    "revision": "0234348fd175c227aefb8e51a55b79acc33d6f61",
                    "build_date": BUILD_DATE,
                    "vcs": "h",
                    "vcs_name": "hg",
                },
            ),
        ),
        (
            "pattern",
            {"pattern": r"re:^v"},
            VCSDescription(
                tag="v0.1.0",
                state="distance",
                branch="default",
                fields={
                    "distance": 4,
                    "rev": "7850f9f76320",
                    "revision": "7850f9f763204ca4c886db3e5fc46be8f4472583",
                    "build_date": BUILD_DATE,
                    "vcs": "h",
                    "vcs_name": "hg",
                },
            ),
        ),
        (
            "pattern",
            {},
            VCSDescription(
                tag="0.2.0",
                state="distance",
                branch="default",
                fields={
                    "distance": 1,
                    "rev": "7850f9f76320",
                    "revision": "7850f9f763204ca4c886db3e5fc46be8f4472583",
                    "build_date": BUILD_DATE,
                    "vcs": "h",
                    "vcs_name": "hg",
                },
            ),
        ),
    ],
)
def test_describe_hg(
    repo: str, params: Dict[str, Any], description: VCSDescription, tmp_path: Path
) -> None:
    shutil.unpack_archive(str(DATA_DIR / "repos" / "hg" / f"{repo}.zip"), str(tmp_path))
    desc = describe_hg(project_dir=tmp_path, params=params)
    assert desc == description
    assert desc.fields["build_date"].tzinfo is timezone.utc


@pytest.mark.parametrize(
    "repo",
    [
        pytest.param("hg/default-tag.zip", marks=needs_hg),
        "archives/hg-archive-default-tag.zip",
    ],
)
def test_describe_hg_no_tag(repo: str, tmp_path: Path) -> None:
    shutil.unpack_archive(str(DATA_DIR / "repos" / repo), str(tmp_path))
    with pytest.raises(NoTagError) as excinfo:
        describe_hg(project_dir=tmp_path, params={})
    assert str(excinfo.value) == "No latest tag in Mercurial repository"


@needs_hg
def test_describe_hg_no_repo(tmp_path: Path) -> None:
    with pytest.raises(NotVCSError) as excinfo:
        describe_hg(project_dir=tmp_path, params={})
    assert str(excinfo.value) == f"{tmp_path} is not tracked by Mercurial"


@needs_hg
@pytest.mark.parametrize("params", [{}, {"default-tag": "0.0.0"}])
def test_describe_hg_no_commits(tmp_path: Path, params: Dict[str, Any]) -> None:
    subprocess.run(["hg", "--cwd", str(tmp_path), "init"], check=True)
    with pytest.raises(NotVCSError) as excinfo:
        describe_hg(project_dir=tmp_path, params=params)
    assert str(excinfo.value) == f"{tmp_path} is not tracked by Mercurial"


@needs_hg
def test_describe_hg_added_no_commits(tmp_path: Path) -> None:
    shutil.unpack_archive(
        str(DATA_DIR / "repos" / "hg" / "added-no-commits-default-tag.zip"),
        str(tmp_path),
    )
    with pytest.raises(NoTagError) as excinfo:
        describe_hg(project_dir=tmp_path, params={})
    assert str(excinfo.value) == "No latest tag in Mercurial repository"


@needs_hg
def test_describe_hg_added_no_commits_default_tag(
    caplog: pytest.LogCaptureFixture, tmp_path: Path
) -> None:
    shutil.unpack_archive(
        str(DATA_DIR / "repos" / "hg" / "added-no-commits-default-tag.zip"),
        str(tmp_path),
    )
    assert describe_hg(
        project_dir=tmp_path, params={"default-tag": "0.0.0"}
    ) == VCSDescription(
        tag="0.0.0",
        state="dirty",
        branch="default",
        fields={
            "distance": 0,
            "rev": "0" * 12,
            "revision": "0" * 40,
            "build_date": BUILD_DATE,
            "vcs": "h",
            "vcs_name": "hg",
        },
    )
    assert (
        "versioningit",
        logging.INFO,
        "No latest tag; falling back to default tag '0.0.0'",
    ) in caplog.record_tuples


@needs_hg
def test_ensure_is_repo_not_tracked(tmp_path: Path) -> None:
    shutil.unpack_archive(str(DATA_DIR / "repos" / "hg" / "exact.zip"), str(tmp_path))
    (tmp_path / "subdir").mkdir()
    (tmp_path / "subdir" / "file.txt").touch()
    with pytest.raises(NotVCSError) as excinfo:
        HGRepo(tmp_path / "subdir").ensure_is_repo()
    assert str(excinfo.value) == f"{tmp_path / 'subdir'} is not tracked by Mercurial"


@needs_hg
def test_ensure_is_repo_dot_hg_dir(tmp_path: Path) -> None:
    subprocess.run(["hg", "--cwd", str(tmp_path), "init"], check=True)
    with pytest.raises(NotVCSError) as excinfo:
        HGRepo(tmp_path / ".hg").ensure_is_repo()
    assert str(excinfo.value) == f"{tmp_path / '.hg'} is not tracked by Mercurial"


@pytest.mark.skipif(
    shutil.which("hg") is not None, reason="Mercurial must not be installed"
)
def test_ensure_is_repo_hg_not_installed(tmp_path: Path) -> None:
    with pytest.raises(NotVCSError) as excinfo:
        HGRepo(tmp_path).ensure_is_repo()
    assert (
        str(excinfo.value)
        == "hg not installed; assuming this isn't a Mercurial repository"
    )


@pytest.mark.parametrize(
    "archival_file",
    sorted((DATA_DIR / "hg-archival").glob("*.txt")),
    ids=attrgetter("stem"),
)
def test_parse_hg_archival(archival_file: Path) -> None:
    assert parse_hg_archival(archival_file) == json.loads(
        archival_file.with_suffix(".json").read_text(encoding="utf-8")
    )
