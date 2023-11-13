from dataclasses import dataclass
import operator
from typing import Any, Callable, Dict, Tuple, Type, Union
from soleil._utils import infer_solconf_module
from soleil.loader.loader import GLOBAL_LOADER
from soleil.resolvers.base import TypeResolver, resolve


# Add  operator support to ref and call instances
class _operator_support:
    pass


for name in [
    "abs",
    "add",
    "floordiv",
    "mod",
    "mul",
    "neg",
    "pos",
    "pow",
    "sub",
    "truediv",
]:
    setattr(
        _operator_support,
        f"__{name}__",
        lambda self, *args, name=name: call(getattr(operator, name), self, *args),
    )


class ref:
    """
    Used to reference a variable with a value that might be modified (e.g., by CLI overrides).
    The standard python variable referencing rules apply:

    .. code-block::

        # Module *.solconf

        x = ref('a') # Fails because 'a' is not defined yet
        a = 1
        b = ref('a') # Resolves to global `a`

        class A:
            a = ref('a') + 1 # ref('a') resolves to global `a` of value `1`
            a2 = ref('a') # resolves to to the local `a` of value `2`
            b = ref('b') # ref('a') resolves to the resolution of global b which is `1`
            c = ref('z') # Fails since no local or global variable `z` exists.

    """

    def __init__(self, var_name):
        #
        soleil_module_name, f_back = infer_solconf_module()
        self.soleil_module = GLOBAL_LOADER.load(
            soleil_module_name, resolve=False, promoted=False
        )
        self.class_qual_name = f_back.f_locals.get(
            "__qualname__", None
        )  # Will be None for solconf modules
        self.locals_snapshot = tuple(
            f_back.f_locals
        )  # The local vars that exist at the point of this ref defintion
        self.var_name = var_name

        # Check that var_name is defined at this point
        if (
            var_name not in self.locals_snapshot
            and not var_name in self.soleil_module.__soleil_globals__
        ):
            raise NameError(f"name '{var_name}' is not defined")


class RefResolver(TypeResolver, handled_type=ref):
    def compute_resolved(self):
        module = self.resolvable.soleil_module
        obj = module

        # Resolve reference string obj = A.b.c.d
        for member in (
            self.resolvable.class_qual_name.split(".")
            if self.resolvable.class_qual_name
            else []
        ):
            obj = getattr(obj, member)

        # Resolve class-local variable obj = A.b.c.d.var
        if self.resolvable.var_name in self.resolvable.locals_snapshot:
            # Class-local variable
            obj = getattr(obj, self.resolvable.var_name)

        elif hasattr(module, self.resolvable.var_name):
            # Module-level variable
            obj = getattr(module, self.resolvable.var_name)
        else:
            # Could not resolve
            raise ValueError(
                f"Could not resolve reference `{self.resolvable.var_name}` "
                + (
                    ""
                    if self.resolvable.class_qual_name is None
                    else f"within class `{self.resolvable.class_qual_name}` "
                )
                + f"in module `{self.resolvable.soleil_module}`"
            )

        return resolve(obj)


class call:
    """Represents a call to a resolvable applied to resolvable parameters"""

    # TODO: Resolvables of these types are also accepted. Reflect this in the types using, e.g., fxn:Resolvable[Union[Callable, Type]]
    fxn: Union[Callable, Type]
    args: Tuple[Any, ...]
    kwargs: Dict[str, Any]

    def __init__(self, fxn, *args, **kwargs):
        self.fxn = fxn
        self.args = args
        self.kwargs = kwargs


class CallResolver(TypeResolver, handled_type=call):
    def compute_resolved(self):
        args = [resolve(x) for x in self.resolvable.args]
        kwargs = {
            resolve(key): resolve(value)
            for key, value in self.resolvable.kwargs.items()
        }
        fxn = resolve(self.resolvable.fxn)

        return fxn(*args, **kwargs)
