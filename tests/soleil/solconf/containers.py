from soleil.solconf import containers as mdl

from soleil.solconf.parser import Parser
from unittest import TestCase
from soleil.solconf.nodes import ParsedNode


class TestListContainer(TestCase):

    @classmethod
    def get_node(cls, value='$:"abc"'):
        parser = Parser()
        return ParsedNode(value, parser)

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
