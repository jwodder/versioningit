from pathlib import Path
import re
from typing import Any, Optional, Union
from .core import VCSDescription
from .errors import ConfigError
from .logging import log, warn_extra_fields
from .util import str_guard, strip_prefix, strip_suffix

DEFAULT_FORMATS = {
    "distance": "{next_version}.dev{distance}+{vcs}{rev}",
    "dirty": "{version}+dirty",
    "distance-dirty": "{next_version}.dev{distance}+{vcs}{rev}.dirty",
}


def basic_tag2version(tag: str, **kwargs: Any) -> str:
    try:
        rmprefix = str_guard(
            kwargs.pop("rmprefix"), "tool.versioningit.tag2version.rmprefix"
        )
    except KeyError:
        pass
    else:
        tag = strip_prefix(tag, rmprefix)
    try:
        rmsuffix = str_guard(
            kwargs.pop("rmsuffix"), "tool.versioningit.tag2version.rmsuffix"
        )
    except KeyError:
        pass
    else:
        tag = strip_suffix(tag, rmsuffix)
    try:
        regex = str_guard(kwargs.pop("regex"), "tool.versioningit.tag2version.regex")
    except KeyError:
        pass
    else:
        m = re.fullmatch(regex, tag)
        if m is None:
            log.info("tag2version.regex did not match tag; leaving unmodified")
        elif not m.groups():
            raise ConfigError(
                "No capturing groups in tool.versioningit.tag2version.regex"
            )
        else:
            if "version" in m.groupdict():
                tag = m["version"]
            else:
                tag = m[1]
            if tag is None:
                ### TODO: Should this be something else instead of a
                ### ConfigError?
                raise ConfigError(
                    "Version group in tool.versioningit.tag2version.regex did"
                    " not participate in match"
                )
    warn_extra_fields(kwargs, "tool.versioningit.tag2version")
    return tag.lstrip("v")


def basic_format(
    description: VCSDescription, version: str, next_version: str, **kwargs: Any
) -> str:
    branch: Optional[str]
    if description.branch is not None:
        branch = re.sub(r"[^A-Za-z0-9.]", ".", description.branch)
    else:
        branch = None
    fields = {
        **description.fields,
        "branch": branch,
        "version": version,
        "next_version": next_version,
    }
    formats = {**DEFAULT_FORMATS, **kwargs}
    try:
        fmt = formats[description.state]
    except KeyError:
        raise ConfigError(
            f"No format string for {description.state!r} state found in"
            " tool.versioningit.format"
        )
    return fmt.format_map(fields)


def basic_write(project_dir: Union[str, Path], version: str, **kwargs: Any) -> None:
    try:
        filename = str_guard(kwargs.pop("file"), "tool.versioningit.write.file")
    except KeyError:
        log.debug("No 'file' field in tool.versioningit.write; not writing anything")
        return
    path = Path(project_dir, filename)
    enc = kwargs.pop("encoding", None)
    encoding: Optional[str]
    if enc is not None:
        encoding = str_guard(enc, "tool.versioningit.write.encoding")
    else:
        encoding = None
    try:
        template = str_guard(kwargs.pop("template"), "tool.versioningit.write.template")
    except KeyError:
        if path.suffix == ".py":
            template = '__version__ = "{version}"'
        elif path.suffix == ".txt":
            template = "{version}"
        else:
            raise ConfigError(
                "tool.versioningit.write.template not specified and file has"
                f" unknown suffix {path.suffix!r}"
            )
    warn_extra_fields(kwargs, "tool.versioningit.write")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(template.format(version=version) + "\n", encoding=encoding)
