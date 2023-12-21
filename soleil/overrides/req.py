from jztools.validation import NoItem, checked_get_single
from soleil.overrides.overrides import deduce_soleil_var_path
from soleil.resolvers.base import Resolver
from soleil._utils import Unassigned, infer_solconf_module, get_global_loader
from soleil.overrides.overridable import Overridable


class req(Overridable):
    """
    Required but unset members can be initialized with an instance of this class.
    """

    _value = Unassigned
    _unknown_path = "<unknown path>"
    var_path_str = _unknown_path

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
            self.var_path = deduce_soleil_var_path(target, frame).as_str()
            return self  # will fail at resolution


class reqResolver(Resolver):
    """Resolver for ``req`` instances"""

    resolvable: req

    @classmethod
    def can_handle(cls, value):
        return isinstance(value, req)

    def compute_resolved(self):
        error_msg = f"Missing required variable `{self.resolvable.var_path_str}`."
        if self.resolvable.var_path_str == req._unknown_path:
            error_msg = " ".join(
                [
                    error_msg,
                    "Did you use req() as a modifier (`var:req()`) and not as an assigned value (`var = req()`)?",
                ]
            )
        raise ValueError(error_msg)
