from soleil.solconf import solconf as mdl
from .modifiers import build_config_files
from .nodes import ParsedNode

from unittest import TestCase


class TestSolConf(TestCase):

    def test_build_node_tree(self):

        for raw_data, expected in [
                #
                (1, 1),
                #
                ([1, {'a': 2, 'b': '$:3+1', 'c': "$:'xyz'", 'd': [1, 2, '$:"alpha"']},
                  2, {'e': '$:2**3'}],
                 [1, {'a': 2, 'b': 4, 'c': 'xyz', 'd': [1, 2, 'alpha']},
                  2, {'e': 8}]),
                #
                (['abc', {'a': 2, 'b': '$:3+1', 'c': "$:'xyz'", 'd': [1, 2, "$:r_('0')", "$:r_[0]() + 'x'"]},
                  2, {'e': '$:2**3'}],
                 ['abc', {'a': 2, 'b': 4, 'c': 'xyz', 'd': [1, 2, 'abc', 'abcx']},
                  2, {'e': 8}]),
        ]:
            self.assertEqual(
                resolved := (ac_obj := mdl.SolConf(raw_data)).resolve(),
                expected)
            self.assertIs(type(resolved), type(expected))

    def test_resolve_root(self):

        raw_data = [1, {'a': 2, 'b': '$:3+1', 'c': "$:'xyz'", 'd': [1, 2, '$:r_']},
                    2, {'e': '$:2**3'}]
        aconf = mdl.SolConf(raw_data)
        self.assertIs(
            aconf.node_tree, aconf.resolve()[1]['d'][2])

    def test_load(self):
        with build_config_files() as (path, expected):
            ac = mdl.SolConf.load(path)
            dat = ac()
            self.assertEqual(dat, expected)

    def test_replace(self):
        sc = mdl.SolConf({'a': 0, 'b': 1})

        assert sc() == {'a': 0, 'b': 1}

        old_node = sc.node_tree
        assert sc.node_tree.sol_conf_obj is sc

        new_node = ParsedNode(10, parser=sc.parser)
        sc.replace(None, new_node)

        assert old_node.sol_conf_obj is None
        assert sc() == 10
        assert sc.root is new_node

    def test_basic(self):
        assert mdl.SolConf({'_::': 1})() == {'_': 1}
