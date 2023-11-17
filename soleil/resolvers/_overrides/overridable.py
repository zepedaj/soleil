import abc
from types import FrameType
from typing import Any, Optional

from soleil._utils import infer_solconf_module, get_global_loader


class Overridable(abc.ABC):
    """Members that can be overriden in a special way"""

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

    def __init__(self, *args):
        """

        Options:

        #. ``target = submodule(parent_module, overridable_submodule)``

        #. ``target = submodule(overridable_submodule)`` In this case, the the parent
        module name is deduced from the target name -- e.g., this is equivalent to ``target = submodule('.target', overridable_submodule)

        .. code-block::

            # Load module .color.red.
            # Can CLI-override 'red' by e.g,. 'green'
            # with "color='green'"
            color = submodule('.color', 'red')

            # The module .color containing the options can be
            # infered from the target variable if it is the same name
            color = submodule('red')


        """
        self.containing_module = infer_solconf_module()

        if len(args) == 1:
            self.sub_module_name = args[0]
        elif len(args) == 2:
            self.module_name, self.sub_module_name = args
        else:
            raise Exception("Invalid number of input arguments.")

    def set(self, sub_module):
        self.sub_module_name = sub_module

    def get(self, target: str, frame: FrameType):
        if (
            frame.f_locals.get("__is_solconf_module__", False)
            and frame.f_locals.get("__pp_promoted__", None) == target
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
                _target=target,
                _frame=frame,
            )
        )
