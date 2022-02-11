import yaml
from contextlib import nullcontext
from typing import Optional
from .containers import ListContainer
from .dict_container import DictContainer, KeyNode
from .nodes import ParsedNode, Node
from .parser import Parser
from . import varnames
from threading import RLock


class SolConf:

    """
    Soleil configuration object that builds a node tree and resolves :class:`~soleil.solconf.dict_container.KeyNode` decorators, |dstrings|, and cross-references.

    Partiall implements the :class:`~soleil.solconf.containers.Container` interface.
    """

    parser: Parser
    """
    The parser used when parsing :class:`ParsedNode` nodes.
    """
    node_tree: Node
    """
    The root node.
    """
    lock: RLock
    """
    Threading lock used when modifying the object.<
    """

    @property
    def root(self):
        return self.node_tree

    def __init__(self, raw_data, context: dict = {}, parser=None, modify=True):
        """
        :param raw_data: The data to convert to an :class:`SolConf` object.
        :param context: Extra parameters to add to the parser context.
        :param parser: The parser to use (instantiated internally by default). If a parser is provided, ``context`` is ignored.
        """

        self.parser = parser or Parser(context)
        root = self.build_node_tree(raw_data, parser=self.parser)
        self.lock = RLock()
        self.node_tree = None
        self.replace(None, root)
        if modify:
            self.modify()

    @classmethod
    def load(self, path, **kwargs):
        """
        Returns an :class:`SolConf` object built using raw data retrieved from the specified file.

        :param path: The path to the file to load the raw data from.
        :param kwargs: Extra arguments to pass to the :class:`SolConf` initializer.
        """
        with open(path, 'rt') as fo:
            text = fo.read()
        modify = kwargs.pop('modify', True)
        ac = SolConf(raw_data := yaml.safe_load(text), modify=False, **kwargs)
        ac.node_tree._source_file = path
        if modify:
            ac.modify()
        return ac

    def modify(self, root=None):
        """
        Traverses the tree starting at the root and calls method ``modify`` on all nodes that have that method, and all its children.

        If a node has a modify object, its children will not be modified. It is that node's responsibility to modify its own children. This enables the createion of modifiers that change the sub-tree, in which case modification of the changed sub-tree will be their responsibility.
        """
        root = root or self.node_tree

        if hasattr(root, 'modify'):
            root.modify()

    @classmethod
    def build_node_tree(cls, raw_data, parser, parent=None):
        """
        Recursively converts the input raw_data into a node tree. Lists and dictionaries in the tree
        will result in nested levels.
        """

        #
        if isinstance(raw_data, dict):
            # Create a dictionary container.
            out = DictContainer()
            for key, val in raw_data.items():
                key_node = KeyNode(
                    key, cls.build_node_tree(val, parser), parser=parser)
                out.add(key_node)  # Sets parent.

        elif isinstance(raw_data, list):
            # Create a list container.
            out = ListContainer()
            for val in raw_data:
                out.add(cls.build_node_tree(val, parser))  # Sets parent.

        else:
            # Create a parse node.
            out = ParsedNode(
                raw_data, parser=parser)

        #
        return out

    def __call__(self, *args):
        with self.lock:
            return self.node_tree(*args)

    def resolve(self):
        with self.lock:
            return self.node_tree.resolve()

    def replace(self, old_node: Optional[Node], new_node: Node):
        """
        Sets or replaces :attr:`node_tree`. The old node is dissociated from ``self`` and the new node associated so that the :attr:`~Node.sol_conf_obj` attritutes of all tree nodes return ``self``.
        """
        old_node = old_node or self.node_tree
        with self.lock, (old_node.lock if old_node else nullcontext()), new_node.lock:

            # Check valid old node.
            if old_node and old_node is not self.root:
                raise Exception(
                    f'The provided target node `{old_node}` is not '
                    f'at the root of the node tree `{self.root}`.')

            # Remove self from old node.
            if old_node:
                old_node._sol_conf_obj = None

            # Add self to new node
            new_node._sol_conf_obj = self
            self.node_tree = new_node

            # Replace root node var r_ in parser context
            self.parser.register(varnames.ROOT_NODE_VAR_NAME, self.node_tree)

    def __getitem__(self, *args):
        return self.node_tree.__getitem__(*args)
