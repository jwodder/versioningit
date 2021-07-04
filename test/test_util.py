import pytest
from versioningit.util import strip_prefix, strip_suffix

@pytest.mark.parametrize("s,prefix,r", [
    ("foobar", "foo", "bar"),
    ("foobar", "bar", "foobar"),
    ('foobar', '', 'foobar'),
    ('foobar', 'foobar', ''),
    ('foobar', 'foobarx', 'foobar'),
    ('foobar', 'xfoobar', 'foobar'),
])
def test_strip_prefix(s: str, prefix: str, r: str) -> None:
    assert strip_prefix(s, prefix) == r

@pytest.mark.parametrize("s,suffix,r", [
    ('foobar', 'bar', 'foo'),
    ('foobar', 'foo', 'foobar'),
    ('foobar', '', 'foobar'),
    ('foobar', 'foobar', ''),
    ('foobar', 'foobarx', 'foobar'),
    ('foobar', 'xfoobar', 'foobar'),
])
def test_strip_suffix(s: str, suffix: str, r: str) -> None:
    assert strip_suffix(s, suffix) == r
