"""
Base node modifiers included by default in :class:`soleil.solconf.parser.Parser` contexts.
"""
from .parser import register
from functools import partial
import yaml
from .nodes import FLAGS
from .dict_container import KeyNode, DictContainer, as_tuple
from .containers import Container
from .nodes import Node, ParsedNode
from .solconf import SolConf
from pathlib import Path
from .functions import cwd
from .utils import _Unassigned
from .varnames import DEFAULT_EXTENSION, EXTENDED_NODE_VAR_NAME
from .modification_heuristics import modify_tree


@register('noop')
def noop(*args):
    """
    No-operation modifier that returns ``None``.
    """
    return None


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
def load(node: Node = _Unassigned, subdir=None, ext=DEFAULT_EXTENSION):
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
    4. The data in the target file is loaded and used to build a sub-tree. The modifiers of the sub-tree are not applied. Use :func:`modify_tree <soleil.solconf.containers.modify_tree>` or its alias :meth:`SolConf.modify_tree <soleil.solconf.SolConf.modify_tree>` -- this happens automatically when instantiating a :class:`~soleil.solconf.SolConf` object.
    5. The sub-tree is used to replace the original :attr:`node.value` node.
    6. All remaining ``node`` modifiers after ``load`` are applied to the new :attr:`~soleil.solconf.solconf.SolConf.value` node.

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
    :param subdir: All paths will be relative to this subdir. The same relative path interpretation rules apply to subdir.
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

    # Replace the new node as the value in the original container.
    node.parent.replace(node, new_node)

    return new_node


