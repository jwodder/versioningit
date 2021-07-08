from pathlib import Path
import re
from typing import Any, Optional, Union
from .core import VCSDescription
from .errors import ConfigError, InvalidTagError
from .logging import log, warn_extra_fields
from .util import str_guard, strip_prefix, strip_suffix

#: The default formats for the ``"basic"`` ``format`` method
DEFAULT_FORMATS = {
    "distance": "{version}.post{distance}+{vcs}{rev}",
    "dirty": "{version}+d{build_date:%Y%m%d}",
    "distance-dirty": "{version}.post{distance}+{vcs}{rev}.d{build_date:%Y%m%d}",
}


def basic_tag2version(*, tag: str, **kwargs: Any) -> str:
    """Implements the ``"basic"`` ``tag2version`` method"""
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
    require_match = bool(kwargs.pop("require-match", False))
    try:
        regex = str_guard(kwargs.pop("regex"), "tool.versioningit.tag2version.regex")
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
        kwargs,
        "tool.versioningit.tag2version",
        ["rmprefix", "rmsuffix", "regex", "require-match"],
    )
    return tag.lstrip("v")


def basic_format(
    *, description: VCSDescription, version: str, next_version: str, **kwargs: Any
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


def basic_write(*, project_dir: Union[str, Path], version: str, **kwargs: Any) -> None:
    """Implements the ``"basic"`` ``write`` method"""
    try:
        filename = str_guard(kwargs.pop("file"), "tool.versioningit.write.file")
    except KeyError:
        log.debug("No 'file' field in tool.versioningit.write; not writing anything")
        return
    path = Path(project_dir, filename)
    encoding = str_guard(
        kwargs.pop("encoding", "utf-8"), "tool.versioningit.write.encoding"
    )
    try:
        template = str_guard(kwargs.pop("template"), "tool.versioningit.write.template")
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
        kwargs, "tool.versioningit.write", ["file", "encoding", "template"]
    )
    log.debug("Ensuring parent directories of %s exist", path)
    path.parent.mkdir(parents=True, exist_ok=True)
    log.info("Writing version %s to file %s", version, path)
    path.write_text(template.format(version=version) + "\n", encoding=encoding)
