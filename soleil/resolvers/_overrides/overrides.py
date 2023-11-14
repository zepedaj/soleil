import inspect
from typing import Any, Dict, List, Union
from pglib.validation import NoItem, checked_get_single
from soleil._utils import Unassigned, infer_solconf_package

from .parser import Override, OverrideType, Ref, parse_overrides, parse_ref
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

    @classmethod
    def from_override(
        cls, ovr: Override, globals_: dict, locals_: dict
    ) -> "PreCompOverride":
        return cls(
            ovr.target, ovr.assign_type, ovr.get_value(globals_, locals_), ovr.used
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


def deduce_soleil_qualname(target_name, f_back=None):
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
        fxn(deduce_soleil_qualname('b') == 'a.b') # Is True, must be called within a function `fxn` such as override() or load()

    """
    from soleil.loader.loader import GLOBAL_LOADER  # TODO: Slow - load at global level

    f_back = f_back or inspect.currentframe().f_back.f_back

    module_name = f_back.f_globals["__soleil_qualname__"]
    promoted_name = GLOBAL_LOADER.modules[
        f_back.f_globals["__soleil_module__"]
    ].get_promoted_name()
    class_name = f_back.f_locals.get("__qualname__", None)

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


def override(target_name, value):
    """
    Returns the assigned value or an override if any was specified.
    """
    from soleil.loader.loader import GLOBAL_LOADER  # TODO: Slow - load at global level

    target_name = deduce_soleil_qualname(target_name)
    target_ref = parse_ref(target_name)

    if (
        _ovr := checked_get_single(
            filter(
                lambda x: x.target == target_ref,
                GLOBAL_LOADER.package_overrides[infer_solconf_package()],
            ),
            raise_empty=False,
        )
    ) is NoItem:
        return value
    else:
        return _ovr.get_value()
