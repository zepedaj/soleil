from ast import List
from collections import UserDict
from typing import Dict, Optional, Tuple, Union

from pglib.py import display


class Modifiers(UserDict):
    """
    To be used as a type hint that modifies the behaviour of annotated attributes of a resolvable object. Supported entries of this modifier depend on the resolver, and
    can include the following:

    Note that modifiers can be changed in derived classes without changing the class value.

    class A:
       a = 1

    class B(A):
       a:hidden

    * name: str
    * hidden: bool
    * required: bool
    * cast: Callable
    * promote: bool
    """

    def merge(self, modifs: "Modifiers"):
        """Fails if there are clashing values"""
        out = Modifiers(self)
        for name, value in modifs.items():
            if name in out and out[name] != value:
                raise ValueError(f"Multiply-specified modifier `{name}`")
            else:
                out[name] = value

        return out

    def withdefaults(self, modifs: "Modifiers"):
        out = type(self)(self)
        for name, value in modifs.items():
            out.setdefault(name, value)
        return out


hidden = Modifiers(hidden=True)
""" The member should not be passed as an argument to type """
visible = Modifiers(hidden=False)
""" The member should be passed as a type arg """
required = Modifiers(required=True)
""" The member must to be supplied when loading the module """
name = lambda value: Modifiers(name=value)
""" Change the name of the member when passed as a type arg """
cast = lambda value: Modifiers(cast=value)
""" Used to format the value after pre-processing but before resolution """
noid = Modifiers()
""" A no-op modifier that works as a pre-processor flag indicating that an override of a given member should not be used by :func:`soleil.utils.id_str`  """


def merge_modifiers(*modifiers: Modifiers):
    """
    Fails if there are clashing values.
    The type of the output will be that of the most-specialized modifier in the inputs.
    """

    # Merge values
    out = Modifiers()
    for _m in modifiers:
        out = out.merge(_m)

    return out


def from_annotation(
    annotation: Union[Modifiers, Tuple[Modifiers]]
) -> Union[None, Modifiers]:
    """
    Converts the annotation to a ``Modifiers`` object or returns ``None`` if the annotation does not specify a ``Modifiers``.
    If the input is a tuple, the returned object is the merge of all the modifiers. An exception is raised if only some but not all
    tuple members are :class:`Modifiers`.
    """
    if isinstance(annotation, Modifiers):
        return annotation
    elif isinstance(annotation, tuple):
        components = [from_annotation(x) for x in annotation]
        if not all(isinstance(x, Modifiers) for x in components) and any(
            isinstance(x, Modifiers) for x in components
        ):
            raise ValueError(
                f"Expected all tuple components to be {Modifiers} but only some are."
            )
        return merge_modifiers(*components)
    else:
        return None
