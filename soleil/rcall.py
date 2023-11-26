from typing import Any, Callable
from soleil import resolve
from soleil.resolvers.base import TypeResolver


class rcall:
    def __init__(self, fxn: Callable, *args: Any, **kwargs: Any):
        self.fxn = fxn
        self.args = args
        self.kwargs = kwargs

    def __call__(self):
        """Resolves the arguments and fxn and makes the call"""

        return resolve(self.fxn)(
            *[resolve(_x) for _x in self.args],
            **{key: resolve(val) for key, val in self.kwargs.items()}
        )


class RCallResolver(TypeResolver, handled_type=rcall):
    def compute_resolved(self):
        return self.resolvable()
