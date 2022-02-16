"""
Base node modifiers included by default in :class:`soleil.solconf.parser.Parser` contexts.
"""
from .parser import register
from functools import partial
import yaml
from .nodes import FLAGS
from .dict_container import KeyNode, DictContainer
from .nodes import Node
from .solconf import SolConf
from pathlib import Path
from .functions import cwd
from .utils import _Unassigned
from .varnames import DEFAULT_EXTENSION


@register('parent')
def parent(node_or_levels: Node = None, levels=None):
    """
    Returns, for the given node, the ancestor at the specified number of levels up. Use ``levels=0`` to denote the node itself.

    By default, levels will be set internally to ``levels=1`` if not explicitly assigned.

    ..rubric:: Syntax:

    .. code-block::

        # No-op modifier
        parent(0)

        # Modifier that returns the parent
        parent
        parent(1)
        parent(levels=1)

        # Modifier that returns the grandparent
        parent(2)
        parent(levels=2)

        # Can be used as a function
        parent(node)
        parent(node, 2)
        parent(node, levels=2)

    """

    # Check if this is a modification call or a modifier definition call.
    if node_or_levels is None:
        return partial(parent, levels=levels)
    elif isinstance(node_or_levels, int) and levels is None:
        return partial(parent, levels=node_or_levels)
    elif not isinstance(node_or_levels, Node):
        raise Exception('Invalid input arguments.')

    #
    node = node_or_levels
    levels = levels if levels is not None else 1
    for _ in range(levels):
        if node is None:
            raise Exception('Attempted to get the parent of `None`.')
        node = node.parent
    return node


@register('hidden')
def hidden(node):
    """
    Marks the node as a hidden node that will not be included in resolved content.
    """
    node.flags.add(FLAGS.HIDDEN)


@register('load')
def load(node: KeyNode = _Unassigned, subdir=None, ext=DEFAULT_EXTENSION):
    """
    Loads the sub-tree from the file with path obtained by resolving the child value node. The sub-tree will replace the original value node.

    If the resolved path is a relative, two possibilities exist:

    1. An ancestor node was loaded from a file (the ancestor file), in which case the relative path is interpreted to be relative to the ancestor file folder.
    2. No ancestor node was loaded from a file, in which case the relative path is interpreted to be relative to the current working directory.

    Paths can be explicitly made to be relative to the current working directory with function :func:`functions.cwd`.

    .. _Load modifier workflow:

    .. rubric:: Load workflow

    The normal ``load`` workflow is as follows:

    1. A key node's ``load`` modifier call is started. 
    2. The :meth:`~soleil.solconf.nodes.Node.modify` method of the key node's :attr:`~soleil.solconf.solconf.SolConf.value` node is called in preparation for resolution.
    3. The target file path is obtained by resolving the key node's :attr:`~soleil.solconf.solconf.SolConf.value` attribute.
    3. The data in the target file is loaded and used to build a sub-tree. The modifiers of the sub-tree are not applied. Use :func:`modify_tree <soleil.solconf.containers.modify_tree>` or its alias :meth:`SolConf.modify_tree <soleil.solconf.SolConf.modify_tree>` -- this happens automatically when instantiating a :class:`~soleil.solconf.SolConf` object.
    4. The sub-tree is used to replace the original :attr:`node.value` node.
    5. All remaining ``node`` modifiers after ``load`` are applied to the new :attr:`~soleil.solconf.solconf.SolConf.value` node.

    .. rubric:: Syntax

    A ``load`` modifier can be added to a node's modifiers list using one of these syntaxes

    .. code-block::

        load
        load()
        load(ext='.yaml')
        load('source/sub_dir')
        load('source/sub_dir', ext='.yaml')

    .. rubric:: Choice-checking

    The :meth:`load` modifier can be combined with :meth:`choices` to constrain both the valid paths as well as the loaded node values. See the :ref:`load_with_choices.yaml` cookbook recipe for an example.


    :param ext: The default extension to add to files without an extension.
    """

    # Check if this is a modification call or a modifier definition call.
    node = node
    if node is _Unassigned:
        return partial(load, ext=ext)
    elif isinstance(node, (str, Path)):
        return partial(load, subdir=node, ext=ext)
    elif not isinstance(node, Node):
        raise ValueError('Invalid input for argument node.')

    # Get absolute path
    node.modify()
    path = Path(node.value())
    if subdir:
        subdir = Path(subdir)
        path = subdir / path
    if not path.is_absolute():
        root_path = source_file.parent if (source_file := node.source_file) else cwd()
        path = root_path / path

    # Set default extension
    if not path.suffix:
        path = path.with_suffix(ext)

    # Load the data
    with open(path, 'rt') as fo:
        text = fo.read()
    raw_data = yaml.safe_load(text)

    # Build the new node sub-tree
    ac = node.sol_conf_obj
    new_node = SolConf.build_node_tree(raw_data, parser=ac.parser)
    new_node._source_file = path

    # Replace the new node as the value in the original KeyNode.
    node.replace(node.value, new_node)

    # Since the modifier is applied to the KeyNode, and the KeyNode has not changed, return that node and not new_node.
    return new_node


