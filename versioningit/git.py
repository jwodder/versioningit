from datetime import datetime, timezone
from pathlib import Path
import subprocess
from typing import Any, Dict, Union
from .errors import NotVCSError
from .logging import logcmd, warn_extra_fields
from .util import get_build_date, list_str_guard, readcmd


def describe_git(project_dir: Path, **kwargs: Any) -> Dict[str, Any]:
    match = list_str_guard(kwargs.pop("match", []), "tool.versioningit.vcs.match")
    exclude = list_str_guard(kwargs.pop("exclude", []), "tool.versioningit.vcs.exclude")
    warn_extra_fields("tool.versioningit.vcs", kwargs)
    if not is_git_repo(project_dir):
        raise NotVCSError(f"{project_dir} is not a Git repository")
    describe_cmd = ["git", "-C", project_dir, "describe", "--tags", "--long", "--dirty"]
    for m in match:
        describe_cmd.append(f"--match={m}")
    for e in exclude:
        describe_cmd.append(f"--exclude={e}")
    description = readcmd(*describe_cmd)
    if description.endswith("-dirty"):
        dirty = True
        description = description[: -len("-dirty")]
    else:
        dirty = False
    tag, sdistance, ghash = description.rsplit("-", 2)
    distance = int(sdistance)
    rev = ghash[1:]
    if distance and dirty:
        state = "distance-dirty"
    elif distance:
        state = "distance"
    elif dirty:
        state = "dirty"
    else:
        state = "exact"
    revision, author_ts, committer_ts = readcmd(
        "git", "-C", project_dir, "--no-pager", "show", "-s", "--format=%H%n%at%n%ct"
    ).splitlines()
    build_date = get_build_date()
    return {
        "tag": tag,
        "state": state,
        "distance": distance,
        "rev": rev,
        "revision": revision,
        "author_date": min(
            build_date, datetime.fromtimestamp(int(author_ts), tz=timezone.utc)
        ),
        "committer_date": min(
            build_date, datetime.fromtimestamp(int(committer_ts), tz=timezone.utc)
        ),
        "build_date": build_date,
        "scm": "g",
        "scm_name": "git",
    }


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
