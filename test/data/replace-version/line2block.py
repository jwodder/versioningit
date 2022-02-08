""" A source file """

try:
    from importlib.metadata import version
except ImportError:
    from importlib_metadata import version

__version__ = version("mypackage")

if __version__ == "UNKNOWN":
    __version_info__ = (0, 0, 0)
else:
    __version_info__ = tuple(map(int, __version__.split(".")))
