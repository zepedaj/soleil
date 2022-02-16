"""

"""

import yaml
from contextlib import nullcontext
from typing import Optional
from .containers import ListContainer
from .modification_heuristics import modify_tree
from .dict_container import DictContainer, KeyNode
from .nodes import ParsedNode, Node
from .parser import Parser
from threading import RLock
from pathlib import Path


class SolConf:

    """
    Soleil configuration object that builds a node tree and invokes the modifier methods of all :class:`~soleil.solconf.dict_container.KeyNode` nodes in the tree. Exposes a :class:`__call__` method that is an alias to the root node's call method and accordingly resolves |dstrings| and cross-references for the entire tree.

    Partially implements the :class:`~soleil.solconf.containers.Container` interface.


    .. rubric:: Workflow

    As part of initialization, the following sequence of steps occurs:

    1. The node tree is built completely by recursively traversing the input raw content top-down.
    2. All :class:`modify` methods are called and applied top-down. This behaviour is implicit in the default implementations of :meth:`KeyNode.modify <soleil.solconf.dict_container.KeyNode.modify>` and :meth:`Container.modify <soleil.solconf.containers.Container.modify>`.

    After initializaion,

    3. upon invoking the object's :meth:`__call__` method, the node tree is resolved.


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
    def root(self) -> Node:
        """
        The root node.
        """
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
            self.modify_tree()

    @classmethod
    def load(self, path, **kwargs) -> 'SolConf':
        """
        Returns an :class:`SolConf` object built using raw data retrieved from the specified file.

        :param path: The path to the file to load the raw data from.
        :param kwargs: Extra arguments to pass to the :class:`SolConf` initializer.
        """
        path = Path(path)
        with open(path, 'rt') as fo:
            text = fo.read()
        modify = kwargs.pop('modify', True)
        ac = SolConf(raw_data := yaml.safe_load(text), modify=False, **kwargs)
        ac.node_tree._source_file = path
        if modify:
            ac.modify_tree()
        return ac

    def modify_tree(self, node=None, **kwargs) -> Optional[Node]:
        """
        An alias to :func:`containers.modify_tree <soleil.solconf.containers.modify_tree`> that sets ``node`` to :attr:`root` if unspecified.
        """
        return modify_tree(node or self.root, **kwargs)

    @classmethod
    def build_node_tree(cls, raw_data, parser, parent=None) -> Node:
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
        """
        An alias to the :attr:`root` node's :meth:`__call__` method.
        """
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
            if new_node.parent:
                new_node.parent.remove(new_node)
            new_node._sol_conf_obj = self
            self.node_tree = new_node

    def __getitem__(self, *args):
        return self.node_tree.__getitem__(*args)
