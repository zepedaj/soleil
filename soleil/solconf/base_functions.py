from typing import Union
from numpy import datetime64
from .utils import register
import builtins

ENABLED_BUILTIN_TYPES = ['float', 'int', 'bytes', 'str', 'bool']


@register('type')
def as_builtin_type(val, type_name):
    """
    Casts to one of the allowed builtin types in :attr:`ENABLED_BUILTIN_TYPES`.
    """
    assert type_name in ENABLED_BUILTIN_TYPES
    return getattr(builtins, type_name)(val)


# Register the enabled builtin types.
for t_ in ENABLED_BUILTIN_TYPES:
    register(t_, doc=f'Casts to ``{t_}``.')(lambda val,
                                            type_name=t_: as_builtin_type(val, type_name))
