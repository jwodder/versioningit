.. currentmodule:: versioningit

.. _configuration:

Configuration
=============

The ``[tool.versioningit]`` table in :file:`pyproject.toml` is divided into six
subtables, each describing how one of the six steps of the version extraction &
calculation should be carried out.  Each subtable consists of an optional
``method`` key specifying the :dfn:`method` (entry point or function) that
should be used to carry out that step, plus zero or more extra keys that will
be passed as parameters to the method when it's called.  If the ``method`` key
is omitted, the default method for the step is used.

.. _specifying-method:

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
auxiliary file); see ":ref:`writing_methods`" for more information.  To tell
``versioningit`` to use such a method, set the ``method`` key to a table with a
``module`` key giving the dotted name of the module in which the method is
defined and a ``value`` key giving the name of the callable object in the
module that implements the method.  For example, if you created a custom
``next-version`` method that's named `my_next_version()` and is located in
:file:`mypackage/mymodule.py`, you would write:

.. code:: toml

    [tool.versioningit.next-version]
    method = { module = "mypackage.module", value = "my_next_version" }
    # Put any parameters here

Note that this assumes that :file:`mypackage/` is located at the root of the
project directory (i.e., the directory containing the :file:`pyproject.toml`
file); if is located inside another directory, like :file:`src/`, you will need
to add a ``module-dir`` key to the method table giving the path to that
directory relative to the project root, like so:

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

    .. note::

        Specifying more than one match pattern requires Git 2.13.0 or higher.

``exclude`` : list of strings
    A set of fileglob patterns to pass to the ``--exclude`` option of ``git
    describe`` to make Git not consider tags matching the given pattern(s).
    Defaults to an empty list.

    .. note::

        This option requires Git 2.13.0 or higher.

``default-tag`` : string
    If ``git describe`` cannot find a tag, ``versioningit`` will raise a
    `versioningit.errors.NoTagError` unless ``default-tag`` is set, in which
    case it will act as though the initial commit is tagged with the value of
    ``default-tag``

``"git-archive"``
~~~~~~~~~~~~~~~~~

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
    raise a `versioningit.errors.NoTagError` unless ``default-tag`` is set,
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

.. versionchanged:: 1.0.0

    The "match" and "exclude" settings are now parsed from the
    ``describe-subst`` parameter, which is now required, and the old ``match``
    and ``exclude`` parameters are now ignored.  Also, support for the "tags"
    option was added.

.. topic:: A note on Git version requirements

    - The ``%(describe)s`` placeholder was only added to Git in version 2.32.0,
      and so a Git repository archive must be created using at least that
      version in order to be installable with this method.  Fortunately, GitHub
      repository ZIP downloads support ``%(describe)``, and so
      :command:`pip`-installing a "git-archive"-using project from a URL of the
      form ``https://github.com/$OWNER/$REPO/archive/$BRANCH.zip`` will work.

    - The ``%(describe)s`` placeholder only gained support for the "tags"
      option in Git 2.35.0, and so, if this option is included in the
      ``describe-subst`` parameter, that Git version or higher will be required
      when creating a repository archive in order for the result to be
      installable.  Unfortunately, as of 2022-02-05, GitHub repository Zips do
      not support this option.

    - When installing from a Git repository rather than an archive, the
      "git-archive" method parses the ``describe-subst`` parameter into the
      equivalent ``git describe`` options, so a bleeding-edge Git is not
      required in that situation (but see the version requirements for the
      "git" method above).

.. note::

    In order to avoid DOS attacks, Git will not expand more than one
    ``%(describe)s`` placeholder per archive, and so you should not have any
    other ``$Format:%(describe)$`` placeholders in your repository.

.. note::

    This method will not work correctly if you have a tag that resembles ``git
    describe`` output, i.e., that is of the form
    ``<anything>-<number>-g<hex-chars>``.  So don't do that.

``"hg"``
~~~~~~~~

The ``"hg"`` method supports installing from a Mercurial repository or archive.
When installing from a repository, Mercurial 5.2 or higher must be installed.

The ``"hg"`` method takes the following parameters, all optional:

``pattern`` : string
    A revision pattern (See ``hg help revisions.patterns``) to pass to the
    ``latesttag()`` template function.  Note that this parameter has no effect
    when installing from a Mercurial archive.

``default-tag`` : string
    If there is no latest tag, ``versioningit`` will raise a
    `versioningit.errors.NoTagError` unless ``default-tag`` is set, in which
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
  matches the tag (using `re.search`), the tag is replaced with the contents of
  the capturing group named "``version``", or the entire matched text if there
  is no group by that name.  If the regex does not match the tag, the behavior
  depends on the ``require-match`` parameter: if true, an error is raised; if
  false or unset, the tag is left as-is.

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
    *(required)* The path to the file to which to write the version, relative
    to the root of your project directory.  This path should use forward
    slashes (``/``) as the path separator, even on Windows.

    .. note::

        This file should not be committed to version control, but it should be
        included in your project's built sdists and wheels.

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


