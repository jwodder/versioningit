from dataclasses import dataclass
import os
from pathlib import Path
import re
from typing import Any, Mapping, Tuple, Union
from packaging.version import Version
import tomli
from .config import Config
from .errors import MethodError, NoVersioningitError, NotSdistError, NotVCSError
from .logging import LOG_LEVEL_ENVVAR, init_logging, log
from .methods import VersioningitMethod


@dataclass
class Versioningit:
    project_dir: Path
    vcs: VersioningitMethod
    tag2version: VersioningitMethod
    next_version: VersioningitMethod
    format: VersioningitMethod
    write: VersioningitMethod

    @classmethod
    def from_project_dir(
        cls, project_dir: Union[str, Path] = os.curdir
    ) -> "Versioningit":
        ### TODO: When there is no pyproject.toml, should a FileNotFoundError
        ### be raised or a NoVersioningitError?
        with Path(project_dir, "pyproject.toml").open() as fp:
            config = tomli.load(fp).get("tool", {}).get("versioningit")
        if config is None:
            raise NoVersioningitError("versioningit not enabled in pyproject.toml")
        return cls.from_config(project_dir, config)

    @classmethod
    def from_config(cls, project_dir: Union[str, Path], config: Any) -> "Versioningit":
        return cls.from_parsed_config(project_dir, Config.parse_obj(config))

    @classmethod
    def from_parsed_config(
        cls, project_dir: Union[str, Path], cfg: Config
    ) -> "Versioningit":
        pdir = Path(project_dir)
        return cls(
            project_dir=pdir,
            vcs=cfg.vcs.load(pdir),
            tag2version=cfg.tag2version.load(pdir),
            next_version=cfg.next_version.load(pdir),
            format=cfg.format.load(pdir),
            write=cfg.write.load(pdir),
        )

    def get_version(self, fallback: bool = False) -> str:
        try:
            tag, state, fields = self.get_vcs_description()
        except NotVCSError:
            if fallback:
                return get_version_from_pkg_info(self.project_dir)
            else:
                raise
        tag_version = self.get_tag2version(tag)
        if state == "exact":
            version = tag_version
        else:
            next_version = self.get_next_version(tag_version)
            version = self.format_version(
                state, {**fields, "version": tag_version, "next_version": next_version}
            )
        try:
            Version(version)
        except ValueError:
            log.warning("Final version %r is not PEP 440-compliant", version)
        return version

    def get_vcs_description(self) -> Tuple[str, str, Mapping]:
        description = self.vcs(project_dir=self.project_dir)
        if not isinstance(description, Mapping):
            raise MethodError(
                f"vcs method returned {description!r} instead of a mapping"
            )
        tag = description.pop("tag", None)
        if not isinstance(tag, str):
            raise MethodError(f"vcs method returned {tag!r} instead of string tag")
        state = description.pop("state", None)
        if not isinstance(state, str):
            raise MethodError(f"vcs method returned {state!r} instead of string state")
        return tag, state, description

    def get_tag2version(self, tag: str) -> str:
        version = self.tag2version(tag=tag)
        if not isinstance(version, str):
            raise MethodError(
                f"tag2version method returned {version!r} instead of a string"
            )
        return version

    def get_next_version(self, version: str) -> str:
        next_version = self.next_version(version=version)
        if not isinstance(next_version, str):
            raise MethodError(
                f"next_version method returned {next_version!r} instead of a string"
            )
        return next_version

    def format_version(self, state: str, fields: Mapping) -> str:
        new_version = self.format(state=state, fields=fields)
        if not isinstance(new_version, str):
            raise MethodError(
                f"format method returned {new_version!r} instead of a string"
            )
        return new_version

    def write_version(self, version) -> None:
        self.write(project_dir=self.project_dir, version=version)

    ### TODO: Add a method that does get_version + write_version?


def get_version(
    project_dir: Union[str, Path] = os.curdir,
    write: bool = False,
    fallback: bool = True,
) -> str:
    if LOG_LEVEL_ENVVAR in os.envvar:
        init_logging()
    vgit = Versioningit.from_project_dir(project_dir)
    try:
        version = vgit.get_version(fallback=False)
    except NotVCSError:
        if fallback:
            version = get_version_from_pkg_info(project_dir)
            fellback = True
        else:
            raise
    else:
        fellback = False
    if write and not fellback:
        vgit.write_version(version)
    return version


def get_version_from_pkg_info(project_dir: Path) -> str:
    try:
        with (project_dir / "PKG-INFO").open() as fp:
            for line in fp:
                m = re.match(r"Version\s*:\s*", line)
                if m:
                    return line[m.end() :].strip()
                elif not line.rstrip("\r\n"):
                    break
    except FileNotFoundError:
        raise NotSdistError(f"{project_dir} does not contain a PKG-INFO file")
    raise ValueError("PKG-INFO does not contain a Version field")
