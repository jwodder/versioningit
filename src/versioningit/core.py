from __future__ import annotations
from dataclasses import dataclass
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional
from .config import Config
from .errors import Error, MethodError, NotSdistError, NotVCSError, NotVersioningitError
from .logging import log, warn_bad_version
from .methods import VersioningitMethod
from .onbuild import OnbuildFileProvider, SetuptoolsFileProvider
from .util import is_sdist, parse_version_from_metadata

if TYPE_CHECKING:
    from setuptools import Distribution


@dataclass
class VCSDescription:
    """A description of the state of a version control repository"""

    #: The name of the most recent tag in the repository (possibly after
    #: applying any match or exclusion rules based on user parameters) from
    #: which the current repository state is descended
    tag: str

    #: The relationship of the repository's current state to the tag.  If the
    #: repository state is exactly the tagged state, this field should equal
    #: ``"exact"``; otherwise, it will be a string that will be used as a key
    #: in the ``format`` subtable of the versioningit configuration.
    #: Recommended values are ``"distance"``, ``"dirty"``, and
    #: ``"distance-dirty"``.
    state: str

    #: The name of the repository's current branch, or `None` if it cannot be
    #: determined or does not apply
    branch: Optional[str]

    #: A `dict` of additional information about the repository state to make
    #: available to the ``format`` method.  Custom ``vcs`` methods are advised
    #: to adhere closely to the set of fields used by the built-in methods.
    fields: dict[str, Any]


@dataclass
class Report:
    """
    .. versionadded:: 2.0.0

    A report of the intermediate & final values calculated during a
    ``versioningit`` run
    """

    #: The final version
    version: str

    #: A description of the state of the version control repository; `None` if
    #: the "vcs" step failed
    description: Optional[VCSDescription]

    #: A version string extracted from the VCS tag; `None` if the "tag2version"
    #: step or a previous step failed
    base_version: Optional[str]

    #: A "next version" calculated by the "next-version" step; `None` if the
    #: step or a previous one failed
    next_version: Optional[str]

    #: A `dict` of fields for use in templating by the "write" and "onbuild"
    #: steps
    template_fields: dict[str, Any]

    #: `True` iff an error occurred during version calculation, causing a
    #: ``default-version`` setting to be used
    using_default_version: bool


@dataclass
class FallbackReport:
    """
    .. versionadded:: 2.0.0

    A report of the version extracted from a :file:`PKG-INFO` file in an sdist
    """

    #: The version
    version: str


