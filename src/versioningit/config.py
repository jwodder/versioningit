from dataclasses import Field, dataclass, field, fields
from pathlib import Path
from typing import Any, Dict, Optional, Union
import tomli
from .errors import ConfigError, NotVersioningitError
from .logging import log, warn_extra_fields
from .methods import (
    CallableSpec,
    CustomMethodSpec,
    EntryPointSpec,
    MethodSpec,
    VersioningitMethod,
)
from .util import str_guard


@dataclass
class ConfigSection:
    method_spec: MethodSpec
    params: Dict[str, Any]

    def load(self, project_dir: Union[str, Path]) -> VersioningitMethod:
        return VersioningitMethod(self.method_spec.load(project_dir), self.params)


@dataclass
class Config:
    vcs: ConfigSection = field(
        metadata={"default_entry_point": "git", "forbidden_params": ["project_dir"]}
    )
    tag2version: ConfigSection = field(
        metadata={"default_entry_point": "basic", "forbidden_params": ["tag"]}
    )
    next_version: ConfigSection = field(
        metadata={
            "key": "next-version",
            "default_entry_point": "minor",
            "forbidden_params": ["version", "branch"],
        }
    )
    format: ConfigSection = field(
        metadata={
            "default_entry_point": "basic",
            "forbidden_params": ["description", "version", "next_version"],
        }
    )
    write: ConfigSection = field(
        metadata={
            "default_entry_point": "basic",
            "forbidden_params": ["project_dir", "version"],
        }
    )
    default_version: Optional[str] = None

    @classmethod
    def parse_toml_file(cls, filepath: Union[str, Path]) -> "Config":
        with open(filepath, "r", encoding="utf-8") as fp:
            data = tomli.load(fp).get("tool", {}).get("versioningit")
        if data is None:
            raise NotVersioningitError("versioningit not enabled in pyproject.toml")
        return cls.parse_obj(data)

    @classmethod
    def parse_obj(cls, obj: Any) -> "Config":
        if not isinstance(obj, dict):
            raise ConfigError("tool.versioningit must be a table")
        defver = obj.pop("default-version", None)
        default_version: Optional[str]
        if defver is not None:
            default_version = str_guard(defver, "tool.versioningit.default-version")
        else:
            default_version = None
        sections: Dict[str, ConfigSection] = {}
        for f in fields(cls):
            if f.type is not ConfigSection:
                continue
            key = f.metadata.get("key", f.name)
            sections[f.name] = cls.parse_section(f, obj.pop(key, None))
        warn_extra_fields(obj, "tool.versioningit")
        return cls(default_version=default_version, **sections)

    @staticmethod
    def parse_section(f: Field, obj: Any) -> "ConfigSection":
        key = f.metadata.get("key", f.name)
        if obj is None or isinstance(obj, str):
            method_spec = Config.parse_method_spec(f, obj)
            return ConfigSection(method_spec, {})
        elif callable(obj):
            method_spec = CallableSpec(obj)
            return ConfigSection(method_spec, {})
        elif isinstance(obj, dict):
            if "method" not in obj and "module" in obj and "value" in obj:
                method_spec = Config.parse_method_spec(f, obj)
                return ConfigSection(method_spec, {})
            method_spec = Config.parse_method_spec(f, obj.pop("method", None))
            for p in f.metadata["forbidden_params"]:
                if p in obj:
                    log.warning(
                        "tool.versioningit.%s cannot contain %r field; discarding",
                        key,
                        p,
                    )
                    obj.pop(p)
            return ConfigSection(method_spec, obj)
        else:
            raise ConfigError(f"tool.versioningit.{key} must be a string or table")

    @staticmethod
    def parse_method_spec(f: Field, method: Any) -> MethodSpec:
        key = f.metadata.get("key", f.name)
        if method is None:
            return EntryPointSpec(group=f.name, name=f.metadata["default_entry_point"])
        elif isinstance(method, str):
            return EntryPointSpec(group=f.name, name=method)
        elif callable(method):
            return CallableSpec(method)
        elif isinstance(method, dict):
            module = method.pop("module", None)
            if not isinstance(module, str):
                raise ConfigError(
                    f"tool.versioningit.{key}.method.module is required and"
                    " must be a string"
                )
            value = method.pop("value", None)
            if not isinstance(value, str):
                raise ConfigError(
                    f"tool.versioningit.{key}.method.value is required and"
                    " must be a string"
                )
            module_dir = method.pop("module-dir", None)
            if module_dir is not None and not isinstance(module_dir, str):
                raise ConfigError(
                    f"tool.versioningit.{key}.method.module-dir must be a string"
                )
            warn_extra_fields(method, f"tool.versioningit.{key}.method")
            return CustomMethodSpec(module, value, module_dir)
        else:
            raise ConfigError(
                f"tool.versioningit.{key}.method must be a string or table"
            )
