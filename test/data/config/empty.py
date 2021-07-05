from versioningit.config import Config, ConfigSection
from versioningit.methods import EntryPointSpec

cfg = Config(
    vcs=ConfigSection(
        method_spec=EntryPointSpec(group="vcs", name="git"),
        params={},
    ),
    tag2version=ConfigSection(
        method_spec=EntryPointSpec(group="tag2version", name="basic"),
        params={},
    ),
    next_version=ConfigSection(
        method_spec=EntryPointSpec(group="next_version", name="minor"),
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
