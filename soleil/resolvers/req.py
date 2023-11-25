from pglib.validation import NoItem, checked_get_single
from soleil.overrides.overrides import deduce_soleil_var_path
from soleil.resolvers.base import Resolver
from soleil._utils import Unassigned, infer_solconf_module, get_global_loader
from soleil.overrides.overridable import Overridable


class req(Overridable):
    """
    Required but unset members can be initialized with an instance of this class.
    """

    _value = Unassigned

    @property
    def missing(self):
        return self._value is Unassigned

    def set(self, value):
        self._value = value

    def get(self, target, frame):
        solconf_module = get_global_loader().modules[infer_solconf_module()]
        var_path = deduce_soleil_var_path(target, frame, relative=True)

        if not self.missing:
            return self._value
        elif (
            ovr := checked_get_single(
                filter(
                    lambda _x: _x.target == var_path, solconf_module.__soleil_reqs__
                ),
                raise_empty=False,
            )
        ) is not NoItem:
            return ovr.get_value()
        else:
            raise ValueError(
                f"Missing required variable {deduce_soleil_var_path(target, frame)}."
            )


class reqResolver(Resolver):
    """Resolver for ``req`` instances"""

    resolvable: req

    @classmethod
    def can_handle(cls, value):
        return isinstance(value, req)

    def compute_resolved(self):
        # Should never be resolved -- resolution should happen at override time
        raise SyntaxError(
            "Unexpected attempt to resolve a `req()` -- req() can only be assigned directly to a name and cannot be used in expressions"
        )
