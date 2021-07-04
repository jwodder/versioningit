from abc import ABC, abstractmethod
from contextlib import suppress
from dataclasses import dataclass
from importlib import import_module
import os.path
from pathlib import Path
import sys
from typing import Any, Callable, Dict, Optional, Union
import entrypoints
from .errors import ConfigError, MethodError


class MethodSpec(ABC):
    @abstractmethod
    def load(self, project_dir: Union[str, Path]) -> Callable:
        ...


@dataclass
class EntryPointSpec(MethodSpec):
    group: str
    name: str

    def load(self, _project_dir: Union[str, Path]) -> Callable:
        try:
            ep = entrypoints.get_single(f"versioningit.{self.group}", self.name)
        except entrypoints.NoSuchEntryPoint:
            raise ConfigError(f"{self.group} entry point {self.name!r} not found")
        c = ep.load()
        if not callable(c):
            raise MethodError(
                f"{self.group} entry point {self.name!r} did not resolve to a"
                " callable object"
            )
        return c


@dataclass
class CustomMethodSpec(MethodSpec):
    module: str
    callable: str
    module_dir: Optional[str]

    def load(self, project_dir: Union[str, Path]) -> Callable:
        if self.module_dir is not None:
            modpath = os.path.join(project_dir, self.module_dir)
        else:
            modpath = str(project_dir)
        sys.path.insert(0, modpath)
        try:
            obj = import_module(self.module)
        finally:
            with suppress(ValueError):
                sys.path.remove(modpath)
        for attr in self.callable.split("."):
            obj = getattr(obj, attr)
        if not callable(obj):
            raise MethodError(
                f"Custom method '{self.module}:{self.callable}' did not"
                " resolve to a callable object"
            )
        return obj


@dataclass
class VersioningitMethod:
    method: Callable
    params: Dict[str, Any]

    def __call__(self, **kwargs: Any) -> Any:
        return self.method(**self.params, **kwargs)
