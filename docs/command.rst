.. index:: versioningit (command)

.. _command:

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

.. program:: versioningit

.. option:: -n, --next-version

    Instead of printing the current version of the project, print the value of
    the next release version as computed by the ``next-version`` step

.. option:: --traceback

    Normally, any library errors are shown as just the error message.  Specify
    this option to show the complete error traceback.

.. option:: -v, --verbose

    Increase the amount of log messages displayed.  Specify twice for maximum
    information.

    The logging level can also be set via the :envvar:`VERSIONINGIT_LOG_LEVEL`
    environment variable.  If both :option:`-v` and
    :envvar:`VERSIONINGIT_LOG_LEVEL` are specified, the more verbose log level
    of the two will be used, where one :option:`-v` corresponds to ``INFO``
    level and two or more correspond to ``DEBUG`` level.  (If neither are
    specified, the default level of ``WARNING`` is used.)

.. option:: -w, --write

    Write the version to the file specified in the
    ``[tool.versioningit.write]`` subtable, if so configured
