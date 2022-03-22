from soleil.solconf import containers as mdl, SolConf

from soleil.solconf.parser import Parser
from unittest import TestCase
from soleil.solconf.nodes import ParsedNode


class TestListContainer(TestCase):

    @classmethod
    def get_node(cls, value='$:"abc"'):
        parser = Parser()
        return ParsedNode(value, parser=parser)

    def test_all(self):

        for (values, expected) in [
                (('$:"abc"', '$:1+3'), ['abc', 4]),
                (tuple(), []),
        ]:

            #
            container = mdl.ListContainer()
            [container.add(self.get_node(x)) for x in values]

            #
            self.assertEqual(
                container.resolve(),
                expected)

    def test_get_child_posn(self):
        node = SolConf([0, 1, 2, 3]).root
        self.assertEqual(len(node), 4)
        for k in range(len(node)):
            self.assertEqual(node.get_child_posn(node.children[k]), k)

    def test_replace(self):
        sc = SolConf([0, 1, 2, 3])
        node = sc.root
        node.replace(node.children[1], ParsedNode(10, parser=sc.parser))

        self.assertEqual(sc(), [0, 10, 2, 3])
