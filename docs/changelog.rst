.. currentmodule:: versioningit

Changelog
=========

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
