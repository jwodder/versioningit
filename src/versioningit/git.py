from pathlib import Path
import re
import subprocess
from typing import Any, Optional, Union
from .core import VCSDescription
from .errors import NotVCSError
from .logging import log, logcmd, warn_extra_fields
from .util import fromtimestamp, get_build_date, list_str_guard, readcmd, str_guard


def describe_git(project_dir: Union[str, Path], **kwargs: Any) -> VCSDescription:
    match = list_str_guard(kwargs.pop("match", []), "tool.versioningit.vcs.match")
    exclude = list_str_guard(kwargs.pop("exclude", []), "tool.versioningit.vcs.exclude")
    default_tag = str_guard(
        kwargs.pop("default_tag", "0.0.0"), "tool.versioningit.vcs.default_tag"
    )
    warn_extra_fields(kwargs, "tool.versioningit.vcs")
    build_date = get_build_date()
    if not is_git_repo(project_dir):
        raise NotVCSError(f"{project_dir} is not a Git repository")

    def readgit(*args: str) -> str:
        return readcmd("git", "-C", project_dir, *args)

    describe_cmd = ["describe", "--tags", "--long", "--dirty", "--always"]
    for pat in match:
        describe_cmd.append(f"--match={pat}")
    for pat in exclude:
        describe_cmd.append(f"--exclude={pat}")
    description = readgit(*describe_cmd)
    if description.endswith("-dirty"):
        dirty = True
        description = description[: -len("-dirty")]
    else:
        dirty = False
    m = re.fullmatch(
        r"(?P<tag>.+)-(?P<distance>[0-9]+)-g(?P<rev>[0-9a-f]+)", description
    )
    if m:
        tag = m["tag"]
        assert tag is not None
        sdistance = m["distance"]
        assert sdistance is not None
        distance = int(sdistance)
        rev = m["rev"]
        assert rev is not None
    else:
        log.debug(
            "`git describe` returned a hash instead of a tag; falling back to"
            " default tag"
        )
        tag = default_tag
        distance = int(readgit("rev-list", "--count", "HEAD")) - 1
        rev = description
    if distance and dirty:
        state = "distance-dirty"
    elif distance:
        state = "distance"
    elif dirty:
        state = "dirty"
    else:
        state = "exact"
    revision, author_ts, committer_ts = readgit(
        "--no-pager", "show", "-s", "--format=%H%n%at%n%ct"
    ).splitlines()
    branch: Optional[str]
    try:
        branch = readgit("symbolic-ref", "--short", "-q", "HEAD")
    except subprocess.CalledProcessError:
        branch = None
    return VCSDescription(
        tag=tag,
        state=state,
        branch=branch,
        fields={
            "distance": distance,
            "rev": rev,
            "revision": revision,
            "author_date": min(build_date, fromtimestamp(int(author_ts))),
            "committer_date": min(build_date, fromtimestamp(int(committer_ts))),
            "build_date": build_date,
            "vcs": "g",
            "vcs_name": "git",
        },
    )


def is_git_repo(project_dir: Union[str, Path]) -> bool:
    """
    Tests whether the given directory is or is contained in a Git repository
    """
    cmd = ["git", "-C", str(project_dir), "rev-parse", "--git-dir"]
    logcmd(cmd)
    try:
        r = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        # Git is not installed
        return False
    else:
        return bool(r.returncode == 0)