.. _onbuild:

The ``[tool.versioningit.onbuild]`` Subtable
--------------------------------------------

.. versionadded:: 1.1.0

The ``onbuild`` subtable configures an optional feature, inserting the project
version into built project trees when building an sdist or wheel.
Specifically, this feature allows you to create sdists & wheels in which some
file has been modified to contain the line ``__version__ = "<project
version>"`` or similar while leaving your repository alone.

In order to use this feature, in addition to filling out the subtable, your
project must include a ``setup.py`` file that passes
`versioningit.get_cmdclasses()` as the ``cmdclass`` argument to `setup()`,
e.g.:

.. code:: python

    from setuptools import setup
    from versioningit import get_cmdclasses

    setup(
        cmdclass=get_cmdclasses(),
        # Other arguments go here
    )

``versioningit`` provides one ``onbuild`` method, ``"replace-version"`` (the
default).  It scans a given file for a line matching a given regex and inserts
the project version into the first line that matches.  The method takes the
following parameters:

``source-file`` : string
    *(required)* The path to the file to modify, relative to the root of your
    project directory.  This path should use forward slashes (``/``) as the
    path separator, even on Windows.

``build-file`` : string
    *(required)* The path to the file to modify when building a wheel.  This
    path should be the location of the file when your project is installed,
    relative to the root of the installation directory.  For example, if
    ``source-file`` is ``"src/mypackage/__init__.py"``, where ``src/`` is your
    project dir, set ``build-file`` to ``"mypackage/__init__.py``.  If
    you do not use a ``src/``-layout or other remapping of package files, set
    ``build-file`` to the same value as ``source-file``.

    This path should use forward slashes (``/``) as the path separator, even on
    Windows.

``encoding`` : string
    *(optional)* The encoding with which to read & write the file.  Defaults to
    UTF-8.

``regex`` : string
    *(optional)* A Python regex that is tested against each line of the file
    using `re.search`.  The first line that matches is updated as follows:

    - If the regex contains a capturing group named "``version``", the
      substring matched by the group is replaced with the expansion of
      ``replacement`` (see below).  If ``version`` did not participate in the
      match, an error is raised.

    - Otherwise, the entire substring of the line matched by the regex is
      replaced by the expansion of ``replacement``.

    The default regex is::

        ^\s*__version__\s*=\s*(?P<version>.*)

``require-match`` : boolean
    *(optional)* If ``regex`` does not match any lines in the file and
    ``append-line`` is not set, an error will be raised if ``require-match`` is
    true (default: false).

``replacement`` : string
    *(optional)* The string used to replace the relevant portion of the matched
    line.  The string is first expanded by replacing any occurrences of
    ``{version}`` with the project version, and then any backreferences to
    capturing groups in the regex are expanded.

    The default value is ``"{version}"`` (that is, the version enclosed in
    double quotes).

``append-line`` : string
    *(optional)* If ``regex`` does not match any lines in the file and
    ``append-line`` is set, any occurrences of ``{version}`` in ``append-line``
    are replaced with the project version, and the resulting line is appended
    to the end of the file.

Thus, with the default settings, ``"replace-version"`` finds the first line in
the given file of the form "``__version__ = ...``" and replaces the part after
the ``=`` with the project version in double quotes; if there is no such line,
the file is left unmodified.

.. note::

    Because the ``onbuild`` step runs both when building an sdist from the
    repository and when building a wheel from an sdist, the configuration
    should be such that running the step a second time doesn't change the file
    any further.  (The technical term for this is "idempotence")

.. note::

    If you use this feature and run :command:`python setup.py` directly (as
    opposed to building with ``build`` or similar), you must invoke
    :file:`setup.py` from the root project directory (the one containing your
    :file:`setup.py`).

.. tip::

    You are encouraged to test your ``onbuild`` configuration by building an
    sdist and wheel for your project and examining the files within to ensure
    that they look how you want.  An sdist can be expanded by running
    :command:`tar zxf <filename>`, and a wheel can be expanded by running
    :command:`unzip <filename>`.


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
time by running the ``versioningit`` command (See ":ref:`command`").


Log Level Environment Variable
------------------------------

When ``versioningit`` is invoked via the setuptools plugin interface, it logs
various information to stderr.  By default, only messages at ``WARNING`` level
or higher are displayed, but this can be changed by setting the
:envvar:`VERSIONINGIT_LOG_LEVEL` environment variable to the name of a Python
`logging level`_ (case insensitive) or the equivalent integer value.

.. _logging level: https://docs.python.org/3/library/logging.html#logging-levels
