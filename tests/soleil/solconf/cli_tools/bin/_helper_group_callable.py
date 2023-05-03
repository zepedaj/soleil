from pathlib import Path
from tempfile import TemporaryDirectory
from soleil import solex
import climax as clx


@clx.group()
def cmd_group():
    pass


@cmd_group.command()
@clx.argument("filename", type=Path)
def bar(filename):
    with open(filename, "a") as fo:
        fo.write("bar")


@solex(cmd_group)
@clx.argument("--my_opt", default="empty", help="My optional argument.")
def foo(obj, my_opt):
    """Optional doc string will override the default."""

    with open(obj["filename"], "a") as fo:
        fo.write(f"foo {my_opt}")


if __name__ == "__main__":
    cmd_group()