@dataclass
class Versioningit:
    """
    A class for getting a version-controlled project's current version based on
    its most recent tag and the difference therefrom
    """

    #: The path to the root of the project directory (usually the location of a
    #: :file:`pyproject.toml` file)
    #:
    #: :meta private:
    project_dir: Path

    #: The default version, if any, to use if an error occurs
    #:
    #: :meta private:
    default_version: Optional[str]

    #: The method to call for the ``vcs`` step
    #:
    #: :meta private:
    vcs: VersioningitMethod

    #: The method to call for the ``tag2version`` step
    #:
    #: :meta private:
    tag2version: VersioningitMethod

    #: The method to call for the ``next-version`` step
    #:
    #: :meta private:
    next_version: VersioningitMethod

    #: The method to call for the ``format`` step
    #:
    #: :meta private:
    format: VersioningitMethod

    #: The method to call for the ``template-fields`` step
    #:
    #: :meta private:
    template_fields: VersioningitMethod

    #: The method to call for the ``write`` step
    #:
    #: :meta private:
    write: Optional[VersioningitMethod]

    #: The method to call for the ``onbuild`` step
    #:
    #: :meta private:
    onbuild: Optional[VersioningitMethod]

    @classmethod
    def from_project_dir(
        cls, project_dir: str | Path = os.curdir, config: Optional[dict] = None
    ) -> Versioningit:
        """
        Construct a `Versioningit` object for the project rooted at
        ``project_dir`` (default: the current directory).

        If ``config`` is `None`, then ``project_dir`` must contain a
        :file:`pyproject.toml` file containing either a ``[tool.versioningit]``
        table or a ``[tool.hatch.version]`` table with the ``source`` key set
        to ``"versioningit"``; if it does not, a `NotVersioningitError` is
        raised.  If ``config`` is not `None`, then any :file:`pyproject.toml`
        file in ``project_dir`` will be ignored, and the configuration will be
        taken from ``config`` instead.  See ":ref:`config_dict`".

        :raises NotVersioningitError:
            - if ``config`` is `None` and ``project_dir`` does not contain a
              :file:`pyproject.toml` file
            - if ``config`` is `None` and the :file:`pyproject.toml` file does
              not contain a versioningit configuration table
        :raises ConfigError:
            if the configuration object/table or any of its subfields are not
            of the correct type
        """
        if config is None:
            try:
                path = Path(project_dir, "versioningit.toml")
                path = path if path.is_file() else Path(project_dir, "pyproject.toml")
                cfg = Config.parse_toml_file(path)
            except FileNotFoundError:
                raise NotVersioningitError(f"No pyproject.toml or versioningit.toml file in {project_dir}")
        else:
            cfg = Config.parse_obj(config)
        return cls.from_config(project_dir, cfg)

    @classmethod
    def from_config(cls, project_dir: str | Path, config: Config) -> Versioningit:
        """
        Construct a `Versioningit` object from a parsed configuration object

        :meta private:
        """
        project_dir = Path(project_dir)
        return cls(
            project_dir=project_dir,
            default_version=config.default_version,
            vcs=config.vcs.load(project_dir),
            tag2version=config.tag2version.load(project_dir),
            next_version=config.next_version.load(project_dir),
            format=config.format.load(project_dir),
            template_fields=config.template_fields.load(project_dir),
            write=config.write.load(project_dir) if config.write is not None else None,
            onbuild=(
                config.onbuild.load(project_dir) if config.onbuild is not None else None
            ),
        )

    def get_version(self, write: bool = False, fallback: bool = True) -> str:
        """
        Determine the version for the project.

        If ``write`` is true, then the file specified in the ``write`` subtable
        of the versioningit configuration, if any, will be updated.

        If ``fallback`` is true, then if ``project_dir`` is not under version
        control (or if the VCS executable is not installed), ``versioningit``
        will assume that the directory is an unpacked sdist and will read the
        version from the :file:`PKG-INFO` file.

        .. versionchanged:: 2.0.0

            ``write`` and ``fallback`` arguments added

        :raises NotVCSError:
            if ``fallback`` is false and ``project_dir`` is not under version
            control
        :raises NotSdistError:
            if ``fallback`` is true, ``project_dir`` is not under version
            control, and there is no :file:`PKG-INFO` file in ``project_dir``
        :raises ConfigError:
            if any of the values in ``config`` are not of the correct type
        :raises MethodError: if a method returns a value of the wrong type
        """
        return self.run(write=write, fallback=fallback).version

    def run(
        self, write: bool = False, fallback: bool = True
    ) -> Report | FallbackReport:
        """
        .. versionadded:: 2.0.0

        Run all of the steps for the project — aside from "onbuild" and,
        optionally, "write" — and return an object containing the final version
        and intermediate values.

        If ``write`` is true, then the file specified in the ``write`` subtable
        of the versioningit configuration, if any, will be updated.

        If ``fallback`` is true, then if ``project_dir`` is not under version
        control (or if the VCS executable is not installed), ``versioningit``
        will assume that the directory is an unpacked sdist and will read the
        version from the :file:`PKG-INFO` file, returning a `FallbackReport`
        instance instead of a `Report`.

        :raises NotVCSError:
            if ``fallback`` is false and ``project_dir`` is not under version
            control
        :raises NotSdistError:
            if ``fallback`` is true, ``project_dir`` is not under version
            control, and there is no :file:`PKG-INFO` file in ``project_dir``
        :raises ConfigError:
            if any of the values in ``config`` are not of the correct type
        :raises MethodError: if a method returns a value of the wrong type
        """
        description: Optional[VCSDescription] = None
        base_version: Optional[str] = None
        next_version: Optional[str] = None
        using_default_version: bool = False
        try:
            description = self.do_vcs()
            base_version = self.do_tag2version(description.tag)
            next_version = self.do_next_version(base_version, description.branch)
            if description.state == "exact":
                log.info("Tag is exact match; returning extracted version")
                version = base_version
            else:
                log.info("VCS state is %r; formatting version", description.state)
                version = self.do_format(
                    description=description,
                    base_version=base_version,
                    next_version=next_version,
                )
            log.info("Final version: %s", version)
        except Error as e:
            if (
                isinstance(e, NotVCSError)
                and fallback
                and (is_sdist(self.project_dir) or self.default_version is None)
            ):
                log.info("Could not get VCS data from %s: %s", self.project_dir, str(e))
                log.info("Falling back to reading from PKG-INFO")
                return FallbackReport(
                    version=get_version_from_pkg_info(self.project_dir)
                )
            if self.default_version is not None:
                log.error("%s: %s", type(e).__name__, str(e))
                log.info("Falling back to default-version")
                version = self.default_version
                using_default_version = True
            else:
                raise
        except Exception:  # pragma: no cover
            if self.default_version is not None:
                log.exception("An unexpected error occurred:")
                log.info("Falling back to default-version")
                version = self.default_version
                using_default_version = True
            else:
                raise
        warn_bad_version(version, "Final version")
        template_fields = self.do_template_fields(
            version=version,
            description=description,
            base_version=base_version,
            next_version=next_version,
        )
        if write:
            self.do_write(template_fields)
        return Report(
            version=version,
            description=description,
            base_version=base_version,
            next_version=next_version,
            template_fields=template_fields,
            using_default_version=using_default_version,
        )

    def do_vcs(self) -> VCSDescription:
        """
        Run the ``vcs`` step

        :raises MethodError: if the method does not return a `VCSDescription`
        """
        description = self.vcs(project_dir=self.project_dir)
        if not isinstance(description, VCSDescription):
            raise MethodError(
                f"vcs method returned {description!r} instead of a VCSDescription"
            )
        log.info("vcs returned tag %s", description.tag)
        log.debug("vcs state: %s", description.state)
        log.debug("vcs branch: %s", description.branch)
        log.debug("vcs fields: %r", description.fields)
        return description

    def do_tag2version(self, tag: str) -> str:
        """
        Run the ``tag2version`` step

        :raises MethodError: if the method does not return a `str`
        """
        version = self.tag2version(tag=tag)
        if not isinstance(version, str):
            raise MethodError(
                f"tag2version method returned {version!r} instead of a string"
            )
        log.info("tag2version returned version %s", version)
        warn_bad_version(version, "Version extracted from tag")
        return version

    def do_next_version(self, version: str, branch: Optional[str]) -> str:
        """
        Run the ``next-version`` step

        :raises MethodError: if the method does not return a `str`
        """
        next_version = self.next_version(version=version, branch=branch)
        if not isinstance(next_version, str):
            raise MethodError(
                f"next-version method returned {next_version!r} instead of a string"
            )
        log.info("next-version returned version %s", next_version)
        warn_bad_version(next_version, "Calculated next version")
        return next_version

    def do_format(
        self, description: VCSDescription, base_version: str, next_version: str
    ) -> str:
        """
        Run the ``format`` step

        .. versionchanged:: 2.0.0

            The ``version`` argument was renamed to ``base_version``.

        :raises MethodError: if the method does not return a `str`
        """
        new_version = self.format(
            description=description,
            base_version=base_version,
            next_version=next_version,
        )
        if not isinstance(new_version, str):
            raise MethodError(
                f"format method returned {new_version!r} instead of a string"
            )
        return new_version

    def do_template_fields(
        self,
        version: str,
        description: Optional[VCSDescription],
        base_version: Optional[str],
        next_version: Optional[str],
    ) -> dict:
        """
        .. versionadded:: 2.0.0

        Run the ``template_fields`` step

        :raises MethodError: if the method does not return a `dict`
        """
        fields = self.template_fields(
            version=version,
            description=description,
            base_version=base_version,
            next_version=next_version,
        )
        if not isinstance(fields, dict):
            raise MethodError(
                f"template-fields method returned {fields!r} instead of a dict"
            )
        log.debug("Template fields available to `write` and `onbuild`: %r", fields)
        return fields

    def do_write(self, template_fields: dict[str, Any]) -> None:
        """
        Run the ``write`` step

        .. versionchanged:: 2.0.0

            ``version`` argument replaced with ``template_fields``
        """
        if self.write is not None:
            self.write(project_dir=self.project_dir, template_fields=template_fields)
        else:
            log.info("'write' step not configured; not writing anything")

    def do_onbuild(
        self,
        file_provider: OnbuildFileProvider,
        is_source: bool,
        template_fields: dict[str, Any],
    ) -> None:
        """
        .. versionadded:: 1.1.0

        Run the ``onbuild`` step

        .. versionchanged:: 2.0.0

            ``version`` argument replaced with ``template_fields``

        .. versionchanged:: 3.0.0

            ``build_dir`` argument replaced with ``file_provider``
        """
        if self.onbuild is not None:
            self.onbuild(
                file_provider=file_provider,
                is_source=is_source,
                template_fields=template_fields,
            )
        else:
            log.info("'onbuild' step not configured; not doing anything")


