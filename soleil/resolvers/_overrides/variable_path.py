from collections import UserList
from dataclasses import dataclass
from typing import Any
from soleil._utils import Unassigned
import abc


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


class VariablePath(UserList):
    """
    Contains a sequence of references relative to the root configuration that point to a variable.
    """

    # TODO: Support for subscripts needs work

    def get(self, obj=Unassigned):
        """Applies the get methods of a a sequence of refs to the root config or the specified object"""

        if obj is Unassigned:
            obj = deduce_root()

        for _ref in self:
            obj = _ref.get(obj)
            return obj

    def get_modifiers(self):
        pass
