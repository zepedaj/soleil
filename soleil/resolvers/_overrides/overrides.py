from typing import Any, Dict, Union

from soleil.resolvers.module_resolver import SolConfModule
from .parser import (
    Override,
    OverrideType,
    Ref,
    parse_overrides,
    parse_ref,
    refs_get,
)
from soleil.resolvers.setter import get_setter

CompoundRefStr = str
"""
A reference string such as ``'a[0].b.c[0]'``
"""

OverrideSpec = Union[str, Dict[CompoundRefStr, Any], Override]
"""
Various possible override specifications:

.. code-block::

    # As a string
    'a[0].b = 3'

    # As a multi-line or semicolon-separated string
    \"\"\"
    a[0].b = 3; x.y = 4
    var.sub = a[0].b
    \"\"\"

    # As a dictionary
    {'a[0].b': 3, 'x.y':4, 'var.sub':a[0].b

    # As an Override object
    overrides = parse_overrides('a[0].b=3')[0]
"""


class PreCompOverride(Override):
    """
    An :class:`Override` with a pre-computed value.
    """

    def get_value(self, *args, **kwargs):
        return self.value_expr


def assign_existing(obj: Any, member_ref: Ref, new_value: Any):
    """
    Applies an override to an existing member of an object.
    """

    current_value = member_ref.get(obj)
    if setter := get_setter(current_value):
        # Set with special setter
        setter.set(current_value, new_value)
        return
    else:
        # No special setter, assign value
        member_ref.set(obj, new_value)


def apply_overrides(obj: SolConfModule, *overrides: OverrideSpec):
    """
    Applies the specified overrides to the given object.

    Takes strings with one or more overrides, dictionaries with refs and values (e.g., {'a.b[0].x':3}) or :class:`Override` objects
    obtained from :func:`parse_overrides`.
    """
    # Map dicts and strings to Override objects
    _overrides = []
    for _ovr in overrides:
        if isinstance(_ovr, Override):
            _overrides.append(_ovr)
        elif isinstance(_ovr, str):
            _overrides.extend(parse_overrides(_ovr))
        elif isinstance(_ovr, dict):
            for key, val in _ovr.items():
                _overrides.append(
                    PreCompOverride(parse_ref(key), OverrideType.existing, val)
                )
        else:
            raise TypeError(f"Invalid type {type(_ovr)} for override specification")

    # Apply overrides
    for _ovr in _overrides:
        if _ovr.assign_type is OverrideType.existing:
            assign_existing(
                refs_get(_ovr.target[:-1], obj),
                _ovr.target[-1],
                _ovr.get_value({}, vars(obj)),
            )
        else:
            raise ValueError(f"Invalid assignment type `{_ovr.assign_type}`")
