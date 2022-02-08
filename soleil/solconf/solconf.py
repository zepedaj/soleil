import yaml
from .containers import ListContainer
from .dict_container import DictContainer, KeyNode
from .nodes import ParsedNode, Node
from .ast_parser import Parser
from . import varnames


class SolConf:

    parser: Parser
    """
    The parser used when parsing :class:`ParsedNode` nodes.
    """
    node_tree: Node
    """
    The root node.
    """

    def __init__(self, raw_data, context: dict = {}, parser=None, modify=True):
        """
        :param raw_data: The data to convert to an :class:`SolConf` object.
        :param context: Extra parameters to add to the parser context.
        :param parser: The parser to use (instantiated internally by default). If a parser is provided, ``context`` is ignored.
        """

        self.parser = parser or Parser(context)
        self.node_tree = self.build_node_tree(raw_data, parser=self.parser)
        self.node_tree._alpha_conf_obj = self  # Needed to support Node.alpha_conf_obj propagation
        self.parser.register(varnames.ROOT_NODE_VAR_NAME, self.node_tree)
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
        Traverses the tree starting at the root and calls method ``modify`` on all nodes that have that method.

        If a node has a method ``modify``, tree traversal is not continued further down that node.
        """
        root = root or self.node_tree

        if hasattr(root, 'modify'):
            root.modify()
        elif hasattr(root, 'children'):
            for child in list(root.children):
                # Some nodes might modify the node tree. Taking a snapshot here with list()
                # avoids errors related to modifying the childrens iterable while iterating
                # over it.
                self.modify(child)

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
        return self.node_tree.resolve(*args)

    def resolve(self):
        return self.node_tree.resolve()

    def __getitem__(self, *args):
        return self.node_tree.__getitem__(*args)
