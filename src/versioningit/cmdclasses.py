from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Optional, Type
from .core import get_template_fields_from_distribution, run_onbuild
from .logging import init_logging, log

if TYPE_CHECKING:
    from setuptools import Command


def get_cmdclasses(
    bases: Optional[Dict[str, Type["Command"]]] = None
) -> Dict[str, Type["Command"]]:
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
    # Import setuptools here so there isn't a slowdown from importing it
    # unconditionally whenever versioningit is imported
    from setuptools.command.build_py import build_py
    from setuptools.command.sdist import sdist

    cmds = {} if bases is None else bases.copy()

    sdist_base = cmds.get("sdist", sdist)

    class VersioningitSdist(sdist_base):  # type: ignore[valid-type,misc]
        editable_mode: bool = False

        def make_release_tree(self, base_dir: str, files: Any) -> None:
            super().make_release_tree(base_dir, files)
            init_logging()
            template_fields = get_template_fields_from_distribution(self.distribution)
            if not self.editable_mode and template_fields is not None:
                PROJECT_ROOT = Path().resolve()
                log.debug("Running onbuild step; cwd=%s", PROJECT_ROOT)
                run_onbuild(
                    project_dir=PROJECT_ROOT,
                    build_dir=base_dir,
                    is_source=True,
                    template_fields=template_fields,
                )
            else:
                log.debug(
                    "Appear to be building from an sdist; not running onbuild step"
                )

    cmds["sdist"] = VersioningitSdist

    build_py_base = cmds.get("build_py", build_py)

    class VersioningitBuildPy(build_py_base):  # type: ignore[valid-type,misc]
        editable_mode: bool = False

        def run(self) -> None:
            super().run()
            init_logging()
            template_fields = get_template_fields_from_distribution(self.distribution)
            if not self.editable_mode and template_fields is not None:
                PROJECT_ROOT = Path().resolve()
                log.debug("Running onbuild step; cwd=%s", PROJECT_ROOT)
                run_onbuild(
                    project_dir=PROJECT_ROOT,
                    build_dir=self.build_lib,
                    is_source=False,
                    template_fields=template_fields,
                )
            else:
                log.debug(
                    "Appear to be building from an sdist; not running onbuild step"
                )

    cmds["build_py"] = VersioningitBuildPy

    return cmds
