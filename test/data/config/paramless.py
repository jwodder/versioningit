from versioningit.config import Config, ConfigSection
from versioningit.methods import EntryPointSpec

cfg = Config(
    vcs=ConfigSection(
        method_spec=EntryPointSpec(group="versioningit.vcs", name="svn"),
        params={},
    ),
    tag2version=ConfigSection(
        method_spec=EntryPointSpec(group="versioningit.tag2version", name="acme"),
        params={"style": "good"},
    ),
    next_version=ConfigSection(
        method_spec=EntryPointSpec(group="versioningit.next_version", name="smallest"),
        params={},
    ),
    format=ConfigSection(
        method_spec=EntryPointSpec(group="versioningit.format", name="basic"),
        params={},
    ),
    template_fields=ConfigSection(
        method_spec=EntryPointSpec(group="versioningit.template_fields", name="basic"),
        params={},
    ),
    write=None,
    onbuild=None,
)
