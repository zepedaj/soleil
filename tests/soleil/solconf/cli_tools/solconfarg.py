from soleil.solconf.cli_tools import solconfarg as mdl
from soleil.solconf.cli_tools import ReduceAction
import argparse
from ..modifiers import build_config_files
from .._helpers import file_structure, DOCS_CONTENT_ROOT
from unittest import TestCase


class TestSolConfArg(TestCase):
    def test_argparse(self):
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "req_arg", nargs="*", type=mdl.SolConfArg(), action=ReduceAction
        )
        parser.add_argument(
            "--opt_arg",
            nargs="*",
            type=mdl.SolConfArg(
                DOCS_CONTENT_ROOT / "yaml/load_with_choices/config.yaml"
            ),
            action=ReduceAction,
        )
        args = parser.parse_args(
            [str(DOCS_CONTENT_ROOT / "yaml/load_with_choices/config.yaml")]
        )

    def test_all(self):

        # Change value
        with build_config_files(file1_expected_updates={"file1_0": 123}) as (
            config_file,
            expected,
        ):

            sca = mdl.SolConfArg(config_file)
            actual = sca(["root_5.file1_0=123"])
            self.assertEqual(actual, expected)

        # Set load target (to same)
        with build_config_files() as (config_file, expected):

            # Replace by same.
            sca = mdl.SolConfArg(config_file)
            actual = sca(["root_5=subdir1/file1"])
            self.assertEqual(expected, actual)

            # Replace file1 by file2
            sca = mdl.SolConfArg(config_file)
            actual = sca(["root_5=subdir1/file2"])
            self.assertNotEqual(expected, actual)
            self.assertEqual(expected["root_5"]["file1_5"], actual["root_5"])

    def test_parse_override_str(self):
        for raw_override, (ref, assgn, raw_val) in [
            (
                ".*={'_::load,promote': /tmp/tmpsx0kl2rt/numbers/prime.yaml}",
                (".", "*=", "{'_::load,promote': /tmp/tmpsx0kl2rt/numbers/prime.yaml}"),
            ),
        ]:
            self.assertEqual(
                mdl.SolConfArg._parse_override_str(raw_override), (ref, assgn, raw_val)
            )

    def test_edge_cases(self):
        with file_structure(
            {
                "config.yaml": {
                    "numbers::load": "numbers/prime",
                    "colors::load": "colors/reddish",
                },
                "numbers/prime.yaml": [1, 3, 5],
                "colors/reddish.yaml": {"primary": "red", "derived": "pink"},
            }
        ) as (temp_dir, paths):

            # Clobber-replace with load
            sca = mdl.SolConfArg(paths["config.yaml"])
            self.assertEqual(
                sca(
                    ['.*={"_::load,promote": ' + str(paths["numbers/prime.yaml"]) + "}"]
                ),
                [1, 3, 5],
            )

            # No overrides
            sca = mdl.SolConfArg(paths["config.yaml"])
            self.assertEqual(
                sca([]),
                {"colors": {"derived": "pink", "primary": "red"}, "numbers": [1, 3, 5]},
            )

            # Clobber-replace the root
            sca = mdl.SolConfArg(paths["config.yaml"])
            self.assertEqual(sca([".*=1"]), 1)

            # Replace with parent references
            sca = mdl.SolConfArg(paths["config.yaml"])
            self.assertEqual(
                sca(
                    ["colors..numbers.2=7", "colors..numbers.2...colors.derived=orange"]
                ),
                {
                    "colors": {"derived": "orange", "primary": "red"},
                    "numbers": [1, 3, 7],
                },
            )

    def test_clobber(self):
        sca2 = mdl.SolConfArg(f"{DOCS_CONTENT_ROOT}/yaml/load_with_choices/config.yaml")
        sca2(["typing_a*=soft"])
