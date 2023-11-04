from versioningit.config import Config, ConfigSection
from versioningit.methods import EntryPointSpec

cfg = Config(
    vcs=ConfigSection(
        method_spec=EntryPointSpec(group="versioningit.vcs", name="git"),
        params={},
    ),
    tag2version=ConfigSection(
        method_spec=EntryPointSpec(group="versioningit.tag2version", name="basic"),
        params={},
    ),
    next_version=ConfigSection(
        method_spec=EntryPointSpec(group="versioningit.next_version", name="minor"),
        params={},
    ),
    format=ConfigSection(
        method_spec=EntryPointSpec(group="versioningit.format", name="basic"),
        params={
            "distance": "{next_version}.dev{distance}+{vcs}{rev}",
            "dirty": "{version}+dirty",
            "distance-dirty": "{next_version}.dev{distance}+{vcs}{rev}.dirty",
        },
    ),
    template_fields=ConfigSection(
        method_spec=EntryPointSpec(group="versioningit.template_fields", name="basic"),
        params={},
    ),
    write=None,
    onbuild=None,
)
