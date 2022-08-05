"""
Heuristics for modifying groups of interdependent nodes.

Node modifications can alter other parts of the tree node, so previously modified nodes can potentially be replaced by other un-modified nodes. The methods below provide various heuristics that attempt to modify groups of interdepenent nodes.
"""

from typing import Union, List, Callable
from .dict_container import KeyNode
from .nodes import Node
from .containers import Container
from .dict_container import DictContainer
from .utils import traverse_tree

DEFAULT_MAX_ITERS = 100
"""
The maximum number of iterations to attempt as part of modification heuristics.
"""


def modify_tree(
    node: Union[Node, Callable[[], Node]], iterative=True, max_iters=DEFAULT_MAX_ITERS
):
    """
    Traverses the tree top-down and calls the :meth:`~soleil.solconf.nodes.Node.modify` method of each node, by default iterating over these traversals until all nodes are modified.

    .. warning:: Care must be taken with modifiers that can replace the root node of the tree (e.g., :func:`promote`), as :func:`modify_tree` will exit once the discarded root is fully modified, leaving the modification of the tree with the new root incomplete. This problem can be avoided by using a callable for ``node`` that returns the correct node regardless of modifications. Attaching the tree to a :class:`~soleil.solconf.SolConf` object and using the wrapper method :meth:`SolConf.modify_tree <soleil.solconf.solconf.SolConf.modify_tree>` will do this automatically.

    :param node: The tree's root node or a callable that returns the root node.
    :param iterative: Whether to iterate over traversals until all nodes are modified.
    :param max_iters: The max number of full tree traversals.
    :return: If ``iterative=False``, the number of modified nodes, else ``0``.
    """

    # Convert node to a callable if not the case.
    if isinstance(node, Node):

        def node_callable(x=node):
            return x

    else:
        node_callable = node

    for _ in range(max_iters):

        # Get the node
        node = node_callable()

        # Modify the node
        num_modified = int(not node.modified)
        node.modify()

        # Modify its children
        if isinstance(node, Container):
            for child in list(node.children):
                num_modified += modify_tree(child, iterative=False, max_iters=1)

        if num_modified == 0 or not iterative:
            break

    if iterative and num_modified != 0:
        raise Exception(
            f"Could note finalize node tree modifications after `{max_iters}` iterations."
        )

    return num_modified
