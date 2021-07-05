class Error(Exception):
    pass


class ConfigError(Error, ValueError):
    pass


class MethodError(Error):
    """Raised when a method returns an invalid value"""

    pass


class NotVersioningitError(Error):
    """
    Raised when the library is called on a project that does not have
    versioningit enabled
    """

    pass


class NotSdistError(Error):
    pass


class NotVCSError(Error):
    pass


class NoTagError(Error):
    pass


class InvalidTagError(Error, ValueError):
    pass


class InvalidVersionError(Error, ValueError):
    pass