def get_version(
    project_dir: str | Path = os.curdir,
    config: Optional[dict] = None,
    write: bool = False,
    fallback: bool = True,
) -> str:
    """
    Determine the version for the project at ``project_dir``.

    If ``config`` is `None`, then ``project_dir`` must contain a
    :file:`pyproject.toml` file containing either a ``[tool.versioningit]``
    table or a ``[tool.hatch.version]`` table with the ``source`` key set to
    ``"versioningit"``; if it does not, a `NotVersioningitError` is raised.  If
    ``config`` is not `None`, then any :file:`pyproject.toml` file in
    ``project_dir`` will be ignored, and the configuration will be taken from
    ``config`` instead.  See ":ref:`config_dict`".

    If ``write`` is true, then the file specified in the ``write`` subtable of
    the versioningit configuration, if any, will be updated.

    If ``fallback`` is true, then if ``project_dir`` is not under version
    control (or if the VCS executable is not installed), ``versioningit`` will
    assume that the directory is an unpacked sdist and will read the version
    from the :file:`PKG-INFO` file.

    :raises NotVCSError:
        if ``fallback`` is false and ``project_dir`` is not under version
        control
    :raises NotSdistError:
        if ``fallback`` is true, ``project_dir`` is not under version control,
        and there is no :file:`PKG-INFO` file in ``project_dir``
    :raises NotVersioningitError:
        - if ``config`` is `None` and ``project_dir`` does not contain a
          :file:`pyproject.toml` file
        - if ``config`` is `None` and the :file:`pyproject.toml` file does not
          contain a versioningit configuration table
    :raises ConfigError:
        if any of the values in ``config`` are not of the correct type
    :raises MethodError: if a method returns a value of the wrong type
    """
    vgit = Versioningit.from_project_dir(project_dir, config)
    return vgit.get_version(write=write, fallback=fallback)


