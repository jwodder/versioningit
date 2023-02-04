.. currentmodule:: versioningit

Library API
===========

High-Level Functions
--------------------

.. autofunction:: get_version
.. autofunction:: get_next_version
.. autofunction:: get_cmdclasses

.. class:: versioningit.cmdclass.sdist

    .. versionadded:: 2.2.0

    A custom subclass of `setuptools.command.sdist.sdist` that runs the
    ``onbuild`` step when building an sdist.  This class is equivalent to
    ``get_cmdclasses()["sdist"]``, except that it can also be used in the
    ``[options]cmdclass`` field in :file:`setup.cfg`.

.. class:: versioningit.cmdclass.build_py

    .. versionadded:: 2.2.0

    A custom subclass of `setuptools.command.build_py.build_py` that runs the
    ``onbuild`` step when building a wheel.  This class is equivalent to
    ``get_cmdclasses()["build_py"]``, except that it can also be used in the
    ``[options]cmdclass`` field in :file:`setup.cfg`.

.. note::

    When importing or referring to the ``sdist`` and ``build_py`` command
    classes, the ``.cmdclass`` submodule needs to be specified; unlike the rest
    of the library API, they are not importable directly from ``versioningit``.

    .. code:: ini

        [options]
        cmdclass =
            # Right!
            sdist = versioningit.cmdclass.sdist
            build_py = versioningit.cmdclass.build_py

        [options]
        cmdclass =
            # Wrong!
            sdist = versioningit.sdist
            build_py = versioningit.build_py


Low-Level Class
---------------

.. autoclass:: Versioningit()
    :member-order: bysource

Exceptions
----------

.. autoexception:: Error
.. autoexception:: ConfigError
    :show-inheritance:
.. autoexception:: InvalidTagError
    :show-inheritance:
.. autoexception:: InvalidVersionError
    :show-inheritance:
.. autoexception:: MethodError
    :show-inheritance:
.. autoexception:: NoTagError
    :show-inheritance:
.. autoexception:: NotSdistError
    :show-inheritance:
.. autoexception:: NotVCSError
    :show-inheritance:
.. autoexception:: NotVersioningitError
    :show-inheritance:

Utilities
---------

.. autoclass:: VCSDescription
.. autoclass:: Report
.. autoclass:: FallbackReport
.. autofunction:: get_version_from_pkg_info
.. autofunction:: run_onbuild
.. autofunction:: get_template_fields_from_distribution

.. _config_dict:

Passing Explicit Configuration
------------------------------

The functions & methods that take a path to a project directory normally read
the project's configuration from the :file:`pyproject.toml` file therein, but
they can also be passed a ``config`` argument to take the configuration from
instead, in which case :file:`pyproject.toml` will be ignored and need not even
exist.

A ``config`` argument must be a `dict` whose structure mirrors the structure of
the ``[tool.versioningit]`` table in :file:`pyproject.toml`.  For example, the
following TOML configuration:

.. code:: toml

    [tool.versioningit.vcs]
    method = "git"
    match = ["v*"]

    [tool.versioningit.next-version]
    method = { module = "setup", value = "my_next_version" }

    [tool.versioningit.format]
    distance = "{next_version}.dev{distance}+{vcs}{rev}"
    dirty = "{base_version}+dirty"
    distance-dirty = "{next_version}.dev{distance}+{vcs}{rev}.dirty"

corresponds to the following Python ``config`` value:

.. code:: python

    {
        "vcs": {
            "method": "git",
            "match": ["v*"],
        },
        "next-version": {
            "method": {
                "module": "setup",
                "value": "my_next_version",
            },
        },
        "format": {
            "distance": "{next_version}.dev{distance}+{vcs}{rev}",
            "dirty": "{base_version}+dirty",
            "distance-dirty": "{next_version}.dev{distance}+{vcs}{rev}.dirty",
        },
    }

This is the same structure that you would get by reading from the
:file:`pyproject.toml` file like so:

.. code:: python

    import tomli

    with open("pyproject.toml", "rb") as fp:
        config = tomli.load(fp)["tool"]["versioningit"]

When passing ``versioningit`` configuration as a ``config`` argument, an
alternative way to specify methods becomes available: in place of a method
specification, one can pass a callable object directly.
