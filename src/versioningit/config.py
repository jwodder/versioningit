from dataclasses import Field, dataclass, field, fields
from pathlib import Path
from typing import Any, Dict, List, Union
import tomli
from .errors import ConfigError, NotVersioningitError
from .logging import log, warn_extra_fields
from .methods import CustomMethodSpec, EntryPointSpec, MethodSpec, VersioningitMethod


@dataclass
class SectionSpec:
    name: str
    default_entry_point: str
    forbidden_params: List[str]


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
        sections: Dict[str, ConfigSection] = {}
        for f in fields(cls):
            sections[f.name] = cls.parse_section(f, obj.pop(f.name, None))
        warn_extra_fields(obj, "tool.versioningit")
        return cls(**sections)

    @staticmethod
    def parse_section(f: Field, obj: Any) -> "ConfigSection":
        if obj is None or isinstance(obj, str):
            method_spec = Config.parse_method_spec(
                f.name, f.metadata["default_entry_point"], obj
            )
            return ConfigSection(method_spec, {})
        elif isinstance(obj, dict):
            method_spec = Config.parse_method_spec(
                f.name, f.metadata["default_entry_point"], obj.pop("method", None)
            )
            for p in f.metadata["forbidden_params"]:
                if p in obj:
                    ### TODO: Change to INFO?
                    log.warning(
                        "tool.versioningit.%s cannot contain %r field; discarding",
                        f.name,
                        p,
                    )
                    obj.pop(p)
            return ConfigSection(method_spec, obj)
        else:
            raise ConfigError(f"tool.versioningit.{f.name} must be a string or table")

    @staticmethod
    def parse_method_spec(group: str, default: str, method: Any) -> MethodSpec:
        if method is None:
            return EntryPointSpec(group=group, name=default)
        elif isinstance(method, str):
            return EntryPointSpec(group=group, name=method)
        elif isinstance(method, dict):
            module = method.pop("module", None)
            if not isinstance(module, str):
                raise ConfigError(
                    f"tool.versioningit.{group}.method.module is required and"
                    " must be a string"
                )
            value = method.pop("value", None)
            if not isinstance(value, str):
                raise ConfigError(
                    f"tool.versioningit.{group}.method.value is required and"
                    " must be a string"
                )
            module_dir = method.pop("module_dir", None)
            if module_dir is not None and not isinstance(module_dir, str):
                raise ConfigError(
                    f"tool.versioningit.{group}.method.module_dir must be a string"
                )
            warn_extra_fields(method, f"tool.versioningit.{group}.method")
            return CustomMethodSpec(module, value, module_dir)
        else:
            raise ConfigError(
                f"tool.versioningit.{group}.method must be a string or table"
            )
