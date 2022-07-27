"""
Base node modifiers included by default in :class:`soleil.solconf.parser.Parser` contexts.
"""
#
from typing import Union
from .parser import register
from functools import partial
import yaml
from .dict_container import KeyNode, DictContainer, merge_decorator_values
from .containers import Container
from .nodes import Node, ParsedNode, FLAGS, EvaledNode
from .solconf import SolConf
from pathlib import Path
from .functions import cwd
from .utils import _Unassigned
from .varnames import DEFAULT_EXTENSION
from .modification_heuristics import modify_tree
from pglib.py import strict_zip


@register('noop')
def noop(*args):
    """
    No-operation modifier that returns ``None``.
    """
    return None


# def parent(node_or_levels: Node = None, levels=None):
@register('parent')
def parent(*args):
    """
    Returns, for the given node, the ancestor at a specified number of levels up (defauls to :math:`1` level up).

    .. rubric:: Syntax:

    * ``parent``: Modifier that returns the parent (same as ``parent(1)``).
    * ``parent(N:int)``: Modifier that returns the :math:`N`-th ancestor.
    * ``parent(node)``: Retuns the parent of the specified node (same as ``parent(1, node)``).
    * ``parent(N, node)``: Returns the :math:`N`-th ancestor of node.

    """

    # Check if this is a modification call or a modifier definition call.

    invalid_args = ValueError('Invalid input arguments.')
    if len(args) == 1:
        if isinstance(args[0], int):
            # parent(N)
            return partial(parent, *args)
        elif isinstance(args[0], Node):
            # parent(node)
            node, levels = args[0], 1
        else:
            raise invalid_args
    elif len(args) == 2:
        # parent(node, N)
        levels, node = args
    else:
        raise invalid_args

    for _ in range(levels):
        if node is None:
            raise Exception('Attempted to get the parent of `None`.')
        node = node.parent
    return node


@register('hidden')
def hidden(node):
    """
    Marks the node as a hidden node that will not be included in resolved content. Accordingly, the |SolConf.post_processor| is not applied to this node (and sub-tree), as the post-processor operates following tree resolution.
    """
    node.flags.add(FLAGS.HIDDEN)


def _abs_path(node, path, subdir=None, ext=DEFAULT_EXTENSION):
    """
    Returns the absolute path as interpreted from the given node. See the discussion in :func:`load` concerning relative path interpretation rules.
    """
    path = Path(path)
    if subdir:
        path = Path(subdir) / path
    if not path.is_absolute():
        root_path = source_file.parent if (source_file := node.source_file) else cwd()
        path = root_path / path

    # Set default extension
    if not path.suffix:
        path = path.with_suffix(ext)

    return path


