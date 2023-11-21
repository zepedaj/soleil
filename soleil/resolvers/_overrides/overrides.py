from types import FrameType
from typing import Any, Dict, List, Union
from pglib.validation import NoItem, checked_get_single
from soleil._utils import (
    infer_solconf_package,
    Unassigned,
    get_caller_frame,
    get_global_loader,
)
from .overridable import Overridable

from .parser import Override, OverrideType, parse_overrides, parse_ref

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


def cast_overrides(*overrides: OverrideSpec) -> List[Override]:
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
    overrides: List[OverrideSpec], globals_, locals_
) -> List[PreCompOverride]:
    """
    Computes the value of all input overrides.
    """
    return [
        PreCompOverride.from_override(_ovr, globals_, locals_)
        for _ovr in cast_overrides(*overrides)
    ]


def deduce_soleil_qualname(target_name: str, frame: Union[FrameType, int, None] = 0):
    """
    Returns a string specifying a variables name as seen from the root configuration.

    Example:

    .. code-block::

        # main.solconf
        assert __soleil_qualname__ is None # Is True
        a = load('module2') # Will propagate 'a' as the module's __soleil_qualname__

        # module2.solconf
        assert __soleil_qualname__ == 'a' # Is True
        b = 1
        deduce_soleil_qualname('b', -1) == 'a.b' # Is True, -1 bc usuallly called within a function `fxn` such as override() or load()

    """

    # Get the frame two levels up by default
    if not isinstance(frame, FrameType):
        frame = get_caller_frame((frame or 0) + 2)

    #
    module_name = frame.f_globals["__soleil_qualname__"]
    promoted_name = (
        get_global_loader().modules[frame.f_globals["__name__"]].__pp_promoted__
    )
    class_name = frame.f_locals.get("__qualname__", None)

    if promoted_name:
        if class_name is None and target_name == promoted_name:
            # The promoted variable is overriden in the loading module
            # and not in the containing module.
            return None
        elif (
            class_name is not None
            and (class_components := class_name.split("."))[0] == promoted_name
        ):
            # The promoted variable is a root-level class, skip the name of that root-level class
            return ".".join(
                filter(
                    lambda x: x is not None,
                    [module_name] + class_components[1:] + [target_name],
                )
            )
    else:
        return ".".join(
            filter(lambda x: x is not None, [module_name, class_name, target_name])
        )


def _soleil_override(target_name: str, value: Any):
    """
    Returns the assigned value or an override if any was specified.
    """

    frame = get_caller_frame()
    target_qualname = deduce_soleil_qualname(target_name, frame=frame)
    target_ref = None if target_qualname is None else parse_ref(target_qualname)

    ovr_value = Unassigned
    if (
        target_ref is not None  # Is None if target is inaccesible due to a promotion
        and (
            _ovr := checked_get_single(
                filter(
                    lambda x: x.target == target_ref,
                    get_global_loader().package_overrides[infer_solconf_package()],
                ),
                raise_empty=False,
            )
        )
        is not NoItem
    ):
        # Get the override value
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
