from pathlib import Path
from typing import Any
from .core import get_version
from .errors import NotVersioningitError
from .logging import init_logging, log


def setuptools_finalizer(dist: Any) -> None:
    init_logging()
    # I *think* it's reasonable to assume that the project root is always the
    # current directory when this function is called.  Setuptools doesn't seem
    # to have decent support for running `setup.py` from another directory, and
    # the pep517.build command changes the working directory to the project
    # directory when run.  PEP 517 also says, "All hooks are run with working
    # directory set to the root of the source tree".
    PROJECT_ROOT = Path()
    log.debug("Project dir: %s", PROJECT_ROOT.resolve())
    try:
        version = get_version(PROJECT_ROOT, write=True, fallback=True)
    except NotVersioningitError:
        log.info("versioningit not enabled in pyproject.toml; doing nothing")
        return
    ### TODO: If NoSdistError, raise an informative error message à la
    ### setuptools_scm's
    dist.metadata.version = version
