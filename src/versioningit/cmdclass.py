# Note: The classes in this module are not to be re-exported by `__init__.py`,
# as that would mean unconditionally importing setuptools whenever versioningit
# is imported, slowing things down.

from .get_cmdclasses import get_cmdclasses

_cmdclasses = get_cmdclasses()
sdist = _cmdclasses["sdist"]
build_py = _cmdclasses["build_py"]