@register('load')
def load(node: Node = _Unassigned, subdir=None, ext=DEFAULT_EXTENSION, vars=None):
    """
    Loads the sub-tree from the source file with path obtained by resolving the node's value. The loaded sub-tree will replace the original node.

    :param node: If specified, modifies that node. If unspecified, returns a modifier with other specified parameters bound to the given values.
    :param ext: The default extension to add to files without an extension. Use ``''`` to skip adding extensions.
    :param subdir: All relative paths will be relative to this sub-directory. The same :ref:`relative path interpretation <path conventions>` rules that apply to relative paths apply to the value of ``subdir``.

    .. _path conventions:

    .. rubric:: Relative path interpretation

    If the resolved path is a relative path, two possibilities exist:

        #. **Relative to ancestor file**: The node or one of its ancestors was loaded from a file (the ancestor file), in which case the relative path is interpreted to be relative to the directory of that ancestor file. The closest ancestor is used if more than one ancestors were loaded from a file.
        #. **Relative to working directory**: No ancestor node was loaded from a file, in which case the relative path is interpreted to be relative to the current working directory.

    Paths can be explicitly made relative to the current working directory by post-concatenating relative paths to the output of registered function :func:`soleil.solconf.functions.cwd`.

    .. _Load modifier workflow:

    .. rubric:: Load workflow

    The normal ``load`` workflow is usually triggered during an iterative tree modification heuristic (usually carried out by :meth:`SolConf.modify_tree <soleil.solconf.solconf.SolConf.modify_tree>` as part of |SolConf| initialization):

        #. A node's ``load`` modifier call is started.
        #. The target file path is obtained by resolving the node, using the :ref:`relative path interpretation <path conventions>` described above.
        #. The data in the target file is loaded and used to build a sub-tree. The modifiers of all nodes in the loaded sub-tree are not applied immediately -- this will happen in latter iterations of the tree modification heuristic.
        #. The sub-tree is used to replace the original node in the node tree.
        #. All remaining modifiers from the original node after the ``load`` modifier are applied to the new sub-tree.

    .. rubric:: Choice-checking

    The :meth:`load` modifier can be combined with :meth:`choices` to constrain both the valid paths as well as the loaded node values. See the :ref:`Load with choices` cookbook recipe for an example.

    """

    # Check if this is a modification call or a modifier definition call.
    node = node
    if node is _Unassigned:
        return partial(load, subdir=subdir, ext=ext, vars=vars)
    elif isinstance(node, (str, Path)):
        return partial(load, subdir=node, ext=ext, vars=vars)
    elif not isinstance(node, Node):
        raise ValueError('Invalid input for argument node.')

    # Get absolute path
    node.modify()
    path = Path(node())
    path = _abs_path(node, path, subdir=subdir, ext=ext)

    # Load the data
    with open(path, 'rt') as fo:
        text = fo.read()
    raw_data = yaml.safe_load(text)

    # Build the new node sub-tree
    ac = node.sol_conf_obj
    new_node = SolConf.build_node_tree(raw_data, parser=ac.parser)
    new_node._source_file = path

    # Carry out the specified substitutions of ParsedNodes:
    for key, val in (vars or {}).items():
        new_node[key].raw_value = val

    # Replace the new node as the value in the original container.
    node.parent.replace(node, new_node)

    return new_node


@register('promote')
def promote(value_node: Node):
    """
    Replaces the grand-parent dictionary container by the promoted value node.

    Valid only for nodes that are a value of a |KeyNode| node (the parent) within a |DictContainer| container node (the grand-parent). The grand-parent dictionary container will be replaced by the input ``value_node``. The grand-parent :class:`DictContainer` must contain a single child, otherwise an error is raised.

    .. rubric:: Workflow:

    #. *Before* ``promote`` *modifier call*: All modifiers up to and including ``promote`` are applied to ``value_node``.
    #. *During* ``promote`` *modifier call*:

      #. Node ``value_node`` replaces the grand-parent dictionary container. Modifiers of node ``value_node`` are not applied immediately -- they will be applied in a latter iteration of the recursive tree node modification.

    #. *After* ``promote`` *modifier call*: Since the grand-parent dictionary container was replaced by ``value_node``, all modifiers from the original grand-parent after ``promote`` are applied to the promoted ``value_node`` node.
    #. In a latter tree modification iteration, modifiers of ``value_node`` are applied to that node.

    """

    # Check that this is a key node within a dictionary container.
    if not ((key_node := value_node.parent)
            and (dict_node := key_node.parent)
            and isinstance(key_node, KeyNode)
            and isinstance(dict_node, DictContainer)):
        raise Exception(
            f'Expected {value_node} to be the value of a bound `KeyNode` but it was not.')

    # Replacement will happen in the key nodes's grandparent. The key nodes's dict container will
    # be replaced (by the key node's child value node) in the dict container's parent container.
    if (dict_node_container := dict_node.parent) is None and (
            dict_node_container := value_node.sol_conf_obj) is None:
        raise Exception(
            'Cannot promote a `KeyNode` from a `DictContainer` that has no parent and is not the root of a `SolConf` object.')

    with value_node.lock, key_node.lock, dict_node.lock, dict_node_container.lock:

        # Check that the container has only one child.
        if (num_children := len(dict_node)) != 1:
            raise Exception(
                f'Node `{value_node}` promotion requires that the DictContainer `{dict_node}`'
                f'have a single child, but `{num_children}` were found.')

        # Replace key node parent by key node child.
        dict_node_container.replace(dict_node, value_node)

        # Return the grandchild.
        return value_node


