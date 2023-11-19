Hatch Integration
=================

.. versionadded:: 2.3.0

If you're not a setuptools user, ``versioningit`` can also be used as a version
source plugin for the Hatch_ build backend.  You use it in pretty much the same
way as for setuptools:

.. _Hatch: https://hatch.pypa.io

- Include ``versioningit`` in your build requirements like so:

    .. code:: toml

        [build-system]
        requires = ["hatchling", "versioningit"]
        build-backend = "hatchling.build"

- Tell Hatch that you're using a dynamic version source by including
  ``"version"`` in the ``project.dynamic`` key:

    .. code:: toml

        [project]
        name = "your-project-name"
        dynamic = ["version"]
        # The rest of your project metadata follows after.

        # Do not set the `version` key in [project].  If it's currently set,
        # remove it.

- Tell Hatch to use ``versioningit`` as the version source:

    .. code:: toml

        [tool.hatch.version]
        source = "versioningit"

- Configure ``versioningit`` as normal.  However, with Hatch, you have two
  possible locations to put ``versioningit``'s configuration in: either a
  ``[tool.versioningit]`` table as used with setuptools or under the
  ``[tool.hatch.version]`` table.  Moreover, unlike when using setuptools, you
  don't even need the ``[tool.versioningit]`` table if it's just going to be
  empty.

  For example, the following configurations are equivalent:

    - Using ``[tool.versioningit]``:

        .. code:: toml

            [tool.hatch.version]
            source = "versioningit"

            [tool.versioningit]
            default-version = "0.0.0+unknown"

            [tool.versioningit.format]
            distance = "{next_version}.dev{distance}+{vcs}{rev}"
            dirty = "{version}+dirty"
            distance-dirty = "{next_version}.dev{distance}+{vcs}{rev}.dirty"

    - Using ``[tool.hatch.version]``:

        .. code:: toml

            [tool.hatch.version]
            source = "versioningit"
            default-version = "0.0.0+unknown"

            [tool.hatch.version.format]
            distance = "{next_version}.dev{distance}+{vcs}{rev}"
            dirty = "{version}+dirty"
            distance-dirty = "{next_version}.dev{distance}+{vcs}{rev}.dirty"

    If you configure ``versioningit`` via ``[tool.hatch.version]`` and also
    define a ``[tool.versioningit]`` table (even if it's empty), a warning will
    be emitted, and only the ``[tool.hatch.version]`` configuration will be
    used.

- If you use the ``write`` step to create a file containing your project
  version, and this file is listed in your :file:`.gitignore` or
  :file:`.hgignore`, you will need to tell Hatch to include the file in sdists
  & wheels like so:

    .. code:: toml

        [tool.hatch.build]
        # Replace the path below with the path to the file created by the
        # `write` step:
        artifacts = ["src/mypackage/_version.py"]

.. attention::

    Currently, :ref:`the onbuild step <onbuild>` is not supported when using
    ``versioningit`` with Hatch.  See `issue #54`__ for more information.

    __ https://github.com/jwodder/versioningit/issues/54

.. note::

    If you use ``versioningit`` with Hatch, you will not be able to set your
    project's version by running ``hatch version x.y.z``.  Just create a tag
    instead!
