from operator import attrgetter
from pathlib import Path
from typing import Any, Dict
import pytest
from versioningit.config import Config, ConfigSection
from versioningit.errors import ConfigError, NotVersioningitError
from versioningit.git import describe_git
from versioningit.methods import CallableSpec, EntryPointSpec
from versioningit.next_version import next_smallest_version

DATA_DIR = Path(__file__).with_name("data")


@pytest.mark.parametrize(
    "tomlfile",
    sorted((DATA_DIR / "config").glob("*.toml")),
    ids=attrgetter("stem"),
)
def test_parse_toml_file(tomlfile: Path) -> None:
    cfg = Config.parse_toml_file(tomlfile)
    namespace: Dict[str, Any] = {}
    exec(tomlfile.with_suffix(".py").read_text(encoding="utf-8"), namespace)
    assert cfg == namespace["cfg"]


@pytest.mark.parametrize(
    "tomlfile",
    sorted((DATA_DIR / "config-error").glob("*.toml")),
    ids=attrgetter("stem"),
)
def test_parse_bad_toml_file(tomlfile: Path) -> None:
    with pytest.raises((ConfigError, NotVersioningitError)) as excinfo:
        Config.parse_toml_file(tomlfile)
    assert str(excinfo.value) == tomlfile.with_suffix(".txt").read_text().strip()


def test_parse_obj_callable_methods() -> None:
    cfg = Config.parse_obj(
        {
            "vcs": describe_git,
            "next-version": {"method": next_smallest_version},
        }
    )
    assert cfg == Config(
        vcs=ConfigSection(
            method_spec=CallableSpec(describe_git),
            params={},
        ),
        tag2version=ConfigSection(
            method_spec=EntryPointSpec(group="tag2version", name="basic"),
            params={},
        ),
        next_version=ConfigSection(
            method_spec=CallableSpec(next_smallest_version),
            params={},
        ),
        format=ConfigSection(
            method_spec=EntryPointSpec(group="format", name="basic"),
            params={},
        ),
        write=ConfigSection(
            method_spec=EntryPointSpec(group="write", name="basic"),
            params={},
        ),
    )
