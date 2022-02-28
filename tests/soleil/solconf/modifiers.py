from unittest import TestCase
from ._helpers import file_structure
from soleil.solconf.modifiers import noop
import re
from soleil.solconf.parser import Parser
from soleil.solconf.nodes import ParsedNode
from soleil.solconf.dict_container import KeyNode
from soleil.solconf.solconf import SolConf
from soleil.solconf import modifiers as mdl  # noqa
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
            value_node := ParsedNode('$:(n_, parent(n_))', parser=parser),
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
            # self.assertTrue(node[1]['b'].hidden)

            resolved_value = node.resolve()
            self.assertEqual(resolved_value, expected_resolved_value)

    def test_load(self):
        # (config_file, (root_dat, file1_dat, file2_dat)):
        with build_config_files() as (config_file, expected):
            super_root = {'super_root::load': str(config_file.absolute())}
            ac = SolConf(super_root)
            resolved = ac.resolve()['super_root']

            self.assertEqual(expected, resolved)

    def test_load__relative(self):
        with build_config_files() as (config_file, expected):
            # relative load
            config_root = str(config_file.parent.absolute())
            super_root = {f'_::load("{config_root}/subdir1")': 'file1'}
            sc = SolConf(super_root)

            resolved = sc()
            self.assertEqual(resolved, {'_': expected['root_5']})

    def test_promote(self):

        sc = SolConf({'a': {'x:int:promote': 0}})
        self.assertEqual(sc(), {'a': 0})

        sc = SolConf({'x:int:promote': 0})
        assert sc() == 0

        sc = SolConf([{'x:int:promote': 0}])
        self.assertEqual(sc(), [0])

        sc = SolConf(
            [{'x:int:promote': 0},
             1,
             {'y:float:promote': "$: float(r_[0]() + 2*r_('1'))"}])
        self.assertEqual(sc(), [0, 1, 2.0])

        sc = SolConf({
            'a': {'x:bool:promote': False},
            'b': '$: r_["a"]()'})
        self.assertEqual(sc(), {'a': False, 'b': False})

        sc = SolConf({
            'a': {'x:bool:promote,hidden': False},
            'b': '$: r_["a"]()'})
        self.assertEqual(sc(), {'b': False})

    def test_special_vars_in_modifier_string(self):
        #
        sc = SolConf([0, {"x:int:promote,choices(r_('0'),1)": 1}])
        assert sc() == [0, 1]

        #
        sc = SolConf(
            {
                'base': 'red',
                'fancy_versions': "$: {'red': 'fuscia', 'green': 'chartreuse'}",
                "fancy_base:str:choices(*list(values(r_('fancy_versions'))))": "$: r_('fancy_versions')[r_('base')]"})
        self.assertEqual(
            sc(), {'base': 'red',
                   'fancy_versions': {'red': 'fuscia', 'green': 'chartreuse'},
                   'fancy_base': 'fuscia'})

    def test_choices(self):

        #
        sc = SolConf({'_:int:promote,choices(1,2,3)': 1})
        self.assertEqual(sc(), 1)
        #
        sc = SolConf({'_:int:choices(1,2,3),promote': 1})
        self.assertEqual(sc(), 1)

        # Check KeyNode dereferencing ability
        #
        sc = SolConf({'_:int:choices(1,2,3),promote': 4})
        with self.assertRaisesRegex(
                ValueError,
                re.escape("The resolved value of `ParsedNode@''` is `4`, but it must be one of `(1, 2, 3)`.")):
            sc()

        #
        sc = SolConf({'_:int:promote,choices(1,2,3)': 4})
        with self.assertRaisesRegex(
                ValueError,
                re.escape("The resolved value of `ParsedNode@''` is `4`, but it must be one of `(1, 2, 3)`.")):
            sc()

    def test_load_with_choices(self):

        # Source choice.
        with build_config_files(
                file1_updates={"file1_6::choices('file3'),load": 'file2'}
        ) as (config_file, expected):
            try:
                sc = SolConf.load(config_file)
            except Exception as err:
                self.assertRegex(
                    str(err.__cause__),
                    '.*' + re.escape("is `file2`, but it must be one of `('file3',)`."))
            else:
                raise Exception('Error expected!')

        # Source choice and loaded choice
        with build_config_files(
                file1_updates={"file1_6::choices('file2'),load,choices([0])": 'file2'}
        ) as (config_file, expected):
            sc = SolConf.load(config_file)
            try:
                sc()
            except Exception as err:
                self.assertRegex(
                    str(err.__cause__),
                    '.*' + re.escape(", but it must be one of `([0],)`."))
            else:
                raise Exception('Exception expected!')

    def test_hidden_and_promote_order(self):

        for modifiers_str in ['promote,hidden', 'hidden,promote']:
            sc = SolConf({'a0': {f'x:bool:{modifiers_str}': False}, 'a1': "$: r_['a0']()"})
            self.assertEqual(sc(), {'a1': False})

    def test_extends(self):

        # Simple
        with file_structure({
                'config_source.yaml': {'a': 1, 'b:int': 2, 'c:float,int:noop': 3, 'd::noop': 4},
                'config_extends.yaml': {"_::extends('config_source'),promote": {'b': 3, 'e': 5}}}
        ) as (tmp_dir, paths):
            sc = SolConf.load(paths['config_extends.yaml'])
            self.assertEqual((sc['a'].types, sc['a'].modifiers), (None, tuple()))
            self.assertEqual((sc['b'].types, sc['b'].modifiers), ((int,), tuple()))
            self.assertEqual((sc['c'].types, sc['c'].modifiers), ((float, int), (mdl.noop,)))
            self.assertEqual((sc['d'].types, sc['d'].modifiers), (None, (mdl.noop,)))
            self.assertEqual(sc(), {'a': 1, 'b': 3, 'c': 3, 'd': 4, 'e': 5})

        # With x_ cross-ref
        with file_structure({
            'config_source.yaml': {'a::noop': 1, 'b': 2, 'c': 3},
            'config_extends.yaml': {
                "_::extends('config_source'),promote": {"a::modifiers(x_)": 0, "d": 4}}}
        ) as (temp_dir, path_mappings):
            sc = SolConf.load(path_mappings['config_extends.yaml'])
            self.assertEqual(sc['a'].modifiers, (noop,))
            self.assertEqual(
                sc(),
                {'a': 0, 'b': 2, 'c': 3, 'd': 4})
