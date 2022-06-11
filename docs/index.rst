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
    command
    api
    writing-methods
    notes
    changelog

``versioningit`` is yet another setuptools plugin for automatically determining
your package's version based on your version control repository's tags.  Unlike
others, it allows easy customization of the version format and even lets you
easily override the separate functions used for version extraction &
calculation.

.. rubric:: Features:

- Installed & configured through :pep:`518`'s :file:`pyproject.toml`

- Supports Git, modern Git archives, and Mercurial

- Formatting of the final version uses format template strings, with fields for
  basic VCS information and separate template strings for distanced vs. dirty
  vs. distanced-and-dirty repository states

- Can optionally write the final version and other details to a file for
  loading at runtime

- Provides custom setuptools commands for inserting the final version and other
  details into a source file at build time

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
``versioningit`` requires Python 3.6 or higher.  Just use `pip
<https://pip.pypa.io>`_ for Python 3 (You have pip, right?) to install
``versioningit`` and its dependencies::

    python3 -m pip install versioningit

However, usually you won't need to install ``versioningit`` in your environment
directly.  Instead, you specify it in your project's :file:`pyproject.toml`
file in the ``build-system.requires`` key, like so:

.. code:: toml

    [build-system]
    requires = [
        "setuptools >= 42",  # At least v42 of setuptools required!
        "versioningit ~= 1.0",
        "wheel"
    ]
    build-backend = "setuptools.build_meta"

Then, you configure ``versioningit`` by adding a ``[tool.versioningit]`` table
to your :file:`pyproject.toml`.  See ":ref:`configuration`" for details, but
you can get up & running with just the minimal configuration, an empty table:

.. code:: toml

    [tool.versioningit]

``versioningit`` replaces the need for (and will overwrite) the ``version``
keyword to the `setup()` function, so you should remove any such keyword from
your :file:`setup.py`/:file:`setup.cfg` to reduce confusion.

.. note::

    If you're using setuptools' recent support for specifying project metadata
    in :file:`pyproject.toml`, you need to omit the ``project.version`` key and
    set ``project.dynamic = ["version"]`` in order for ``versioningit`` to
    work.

Once you have a ``[tool.versioningit]`` table in your :file:`pyproject.toml` —
and once your repository has at least one tag — building your project with
``setuptools`` while ``versioningit`` is installed (which happens automatically
if you set up your ``build-system.requires`` as above and you're using a
:pep:`517` frontend like build_) will result in your project's version
automatically being set based on the latest tag in your Git repository.  You
can test your configuration and see what the resulting version will be using
the ``versioningit`` command (see ":ref:`command`").

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

    # Format used when there are uncommitted changes:
    dirty = "{base_version}+d{build_date:%Y%m%d}"

    # Format used when there are both commits and uncommitted changes:
    distance-dirty = "{base_version}.post{distance}+{vcs}{rev}.d{build_date:%Y%m%d}"

Other format configurations of interest include:

- The default format used by setuptools_scm_:

  .. code:: toml

      [tool.versioningit.next-version]
      method = "smallest"

      [tool.versioningit.format]
      distance = "{next_version}.dev{distance}+{vcs}{rev}"
      dirty = "{base_version}+d{build_date:%Y%m%d}"
      distance-dirty = "{next_version}.dev{distance}+{vcs}{rev}.d{build_date:%Y%m%d}"

- The format used by versioneer_:

  .. code:: toml

      [tool.versioningit.format]
      distance = "{base_version}+{distance}.{vcs}{rev}"
      dirty = "{base_version}+{distance}.{vcs}{rev}.dirty"
      distance-dirty = "{base_version}+{distance}.{vcs}{rev}.dirty"

- The format used by vcversioner_:

  .. code:: toml

      [tool.versioningit.format]
      distance = "{base_version}.post{distance}"
      dirty = "{base_version}"
      distance-dirty = "{base_version}.post{distance}"

.. _setuptools_scm: https://github.com/pypa/setuptools_scm
.. _versioneer: https://github.com/python-versioneer/python-versioneer
.. _vcversioner: https://github.com/habnabit/vcversioner


Indices and Tables
==================
* :ref:`genindex`
* :ref:`search`
