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

    def test_choices_docs(self):
        with file_structure({
                'config_source.yaml': {'a': 1, 'b:float:': 2.0, 'c:int:choices(1,3,5)': 3},
                'config_extends.yaml': {"_::extends('config_source'),promote":
                                        {'b': 3.0, 'c:float': 5.0}}
        }) as (tmp_dir, paths):
            sc = SolConf.load(paths['config_extends.yaml'])
            self.assertTrue(isinstance(sc['c'].modifiers[0], mdl.choices))

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

    def test_extends(self):

        # Simple
        with file_structure({
                'config_source.yaml': {'a': 1, 'b:int': 2, 'c:float,int:noop': 3, 'd::noop': 4, 'a1:int:noop': 10, 'e': {'f::noop': 11}},
                # 'config_extends.yaml': {"_::extends('config_source'),promote": {'b': 3, 'e': 5, 'a1:None:None': 10}}}
                'config_extends.yaml': {"_::extends('config_source'),promote": {'b': 3, 'a1:None:None': 10, 'e': {'f': 12}}}}
        ) as (tmp_dir, paths):
            sc = SolConf.load(paths['config_extends.yaml'])
            self.assertEqual((sc['a'].types, sc['a'].modifiers), (None, tuple()))
            self.assertEqual((sc['b'].types, sc['b'].modifiers), ((int,), tuple()))
            self.assertEqual((sc['c'].types, sc['c'].modifiers), ((float, int), (mdl.noop,)))
            self.assertEqual((sc['d'].types, sc['d'].modifiers), (None, (mdl.noop,)))
            self.assertEqual((sc['a1'].types, sc['a1'].modifiers), (None, ()))
            self.assertEqual(sc(), {'a': 1, 'b': 3, 'c': 3, 'd': 4, 'a1': 10, 'e': {'f': 12}})

    def test_extends__xrefs(self):
        # With x_ cross-ref
        with file_structure({
            'config_source.yaml': {'a::noop': 1, 'b': 2, 'c:int': 3, 'd': {'e:int:noop': 10}},
            'config_extends.yaml': {
                "_::extends('config_source'),promote": {"a::modifiers(x_)+(noop,)": 0, 'd': {'e::modifiers(x_)+(noop,)': 11}}}}
        ) as (temp_dir, path_mappings):
            sc = SolConf.load(path_mappings['config_extends.yaml'])
            self.assertEqual(sc['a'].modifiers, (noop, noop))
            self.assertEqual(sc['d']['e'].modifiers, (noop, noop))
            self.assertEqual(sc['d']['e'].types, (int,))
            self.assertEqual(
                sc(),
                {'a': 0, 'b': 2, 'c': 3, 'd': {'e': 11}})

    def test_extends__node(self):
        sc = SolConf(
            {'a::noop': {'a0': "$:2-1"},
             'b::extends(r_["d"])': {'e': 4},
             'c:int': 3,
             'd': {'e:int:noop': 10, 'f': "$: 10+1", 'g::extends(r_["a"])': {}}},
            modify=False)

        # Check that ParseNode raw values are converted to literal values.
        modify_tree(sc['*b'])
        #
        sc.modify_tree()

        self.assertEqual(
            sc(),
            {'a': {'a0': 1},
             'b': {'e': 4, 'f': 11, 'g': {'a0': 1}},
             'c': 3, 'd': {'e': 10, 'f': 11, 'g': {'a0': 1}}}
        )

    def test_extends__node_chained(self):
        sc = SolConf(
            {'a::noop': {'a0': "$:2-1", 'b0': '$:3-1', 'c0': '$:4-1'},
             'b::extends(r_["a"])': {'a0': -1},
             'c::extends(r_["b"])': {'b0': -2}},
            modify=False)
        #
        modify_tree(sc['c'])
        self.assertTrue(sc['a'].modified)
        self.assertTrue(sc['b'].modified)
        self.assertTrue(sc['c'].modified)

        self.assertEqual(
            sc(),
            {'a': {'a0': 1, 'b0': 2, 'c0': 3},
             'b': {'a0': -1, 'b0': 2, 'c0': 3},
             'c': {'a0': -1, 'b0': -2, 'c0': 3}})

    def test_extends__decorators(self):
        sc = SolConf(
            {'a:dict': {'a0': 1},
             'b::extends(r_["a"])': {'a0:int:promote': '$:x_()'}})
        self.assertEqual(
            sc(),
            {'a': {'a0': 1},
             'b': 1})

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
