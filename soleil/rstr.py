from typing import Tuple, Union, Any

from soleil.resolvers.base import TypeResolver


class RStr:
    """Supports late-evaluated strings that are computed at resolution time"""

    components: Tuple
    """A tuple of anything that can be converted to a string"""

    def __init__(self, components: Tuple = tuple()):
        self.components = components

    def __add__(self, x: Any):
        return RStr((self, x))

    def __radd__(self, x):
        return RStr((x, self))

    def __truediv__(self, x):
        return RStr((self, "/", x))

    def __rtruediv__(self, x):
        return RStr((x, "/", self))

    def to_str(self):
        return "".join(
            x.to_str() if isinstance(x, RStr) else str(x) for x in self.components
        )

    def __str__(self):
        raise SyntaxError(
            "Objects of type ``RStr`` must be resolved to be converted to their string representation"
        )


class RStrResolver(TypeResolver, handled_type=RStr):
    def compute_resolved(self):
        return self.resolvable.to_str()
