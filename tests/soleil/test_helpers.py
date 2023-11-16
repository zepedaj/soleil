from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory


@contextmanager
def solconf_file(contents):
    """
    Return a path to a solconf file (or multiple
    """
    with TemporaryDirectory() as temp_dir:
        with open(path := (Path(temp_dir) / "main.solconf"), "w") as fo:
            fo.write(f"from soleil import *\n{contents}")
        yield path
