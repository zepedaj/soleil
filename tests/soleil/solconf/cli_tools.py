from unittest import TestCase
from .modifiers import build_config_files


import argparse
from soleil.solconf import cli_tools as mdl


class TestSolConfArg(TestCase):

    # def test_all(self):
    #     parser = argparse.ArgumentParser()
    #     parser.add_argument('req_arg', nargs='*', type=mdl.SolConfArg)
    #     parser.add_argument('--opt_arg', nargs='*',
    #                         type=mdl.SolConfArg('yaml/load_with_choices/config.yaml'),)
    #     args = parser.parse_args(['yaml/load_with_choices/config.yaml'])

    def test_all(self):
        with build_config_files(
                file1_expected_updates={'file1_0': 123}) as \
                (config_file, expected):

            sca = mdl.SolConfArg(config_file)
            actual = sca(['root_5.file1_0=123'])
            self.assertEqual(actual, expected)
