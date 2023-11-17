from collections import UserDict
import inspect
from itertools import chain
from types import MappingProxyType
from soleil.resolvers.req import req
from soleil.resolvers.modifiers import Modifiers, from_annotation, merge_modifiers
from soleil._utils import Unassigned, get_all_annotations
from .base import Resolver, displayable, resolve
from typing import Any, Dict, Optional
from pglib.py import entity_from_name


def type_cast(value):
    return entity_from_name(value) if isinstance(value, str) else value


as_type = Modifiers(
    as_type=True,
    hidden=False,
    cast=lambda x: (entity_from_name(x) if isinstance(x, str) else x),
)
"""
Annotates a variable containing a class or callable (or the fully qualified name of one)
that will be used to instantiate the meta object.
"""
as_args = Modifiers(as_args=True, hidden=False)


class DisplayableFromClassResolver(UserDict):
    pass


class ClassResolver(Resolver):
    args = tuple()
    type = None
    valid_modifier_keys = frozenset({"name", "hidden", "cast", "as_type", "as_args"})
    special_members = MappingProxyType({"args": "as_args", "type": "as_type"})
    """Tuples of attribute names and modifier type for special members."""

    def __init__(self, resolvable, _build=True):
        super().__init__(resolvable)
        if _build:
            self._get_members_and_modifiers()

    @classmethod
    def can_handle(cls, value):
        """Must by a type and have an `as_type` modifier."""
        return isinstance(value, type) and (
            any(
                x.get("as_type", False)
                for x in cls(value, _build=False)._get_resolved_modifiers().values()
            )
        )

    def _get_raw_members(self):
        # Returns all attributes for all mro classes
        return {
            name: param
            for _cls in inspect.getmro(self.resolvable)[::-1]
            for name, param in vars(_cls).items()
        }

    def _get_raw_annotations(self):
        return get_all_annotations(self.resolvable)

    def _get_resolved_modifiers(self) -> Dict[str, Modifiers]:
        # Only returns annotations that are modifiers or tuples, with tuples merged into a modifier
        annotations = self._get_raw_annotations()

        return {
            key: modifs
            for key, value in resolve(annotations).items()
            if (modifs := from_annotation(value)) is not None
        }

    def _get_required_member_names(self):
        return {
            key
            for key, value in self.members.items()
            if isinstance(value, req) and req.missing
        }

    def _get_default_hidden_value(self, name: str):
        return (name.startswith("__") and name.endswith("__")) or (
            name in getattr(self.resolvable, "__soleil_default_hidden_members__", set())
        )

    def _get_default_modifier(
        self, name: str, value: Any = Unassigned, modifier: Optional[Modifiers] = None
    ):
        modifier = (modifier if modifier is not None else Modifiers()).withdefaults(
            Modifiers(hidden=self._get_default_hidden_value(name))
        )
        return modifier

    def _get_members_and_modifiers(self):
        # Returns members and non-members
        raw_members = self._get_raw_members()

        # Get explicit modifiers
        explicit_modifiers = self._get_resolved_modifiers()

        # Check all explicit modifiers have valid keys.
        for name, modifier in explicit_modifiers.items():
            if not set(modifier.keys()).issubset(self.valid_modifier_keys):
                raise ValueError(
                    f"Invalid modifier key(s) `{', '.join(modifier.keys())}` for resolvable {self.resolvable}"
                )

        # Get implicit modifiers for un-annotated and partially annotated members,
        # including required members with no explicit value
        extended_modifiers = {}  # Includes explicit and implicit
        for name in set(chain(raw_members.keys(), explicit_modifiers.keys())):
            extended_modifiers[name] = self._get_default_modifier(
                name,
                raw_members.get(name, Unassigned),
                explicit_modifiers.get(name, Modifiers()),
            )

        self.explicit_modifiers = explicit_modifiers
        self.extended_modifiers = extended_modifiers
        self.extended_members = {
            key: self.extended_modifiers[key].get("cast", lambda x: x)(raw_members[key])
            for key in raw_members
        }

        # Set the special members
        for special_name, special_flag in self.special_members.items():
            if (
                special_value := self.get_special_member(special_flag)
            ) is not Unassigned:
                setattr(self, special_name, special_value)

    def get_special_member(self, flag_name: str):
        # Check validity of provided type and args variables.
        arg_names = [
            name
            for name, value in self.extended_modifiers.items()
            if value.get(flag_name, False)
        ]
        if len(arg_names) > 1:
            raise ValueError(
                f"Expected a single `{flag_name}` argument but got multiple ({', '.join(arg_names)}) for resolvable `{self.resolvable}`"
            )
        elif len(arg_names) == 1:
            if (
                out := self.extended_members.get(arg_names[0], Unassigned)
            ) is Unassigned:
                raise ValueError(
                    f'Annotation with no value provided for explicit special modifier "{flag_name}"'
                )
            return out
        else:
            return Unassigned

    @property
    def modifiers(self):
        """Non-special, visible modifiers"""
        special_member_flags = tuple(self.special_members.values())
        return {
            key: value
            for key, value in self.extended_modifiers.items()
            if not value["hidden"]
            and not any(value.get(flag, False) for flag in special_member_flags)
        }

    @property
    def members(self):
        """Non-special, visible members"""
        return {key: self.extended_members[key] for key in self.modifiers}

    def compute_resolved(self):
        # Check no requireds are missing
        if missing_var_names := list(self._get_required_member_names()):
            raise ValueError(
                f"Missing values for required members `{', '.join(missing_var_names)}` for resolvable {self.resolvable}"
            )

        # Resolve
        resolved_args = resolve(self.args or tuple())
        resolved_members = {
            resolve(name): resolve(value)
            for name, value in self.members.items()
            if not self.modifiers[name]["hidden"]
        }
        return self.type(*resolved_args, **resolved_members)

    def displayable(self, _dict_class=DisplayableFromClassResolver):
        raw_members = self._get_raw_members()
        expl_modifiers = self._get_resolved_modifiers()

        return _dict_class(
            [
                (
                    f"{displayable(name)}"
                    + (
                        f":{x}"
                        if (x := str(displayable(expl_modifiers.get(name, ""))))
                        else ""
                    ),
                    displayable(value),
                )
                for name, value in raw_members.items()
                if not self.extended_modifiers[name]["hidden"]
                or name in self.explicit_modifiers
            ]
        )
