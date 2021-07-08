from pathlib import Path
from typing import Any
from .core import get_version
from .errors import NoTagError, NotSdistError, NotVersioningitError
from .logging import init_logging, log


def setuptools_finalizer(dist: Any) -> None:
    init_logging()
    # PEP 517 says that "All hooks are run with working directory set to the
    # root of the source tree".
    PROJECT_ROOT = Path().resolve()
    log.debug("Project dir: %s", PROJECT_ROOT)
    try:
        version = get_version(PROJECT_ROOT, write=True, fallback=True)
    except NotVersioningitError:
        log.info("versioningit not enabled in pyproject.toml; doing nothing")
        return
    except (NotSdistError, NoTagError):
        raise RuntimeError(
            "\nversioningit could not find a version for the project in"
            f" {PROJECT_ROOT}!\n\n"
            "You may be installing from a shallow clone, in which case you"
            " need to unshallow it first.\n\n"
            "Alternatively, you may be installing from a Git archive, which is"
            " not supported.  Install from a git+https://... URL instead.\n\n"
        )
    dist.metadata.version = version
