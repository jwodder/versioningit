from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import re
import subprocess
from typing import Any, Dict, List, NamedTuple, Optional, Union
from .core import VCSDescription
from .errors import ConfigError, NoTagError, NotVCSError
from .logging import log, warn_extra_fields
from .util import (
    fromtimestamp,
    get_build_date,
    is_sdist,
    list_str_guard,
    optional_str_guard,
    readcmd,
    runcmd,
    str_guard,
)

DEFAULT_DATE = fromtimestamp(0)

# Values git-config accepts as true & false:
TRUTH_VALUES = {
    "yes": True,
    "on": True,
    "true": True,
    "1": True,
    "no": False,
    "off": False,
    "false": False,
    "0": False,
    "": False,
}


class Describe(NamedTuple):
    """
    Parsed representation of `git describe` output when it includes all three
    fields and does not end with "``-dirty``"
    """

    #: The most recent tag
    tag: str

    #: The number of commits since the tag
    distance: int

    #: The abbreviated hash of the HEAD commit
    rev: str

    @classmethod
    def parse(cls, s: str) -> "Describe":
        m = re.fullmatch(r"(?P<tag>.+)-(?P<distance>[0-9]+)-g(?P<rev>[0-9a-f]+)?", s)
        if not m:
            raise ValueError("Could not parse `git describe` output")
        tag = m["tag"]
        assert isinstance(tag, str)
        distance = int(m["distance"])
        rev = m["rev"]
        assert isinstance(rev, str)
        return cls(tag, distance, rev)


@dataclass
class DescribeOpts:
    tags: bool
    match: List[str]
    exclude: List[str]

    @classmethod
    def parse_describe_subst(cls, s: str) -> "DescribeOpts":
        m = re.fullmatch(r"\$Format:%\(describe(?::(?P<options>.*))?\)\$", s)
        if not m:
            raise ValueError(
                f"Expected string in format '$Format:%(describe[:options])$', got {s!r}"
            )
        tags = False
        match: List[str] = []
        exclude: List[str] = []
        options = m["options"]
        if options:
            # As of Git 2.35.1, though the docs say that %(describe) options
            # are comma-separated, they're actually comma-terminated, with
            # consecutive commas creating an empty option and empty options
            # causing the whole placeholder to be invalid.  Also, there's no
            # escaping support to worry about.
            if options.endswith(","):
                options = options[:-1]
            for opt in options.split(","):
                name, eq, value = opt.partition("=")
                if name == "tags":
                    if eq:
                        try:
                            tags = TRUTH_VALUES[value.lower()]
                        except KeyError:
                            # Git accepts invalid booleans and treats them as
                            # false, so we should, too, but we should at least
                            # warn the user that they probably made a mistake.
                            log.warning(
                                "Invalid boolean value for 'tags' option to"
                                " %%(describe) format: %r; treating as false",
                                value,
                            )
                            tags = False
                    else:
                        tags = True
                elif name == "match":
                    if not value:
                        raise ValueError(f"Option missing value: {opt!r}")
                    match.append(value)
                elif name == "exclude":
                    if not value:
                        raise ValueError(f"Option missing value: {opt!r}")
                    exclude.append(value)
                else:
                    raise ValueError(f"Unknown option: {opt!r}")
        return cls(tags=tags, match=match, exclude=exclude)

    def as_args(self) -> List[str]:
        args: List[str] = []
        if self.tags:
            args.append("--tags")
        for pat in self.match:
            args.append(f"--match={pat}")
        for pat in self.exclude:
            args.append(f"--exclude={pat}")
        return args


@dataclass
class GitRepo:
    """Methods for querying a Git repository"""

    #: The repository's working tree or a subdirectory thereof
    path: Union[str, Path]

    def ensure_is_repo(self) -> None:
        """
        Test whether `path` is under Git revision control; if it is not (or if
        Git is not installed), raise a `NotVCSError`
        """
        try:
            if (
                self.read(
                    "rev-parse", "--is-inside-work-tree", stderr=subprocess.DEVNULL
                )
                == "false"
            ):
                # We are inside a .git directory
                raise NotVCSError(f"{self.path} is not in a Git working tree")
        except FileNotFoundError:
            raise NotVCSError("Git not installed; assuming this isn't a Git repository")
        except subprocess.CalledProcessError:
            raise NotVCSError(f"{self.path} is not in a Git repository")
        try:
            # Check whether `path` is tracked by Git (Note that we can't rely
            # on this check alone, as it succeeds when inside a .git/
            # directory)
            runcmd(
                "git",
                "ls-files",
                "--error-unmatch",
                ".",
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                cwd=str(self.path),
            )
        except subprocess.CalledProcessError:
            raise NotVCSError(f"{self.path} is not tracked by Git")

    def read(self, *args: str, **kwargs: Any) -> str:
        """
        Run a Git command with the given arguments in `path` and return the
        stripped stdout
        """
        return readcmd("git", *args, cwd=str(self.path), **kwargs)

    def describe(self, opts: DescribeOpts) -> str:
        """
        Run ``git describe --long --dirty --always`` in the repository with the
        given options; if the command fails, raises `NoTagError`
        """
        try:
            return self.read(
                "describe",
                "--long",
                "--dirty",
                "--always",
                *opts.as_args(),
                stderr=subprocess.PIPE,
            )
        except subprocess.CalledProcessError as e:
            # As far as I'm aware, this only happens in a repo without any
            # commits or a corrupted repo.
            raise NoTagError(f"`git describe` command failed: {e.stderr.strip()}")

    def get_branch(self) -> Optional[str]:
        """
        Return the name of the current branch, or `None` if the repository is
        in a detached HEAD state
        """
        try:
            return self.read(
                "symbolic-ref", "--short", "-q", "HEAD", stderr=subprocess.DEVNULL
            )
        except subprocess.CalledProcessError:
            return None


