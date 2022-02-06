from pathlib import Path
from typing import Any, Dict
import pytest
from versioningit.basics import basic_write
from versioningit.errors import ConfigError


@pytest.mark.parametrize(
    "filename,params,content",
    [
        ("foo/bar.txt", {}, "1.2.3\n"),
        ("foo/bar.py", {}, '__version__ = "1.2.3"\n'),
        ("foo/bar", {}, "1.2.3\n"),
        (
            "foo/bar.py",
            {"template": "__version__ = {version!r}"},
            "__version__ = '1.2.3'\n",
        ),
        ("foo/bar.tex", {"template": r"$v = {version}$\bye"}, "$v = 1.2.3$\\bye\n"),
    ],
)
def test_basic_write(
    filename: str, params: Dict[str, Any], content: str, tmp_path: Path
) -> None:
    basic_write(
        project_dir=tmp_path, version="1.2.3", params={"file": filename, **params}
    )
    assert (tmp_path / filename).read_text(encoding="utf-8") == content


def test_basic_write_no_file(tmp_path: Path) -> None:
    with pytest.raises(ConfigError) as excinfo:
        basic_write(project_dir=tmp_path, version="1.2.3", params={})
    assert str(excinfo.value) == "tool.versioningit.write.file must be set to a string"


def test_basic_write_bad_ext(tmp_path: Path) -> None:
    with pytest.raises(ConfigError) as excinfo:
        basic_write(
            project_dir=tmp_path, version="1.2.3", params={"file": "foo/bar.tex"}
        )
    assert str(excinfo.value) == (
        "tool.versioningit.write.template not specified and file has unknown"
        " suffix '.tex'"
    )
    assert list(tmp_path.iterdir()) == []
