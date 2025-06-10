from __future__ import annotations
from dataclasses import Field, dataclass, field, fields
from pathlib import Path
import sys
from typing import Any, Optional
from .errors import ConfigError, NoConfigSectionError
from .logging import log, warn_extra_fields
from .methods import (
    CallableSpec,
    CustomMethodSpec,
    EntryPointSpec,
    MethodSpec,
    VersioningitMethod,
)
from .util import optional_str_guard

if sys.version_info[:2] >= (3, 11):
    from tomllib import load as toml_load
else:
    from tomli import load as toml_load


@dataclass
class ConfigSection:
    """A parsed method subtable of the `versioningit` configuration"""

    #: Specification of the method for this subtable
    method_spec: MethodSpec

    #: Additional parameters to pass to the method
    params: dict[str, Any]

    def load(self, project_dir: str | Path) -> VersioningitMethod:
        """Loads the method and returns a `VersioningitMethod`"""
        return VersioningitMethod(self.method_spec.load(project_dir), self.params)


@dataclass
class Config:
    """Parsed `versioningit` configuration"""

    #: Parsed ``vcs`` subtable
    vcs: ConfigSection = field(metadata={"default_entry_point": "git"})

    #: Parsed ``tag2version`` subtable
    tag2version: ConfigSection = field(metadata={"default_entry_point": "basic"})

    #: Parsed ``next-version`` subtable
    next_version: ConfigSection = field(metadata={"default_entry_point": "minor"})

    #: Parsed ``format`` subtable
    format: ConfigSection = field(metadata={"default_entry_point": "basic"})

    #: Parsed ``template-fields`` subtable
    template_fields: ConfigSection = field(metadata={"default_entry_point": "basic"})

    #: Parsed ``write`` subtable
    write: Optional[ConfigSection] = field(
        default=None, metadata={"default_entry_point": "basic", "optional": True}
    )

    #: Parsed ``onbuild`` subtable
    onbuild: Optional[ConfigSection] = field(
        default=None,
        metadata={"default_entry_point": "replace-version", "optional": True},
    )

    #: The ``default-version`` setting
    default_version: Optional[str] = None

    @classmethod
    def parse_toml_file(cls, filepath: str | Path) -> Config:
        """
        Parse the given TOML file and extract the contents of either the
        ``[tool.versioningit]`` table or the ``[tool.hatch.version]`` table (if
        it contains a ``source`` key set to ``"versioningit"``).

        If the ``[tool.versioningit]`` table is present and the
        ``[tool.hatch.version]`` table has more than just a ``source`` key,
        then a warning is emitted and the latter table is used.

        :raises NoConfigSectionError:
            if the file does not contain a versioningit configuration table
        :raises ConfigError:
            if the configuration table or any of its subfields are not of the
            correct type
        """
        with open(filepath, "rb") as fp:
            tool = toml_load(fp).get("tool", {})
        table = tool.get("versioningit")
        try:
            hatch_config = tool["hatch"]["version"]
        except (AttributeError, LookupError, TypeError):
            pass
        else:
            if (
                isinstance(hatch_config, dict)
                and hatch_config.get("source") == "versioningit"
            ):
                hatch_config.pop("source", None)
                if hatch_config:
                    if table is not None:
                        log.warning(
                            "versioningit configuration found in both"
                            " [tool.hatch.version] and [tool.versioningit];"
                            " only using the former"
                        )
                    table = hatch_config
                elif table is None:
                    table = hatch_config
                if table.get("onbuild") is not None:
                    log.warning(
                        "onbuild configuration in versioningit table detected."
                        "  When using Hatch, onbuild must be configured via"
                        " [tool.hatch.build.hooks.versioningit-onbuild]."
                    )
        if table is None:
            raise NoConfigSectionError(config_path=Path(filepath))
        return cls.parse_obj(table)

    @classmethod
    def parse_obj(cls, obj: Any) -> Config:
        """
        Parse a raw Python configuration structure

        :raises ConfigError:
            - if ``obj`` is not a `dict`
            - if ``default-version`` or any of the subtable or ``method``
              fields are not of the correct type
        """
        if not isinstance(obj, dict):
            raise ConfigError("versioningit config must be a table")
        default_version = optional_str_guard(
            obj.pop("default-version", None), "default-version"
        )
        sections: dict[str, Optional[ConfigSection]] = {}
        for f in fields(cls):
            if not f.metadata:
                continue
            sections[f.name] = cls.parse_section(f, obj.pop(attr2key(f.name), None))
        warn_extra_fields(
            obj,
            None,
            [attr2key(f.name) for f in fields(cls)],
        )
        return cls(
            default_version=default_version, **sections  # type: ignore[arg-type]
        )

    @staticmethod
    def parse_section(f: Field, obj: Any) -> Optional["ConfigSection"]:
        """
        Parse a step configuration field according to the metadata in the given
        `dataclasses.Field`, which must consist of the following items:

        ``default_entry_point`` : string
            The name of the default method to use for the step if one is not
            specified in the configuration

        ``optional`` : bool
            If true, an absent/`None` step field will be converted to `None`
            instead of to a section with the default method and no user
            parameters.  If not specified, defaults to false.

        :raises ConfigError:
            - if ``obj`` is not `None`, a callable, a string, or a `dict`
            - if any of the ``method`` fields are not of the correct type
        """
        if obj is None:
            if f.metadata.get("optional"):
                return None
            else:
                obj = f.metadata["default_entry_point"]
        if isinstance(obj, str):
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
            return ConfigSection(method_spec, obj)
        else:
            raise ConfigError(
                f"versioningit: {attr2key(f.name)} must be a string or table"
            )

    @staticmethod
    def parse_method_spec(f: Field, method: Any) -> MethodSpec:
        """
        Parse a ``method`` field according to the metadata in the given
        `dataclasses.Field` (see `parse_section()`)

        :raises ConfigError:
            - if ``method`` is not `None`, a string, a callable, or a `dict`
            - if ``method`` is a `dict` without a ``module`` or ``value`` key
            - if any of the fields in ``method`` are not of the correct type
        """
        key = attr2key(f.name)
        if method is None:
            method = f.metadata["default_entry_point"]
        if isinstance(method, str):
            return EntryPointSpec(group=f"versioningit.{f.name}", name=method)
        elif callable(method):
            return CallableSpec(method)
        elif isinstance(method, dict):
            module = method.pop("module", None)
            if not isinstance(module, str):
                raise ConfigError(
                    f"versioningit: {key}.method.module is required and"
                    " must be a string"
                )
            value = method.pop("value", None)
            if not isinstance(value, str):
                raise ConfigError(
                    f"versioningit: {key}.method.value is required and"
                    " must be a string"
                )
            module_dir = method.pop("module-dir", None)
            if module_dir is not None and not isinstance(module_dir, str):
                raise ConfigError(
                    f"versioningit: {key}.method.module-dir must be a string"
                )
            warn_extra_fields(
                method,
                f"{key}.method",
                ["module", "value", "module-dir"],
            )
            return CustomMethodSpec(module, value, module_dir)
        else:
            raise ConfigError(f"versioningit: {key}.method must be a string or table")


def attr2key(name: str) -> str:
    return name.replace("_", "-")
