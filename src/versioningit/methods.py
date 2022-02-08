from abc import ABC, abstractmethod
from contextlib import suppress
from dataclasses import dataclass
from importlib import import_module
import os.path
from pathlib import Path
import sys
from typing import Any, Callable, Dict, Optional, Union, cast
from .errors import ConfigError, MethodError
from .logging import didyoumean, log

if sys.version_info[:2] >= (3, 10):
    from importlib.metadata import entry_points
else:
    from importlib_metadata import entry_points


# Call `entry_points()` only once and save the results for a speedup.  See
# <https://github.com/jwodder/versioningit/pull/7>.
ENTRY_POINTS = entry_points()


class MethodSpec(ABC):
    """
    An abstract base class for method specifications parsed from `versioningit`
    configurations
    """

    @abstractmethod
    def load(self, project_dir: Union[str, Path]) -> Callable:
        """
        Load & return the callable specified by the `MethodSpec`.
        ``project_dir`` is provided in case the method needs to load anything
        from the project directory itself.
        """
        ...


@dataclass
class EntryPointSpec(MethodSpec):
    """
    A parsed method specification identifying a Python packaging entry point
    """

    #: The name of the group in which to look up the entry point
    group: str

    #: The name of the entry point
    name: str

    def load(self, _project_dir: Union[str, Path]) -> Callable:
        """
        Loads & returns the entry point

        :raises ConfigError: if no such entry point exists
        :raises MethodError: if the loaded entry point is not a callable
        """
        log.debug("Loading entry point %r in group %s", self.name, self.group)
        try:
            ep, *_ = ENTRY_POINTS.select(group=self.group, name=self.name)
        except ValueError:
            valid = [ep.name for ep in entry_points(group=self.group)]
            raise ConfigError(
                f"{self.group} entry point {self.name!r} not"
                f" found{didyoumean(self.name, valid)}"
            )
        c = ep.load()
        if not callable(c):
            raise MethodError(
                f"{self.group} entry point {self.name!r} did not resolve to a"
                " callable object"
            )
        return cast(Callable, c)


@dataclass
class CustomMethodSpec(MethodSpec):
    """
    A parsed method specification identifying a callable in a local Python
    module
    """

    #: The dotted name of the module containing the callable
    module: str

    #: The name of the callable object within the module
    value: str

    #: The directory in which the module is located; defaults to
    #: ``project_dir``
    module_dir: Optional[str]

    def load(self, project_dir: Union[str, Path]) -> Callable:
        """
        Loads the module and returns the callable

        :raises MethodError: if the object is not actually a callable
        """
        if self.module_dir is not None:
            modpath = os.path.join(project_dir, self.module_dir)
        else:
            modpath = str(project_dir)
        log.debug("Prepending %s to sys.path", modpath)
        sys.path.insert(0, modpath)
        try:
            log.debug("Importing %s from %s", self.value, self.module)
            obj = import_module(self.module)
        finally:
            log.debug("Removing %s from sys.path", modpath)
            with suppress(ValueError):
                sys.path.remove(modpath)
        for attr in self.value.split("."):
            obj = getattr(obj, attr)
        if not callable(obj):
            raise MethodError(
                f"Custom method '{self.module}:{self.value}' did not resolve"
                " to a callable object"
            )
        return cast(Callable, obj)


@dataclass
class CallableSpec(MethodSpec):
    """
    A parsed method specification identifying a callable by the callable itself
    """

    #: The callable
    func: Callable

    def load(self, _project_dir: Union[str, Path]) -> Callable:
        """Return the callable"""
        return self.func


@dataclass
class VersioningitMethod:
    """
    A loaded `versioningit` method and the user-supplied parameters to pass to
    it
    """

    #: The loaded method
    method: Callable

    #: User-supplied parameters obtained from the original configuration
    params: Dict[str, Any]

    def __call__(self, **kwargs: Any) -> Any:
        """
        Invokes the method with the given keyword arguments and the
        user-supplied parameters
        """
        return self.method(params=self.params, **kwargs)
