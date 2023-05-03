from pathlib import Path
import re
from tempfile import TemporaryDirectory
import pytest
from soleil.solconf.cli_tools import solex as mdl
from xerializer.decorator import serializable
from subprocess import CalledProcessError, check_call, run


def test_solex():
    with TemporaryDirectory() as temp_dir:
        output_path = Path(temp_dir) / "output.txt"

        # Case 1
        with open(conf_path := (Path(temp_dir) / "conf.yaml"), "wt") as fo:
            fo.write(f"{{'a':0}}")

        run(["solex", str(conf_path)], capture_output=True, check=True)

        # Case 2
        with open(conf_path := (Path(temp_dir) / "conf.yaml"), "wt") as fo:
            fo.write(f"{{'__type__':'undefined_signature'}}")

        try:
            run(["solex", str(conf_path)], capture_output=True, check=True)
        except CalledProcessError as err:
            assert re.match(
                re.compile(
                    ".*No installed handler for types with signature undefined_signature.*",
                    re.MULTILINE,
                ),
                err.stderr.decode("utf-8").strip().split("\n")[-1],
            )
        else:
            raise Exception("Error expected but no raised.")


def test_command():
    with TemporaryDirectory() as temp_dir:
        #
        temp_dir = Path(temp_dir)
        output_path = temp_dir / "output.txt"
        conf_path = temp_dir / "conf.yaml"
        with open(conf_path, "wt") as fo:
            fo.write(f"{{'filename':{output_path}}}")

        script_path = Path(__file__).parent / "_helper_callable.py"

        # Call foo
        check_call(
            [
                "python",
                str(script_path),
                str(conf_path),
                "--my_opt",
                "my_opt_value",
            ]
        )
        with open(output_path, "r") as fo:
            assert fo.read() == "foo my_opt_value"


def test_group_command():
    with TemporaryDirectory() as temp_dir:
        #
        temp_dir = Path(temp_dir)
        output_path = temp_dir / "output.txt"
        conf_path = temp_dir / "conf.yaml"
        with open(conf_path, "wt") as fo:
            fo.write(f"{{'filename':{output_path}}}")

        # Call bar
        script_path = Path(__file__).parent / "_helper_group_callable.py"
        check_call(["python", str(script_path), "bar", str(output_path)])
        with open(output_path, "r") as fo:
            assert fo.read() == "bar"

        # Call foo
        output_path.unlink()
        check_call(
            [
                "python",
                str(script_path),
                "foo",
                str(conf_path),
                "--my_opt",
                "my_opt_value",
            ]
        )
        with open(output_path, "r") as fo:
            assert fo.read() == "foo my_opt_value"
