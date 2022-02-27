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

.. contents::
    :backlinks: top


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
to your ``pyproject.toml``.  See "Configuration_" below for details, but you
can get up & running with just the minimal configuration, an empty table:

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
the ``versioningit`` command (`see below <Command_>`_).

.. _build: https://github.com/pypa/build


Configuration
=============

The ``[tool.versioningit]`` table in ``pyproject.toml`` is divided into five
subtables, each describing how one of the five steps of the version extraction
& calculation should be carried out.  Each subtable consists of an optional
``method`` key specifying the *method* (entry point or function) that should be
used to carry out that step, plus zero or more extra keys that will be passed
as parameters to the method when it's called.  If the ``method`` key is
omitted, the default method for the step is used.

Specifying the Method
---------------------

A method can be specified in two different ways, depending on where it's
implemented.  A method that is built in to ``versioningit`` or provided by an
installed third-party extension is specified by giving its name as a string,
e.g.:

.. code:: toml

    [tool.versioningit.vcs]
    # The method key:
    method = "git"  # <- The method name

    # Parameters to pass to the method:
    match = ["v*"]
    default-tag = "1.0.0"

Alternatively, a method can be implemented as a function in a Python source
file in your project directory (either part of the main Python package or in an
auxiliary file); see "`Writing Your Own Methods`_" below for more information.
To tell ``versioningit`` to use such a method, set the ``method`` key to a
table with a ``module`` key giving the dotted name of the module in which the
method is defined and a ``value`` key giving the name of the callable object in
the module that implements the method.  For example, if you created a custom
``next-version`` method that's named ``my_next_version()`` and is located in
``mypackage/mymodule.py``, you would write:

.. code:: toml

    [tool.versioningit.next-version]
    method = { module = "mypackage.module", value = "my_next_version" }
    # Put any parameters here

Note that this assumes that ``mypackage/`` is located at the root of the
project directory (i.e., the directory containing the ``pyproject.toml`` file);
if is located inside another directory, like ``src/``, you will need to add a
``module-dir`` key to the method table giving the path to that directory
relative to the project root, like so:

.. code:: toml

    [tool.versioningit.next-version]
    method = { module = "mypackage.module", value = "my_next_version", module-dir = "src" }
    # Put any parameters here

As a special case, if there are no parameters for a given step, the respective
subtable can be replaced by the method specification, e.g.:

.. code:: toml

    [tool.versioningit]
    # Use the "git" method for the vcs step with no parameters:
    vcs = "git"
    # Use a custom function for the next-version step with no parameters:
    next-version = { module = "mypackage.module", value = "my_next_version" }


The ``[tool.versioningit.vcs]`` Subtable
----------------------------------------

The ``vcs`` subtable specifies the version control system used by the project
and how to extract the tag and related information from it.  ``versioningit``
provides three ``vcs`` methods: ``"git"`` (the default), ``"git-archive"``, and
``"hg"``.

``"git"``
~~~~~~~~~

The ``"git"`` method relies on the project directory being located inside a Git
repository with one or more commits.  Git 1.8.0 or higher must be installed,
though some optional features require more recent Git versions.

The ``"git"`` method takes the following parameters, all optional:

``match`` : list of strings
    A set of fileglob patterns to pass to the ``--match`` option of ``git
    describe`` to make Git only consider tags matching the given pattern(s).
    Defaults to an empty list.

    **Note:** Specifying more than one match pattern requires Git 2.13.0 or
    higher.

``exclude`` : list of strings
    A set of fileglob patterns to pass to the ``--exclude`` option of ``git
    describe`` to make Git not consider tags matching the given pattern(s).
    Defaults to an empty list.

    **Note:** This option requires Git 2.13.0 or higher.

``default-tag`` : string
    If ``git describe`` cannot find a tag, ``versioningit`` will raise a
    ``versioningit.errors.NoTagError`` unless ``default-tag`` is set, in which
    case it will act as though the initial commit is tagged with the value of
    ``default-tag``

``"git-archive"``
~~~~~~~~~~~~~~~~~

*New in version 0.2.0*

