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

from soleil.resolvers.modifiers import Modifiers, from_annotation

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

    .. warning::

        The ``get_*`` methods will only work once all the modules nested in the root config and have been loaded --
        i.e., after the root config is loaded. In practice, this means that they should only be called as part of
        member resolution.

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

        return self.get_with_container(obj)[0]

    def get_module(self, obj=Unassigned):
        """Returns the module containing the variable where the variable path points to"""
        from soleil.resolvers.module_resolver import SolConfModule

        _, container = self.get_with_container(obj)
        if not isinstance(container, SolConfModule):
            return get_global_loader().modules[container.__module__]
        else:
            return container

    def get_modifiers(self, obj=Unassigned):
        """
        Returns the explicit modifiers for the referenced variable or ``None`` if none are specified
        """
        ## TODO: Use the modifiers from the pre-processor
        obj, container = self.get_with_container(obj)
        if container is None:
            raise ValueError("Root objects have no modifiers -- only their members do")
        if isinstance(self[-1], Subscript):
            raise NotImplementedError(
                "Getting modifiers of a subscripted item not currently supported"
            )
        return from_annotation(
            getattr(container, "__annotations__", {}).get(self[-1].name, None)
        )

    def get_with_container(self, obj=Unassigned):
        """
        Returns a tuple with the referenced  object and its container (either a class or a solconf object) of the variable pointed to by the path. If the path points to the root, then ``None`` is returned.
        Note that the parent of a promoted member is its solconf module (promoted members can only exist at the global level within a solconf module).
        """

        from soleil.resolvers.module_resolver import (
            SolConfModule,
        )  # TODO: Finad another way to break circular imports

        if obj is Unassigned:
            obj = infer_root_config()

        container = None
        ref_iter = iter(self)

        while True:
            if isinstance(obj, SolConfModule) and (
                promoted_name := obj.__soleil_pp_meta__["promoted"]
            ):
                container = obj
                obj = getattr(obj, promoted_name)
            try:
                _ref = next(ref_iter)
            except StopIteration:
                break
            container = obj
            obj = _ref.get(obj)

        return obj, container

    @classmethod
    def from_str(cls, value: str):
        from .parser import parse_ref

        return parse_ref(value)

    def as_str(self):
        out = ""
        for _ref in self:
            if isinstance(_ref, Attribute):
                if out:
                    out += f".{_ref.name}"
                else:
                    out = _ref.name
            elif isinstance(_ref, Subscript):
                out += f"[{_ref.value}]"

        return out


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
        get_global_loader()
        .modules[frame.f_globals["__name__"]]
        .__soleil_pp_meta__["promoted"]
        or ""
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
