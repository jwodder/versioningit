.. currentmodule:: versioningit

Changelog
=========

v3.0.0 (in development)
-----------------------
- Migrated from setuptools to hatch
- Support using the ``onbuild`` step with Hatch
- **Breaking**: The ``build_dir`` argument passed to
  `Versioningit.do_onbuild()` and ``onbuild`` method callables has been changed
  to a `FileProvider` ABC


v2.3.0 (2023-11-19)
-------------------
- Always read :file:`.hg_archival.txt` files using UTF-8 encoding
- Added support for using versioningit with `Hatch <https://hatch.pypa.io>`_


v2.2.1 (2023-09-22)
-------------------
- Raise a `ConfigError` if the selected ``tool.versioningit.format`` field is
  not a string
- Update tests for pydantic 2.0
- Update tests for Python 3.12
- Support Python 3.12


v2.2.0 (2023-02-11)
-------------------
- The custom setuptools command classes can now be imported directly from the
  ``versioningit.cmdclass`` module as an alternative to calling
  `get_cmdclasses()`


v2.1.0 (2022-10-25)
-------------------
- Drop support for Python 3.6
- Support Python 3.11
- Use `tomllib` on Python 3.11


v2.0.1 (2022-08-01)
-------------------
- Don't run the ``onbuild`` step under setuptools' upcoming PEP 660 editable
  mode (contributed by `@abravalheri <https://github.com/abravalheri>`_)


v2.0.0 (2022-06-12)
-------------------
- The ``{version}`` placeholder in the "basic" ``format`` step has been renamed
  to ``{base_version}``.  The old name remains usable, but is deprecated.

  - **Breaking**: The ``version`` argument passed to `Versioningit.do_format()`
    and ``format`` method callables has been renamed to ``base_version``.

- A ``{version_tuple}`` field, along with the fields available in the
  ``format`` step, is now available for use in templates in the ``write`` and
  ``onbuild`` steps.

  - New step and subtable: "template-fields"

  - **Breaking**: The ``version`` arguments passed to
    `Versioningit.do_write()`, `Versioningit.do_onbuild()`, `run_onbuild()`,
    and ``write`` & ``onbuild`` method callables have been replaced with
    ``template_fields`` arguments

  - Added a `get_template_fields_from_distribution()` function for use by
    callers of `run_onbuild()`

- `Versioningit.get_version()` now takes optional ``write`` and ``fallback``
  arguments

- The ``onbuild`` step is no longer run when building from an sdist; the
  configuration therefore no longer needs to be idempotent

- Drop setuptools runtime dependency

  - setuptools is only needed for `get_cmdclasses()`, which should only be
    called in an environment where setuptools is already installed.

- Prevent log messages from being printed twice under recent versions of
  setuptools

- Values supplied for the ``require-match`` parameters of the ``tag2version``
  and ``onbuild`` steps must now actually be booleans; previously, values of
  any type were accepted and were converted to booleans.

- Added a `Versioningit.run()` method that returns a structure containing all
  intermediate & final values

- "git" method: ``{author_date}`` and ``{committer_date}`` are no longer
  "clamped" to less than or equal to ``{build_date}``.  This undocumented
  behavior was based on a misinterpretation of the :envvar:`SOURCE_DATE_EPOCH`
  spec, and was even applied when :envvar:`SOURCE_DATE_EPOCH` was not set.

- When resolving entry points, if multiple entry points with the given group &
  name are found, error instead of using the first one returned


v1.1.2 (2022-08-12)
-------------------
- Backport "Don't run the ``onbuild`` step under setuptools' upcoming PEP 660
  editable mode" from v2.0.1 (contributed by `@abravalheri
  <https://github.com/abravalheri>`_)


v1.1.1 (2022-04-08)
-------------------
- Do not import setuptools unless needed (contributed by `@jenshnielsen
  <https://github.com/jenshnielsen>`_)


v1.1.0 (2022-03-03)
-------------------
- Added custom setuptools commands for inserting the project version into a
  source file at build time

  - New step and subtable: "onbuild"
  - New public `get_cmdclasses()` and `run_onbuild()` functions

