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
