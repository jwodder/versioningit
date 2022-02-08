from pathlib import Path
from typing import Any, Dict, Optional, Type
from setuptools import Command
from setuptools.command.build_py import build_py
from setuptools.command.sdist import sdist
from .core import run_onbuild
from .logging import init_logging, log


def get_cmdclasses(
    bases: Optional[Dict[str, Type[Command]]] = None
) -> Dict[str, Type[Command]]:
    """
    .. versionadded:: 1.1.0

    Return a `dict` of custom setuptools `Command` classes, suitable for
    passing to the ``cmdclass`` argument of `setuptools.setup()`, that run the
    ``onbuild`` step for the project when building an sdist or wheel.
    Specifically, the `dict` contains a subclass of
    `setuptools.command.sdist.sdist` at the ``"sdist"`` key and a subclass of
    `setuptools.command.build_py.build_py` at the ``"build_py"`` key.

    A `dict` of alternative base classes can optionally be supplied; if the
    `dict` contains an ``"sdist"`` entry, that entry will be used as the base
    class for the customized ``sdist`` command, and likewise for
    ``"build_py"``.  All other classes in the input `dict` are passed through
    unchanged.
    """

    cmds = {} if bases is None else bases.copy()

    sdist_base = cmds.get("sdist", sdist)

    class VersioningitSdist(sdist_base):  # type: ignore[valid-type,misc]
        def make_release_tree(self, base_dir: str, files: Any) -> None:
            super().make_release_tree(base_dir, files)
            init_logging()
            PROJECT_ROOT = Path().resolve()
            log.debug("Running onbuild step; cwd=%s", PROJECT_ROOT)
            run_onbuild(
                project_dir=PROJECT_ROOT,
                build_dir=base_dir,
                is_source=True,
                version=self.distribution.get_version(),
            )

    cmds["sdist"] = VersioningitSdist

    build_py_base = cmds.get("build_py", build_py)

    class VersioningitBuildPy(build_py_base):  # type: ignore[valid-type,misc]
        def run(self) -> None:
            super().run()
            init_logging()
            PROJECT_ROOT = Path().resolve()
            log.debug("Running onbuild step; cwd=%s", PROJECT_ROOT)
            run_onbuild(
                project_dir=PROJECT_ROOT,
                build_dir=self.build_lib,
                is_source=False,
                version=self.distribution.get_version(),
            )

    cmds["build_py"] = VersioningitBuildPy

    return cmds