@register('choices')
class choices:
    """
    Checks that a node's resolved value is one of the allowed choices. A ``ValueError`` exception is raised otherwise.

    .. todo:: To support auto-CLI generation, the choices of each node chouls be available to generate documentation. Best add a ``choices`` attribute to nodes and have this modifier set that attribute.
    """

    def __init__(self, *valid_values):
        """
        :param valid_values: All values that are valid for the resolved node.
        """
        self.valid_values = valid_values

    def __call__(self, node: Node):
        """
        Appends the modifier instance to the node's |Node.value_modifiers|.
        """
        self.node = node
        node.value_modifiers.append(self._checked_resolve)

    def _checked_resolve(self, resolved_value):
        if resolved_value not in self.valid_values:
            raise ValueError(
                f'The resolved value of `{self.node}` is `{resolved_value}`, but it must be one of `{self.valid_values}`.')
        return resolved_value


@register('types')
def types(node: Node):
    """
    Returns the node's :attr:`~soleil.solconf.modifiers.Nodes.types` attribute.
    """
    if isinstance(node, KeyNode):
        node._parse_raw_key()
        return node.value.types
    else:
        return node.types


@register('modifiers')
def modifiers(node: Node):
    """
    Returns the node's :attr:`~soleil.solconf.modifiers.Nodes.modifiers` attribute.
    """
    if isinstance(node, KeyNode):
        node._parse_raw_key()
        return node.value.modifiers
    else:
        return node.modifiers


@register('raw_value')
def raw_value(node: ParsedNode):
    # TODO: (?) Return the raw content interpreted by SolConf.build_node_tree for non-ParsedNode nodes?
    return node.raw_value


@register('child')
def child(node: Container):
    """
    Returns the single child, if a single child exists, raising an exception otherwise.
    """
    with node.lock:
        children = list(node.children)
        if len(children) != 1:
            raise Exception(
                f'Expected a single child node for container node `{node}` but found `{len(children)}`.')
        return children[0]


@register('derives')
class derives:
    """
    Inherits the contents of ``super_container`` and extends it dynamically with the contents of the modified node.

    .. rubric:: Examples

    The decorated dictionary will include the super container's entries:

    .. doctest::
      :options: +NORMALIZE_WHITESPACE

      >>> from soleil import SolConf
      >>> SolConf(
      ...  {'x': {'a': 0, 'b': 1, 'c': 2}, 
      ...   'y::derives(r_["x"])': {'c': -2, 'd':3}
      ...  })()
      {'x': {'a': 0, 'b': 1, 'c': 2},
       'y': {'c': -2, 'd': 3, 'a': 0, 'b': 1}}

    Derivations can be chained:

    .. doctest::
      :options: +NORMALIZE_WHITESPACE

      >>> from soleil import SolConf
      >>> SolConf(
      ...   {'x': {'a': 0, 'b': 1, 'c': 2}, 
      ...    'y::derives(r_["x"])': {'c': -2, 'd': 3}, 
      ...    'z::derives(r_["y"])': {'e': 4}
      ...   })()
      {'x': {'a': 0, 'b': 1, 'c': 2}, 
       'y': {'c': -2, 'd': 3, 'a': 0, 'b': 1}, 
       'z': {'e': 4, 'c': -2, 'd': 3, 'a': 0, 'b': 1}}

    The nodes of ``super_container``, however, will not have access to contents overloaded in the modified node:

    .. doctest::
      :options: +NORMALIZE_WHITESPACE

      >>> from soleil import SolConf
      >>> SolConf(
      ...   {'x': {'a': 0, 'b': '$:n_("..a")'},
      ...    'y::derives(r_["x"])': {'a': 1},
      ...   })()
      {'x': {'a': 0, 'b': 0},
       'y': {'a': 1, 'b': 0}}


    """

    def __init__(self, super_container):
        """
        :param super_container: The node to derive from.
        """
        self.super_container = super_container

    def __call__(self, node):
        """
        Sets the specified node's ``super_container`` attribute to the modifier's homonymous attribute.
        """
        self.super_container = self.super_container.modify() or self.super_container
        if not isinstance(self.super_container, DictContainer):
            raise Exception(f"'DictContainer' required, but got {type(self.super_container)}.")
        node.super_container = self.super_container


