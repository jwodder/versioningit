How it Works
============

``versioningit`` divides its operation into seven :dfn:`steps`: ``vcs``,
``tag2version``, ``next-version``, ``format``, ``template-fields``, ``write``,
and ``onbuild``.  The first four steps make up the actual version calculation,
while the rest normally only happen while building with setuptools.

Version Calculation
-------------------

The version for a given project is determined as follows:

- ``vcs`` step: The version control system specified in the project's
  ``versioningit`` configuration is queried for information about the project's
  working directory: the most recent tag, the number of commits since that tag,
  whether there are any uncommitted changes, and other data points.

- ``tag2version`` step: A version is extracted from the tag returned by the
  ``vcs`` step

- ``next-version`` step: The next version after the most recent version is
  calculated

- If there have been no commits or uncommitted changes since the most recent
  tag, the version returned by the ``tag2version`` step is used as the project
  version.  Otherwise:

  - ``format`` step: The results of the preceding steps are combined to produce
    a final project version.

- ``template-fields`` step: Values from the preceding steps are used to
  calculate a set of template fields for use by the ``write`` and/or
  ``onbuild`` steps


Setuptools Integration
----------------------

Setting the Version
^^^^^^^^^^^^^^^^^^^

``versioningit`` registers a ``setuptools.finalize_distribution_options`` entry
point that causes it to be run whenever setuptools computes the metadata for a
project in an environment in which ``versioningit`` is installed.  If the
project in question has a :file:`pyproject.toml` file with a
``[tool.versioningit]`` table, then ``versioningit`` performs the version
calculations described above and sets the project's version to the final value.
(If a version cannot be determined because the project is not in a repository
or repository archive, then ``versioningit`` will assume the project is an
unpacked sdist and will look for a :file:`PKG-INFO` file to fetch the version
from instead.)  If the :file:`pyproject.toml` contains a
``[tool.versioningit.write]`` table, then the ``write`` step will also be run
at this time; the default ``write`` method creates a file at a specified path
containing the project's version.

``onbuild`` Step
^^^^^^^^^^^^^^^^

When a project is built that uses ``versioningit``'s custom setuptools
commands, the ``onbuild`` step becomes added to the build process.  The default
``onbuild`` method updates one of the files in the built distribution to
contain the project version while leaving the source files in the actual
project alone.  See ":ref:`onbuild`" for more information.
