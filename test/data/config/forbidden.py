from versioningit.config import Config, ConfigSection
from versioningit.methods import EntryPointSpec

cfg = Config(
    vcs=ConfigSection(
        method_spec=EntryPointSpec(group="vcs", name="git"),
        params={
            "match": ["v*", "package-*"],
            "exclude": ["*-alpha"],
            "default_tag": "package-0.0.0",
        },
    ),
    tag2version=ConfigSection(
        method_spec=EntryPointSpec(group="tag2version", name="basic"),
        params={"rmprefix": "package-"},
    ),
    next_version=ConfigSection(
        method_spec=EntryPointSpec(group="next_version", name="smallest"),
        params={},
    ),
    format=ConfigSection(
        method_spec=EntryPointSpec(group="format", name="basic"),
        params={
            "distance": "{version}.post{distance}+{vcs}{rev}",
            "dirty": "{version}+dirty.{build_date:%Y%m%d}",
            "distance-dirty": "{version}.post{distance}+{vcs}{rev}.dirty.{build_date:%Y%m%d}",
        },
    ),
    write=ConfigSection(
        method_spec=EntryPointSpec(group="write", name="basic"),
        params={
            "file": "src/package/_version.py",
            "encoding": "utf-8",
            "template": "VERSION = {version!r}",
        },
    ),
)
