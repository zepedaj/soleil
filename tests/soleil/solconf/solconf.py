from soleil.solconf import solconf as mdl
from .modifiers import build_config_files

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
