from pathlib import Path
from tempfile import mkdtemp
from typing import Dict, Optional
from warnings import warn


def package_as_serializable(package_root: Path):
    """
    Returns a dictionary with module names as keys and source code as values.
    """
    package_root = Path(package_root)

    contents = {}
    for path in package_root.glob("**/*"):
        if path.is_dir():
            continue
        elif path.suffix != ".solconf":
            warn(
                f"File will not be included in serializable representation of solconf package: `{path}`"
            )
        else:
            contents[str(path.relative_to(package_root))] = path.read_text()

    return contents


def package_from_serializable(package_srlzbl: Dict[str, str], target_dir: Path):
    """
    Creates the specified solconf in the specified target directory (a random directory by default).
    """

    for module_rel_path, module_contents in package_srlzbl.items():
        module_abs_path = target_dir / module_rel_path
        if target_dir not in module_abs_path.parents:
            raise Exception(
                f"Invalid module relative path {module_rel_path} refers to path outside the package directory."
            )
        module_abs_path.parent.mkdir(parents=True, exist_ok=True)

        with open(module_abs_path, "w") as fo:
            fo.write(module_contents)
