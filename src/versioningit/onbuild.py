from __future__ import annotations
from abc import ABC, abstractmethod
from contextlib import suppress
from dataclasses import dataclass, field
import os
from pathlib import Path, PurePath
import re
import shutil
import tempfile
from typing import IO, TYPE_CHECKING, Any, TextIO, overload
from .errors import ConfigError
from .logging import log, warn_extra_fields
from .util import bool_guard, ensure_terminated, optional_str_guard, str_guard

if TYPE_CHECKING:
    from typing_extensions import Literal, TypeAlias

    TextMode: TypeAlias = Literal["r", "w", "a"]
    BinaryMode: TypeAlias = Literal["rb", "br", "wb", "bw", "ab", "ba"]


class OnbuildFileProvider(ABC):
    """
    .. versionadded:: 3.0.0

    An abstract base class for accessing files that are about to be included in
    an sdist or wheel currently being built
    """

    @abstractmethod
    def get_file(
        self, source_path: str | PurePath, install_path: str | PurePath, is_source: bool
    ) -> OnbuildFile:
        """
        Get an object for reading & writing a file in the project being built.

        :param source_path:
            the path to the file relative to the root of the project's source
        :param install_path:
            the path to the same file when it's in a wheel, relative to the
            root of the wheel (or, equivalently, the path to the file when it's
            installed in a site-packages directory, relative to that directory)
        :param is_source:
            `True` if building an sdist or other artifact that preserves source
            paths, `False` if building a wheel or other artifact that uses
            install paths
        """
        ...


class OnbuildFile(ABC):
    """
    .. versionadded:: 3.0.0

    An abstract base class for opening a file in a project currently being
    built
    """

    @overload
    def open(
        self,
        mode: TextMode = "r",
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
    ) -> TextIO: ...

    @overload
    def open(
        self,
        mode: BinaryMode,
        encoding: None = None,
        errors: None = None,
        newline: None = None,
    ) -> IO[bytes]: ...

    @abstractmethod
    def open(
        self,
        mode: TextMode | BinaryMode = "r",
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
    ) -> IO:
        """
        Open the associated file.  ``mode`` must be ``"r"``, ``"w"``, ``"a"``,
        ``"rb"``, ``"br"``, ``"wb"``, ``"bw"``, ``"ab"``, or ``"ba"``.

        When opening a file for writing or appending, if the file does not
        already exist, any parent directories are created automatically.
        """
        ...


@dataclass
class SetuptoolsFileProvider(OnbuildFileProvider):
    """
    .. versionadded:: 3.0.0

    `OnbuildFileProvider` implementation for use when building sdists or wheels
    under setuptools.

    Setuptools builds its artifacts by creating a temporary directory
    containing all of the files (sometimes hardlinked) that will go into them
    and then building an archive from that directory.  "onbuild" runs just
    before the archive step, so this provider simply operates directly on the
    temporary directory without ever looking at the project source.
    """

    #: The setuptools-managed temporary directory containing the files for the
    #: archive currently being built
    build_dir: Path

    #: The set of file paths in `build_dir` (relative to `build_dir`) that have
    #: been opened for writing or appending
    modified: set[PurePath] = field(init=False, default_factory=set)

    def get_file(
        self, source_path: str | PurePath, install_path: str | PurePath, is_source: bool
    ) -> SetuptoolsOnbuildFile:
        return SetuptoolsOnbuildFile(
            provider=self,
            source_path=PurePath(source_path),
            install_path=PurePath(install_path),
            is_source=is_source,
        )


