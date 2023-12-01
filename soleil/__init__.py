# Core
from soleil.loader.loader import load_config
from soleil.resolvers.base import resolve
from soleil.cli_tools.solex import solex

__all__ = ["load_config", "resolve", "solex"]


# Modifiers
from soleil.resolvers.class_resolver import as_type, as_args
from soleil.resolvers.module_resolver import promoted, resolves, as_run
from soleil.resolvers.modifiers import hidden, visible, name, cast, noid

__all__ += [
    "as_type",
    "as_args",
    "promoted",
    "resolves",
    "as_run",
    "hidden",
    "visible",
    "name",
    "cast",
    "noid",
]

# Utilities
from soleil.utils import (
    id_str,
    root_stem,
    sub_dir,
    derive,
    temp_dir,
    spawn,
    package_overrides,
)
from soleil.rcall import rcall

__all__ += [
    "id_str",
    "root_stem",
    "sub_dir",
    "derive",
    "temp_dir",
    "spawn",
    "rcall",
    "package_overrides",
]

# Overridables
#
from soleil.overrides.overridable import submodule, choices
from soleil.overrides.req import req

__all__ += ["submodule", "choices", "req"]
