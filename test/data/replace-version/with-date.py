""" A source file """

__version__ = "1.2.3"
__build_date__ = "20380119T031407Z"

if __version__ == "UNKNOWN":
    __version_info__ = (0, 0, 0)
else:
    __version_info__ = tuple(map(int, __version__.split(".")))
