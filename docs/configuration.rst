.. currentmodule:: versioningit

.. _configuration:

Configuration
=============

The ``[tool.versioningit]`` table in :file:`pyproject.toml` is divided into
seven subtables, each describing how one of the seven steps of the version
extraction & calculation should be carried out.  Each subtable consists of an
optional ``method`` key specifying the :dfn:`method` (entry point or function)
that should be used to carry out that step, plus zero or more extra keys that
will be passed as parameters to the method when it's called.  If the ``method``
key is omitted, the default method for the step is used.

If you'd like to use ``versioningit`` for non-Python projects but don't want a
misleading :file:`pyproject.toml` in the project's directory, you can place the
configuration into a :file:`versioningit.toml` file instead.  If a project
contains both configuration files, ``versioningit`` will use the
:file:`versioningit.toml` file.

Any mentions of just :file:`pyproject.toml` in this documentation should be
understood to apply to :file:`versioningit.toml` as well.

.. versionadded:: 3.2.0

    Support for :file:`versioningit.toml`

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
      and the "tags" option was added in Git 2.35.0.  A Git repository archive
      must be created with a Git of the appropriate minimum version in order to
      be installable with this method.

      Fortunately, GitHub repository ZIP downloads currently support both
      ``%(describe)`` and ``%(describe:tags)``, and so
      :command:`pip`-installing a "git-archive"-using project from a URL of the
      form ``https://github.com/$OWNER/$REPO/archive/$BRANCH.zip`` will work.

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
    something horrible and unparsable.

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
and formats the template using the given format fields plus ``{base_version}``,
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
``{base_version}``    The version extracted from the most recent tag
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
``{revision}``        The full hash of the HEAD commit (``"git"`` and ``"hg"``
                      only)
``{vcs}``             The first letter of the name of the VCS (i.e., "``g``" or
                      "``h``")
``{vcs_name}``        The name of the VCS (i.e., "``git``" or "``hg``")
====================  =========================================================

