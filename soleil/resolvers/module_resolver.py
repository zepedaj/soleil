from pathlib import Path
from types import FrameType, MappingProxyType, ModuleType
from typing import Callable, Dict, Optional, Set, Union, List
from soleil.overrides.overrides import (
    OverrideSpec,
    deduce_soleil_var_path,
    _soleil_override,
    eval_overrides,
)
from soleil.overrides.parser import Override
from soleil.overrides.variable_path import VarPath
from soleil.resolvers.modifiers import Modifiers
from .class_resolver import ClassResolver
from .base import resolve as call_resolve
from .._utils import Unassigned, abs_mod_name, get_global_loader


as_run = Modifiers(as_run=True)
""" Indicates that the annotated member is a callable that :func:`solex` will run on the module """

promoted = Modifiers(promoted=True)
"""
When a module's member is annotated as promoted it will be returned when that module is loaded without resolving. Accordingly, the module will also resolve to the resolution of that member.
When a member in a module is marked as promoted, all other members in the module no longer have a variable path, since the module's variable path becomes the promoted member's variable path.
Hence, no other members can be overriden by CLI overrides.

Modifier :attr:`promoted` is special because it also operates as a pre-processor directive. The reason is that correct dereferencing of
CLI overrides in modules with promoted members requires knowing the name of the promoted member before executing the code.
"""

resolves = Modifiers(resolves=True)
"""
When a module's member is annotated as ``resolves``, the module will resolve to the resolution of that member. Unlike :attr:`promoted` members,
loading a module (without resolving) containing a ``resolves``-annoted member will still produce that module.
"""


class SolConfModule(ModuleType):
    """The class used to represent `*.solconf` modules."""

    __is_solconf_module__: bool
    """ Marker to detect soleil modules """

    __name__: str
    """ The qualified name of the module, including package name """

    __package__: str
    """ The name of the soleil package -- usually a random string """

    __file__: Path
    """ The module file path """

    __soleil_var_path__: VarPath
    """ The variable/attribute name sequence to access this module from to the root module, will be ``None`` for the root module"""

    __soleil_default_hidden_members__: Set[str]
    """ Members that default to hidden. They can be made visible with an explicit `visible` annotation """

    __soleil_pp_meta__: Dict
    """ Pro-processor-extracted meta-data, including the promoted member name (key ``'promoted'``)"""

    __soleil_root_config__: Optional["SolConfModule"]
    """ The root configuration of the module -- will be ``None`` if this module is the root config """

    __soleil_reqs__: List[Override]
    """ Contains values to supply to :class:`req` members by default """

    def __init__(
        self,
        soleil_module: str,
        soleil_path: Path,
        soleil_var_path: Optional[Union[VarPath, str]] = None,
        soleil_reqs: Optional[List[Override]] = None,
        root_config: Optional["SolConfModule"] = None,
    ):
        #
        self.__soleil_pp_meta__ = {}
        self.__is_solconf_module__ = True
        self.__name__ = soleil_module
        self.__package__ = soleil_module.split(".")[0]
        self.__file__ = soleil_path
        self.__soleil_var_path__ = (
            VarPath()
            if not soleil_var_path
            else soleil_var_path
            if isinstance(soleil_var_path, VarPath)
            else VarPath.from_str(soleil_var_path)
        )
        self.__annotations__ = {}  # Clears class-level annotations

        # Inject all members of soleil.injected module
        self.__soleil_default_hidden_members__ = set()

        # Add load method
        for method in ["load"]:
            setattr(self, method, getattr(self, method))
            self.__soleil_default_hidden_members__.add(method)

        # Inject _soleil_override
        self._soleil_override = _soleil_override
        self.__soleil_default_hidden_members__.add("_soleil_override")

        # Add root config
        self.__soleil_root_config__ = root_config

        self.__soleil_reqs__ = soleil_reqs or []

    def load(
        self,
        module_name,
        promoted=True,
        resolve=False,
        reqs: Optional[List[OverrideSpec]] = None,
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
        :param resolve: Whether to resolve the module.
        :param reqs: Default values for :class:`req` members.
        """
        # NOTE: Parameter ``_target`` will be set by the pre-processor in simple load assignments, e.g.
        #   a = load('.sub.module')          # load('.sub.module', _target='a')
        #   b = submodule('.sub', 'module')  # submodule('.sub', 'module', _target='b')
        #
        #   _target will be ``None`` e.g., when using load(...) as an argument for a class inheritance: class A(load('.B')): pass

        # Build the soleil var_path of the module
        _var_path = (
            None if _target is None else deduce_soleil_var_path(_target, frame=_frame)
        )

        # Get an absolute module name
        if module_name[0] != ".":
            module_name = ".".join([self.__package__, module_name])
        module_name = abs_mod_name(self.__name__, module_name)

        # Load the module using the global loader
        module = get_global_loader().load(
            module_name,
            resolve=resolve,
            promoted=promoted,
            reqs=reqs,
            _var_path=_var_path,
            _root_config=(self.__soleil_root_config__ or self),
            **kwargs,
        )

        return module

    def __str__(self):
        return f"<solconf module '{self.__name__}' from '{str(self.__file__.absolute()) if self.__file__ else '<unknown>'}'>"

    def __repr__(self):
        return str(self)


class ModuleResolver(ClassResolver):
    resolvable: SolConfModule
    valid_modifier_keys = frozenset(
        {*ClassResolver.valid_modifier_keys, "promoted", "resolves"}
    )
    special_members = MappingProxyType(
        {
            **ClassResolver.special_members,
            "promoted": "promoted",
            "resolves": "resolves",
        }
    )

    promoted = Unassigned
    """ The promoted member """

    resolves = Unassigned
    """ The member that the module resolves to. Modules must have at most one resolved or promoted member. """

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
            elif self.resolves is not Unassigned:
                return call_resolve(self.resolves)
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

    def _get_members_and_modifiers(self):
        super()._get_members_and_modifiers()
        if self.resolves is not Unassigned and self.promoted is not Unassigned:
            raise ValueError(
                "Solconf modules cannot have both `promoted` and `resolves` members"
            )
