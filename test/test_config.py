from operator import attrgetter
from pathlib import Path
from typing import Any, Dict
import pytest
from versioningit.config import Config

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
