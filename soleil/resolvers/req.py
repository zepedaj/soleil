from soleil.resolvers.base import Resolver
from soleil._utils import Unassigned
from soleil.resolvers.setter import Setter


class req:
    """
    Required but unset members can be initialized with an instance of this class.
    """

    _value = Unassigned

    @property
    def missing(self):
        return self._value is Unassigned


class reqResolver(Resolver):
    """Resolver for ``req`` instances"""

    resolvable: req

    @classmethod
    def can_handle(cls, value):
        return isinstance(value, req)

    def compute_resolved(self):
        if self.resolvable._value is Unassigned:
            raise Exception("Missing required value")
        return self.resolvable._value


class reqSetter(Setter):
    """Setter for ``req`` instances"""

    @classmethod
    def can_handle(cls, value):
        return isinstance(value, req)

    def set(self, current, new):
        current._value = new
        return current