@dataclass
class SetuptoolsOnbuildFile(OnbuildFile):
    provider: SetuptoolsFileProvider
    source_path: PurePath
    install_path: PurePath
    is_source: bool

    @overload
    def open(
        self,
        mode: TextMode = "r",
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
    ) -> TextIO: ...

    @overload
    def open(
        self,
        mode: BinaryMode,
        encoding: None = None,
        errors: None = None,
        newline: None = None,
    ) -> IO[bytes]: ...

    def open(
        self,
        mode: TextMode | BinaryMode = "r",
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
    ) -> IO:
        path = self.source_path if self.is_source else self.install_path
        p = self.provider.build_dir / path
        if ("w" in mode or "a" in mode) and path not in self.provider.modified:
            self.provider.modified.add(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            # If setuptools is using hard links for the build files, undo that
            # for this file:
            if "w" in mode:
                with suppress(FileNotFoundError):
                    p.unlink()
            elif p.exists():
                # We've been asked to append to the file, so replace it with a
                # non-hardlinked copy of its contents:
                fd, tmp = tempfile.mkstemp(dir=self.provider.build_dir)
                os.close(fd)
                shutil.copy2(p, tmp)
                os.replace(tmp, p)
        return p.open(mode=mode, encoding=encoding, errors=errors, newline=newline)


@dataclass
class HatchFileProvider(OnbuildFileProvider):
    """
    .. versionadded:: 3.0.0

    `OnbuildFileProvider` implementation for use when building sdists or wheels
    under Hatch.

    Hatch builds its artifacts by reading the contents of the files in the
    project directory directly into an in-memory archive.  In order to modify
    what goes into that archive without altering anything in the project
    directory, we need to write all modifications to a temporary directory and
    register the resulting files as "forced inclusion paths."
    """

    #: The root of the project directory
    src_dir: Path

    #: A temporary directory (managed outside the provider) in which to create
    #: modified files
    tmp_dir: Path

    #: The set of file paths created under the temporary directory, relative to
    #: the temporary directory
    modified: set[PurePath] = field(init=False, default_factory=set)

    def get_file(
        self, source_path: str | PurePath, install_path: str | PurePath, is_source: bool
    ) -> HatchOnbuildFile:
        return HatchOnbuildFile(
            provider=self,
            source_path=PurePath(source_path),
            install_path=PurePath(install_path),
            is_source=is_source,
        )

    def get_force_include(self) -> dict[str, str]:
        return {str(self.tmp_dir / p): str(p) for p in self.modified}


@dataclass
class HatchOnbuildFile(OnbuildFile):
    provider: HatchFileProvider
    source_path: PurePath
    install_path: PurePath
    is_source: bool

    @overload
    def open(
        self,
        mode: TextMode = "r",
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
    ) -> TextIO: ...

    @overload
    def open(
        self,
        mode: BinaryMode,
        encoding: None = None,
        errors: None = None,
        newline: None = None,
    ) -> IO[bytes]: ...

    def open(
        self,
        mode: TextMode | BinaryMode = "r",
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
    ) -> IO:
        path = self.source_path if self.is_source else self.install_path
        if "r" in mode and path not in self.provider.modified:
            return (self.provider.src_dir / self.source_path).open(
                mode=mode, encoding=encoding, errors=errors
            )
        else:
            p = self.provider.tmp_dir / path
            if ("w" in mode or "a" in mode) and path not in self.provider.modified:
                self.provider.modified.add(path)
                p.parent.mkdir(parents=True, exist_ok=True)
                if not p.exists() and "a" in mode:
                    with suppress(FileNotFoundError):
                        shutil.copy2(self.provider.src_dir / self.source_path, p)
            return p.open(mode=mode, encoding=encoding, errors=errors, newline=newline)


def replace_version_onbuild(
    *,
    file_provider: OnbuildFileProvider,
    is_source: bool,
    template_fields: dict[str, Any],
    params: dict[str, Any],
) -> None:
    """Implements the ``"replace-version"`` ``onbuild`` method"""

    DEFAULT_REGEX = r"^\s*__version__\s*=\s*(?P<version>.*)"
    DEFAULT_REPLACEMENT = '"{version}"'

    params = params.copy()
    source_file = str_guard(params.pop("source-file", None), "onbuild.source-file")
    build_file = str_guard(params.pop("build-file", None), "onbuild.build-file")
    encoding = str_guard(params.pop("encoding", "utf-8"), "onbuild.encoding")
    regex = str_guard(params.pop("regex", DEFAULT_REGEX), "onbuild.regex")
    try:
        rgx = re.compile(regex)
    except re.error as e:
        raise ConfigError(f"versioningit: onbuild.regex: Invalid regex: {e}")
    require_match = bool_guard(
        params.pop("require-match", False), "onbuild.require-match"
    )
    replacement = str_guard(
        params.pop("replacement", DEFAULT_REPLACEMENT), "onbuild.replacement"
    )
    append_line = optional_str_guard(
        params.pop("append-line", None), "onbuild.append-line"
    )
    warn_extra_fields(
        params,
        "onbuild",
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

    path = source_file if is_source else build_file
    log.info("Updating version in file %s", path)
    file = file_provider.get_file(
        source_path=source_file,
        install_path=build_file,
        is_source=is_source,
    )
    with file.open(encoding=encoding) as fp:
        # Don't use readlines(), as that doesn't split on everything that
        # splitlines() uses
        lines = fp.read().splitlines(keepends=True)
    for i, ln in enumerate(lines):
        m = rgx.search(ln)
        if m:
            log.debug("onbuild.regex matched file on line %d", i + 1)
            vgroup: str | int
            if "version" in m.groupdict():
                vgroup = "version"
            else:
                vgroup = 0
            if m[vgroup] is None:
                raise RuntimeError(
                    "'version' group in versioningit's onbuild.regex did"
                    " not participate in match"
                )
            newline = ensure_terminated(
                ln[: m.start(vgroup)]
                + m.expand(replacement.format_map(template_fields))
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
            lines.append(ensure_terminated(append_line.format_map(template_fields)))
        else:
            log.info(
                "onbuild.regex did not match any lines in the file; leaving unmodified"
            )
            return
    with file.open("w", encoding=encoding) as fp:
        fp.writelines(lines)


def get_pretend_version(project_root: Path) -> str | None:
    # Reads from a file .git/versioningit-pretend-version
    filename = project_root / ".git" / "versioningit-pretend-version"
    if not filename.exists():
        return None
    with open(filename) as f:
        return f.read().strip()
