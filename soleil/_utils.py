from importlib import import_module
import inspect
from pathlib import Path
from types import ModuleType
from typing import Any, Union, Dict
from collections import ChainMap

from soleil.resolvers.modifiers import Modifiers, from_annotation

PathSpec = Union[str, Path]


class Unassigned:
    pass


def is_solconf_module(module: ModuleType):
    from soleil.resolvers.module_resolver import SolConfModule

    return isinstance(module, SolConfModule)


def _get_module_by_name(f_back):
    if (
        "__soleil_loader__" not in f_back.f_globals
        or "__name__" not in f_back.f_globals
    ):
        return None
    else:
        return import_module(f_back.f_globals["__name__"])


def infer_solconf_module(do_raise=False):
    """Infer the parent solconf module where the (possibly nested) call was made."""
    module = None

    f_back = (
        None
        if (current_frame := inspect.currentframe()) is None
        else current_frame.f_back
    )
    while f_back is not None and (
        ((module := _get_module_by_name(f_back)) is None)
        or not is_solconf_module(module)
    ):
        f_back = f_back.f_back
    if f_back is None:
        module = None

    if do_raise and module is None:
        raise Exception("Unable to deduce the parent solconf module.")

    return module


def get_all_annotations(cls) -> Dict[str, Any]:
    """Returns a dictionary of annotations for all attributes defined in cls or inherited from superclasses."""
    return dict(
        ChainMap(
            *(c.__annotations__ for c in cls.__mro__ if "__annotations__" in c.__dict__)
        )
    )


def as_valid_filename(in_str) -> str:
    return in_str.replace("/", "|").replace("\\", "|").replace(":", "|")
