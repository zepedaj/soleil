import abc
from typing import Dict, Any, List, Set, Type
from numbers import Number
from pglib.py import entity_name
from .modifiers import Modifiers

__registered_resolvers__: Set[Type["Resolver"]] = set()


class ResolutionError(Exception):
    def __init__(self, error_location: List[str]):
        super().__init__(
            f'The above error occurred during the following nested resolution: `{"`, `".join(error_location) }`'
        )


class Resolver(abc.ABC):
    resolvable: Any
    members: Dict[str, Any]
    modifiers: Dict[str, Any]

    def __init__(self, resolvable):
        self.resolvable = resolvable

    def __init_subclass__(cls):
        __registered_resolvers__.add(cls)

    @classmethod
    @abc.abstractmethod
    def can_handle(cls, resolvable):
        ...

    def resolve(self):
        if "__soleil_resolved__" not in vars(self.resolvable):
            self.resolvable.__soleil_resolved__ = self.compute_resolved()
        return self.resolvable.__soleil_resolved__

    @abc.abstractmethod
    def compute_resolved(self):
        ...

    def displayable(self):
        """
        Returns a displayable representation of the resolvable consisting of only base types
        """
        if self.resolvable.__str__ is not object.__str__:
            return f"{entity_name(type(self.resolvable))}<{str(self.resolvable)}>"
        else:
            return str(self.resolvable)


class NonCachedResolver(Resolver):
    def resolve(self):
        return self.compute_resolved()


class FirstResolver(NonCachedResolver):
    @classmethod
    def can_handle(cls, resolvable):
        # None
        return resolvable is None or isinstance(
            resolvable, (Number, str, bytes, Modifiers)
        )

    def compute_resolved(self):
        return self.resolvable

    def displayable(self):
        return self.resolvable


class DictResolver(NonCachedResolver):
    # resolved = {}

    @classmethod
    def can_handle(cls, resolvable):
        return isinstance(resolvable, dict)

    def compute_resolved(self):
        return {resolve(key): resolve(value) for key, value in self.resolvable.items()}

    def displayable(self):
        # TODO: will produce incomplete results if displayables for some keys are the same
        return {
            displayable(key): displayable(value)
            for key, value in self.resolvable.items()
        }


class IterableResolver(NonCachedResolver):
    iterable_types = (list, tuple, set)

    @classmethod
    def can_handle(cls, resolvable):
        return isinstance(resolvable, cls.iterable_types)

    def compute_resolved(self):
        return type(self.resolvable)(resolve(value) for value in self.resolvable)

    def displayable(self):
        return type(self.resolvable)(displayable(value) for value in self.resolvable)


def get_resolver(value):
    """
    Checks if the input value can be resolved and returns the resolver or ``None`` otherwise.
    """
    # Registered resolvers
    for Rslvr in __registered_resolvers__:
        if Rslvr.can_handle(value):
            return Rslvr(value)

    # raise ValueError(f"No resolver available for {value}.")
    return None


def resolve(value):
    """
    Find a matching resolver and returns the resolved value.
    """
    __soleil_nested_resolve__ = None  # Marker used to detect nested resolve calls

    if (resolver := get_resolver(value)) is not None:
        try:
            return resolver.resolve()
        except Exception as err:
            import inspect

            stack = inspect.stack()
            if isinstance(err, ResolutionError):
                raise
            else:
                raise ResolutionError(
                    [
                        str(f.frame.f_locals["value"])
                        for f in stack
                        if "__soleil_nested_resolve__" in f.frame.f_locals
                    ]
                ) from err
    else:
        return value


def displayable(value):
    """
    Find a matching resolver and returns the displayable for the input.
    """
    if (resolver := get_resolver(value)) is not None:
        return resolver.displayable()
    else:
        return str(value)
