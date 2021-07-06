from dataclasses import dataclass
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union
from .config import Config
from .errors import MethodError, NotSdistError, NotVCSError, NotVersioningitError
from .logging import log, warn_bad_version
from .methods import VersioningitMethod
from .util import parse_version_from_metadata


@dataclass
class VCSDescription:
    tag: str
    state: str
    branch: Optional[str]
    fields: Dict[str, Any]


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
        try:
            config = Config.parse_toml_file(Path(project_dir, "pyproject.toml"))
        except FileNotFoundError:
            raise NotVersioningitError(f"No pyproject.toml file in {project_dir}")
        return cls.from_config_obj(project_dir, config)

    @classmethod
    def from_config(cls, project_dir: Union[str, Path], config: Any) -> "Versioningit":
        return cls.from_config_obj(project_dir, Config.parse_obj(config))

    @classmethod
    def from_config_obj(
        cls, project_dir: Union[str, Path], config: Config
    ) -> "Versioningit":
        pdir = Path(project_dir)
        return cls(
            project_dir=pdir,
            vcs=config.vcs.load(pdir),
            tag2version=config.tag2version.load(pdir),
            next_version=config.next_version.load(pdir),
            format=config.format.load(pdir),
            write=config.write.load(pdir),
        )

    def get_version(self) -> str:
        description = self.get_vcs_description()
        log.info("vcs returned tag %s", description.tag)
        log.debug("vcs state: %s", description.state)
        log.debug("vcs branch: %s", description.branch)
        log.debug("vcs fields: %r", description.fields)
        tag_version = self.get_tag2version(description.tag)
        log.info("tag2version returned version %s", tag_version)
        warn_bad_version(tag_version, "Version extracted from tag")
        if description.state == "exact":
            log.info("Tag is exact match; returning extracted version")
            version = tag_version
        else:
            log.info("VCS state is %r; formatting version", description.state)
            next_version = self.get_next_version(tag_version, description.branch)
            log.info("next-version returned version %s", next_version)
            warn_bad_version(next_version, "Calculated next version")
            version = self.format_version(
                description=description,
                version=tag_version,
                next_version=next_version,
            )
        log.info("Final version: %s", version)
        warn_bad_version(version, "Final version")
        return version

    def get_vcs_description(self) -> VCSDescription:
        description = self.vcs(project_dir=self.project_dir)
        if not isinstance(description, VCSDescription):
            raise MethodError(
                f"vcs method returned {description!r} instead of a VCSDescription"
            )
        return description

    def get_tag2version(self, tag: str) -> str:
        version = self.tag2version(tag=tag)
        if not isinstance(version, str):
            raise MethodError(
                f"tag2version method returned {version!r} instead of a string"
            )
        return version

    def get_next_version(self, version: str, branch: Optional[str]) -> str:
        next_version = self.next_version(version=version, branch=branch)
        if not isinstance(next_version, str):
            raise MethodError(
                f"next-version method returned {next_version!r} instead of a string"
            )
        return next_version

    def format_version(
        self, description: VCSDescription, version: str, next_version: str
    ) -> str:
        new_version = self.format(
            description=description, version=version, next_version=next_version
        )
        if not isinstance(new_version, str):
            raise MethodError(
                f"format method returned {new_version!r} instead of a string"
            )
        return new_version

    def write_version(self, version: str) -> None:
        self.write(project_dir=self.project_dir, version=version)


def get_version(
    project_dir: Union[str, Path] = os.curdir,
    config: Optional[dict] = None,
    write: bool = False,
    fallback: bool = True,
) -> str:
    if config is None:
        vgit = Versioningit.from_project_dir(project_dir)
    else:
        vgit = Versioningit.from_config(project_dir, config)
    try:
        version = vgit.get_version()
    except NotVCSError as e:
        if fallback:
            log.info("Could not get VCS data from %s: %s", project_dir, str(e))
            log.info("Falling back to reading from PKG-INFO")
            version = get_version_from_pkg_info(project_dir)
            fellback = True
        else:
            raise
    else:
        fellback = False
    if write and not fellback:
        vgit.write_version(version)
    return version


def get_version_from_pkg_info(project_dir: Union[str, Path]) -> str:
    try:
        return parse_version_from_metadata(
            Path(project_dir, "PKG-INFO").read_text(encoding="utf-8")
        )
    except FileNotFoundError:
        raise NotSdistError(f"{project_dir} does not contain a PKG-INFO file")
