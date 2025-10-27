from pathlib import Path


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


class NoConfigFileError(NotVersioningitError):
    """
    .. versionadded:: 3.2.0

    Raised when ``versioningit`` is used on a project that does not contain a
    :file:`versioningit.toml` or :file:`pyproject.toml` file
    """

    def __init__(self, project_dir: Path) -> None:
        #: The path to the project directory
        self.project_dir: Path = project_dir
        super().__init__(project_dir)

    def __str__(self) -> str:
        return f"No pyproject.toml or versioningit.toml file in {self.project_dir}"


class NoConfigSectionError(NotVersioningitError):
    """
    .. versionadded:: 3.2.0

    Raised when ``versioningit`` is used on a project whose
    :file:`versioningit.toml` or :file:`pyproject.toml` file does not contain a
    ``versioningit`` configuration table
    """

    def __init__(self, config_path: Path) -> None:
        #: The path to the configuration file
        self.config_path: Path = config_path
        super().__init__(config_path)

    def __str__(self) -> str:
        return f"versioningit not configured in {self.config_path}"


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
    Raised by ``next-version`` and ``template-fields`` methods when passed a
    version that they cannot work with
    """

    pass
