from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Dict, Generator


@contextmanager
def solconf_file(
    contents: str, header="from soleil.solconf import * "
) -> Generator[Path, None, None]:
    """
    Return a path to a solconf file
    """
    with TemporaryDirectory() as temp_dir:
        with open(path := (Path(temp_dir) / "main.solconf"), "w") as fo:
            fo.write(f"{header}\n{contents}")
        yield path


@contextmanager
def solconf_package(
    contents: Dict[str, str], header="from soleil.solconf import * "
) -> Generator[Path, None, None]:
    """
    Creates a solconf package and returns a path to a solconf package.
    The contents are specified as module-name/code tuples (keys and values, respectively of the parameter ``contents``).
    """

    with TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)
        for module_name, module_contents in contents.items():
            path_parts = module_name.split(".")
            subdir = temp_dir
            for part in path_parts[:-1]:
                subdir /= part
                subdir.mkdir(exist_ok=True)
            with open(subdir / f"{path_parts[-1]}.solconf", "w") as fo:
                fo.write(f"{header}\n{module_contents}")
        yield temp_dir
