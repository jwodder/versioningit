from __future__ import annotations
from pathlib import Path
from typing import TYPE_CHECKING
from .core import Report, Versioningit
from .errors import NoTagError, NotSdistError, NotVersioningitError
from .logging import init_logging, log
from .onbuild import get_pretend_version

if TYPE_CHECKING:
    from setuptools import Distribution


def setuptools_finalizer(dist: Distribution) -> None:
    """
    The entry point called by setuptools to retrieve the version for a project
    """
    init_logging()
    # PEP 517 says that "All hooks are run with working directory set to the
    # root of the source tree".
    PROJECT_ROOT = Path().resolve()
    log.info("Project dir: %s", PROJECT_ROOT)
    pretend_version = get_pretend_version(project_root=PROJECT_ROOT)
    if pretend_version is not None:
        dist.metadata.version = pretend_version
        return
    try:
        vgit = Versioningit.from_project_dir(PROJECT_ROOT)
        report = vgit.run(write=True, fallback=True)
    except NotVersioningitError as e:
        log.info(f"versioningit not enabled: {e}; doing nothing")
        return
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
    dist.metadata.version = report.version
    if isinstance(report, Report):
        dist._versioningit_template_fields = (  # type: ignore[attr-defined]
            report.template_fields
        )
