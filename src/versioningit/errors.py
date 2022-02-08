class Error(Exception):
    """Base class of all ``versioningit``-specific errors"""

    pass


class ConfigError(Error, ValueError):
    """
    Raised when the ``versioningit`` configuration contain invalid settings
    """

    pass


class MethodError(Error):
    """Raised when a method is invalid or returns an invalid value"""

    pass


class NotVersioningitError(Error):
    """
    Raised when ``versioningit`` is used on a project that does not have
    ``versioningit`` enabled
    """

    pass


class NotSdistError(Error):
    """
    Raised when attempting to read a :file:`PKG-INFO` file from a directory
    that doesn't have one
    """

    pass


class NotVCSError(Error):
    """
    Raised when ``versioningit`` is run in a directory that is not under
    version control or when the relevant VCS program is not installed
    """

    pass


class NoTagError(Error):
    """Raised when a tag cannot be found in version control"""

    pass


class InvalidTagError(Error, ValueError):
    """
    Raised by ``tag2version`` methods when passed a tag that they cannot work
    with
    """

    pass


class InvalidVersionError(Error, ValueError):
    """
    Raised by ``next-version`` methods when passed a version that they cannot
    work with
    """

    pass
