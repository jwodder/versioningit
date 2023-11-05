"""
Versioning It with your Version In Git

``versioningit`` is yet another Python packaging plugin for automatically
determining your package's version based on your version control repository's
tags.  Unlike others, it allows easy customization of the version format and
even lets you easily override the separate functions used for version
extraction & calculation.

**Features:**

- Works with both setuptools and Hatch_

  .. _hatch: https://hatch.pypa.io

- Installed & configured through :pep:`518`'s ``pyproject.toml``

- Supports Git, modern Git archives, and Mercurial

- Formatting of the final version uses format template strings, with fields for
  basic VCS information and separate template strings for distanced vs. dirty
  vs. distanced-and-dirty repository states

- Can optionally write the final version to a file for loading at runtime

- Provides custom setuptools commands for inserting the final version into a
  source file at build time

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

Visit <https://github.com/jwodder/versioningit> or
<https://versioningit.rtfd.io> for more information.
"""

__version__ = "3.0.0.dev1"
__author__ = "John Thorvald Wodder II"
__author_email__ = "versioningit@varonathe.org"
__license__ = "MIT"
__url__ = "https://github.com/jwodder/versioningit"

from .core import (
    FallbackReport,
    Report,
    VCSDescription,
    Versioningit,
    get_next_version,
    get_template_fields_from_distribution,
    get_version,
    get_version_from_pkg_info,
    run_onbuild,
)
from .errors import (
    ConfigError,
    Error,
    InvalidTagError,
    InvalidVersionError,
    MethodError,
    NoTagError,
    NotSdistError,
    NotVCSError,
    NotVersioningitError,
)
from .get_cmdclasses import get_cmdclasses
from .onbuild import OnbuildFile, OnbuildFileProvider

__all__ = [
    "ConfigError",
    "Error",
    "FallbackReport",
    "InvalidTagError",
    "InvalidVersionError",
    "MethodError",
    "NoTagError",
    "NotSdistError",
    "NotVCSError",
    "NotVersioningitError",
    "OnbuildFile",
    "OnbuildFileProvider",
    "Report",
    "VCSDescription",
    "Versioningit",
    "get_cmdclasses",
    "get_next_version",
    "get_template_fields_from_distribution",
    "get_version",
    "get_version_from_pkg_info",
    "run_onbuild",
]
