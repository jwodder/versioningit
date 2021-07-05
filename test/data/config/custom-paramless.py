from versioningit.config import Config, ConfigSection
from versioningit.methods import CustomMethodSpec, EntryPointSpec

cfg = Config(
    vcs=ConfigSection(
        method_spec=CustomMethodSpec(
            module="mypackage.mymodule", value="myvcs", module_dir=None
        ),
        params={},
    ),
    tag2version=ConfigSection(
        method_spec=CustomMethodSpec(
            module="mypackage.mytags", value="custom", module_dir="src"
        ),
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
