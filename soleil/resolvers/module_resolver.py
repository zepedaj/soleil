from importlib import import_module
from pathlib import Path
import re
from types import MappingProxyType, ModuleType
from typing import TYPE_CHECKING, Callable, List, Optional, Set
from numpy.testing._private.utils import partial

from pglib.validation import checked_get_single
from soleil.resolvers.modifiers import Modifiers
from .class_resolver import ClassResolver
from .base import resolve as call_resolve, _UNRESOLVED
from .._utils import Unassigned, abs_mod_name

if TYPE_CHECKING:
    from soleil.loader.loader import ConfigLoader


as_run = Modifiers(as_run=True)
""" Annotates a callable (or the fully qualified name of one) that solex will run on the resolved module """


class SolConfModule(type):
    """Soleil configuration modules will be of this type."""

    __soleil_default_hidden_members__: Set[str]
    """ Members that default to hidden. They can be made visible with an explicit `visible` annotation """

    __file__: Path
    """ The module file path """

    __name__: str
    """ The module name """

    @property
    def __package_name__(self):
        return __name__.split(".")[0]

    def __new__(cls, name, bases=None, members=None):
        return super().__new__(cls, name, bases or tuple(), members or {})

    def init_as_module(self, name: str, filepath: Path, reqs=None):
        self.__name__ = name
        self.__file__ = filepath

        # Inject all members of soleil.injected module
        for attr in (injected := import_module("soleil.injected")).__all__:
            setattr(self, attr, getattr(injected, attr))
        self.__soleil_default_hidden_members__ = set(injected.__all__)

        # Add load method
        for method in ["load", "submodule"]:
            setattr(self, method, getattr(self, method))
            self.__soleil_default_hidden_members__.add(method)

        # Add required var values
        for name, val in (reqs or {}).items():
            setattr(self, name, val)

    def load(self, module_name, promoted=True, resolve=False):
        """
        Loads a module by relative name. Names with leading dots are interepreted relative to this module. Names with no leading dots are
        interpreted relative to the parent package.

        If the loaded module contains a promoted member, that member is returned by default.

        :param module_name: The relative or absolute (without package name) module name.
        :param promoted: Whether the return the promoted member, if it exists, otherwise (or if ``promoted=False``) the full module.
        """
        #

        # Get an absolute module name
        if module_name[0] != ".":
            module_name = self.__package_name__ + module_name
        module_name = abs_mod_name(self.__name__, module_name)

        # Load the module using the global loader
        from soleil.loader import GLOBAL_LOADER

        module = GLOBAL_LOADER.load(module_name, resolve=resolve, promoted=promoted)

        return module

    def submodule(self, sub_package_name, sub_module_name, /, **kwargs):
        return self.load(f"{sub_package_name}.{sub_module_name}", **kwargs)

    def __str__(self):
        return f"<solconf module '{self.__name__}' from '{str(Path(self.__file__).absolute()) if self.__file__ else '<unknown>'}'>"

    def __repr__(self):
        return str(self)


promoted = Modifiers(promoted=True)
unpromoted = Modifiers(promoted=False)


class ModuleResolver(ClassResolver):
    resolvable: SolConfModule
    valid_modifier_keys = frozenset(
        {*ClassResolver.valid_modifier_keys, "promoted", "as_run"}
    )
    special_members = MappingProxyType(
        {**ClassResolver.special_members, "run": "as_run", "promoted": "promoted"}
    )

    run: Optional[Callable] = None
    """ The callable that :func:`solex` calls on the resolved module by default """

    promoted = Unassigned
    """ The promoted member """

    def compute_resolved(self):
        """
        If no ``as_type`` member is provided, applies the following resolution:

        If a single variable is explicitly promoted, resolves to that variable.
        Otherwise, resolves to a dictionary with all visible members resolved.
        """

        if self.type is not None:
            return super().compute_resolved()
        else:
            if self.promoted is not Unassigned:
                # A variable is promoted
                return call_resolve(self.promoted)
            else:
                # Use user-provided names if any.
                return {
                    self.modifiers[key].get("name", key): call_resolve(value)
                    for key, value in self.members.items()
                }

    @classmethod
    def can_handle(cls, value):
        return isinstance(value, SolConfModule)
