from importlib import import_module
from pathlib import Path
import re
from types import MappingProxyType, ModuleType
from typing import TYPE_CHECKING, Callable, List, Optional, Set
from numpy.testing._private.utils import partial

from pglib.validation import checked_get_single
from soleil.resolvers.modifiers import Modifiers
from .class_resolver import ClassResolver
from .base import resolve

if TYPE_CHECKING:
    from soleil.loader.loader import ConfigLoader


as_run = Modifiers(as_run=True)
""" Modifier that indicates the default callable that solex will run on the resolved module """


class SolConfModule(ModuleType):
    """Soleil configuration modules will be of this type."""

    __soleil_default_hidden_members__: Set[str]
    """ Members that default to hidden. They can be made visible with an explicit `visible` annotation """

    __soleil_loader__: "ConfigLoader"
    """ The loader used to load this module """

    def __init__(self, *args, loader, reqs=None, **kwargs):
        # Set the loader
        self.__soleil_loader__ = loader

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

        # Super init
        super().__init__(*args, **kwargs)

    def load(self, module_name, reqs=None, **kwargs):
        """
        :param module_name: The name of the module to load. Relative names (with leading dots, e.g., ``'.submod1.submod2'``) are interpreted relative to this module.
        Absolute names (with no leading dots, e.g., ``'submod1.submod2'``) are interpreted relative to the package root.
        """

        # Get the root, submods and preceding dots
        matched = re.fullmatch(r"(?P<dots>\.*)(?P<submods>(\w+\.)*\w+)", module_name)
        parts = matched.groupdict() if matched else {}
        if not matched or not (
            root := ".".join(  # If empty, more dots than up levels
                vars(self)["__name__"].split(".", -1)[: -len(parts["dots"]) or None]
            )
        ):
            raise ValueError(f"Invalid module name `{module_name}`")
        elif not parts["dots"]:
            root = vars(self)["__name__"].split(".")[0]

        # Get the load target
        load_target = f'{root}.{parts["submods"]}'

        #
        return self.__soleil_loader__.load(
            load_target, reqs=reqs, resolve=False, **kwargs
        )

    def submodule(self, sub_package_name, sub_module_name, /, **kwargs):
        return self.load(f"{sub_package_name}.{sub_module_name}", **kwargs)

    def __getitem__(self, k):
        """
        Supports accessing entries of a promoted but non-yet-resolved component of a module
        """
        if promoted_key := ModuleResolver(self)._get_promoted_member_name():
            return getattr(self, promoted_key)[k]
        else:
            raise Exception(
                f"{type(self).__name__} with no promoted type is not subscriptable"
            )

    def __str__(self):
        return f"<solconf module '{self.__name__}' from '{str(Path(self.__file__).absolute()) if self.__file__ else '<unknown>'}'>"

    def __repr__(self):
        return str(self)

    def __setattr__(self, __name: str, __value) -> None:
        if hasattr(self, "__soleil_resolved__"):
            # Unexpected results would occur because Resolver.resolve() results are cached.
            # This can be avoided by calling Resolver.compute_resolved() from resolve every time,
            # but then objects do not resolve to the same resolved object, breaking down reference expectaions.
            # This warning applies to modifications of any resolvable, but currently only SolConfModule
            # is checked
            raise Exception(
                "Setting attributes after resolution will produce unexpected results!"
            )
        return super().__setattr__(__name, __value)


promoted = Modifiers(promoted=True)
unpromoted = Modifiers(promoted=False)


class ModuleResolver(ClassResolver):
    resolvable: SolConfModule
    valid_modifier_keys = frozenset(
        {*ClassResolver.valid_modifier_keys, "promoted", "as_run"}
    )
    special_members = MappingProxyType(
        {**ClassResolver.special_members, "run": "as_run"}
    )

    run: Optional[Callable] = None
    """ The callable that :func:`solex` calls on the resolved module by default """

    def _get_members_and_modifiers(self):
        super()._get_members_and_modifiers()

        # Check at most one promoted
        promoted = [
            name
            for name, value in self.modifiers.items()
            if value.get("promoted", False)
        ]
        if len(promoted) > 1:
            raise ValueError(
                f"At most one module variable can be promoted, but found {len(promoted)} ({promoted}) for resolvable {self.resolvable}"
            )

    def _get_promoted_member_name(self) -> Optional[str]:
        promotions = {
            key: self.modifiers[key].get("promoted", None) for key in self.members
        }
        if promoted_key := [key for key, val in promotions.items() if val is True]:
            # One Resolvable is explicitly promoted.
            return checked_get_single(promoted_key)
        elif len(self.members) == 1 and next(iter(promotions.values())) is None:
            # One Resolvable is implicitly promoted.
            return next(iter(self.members.keys()))
        else:
            return None

    def default_module_type(self, **kwargs):
        """

        * promote: ``True``: Promote always (at most one :class:`Resolvable` in the module can have this set). ``False``: All :class:`Resolvables` will be returned as a dictionary. None [default]: Promote if single-non-hidden-:class:`Resolvables` module, don't promote otherwise.

        If a single variable is explicitly promoted in the module or if there is a single variable that without an explicit ``promote(False)`` modifier, resolves to that variable.
        Otherwise, resolves to a dictionary with all resolved module variables.
        """

        resolved = {name: resolve(value) for name, value in self.members.items()}

        if promoted_key := self._get_promoted_member_name():
            # One member is promoted, return it
            return resolved[promoted_key]
        else:
            # Return all resolved non-hidden members as a dictionary

            # Use user-provided names if any.
            return {
                self.modifiers[key].get("name", key): value
                for key, value in resolved.items()
            }

    type = default_module_type

    @classmethod
    def can_handle(cls, value):
        return isinstance(value, SolConfModule)

    def _get_raw_members(self):
        return dict(vars(self.resolvable))

    def _get_raw_annotations(self):
        return dict(vars(self.resolvable).get("__annotations__", {}))
