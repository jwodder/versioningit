from typing import Any, Dict
import pytest
from versioningit.basics import basic_tag2version
from versioningit.errors import InvalidTagError


@pytest.mark.parametrize(
    "tag,params,version",
    [
        ("v01.02.03", {}, "01.02.03"),
        ("01.02.03", {}, "01.02.03"),
        ("vbad", {}, "bad"),
        ("v", {}, ""),
        ("rel-1.2.3", {}, "rel-1.2.3"),
        ("rel-1.2.3", {"rmprefix": "rel-"}, "1.2.3"),
        ("1.2.3-final", {}, "1.2.3-final"),
        ("1.2.3-final", {"rmsuffix": "-final"}, "1.2.3"),
        ("rel-1.2.3-final", {"regex": r"\d+(\.\d+)+"}, "1.2.3"),
        (
            "rel-1.2.3-final",
            {"regex": r"^rel-(?P<version>\d+(\.\d+)+)-final$"},
            "1.2.3",
        ),
        (
            "rel-1.2.3-final",
            {"rmprefix": "rel-", "regex": r"^rel-(?P<version>\d+(\.\d+)+)-final$"},
            "1.2.3-final",
        ),
    ],
)
def test_basic_tag2version(tag: str, params: Dict[str, Any], version: str) -> None:
    assert basic_tag2version(tag=tag, params=params) == version


def test_basic_tag2version_no_version_captured() -> None:
    with pytest.raises(InvalidTagError) as excinfo:
        basic_tag2version(
            tag="rel-final", params={"regex": r"^rel-(?P<version>\d+(\.d+)+)?"}
        )
    assert str(excinfo.value) == (
        "'version' group in tool.versioningit.tag2version.regex did"
        " not participate in match"
    )


def test_basic_tag2version_require_match() -> None:
    with pytest.raises(InvalidTagError) as excinfo:
        basic_tag2version(
            tag="rel-1.2.3-final",
            params={
                "rmprefix": "rel-",
                "regex": r"^rel-(?P<version>\d+(\.\d+)+)-final$",
                "require-match": True,
            },
        )
    assert str(excinfo.value) == "tag2version.regex did not match tag '1.2.3-final'"
