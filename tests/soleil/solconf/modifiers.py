from unittest import TestCase
from functools import partial
import traceback
import numpy as np
from ._helpers import file_structure
from soleil.solconf.modifiers import noop
from soleil.solconf.modification_heuristics import modify_tree
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

    #######################################################
    # USE ._helpers.file_structure INSTEAD OF THIS METHOD!
    #######################################################

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
            raw_key='my_name',
            value=(value_node := ParsedNode('$:(n_, parent(n_))', parser=parser)),
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
            sc = SolConf(super_root)
            resolved = sc()['super_root']

            self.assertEqual(expected, resolved)

    def test_load__relative(self):
        with build_config_files() as (config_file, expected):
            # relative load
            config_root = str(config_file.parent.absolute())
            super_root = {f'_::load("{config_root}/subdir1")': 'file1'}
            sc = SolConf(super_root)

            resolved = sc()
            self.assertEqual(resolved, {'_': expected['root_5']})

    def test_load__substitution(self):
        with file_structure({
                'config_source.yaml': {'a': 1, "b::load(vars={'d':7.0})": 'config_load'},
                'config_load.yaml': {'c': 3.0, 'd:float': 5.0}}
        ) as (tmp_dir, paths):
            self.assertEqual(
                SolConf.load(paths['config_source.yaml'])(),
                {'a': 1, 'b': {'c': 3.0, 'd': 7.0}})

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
        for key in ['_:int:choices(1,2,3),promote', '_:int:promote,choices(1,2,3)']:
            sc = SolConf({key: 4})
            try:
                sc()
            except Exception:
                self.assertIsNotNone(re.search(re.escape(
                    "The resolved value of `ParsedNode@''` is `4`, but it must be one of `(1, 2, 3)`."),
                    traceback.format_exc()))
            else:
                raise Exception('Exception expected!')

    def test_load_with_choices(self):

        # Source choice.
        with build_config_files(
                file1_updates={"file1_6::choices('file3'),load": 'file2'}
        ) as (config_file, expected):
            try:
                sc = SolConf.load(config_file)
            except Exception:
                self.assertIsNotNone(re.search(
                    '.*' + re.escape("is `file2`, but it must be one of `('file3',)`."),
                    traceback.format_exc()))
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

    def test_fuse(self):

        # Fuse
        sc = SolConf({'_::fuse':
                      {'value': 1,
                       'types': 'int',
                       'modifiers': 'noop'}
                      })

        self.assertEqual(sc.root['_'].types, (int,))
        self.assertEqual(sc.root['_'].modifiers, (noop,))
        self.assertEqual(sc(), {'_': 1})

        # Fuse, fused promote
        sc = SolConf({'_::fuse':
                      {'value': 1,
                       'types': 'int',
                       'modifiers': 'promote'}
                      })

        self.assertEqual(sc.root.types, (int,))
        self.assertEqual(sc.root.modifiers, (mdl.promote,))
        self.assertEqual(sc(), 1)

        # Fuse, raw-key promote
        sc = SolConf({'_::fuse,promote':
                      {'value': 1,
                       'types': 'int',
                       'modifiers': 'noop'}
                      })

        self.assertEqual(sc.root.types, (int,))
        self.assertEqual(sc.root.modifiers, (mdl.noop,))
        self.assertEqual(sc(), 1)

        # Fuse, partial keys
        sc = SolConf({'_::fuse,promote':
                      {'value': 1}
                      })

        self.assertEqual(sc(), 1)

        #

    def test_docs(self):

        # Fuse-based syntax
        sc_fused = SolConf(
            {'base::fuse': {
                'value': '$: 1+2',
                'types': 'int',
                'modifiers': 'noop'
            }}
        )

        # Equivalent raw key-based syntax
        sc_rk = SolConf({'base:int:noop': '$: 1+2'})

        self.assertEqual(
            (sc_fused['base'].types, sc_rk['base'].types),
            ((int,), (int,)))

        self.assertEqual(
            (sc_fused['base'].modifiers, sc_rk['base'].modifiers),
            ((noop,), (noop,)))

        self.assertEqual(
            (sc_fused['base'].raw_value, sc_rk['base'].raw_value),
            ('$: 1+2', '$: 1+2'))

        self.assertEqual(
            (sc_fused(), sc_rk()),
            ({'base': 3}, {'base': 3}))

        ###

        # Fuse-based syntax: lists
        sc_fused = SolConf(
            {'base::fuse': {
                'value': '$: 1+2',
                'types': ['int', 'float'],
                'modifiers': ['noop', 'choices(1,2,3)']
            }}
        )

        self.assertEqual(
            sc_fused['base'].types, (int, float))
        self.assertEqual(len(sc_fused['base'].modifiers), 2)
        self.assertEqual(sc_fused['base'].modifiers[0], mdl.noop)
        self.assertEqual(type(sc_fused['base'].modifiers[1]), mdl.choices)

    def test_cast(self):
        out = SolConf({'_:dt64:cast(dt64),promote': '2020-10-10'})()
        self.assertIsInstance(out, np.datetime64)
        self.assertEqual(out, np.datetime64('2020-10-10'))

    def test_derives(self):
        # Vanilla
        with file_structure({
            'config_source.yaml': {'x::load()': 'config_derives', 'y::derives(f_["x"])': {}},
            'config_derives.yaml': {'c': 2, 'd': 3, 'e': 4}
        }) as (temp_dir, path_mappings):
            out = SolConf.load(path_mappings['config_source.yaml'])()
            self.assertEqual(
                out,
                {'x': {'c': 2, 'd': 3, 'e': 4},
                 'y': {'c': 2, 'd': 3, 'e': 4}})

        # New params
        with file_structure({
            'config_source.yaml': {'x::load()': 'config_derives', 'y::derives(f_["x"])': {'a': 0, 'b': 1}},
            'config_derives.yaml': {'c': 2, 'd': 3, 'e': 4}
        }) as (temp_dir, path_mappings):
            out = SolConf.load(path_mappings['config_source.yaml'])()
            self.assertEqual(
                out,
                {'x': {'c': 2, 'd': 3, 'e': 4},
                 'y': {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4}})

        # Overrides params
        with file_structure({
            'config_source.yaml': {'x::load()': 'config_derives', 'y::derives(f_["x"])': {'a': 0, 'b': 1, 'c': -2}},
            'config_derives.yaml': {'c': 2, 'd': 3, 'e': 4}
        }) as (temp_dir, path_mappings):
            out = SolConf.load(path_mappings['config_source.yaml'])()
            self.assertEqual(
                out,
                {'x': {'c': 2, 'd': 3, 'e': 4},
                 'y': {'a': 0, 'b': 1, 'c': -2, 'd': 3, 'e': 4}})

        # Chained derivations
        with file_structure({
            'config_source.yaml': {'x::load()': 'config_derives_0', 'y::derives(f_["x"])': {'a': 0, 'b': 1}},
            'config_derives_0.yaml': {'c': 2, 'z::load()': 'config_derives_1'},
            'config_derives_1.yaml': {'d': 3, 'e': 4}
        }) as (temp_dir, path_mappings):
            out = SolConf.load(path_mappings['config_source.yaml'])()
            self.assertEqual(
                out,
                {'x': {'c': 2, 'z': {'d': 3, 'e': 4}},
                 'y': {'a': 0, 'b': 1, 'c': 2, 'z': {'d': 3, 'e': 4}}})

        # Super unaffected (unfortunately)
        with file_structure({
            'config_source.yaml': {'x::load()': 'config_derives', 'y::derives(f_["x"])': {'c': -2}},
            'config_derives.yaml': {'c': 2, 'd': '$:n_("..c")'},
        }) as (temp_dir, path_mappings):
            out = SolConf.load(path_mappings['config_source.yaml'])()
            self.assertEqual(
                out,
                {'x': {'c': 2, 'd': 2},
                 'y': {'c': -2, 'd': 2}})