def get_next_version(
    project_dir: str | Path = os.curdir, config: Optional[dict] = None
) -> str:
    """
    .. versionadded:: 0.3.0

    Determine the next version after the current VCS-tagged version for
    ``project_dir``.

    If ``config`` is `None`, then ``project_dir`` must contain a
    :file:`pyproject.toml` file containing either a ``[tool.versioningit]``
    table or a ``[tool.hatch.version]`` table with the ``source`` key set to
    ``"versioningit"``; if it does not, a `NotVersioningitError` is raised.  If
    ``config`` is not `None`, then any :file:`pyproject.toml` file in
    ``project_dir`` will be ignored, and the configuration will be taken from
    ``config`` instead.  See ":ref:`config_dict`".

    :raises NotVCSError:
        if ``project_dir`` is not under version control
    :raises NotVersioningitError:
        - if ``config`` is `None` and ``project_dir`` does not contain a
          :file:`pyproject.toml` file
        - if ``config`` is `None` and the :file:`pyproject.toml` file does not
          contain a versioningit configuration table
    :raises ConfigError:
        if any of the values in ``config`` are not of the correct type
    :raises MethodError: if a method returns a value of the wrong type
    """
    vgit = Versioningit.from_project_dir(project_dir, config)
    description = vgit.do_vcs()
    tag_version = vgit.do_tag2version(description.tag)
    next_version = vgit.do_next_version(tag_version, description.branch)
    return next_version


