from pathlib import Path
import re
from typing import Any, Dict, Union
from .errors import ConfigError
from .logging import log, warn_extra_fields
from .util import optional_str_guard, str_guard


def replace_version_onbuild(
    *,
    build_dir: Union[str, Path],
    is_source: bool,
    version: str,
    params: Dict[str, Any],
) -> None:
    """Implements the ``"replace-version"`` ``onbuild`` method"""

    DEFAULT_REGEX = r"^\s*__version__\s*=\s*(?P<version>.*)"
    DEFAULT_REPLACEMENT = '"{version}"'

    source_file = str_guard(
        params.pop("source-file", None), "tool.versioningit.onbuild.source-file"
    )
    build_file = str_guard(
        params.pop("build-file", None), "tool.versioningit.onbuild.build-file"
    )
    encoding = str_guard(
        params.pop("encoding", "utf-8"), "tool.versioningit.onbuild.encoding"
    )
    regex = str_guard(
        params.pop("regex", DEFAULT_REGEX), "tool.versioningit.onbuild.regex"
    )
    try:
        rgx = re.compile(regex)
    except ValueError as e:
        raise ConfigError(f"tool.versioningit.onbuild.regex: Invalid regex: {e}")
    require_match = bool(params.pop("require-match", False))
    replacement = str_guard(
        params.pop("replacement", DEFAULT_REPLACEMENT),
        "tool.versioningit.onbuild.replacement",
    )
    append_line = optional_str_guard(
        params.pop("append-line", None), "tool.versioningit.onbuild.append-line"
    )
    warn_extra_fields(
        params,
        "tool.versioningit.onbuild",
        [
            "source-file",
            "build-file",
            "encoding",
            "regex",
            "require-match",
            "replacement",
            "append-line",
        ],
    )

    path = Path(build_dir, source_file if is_source else build_file)
    log.info("Updating version in file %s", path)
    lines = path.read_text(encoding=encoding).splitlines(keepends=True)
    for i, ln in enumerate(lines):
        m = rgx.search(ln)
        if m:
            log.debug("onbuild.regex matched file on line %d", i + 1)
            vgroup: Union[str, int]
            if "version" in m.groupdict():
                vgroup = "version"
            else:
                vgroup = 0
            if m[vgroup] is None:
                raise RuntimeError(
                    "<version> group in onbuild.regex did not participate in match"
                )
            newline = ensure_terminated(
                ln[: m.start(vgroup)]
                + m.expand(replacement.format(version=version))
                + ln[m.end(vgroup) :]
            )
            log.debug("Replacing line %r with %r", ln, newline)
            lines[i] = newline
            break
    else:
        if require_match:
            raise RuntimeError(f"onbuild.regex did not match any lines in {path}")
        elif append_line is not None:
            log.info(
                "onbuild.regex did not match any lines in the file; appending line"
            )
            if lines:
                lines[-1] = ensure_terminated(lines[-1])
            lines.append(ensure_terminated(append_line.format(version=version)))
        else:
            log.info(
                "onbuild.regex did not match any lines in the file; leaving unmodified"
            )
            return
    path.unlink()  # In case of hard links
    path.write_text("".join(lines), encoding=encoding)


def ensure_terminated(s: str) -> str:
    if s.endswith(("\r\n", "\n", "\r")):
        return s
    else:
        return s + "\n"