def describe_git(
    *, project_dir: Union[str, Path], params: Dict[str, Any]
) -> VCSDescription:
    """Implements the ``"git"`` ``vcs`` method"""
    match = list_str_guard(params.pop("match", []), "tool.versioningit.vcs.match")
    exclude = list_str_guard(params.pop("exclude", []), "tool.versioningit.vcs.exclude")
    default_tag = optional_str_guard(
        params.pop("default-tag", None), "tool.versioningit.vcs.default-tag"
    )
    warn_extra_fields(
        params, "tool.versioningit.vcs", ["match", "exclude", "default-tag"]
    )
    build_date = get_build_date()
    repo = GitRepo(project_dir)
    repo.ensure_is_repo()
    vdesc = describe_git_core(
        repo,
        build_date,
        default_tag,
        DescribeOpts(tags=True, match=match, exclude=exclude),
    )
    if "revision" not in vdesc.fields:
        revision, author_ts, committer_ts = repo.read(
            "--no-pager", "show", "-s", "--format=%H%n%at%n%ct"
        ).splitlines()
        vdesc.fields["revision"] = revision
        vdesc.fields["author_date"] = min(build_date, fromtimestamp(int(author_ts)))
        vdesc.fields["committer_date"] = min(
            build_date, fromtimestamp(int(committer_ts))
        )
    return vdesc


def describe_git_archive(
    *, project_dir: Union[str, Path], params: Dict[str, Any]
) -> VCSDescription:
    """Implements the ``"git-archive"`` ``vcs`` method"""
    default_tag = optional_str_guard(
        params.pop("default-tag", None), "tool.versioningit.vcs.default-tag"
    )
    describe_subst = str_guard(
        params.pop("describe-subst", None), "tool.versioningit.vcs.describe-subst"
    )
    warn_extra_fields(
        params, "tool.versioningit.vcs", ["default-tag", "describe-subst"]
    )
    build_date = get_build_date()
    repo = GitRepo(project_dir)
    try:
        repo.ensure_is_repo()
    except NotVCSError:
        if is_sdist(project_dir):
            pass
        elif describe_subst == "":
            raise NoTagError(
                "tool.versioningit.vcs.describe-subst is empty in Git archive"
            )
        elif describe_subst.startswith("$Format"):
            raise NoTagError(
                "tool.versioningit.vcs.describe-subst not expanded in Git archive"
            )
        else:
            log.info(
                "Parsing version information from describe-subst = %r", describe_subst
            )
            try:
                tag, distance, rev = Describe.parse(describe_subst)
            except ValueError:
                tag = describe_subst
                distance = 0
                rev = "0" * 7
            return VCSDescription(
                tag=tag,
                state="distance" if distance else "exact",
                branch=None,
                fields={
                    "distance": distance,
                    "rev": rev,
                    "build_date": build_date,
                    "vcs": "g",
                    "vcs_name": "git",
                },
            )
        raise
    try:
        opts = DescribeOpts.parse_describe_subst(describe_subst)
    except ValueError as e:
        raise ConfigError(f"Invalid tool.versioningit.vcs.describe-subst value: {e}")
    vdesc = describe_git_core(repo, build_date, default_tag, opts)
    vdesc.fields.pop("revision", None)
    vdesc.fields.pop("author_date", None)
    vdesc.fields.pop("committer_date", None)
    return vdesc


def describe_git_core(
    repo: GitRepo,
    build_date: datetime,
    default_tag: Optional[str],
    opts: DescribeOpts,
) -> VCSDescription:
    """Common functionality of the ``"git"`` and ``"git-archive"`` methods"""
    try:
        description = repo.describe(opts)
    except NoTagError as e:
        # There are no commits in the repo
        if default_tag is not None:
            log.error("%s", e)
            log.info("Falling back to default tag %r", default_tag)
            return VCSDescription(
                tag=default_tag,
                state="dirty",
                branch=repo.get_branch(),
                fields={
                    "distance": 0,
                    "rev": "0" * 7,
                    "revision": "0" * 40,
                    "author_date": min(build_date, DEFAULT_DATE),
                    "committer_date": min(build_date, DEFAULT_DATE),
                    "build_date": build_date,
                    "vcs": "g",
                    "vcs_name": "git",
                },
            )
        else:
            raise
    if description.endswith("-dirty"):
        dirty = True
        description = description[: -len("-dirty")]
    else:
        dirty = False
    try:
        tag, distance, rev = Describe.parse(description)
    except ValueError:
        if default_tag is not None:
            log.info(
                "`git describe` returned a hash instead of a tag; falling back to"
                " default tag %r",
                default_tag,
            )
            tag = default_tag
            distance = int(repo.read("rev-list", "--count", "HEAD")) - 1
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
    return VCSDescription(
        tag=tag,
        state=state,
        branch=repo.get_branch(),
        fields={
            "distance": distance,
            "rev": rev,
            "build_date": build_date,
            "vcs": "g",
            "vcs_name": "git",
        },
    )
