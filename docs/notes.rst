Restrictions & Caveats
======================

- When building or installing a project that uses ``versioningit``, the entire
  repository history (or at least everything back through the most recent tag)
  must be available.  This means that installing from a shallow clone (the
  default on most CI systems) will not work.  If you are using the ``"git"`` or
  ``"git-archive"`` ``vcs`` method and have ``default-tag`` set in
  ``[tool.versioningit.vcs]``, then shallow clones will end up assigned the
  default tag, which may or may not be what you want.

- If using the ``[tool.versioningit.write]`` subtable to write the version to a
  file, this file will only be updated whenever the project is built or
  installed.  If using editable installs, this means that you must re-run
  ``python setup.py develop`` or ``pip install -e .`` after each
  commit if you want the version to be up-to-date.

- If you define & use a custom method inside your Python project's package, you
  will not be able to retrieve your project version by calling
  `importlib.metadata.version()` inside :file:`__init__.py` — at least, not
  without a ``try: ... except ...`` wrapper.  This is because ``versioningit``
  loads the package containing the custom method before the package is
  installed, but `importlib.metadata.version()` only works after the package is
  installed.

- If you generate a conda package from your sdist (e.g., for a conda-forge
  feedstock), you will likely want to include ``versioningit`` as a ``host``
  dependency in your conda ``meta.yaml`` file.  This is needed for the package
  produced from your sdist to contain the correct version number in its
  ``dist-info``.
