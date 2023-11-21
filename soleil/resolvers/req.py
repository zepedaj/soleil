from soleil.overrides.overrides import deduce_soleil_var_path
from soleil.resolvers.base import Resolver
from soleil._utils import Unassigned
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
        if self.missing:
            raise ValueError(
                f"Missing required variable {deduce_soleil_var_path(target, frame)}."
            )
        return self._value


class reqResolver(Resolver):
    """Resolver for ``req`` instances"""

    resolvable: req

    @classmethod
    def can_handle(cls, value):
        return isinstance(value, req)

    def compute_resolved(self):
        # Should never be resolved -- resolution should happen at override time
        raise Exception("Missing required value")
