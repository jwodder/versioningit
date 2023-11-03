from __future__ import annotations
from datetime import datetime, timezone
import json
import logging
from operator import attrgetter
from pathlib import Path
import shutil
import subprocess
from typing import Any
from pydantic import BaseModel
import pytest
from versioningit.core import VCSDescription
from versioningit.errors import NoTagError, NotVCSError
from versioningit.hg import HGRepo, describe_hg, parse_hg_archival

needs_hg = pytest.mark.skipif(
    shutil.which("hg") is None, reason="Mercurial not installed"
)

BUILD_DATE = datetime(2038, 1, 19, 3, 14, 7, tzinfo=timezone.utc)

DATA_DIR = Path(__file__).parent.with_name("data")


class HGFields(BaseModel):
    build_date: datetime
    distance: int
    rev: str
    revision: str
    vcs: str
    vcs_name: str


@needs_hg
@pytest.mark.parametrize(
    "repo,params,tag,state",
    [
        ("exact", {}, "v0.1.0", "exact"),
        ("distance", {}, "v0.1.0", "distance"),
        ("distance-dirty", {}, "v0.1.0", "distance-dirty"),
        ("default-tag", {"default-tag": "v0.0.0"}, "v0.0.0", "distance"),
        ("pattern", {"pattern": r"re:^v"}, "v0.1.0", "distance"),
    ],
)
def test_describe_hg(
    repo: str, params: dict[str, Any], tag: str, state: str, tmp_path: Path
) -> None:
    shutil.unpack_archive(DATA_DIR / "repos" / "hg" / f"{repo}.zip", tmp_path)
    with (DATA_DIR / "repos" / "hg" / f"{repo}.fields.json").open(
        encoding="utf-8"
    ) as fp:
        fields = HGFields.model_validate(json.load(fp))
    description = VCSDescription(
        tag=tag,
        state=state,
        branch="default",
        fields=fields.model_dump(),
    )
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
    shutil.unpack_archive(DATA_DIR / "repos" / repo, tmp_path)
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
def test_describe_hg_no_commits(tmp_path: Path, params: dict[str, Any]) -> None:
    subprocess.run(["hg", "--cwd", str(tmp_path), "init"], check=True)
    with pytest.raises(NotVCSError) as excinfo:
        describe_hg(project_dir=tmp_path, params=params)
    assert str(excinfo.value) == f"{tmp_path} is not tracked by Mercurial"


@needs_hg
def test_describe_hg_added_no_commits(tmp_path: Path) -> None:
    shutil.unpack_archive(
        DATA_DIR / "repos" / "hg" / "added-no-commits-default-tag.zip", tmp_path
    )
    with pytest.raises(NoTagError) as excinfo:
        describe_hg(project_dir=tmp_path, params={})
    assert str(excinfo.value) == "No latest tag in Mercurial repository"


@needs_hg
def test_describe_hg_added_no_commits_default_tag(
    caplog: pytest.LogCaptureFixture, tmp_path: Path
) -> None:
    shutil.unpack_archive(
        DATA_DIR / "repos" / "hg" / "added-no-commits-default-tag.zip", tmp_path
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
    shutil.unpack_archive(DATA_DIR / "repos" / "hg" / "exact.zip", tmp_path)
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