@register('promote')
def promote(node: KeyNode):
    """
    Replaces the parent dictionary container by the key node's value node. The parent :class:`DictContainer` must contain a single child.

    ..rubric:: Workflow:

    1. Before ``promote`` modifier call: All modifiers up to and including ``promote`` are be applied to the containing key node. 
    2. During ``promote`` modifier call:
      a. The key node's :attr:`value` node replaces the key node's parent node. The modifiers of the new :attr:`value` node are not applied -- use :func:`modify_tree <soleil.solconf.containers.modify_tree>` or its alias :meth:`SolConf.modify_tree <soleil.solconf.SolConf.modify_tree>`.
    3. After ``promote`` modifier call: Since the call returns the key node's value node, all modifiers from the original key node after ``promote`` are applied to the promoted value node.

    """

    # Check that this is a key node within a dictionary container.
    if not isinstance(node, KeyNode) or not isinstance(node.parent, DictContainer):
        raise Exception(
            f'Expected a bound `KeyNode` input node, but received `{node}` with parent `{node.parent}`.')

    # Replacement will happen in the key nodes's grandparent. The key nodes's dict container will
    # will be replaced (by the key node's child value node) in the dict container's parent container.
    if (grandparent := node.parent.parent) is None:
        if (grandparent := node.sol_conf_obj) is None:
            raise Exception(
                'Cannot promote a `KeyNode` from a `DictContainer` that has no parent and is not the root of a `SolConf` object.')

    with node.lock, node.parent.lock, grandparent.lock:

        # Check that the container has only one child.
        if (num_children := len(node.parent.children)) != 1:
            raise Exception(
                f'Value node promotion requires that the parent `DictContainer` '
                f'have a single child, but {num_children} were found.')

        # Replace key node parent by key node child.
        value_node = node.value
        grandparent.replace(node.parent, value_node)

        # Apply value node modifiers.
        # value_node.modify()

        # Return the grandchild.
        return value_node


@register('choices')
class choices:
    """
    Checks that the resolved value is one of the allowed choices.

    If the modified node is a ``KeyNode``, the verification is applied to its value node. Otherwise, the verification is applied directly to the node.

    Because of this, the modifier sequence ``choices(1,2,3),promote`` and ``promote,choices(1,2,3)`` will have the same result.
    """

    def __init__(self, *valid_values):
        self.valid_values = valid_values

    def __call__(self, node: Node):
        """
        Monkey-patches the input node's resolve method. If the input node is a ``KeyNode``, its child value node's resolve method is monkey-patched instead.

        The new resolve method will verify that the resolved value is one of the valid choices or raise an exception otherwise.
        """
        node = node.value if isinstance(node, KeyNode) else node
        orig_resolve = node.resolve
        node.resolve = lambda: self._checked_resolve(node, orig_resolve)

    def _checked_resolve(self, node, orig_resolve):
        out = orig_resolve()
        if out not in self.valid_values:
            raise ValueError(
                f'The resolved value of `{node}` is `{out}`, but it must be one of `{self.valid_values}`.')
        return out
