""" A source file """

__version__ = "UNKNOWN"

if __version__ == "UNKNOWN":
    __version_info__ = (0, 0, 0)
else:
    __version_info__ = tuple(map(int, __version__.split(".")))
VERSION = '1.2.3'
BUILD_DATE = '2038-01-19T03:14:07Z'
