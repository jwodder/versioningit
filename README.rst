.. image:: http://www.repostatus.org/badges/latest/active.svg
    :target: http://www.repostatus.org/#active
    :alt: Project Status: Active — The project has reached a stable, usable
          state and is being actively developed.

.. image:: https://github.com/jwodder/versioningit/workflows/Test/badge.svg?branch=master
    :target: https://github.com/jwodder/versioningit/actions?workflow=Test
    :alt: CI Status

.. image:: https://codecov.io/gh/jwodder/versioningit/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/jwodder/versioningit

.. image:: https://img.shields.io/pypi/pyversions/versioningit.svg
    :target: https://pypi.org/project/versioningit/

.. image:: https://img.shields.io/github/license/jwodder/versioningit.svg
    :target: https://opensource.org/licenses/MIT
    :alt: MIT License

`GitHub <https://github.com/jwodder/versioningit>`_
| `PyPI <https://pypi.org/project/versioningit/>`_
| `Documentation <https://versioningit.readthedocs.io>`_
| `Issues <https://github.com/jwodder/versioningit/issues>`_
| `Changelog <https://github.com/jwodder/versioningit/blob/master/CHANGELOG.md>`_

``versioningit`` — *Versioning It with your Version In Git*

``versioningit`` is yet another setuptools plugin for automatically determining
your package's version based on your version control repository's tags.  Unlike
others, it allows easy customization of the version format and even lets you
easily override the separate functions used for version extraction &
calculation.

**Features:**

- Installed & configured through :pep:`518`'s ``pyproject.toml``

- Supports Git, modern Git archives, and Mercurial

- Formatting of the final version uses format template strings, with fields for
  basic VCS information and separate template strings for distanced vs. dirty
  vs. distanced-and-dirty repository states

- Can optionally write the final version to a file for loading at runtime

- Provides custom setuptools commands for inserting the final version into a
  source file at build time

- The individual methods for VCS querying, tag-to-version calculation, version
  bumping, version formatting, and writing the version to a file can all be
  customized using either functions defined alongside one's project code or via
  publicly-distributed entry points

- Can alternatively be used as a library for use in ``setup.py`` or the like,
  in case you don't want to or can't configure it via ``pyproject.toml``

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
directly.  Instead, you specify it in your project's ``pyproject.toml`` file in
the ``build-system.requires`` key, like so:

.. code:: toml

    [build-system]
    requires = [
        "setuptools >= 42",  # At least v42 of setuptools required!
        "versioningit ~= 1.0",
        "wheel"
    ]
    build-backend = "setuptools.build_meta"

Then, you configure ``versioningit`` by adding a ``[tool.versioningit]`` table
to your ``pyproject.toml``.  See `the documentation`__ for details, but you
can get up & running with just the minimal configuration, an empty table:

__ https://versioningit.readthedocs.io/en/stable/configuration.html

.. code:: toml

    [tool.versioningit]

``versioningit`` replaces the need for (and will overwrite) the ``version``
keyword to the ``setup()`` function, so you should remove any such keyword from
your ``setup.py``/``setup.cfg`` to reduce confusion.

Once you have a ``[tool.versioningit]`` table in your ``pyproject.toml`` — and
once your repository has at least one tag — building your project with
``setuptools`` while ``versioningit`` is installed (which happens automatically
if you set up your ``build-system.requires`` as above and you're using a
:pep:`517` frontend like build_) will result in your project's version
automatically being set based on the latest tag in your Git repository.  You
can test your configuration and see what the resulting version will be using
the ``versioningit`` command (`see the documentation`__).

.. _build: https://github.com/pypa/build

__ https://versioningit.readthedocs.io/en/stable/command.html


Example Configurations
======================

One of ``versioningit``'s biggest strengths is its ability to configure the
version format using placeholder strings.  The default format configuration
looks like this:

.. code:: toml

    [tool.versioningit.format]

    # Format used when there have been commits since the most recent tag:
    distance = "{version}.post{distance}+{vcs}{rev}"

    # Format used when there are uncommitted changes:
    dirty = "{version}+d{build_date:%Y%m%d}"

    # Format used when there are both commits and uncommitted changes:
    distance-dirty = "{version}.post{distance}+{vcs}{rev}.d{build_date:%Y%m%d}"

Other format configurations of interest include:

- The default format used by setuptools_scm_:

  .. code:: toml

      [tool.versioningit.next-version]
      method = "smallest"

      [tool.versioningit.format]
      distance = "{next_version}.dev{distance}+{vcs}{rev}"
      dirty = "{version}+d{build_date:%Y%m%d}"
      distance-dirty = "{next_version}.dev{distance}+{vcs}{rev}.d{build_date:%Y%m%d}"

- The format used by versioneer_:

  .. code:: toml

      [tool.versioningit.format]
      distance = "{version}+{distance}.{vcs}{rev}"
      dirty = "{version}+{distance}.{vcs}{rev}.dirty"
      distance-dirty = "{version}+{distance}.{vcs}{rev}.dirty"

- The format used by vcversioner_:

  .. code:: toml

      [tool.versioningit.format]
      distance = "{version}.post{distance}"
      dirty = "{version}"
      distance-dirty = "{version}.post{distance}"

.. _setuptools_scm: https://github.com/pypa/setuptools_scm
.. _versioneer: https://github.com/python-versioneer/python-versioneer
.. _vcversioner: https://github.com/habnabit/vcversioner
