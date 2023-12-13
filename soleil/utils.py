from pathlib import Path
from typing import Type, List

from jztools.rentemp import RenTempDir, RenTempDirExists
from soleil.loader.loader import GLOBAL_LOADER, load_config
from soleil.rstr import RStr
from ._utils import (
    infer_solconf_package,
    as_valid_filename,
    infer_solconf_module,
    infer_root_config,
    abs_mod_name,
)

# Utilities that can be called from inside solconf modules.

from tempfile import mkdtemp as temp_dir

temp_dir = temp_dir
""" Returns a temporary directory """


def derive(*parents, **new_vars):
    """
    Derives the specified class, overloading the supplied indicated members. Example::

        class Source:
            a = 1
            b = 2

        b3 = derive(Source, b=3)
    """
    # TODO: How does this play with overrides?
    return type(f"<{','.join(x.__name__ for x in parents)} derived>", parents, new_vars)


def root_stem(root_config=None) -> str:
    """
    Returns the stem of the filename name of the root configuration.
    """
    return (root_config or infer_root_config()).__file__.stem


def package_overrides(as_source=True) -> List:
    """
    Returns a list of all supplied package overrides.
    """
    overrides = GLOBAL_LOADER.package_overrides[infer_solconf_package()]
    if as_source:
        overrides = [ovr.source for ovr in overrides]
        if any(ovr is None for ovr in overrides):
            raise ValueError(f"Could not retrieve the source for override {ovr}")
    return overrides


class id_str(RStr):
    def __init__(self, glue=",", safe=True, full=False, with_root_stem=True):
        """
        A special class that resolves to an id string built from the overrides that are not annotated with :attr:`noid`.

        :param glue: String that joins all the override strings
        :param safe: Whether the escape characters that are invalid in filenames
        :param full: If ``False`` (the default), only the right-most target attribute is used. (e.g., with the default ``full=False``,  ``'height=2'``  instead of  ``'rectangle.dimensions.height=2``).
        :param with_root_stem: Whether to include the file path stem of the root config
        """
        # NOTE: The initializer code executes within a *.solconf file
        # while the ``to_str`` does not and runs within a standard python
        # program.
        self.glue = glue
        self.safe = safe
        self.full = full
        self.package_name = infer_solconf_package()
        self.root_config = infer_root_config()
        self.with_root_stem = with_root_stem

    @property
    def _components(self):
        return (self,)

    def compute_resolved(self):
        overrides = GLOBAL_LOADER.package_overrides[self.package_name]

        out = self.glue.join(
            ([root_stem(self.root_config)] if self.with_root_stem else [])
            + [
                _x.source
                if self.full
                else _x.source.replace(_x.target.as_str(), _x.target[-1:].as_str())
                for _x in overrides
                if not (_x.target.get_modifiers(self.root_config) or {}).get(
                    "noid", False
                )
            ]
        )
        if self.safe:
            out = as_valid_filename(out)
        return out


def _is_int(string):
    """Returns True if the string can be converted to an integer, False otherwise."""
    try:
        int(string)
        return True
    except ValueError:
        return False


def sub_dir(root: Path, create=True):
    """
    Returns a sub-directory with a sequential number
    """
    root = Path(root)

    if create and not root.is_dir():
        root.mkdir(parents=True, exist_ok=True)

    while True:
        new_sub_dir = root / str(
            max(
                (int(x.name) for x in root.glob("*") if _is_int(x.name) and x.is_dir()),
                default=0,
            )
            + 1
        )
        if not create:
            break
        try:
            with RenTempDir(new_sub_dir):
                pass
        except RenTempDirExists:
            continue
        break
    return str(new_sub_dir)


def spawn(rel_module_name, pass_overrides=True, var_path=None) -> Type:
    """
    Takes the name of a target module (relative to the calling module, if dot-prefixed, or the current package
    otherwise) that promotes a class, and loads it in a new package, providing the calling package's overrides
    as possible overrides.

    The target module must expose a promoted class that will then be returned with the specified overrides
    applied (those that are compatible).

    This returned class can then be used as a parent class for a new class in the calling module. The new
    class will also have the compatible specified overrides applied to it.

    For correct transference of overrides to the parent class, the child class must also be promoted
    in the calling module or the ``var_path`` parameter must be set to the child class's ``__qualname__`` attribute.

    For example, assuming file ``'main.solconf'`` promotes a class:

    .. code-block::

        @promoted
        class B(A := spawn(".main")):
            type: as_type = lambda **kwargs: kwargs
            c = A.b + 1
            d = c + 1

    Note that one can optionally access the parent class's attributes by assigning it to a local variable

    """

    calling_package = infer_solconf_package()
    target_module_name = abs_mod_name(infer_solconf_module(), rel_module_name)
    target_module_path = GLOBAL_LOADER.get_sub_module_path(target_module_name)

    return load_config(
        target_module_path,
        overrides=(
            []
            if not pass_overrides
            else GLOBAL_LOADER.package_overrides[calling_package]
        ),
        resolve=False,
        _var_path=var_path,
    )
