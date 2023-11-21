from collections import UserList
from dataclasses import dataclass
from types import FrameType
from typing import Any, Optional, Union
from soleil._utils import (
    Unassigned,
    infer_root_config,
    get_caller_frame,
    get_global_loader,
)
import abc

CompoundRefStr = str
"""
A reference string such as ``'a[0].b.c[0]'`` that can be converted to a :class:`VarPath`
"""


class Ref(abc.ABC):
    @abc.abstractmethod
    def get(self, obj):
        ...

    @abc.abstractmethod
    def set(self, obj, value):
        ...


@dataclass
class Attribute(Ref):
    name: str

    def get(self, obj):
        return getattr(obj, self.name)

    def set(self, obj, value):
        return setattr(obj, self.name, value)


@dataclass
class Subscript(Ref):
    value: Any = Unassigned

    def get(self, obj):
        return obj.__getitem__(self.value)

    def set(self, obj, value):
        obj.__setitem__(self.value, value)


class VarPath(UserList):
    """
    Contains a sequence of references relative to the root configuration that point to a variable.
    """

    # TODO: Support for subscripts needs work

    def _check_entry(self, entry):
        if not isinstance(entry, Ref):
            raise ValueError(f"All entries of {VarPath} must be sub-types of {Ref}")
        return entry

    def append(self, entry):
        super().append(self._check_entry(entry))

    def get(self, obj=Unassigned):
        """Applies the get methods of a a sequence of refs to the root config or the specified object"""

        from soleil.resolvers.module_resolver import (
            SolConfModule,
        )  # TODO: Breaks circular imports

        if obj is Unassigned:
            obj = infer_root_config()

        # Skip to promoted
        if obj.__pp_promoted__:
            obj = getattr(obj, obj.__pp_promoted__)

        for _ref in self:
            obj = _ref.get(obj)
            if isinstance(obj, SolConfModule) and obj.__pp_promoted__:
                # Skip to promoted
                obj = getattr(obj, obj.__pp_promoted__)

        return obj

    def get_modifiers(self):
        pass

    @classmethod
    def from_str(cls, value: str):
        from .parser import parse_ref

        return parse_ref(value)


def deduce_soleil_var_path(
    target_name: str, frame: Union[FrameType, int, None] = 0
) -> Optional[VarPath]:
    """
    Returns a :class:`VarPath` specifying how to access a variable named ``target_name`` defined in the specified frame relative to the root configuration.
    Will return ``None`` if the variable is not visible (e.g., it is promoted, and hence its name is not accessible)

    :param target_name: The name of the variable whose name is being deduced.
    :param frame: The frame where the variable named ``target_name`` is being defined -- by default assumed to be the the parent frame of the caller,
    since ``deduce_soleil_var_path`` is usually called within :func:`_soleil_overrides` or :func:``.

    Example:

    .. test-code::

        # main.solconf
        assert __soleil_var_path__ == VarPath() # Is True (this is the root config)
        a = load('module2') # Will propagate 'a' as the module's __soleil_var_path__

        # module2.solconf
        assert __soleil_var_path__ == 'a' # Is True
        b = 1
        deduce_soleil_var_path('b', -1) == 'a.b' # Is True, -1 bc usuallly called within a function `fxn` such as override() or load()

    """

    # Get the frame two levels up by default -- one frame for this call, and one frame for the call within the containing module.
    if not isinstance(frame, FrameType):
        frame = get_caller_frame((frame or 0) + 2)

    # The variable path of the module
    module_var_path = frame.f_globals["__soleil_var_path__"]
    # The name of the promoted variable as a variable path
    promoted_rel_var_path = VarPath.from_str(
        get_global_loader().modules[frame.f_globals["__name__"]].__pp_promoted__ or ""
    )
    # The (nested) path to the (nested) variable relative to the containing module
    class_rel_var_path = VarPath.from_str(frame.f_locals.get("__qualname__", ""))

    if promoted_rel_var_path:
        if not class_rel_var_path or (promoted_rel_var_path != class_rel_var_path[:1]):
            # When a var is promoted, cannot access any global-level vars (including the promoted one) --
            # only the members of the promoted var are accessible.
            return None
        else:
            # The target_name is contained (possibly with nesting) within the promoted variable
            return module_var_path + class_rel_var_path[1:] + [Attribute(target_name)]
    else:
        return module_var_path + class_rel_var_path + [Attribute(target_name)]
