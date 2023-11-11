# Specifies all the imports that are automatically injected into solconf modules.


from soleil.resolvers.class_resolver import Modifiers
from soleil.resolvers.class_resolver import as_type, as_args
from soleil.resolvers.module_resolver import promoted, unpromoted, as_run
from soleil.resolvers.modifiers import hidden, visible, name, cast, noid
from soleil.resolvers.base import resolve
from soleil.resolvers.req import req
from soleil.utils import id_str, sub_dir, derive, temp_dir


__all__ = [x for x in dir() if not x.startswith("__")]
