.. _writing_methods:

Writing Your Own Methods
========================

.. versionchanged:: 1.0.0

    User parameters, previously passed as keyword arguments, are now passed as
    a single ``params`` argument.

If you need to customize how a ``versioningit`` step is carried out, you can
write a custom function in a Python module in your project directory and point
``versioningit`` to that function as described under
":ref:`specifying-method`".

When a custom function is called, it will be passed a step-specific set of
arguments, as documented below, plus all of the parameters specified in the
step's subtable in :file:`pyproject.toml`.  (The arguments are passed as
keyword arguments, so custom methods need to give them the same names as
documented here.)  For example, given the below configuration:

.. code:: toml

    [tool.versioningit.vcs]
    method = { module = "ving_methods", value = "my_vcs", module-dir = "tools" }
    tag-dir = "tags"
    annotated-only = true

``versioningit`` will carry out the ``vcs`` step by calling `my_vcs()` in
:file:`ving_methods.py` in the :file:`tools/` directory with the arguments
``project_dir`` (set to the directory in which the :file:`pyproject.toml` file
is located) and ``params={"tag-dir": "tags", "annotated-only": True}``.

If a user-supplied parameter to a method is invalid, the method should raise a
`versioningit.errors.ConfigError`.  If a method is passed a parameter that it
does not recognize, it should ignore it (though it may log a warning).

If you choose to store your custom methods in your :file:`setup.py`, be sure to
place the call to `setup()` under an ``if __name__ == "__main__":`` guard so
that the module can be imported without executing `setup()`.

If you store your custom methods in a module other than :file:`setup.py` that
is not part of the project's Python package (e.g., if the module is stored in a
:file:`tools/` directory), you need to ensure that the module is included in
your project's sdists but not in wheels.

If your custom method depends on any third-party libraries, they must be listed
in your project's ``build-system.requires``.

``vcs``
-------

A custom ``vcs`` method is a callable with the following synopsis:

.. function:: funcname(*, project_dir: Union[str, pathlib.Path], params: Dict[str, Any]) -> versioningit.VCSDescription
    :noindex:

    :param path project_dir: the path to a project directory
    :param dict params: a collection of user-supplied parameters
    :returns:
        a description of the state of the version control repository at the
        directory
    :rtype: versioningit.VCSDescription
    :raises versioningit.errors.NoTagError:
        If a tag cannot be determined for the repository
    :raises versioningit.errors.NotVCSError:
        if ``project_dir`` is not under the expected type of version control

``tag2version``
---------------

A custom ``tag2version`` method is a callable with the following synopsis:

.. function:: funcname(*, tag: str, params: Dict[str, Any]) -> str
    :noindex:

    :param str tag: a tag retrieved from version control
    :param dict params: a collection of user-supplied parameters
    :returns: a version string extracted from ``tag``
    :rtype: str
    :raises versioningit.errors.InvalidTagError: if the tag cannot be parsed

``next-version``
----------------

A custom ``next-version`` method is a callable with the following synopsis:

.. function:: funcname(*, version: str, branch: Optional[str], params: Dict[str, Any]) -> str
    :noindex:

    :param str version: a project version (as extracted from a VCS tag)
    :param Optional[str] branch: the name of the VCS repository's current branch (if any)
    :param dict params: a collection of user-supplied parameters
    :return:
        a version string for use as the ``{next_version}`` field in
        ``[tool.versioningit.format]`` format templates.
    :rtype: str
    :raises versioningit.errors.InvalidVersionError:
        if ``version`` cannot be parsed

``format``
----------

A custom ``format`` method is a callable with the following synopsis:

.. function:: funcname(*, description: versioningit.VCSDescription, base_version: str, next_version: str, params: Dict[str, Any]) -> str
    :noindex:

    :param description:
        a `versioningit.VCSDescription` returned by a ``vcs`` method
    :param str base_version: a version string extracted from the VCS tag
    :param str next_version:
        a "next version" calculated by the ``next-version`` step
    :param dict params: a collection of user-supplied parameters
    :returns: the project's final version string
    :rtype: str

.. versionchanged:: 2.0.0

    The ``version`` argument was renamed to ``base_version``.

Note that the ``format`` method is not called if ``description.state`` is
``"exact"``, in which case the version returned by the ``tag2version`` step is
used as the final version.

``write``
---------

A custom ``write`` method is a callable with the following synopsis:

.. function:: funcname(*, project_dir: Union[str, pathlib.Path], version: str, params: Dict[str, Any]) -> None
    :noindex:

    :param path project_dir: the path to a project directory
    :param str version: the project's final version
    :param dict params: a collection of user-supplied parameters

``onbuild``
-----------

A custom ``onbuild`` method is a callable with the following synopsis:

.. function:: funcname(*, build_dir: Union[str, pathlib.Path], is_source: bool, version: str, params: Dict[str, Any]) -> None
    :noindex:

    Modifies one or more files in ``build_dir``

    :param path build_dir:
        the path to the directory where the project is being built
    :param bool is_source:
        true if an sdist or other artifact that preserves source paths is being
        built, false if a wheel or other artifact that uses installation paths
        is being built
    :param str version: the project's final version
    :param dict params: a collection of user-supplied parameters

Distributing Your Methods in an Extension Package
-------------------------------------------------

If you want to make your custom ``versioningit`` methods available for others
to use, you can package them in a Python package and distribute it on PyPI.
Simply create a Python package as normal that contains the method function, and
specify the method function as an entry point of the project.  The name of the
entry point group is ``versioningit.STEP`` (though, for ``next-version``, the
group is spelled with an underscore instead of a hyphen:
``versioningit.next_version``).  For example, if you have a custom ``vcs``
method implemented as a `foobar_vcs()` function in :file:`mypackage/vcs.py`,
you would declare it in :file:`setup.cfg` as follows:

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