**This method is experimental and may change in future releases.**

The ``"git-archive"`` method is a variation of the ``"git"`` method that also
supports determining the version when installing from a properly-prepared Git
archive.  The method takes the following parameters:

``describe-subst`` : string
    *(required)* Set this to ``"$Format:%(describe)$"`` and add the line
    ``pyproject.toml export-subst`` to your repository's ``.gitattributes``
    file.  This will cause any Git archive made from your repository from this
    point forward to contain the minimum necessary information to determine a
    version.

    ``match`` and ``exclude`` options are set by including them in the format
    placeholder like so:

    .. code:: toml

        # Match 'v*' tags:
        describe-subst = "$Format:%(describe:match=v*)$"

        # Match 'v*' and 'r*' tags:
        describe-subst = "$Format:%(describe:match=v*,match=r*)$"

        # Match 'v*' tags, exclude '*-final' tags:
        describe-subst = "$Format:%(describe:match=v*,exclude=*-final)$"

    By default, only annotated tags are considered, and lightweight tags are
    ignored; this can be changed by including the "tags" option in the
    placeholder like so:

    .. code:: toml

        # Honor all tags:
        describe-subst = "$Format:%(describe:tags)$"

        # Honor all tags, exclude '*rc' tags:
        describe-subst = "$Format:%(describe:tags,exclude=*rc)$"

    Options other than "match", "exclude", and "tags" are not supported by
    ``versioningit`` and will result in an error.

``default-tag`` : string
    *(optional)* If ``git describe`` cannot find a tag, ``versioningit`` will
    raise a ``versioningit.errors.NoTagError`` unless ``default-tag`` is set,
    in which case it will act as though the initial commit is tagged with the
    value of ``default-tag``.

    Note that this parameter has no effect when installing from a Git archive;
    if the repository that the archive was produced from had no relevant tags
    for the archived commit (causing the value of ``describe-subst`` to be set
    to the empty string), ``versioningit`` will raise an error when trying to
    install the archive.

Note that, in order to provide a consistent set of information regardless of
whether installing from a repository or an archive, the ``"git-archive"``
method provides the ``format`` step with only a subset of the fields that the
``"git"`` method does; `see below <format-fields_>`_ for more information.

*Changed in version 1.0.0:* The "match" and "exclude" settings are now parsed
from the ``describe-subst`` parameter, which is now required, and the old
``match`` and ``exclude`` parameters are now ignored.  Also, support for the
"tags" option was added.

**A note on Git version requirements:**

- The ``%(describe)s`` placeholder was only added to Git in version 2.32.0, and
  so a Git repository archive must be created using at least that version in
  order to be installable with this method.  Fortunately, GitHub repository ZIP
  downloads support ``%(describe)``, and so ``pip``-installing a
  "git-archive"-using project from a URL of the form
  ``https://github.com/$OWNER/$REPO/archive/$BRANCH.zip`` will work.

- The ``%(describe)s`` placeholder only gained support for the "tags" option in
  Git 2.35.0, and so, if this option is included in the ``describe-subst``
  parameter, that Git version or higher will be required when creating a
  repository archive in order for the result to be installable.  Unfortunately,
  as of 2022-02-05, GitHub repository Zips do not support this option.

- When installing from a Git repository rather than an archive, the
  "git-archive" method parses the ``describe-subst`` parameter into the
  equivalent ``git describe`` options, so a bleeding-edge Git is not required
  in that situation (but see the version requirements for the "git" method
  above).

**Note:** In order to avoid DOS attacks, Git will not expand more than one
``%(describe)s`` placeholder per archive, and so you should not have any other
``$Format:%(describe)$`` placeholders in your repository.

**Note:** This method will not work correctly if you have a tag that resembles
``git describe`` output, i.e., that is of the form
``<anything>-<number>-g<hex-chars>``.  So don't do that.

``"hg"``
~~~~~~~~

*New in version 0.2.0*

The ``"hg"`` method supports installing from a Mercurial repository or archive.
When installing from a repository, Mercurial 5.2 or higher must be installed.

The ``"hg"`` method takes the following parameters, all optional:

