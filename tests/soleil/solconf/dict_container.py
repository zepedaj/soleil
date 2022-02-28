from soleil.solconf import dict_container as mdl

import re
from unittest import TestCase
from pglib.py import setdefaultattr
from soleil.solconf.parser import Parser
from soleil.solconf.nodes import ParsedNode
from soleil.solconf import exceptions
from soleil.solconf.solconf import SolConf

# Test modifiers


def add_val_modif(key, val):
    def wrapper(node):
        modifs = setdefaultattr(node, 'modifs', {})
        modifs[key] = val
    return wrapper

# Test classes


class TestRawKeyPatterns(TestCase):
    def test_split_raw_key(self):
        for raw_key, expected in [
            ('_',
             {'key': '_',
              'types': None,
              'modifiers': None}),
            ('_::',
             {'key': '_',
              'types': None,
              'modifiers': None}),
            ('my_key',
             {'key': 'my_key',
              'types': None,
              'modifiers': None}),
            ('my_key:int',
             {'key': 'my_key',
              'types': 'int',
              'modifiers': None}),
            ('my_key:"my.xerializer:Type"',
             {'key': 'my_key',
              'types': '"my.xerializer:Type"',
              'modifiers': None}),
            ('my_key::modif1,modif2(1,2),modif3',
             {'key': 'my_key',
              'types': None,
              'modifiers': 'modif1,modif2(1,2),modif3'}),
            ('my_key:int:modif1,modif2,modif3(64,"abc",True)',
             {'key': 'my_key',
              'types': 'int', 'modifiers':
              'modif1,modif2,modif3(64,"abc",True)'}),
            ('my_key:"my.xerializer:Type":modif1,modif2,modif3(64,"abc",True)',
             {'key': 'my_key',
              'types': '"my.xerializer:Type"',
              'modifiers': 'modif1,modif2,modif3(64,"abc",True)'}),
            ('my_key:(str,"my.xerializer:Type",float,int):modif1,modif2,modif3(64,"abc",True)',
             {'key': 'my_key',
              'types': '(str,"my.xerializer:Type",float,int)',
              'modifiers': 'modif1,modif2,modif3(64,"abc",True)'}),
        ]:
            self.assertEqual(
                mdl.KeyNode._split_raw_key(raw_key), expected)


class TestKeyNode(TestCase):
    @classmethod
    def get_node(cls, key='my_key'):
        parser = Parser({'add_val': add_val_modif})
        node = mdl.KeyNode(
            f'{key}:int:add_val(0, "abc"),add_val(1,2),add_val(2,True)',
            ParsedNode('$:10+1', parser),
            parser=parser)
        return node

    def test_all(self):

        node = self.get_node()

        # Modify the node
        node.modify()
        node.value.modify()

        # Check modifications
        self.assertEqual(node.value.modifs[0], 'abc')
        self.assertEqual(node.value.modifs[1], 2)
        self.assertEqual(node.value.modifs[2], True)

        #
        self.assertEqual(node.resolve(), ('my_key', 11))

    def test_modify_exceptions(self):

        # Types string error
        with self.assertRaisesRegex(exceptions.RawKeyComponentError, re.escape(
                "Error while parsing the raw key `types` string `invalid_type` of node `KeyNode@'*abc'`.")):
            SolConf({'abc:invalid_type': 1})()

        # Modifiers string error
        with self.assertRaisesRegex(exceptions.RawKeyComponentError, re.escape(
                "Error while parsing the raw key `modifiers` string `invalid_modif` of node `KeyNode@'*abc'`.")):
            SolConf({'abc::invalid_modif': 1})()

        # Modification error
        with self.assertRaisesRegex(
                exceptions.ModificationError,
                re.escape(
                    "Error while applying modifier `functools.partial(<function parent at 0x") +
                r'\w+' + re.escape(">, 4)` to node `ParsedNode@'abc'`.")):
            SolConf({'abc::parent(4)': 1})()


class TestDictContainer(TestCase):

    def test_hashing(self):
        node1 = TestKeyNode.get_node()
        node2 = TestKeyNode.get_node()
        node3 = TestKeyNode.get_node('my_key_3')

        container = mdl.DictContainer()
        container.add(node1)
        container.add(node2)
        container.add(node3)

        self.assertEqual(len(container.children), 2)
        # Both hashes match, so retreiven node1 or node2
        # should result in the same node.
        self.assertIs(container.children[node1], node2)

    def test_keynode_change_key(self):
        node1 = TestKeyNode.get_node()
        node2 = TestKeyNode.get_node()

        container = mdl.DictContainer()
        [container.add(x) for x in [node1, node2]]

        # Test parent relationships.
        self.assertIs(node1.parent, None)
        self.assertIs(node2.parent, container)

        # Test renaming bound KeyNode
        node1.key = 'abc'  # Works, as node1 was removed when adding node2.
        with self.assertRaisesRegex(
                Exception,
                re.escape(f'Remove `{node2}` from parent container before re-naming.')):
            node2.key = 'abc'

        # Test removal
        self.assertEqual(
            {'my_key'}, set(container.children.keys()))
        container.remove(node2)
        self.assertEqual(
            set(), set(container.children.keys()))

    def test_qual_name(self):

        #
        ac = SolConf({'node0': {'node1': 1}})

        #
        assert ac.node_tree.qual_name == ''

        # Refer to the key node.
        node = ac['node0']['*node1']
        assert type(node) is mdl.KeyNode
        assert node is ac.node_tree.children['node0'].value.children['node1']
        assert node.qual_name == 'node0.*node1'
        assert ac.node_tree.node_from_ref(node.qual_name) is node

        # Refer to the value node.
        node = ac['node0']['node1']
        assert type(node) is mdl.ParsedNode
        assert node is ac.node_tree.children['node0'].value.children['node1'].value
        assert node.qual_name == 'node0.node1'
        assert ac.node_tree.node_from_ref(node.qual_name) is node
