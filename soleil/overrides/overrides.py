from collections import Counter
from typing import Any, Dict, List, Optional, Union
from pglib.validation import NoItem, checked_get_single
from soleil._utils import (
    infer_solconf_package,
    Unassigned,
    get_caller_frame,
    get_global_loader,
)
from .overridable import Overridable
from .variable_path import deduce_soleil_var_path, CompoundRefStr
from .parser import Override, OverrideType, parse_overrides, parse_ref


OverrideSpec = Union[str, Dict[CompoundRefStr, Any], Override]
"""
An override specification -- Various possibilities:

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

    @classmethod
    def from_override(
        cls, ovr: Override, globals_: dict, locals_: dict
    ) -> "PreCompOverride":
        return cls(
            target=ovr.target,
            assign_type=ovr.assign_type,
            value_expr=ovr.get_value(globals_, locals_),
            used=ovr.used,
            source=ovr.source,
        )

    def get_value(self, *args, **kwargs):
        return self.value_expr


def cast_overrides(overrides: List[OverrideSpec]) -> List[Override]:
    """
    Takes strings with one or more overrides, dictionaries with refs and values (e.g., {'a.b[0].x':3}) or :class:`Override` objects
    obtained from :func:`parse_overrides` and converts them to a list of :class:`Override` objects.

    The output list can contain more elements than the input since both ``str`` and ``dict`` override specifiers can contain multiple overrides.
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

    return _overrides


def eval_overrides(
    overrides: Union[OverrideSpec, List[OverrideSpec]],
    globals_=None,
    locals_=None,
    check_unique=True,
) -> List[PreCompOverride]:
    """
    Computes the value of all input overrides.
    """
    globals_ = globals_ or {}
    locals_ = locals_ or {}
    if not isinstance(overrides, List):
        overrides = [overrides]
    out = [
        PreCompOverride.from_override(_ovr, globals_, locals_)
        for _ovr in cast_overrides(overrides)
    ]

    # Check unique targets
    if check_unique:
        counts = Counter(_y.target.as_str() for _y in out)
        if multiply_defined := [_t for _t, _c in counts.items() if _c > 1]:
            raise ValueError(
                f"Multiple overrides provided for target(s) `{', '.join(multiply_defined)}`"
            )

    return out


def merge_overrides(
    overrides: List[PreCompOverride], new_overrides: List[PreCompOverride]
):
    """ """

    new_targets = {x.target.as_str(): x for x in new_overrides}

    return [
        x if (ts := x.target.as_str()) not in new_targets else new_targets.pop(ts)
        for x in overrides
    ] + list(new_targets.values())


def _soleil_override(target_name: str, value: Any):
    """
    Returns the assigned value or an override if any was specified. Adds support for special adds support for special :class:`~soleil.overrides.overridable.Overridable` values such as
    :class:`~soleil.overrides.overridable.submodule` and :class:`~soleil.overrides.overridable.choices` that use the user-supplied override value to choose a submodule or value.
    """

    frame = get_caller_frame()
    target_var_path = deduce_soleil_var_path(target_name, frame=frame)
    overrides = get_global_loader().package_overrides[infer_solconf_package()]

    ovr_value = Unassigned
    if (
        target_var_path
        is not None  # Is None if target is inaccesible due to a promotion
        and (
            _ovr := checked_get_single(
                filter(
                    lambda x: x.target == target_var_path,
                    get_global_loader().package_overrides[infer_solconf_package()],
                ),
                raise_empty=False,
            )
        )
        is not NoItem
    ):
        # Get the override value
        _ovr.used += 1
        ovr_value = _ovr.get_value()

    # Compute the output value
    if isinstance(value, Overridable):
        if ovr_value is not Unassigned:
            value.set(ovr_value)
        return value.get(target_name, frame)
    else:
        if ovr_value is not Unassigned:
            return ovr_value
        else:
            return value
