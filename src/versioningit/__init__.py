"""
Versioning It with your Version in Git

Visit <https://github.com/jwodder/versioningit> for more information.
"""

__version__ = "0.1.0.dev1"
__author__ = "John Thorvald Wodder II"
__author_email__ = "versioningit@varonathe.org"
__license__ = "MIT"
__url__ = "https://github.com/jwodder/versioningit"

### TODO: Also export errors
from .core import get_version

__all__ = ["get_version"]
