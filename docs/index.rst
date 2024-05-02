.. module:: versioningit

=====================================================
versioningit — Versioning It with your Version In Git
=====================================================

`GitHub <https://github.com/jwodder/versioningit>`_
| `PyPI <https://pypi.org/project/versioningit/>`_
| `Documentation <https://versioningit.readthedocs.io>`_
| `Issues <https://github.com/jwodder/versioningit/issues>`_
| :doc:`Changelog <changelog>`

.. toctree::
    :hidden:

    how
    configuration
    runtime-version
    hatch
    command
    api
    writing-methods
    notes
    changelog

``versioningit`` is yet another Python packaging plugin for automatically
determining your package's version based on your version control repository's
tags.  Unlike others, it allows easy customization of the version format and
even lets you easily override the separate functions used for version
extraction & calculation.

.. rubric:: Features:

- Works with both setuptools and Hatch_

  .. _hatch: https://hatch.pypa.io

- Installed & configured through :pep:`518`'s :file:`pyproject.toml`

- Supports Git, modern Git archives, and Mercurial

- Formatting of the final version uses format template strings, with fields for
  basic VCS information and separate template strings for distanced vs. dirty
  vs. distanced-and-dirty repository states

- Can optionally write the final version and other details to a file for
  loading at runtime

- Provides custom hooks for inserting the final version and other details into
  a source file at build time

- The individual methods for VCS querying, tag-to-version calculation, version
  bumping, version formatting, and writing the version to a file can all be
  customized using either functions defined alongside one's project code or via
  publicly-distributed entry points

- Can alternatively be used as a library for use in :file:`setup.py` or the
  like, in case you don't want to or can't configure it via
  :file:`pyproject.toml`

- The only thing it does is calculate your version and optionally write it to a
  file; there's no overriding of your sdist contents based on what's in your
  Git repository, especially not without a way to turn it off, because that
  would just be rude.


Installation & Setup
====================
``versioningit`` requires Python 3.8 or higher.  Just use `pip
<https://pip.pypa.io>`_ for Python 3 (You have pip, right?) to install
``versioningit`` and its dependencies::

    python3 -m pip install versioningit

However, usually you won't need to install ``versioningit`` in your environment
directly.  Instead, you specify it in your project's :file:`pyproject.toml`
file in the ``build-system.requires`` key, like so:

.. tab:: Setuptools

    .. code:: toml

        [build-system]
        requires = [
            "setuptools",
            "versioningit",
        ]
        build-backend = "setuptools.build_meta"

.. tab:: Hatch

    .. code:: toml

        [build-system]
        requires = [
            "hatchling",
            "versioningit",
        ]
        build-backend = "hatchling.build"

        [tool.hatch.version]
        source = "versioningit"

Then, you configure ``versioningit`` by adding a ``[tool.versioningit]`` table
to your :file:`pyproject.toml`.  See ":ref:`configuration`" for details, but
you can get up & running with just the minimal configuration, an empty table:

.. code:: toml

    [tool.versioningit]

``versioningit`` eliminates the need to list an explicit version in
:file:`setup.py`, :file:`setup.cfg`, or :file:`pyproject.toml` (and any
explicit version you do list will be ignored when using ``versioningit``), so
you should remove any such settings in order to reduce confusion.

.. note::

    If you're specifying your project metadata via a ``[project]`` table in
    :file:`pyproject.toml``, you need to set ``project.dynamic = ["version"]``
    in order for ``versioningit`` to work.

Once you have a ``[tool.versioningit]`` table in your :file:`pyproject.toml` —
and once your repository has at least one tag — building your project with
build_ or similar will result in your project's version automatically being set
based on the latest tag in your Git repository.  You can test your
configuration and see what the resulting version will be using the
``versioningit`` command (see ":ref:`command`").

.. _build: https://github.com/pypa/build


Example Configurations
======================

One of ``versioningit``'s biggest strengths is its ability to configure the
version format using placeholder strings.  The default format configuration
looks like this:

.. code:: toml

    [tool.versioningit.format]

    # Format used when there have been commits since the most recent tag:
    distance = "{base_version}.post{distance}+{vcs}{rev}"
    # Example formatted version: 1.2.3.post42+ge174a1f

    # Format used when there are uncommitted changes:
    dirty = "{base_version}+d{build_date:%Y%m%d}"
    # Example formatted version: 1.2.3+d20230922

    # Format used when there are both commits and uncommitted changes:
    distance-dirty = "{base_version}.post{distance}+{vcs}{rev}.d{build_date:%Y%m%d}"
    # Example formatted version: 1.2.3.post42+ge174a1f.d20230922

Other format configurations of interest include:

- The default format used by setuptools_scm_:

  .. code:: toml

      [tool.versioningit.next-version]
      method = "smallest"

      [tool.versioningit.format]
      distance = "{next_version}.dev{distance}+{vcs}{rev}"
      # Example formatted version: 1.2.4.dev42+ge174a1f

      dirty = "{base_version}+d{build_date:%Y%m%d}"
      # Example formatted version: 1.2.3+d20230922

      distance-dirty = "{next_version}.dev{distance}+{vcs}{rev}.d{build_date:%Y%m%d}"
      # Example formatted version: 1.2.4.dev42+ge174a1f.d20230922

- The format used by versioneer_:

  .. code:: toml

      [tool.versioningit.format]
      distance = "{base_version}+{distance}.{vcs}{rev}"
      # Example formatted version: 1.2.3+42.ge174a1f

      dirty = "{base_version}+{distance}.{vcs}{rev}.dirty"
      # Example formatted version: 1.2.3+42.ge174a1f.dirty

      distance-dirty = "{base_version}+{distance}.{vcs}{rev}.dirty"
      # Example formatted version: 1.2.3+42.ge174a1f.dirty

- The format used by vcversioner_:

  .. code:: toml

      [tool.versioningit.format]
      distance = "{base_version}.post{distance}"
      # Example formatted version: 1.2.3.post42

      dirty = "{base_version}"
      # Example formatted version: 1.2.3

      distance-dirty = "{base_version}.post{distance}"
      # Example formatted version: 1.2.3.post42

.. _setuptools_scm: https://github.com/pypa/setuptools_scm
.. _versioneer: https://github.com/python-versioneer/python-versioneer
.. _vcversioner: https://github.com/habnabit/vcversioner


Indices and Tables
==================
* :ref:`genindex`
* :ref:`search`
