from versioningit.config import Config, ConfigSection
from versioningit.methods import CustomMethodSpec, EntryPointSpec

cfg = Config(
    vcs=ConfigSection(
        method_spec=CustomMethodSpec(
            module="mypackage.mymodule", value="myvcs", module_dir=None
        ),
        params={"tag-dir": "tags"},
    ),
    tag2version=ConfigSection(
        method_spec=CustomMethodSpec(
            module="mypackage.mytags", value="custom", module_dir="src"
        ),
        params={"style": "acme"},
    ),
    next_version=ConfigSection(
        method_spec=EntryPointSpec(group="versioningit.next_version", name="minor"),
        params={},
    ),
    format=ConfigSection(
        method_spec=EntryPointSpec(group="versioningit.format", name="basic"),
        params={},
    ),
    write=None,
    onbuild=None,
)
