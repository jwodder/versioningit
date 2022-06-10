from versioningit.config import Config, ConfigSection
from versioningit.methods import EntryPointSpec

cfg = Config(
    vcs=ConfigSection(
        method_spec=EntryPointSpec(group="versioningit.vcs", name="git"),
        params={
            "match": ["v*", "package-*"],
            "exclude": ["*-alpha"],
            "default-tag": "package-0.0.0",
            "project_dir": "/usr/src/project",
        },
    ),
    tag2version=ConfigSection(
        method_spec=EntryPointSpec(group="versioningit.tag2version", name="basic"),
        params={"rmprefix": "package-", "tag": "v1.2.3"},
    ),
    next_version=ConfigSection(
        method_spec=EntryPointSpec(group="versioningit.next_version", name="smallest"),
        params={"version": "1.3.0", "branch": "master"},
    ),
    format=ConfigSection(
        method_spec=EntryPointSpec(group="versioningit.format", name="basic"),
        params={
            "distance": "{base_version}.post{distance}+{vcs}{rev}",
            "dirty": "{base_version}+dirty.{build_date:%Y%m%d}",
            "distance-dirty": "{base_version}.post{distance}+{vcs}{rev}.dirty.{build_date:%Y%m%d}",
            "description": "This will be discarded",
            "version": "1.2.3",
            "next_version": "1.3.0",
        },
    ),
    write=ConfigSection(
        method_spec=EntryPointSpec(group="versioningit.write", name="basic"),
        params={
            "file": "src/package/_version.py",
            "encoding": "utf-8",
            "template": "VERSION = {version!r}",
            "project_dir": "/usr/src/project",
            "version": "1.3.0",
        },
    ),
    onbuild=ConfigSection(
        method_spec=EntryPointSpec(
            group="versioningit.onbuild", name="replace-version"
        ),
        params={
            "source-file": "src/package/__init__.py",
            "build-file": "package/__init__.py",
            "build_dir": "/tmp/build",
            "is_source": True,
            "version": "1.2.3",
        },
    ),
)
