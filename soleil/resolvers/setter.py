import abc
from typing import Optional, Set, Type

__registered_setters__: Set[Type["Setter"]] = set()


class Setter(abc.ABC):
    """Members that can be set in a special way"""

    def __init_subclass__(cls):
        __registered_setters__.add(cls)

    @classmethod
    @abc.abstractmethod
    def can_handle(cls, value):
        ...

    @classmethod
    @abc.abstractmethod
    def set(cls, current_value, new_value):
        ...


def get_setter(settable) -> Optional[Setter]:
    for setter in __registered_setters__:
        if setter.can_handle(settable):
            return setter
