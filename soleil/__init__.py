# Core
from soleil.loader.loader import load_config
from soleil.resolvers.base import resolve
from soleil.cli_tools.solex import solex

__all__ = ["load_config", "resolve", "solex"]


# Modifiers
from soleil.resolvers.class_resolver import as_type, as_args
from soleil.resolvers.module_resolver import promoted, unpromoted, as_run
from soleil.resolvers.modifiers import hidden, visible, name, cast, noid

__all__ += [
    "as_type",
    "as_args",
    "promoted",
    "unpromoted",
    "as_run",
    "hidden",
    "visible",
    "name",
    "cast",
    "noid",
]

# Utilities
from soleil.resolvers.req import req
from soleil.utils import id_str, sub_dir, derive, temp_dir, spawn

__all__ += ["req", "id_str", "sub_dir", "derive", "temp_dir", "spawn"]

from soleil.resolvers._overrides.overrides import override
from soleil.resolvers._overrides.overridable import submodule

__all__ += ["override", "submodule"]

__keywords__ = [
    "override",
    "load",
]  # Rename override to _soleil_override, check keywords are not re-defined in pre-processor
