from typing import Tuple, Union, Any

from soleil.resolvers.base import TypeResolver, resolve


class RStr:
    """Supports late-evaluated strings that are computed at resolution time"""

    _components: Tuple[Any]
    """A tuple :class:`RStr` objects or string-convertibles"""

    def __init__(self, components: Tuple = tuple()):
        self._components = components

    def __add__(self, x: Any):
        return RStr((*self._components, x))

    def __radd__(self, x):
        return RStr((x, *self._components))

    def __truediv__(self, x):
        return RStr((*self._components, "/", x))

    def __rtruediv__(self, x):
        return RStr((x, "/", *self._components))

    def compute_resolved(self):
        return "".join(
            x.compute_resolved() if isinstance(x, RStr) else str(resolve(x))
            for x in self._components
        )

    def __str__(self):
        raise SyntaxError(
            "Objects of type ``RStr`` must be resolved to be converted to their string representation"
        )


class RStrResolver(TypeResolver, handled_type=RStr):
    def compute_resolved(self):
        return self.resolvable.compute_resolved()
