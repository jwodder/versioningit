from dataclasses import dataclass
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union
from .config import Config
from .errors import MethodError, NotSdistError, NotVCSError
from .logging import warn_bad_version
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
        ### TODO: When there is no pyproject.toml, should a FileNotFoundError
        ### be raised or a NotVersioningitError?
        config = Config.parse_toml_file(Path(project_dir, "pyproject.toml"))
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
        tag_version = self.get_tag2version(description.tag)
        warn_bad_version(tag_version, "Version extracted from tag")
        if description.state == "exact":
            version = tag_version
        else:
            next_version = self.get_next_version(tag_version, description.branch)
            warn_bad_version(next_version, "Calculated next version")
            version = self.format_version(
                description=description,
                version=tag_version,
                next_version=next_version,
            )
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
                f"next_version method returned {next_version!r} instead of a string"
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


def get_version_from_pkg_info(project_dir: Union[str, Path]) -> str:
    try:
        return parse_version_from_metadata(
            Path(project_dir, "PKG-INFO").read_text(encoding="utf-8")
        )
    except FileNotFoundError:
        raise NotSdistError(f"{project_dir} does not contain a PKG-INFO file")