@register('fuse')
def fuse(dict_node: DictContainer):
    """
    Provides an alternate syntax for node type and modifier specification.

    Takes a |DictContainer| (the 'base' node)  having keys ``'value'`` and optional keys ``'types'`` and ``'modifiers'`` -- the contents of these three keys are fused to produce a single node that replaces the base node.

    The ``'value'`` node contains the sub-tree that will replace the base node and become the fused node. The ``'types'`` and ``'modifiers'`` nodes can contain a string or list of strings that will set the types and modifiers of the fused node.

    .. rubric:: Example

    .. doctest::
      :options: +NORMALIZE_WHITESPACE, +ELLIPSIS

      >>> from soleil import SolConf      

      # Fuse-based syntax
      >>> sc_fused = SolConf(
      ...   {'base::fuse': {
      ...      'value': '$: 1+2',
      ...      'types': ['int', 'float'], # (List of) python statement(s)
      ...      'modifiers': 'noop'        # (List of) python statement(s)
      ...   }})
      >>> sc_fused.print_tree()
      {"DictContainer@''()": [{"KeyNode@'*base'()": ["ParsedNode@'base'(types=(<class 'int'>, <class 'float'>), modifiers=(<function noop at 0x...>,))"]}]}
      >>> sc_fused()
      {'base': 3}

      # Equivalent raw key-based syntax
      >>> sc_rk = SolConf({'base:int,float:noop': '$: 1+2'})
      >>> sc_rk.print_tree() # Same as sc_fused.print_tree()
      {"DictContainer@''()": [{"KeyNode@'*base'()": ["ParsedNode@'base'(types=(<class 'int'>, <class 'float'>), modifiers=(<function noop at 0x...>,))"]}]}
      >>> sc_rk()
      {'base': 3}

    """

    with dict_node.lock:

        # Check input
        if not isinstance(dict_node, DictContainer):
            raise TypeError(
                f'Expected fused meta values dictionary `{dict_node}` to be of type `{DictContainer}`.')

        # Check input
        if 'value' not in (keys := {x.key for x in dict_node.children}):
            raise ValueError(
                "Expected fused meta values dictionary to have key 'value'.")
        if invalid_keys := (keys - (valid_keys := {'value', 'types', 'modifiers'})):
            raise ValueError(
                f'Invalid keys `{invalid_keys}` for fused meta values dictionary should come from {valid_keys}.')

        # Fuse

        # Set types and modifiers
        for attr in ['types', 'modifiers']:
            if attr in keys:
                modify_tree(lambda: dict_node[f'*{attr}'])
                attr_value = merge_decorator_values(
                    dict_node(f'{attr}'), dict_node[f'*{attr}'].safe_eval)
                setattr(dict_node['value'], attr, attr_value)

        # Reset dict_node types and modifiers
        dict_node['value'].modified = False

        # Promote the value node
        for attr in ['types', 'modifiers']:
            if attr in keys:
                dict_node.remove(dict_node[f'*{attr}'])
        value = dict_node['value']

        promote(value)

        return value


@register('cast')
def cast(*args):
    """
    Applies a callable to the node's resolved value. The output of the callable is returned as the node's resolved value. The modifier accomplishes this by appending a partial version of this method to the node's |Node.value_modifiers| attribute.

    .. rubric:: Syntax

    * ``cast(callable)`` : Returns a modifier that appends the specified callable to the node's |Node.value_modifiers| attribute.
    * ``cast(callable, node)``: Adds the specified callable to the resolved node's |Node.value_modifiers|.

    """

    if len(args) == 1:
        return partial(cast, *args)
    elif len(args) == 2:
        caster, node = args
        node.value_modifiers.append(caster)
    else:
        raise ValueError('Expected 1 or 2 input arguments but received `{len(args)}`.')


@register('pproc')
def pproc(node):
    """
    Applies the post-processor to the modified node as part of node resolution (as a value modifier).
    """
    node.value_modifiers.append(node.sol_conf_obj.post_processor)