def get_version_from_pkg_info(project_dir: str | Path) -> str:
    """
    Return the :mailheader:`Version` field from the :file:`PKG-INFO` file in
    ``project_dir``

    :raises NotSdistError: if there is no :file:`PKG-INFO` file
    :raises ValueError:
        if the :file:`PKG-INFO` file does not contain a :mailheader:`Version`
        field
    """
    try:
        return parse_version_from_metadata(
            Path(project_dir, "PKG-INFO").read_text(encoding="utf-8")
        )
    except FileNotFoundError:
        raise NotSdistError(f"{project_dir} does not contain a PKG-INFO file")


def run_onbuild(
    *,
    build_dir: str | Path,
    is_source: bool,
    template_fields: dict[str, Any],
    project_dir: str | Path = os.curdir,
    config: Optional[dict] = None,
) -> None:
    """
    .. versionadded:: 1.1.0

    Run the ``onbuild`` step for the given setuptools project.

    This function is intended to be used by custom setuptools command classes
    that are used in place of ``versioningit``'s command classes but still need
    to be able to run the ``onbuild`` step.  The ``template_fields`` value can
    be obtained by passing a command class's ``distribution`` attribute to
    `get_template_fields_from_distribution()`; if this returns `None`, then we
    are building from an sdist, and `run_onbuild()` should not be called.

    If ``config`` is `None`, then ``project_dir`` must contain a
    :file:`pyproject.toml` file containing a ``[tool.versioningit]`` table; if
    it does not, a `NotVersioningitError` is raised.  If ``config`` is not
    `None`, then any :file:`pyproject.toml` file in ``project_dir`` will be
    ignored, and the configuration will be taken from ``config`` instead; see
    ":ref:`config_dict`".

    .. versionchanged:: 2.0.0

        ``version`` argument replaced with ``template_fields``

    :param build_dir: The directory containing the in-progress build
    :param is_source:
        Set to `True` if building an sdist or other artifact that preserves
        source paths, `False` if building a wheel or other artifact that uses
        installation paths
    :param template_fields: A `dict` of fields to be used when templating
    :raises NotVersioningitError:
        - if ``config`` is `None` and ``project_dir`` does not contain a
          :file:`pyproject.toml` file
        - if the :file:`pyproject.toml` file does not contain a
          ``[tool.versioningit]`` table
    :raises ConfigError:
        if any of the values in ``config`` are not of the correct type
    :raises MethodError: if a method returns a value of the wrong type
    """
    vgit = Versioningit.from_project_dir(project_dir, config)
    vgit.do_onbuild(
        file_provider=SetuptoolsFileProvider(build_dir=Path(build_dir)),
        is_source=is_source,
        template_fields=template_fields,
    )


def get_template_fields_from_distribution(
    dist: Distribution,
) -> Optional[dict[str, Any]]:
    """
    Extract the template fields (calculated by the "template-fields" step) that
    were stashed on the `setuptools.Distribution` by ``versioningit``'s
    setuptools hook, for passing to the "onbuild" step.  If setuptools is
    building from an sdist instead of a repository, no template fields will
    have been calculated, and `None` will be returned, indicating that the
    "onbuild" step should not be run.
    """
    return getattr(dist, "_versioningit_template_fields", None)