``pattern`` : string
    A revision pattern (See ``hg help revisions.patterns``) to pass to the
    ``latesttag()`` template function.  Note that this parameter has no effect
    when installing from a Mercurial archive.

``default-tag`` : string
    If there is no latest tag, ``versioningit`` will raise a
    ``versioningit.errors.NoTagError`` unless ``default-tag`` is set, in which
    case it will act as though the initial commit is tagged with the value of
    ``default-tag``


The ``[tool.versioningit.tag2version]`` Subtable
------------------------------------------------

The ``tag2version`` subtable specifies how to extract the version from the tag
found by the ``vcs`` step.  ``versioningit`` provides one ``tag2version``
method, ``"basic"`` (the default), which proceeds as follows:

- If the ``rmprefix`` parameter is set to a string and the tag begins with that
  string, the given string is removed from the tag.

- If the ``rmsuffix`` parameter is set to a string and the tag ends with that
  string, the given string is removed from the tag.

- If the ``regex`` parameter is set to a string (a Python regex) and the regex
  matches the tag (using ``re.search()``), the tag is replaced with the
  contents of the capturing group named "``version``", or the entire matched
  text if there is no group by that name.  If the regex does not match the tag,
  the behavior depends on the ``require-match`` parameter: if true, an error is
  raised; if false or unset, the tag is left as-is.

- Finally, any remaining leading ``v``'s are removed from the tag.

A warning is emitted if the resulting version is not :pep:`440`-compliant.


The ``[tool.versioningit.next-version]`` Subtable
-------------------------------------------------

The ``next-version`` subtable specifies how to calculate the next release
version from the version extracted from the VCS tag.  ``versioningit`` provides
the following ``next-version`` methods; none of them take any parameters.

``minor``
    *(default)* Strips the input version down to just the epoch segment (if
    any) and release segment (i.e., the ``N(.N)*`` bit), increments the second
    component of the release segment, and replaces the following components
    with a single zero.  For example, if the version extracted from the VCS tag
    is ``1.2.3.4``, the ``"minor"`` method will calculate a new version of
    ``1.3.0``.

``minor-release``
    Like ``minor``, except that if the input version is a prerelease or
    development release, the base version is returned; e.g., ``1.2.3a0``
    becomes ``1.2.3``.  This method requires the input version to be
    :pep:`440`-compliant.

``smallest``
    Like ``minor``, except that it increments the last component of the release
    segment.  For example, if the version extracted from the VCS tag is
    ``1.2.3.4``, the ``"smallest"`` method will calculate a new version of
    ``1.2.3.5``.

``smallest-release``
    Like ``smallest``, except that if the input version is a prerelease or
    development release, the base version is returned; e.g., ``1.2.3a0``
    becomes ``1.2.3``.  This method requires the input version to be
    :pep:`440`-compliant.

``null``
    Returns the input version unchanged.  Useful if your repo version is
    something horrible and unparseable.

A warning is emitted if the resulting version is not :pep:`440`-compliant.


The ``[tool.versioningit.format]`` Subtable
-------------------------------------------

The ``format`` subtable specifies how to format the project's final version
based on the information calculated in previous steps.  (Note that, if the
repository's current state is an exact tag match, this step will be skipped and
the version returned by the ``tag2version`` step will be used as the final
version.)  ``versioningit`` provides one ``format`` method, ``"basic"`` (the
default).

