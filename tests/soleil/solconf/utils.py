from soleil.solconf import utils as mdl

from unittest import TestCase
from soleil import SolConf


class TestFunctions(TestCase):

    def test_traverse_tree(self):
        sc = SolConf({'a': {'b': 0}})
        nodes = set(map(lambda x: x.qual_name, mdl.traverse_tree(sc.root)))
        self.assertEqual(nodes, {'', '*a', 'a',  'a.*b', 'a.b'})
