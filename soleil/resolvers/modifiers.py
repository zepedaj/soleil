from collections import UserDict
from typing import Tuple, Union

from soleil._utils import Unassigned


class Modifiers(UserDict):
    """
    To be used as a type hint or class decorator that modifies the behaviour of annotated members of a resolvable object. Supported entries of this modifier depend on the resolver.

    Pre-instantiated modifier objects or object factories that make code more readable are provided as part of various soleil modules:

    * ``name(value:str)``: Specifies that the annotated member should be passed to its type with this name instead of its declared variable name.
    * ``hidden`` : The annotated member should not be passed to its type.
    * ``cast(value:Callable)``: The value assigned to the member will be mapped with this callable **before** resolution.
    * ``promoted``: Valid only to annotate root-level members of solconf modules. The promoted member will be returned when the module is loaded instead of the module itself, and
        CLI override variable paths that point to the containing module will instead be re-directed to the annotated member. Modules resolved with a promoted member (assuming the default
        module type)



    Note that modifiers can be changed in derived classes without changing the class value.

    .. code-block::

        class A:
           a = 1

        class B(A):
           a:hidden

    Modifiers can be applied to classes by using value-less annotation declarations:

    .. code-block::

        A:(hidden, noid)

        class A:
            ...

    Alternatively, all modifier objects can be used as class decorators:

    .. code-block::

        @hidden
        @noid
        class A:
            ...

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

    def __call__(self, cls):
        """
        Used to allow the modifiers object to decorate classes.

        Appends the specified modifier to the class
        """

        from soleil.loader.loader import GLOBAL_LOADER  # TODO: Should load globally

        if not isinstance(cls, type):
            raise Exception(f"Expected a class but received {type(cls)}")

        parent = GLOBAL_LOADER.modules[cls.__module__]
        components = cls.__qualname__.split(".")
        for name in components[:-1]:
            parent = getattr(parent, name)

        anns = getattr(parent, "__annotations__", {})
        setattr(parent, "__annotations__", anns)

        if anns.get(cls.__name__, Unassigned) is Unassigned:
            # No previous annotation
            anns[cls.__name__] = self
        elif isinstance(anns[cls.__name__], Modifiers):
            # Annotation has Modifiers object
            anns[cls.__name__] = (anns[cls.__name__], self)
        elif isinstance(anns[cls.__name__], tuple):
            # Annotation has tuple of Modifiers object
            anns[cls.__name__] = (*anns[cls.__name__], self)
        else:
            raise ValueError(
                f"Annotations must consist of Modifiers or tuples thereof, but where {type(anns[cls.__name__])}"
            )

        return cls


hidden = Modifiers(hidden=True)
""" The member should not be passed as an argument to type """
visible = Modifiers(hidden=False)
""" The member should be passed as a type arg """
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