@register('promote')
def promote(value_node: Node):
    """
    Replaces the parent dictionary container by the key node's value node. The parent :class:`DictContainer` must contain a single child.

    ..rubric:: Workflow:

    1. Before ``promote`` modifier call: All modifiers up to and including ``promote`` are be applied to the containing key node.
    2. During ``promote`` modifier call:

      a. The key node's :attr:`value` node replaces the key node's parent node. The modifiers of the new :attr:`value` node are not applied -- use :func:`modify_tree <soleil.solconf.containers.modify_tree>` or its alias :meth:`SolConf.modify_tree <soleil.solconf.SolConf.modify_tree>`.

    3. After ``promote`` modifier call: Since the call returns the key node's value node, all modifiers from the original key node after ``promote`` are applied to the promoted value node.

    """

    # Check that this is a key node within a dictionary container.
    if not ((key_node := value_node.parent)
            and (dict_node := key_node.parent)
            and isinstance(key_node, KeyNode)
            and isinstance(dict_node, DictContainer)):
        raise Exception(
            f'Expected {value_node} to be the value of a bound `KeyNode` but it was not.')

    # Replacement will happen in the key nodes's grandparent. The key nodes's dict container will
    # will be replaced (by the key node's child value node) in the dict container's parent container.
    if (dict_node_container := dict_node.parent) is None and (
            dict_node_container := value_node.sol_conf_obj) is None:
        raise Exception(
            'Cannot promote a `KeyNode` from a `DictContainer` that has no parent and is not the root of a `SolConf` object.')

    with value_node.lock, key_node.lock, dict_node.lock, dict_node_container.lock:

        # Check that the container has only one child.
        if (num_children := len(dict_node.children)) != 1:
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
    Returns the node's :attr:`~soleil.solconf.modifiers.Nodes.types`.
    """
    if isinstance(node, KeyNode):
        node._parse_raw_key()
        return node.value.types
    else:
        return node.types


@register('modifiers')
def modifiers(node: Node):
    """
    Returns the node's :attr:`~soleil.solconf.modifiers.Nodes.modifiers`.
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
    Returns the single child, if a single child exists, and raises an exception otherwise.
    """
    with node.lock:
        children = list(node.children)
        if len(children) != 1:
            raise Exception(
                f'Expected a single child node for container node `{node}` but found `{len(children)}`.')
        return children[0]


def _inject_extended_node(extend_source_node: KeyNode, override_node: KeyNode):
    """
    Monkey-patches :meth:`~soleil.solconf.nodes.ParsedNode.safe_eval` so that it injects the ``extend_source_node`` as new variable {EXTENDED_NODE_VAR_NAME} into the eval context of ``override_node``.
    """

    prev_safe_eval = override_node.safe_eval

    def new_safe_eval(py_expr: str, context=None):
        context = {
            EXTENDED_NODE_VAR_NAME: extend_source_node,
            **(context or {})}
        return prev_safe_eval(py_expr, context)

    override_node.safe_eval = new_safe_eval


@register('extends')
class extends:
    """
    Loads the specified path and updates it with the new content. The new nodes will have their evaluation context extended by the node being extended under variable |EXTENDED_NODE_VAR_NAME|.

    .. code-block:: yaml

        _::promote,extends('config.yaml'):
          a: 1       # Keep parent types and modifiers.
          b:int: 2   # Replaces the parent type.
          c::noop: 3 # Replaces the parent modifier.

          # TODO
          d:types(x_)+(int,):modifiers(x_)+(modif1,modif2): 4 # Expands the types or modifiers

          # TODO
          # Replaces nested content, possibly from another file -- see SolConfArg overrides approach.
          d.x.y: 4
    """

    def __init__(self, path):
        # Set default extension
        path = Path(path)
        if not path.suffix:
            path = path.with_suffix(DEFAULT_EXTENSION)
        self.path = path

    def __str__(self):
        return f'extends<{self.path}>'

    def __call__(self, overrides_node: DictContainer):
        """
        :param overrides_node: KeyNode with |DictContainer| value attribute.
        """
        # Check input
        if not (isinstance(overrides_node, DictContainer)
                and isinstance(key_node := overrides_node.parent, KeyNode)):
            raise TypeError(f'Expected ``overrides_node`` to be a `DictContainer` '
                            'that is the value of a `KeyNode`.')

        # Load the template to extend
        path = _abs_path(overrides_node, self.path)
        extend_source_tree = SolConf.load(path, modify=False).root

        #
        for extend_source_node in list(extend_source_tree.children):

            if curr_override := overrides_node.children.get(extend_source_node.key, None):

                # Parse source node raw keys
                extend_source_node._parse_raw_key()

                # Source exists for this override
                _inject_extended_node(extend_source_node, curr_override)
                curr_override._parse_raw_key()
                curr_override.value.types = (
                    curr_override.value.types or extend_source_node.value.types)
                curr_override.value.modifiers = curr_override.value.modifiers or extend_source_node.value.modifiers

            else:
                # No source exists for this override
                # TODO: don't do this. Add copy method to node using deepcopy and use that.
                extend_source_tree.remove(extend_source_node)
                overrides_node.add(extend_source_node)

        return overrides_node


@register('fuse')
def fuse(dict_node: DictContainer):
    """

    Provides an alternate syntax for decorated key nodes

    Takes a |KeyNode| (the 'base' node) with a |KeyNode.attr| node of type |DictContainer|  (the meta node) having key ``'value'`` and optional keys ``'types'`` and ``'modifiers'`` with values that are strings of lists of strings. The contents of the meta node will be used to set the corresponding attributes of the base node, with the strings in the ``'types'`` and ``'modifiers'`` nodes interpreted as if they were provided as part of a raw key in the base node.

    .. rubric:: Example

    .. doctest::

      >>> from soleil import SolConf

      # Fuse-based syntax
      >>> sc_fused = SolConf(
      ...   {'base::fuse': {
      ...      'value': '$: 1+2',
      ...      'types': 'int',
      ...      'modifiers': 'noop'
      ...   }}
      ...  )

      # Equivalent raw key-based-syntax
      >>> sc_rk = SolConf({'base:int:noop': '$: 1+2'})

      >>> sc_fused['base'].types, sc_rk['base'].types
      ((<class 'int'>,), (<class 'int'>,))

      >>> sc_fused['base'].modifiers, sc_rk['base'].modifiers
      ((<function noop at 0x...>,), (<function noop at 0x...>,))

      >>> sc_fused['base'].raw_value, sc_rk['base'].raw_value
      ('$: 1+2', '$: 1+2')

      >>> sc_fused(), sc_rk()
      ({'base': 3}, {'base': 3})


    It is also valid to use a list of modifiers or types:

    .. doctest::

      # Fuse-based syntax: lists
      >>> sc_fused_2 = SolConf(
      ...  {'base::fuse': {
      ...     'value': '$: 1+2',
      ...     'types': ['int', 'float'],
      ...     'modifiers': ['noop', 'choices(1,2,3)']
      ...      }}
      ...  )

      # Equivalent raw-key-based syntax
      >>> sc_rk_2 = SolConf({'base:int,float:noop,choices(1,2,3)': '$: 1+2'})

      >>> sc_fused_2['base'].types
      (<class 'int'>, <class 'float'>)
      >>> sc_rk_2['base'].types
      (<class 'int'>, <class 'float'>)

      >>> sc_fused_2['base'].modifiers
      (<function noop at 0x...>, <soleil.solconf.modifiers.choices object at 0x...>)
      >>> sc_rk_2['base'].modifiers
      (<function noop at 0x...>, <soleil.solconf.modifiers.choices object at 0x...>)

      >>> sc_fused_2['base'].raw_value
      '$: 1+2'
      >>> sc_rk_2['base'].raw_value
      '$: 1+2'

      >>> sc_fused_2(), sc_rk_2()
      ({'base': 3}, {'base': 3})



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
        def merge_decorator_values(decorator, eval_fxn):
            if isinstance(decorator, str):
                # 'int' or 'int,float' or 'None'
                return (eval_fxn(decorator),)
            elif isinstance(decorator, list):
                # ['int', 'float']
                out = []
                for _x in decorator:
                    out.extend(merge_decorator_values(_x, eval_fxn))
                return tuple(out)
            else:
                raise ValueError(f'Invalid decorator value `{decorator}`.')

        # Set types and modifiers
        for attr in ['types', 'modifiers']:
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
    Applies a callable to the node's resolved value. The output of the callable is returned as the node's resolved value. The modifier accomplishes this by monkey-patching the node's :meth:`Node.resolve <soleil.solconf.nodes.resolve>` method.

      * ``cast(callable)`` : Returns a modifier that applies the callable to the node's value after resolution.
      * ``cast(callable, node)``: Applies to specified callable to the resolved node value.

    """

    if len(args) == 1:
        return partial(cast, *args)
    elif len(args) == 2:
        caster, node = args
        node.value_modifiers.append(caster)
    else:
        raise ValueError('Expected 1 or 2 input arguments but received `{len(args)}`.')
