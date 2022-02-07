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
    cmds = {} if bases is None else bases.copy()

    sdist_base = cmds.get("sdist", sdist)

    class VersioningitSdist(sdist_base):  # type: ignore[valid-type,misc]
        def make_release_tree(self, base_dir: str, files: Any) -> None:
            init_logging()
            PROJECT_ROOT = Path().resolve()
            log.debug("Building in: %s", PROJECT_ROOT)
            super().make_release_tree(base_dir, files)
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
            init_logging()
            PROJECT_ROOT = Path().resolve()
            log.debug("Building in: %s", PROJECT_ROOT)
            super().run()
            run_onbuild(
                project_dir=PROJECT_ROOT,
                build_dir=self.build_lib,
                is_source=False,
                version=self.distribution.get_version(),
            )

    cmds["build_py"] = VersioningitBuildPy

    return cmds
