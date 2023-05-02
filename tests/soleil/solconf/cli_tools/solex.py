from pathlib import Path
from tempfile import TemporaryDirectory
from soleil.solconf.cli_tools import solex as mdl

global OUTPUT


def test_solex():
    global OUTPUT
    OUTPUT = None

    @mdl.solex()
    def fxn(obj):
        global OUTPUT
        OUTPUT = obj["a"] + 7

    with TemporaryDirectory() as temp_dir:
        with open(conf_path := (Path(temp_dir) / "conf.yaml"), "wt") as fo:
            fo.write("{'a':3, 'b':4}")

        assert OUTPUT is None
        fxn.func(**vars(fxn.parser.parse_args([str(conf_path)])))
        assert OUTPUT == 10


def test_group():
    global OUTPUT
    OUTPUT = None

    from soleil import solex
    import climax as clx

    @clx.group()
    def cmd_group():
        pass

    @cmd_group.command()
    def bar():
        global OUTPUT
        OUTPUT = "bar"

    @solex(cmd_group)
    def foo(obj, my_opt):
        """Optional doc string will override the default."""
        global OUTPUT
        OUTPUT = {**obj, "my_opt": my_opt}

    # Add any extra arguments
    foo.parser.add_argument("--my_opt", default="empty", help="My optional argument.")

    with TemporaryDirectory() as temp_dir:
        with open(conf_path := (Path(temp_dir) / "conf.yaml"), "wt") as fo:
            fo.write("{'a':3, 'b':4}")

        # Call foo
        OUTPUT = None
        parsed_args = vars(
            cmd_group.parser.parse_args(["foo", str(conf_path), "--my_opt", "opt_val"])
        )
        func = parsed_args.pop("_func_cmd_group")
        func(**parsed_args)
        assert OUTPUT == {"a": 3, "b": 4, "my_opt": "opt_val"}

        # Call bar
        OUTPUT = None
        parsed_args = vars(cmd_group.parser.parse_args(["bar"]))
        func = parsed_args.pop("_func_cmd_group")
        func(**parsed_args)
        assert OUTPUT == "bar"