The data returned by the ``vcs`` step includes a repository *state* (describing
the relationship of the repository's current contents to the most recent tag)
and a collection of *format fields*.  The ``"basic"`` ``format`` method takes
the name of that state, looks up the ``format`` parameter with the same name
(falling back to a default, given below) to get a `format template string`_,
and formats the template using the given format fields plus ``{version}``,
``{next_version}``, and ``{branch}`` fields.  A warning is emitted if the
resulting version is not :pep:`440`-compliant.

.. _format template string: https://docs.python.org/3/library/string.html
                            #format-string-syntax

For the built-in ``vcs`` methods, the repository states are:

==================  ===========================================================
``distance``        One or more commits have been made on the current branch
                    since the latest tag
``dirty``           No commits have been made on the branch since the latest
                    tag, but the repository has uncommitted changes
``distance-dirty``  One or more commits have been made on the branch since the
                    latest tag, and the repository has uncommitted changes
==================  ===========================================================

.. _format-fields:

For the built-in ``vcs`` methods, the available format fields are:

====================  =========================================================
``{author_date}``     The author date of the HEAD commit [#dt]_ (``"git"``
                      only)
``{branch}``          The name of the current branch (with non-alphanumeric
                      characters converted to periods), or ``None`` if the
                      branch cannot be determined
``{build_date}``      The current date & time, or the date & time specified by
                      the environment variable ``SOURCE_DATE_EPOCH`` if it is
                      set [#dt]_
``{committer_date}``  The committer date of the HEAD commit [#dt]_ (``"git"``
                      only)
``{distance}``        The number of commits since the most recent tag
``{next_version}``    The next release version, calculated by the
                      ``next-version`` step
``{rev}``             The abbreviated hash of the HEAD commit
``{revision}``        The full hash of the HEAD commit (``"git"`` and ``"hg``"
                      only)
``{vcs}``             The first letter of the name of the VCS (i.e., "``g``" or
                      "``h``")
``{vcs_name}``        The name of the VCS (i.e., "``git``" or "``hg``")
``{version}``         The version extracted from the most recent tag
====================  =========================================================

.. [#dt] These fields are UTC ``datetime.datetime`` objects.  They are
   formatted with ``strftime()`` formats by writing ``{fieldname:format}``,
   e.g., ``{build_date:%Y%m%d}``.

The default parameters for the ``format`` step are:

.. code:: toml

    [tool.versioningit.format]
    distance = "{version}.post{distance}+{vcs}{rev}"
    dirty = "{version}+d{build_date:%Y%m%d}"
    distance-dirty = "{version}.post{distance}+{vcs}{rev}.d{build_date:%Y%m%d}"

Other sets of ``format`` parameters of interest include:

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


The ``[tool.versioningit.write]`` Subtable
------------------------------------------

The ``write`` subtable enables an optional feature, writing the final version
to a file.  Unlike the other subtables, if the ``write`` subtable is omitted,
the corresponding step will not be carried out.

``versioningit`` provides one ``write`` method, ``"basic"`` (the default),
which takes the following parameters:

``file`` : string
    *(required)* The path to the file to which to write the version.  This path
    should use forward slashes (``/``) as the path separator, even on Windows.

    **Note:** This file should not be committed to version control, but it
    should be included in your project's built sdists and wheels.

``encoding`` : string
    *(optional)* The encoding with which to write the file.  Defaults to UTF-8.

``template``: string
    *(optional)* The content to write to the file (minus the final newline,
    which ``versioningit`` adds automatically), as a string containing a
    ``{version}`` placeholder.  If this parameter is omitted, the default is
    determined based on the ``file`` parameter's file extension.  For ``.txt``
    files and files without an extension, the default is::

        {version}

    while for ``.py`` files, the default is::

        __version__ = "{version}"

    If ``template`` is omitted and ``file`` has any other extension, an error
    is raised.


``tool.versioningit.default-version``
-------------------------------------

The final key in the ``[tool.versioningit]`` table is ``default-version``,
which is a string rather than a subtable.  When this key is set and an error
occurs during version calculation, ``versioningit`` will set your package's
version to the given default version.  When this key is not set, any errors
that occur inside ``versioningit`` will cause the build/install process to
fail.

Note that ``default-version`` is not applied if an error occurs while parsing
the ``[tool.versioningit]`` table; however, such errors can be caught ahead of
time by running the ``versioningit`` `command <Command_>`_.


Log Level Environment Variable
------------------------------

When ``versioningit`` is invoked via the setuptools plugin interface, it logs
various information to stderr.  By default, only messages at ``WARNING`` level
or higher are displayed, but this can be changed by setting the
``VERSIONINGIT_LOG_LEVEL`` environment variable to the name of a Python
`logging level`_ (case insensitive) or the equivalent integer value.

.. _logging level: https://docs.python.org/3/library/logging.html#logging-levels


Getting Package Version at Runtime
==================================

Automatically setting your project's version is all well and good, but you
usually also want to expose that version at runtime, usually via a
``__version__`` variable.  There are two options for doing this:

1. Use the ``version()`` function in `importlib.metadata`_ to get your
   package's version, like so:

   .. code:: python

       from importlib.metadata import version

       __version__ = version("mypackage")

   Note that ``importlib.metadata`` was only added to Python in version 3.8.
   If you wish to support older Python versions, use the `importlib-metadata`_
   backport available on PyPI for those versions, e.g.:

   .. code:: python

       try:
           from importlib.metadata import version
       except ImportError:
           from importlib_metadata import version

       __version__ = version("mypackage")

   If relying on the backport, don't forget to include ``importlib-metadata;
   python_version < "3.8"`` in your project's ``install_requires``!

2. Fill out the ``[tool.versioningit.write]`` subtable in ``pyproject.toml`` so
   that the project version will be written to a file in your Python package
   which you can then import or read.  For example, if your package is named
   ``mypackage`` and is stored in a ``src/`` directory, you can write the
   version to a Python file ``src/mypackage/_version.py`` like so:

   .. code:: toml

       [tool.versioningit.write]
       file = "src/mypackage/_version.py"

   Then, within ``mypackage/__init__.py``, you can import the version like so:

   .. code:: python

       from ._version import __version__

   Alternatively, you can write the version to a text file, say,
   ``src/mypackage/VERSION``:

   .. code:: toml

      [tool.versioningit.write]
      file = "src/mypackage/VERSION"

   and then read the version in at runtime with:

   .. code:: python

       from pathlib import Path
       __version__ = Path(__file__).with_name("VERSION").read_text().strip()

.. _importlib.metadata: https://docs.python.org/3/library/importlib.metadata.html
.. _importlib-metadata: https://pypi.org/project/importlib-metadata/


Command
=======

::

    versioningit [<options>] [<project-dir>]

When ``versioningit`` is installed in the current Python environment, a command
of the same name will be available that prints out the version for a given
``versioningit``-enabled project (by default, the project rooted in the current
directory).  This can be used to test out your ``versioningit`` setup before
publishing.

Options
-------

-n, --next-version      *(New in version 0.3.0)* Instead of printing the
                        current version of the project, print the value of the
                        next release version as computed by the
                        ``next-version`` step

--traceback             Normally, any library errors are shown as just the
                        error message.  Specify this option to show the
                        complete error traceback.

-v, --verbose           Increase the amount of log messages displayed.  Specify
                        twice for maximum information.

-w, --write             Write the version to the file specified in the
                        ``[tool.versioningit.write]`` subtable, if so
                        configured


Library API
===========

The ``versioningit`` package exports a number of classes & functions for
programmatically determining a VCS-managed project's version and the values at
each step that go into calculating it.  For brevity, only the "topmost"
function is documented here; consult the source (primarily
``src/versioningit/core.py``) for documentation on the other features.

.. code:: python

    versioningit.get_version(
        project_dir: Union[str, pathlib.Path] = os.curdir,
        config: Optional[dict] = None,
        write: bool = False,
        fallback: bool = True,
    ) -> str

Returns the version of the project in ``project_dir``.  If ``config`` is
``None``, then ``project_dir`` must contain a ``pyproject.toml`` file
containing a ``[tool.versioningit]`` table; if it does not, a
``versioningit.errors.NotVersioningitError`` is raised.

If ``config`` is not ``None``, then any ``pyproject.toml`` file in
``project_dir`` will be ignored, and the configuration will be taken from
``config`` instead.  ``config`` must be a ``dict`` whose structure mirrors the
structure of the ``[tool.versioningit]`` table in ``pyproject.toml``.  For
example, the following TOML configuration:

.. code:: toml

    [tool.versioningit.vcs]
    method = "git"
    match = ["v*"]

    [tool.versioningit.next-version]
    method = { module = "setup", value = "my_next_version" }

    [tool.versioningit.format]
    distance = "{next_version}.dev{distance}+{vcs}{rev}"
    dirty = "{version}+dirty"
    distance-dirty = "{next_version}.dev{distance}+{vcs}{rev}.dirty"

when loaded as follows:

.. code:: python

    import toml

    toml_load = toml.load('versioningit.toml')
    print(get_version(config=toml_load['tool']['versioningit']))

yields the following Python ``config`` value:

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
            "dirty": "{version}+dirty",
            "distance-dirty": "{next_version}.dev{distance}+{vcs}{rev}.dirty",
        },
    }

When passing ``versioningit`` configuration as the ``config`` argument, an
alternative way to specify methods becomes available: in place of a method
specification, one can pass a callable object directly.

If ``write`` is true, then the file specified in the
``[tool.versioningit.write]`` subtable, if any, will be updated.

If ``fallback`` is true, then if ``project_dir`` is not under version control
(or if the VCS executable is not installed), ``versioningit`` will assume that
the directory is an unpacked sdist and will read the version from the
``PKG-INFO`` file; if there is no ``PKG-INFO`` file, a
``versioningit.errors.NotSdistError`` is raised.  If ``fallback`` is false and
``project_dir`` is not under version control, a
``versioningit.errors.NotVCSError`` is raised.


Writing Your Own Methods
========================

**Note:** The method function signatures changed in ``versioningit`` v1.0.0.
User parameters, previously passed as keyword arguments, are now passed as a
single ``params`` argument.

If you need to customize how a ``versioningit`` step is carried out, you can
write a custom function in a Python module in your project directory and point
``versioningit`` to that function as described under "`Specifying the
Method`_".

When a custom function is called, it will be passed a step-specific set of
arguments, as documented below, plus all of the parameters specified in the
step's subtable in ``pyproject.toml``.  (The arguments are passed as keyword
arguments, so custom methods need to give them the same names as documented
here.)  For example, given the below configuration:

.. code:: toml

    [tool.versioningit.vcs]
    method = { module = "ving_methods", value = "my_vcs", module-dir = "tools" }
    tag-dir = "tags"
    annotated-only = true

``versioningit`` will carry out the ``vcs`` step by calling ``my_vcs()`` in
``ving_methods.py`` in the ``tools/`` directory with the arguments
``project_dir`` (set to the directory in which the ``pyproject.toml`` file is
located) and ``params={"tag-dir": "tags", "annotated-only": True}``.

If a user-supplied parameter to a method is invalid, the method should raise a
``versioningit.errors.ConfigError``.  If a method is passed a parameter that it
does not recognize, it should ignore it.

If you choose to store your custom methods in your ``setup.py``, be sure to
place the call to ``setup()`` behind an ``if __name__ == "__main__":`` guard so
that the module can be imported without executing ``setup()``.

If you store your custom methods in a module other than ``setup.py`` that is
not part of the project's Python package (e.g., if the module is stored in a
``tools/`` directory), you need to ensure that the module is included in your
project's sdists but not in wheels.

If your custom method depends on any third-party libraries, they must be listed
in your project's ``build-system.requires``.

``vcs``
-------

A custom ``vcs`` method is a callable with the following signature:

.. code:: python

    (*, project_dir: Union[str, pathlib.Path], params: Dict[str, Any]) -> versioningit.VCSDescription

The callable must take a path to a directory and a collection of user-supplied
parameters and return a ``versioningit.VCSDescription`` describing the state of
the version control repository at the directory, where ``VCSDescription`` is a
dataclass with the following fields:

``tag`` : ``str``
    The name of the most recent tag in the repository (possibly after applying
    any match or exclusion rules based on the parameters) from which the
    current repository state is descended.  If a tag cannot be determined, a
    ``versioningit.errors.NoTagError`` should be raised.

``state`` : ``str``
    A string describing the relationship of the current repository state to the
    tag.  If the repository state is exactly the tagged state, this field
    should equal ``"exact"``; otherwise, it should be a custom string that will
    be used as a key in the ``[tool.versioningit.format]`` subtable.  Custom
    ``vcs`` methods are advised to adhere closely to the
    ``"distance"``/``"dirty"``/``"distance-dirty"`` set of states used by
    built-in methods.

``branch`` : ``Optional[str]``
    The name of the repository's current branch, or ``None`` if it cannot be
    determined or does not apply

``fields`` : ``Dict[str, Any]``
    An arbitrary ``dict`` of fields for use in ``[tool.versioningit.format]``
    format templates.  Custom ``vcs`` methods are advised to adhere closely to
    the set of fields used by the built-in methods.

If ``project_dir`` is not under the expected type of version control, a
``versioningit.errors.NotVCSError`` should be raised.

``tag2version``
---------------

A custom ``tag2version`` method is a callable with the following signature:

.. code:: python

    (*, tag: str, params: Dict[str, Any]) -> str

The callable must take a tag retrieved from version control and a collection of
user-supplied parameters and return a version string.  If the tag cannot be
parsed, a ``versioningit.errors.InvalidTagError`` should be raised.

``next-version``
----------------

A custom ``next-version`` method is a callable with the following signature:

.. code:: python

    (*, version: str, branch: Optional[str], params: Dict[str, Any]) -> str

The callable must take a project version (as extracted from a VCS tag), the
name of the VCS repository's current branch (if any), and a collection of
user-supplied parameters and return a version string for use as the
``{next_version}`` field in ``[tool.versioningit.format]`` format templates.
If ``version`` cannot be parsed, a ``versioningit.errors.InvalidVersionError``
should be raised.

``format``
----------

A custom ``format`` method is a callable with the following signature:

.. code:: python

    (*, description: versioningit.VCSDescription, version: str, next_version: str, params: Dict[str, Any]) -> str

The callable must take a ``versioningit.VCSDescription`` as returned by the
``vcs`` method (see above), a version string extracted from the VCS tag, a
"next version" calculated by the ``next-version`` step, and a collection of
user-supplied parameters and return the project's final version string.

Note that the ``format`` method is not called if ``description.state`` is
``"exact"``, in which case the version returned by the ``tag2version`` step is
used as the final version.

``write``
---------

A custom ``write`` method is a callable with the following signature:

.. code:: python

    (*, project_dir: Union[str, pathlib.Path], version: str, params: Dict[str, Any]) -> None

The callable must take the path to a project directory, the project's final
version, and a collection of user-supplied parameters and write the version to
a file in ``project_dir``.

Distributing Your Methods in an Extension Package
-------------------------------------------------

If you want to make your custom ``versioningit`` methods available for others
to use, you can package them in a Python package and distribute it on PyPI.
Simply create a Python package as normal that contains the method function, and
specify the method function as an entry point of the project.  The name of the
entry point group is ``versioningit.STEP`` (though, for ``next-version``, the
group is spelled with an underscore instead of a hyphen:
``versioningit.next_version``).  For example, if you have a custom ``vcs``
method implemented as a ``foobar_vcs()`` function in ``mypackage/vcs.py``, you
would declare it in ``setup.cfg`` as follows:

.. code:: ini

    [options.entry_points]
    versioningit.vcs =
        foobar = mypackage.vcs:foobar_vcs

Once your package is on PyPI, package developers can use it by including it in
their ``build-system.requires`` and specifying the name of the entry point (For
the entry point above, this would be ``foobar``) as the method name in the
appropriate subtable.  For example, a user of the ``foobar`` method for the
``vcs`` step would specify it as:

.. code:: toml

    [tool.versioningit.vcs]
    method = "foobar"
    # Parameters go here


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
  ``python setup.py develop`` or ``pip install -e .`` after each commit if you
  want the version to be up-to-date.

  .. TODO: Confirm the above

- If you define & use a custom method inside your Python project's package, you
  will not be able to retrieve your project version by calling
  ``importlib.metadata.version()`` inside ``__init__.py`` — at least, not
  without a ``try: ... except ...`` wrapper.  This is because ``versioningit``
  loads the package containing the custom method before the package is
  installed, but ``importlib.metadata.version()`` only works after the package
  is installed.
