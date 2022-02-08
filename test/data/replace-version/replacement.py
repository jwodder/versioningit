""" A source file """

__version__ = importlib.metadata.version("mypackage")

if __version__ == "UNKNOWN":
    __version_info__ = (0, 0, 0)
else:
    __version_info__ = tuple(map(int, __version__.split(".")))
