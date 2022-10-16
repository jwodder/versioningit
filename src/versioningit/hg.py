from __future__ import annotations
from dataclasses import dataclass
import os
from pathlib import Path
import subprocess
from typing import Any
from .core import VCSDescription
from .errors import NoTagError, NotVCSError
from .logging import log, warn_extra_fields
from .util import get_build_date, is_sdist, optional_str_guard, readcmd, runcmd


@dataclass
class HGRepo:
    """Methods for querying a Mercurial repository"""

    #: The repository's working tree or a subdirectory thereof
    path: str | Path

    def ensure_is_repo(self) -> None:
        """
        Test whether `path` is under Mercurial revision control; if it is not
        (or if Mercurial is not installed), raise a `NotVCSError`
        """
        try:
            runcmd(
                "hg",
                "--cwd",
                self.path,
                "files",
                ".",
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env={**os.environ, "HGPLAIN": "1"},
            )
        except FileNotFoundError:
            raise NotVCSError(
                "hg not installed; assuming this isn't a Mercurial repository"
            )
        except subprocess.CalledProcessError:
            raise NotVCSError(f"{self.path} is not tracked by Mercurial")

    def read(self, *args: str, **kwargs: Any) -> str:
        """
        Run a Mercurial command with the given arguments in `path` and return
        the stripped stdout
        """
        return readcmd(
            "hg",
            "--cwd",
            self.path,
            *args,
            env={**os.environ, "HGPLAIN": "1"},
            **kwargs,
        )


def describe_hg(*, project_dir: str | Path, params: dict[str, Any]) -> VCSDescription:
    """Implements the ``"hg"`` ``vcs`` method"""
    params = params.copy()
    pattern = optional_str_guard(
        params.pop("pattern", None), "tool.versioningit.vcs.pattern"
    )
    default_tag = optional_str_guard(
        params.pop("default-tag", None), "tool.versioningit.vcs.default-tag"
    )
    warn_extra_fields(params, "tool.versioningit.vcs", ["pattern", "default-tag"])
    build_date = get_build_date()
    repo = HGRepo(project_dir)
    try:
        repo.ensure_is_repo()
    except NotVCSError:
        if not is_sdist(project_dir) and Path(project_dir, ".hg_archival.txt").exists():
            log.info("%s is a Mercurial archive; parsing .hg_archival.txt", project_dir)
            data = parse_hg_archival(Path(project_dir, ".hg_archival.txt"))
            if "tag" in data:
                tag = data["tag"]
                distance = 0
            else:
                tag = data["latesttag"]
                distance = int(data["changessincelatesttag"])
            branch = data["branch"]
            revision = data["node"]
            rev = revision[:12]
        else:
            raise
    else:
        # Use "{changes}" instead of "{distance}", as the former counts all
        # different commits across all parent paths (which is what `git
        # describe` does), while the latter is just the length of the longest
        # path.
        if pattern is None:
            template = "{latesttag() % '{tag}:{changes}:{node}\n'}"
        else:
            template = "{latesttag(" + repr(pattern) + ") % '{tag}:{changes}:{node}\n'}"
        tag, sdistance, revision = (
            repo.read("log", "-r", ".", "--template", template)
            .splitlines()[0]
            .split(":")
        )
        distance = int(sdistance)
        rev, _, branch = repo.read("id", "-i", "-b").partition(" ")
    if rev.endswith("+"):
        dirty = True
        rev = rev[:-1]
    else:
        dirty = False
    if tag == "null":
        if default_tag is not None:
            log.info("No latest tag; falling back to default tag %r", default_tag)
            tag = default_tag
            # Act as though the first commit is the one with the default tag,
            # i.e., don't count it (unless there is no first commit, of course)
            if distance > 0:
                distance -= 1
        else:
            raise NoTagError("No latest tag in Mercurial repository")
    if distance and dirty:
        state = "distance-dirty"
    elif distance:
        state = "distance"
    elif dirty:
        state = "dirty"
    else:
        state = "exact"
    return VCSDescription(
        tag=tag,
        state=state,
        branch=branch,
        fields={
            "distance": distance,
            "rev": rev,
            "revision": revision,
            "build_date": build_date,
            "vcs": "h",
            "vcs_name": "hg",
        },
    )


def parse_hg_archival(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    with path.open() as fp:
        for line in fp:
            key, _, value = line.strip().partition(": ")
            data.setdefault(key, value)
    return data
