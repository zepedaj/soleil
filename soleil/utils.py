from pathlib import Path

from pglib.rentemp import RenTempDir, RenTempDirExists
from soleil.loader.loader import GLOBAL_LOADER
from ._utils import infer_solconf_package, as_valid_filename

# Utilities that can be called from inside solconf modules.

from tempfile import mkdtemp as temp_dir


def derive(*parents, **new_vars):
    return type(f"<{','.join(x.__name__ for x in parents)} derived>", parents, new_vars)


def id_str(glue=",", safe=True, full=False):
    """
    An id string built from the overrides.

    :param glue: String that joins all the override strings
    :param safe: Whether the escape characters that are invalid in filenames
    :param full: If ``False`` (the default), only the right-most target attribute is used. (e.g., with the default ``full=False``,  ``'height=2'``  instead of  ``'rectangle.dimensions.height=2``).
    """
    overrides = GLOBAL_LOADER.package_overrides[
        infer_solconf_module(True)[0].split(".")[0]
    ]
    out = glue.join(overrides)
    if safe:
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