- Moved documentation from the README to a Read the Docs site

  - Established external documentation for the public library API

- When falling back to using ``tool.versioningit.default-version``, emit a
  warning if the version is not PEP 440-compliant.

- The ``versioningit`` command now honors the :envvar:`VERSIONINGIT_LOG_LEVEL`
  environment variable


v1.0.0 (2022-02-06)
-------------------
- Changes to custom methods:

  - The signatures of the method functions have changed; user-supplied
    parameters are now passed as a single ``params: Dict[str, Any]`` argument
    instead of as keyword arguments.
  - User-supplied parameters with the same names as step-specific method
    arguments are no longer discarded.

- Changes to the "git-archive" method:

  - Lightweight tags are now ignored (by default, but see below) when
    installing from a repository in order to match the behavior of the
    ``%(describe)`` format placeholder.
  - The "match" and "exclude" settings are now parsed from the
    ``describe-subst`` parameter, which is now required, and the old ``match``
    and ``exclude`` parameters are now ignored.
  - Git 2.35's "tags" option for honoring lightweight tags is now recognized.
  - Added a dedicated error message when an invalid ``%(describe)`` placeholder
    is "expanded" into itself in an archive

- The ``file`` parameter to the "basic" write method is now required when the
  ``[tool.versioningit.write]`` table is present.  If you don't want to write
  the version to a file, omit the table entirely.

- Library API:

  - ``Config`` is no longer exported; it should now be considered private.
  - Merged ``Versioningit.from_config()`` functionality into
    `Versioningit.from_project_dir()`
  - Renamed ``Versioningit.from_config_obj()`` to
    ``Versioningit.from_config()``; it should now be considered private


v0.3.3 (2022-02-04)
-------------------
- Git 1.8.0 is now the minimum required version for the git methods, and this
  is documented.  (Previously, the undocumented minimum version was Git 1.8.5.)
- Document the minimum supported Mercurial version as 5.2.


v0.3.2 (2022-01-16)
-------------------
- Call `importlib.metadata.entry_points()` only once and reuse the result for
  a speedup (contributed by `@jenshnielsen <https://github.com/jenshnielsen>`_)


v0.3.1 (2022-01-02)
-------------------
- Support Python 3.10
- Support tomli 2.0


v0.3.0 (2021-09-27)
-------------------
- Gave the CLI interface an ``-n``/``--next-version`` option for showing a
  project's next release version
- Added a `get_next_version()` function
- Added a mention to the README of the existence of exported functionality
  other than `get_version()`
- Renamed the individual step-calling methods of `Versioningit` to have names
  of the form ``do_$STEP()``


v0.2.1 (2021-08-02)
-------------------
- Update for tomli 1.2.0


v0.2.0 (2021-07-13)
-------------------
- The log messages displayed for unknown parameters are now at WARNING level
  instead of INFO and include suggestions for what you might have meant
- "git" ``vcs`` method: ``default-tag`` will now be honored if the
  :program:`git describe` command fails (which generally only happens in a
  repository without any commits)
- Added an experimental "git-archive" method for determining a version when
  installing from a Git archive
- Project directories under :file:`.git/` are no longer considered to be under
  version control
- Project directories inside Git working directories that are not themselves
  tracked by Git are no longer considered to be under version control
- Support added for installing from Mercurial repositories & archives


v0.1.0 (2021-07-08)
-------------------
- Add more logging messages
- Changed default version formats to something that doesn't use
  ``{next_version}``
- "basic" ``tag2version`` method:

  - If ``regex`` is given and it does not contain a group named "``version``,"
    the entire text matched by the regex will be used as the version
  - Added a ``require-match`` parameter for erroring if the regex does not
    match

- "basic" ``write`` method: ``encoding`` now defaults to UTF-8
- New ``next-version`` methods: ``"minor-release"``, ``"smallest-release"``, and
  ``"null"``
- Replaced ``entrypoints`` dependency with ``importlib-metadata``
- Added ``tool.versioningit.default-version`` for setting the version to use if
  an error occurs
- When building a project from a shallow clone or in a non-sdist directory
  without VCS information, display an informative error message.


v0.1.0a1 (2021-07-05)
---------------------
Alpha release
