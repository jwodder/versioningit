Getting Package Version at Runtime
==================================

Automatically setting your project's version is all well and good, but you
usually also want to expose that version at runtime, usually via a
``__version__`` variable.  There are three options for doing this:

1. Use the `~importlib.metadata.version()` function in `importlib.metadata` to
   get your package's version, like so:

   .. code:: python

       from importlib.metadata import version

       __version__ = version("mypackage")

   Note that `importlib.metadata` was only added to Python in version 3.8.  If
   you wish to support older Python versions, use the `importlib-metadata`_
   backport available on PyPI for those versions, e.g.:

   .. code:: python

       try:
           from importlib.metadata import version
       except ImportError:
           from importlib_metadata import version

       __version__ = version("mypackage")

   If relying on the backport, don't forget to include ``importlib-metadata;
   python_version < "3.8"`` in your project's ``install_requires``!

   .. _importlib-metadata: https://pypi.org/project/importlib-metadata/

2. Fill out the ``[tool.versioningit.write]`` subtable in
   :file:`pyproject.toml` so that the project version will be written to a file
   in your Python package which you can then import or read.  For example, if
   your package is named ``mypackage`` and is stored in a :file:`src/`
   directory, you can write the version to a Python file
   :file:`src/mypackage/_version.py` like so:

   .. code:: toml

       [tool.versioningit.write]
       file = "src/mypackage/_version.py"

   Then, within :file:`mypackage/__init__.py`, you can import the version like
   so:

   .. code:: python

       from ._version import __version__

   Alternatively, you can write the version to a text file, say,
   :file:`src/mypackage/VERSION`:

   .. code:: toml

      [tool.versioningit.write]
      file = "src/mypackage/VERSION"

   and then read the version in at runtime with:

   .. code:: python

       from pathlib import Path
       __version__ = Path(__file__).with_name("VERSION").read_text().strip()

3. *(New in version 1.1.0)* Fill out the ``[tool.versioningit.onbuild]``
   subtable in :file:`pyproject.toml` and configure your :file:`setup.py` to
   use ``versioningit``'s custom setuptools commands.  This will allow you to
   create sdists & wheels in which some file has been modified to contain the
   line ``__version__ = "<project version>"`` or similar while leaving your
   repository alone.  See ":ref:`onbuild`" for more information.

.. tip::

    Wondering which of ``write`` and ``onbuild`` is right for your project?
    See this table for a comparison:

    .. table::
        :widths: auto
        :align: center

        ==============================================  =========  ===========
        \                                               ``write``  ``onbuild``
        ==============================================  =========  ===========
        Should affected file be under version control?  **No**     **Yes**
        Affected file must already exist?               **No**     **Yes**
        Modifies working tree? [#f1]_                   **Yes**    **No**
        Requires configuration in ``setup.py``?         **No**     **Yes**
        Run when installing in editable mode?           **Yes**    **No**
        ==============================================  =========  ===========

    .. [#f1] That is, the ``write`` method causes a file to be present (though
       likely ignored) in your repository after running, while the ``onbuild``
       method only modifies a file inside sdists & wheels and leaves the
       original copy in your repository unchanged.
