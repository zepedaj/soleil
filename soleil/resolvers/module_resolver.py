from importlib import import_module
from pglib.validation import NoItem, checked_get_single
from pathlib import Path
from types import FrameType, MappingProxyType, ModuleType
from typing import Callable, Optional, Set, Union
from soleil.resolvers._overrides.overrides import deduce_soleil_qualname
from soleil.resolvers.modifiers import Modifiers
from .class_resolver import ClassResolver
from .base import resolve as call_resolve
from .._utils import Unassigned, abs_mod_name


as_run = Modifiers(as_run=True)
""" Annotates a callable (or the fully qualified name of one) that solex will run on the resolved module """


class SolConfModule(ModuleType):
    """Soleil configuration modules will be of this type."""

    __is_soleil_module__: bool
    """ Marker to detect soleil modules """

    __name__: str
    """ The qualified name of the module, including package name """

    __package__: str
    """ The name of the soleil package -- usually a random string """

    __file__: Path
    """ The module file path """

    __soleil_qualname__: Optional[str]
    """ The variable/attribute name sequence to access this module from to the root module, will be ``None`` for the root module"""

    __soleil_default_hidden_members__: Set[str]
    """ Members that default to hidden. They can be made visible with an explicit `visible` annotation """

    def __init__(
        self,
        soleil_module: str,
        soleil_path: Path,
        soleil_qualname: Optional[str] = None,
    ):
        #
        self.__is_soleil_module__ = True
        self.__name__ = soleil_module
        self.__package__ = soleil_module.split(".")[0]
        self.__file__ = soleil_path
        self.__soleil_qualname__ = soleil_qualname

        # Inject all members of soleil.injected module
        for attr in (injected := import_module("soleil.injected")).__all__:
            setattr(self, attr, getattr(injected, attr))
        self.__soleil_default_hidden_members__ = set(injected.__all__)

        # Add load method
        for method in ["load", "submodule"]:
            setattr(self, method, getattr(self, method))
            self.__soleil_default_hidden_members__.add(method)

    def load(
        self,
        module_name,
        promoted=True,
        resolve=False,
        _target: Optional[str] = None,
        _frame: Optional[Union[FrameType, int]] = 0,
        **kwargs,
    ):
        """
        Loads a module by relative name. Names with leading dots are interepreted relative to this module. Names with no leading dots are
        interpreted relative to the parent package.

        If the loaded module contains a promoted member, that member is returned by default.

        :param module_name: The relative or absolute (without package name) module name.
        :param promoted: Whether the return the promoted member, if it exists, otherwise (or if ``promoted=False``) the full module.
        """
        # NOTE: Parameter ``_target`` will be set by the pre-processor in simple load assignments, e.g.
        #   a = load('.sub.module')          # load('.sub.module', _target='a')
        #   b = submodule('.sub', 'module')  # submodule('.sub', 'module', _target='b')
        #
        #   _target will be ``None`` e.g., when using load(...) as an argument for a class inheritance: class A(load('.B')): pass

        # Build the soleil qualname of the module
        _qualname = (
            None if _target is None else deduce_soleil_qualname(_target, frame=_frame)
        )

        # Get an absolute module name
        if module_name[0] != ".":
            module_name = ".".join([self.__package__, module_name])
        module_name = abs_mod_name(self.__name__, module_name)

        # Load the module using the global loader
        from soleil.loader import GLOBAL_LOADER

        module = GLOBAL_LOADER.load(
            module_name,
            resolve=resolve,
            promoted=promoted,
            _qualname=_qualname,
            **kwargs,
        )

        return module

    def get_promoted_name(self) -> Optional[str]:
        """
        Checks the module's ``__annotations__`` to see which variable is promoted
        """
        # TODO: This is required to support override name propagation. For names
        # to propagate correctly through promoted members, the promoted member needs to
        # be defined at the top of the module file.
        if not (anns := getattr(self, "__annotations__", None)):
            return None
        else:
            if (
                pair := checked_get_single(
                    filter(
                        lambda x: (
                            x is promoted or isinstance(x, tuple) and promoted in x
                        ),
                        anns.items(),
                    ),
                    msg=lambda self=self: f"Multiple promoted members found in solconf module {self}.",
                    raise_empty=False,
                )
            ) is NoItem:
                return None
            else:
                return pair[0]

    def __str__(self):
        return f"<solconf module '{self.__name__}' from '{str(self.__file__.absolute()) if self.__file__ else '<unknown>'}'>"

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

    def _get_raw_members(self):
        return dict(vars(self.resolvable))

    def _get_raw_annotations(self):
        return dict(vars(self.resolvable).get("__annotations__", {}))
