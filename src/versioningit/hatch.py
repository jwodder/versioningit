from __future__ import annotations
from pathlib import Path
from hatchling.plugin import hookimpl
from hatchling.version.source.plugin.interface import VersionSourceInterface
from .core import Versioningit
from .errors import NoTagError, NotSdistError, NotVersioningitError
from .logging import init_logging, log


class VersioningitSource(VersionSourceInterface):
    PLUGIN_NAME = "versioningit"

    def get_version_data(self) -> dict:
        """
        The entry point called by hatch to retrieve the version for a project
        """
        init_logging()
        PROJECT_ROOT = Path(self.root)
        log.info("Project dir: %s", PROJECT_ROOT)
        try:
            vgit = Versioningit.from_project_dir(PROJECT_ROOT)
            report = vgit.run(write=True, fallback=True)
        except NotVersioningitError:
            p = PROJECT_ROOT / "pyproject.toml"
            raise RuntimeError(f"versioningit not configured in {p}")
        except (NotSdistError, NoTagError):
            raise RuntimeError(
                "\nversioningit could not find a version for the project in"
                f" {PROJECT_ROOT}!\n\n"
                "You may be installing from a shallow clone, in which case you"
                " need to unshallow it first.\n\n"
                "Alternatively, you may be installing from a Git archive, which is"
                " not supported by default.  Install from a git+https://... URL"
                " instead.\n\n"
            )
        return {"version": report.version}


@hookimpl
def hatch_register_version_source() -> type[VersionSourceInterface]:
    # This function must be named "hatch_register_version_source" exactly.
    return VersioningitSource
