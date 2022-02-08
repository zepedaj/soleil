from unittest import TestCase
from soleil.solconf.ast_parser import Parser
from soleil.solconf.nodes import ParsedNode
from soleil.solconf.dict_container import KeyNode
from soleil.solconf.solconf import SolConf
from soleil.solconf import modifiers as mdl
from tempfile import TemporaryDirectory
from pathlib import Path
import yaml
import contextlib


@contextlib.contextmanager
def build_config_files(
        root_updates=None, root_expected_updates=None,
        file1_updates=None, file1_expected_updates=None,
        file2_updates=None, file2_expected_updates=None):
    # ./root.yaml
    root_dat = dict((f'root_{k}', k) for k in range(5))
    root_dat['root_5::load'] = 'subdir1/file1'
    root_dat.update(root_updates or {})

    # ./subdir1/file1.yaml
    file1_dat = dict((f'file1_{k}', k) for k in range(5))
    file1_dat['file1_5::load'] = 'file2'
    file1_dat.update(file1_updates or {})

    # ./subdir1/file2.yaml
    file2_dat = dict((f'file2_{k}', k) for k in range(5))
    file2_dat.update(file2_updates or {})

    #
    expected = dict(root_dat)
    expected.pop('root_5::load')
    expected.update(root_expected_updates or {})
    #
    expected['root_5'] = dict(file1_dat)
    expected['root_5'].pop('file1_5::load')
    expected['root_5'].update(file1_expected_updates or {})
    #
    expected['root_5']['file1_5'] = dict(file2_dat)
    expected['root_5']['file1_5'].update(file2_expected_updates or {})

    # Build file structure
    with TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)
        (temp_dir / 'subdir1').mkdir()
        for sub_path, dat in [
                ('root.yaml', root_dat),
                ('subdir1/file1.yaml', file1_dat),
                ('subdir1/file2.yaml', file2_dat)
        ]:
            with open(temp_dir / sub_path, 'wt') as fo:
                yaml.dump(dat, fo)
        yield temp_dir/'root.yaml', expected


class TestModifiers(TestCase):

    def test_parent(self):
        parser = Parser()
        key_node = KeyNode(
            'my_name',
            value_node := ParsedNode('$(n_, parent(n_))', parser=parser),
            parser=parser)
        self.assertEqual(resolved := key_node.resolve(), ('my_name', (value_node, key_node)))
        self.assertIs(resolved[1][0], value_node)
        self.assertIs(resolved[1][1], key_node)

    def test_hidden(self):

        for node, expected_resolved_value in [
                (SolConf([
                    0,
                    {'a': 1, 'b::hidden': 2, 'c': [3, 4]},
                    [5, {'d': 6, 'e': 7}, 8],
                ]).node_tree,
                    [
                    0,
                    {'a': 1, 'c': [3, 4]},
                    [5, {'d': 6, 'e': 7}, 8],
                ]),
        ]:

            self.assertTrue(node[1]['*b'].hidden)
            self.assertTrue(node[1]['b'].hidden)

            resolved_value = node.resolve()
            self.assertEqual(resolved_value, expected_resolved_value)

    def test_load(self):
        # (config_file, (root_dat, file1_dat, file2_dat)):
        with build_config_files() as (config_file, expected):
            super_root = {'super_root::load': str(config_file.absolute())}
            ac = SolConf(super_root)
            resolved = ac.resolve()['super_root']

            self.assertEqual(expected, resolved)
