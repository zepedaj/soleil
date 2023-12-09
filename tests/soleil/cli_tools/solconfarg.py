from uuid import uuid4
from soleil.cli_tools import solconfarg as mdl
from soleil.cli_tools._argparse_patches import ReduceAction
import argparse
from tests import TEST_DATA_ROOT

# from ..modifiers import build_config_files
# from .._helpers import file_structure, DOCS_CONTENT_ROOT
from unittest import TestCase


class TestSolConfArg(TestCase):
    def test_argparse(self):
        path = str(TEST_DATA_ROOT / "solconfarg/seasons.solconf")

        def get_parser():
            parser = argparse.ArgumentParser()
            parser.add_argument(
                "req_arg",
                nargs="*",
                type=mdl.SolConfArg(package_name=uuid4().hex),
                action=ReduceAction,
            )
            parser.add_argument(
                "--opt_arg",
                nargs="*",
                type=mdl.SolConfArg(path, package_name=uuid4().hex),
                action=ReduceAction,
            )
            return parser

        parser = get_parser()
        args = parser.parse_args([path])
        orig = {"winter": 0, "spring": 1, "summer": 2, "fall": 3}
        assert args.req_arg == orig

        parser = get_parser()
        args = parser.parse_args([path, "--opt_arg"])
        assert args.req_arg == orig
        assert args.opt_arg == orig

        parser = get_parser()
        args = parser.parse_args([path, "winter=10", "--opt_arg", "fall=30"])
        assert args.req_arg == {**orig, "winter": 10}
        assert args.opt_arg == {**orig, "fall": 30}

    def test_empty_overrides_argparse(self):
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "new_arg",
            type=mdl.SolConfArg(
                TEST_DATA_ROOT.parent / "soleil_examples/vanilla/main.solconf"
            ),
        )
        parser.parse_args([])

    def test_empty_overrides(self):
        sc = mdl.SolConfArg(
            TEST_DATA_ROOT.parent / "soleil_examples/vanilla/main.solconf"
        )
        assert sc() == {"a": 1, "b": 2, "c": 3}
