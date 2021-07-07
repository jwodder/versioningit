import pytest
from versioningit.errors import InvalidVersionError
from versioningit.next_version import (
    BasicVersion,
    next_minor_release_version,
    next_minor_version,
    next_smallest_release_version,
    next_smallest_version,
    null_next_version,
)


@pytest.mark.parametrize(
    "v,bv,s",
    [
        ("1.2.3", BasicVersion(0, [1, 2, 3]), "1.2.3"),
        ("0!1.2.3", BasicVersion(0, [1, 2, 3]), "1.2.3"),
        ("1!1.2.3", BasicVersion(1, [1, 2, 3]), "1!1.2.3"),
        ("21.07.05", BasicVersion(0, [21, 7, 5]), "21.7.5"),
        ("1.2.3.0.0", BasicVersion(0, [1, 2, 3, 0, 0]), "1.2.3.0.0"),
        ("42", BasicVersion(0, [42]), "42"),
        ("1.2.3.post1", BasicVersion(0, [1, 2, 3]), "1.2.3"),
        ("1.2.3a0", BasicVersion(0, [1, 2, 3]), "1.2.3"),
        ("1.2.3.dev1", BasicVersion(0, [1, 2, 3]), "1.2.3"),
        ("v1.2.3", BasicVersion(0, [1, 2, 3]), "1.2.3"),
        ("1!2", BasicVersion(1, [2]), "1!2"),
    ],
)
def test_basic_version(v: str, bv: BasicVersion, s: str) -> None:
    bv2 = BasicVersion.parse(v)
    assert bv2 == bv
    assert str(bv2) == s


@pytest.mark.parametrize(
    "s",
    [
        "",
        "rel1.2.3",
        "1!",
        "1!v1.2.3",
        "1!2!3",
    ],
)
def test_bad_basic_version(s: str) -> None:
    with pytest.raises(InvalidVersionError):
        BasicVersion.parse(s)


@pytest.mark.parametrize(
    "v1,v2",
    [
        ("1.2.3.4", "1.3.0"),
        ("1.2", "1.3.0"),
        ("1", "1.1.0"),
        ("0", "0.1.0"),
        ("1.2.3a0", "1.3.0"),
        ("1.2.3.post1", "1.3.0"),
        ("1.2.3.dev1", "1.3.0"),
        ("1.2.3.0.0", "1.3.0"),
        ("0.5.0", "0.6.0"),
        ("0.5.1", "0.6.0"),
    ],
)
def test_next_minor_version(v1: str, v2: str) -> None:
    assert next_minor_version(version=v1, branch="master") == v2


@pytest.mark.parametrize(
    "v1,v2",
    [
        ("1.2.3.4", "1.2.3.5"),
        ("1.2", "1.3"),
        ("1", "2"),
        ("0", "1"),
        ("1.2.3a0", "1.2.4"),
        ("1.2.3.post1", "1.2.4"),
        ("1.2.3.dev1", "1.2.4"),
        ("1.2.3.0.0", "1.2.3.0.1"),
        ("0.5.0", "0.5.1"),
        ("0.5.1", "0.5.2"),
    ],
)
def test_next_smallest_version(v1: str, v2: str) -> None:
    assert next_smallest_version(version=v1, branch="master") == v2


@pytest.mark.parametrize(
    "v",
    [
        "1.2.3.4",
        "1.2",
        "1",
        "0",
        "1.2.3a0",
        "1.2.3.post1",
        "1.2.3.dev1",
        "1.2.3.0.0",
        "",
        "rel1.2.3",
        "1!",
        "1!v1.2.3",
        "1!2!3",
    ],
)
def test_null_next_version(v: str) -> None:
    assert null_next_version(version=v, branch="master") == v


@pytest.mark.parametrize(
    "v1,v2",
    [
        ("1.2.3.4", "1.3.0"),
        ("1.2", "1.3.0"),
        ("1", "1.1.0"),
        ("0", "0.1.0"),
        ("1.2.3.0.0", "1.3.0"),
        ("0.5.0", "0.6.0"),
        ("0.5", "0.6.0"),
        ("0.5.0.0.0", "0.6.0"),
        ("0.5.1", "0.6.0"),
        ("0.5.0.post1", "0.6.0"),
        ("0.5.1.post1", "0.6.0"),
        ("0.5.0a1", "0.5.0"),
        ("0.5.1a1", "0.5.1"),
        ("0.5.0.dev1", "0.5.0"),
        ("0.5.1.dev1", "0.5.1"),
        ("1!0.5.0", "1!0.6.0"),
    ],
)
def test_next_minor_release_version(v1: str, v2: str) -> None:
    assert next_minor_release_version(version=v1, branch="master") == v2


@pytest.mark.parametrize(
    "v1,v2",
    [
        ("1.2.3.4", "1.2.3.5"),
        ("1.2", "1.3"),
        ("1", "2"),
        ("0", "1"),
        ("1.2.3.0.0", "1.2.3.0.1"),
        ("0.5.0", "0.5.1"),
        ("0.5", "0.6"),
        ("0.5.0.0.0", "0.5.0.0.1"),
        ("0.5.1", "0.5.2"),
        ("0.5.0.post1", "0.5.1"),
        ("0.5.1.post1", "0.5.2"),
        ("0.5.0a1", "0.5.0"),
        ("0.5.1a1", "0.5.1"),
        ("0.5.0.dev1", "0.5.0"),
        ("0.5.1.dev1", "0.5.1"),
        ("1!0.5.0", "1!0.5.1"),
    ],
)
def test_next_smallest_release_version(v1: str, v2: str) -> None:
    assert next_smallest_release_version(version=v1, branch="master") == v2
