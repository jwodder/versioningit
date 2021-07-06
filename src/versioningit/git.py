from pathlib import Path
import re
import subprocess
from typing import Any, Optional, Union
from .core import VCSDescription
from .errors import NoTagError, NotVCSError
from .logging import log, warn_extra_fields
from .util import (
    fromtimestamp,
    get_build_date,
    list_str_guard,
    readcmd,
    runcmd,
    str_guard,
)


def describe_git(project_dir: Union[str, Path], **kwargs: Any) -> VCSDescription:
    match = list_str_guard(kwargs.pop("match", []), "tool.versioningit.vcs.match")
    exclude = list_str_guard(kwargs.pop("exclude", []), "tool.versioningit.vcs.exclude")
    dtag = kwargs.pop("default-tag", None)
    default_tag: Optional[str]
    if dtag is None:
        default_tag = None
    else:
        default_tag = str_guard(dtag, "tool.versioningit.vcs.default-tag")
    warn_extra_fields(kwargs, "tool.versioningit.vcs")
    build_date = get_build_date()

    try:
        runcmd(
            "git",
            "-C",
            project_dir,
            "rev-parse",
            "--git-dir",
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        raise NotVCSError("Git not installed; assuming this isn't a Git repository")
    except subprocess.CalledProcessError:
        raise NotVCSError(f"{project_dir} is not a Git repository")

    def readgit(*args: str, **kwargs: Any) -> str:
        return readcmd("git", "-C", project_dir, *args, **kwargs)

    describe_cmd = ["describe", "--tags", "--long", "--dirty", "--always"]
    for pat in match:
        describe_cmd.append(f"--match={pat}")
    for pat in exclude:
        describe_cmd.append(f"--exclude={pat}")
    try:
        description = readgit(*describe_cmd, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        # As far as I'm aware, this only happens in a repo without any commits
        # or a corrupted repo.
        raise NoTagError(f"`git describe` command failed: {e.stderr.strip()}")
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
        assert isinstance(tag, str)
        sdistance = m["distance"]
        assert isinstance(sdistance, str)
        distance = int(sdistance)
        rev = m["rev"]
        assert isinstance(rev, str)
    elif default_tag is not None:
        log.info(
            "`git describe` returned a hash instead of a tag; falling back to"
            " default tag %r",
            default_tag,
        )
        tag = default_tag
        distance = int(readgit("rev-list", "--count", "HEAD")) - 1
        rev = description
    else:
        raise NoTagError("`git describe` could not find a tag")
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
