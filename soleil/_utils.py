from importlib import import_module
import inspect
from pathlib import Path
from types import ModuleType
from typing import Any, Optional, Union, Dict
from collections import ChainMap

PathSpec = Union[str, Path]


class Unassigned:
    pass


def is_solconf_module(module: ModuleType):
    from soleil.resolvers.module_resolver import SolConfModule

    return isinstance(module, SolConfModule)


def infer_solconf_module(do_raise=True) -> Optional[str]:
    """
    Infer the parent solconf module where the (possibly nested) call was made.
    """

    f_back = inspect.currentframe().f_back

    while f_back is not None and not f_back.f_globals.get(
        "__is_soleil_module__", False
    ):
        f_back = f_back.f_back

    if f_back is None:
        if do_raise:
            raise Exception("Unable to deduce the parent solconf module.")
        else:
            return None

    return f_back.f_globals["__name__"]


def infer_solconf_package(do_raise=False):
    if (mdl := infer_solconf_module(do_raise)) is None:
        return None
    else:
        return mdl.split(".")[0]


def get_all_annotations(cls) -> Dict[str, Any]:
    """Returns a dictionary of annotations for all attributes defined in cls or inherited from superclasses."""
    return dict(
        ChainMap(
            *(c.__annotations__ for c in cls.__mro__ if "__annotations__" in c.__dict__)
        )
    )


def as_valid_filename(in_str) -> str:
    return in_str.replace("/", "|").replace("\\", "|").replace(":", "|")


def abs_mod_name(abs_module_name: str, rel_name: str):
    """
    Takes a module name and a relative module name (.e.g, '..sub_mod2.sub_mod3')
    and returns the absolute module name. If rel_name is already absolute, any
    dot sequences are resolved and that is returned instead.
    """

    # Add a dot to abs_module_name to drop the last module
    abs_module_name += "."

    if not abs_module_name or abs_module_name[0] == ".":
        raise ValueError(f"abs_module_name={abs_module_name}")

    if rel_name[0] == ".":
        concated = abs_module_name + rel_name
    else:
        concated = rel_name

    components = []
    for component in concated.split("."):
        if component:
            components.append(component)
        else:
            try:
                components.pop()
                if not components:
                    # IndexError also raised by pop if components is empty to begin with
                    raise IndexError
            except IndexError:
                raise ValueError(
                    f"Module reference `{concated}` refers beyond the root package"
                )

    return ".".join(components)


def get_caller_frame(levels: int = 1, do_raise=True):
    """
    Returns the frame this many levels up (relative to the calling frame).
    """
    # Get the frame two levels up by default
    frame = inspect.currentframe()
    for _ in range(levels + 1):
        if frame is None:
            break
        else:
            frame = frame.f_back

    if frame is None and do_raise:
        raise ValueError("Invalid `None` value for frame.")

    return frame
