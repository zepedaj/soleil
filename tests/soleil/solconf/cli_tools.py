from soleil.solconf import cli_tools as mdl, SolConf
import argparse
from .modifiers import build_config_files
from unittest import TestCase

from ._helpers import file_structure


class TestSolConfArg(TestCase):

    def test_all(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('req_arg', nargs='*', type=mdl.SolConfArg())
        parser.add_argument('--opt_arg', nargs='*',
                            type=mdl.SolConfArg('yaml/load_with_choices/config.yaml'),)
        args = parser.parse_args(['yaml/load_with_choices/config.yaml'])

    def test_all(self):

        # Change value
        with build_config_files(
                file1_expected_updates={'file1_0': 123}) as \
                (config_file, expected):

            sca = mdl.SolConfArg(config_file)
            actual = sca(['root_5.file1_0=123'])
            self.assertEqual(actual, expected)

        # Set load target (to same)
        with build_config_files() as \
                (config_file, expected):

            # Replace by same.
            sca = mdl.SolConfArg(config_file)
            actual = sca(['root_5=subdir1/file1'])
            self.assertEqual(expected, actual)

            # Replace file1 by file2
            sca = mdl.SolConfArg(config_file)
            actual = sca(['root_5=subdir1/file2'])
            self.assertNotEqual(expected, actual)
            self.assertEqual(
                expected['root_5']['file1_5'],
                actual['root_5'])

    def test_edge_cases(self):
        with file_structure({
                'config.yaml': {
                    'numbers::load': 'numbers/prime',
                    'colors::load': 'colors/reddish'},
                'numbers/prime.yaml': [1, 3, 5],
                'colors/reddish.yaml': {
                    'primary': 'red',
                    'derived': 'pink'}
        }) as (temp_dir, paths):

            # No overrides
            sca = mdl.SolConfArg(paths['config.yaml'])
            self.assertEqual(
                sca([]),
                {'colors': {'derived': 'pink',
                            'primary': 'red'},
                 'numbers': [1, 3, 5]})

            # Clobber-replace the root
            sca = mdl.SolConfArg(paths['config.yaml'])
            self.assertEqual(
                sca(['.*=1']),
                1)

            # Replace with parent references
            sca = mdl.SolConfArg(paths['config.yaml'])
            self.assertEqual(
                sca(['colors..numbers.2=7', 'colors..numbers.2...colors.derived=orange']),
                {'colors': {'derived': 'orange',
                            'primary': 'red'},
                 'numbers': [1, 3, 7]})
