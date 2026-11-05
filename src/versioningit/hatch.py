from __future__ import annotations
from dataclasses import fields
from pathlib import Path
import shutil
import tempfile
from typing import Any
from hatchling.builders.hooks.plugin.interface import BuildHookInterface
from hatchling.plugin import hookimpl
from hatchling.version.source.plugin.interface import VersionSourceInterface
from .config import Config
from .core import Report, Versioningit
from .errors import NoTagError, NotSdistError, NotVersioningitError
from .logging import init_logging, log
from .onbuild import HatchFileProvider, get_pretend_version


class VersioningitSource(VersionSourceInterface):
    PLUGIN_NAME = "versioningit"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.__fields: dict[str, Any] | None = None

    def get_version_data(self) -> dict:
        """
        The entry point called by hatch to retrieve the version for a project
        """
        init_logging()
        PROJECT_ROOT = Path(self.root)
        log.info("Project dir: %s", PROJECT_ROOT)
        pretend_version = get_pretend_version(project_root=PROJECT_ROOT)
        if pretend_version is not None:
            return {"version": pretend_version}
        try:
            vgit = Versioningit.from_project_dir(PROJECT_ROOT)
            report = vgit.run(write=True, fallback=True)
        except NotVersioningitError as e:  # pragma: no cover
            raise RuntimeError(str(e))
        except (NotSdistError, NoTagError) as e:
            raise RuntimeError(
                # If an error occurs in `get_version_data()`, hatchling throws
                # away its cause, so we need to include `str(e)` in the
                # RuntimeError for it to be seen.
                f"{type(e).__name__}: {e}\n"
                "\nversioningit could not find a version for the project in"
                f" {PROJECT_ROOT}!\n\n"
                "You may be installing from a shallow clone, in which case you"
                " need to unshallow it first.\n\n"
                "Alternatively, you may be installing from a Git archive, which is"
                " not supported by default.  Install from a git+https://... URL"
                " instead.\n\n"
            )
        if isinstance(report, Report):
            self.__fields = report.template_fields
        return {"version": report.version}

    def set_version(
        self, _version: str, _version_data: dict
    ) -> None:  # pragma: no cover
        # Can't be tested due to hatch using isolated environments for `hatch
        # version`
        raise NotImplementedError(
            "The versioningit plugin does not support setting the version."
            "  Create a tag instead."
        )

    def get_template_fields(self) -> dict[str, Any] | None:
        return self.__fields


class OnbuildHook(BuildHookInterface):
    PLUGIN_NAME = "versioningit-onbuild"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.__tmpdir = Path(tempfile.mkdtemp())

    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        init_logging()
        if self.target_name == "wheel" and version == "editable":
            log.debug("Not running onbuild step for editable build")
            return None
        version_source = self.metadata.hatch.version.source
        if not isinstance(version_source, VersioningitSource):
            raise RuntimeError(
                "versioningit-onbuild can only be used with 'versioningit'"
                " version source, but version source is"
                f" {self.metadata.hatch.version.source_name!r}"
            )
        template_fields = version_source.get_template_fields()
        if template_fields is None:
            log.debug("Appear to be building from an sdist; not running onbuild step")
            return
        config = self.config.copy()
        for key in [
            "dependencies",
            "require-runtime-dependencies",
            "require-runtime-features",
        ]:
            config.pop(key, None)
        (onbuild_field,) = [f for f in fields(Config) if f.name == "onbuild"]
        onbuild_section = Config.parse_section(onbuild_field, config)
        assert onbuild_section is not None
        onbuild_method = onbuild_section.load(self.root)
        file_provider = HatchFileProvider(
            src_dir=Path(self.root),
            tmp_dir=self.__tmpdir,
        )
        onbuild_method(
            file_provider=file_provider,
            is_source=self.target_name == "sdist",
            template_fields=template_fields,
        )
        build_data.setdefault("force_include", {}).update(
            file_provider.get_force_include()
        )

    def finalize(
        self, _version: str, _build_data: dict[str, Any], _artifact_path: str
    ) -> None:
        shutil.rmtree(self.__tmpdir, ignore_errors=True)


@hookimpl
def hatch_register_version_source() -> type[VersionSourceInterface]:
    # This function must be named "hatch_register_version_source" exactly.
    return VersioningitSource


@hookimpl
def hatch_register_build_hook() -> type[BuildHookInterface]:
    return OnbuildHook
