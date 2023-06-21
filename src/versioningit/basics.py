from __future__ import annotations
from copy import deepcopy
from pathlib import Path
import re
from typing import Any, Optional
from .core import VCSDescription
from .errors import ConfigError, InvalidTagError
from .logging import log, warn_extra_fields
from .util import (
    bool_guard,
    optional_str_guard,
    split_pep440_version,
    split_version,
    str_guard,
    strip_prefix,
    strip_suffix,
)

#: The default formats for the ``"basic"`` ``format`` method
DEFAULT_FORMATS = {
    "distance": "{version}.post{distance}+{vcs}{rev}",
    "dirty": "{version}+d{build_date:%Y%m%d}",
    "distance-dirty": "{version}.post{distance}+{vcs}{rev}.d{build_date:%Y%m%d}",
}


def basic_tag2version(*, tag: str, params: dict[str, Any]) -> str:
    """Implements the ``"basic"`` ``tag2version`` method"""
    params = params.copy()
    try:
        rmprefix = str_guard(
            params.pop("rmprefix"), "tool.versioningit.tag2version.rmprefix"
        )
    except KeyError:
        pass
    else:
        tag = strip_prefix(tag, rmprefix)
    try:
        rmsuffix = str_guard(
            params.pop("rmsuffix"), "tool.versioningit.tag2version.rmsuffix"
        )
    except KeyError:
        pass
    else:
        tag = strip_suffix(tag, rmsuffix)
    require_match = bool_guard(
        params.pop("require-match", False),
        "tool.versioningit.tag2version.require-match",
    )
    try:
        regex = str_guard(params.pop("regex"), "tool.versioningit.tag2version.regex")
    except KeyError:
        pass
    else:
        m = re.search(regex, tag)
        if m is None:
            if require_match:
                raise InvalidTagError(f"tag2version.regex did not match tag {tag!r}")
            else:
                log.info(
                    "tag2version.regex did not match tag %r; leaving unmodified", tag
                )
        else:
            if "version" in m.groupdict():
                tag = m["version"]
            else:
                tag = m[0]
            if tag is None:
                raise InvalidTagError(
                    "'version' group in tool.versioningit.tag2version.regex did"
                    " not participate in match"
                )
    warn_extra_fields(
        params,
        "tool.versioningit.tag2version",
        ["rmprefix", "rmsuffix", "regex", "require-match"],
    )
    return tag.lstrip("v")


def basic_format(
    *,
    description: VCSDescription,
    base_version: str,
    next_version: str,
    params: dict[str, Any],
) -> str:
    """Implements the ``"basic"`` ``format`` method"""
    branch: Optional[str]
    if description.branch is not None:
        branch = re.sub(r"[^A-Za-z0-9.]", ".", description.branch)
    else:
        branch = None
    fields = {
        **description.fields,
        "branch": branch,
        "version": base_version,
        "base_version": base_version,
        "next_version": next_version,
    }
    formats = {**DEFAULT_FORMATS, **params}
    try:
        fmt = formats[description.state]
    except KeyError:
        raise ConfigError(
            f"No format string for {description.state!r} state found in"
            " tool.versioningit.format"
        )
    if not isinstance(fmt, str):
        raise ConfigError("tool.versioningit.format.* values must be strings")
    return fmt.format_map(fields)


def basic_write(
    *,
    project_dir: str | Path,
    template_fields: dict[str, Any],
    params: dict[str, Any],
) -> None:
    """Implements the ``"basic"`` ``write`` method"""
    params = params.copy()
    filename = str_guard(params.pop("file", None), "tool.versioningit.write.file")
    path = Path(project_dir, filename)
    encoding = str_guard(
        params.pop("encoding", "utf-8"), "tool.versioningit.write.encoding"
    )
    try:
        template = str_guard(params.pop("template"), "tool.versioningit.write.template")
    except KeyError:
        if path.suffix == ".py":
            template = '__version__ = "{version}"'
        elif path.suffix == ".txt" or path.suffix == "":
            template = "{version}"
        else:
            raise ConfigError(
                "tool.versioningit.write.template not specified and file has"
                f" unknown suffix {path.suffix!r}"
            )
    warn_extra_fields(
        params, "tool.versioningit.write", ["file", "encoding", "template"]
    )
    log.debug("Ensuring parent directories of %s exist", path)
    path.parent.mkdir(parents=True, exist_ok=True)
    log.info("Writing version to file %s", path)
    path.write_text(template.format_map(template_fields) + "\n", encoding=encoding)


def basic_template_fields(
    *,
    version: str,
    description: Optional[VCSDescription],
    base_version: Optional[str],
    next_version: Optional[str],
    params: dict[str, Any],
) -> dict[str, Any]:
    """Implements the ``"basic"`` ``template-fields`` method"""
    params = deepcopy(params)
    vtuple_params = params.pop("version-tuple", {})
    SUBTABLE = "tool.versioningit.template-fields.version-tuple"
    if not isinstance(vtuple_params, dict):
        raise ConfigError(f"{SUBTABLE} must be a table")
    pep440 = bool_guard(vtuple_params.pop("pep440", False), f"{SUBTABLE}.pep440")
    epoch: Optional[bool]
    try:
        epoch = bool_guard(vtuple_params.pop("epoch"), f"{SUBTABLE}.epoch")
    except KeyError:
        epoch = None
    else:
        if not pep440:
            log.warning("%s.epoch is ignored when pep440 is false", SUBTABLE)
    split_on = optional_str_guard(
        vtuple_params.pop("split-on", None), f"{SUBTABLE}.split-on"
    )
    if pep440 and split_on is not None:
        log.warning("%s.split-on is ignored when pep440 is true", SUBTABLE)
    double_quote = bool_guard(
        vtuple_params.pop("double-quote", True), f"{SUBTABLE}.double-quote"
    )
    warn_extra_fields(
        vtuple_params, SUBTABLE, ["pep440", "epoch", "split-on", "double-quote"]
    )
    warn_extra_fields(params, "tool.versioningit.template-fields", ["version-tuple"])
    if pep440:
        version_tuple = split_pep440_version(
            version, epoch=epoch, double_quote=double_quote
        )
    else:
        version_tuple = split_version(
            version, split_on=split_on, double_quote=double_quote
        )
    fields: dict[str, Any] = {}
    if description is not None:
        fields.update(description.fields)
        fields["branch"] = description.branch
    if base_version is not None:
        fields["base_version"] = base_version
    if next_version is not None:
        fields["next_version"] = next_version
    fields["version"] = version
    fields["version_tuple"] = version_tuple
    return fields
