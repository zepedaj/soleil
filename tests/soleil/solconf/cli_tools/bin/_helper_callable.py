from pathlib import Path
from tempfile import TemporaryDirectory
from soleil import solex
import climax as clx


@solex()
@clx.argument("--my_opt", default="empty", help="My optional argument.")
def foo(obj, my_opt):
    """Optional doc string will override the default."""

    with open(obj["filename"], "a") as fo:
        fo.write(f"foo {my_opt}")


if __name__ == "__main__":
    foo()