.. [#dt] These fields are UTC ``datetime.datetime`` objects.  They are
   formatted with ``strftime()`` formats by writing ``{fieldname:format}``,
   e.g., ``{build_date:%Y%m%d}``.

.. versionchanged:: 2.0.0

    The ``{version}`` field was renamed to ``{base_version}``.  The old name
    remains usable but is deprecated.

The default parameters for the ``format`` step are:

.. code:: toml

    [tool.versioningit.format]
    distance = "{base_version}.post{distance}+{vcs}{rev}"
    dirty = "{base_version}+d{build_date:%Y%m%d}"
    distance-dirty = "{base_version}.post{distance}+{vcs}{rev}.d{build_date:%Y%m%d}"


.. _template-fields:

The ``[tool.versioningit.template-fields]`` Subtable
----------------------------------------------------

.. versionadded:: 2.0.0

The ``template-fields`` subtable controls the fields available for the
templates of the ``write`` and ``onbuild`` steps.  ``versioningit`` provides
one ``template-fields`` method, ``"basic"`` (the default), which provides the
following template fields:

- ``{version}`` — the project's final version

- ``{version_tuple}`` — a string representation of a tuple of ``{version}``'s
  components; see below for how to configure how the version is split up

- All of the same fields available in the ``format`` step with the "basic"
  ``format`` method (`see above <format-fields_>`_), but with ``{branch}`` not
  sanitized and without the ``{version}`` alias of ``{base_version}``

.. important::

    If ``tool.versioningit.default-version`` (`see below <default-version_>`_)
    is set and an error occurs during version calculation, leading to
    ``versioningit`` recovering by using the given default version, there may
    not be enough information afterwards to populate all of the template
    fields, and you will get an error if you try to use an unpopulated field in
    a ``write`` or ``onbuild`` template.

    If ``default-version`` is set, the only fields you can rely on to always be
    present are ``{version}`` and ``{version_tuple}``.

The ``"basic"`` method takes one optional parameter, a ``version-tuple``
subtable (i.e., ``[tool.versioningit.template-fields.version-tuple]``), used to
control how the project's version is converted into the ``{version_tuple}``
field.  This subtable can contain the following fields:

``split-on`` : string
    *(optional)* A Python regex that will be used to split apart the project
    version with `re.split`.  Any `None` or empty items returned by the split
    are discarded.  Any items that consist entirely of digits are converted to
    integers (i.e., they will not be enclosed in quotes in
    ``{version_tuple}``).  Defaults to ``[-_.+!]``.

    This field is ignored when ``pep440`` is true.

``pep440`` : boolean
    *(optional)* If true (default: false), the project version will be parsed &
    normalized as a :pep:`440` version (If is not valid, an error will occur),
    and ``{version_tuple}`` will consist of the following items, in order:

    - The version's epoch (as an integer), if ``epoch`` is true or if ``epoch``
      is unspecified and the epoch is nonzero
    - The individual components of the release version as integers, including
      trailing zero components
    - If the version is a prerelease, the phase identifier and prerelease
      number (e.g., ``"a0"`` or ``"rc1"``)
    - If the version is a postrelease, "``post``" and the postrelease number
    - If the version is a dev release, "``dev``" and the dev release number
    - If the version has a local version label, "``+``" and the label

``epoch`` : boolean
    *(optional)* Whether to include the version's epoch in ``{version_tuple}``.
    If unspecified, the epoch is included iff it is nonzero.

    This option only has an effect when ``pep440`` is true.

``double-quote`` : boolean
    *(optional)* Whether to enclose string components in double quotes (`True`,
    the default) or single quotes (`False`)

Here are some examples of how a version can be converted to a
``{version_tuple}``:

================  =============  ==========  =========  =============================
``{version}``     ``split-on``   ``pep440``  ``epoch``  ``{version_tuple}``
================  =============  ==========  =========  =============================
1.2.3             (default)      Any         —          ``(1, 2, 3)``
1.2.3a0           (default)      ``false``   —          ``(1, 2, "3a0")``
1.2.3a0           (default)      ``true``    —          ``(1, 2, 3, "a0")``
1.2.3.post1       (default)      Any         —          ``(1, 2, 3, "post1")``
1.2.3-1           (default)      ``false``   —          ``(1, 2, 3, 1)``
1.2.3-1           (default)      ``true``    —          ``(1, 2, 3, "post1")``
1.2.3+local.2022  (default)      ``false``   —          ``(1, 2, 3, "local", 2022)``
1.2.3+local.2022  ``\.|(\+.+)``  ``false``   —          ``(1, 2, 3, "+local.2022")``
1.2.3+local.2022  (default)      ``true``    —          ``(1, 2, 3, "+local.2022")``
1.2.3b1.dev3      (default)      ``true``    —          ``(1, 2, 3, "b1", "dev3")``
1.2.3             (default)      ``true``    ``true``   ``(0, 1, 2, 3)``
1!2.3.4           (default)      ``true``    —          ``(1, 2, 3, 4)``
1!2.3.4           (default)      ``true``    ``false``  ``(2, 3, 4)``
0.1.0.0.0         (default)      Any         —          ``(0, 1, 0, 0, 0)``
1.2.3j            (default)      ``false``   —          ``(1, 2, "3j")``
1.2.3j            (default)      ``true``    —          ERROR — Not a PEP 440 version
1.2.3~local.2022  ``[.~]``       ``false``   —          ``(1, 2, 3, "local.2022")``
1.2.3~local.2022  ``[.~]``       ``true``    —          ERROR — Not a PEP 440 version
================  =============  ==========  =========  =============================


The ``[tool.versioningit.write]`` Subtable
------------------------------------------

The ``write`` subtable enables an optional feature, writing the final version
and/or other fields to a file.  Unlike the other subtables, if the ``write``
subtable is omitted, the corresponding step will not be carried out.

``versioningit`` provides one ``write`` method, ``"basic"`` (the default),
which takes the following parameters:

``file`` : string
    *(required)* The path to the file to which to write the version, relative
    to the root of your project directory.  This path should use forward
    slashes (``/``) as the path separator, even on Windows.

    .. note::

        This file should not be committed to version control, but it should be
        included in your project's built sdists and wheels.

    .. note::

        If you're using Hatch and you followed the advice above by adding the
        file to your :file:`.gitignore` or :file:`.hgignore`, then you will
        need to tell Hatch to include the file in sdists & wheels like so:

        .. code:: toml

            [tool.hatch.build]
            # Replace the path below with the value you gave to the "file" key:
            artifacts = ["src/mypackage/_version.py"]

``encoding`` : string
    *(optional)* The encoding with which to write the file.  Defaults to UTF-8.

``template``: string
    *(optional)* The content to write to the file (minus the final newline,
    which ``versioningit`` adds automatically), as a string containing some
    number of ``{fieldname}`` placeholders.  The available placeholders are
    determined by the ``template-fields`` step (`see above
    <template-fields_>`_).

    If this parameter is omitted, the default is determined based on the
    ``file`` parameter's file extension.  For ``.txt`` files and files without
    an extension, the default is::

        {version}

    while for ``.py`` files, the default is::

        __version__ = "{version}"

    If ``template`` is omitted and ``file`` has any other extension, an error
    is raised.

.. note::

    When testing out your configuration with the ``versioningit`` command (See
    :ref:`command`), you will need to pass the ``--write`` option if you want
    the ``[tool.versioningit.write]`` subtable to take effect.


.. _onbuild:

Enabling & Configuring the ``onbuild`` Step
-------------------------------------------

.. versionadded:: 1.1.0

``versioningit`` provides custom setuptools and Hatch hooks for enabling an
optional feature (called the "``onbuild`` step") in which your project's
version and/or other fields are inserted into a file in sdists & wheels at
build time while leaving your local project directory alone.

The steps for enabling the ``onbuild`` step differ depending on whether you're
using setuptools or Hatch as your build backend.  The configuration options for
the step are the same between the backends, but where you put the configuration
and how you tell the backend to enable the hooks differs.

Using ``onbuild`` with setuptools
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There are two steps to enabling the ``onbuild`` step with setuptools.  First,
add a ``[tool.versioningit.onbuild]`` table to your :file:`pyproject.toml`
containing your desired configuration for the step (`see below
<onbuild_opts_>`_).  Second, you need to tell setuptools to use
``versioningit``'s custom command classes.  How to do this depends on what file
you've placed your project's setuptools configuration in.

- If you're configuring setuptools via :file:`setup.cfg`, you can simply add
  the following field to its ``[options]`` table:

   .. code:: ini

       [options]
       cmdclass =
           sdist = versioningit.cmdclass.sdist
           build_py = versioningit.cmdclass.build_py

- If you've instead placed all your setuptools configuration in
  :file:`pyproject.toml`, then add the following table to it:

   .. code:: toml

       [tool.setuptools.cmdclass]
       build_py = "versioningit.cmdclass.build_py"
       sdist = "versioningit.cmdclass.sdist"

- If you're still configuring setuptools through :file:`setup.py`, you'll need
  to pass `versioningit.get_cmdclasses()` as the ``cmdclass`` argument to
  `setup()`, like so:

   .. code:: python

       from setuptools import setup
       from versioningit import get_cmdclasses

       setup(
           cmdclass=get_cmdclasses(),
           # Other arguments go here
       )

If you're already using other custom ``build_py`` and/or ``sdist`` command
classes, you'll need to combine them with ``versioningit``'s command classes.
One option is to pass your custom classes to `get_cmdclasses()` in
:file:`setup.py` so that ``versioningit`` will use them as parent classes; see
the function's documentation for more information.  If that doesn't work, you
may have to manually modify or subclass your command classes and add a call to
`run_onbuild()` at the appropriate location; see the function's documentation
for more information, but you'll largely be on your own at this point.

.. versionadded:: 2.2.0

    ``sdist`` and ``build_py`` classes added for use in :file:`setup.cfg` and
    :file:`pyproject.toml`

Using ``onbuild`` with Hatch
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 3.0.0

    Support for using the ``onbuild`` step with Hatch

In order to enable & configure the ``onbuild`` step when using ``versioningit``
with Hatch, simply place all of your desired configuration for the step under a
``[tool.hatch.build.hooks.versioningit-onbuild]`` table.  Do not use the
``[tool.versioningit.onbuild]`` table with Hatch; it will be ignored, and its
presence will generate a warning.

.. note::

    The ``versioningit-onbuild`` build hook is only usable when also using
    ``versioningit`` as a Hatch version source.  Trying to use the build hook
    with a different version source will result in an error.

.. note::

    The ``versioningit-onbuild`` build hook is only supported when building an
    sdist or wheel.  Using other Hatch builders (such as `the application
    builder`__) with ``versioningit-onbuild`` is not supported or endorsed in
    any way.

    __ https://hatch.pypa.io/latest/plugins/builder/app/


.. _onbuild_opts:

``onbuild`` Configuration Options
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``versioningit`` provides one ``onbuild`` method, ``"replace-version"`` (the
default).  It scans a given file for a line matching a given regex and inserts
the project version (or other templated string) into the first line that
matches.  The method takes the following parameters:

``source-file`` : string
    *(required)* The path to the file to modify, relative to the root of your
    project directory.  This path should use forward slashes (``/``) as the
    path separator, even on Windows.

``build-file`` : string
    *(required)* The path to the file to modify when building a wheel.  This
    path should be the location of the file when your project is installed,
    relative to the root of the installation directory.  For example, if
    ``source-file`` is ``"src/mypackage/__init__.py"``, where ``src/`` is your
    project dir, set ``build-file`` to ``"mypackage/__init__.py"``.  If
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
    ``{fieldname}`` placeholders with the values provided by the
    ``template-fields`` step (`see above <template-fields_>`_), and then any
    backreferences to capturing groups in the regex are expanded.

    The default value is ``"{version}"`` (that is, the version enclosed in
    double quotes).

``append-line`` : string
    *(optional)* If ``regex`` does not match any lines in the file and
    ``append-line`` is set, any occurrences of ``{fieldname}`` in
    ``append-line`` are replaced with the values provided by the
    ``template-fields`` step, and the resulting line is appended to the end of
    the file.

Thus, with the default settings, ``"replace-version"`` finds the first line in
the given file of the form "``__version__ = ...``" and replaces the part after
the ``=`` with the project version in double quotes; if there is no such line,
the file is left unmodified.

.. note::

    If you use this feature and run :command:`python setup.py` directly (as
    opposed to building with ``build`` or similar), you must invoke
    :file:`setup.py` from the root project directory (the one containing your
    :file:`setup.py`).

.. tip::

    You are encouraged to test your ``onbuild`` configuration by building an
    sdist and wheel for your project and examining the files within to ensure
    that they look how you want.  An sdist can be expanded by running
    :samp:`tar zxf {filename}`, and a wheel can be expanded by running
    :samp:`unzip {filename}`.


.. _default-version:

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

When ``versioningit`` is invoked via the setuptools or Hatch plugin interface,
it logs various information to stderr.  By default, only messages at
``WARNING`` level or higher are displayed, but this can be changed by setting
the :envvar:`VERSIONINGIT_LOG_LEVEL` environment variable to the name of a
Python `logging level`_ (case insensitive) or the equivalent integer value.

.. _logging level: https://docs.python.org/3/library/logging.html#logging-levels
