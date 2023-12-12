import abc
from types import FrameType
from typing import Any, Dict, Optional

from soleil._utils import infer_solconf_module, get_global_loader


class Overridable(abc.ABC):
    """
    When an overridable is assigned as a value to a member variable,
    soleil overrides will be applied to that member using its :meth:`set` and :meth:`get` methods
    (see :func:`_soleil_override`).
    """

    @abc.abstractmethod
    def set(self, new_value):
        ...

    @abc.abstractmethod
    def get(self, target: str, frame: FrameType) -> Any:
        """
        :param target: The name of the variable that this overridable is being assigned to.
        :param frame: The frame where the overridable is being assigned.
        """
        ...


class submodule(Overridable):
    module_name: Optional[str] = None
    sub_module_name: str
    containing_module: str

    def __init__(self, *args, reqs=None):
        """

        Loads, from a sub-package, a submodule with an overridable name. The sub-package can be explicitly provided or inferred from the target variable name.

        For example, the *.colors.red* package can be loaded using either of


        .. code-block::

            color = submodule('.colors', 'red')
            color = submodule('red')

        As an overridable, ``submodule`` supports interpreting the override string as a new submodule name. Using

        .. code-block:: bash

            $ solex main.solconf color='"green"'

        for example, will assign the load value of *.color.green* to *color*.

        """
        self.containing_module = infer_solconf_module()

        if len(args) == 1:
            self.sub_module_name = args[0]
        elif len(args) == 2:
            self.module_name, self.sub_module_name = args
        else:
            raise Exception("Invalid number of input arguments.")

        self.reqs = reqs

    def set(self, sub_module):
        self.sub_module_name = sub_module

    def get(self, target: str, frame: FrameType):
        if (
            frame.f_locals.get("__is_solconf_module__", False)
            and frame.f_locals.get("__soleil_pp_meta__", {}).get("promoted", None)
            == target
        ):
            # Promoted submodules can no longer be overriden, hence behave like load.
            raise SyntaxError(
                "Cannot apply `promoted` modifier to `submodule` overridables - either use `resolves` instead of `promoted` or `load` instead of `submodule`."
            )

        return (
            get_global_loader()
            .modules[self.containing_module]
            .load(
                ".".join([self.module_name or f".{target}", self.sub_module_name]),
                reqs=self.reqs,
                _target=target,
                _frame=frame,
            )
        )


class choices(Overridable):
    """
    Choice supporting convenient string-based CLI override

    .. code-block::

        # main.solconf
        a:as_type = choices({'A':'submod1:A', 'B':'symbod2:B'}, 'A')
        color = choices({'red':[1,0,0], 'green':[0,1,0], 'blue':[0,0,1]}, 'red')

    .. code-block:: bash

        bash:~$ solex ./main a='"B"' color='"green"'



    """

    def __init__(self, values: Dict[str, Any], default):
        self.values = dict(values)
        self.choice = default

    def set(self, choice):
        self.choice = choice

    def get(self, *args, **kwargs):
        return self.values[self.choice]
