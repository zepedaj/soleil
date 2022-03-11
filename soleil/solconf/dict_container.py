"""
.. |raw key format| replace:: ``'name[:<types>[:<modifiers>]]'``
"""

from contextlib import contextmanager, nullcontext
from typing import Union, Dict, Optional
import re
from .autonamed_pattern import pxs, AutonamedPattern
from dataclasses import dataclass, field, InitVar, replace
from .utils import kw_only
from .containers import Container
from .nodes import Node, EvaledNode, FLAGS
from . import exceptions


def merge_decorator_values(decorator, eval_fxn):

    if isinstance(decorator, str):
        # 'int' or 'int,float' or 'None' or '()'
        out = eval_fxn(decorator)
        return (None if out is None else
                (out if isinstance(out, tuple) else (out,)))

    elif isinstance(decorator, list):
        # ['int', 'float']
        # ['int', '(float,str)']
        out = []
        for _x in decorator:
            out.extend(merge_decorator_values(_x, eval_fxn))
        return tuple(out)
    else:
        raise ValueError(f'Invalid decorator value `{decorator}`.')


class _RawKeyPatterns:
    """
    Contains regular expressions used to extract key type and modifier decorations from a string key.

    String keys have the format |raw key format|.
    """

    # Matches a single type/signature
    SINGLE_TYPE_PATTERN = AutonamedPattern(
        '('
        # Matches a type
        '{VARNAME}' '|'
        # Matches quoted signatures (with optional colon separator)
        r'(?P<q>\'|\"){NS_VARNAME}((?P<colon>:)({VARNAME}))?(?P=q)'
        ')', vars(pxs))
    """
    Expected type or xerializer signature string representation format. Signatures need to be strings.
    """

    # Matches a single type/signature or a tuple of mixed types/signatures.
    # Tuples may be optionally parentheses-enclosed.
    TYPE_PATTERN = AutonamedPattern(
        r'(?P<paren>\(\s*)?'
        r'{SINGLE_TYPE_PATTERN}(\s*,\s*{SINGLE_TYPE_PATTERN})*'
        r'(?(paren)\s*\))',
        vars())
    """
    Matches a single type/signature or a sequence of types/signatures.
    """

    RAW_KEY_PATTERN = re.compile(
        f'(?P<key>{pxs.VARNAME})'
        r'('
        f'\\s*:\\s*(?P<types>({TYPE_PATTERN}))?'
        # Modifiers could be better checked. Should be a callable or tuple.
        r'(\s*:\s*(?P<modifiers>([^\s].+[^\s]))?)?'
        r')?\s*',
    )
    """
    Valid described-key pattern.
    """


def _keynode_unimplemented(name):
    raise NotImplementedError(f'`KeyNode`s do not implement `{name}`.')


@dataclass
class KeyNode(EvaledNode, Container):
    """
    Key nodes represent a Python dictionary entry and as such, they must always be used as :class:`DictContainer` children. They implement part of the :class:`Container` interface. Key nodes have

    1. a :attr:`key` attribute of type ``str`` containing a valid Python variable name and
    2. a :attr:`value` attribute of type :class:`ValueNode`, :class:`DictNode` or :class:`ListNode`.


    .. _raw string:
    .. rubric:: Initialization from raw string

    Key node keys can be initialized from a raw string in the form |raw key format|, where

    * **key** will be used to set :attr:`KeyNode.key` and must be a valid variable name;
    * **types** is either a valid type in the parser's context, an xerializer-recognized string signature, or a tuple of these; and
    * **modifiers** is a callable or tuple of callables that take a node as an argument an modify it and potentially replace it.

    Both **types** and **modifiers** must be valid python statements.

    .. _key node life cycle:
    .. rubric:: Key node life cycle

    Key node modifiers are applied by calling the node's :meth:`modify` method. Type checking is applied at the end of node resolution. Typically, this happens in the following order:

    1. Modifiers are applied sequentially to ``self``. A modifier can optionally return a new node, in which case subsequent modifiers will be applied to this new node instead of ``self``. This functionality is handy when creating modifiers such as :func:`~soleil.solconf.modifiers.load` and :func:`~soleil.solconf.modifiers.promote` that replace a node by a new node.

      The process is illustrated by the following code snippet inside :meth:`modify`:

      .. code-block::

        node = self
        for modifier in modifiers:
          node = modifier(node) or node

    2. When the node is resolved by a call to :meth:`~soleil.solconf.nodes.Node.__call__` or :meth:`~soleil.solconf.nodes.Node.resolve`, the node checks that the type of the resolved value is one of the valid types, if any where supplied, and raises a :class:`TypeError` otherwise.

    """

    raw_key: str = field(default_factory=kw_only('raw_key'))
    """
    A string in the form |raw key format| (see :ref:`raw string`).
    """

    value: Node = field(default_factory=kw_only('value'))
    """
    The single node contained by this KeyNode container.

    .. todo:: Rename this attribute to ``value_node``.
    """

    # Defined here to be copied automatically by the dataclasses.replace function
    _do_post_init: InitVar[bool] = True  # Set to false to skip post-initialization
    _key_components: dict = None
    _key: str = None
    _raw_key_parsed = False

    def __post_init__(self, _do_post_init):
        if _do_post_init:
            # This switch is used by the copy method to avoid
            # parsing the raw_key and setting the value's parent
            # when a copy is going on.
            self._key_components = self._split_raw_key(self.raw_key)
            self._key = self._key_components['key']
            if self.value.parent:
                raise exceptions.NodeHasParent(self.value, self)
            self.value.parent = self

    @property
    def hidden(self):
        return super().hidden or FLAGS.HIDDEN in self.value.flags

    def copy(self):
        value_copy = self.value.copy()
        out = replace(self, _do_post_init=False)
        out.value = value_copy
        out.value.parent = out
        return out

    @property
    def children(self):
        """
        Returns a tuple containing the key node's :attr:`value` node.
        """
        if self.value is None:
            return tuple()
        else:
            return tuple([self.value])

    # Unimplemented methods from the Container interface.
    def add(self, *args): _keynode_unimplemented(f'add (args: {args})')

    def _getitem(self, key, modify): _keynode_unimplemented(
        f'_getitem (key: {key}, modify: {modify})')

    def modify(self):
        """
        Evaluates the raw key modifiers and types before applying the node modifiers. Calling this function a second time has no effect.
        """
        # Parse the raw modifiers and types strings before applying modifiers
        self._parse_raw_key()
        super().modify()

    def remove(self, node: Node):
        """
        Checks that ``node`` is contained in :attr:`Node.value`. If so, it dissociates :attr:`value` from ``self``, and further dissociates ``self`` from the parent ``DictContainer``.
        """

        with self.lock, node.lock:
            if node is not self.value:
                raise exceptions.NotAChildOf(node, self)
            else:
                node.parent = None
                self.value = None
                self.parent.remove(self)

    @contextmanager
    def lock(self):
        """
        Locks the node and, if the node is bound, the parent.
        """
        with self.lock:
            if self.parent:
                with self.parent.lock:
                    yield
            else:
                yield

    @property
    def key(self): return self._key

    @key.setter
    def key(self, new_key):
        """
        KeyNode keys can only be changed if the ``KeyNode``'s parent container is ``None``.
        """
        with self.lock:
            if self.parent is not None:
                raise Exception(f'Remove `{self}` from parent container before re-naming.')
            else:
                self._key = new_key

    def __hash__(self):
        return hash(self.key)

    def __eq__(self, val):
        """
        Compares to strings or other :class:`KeyNode`s based on the key. Together with :meth:`__hash__`, this method enables
        using :class:`KeyNode`s as string keys in :attr:`DictContainer.children` ``__getitem__`` calls.
        """
        if isinstance(val, str):
            return val == self.key
        elif isinstance(val, KeyNode):
            return val.key == self.key

    @classmethod
    def _split_raw_key(cls, raw_key: str):
        """
        Returns a dict with sub-strings 'key', 'types' and 'modifiers'. The content of 'types' and 'modifiers' will be None if unavailable.
        """
        if not (match := re.fullmatch(_RawKeyPatterns.RAW_KEY_PATTERN, raw_key)):
            # TODO: Add the file, if available, to the error message.
            raise Exception(f'Invalid described key syntax `{raw_key}`.')
        else:
            return {key: match[key] for key in ['key', 'types', 'modifiers']}

    def _parse_raw_key(self):
        """
        Evaluates the raw modifiers and types strings and assigns them to this node's :attr:`modifiers` attribute and to the attr:`value` node's :attr:`~soleil.solconf.nodes.Node.types` attribute.

        This function will only have an effect the first time its called.
        """
        with self.lock:
            if self._raw_key_parsed:
                return
            self._raw_key_parsed = True

            try:
                #
                component = 'types'
                raw_value = self._key_components[component]
                self.value.types = None if raw_value is None else merge_decorator_values(
                    raw_value, self.safe_eval)
                #
                component = 'modifiers'
                raw_value = self._key_components[component]
                self.value.modifiers = tuple() if raw_value is None else (
                    # `or tuple()` below used to support disabling extended modifiers with None
                    merge_decorator_values(raw_value, self.safe_eval) or tuple())
                self.value.modified = False
            except exceptions.RawKeyComponentError:
                raise
            except Exception as err:
                raise exceptions.RawKeyComponentError(self, component, raw_value) from err

    def _unsafe_resolve(self):
        """
        Returns the resolved key and value as a tuple.
        """
        #
        with self.lock:
            key = self.key
            value = self.value.resolve()

            return key, value

    def replace(self, old_value=Optional[Node], new_value: Node = None):
        """
        Replaces the value node by a new value node.

        :param old_value: If provided, must be the current value node :attr:`value`. Use ``None`` to specify it by default. This signature is provided for consistency with the :class:`Container` signature.
        :param new_value: The new value node.
        """
        with self.lock, new_value.lock:
            old_value = old_value or self.value
            with old_value.lock:
                if old_value is not self.value:
                    raise exceptions.NotAChildOfError(old_value, self)
                old_value.parent = None
                if new_value.parent:
                    new_value.parent.remove(new_value)
                self.value = new_value
                new_value.parent = self

    def get_child_qual_name(self, child_node):
        """
        Returns the dictionary-container-relative qualified name.

        Key nodes (respectively, their value nodes) can be accessed directly by indexing the parent :class:`DictContainer` with a ``'*'``-prefixed key (non-prefixed key) as an index. E.g., the ref string ``'*key'`` and ``'key'`` will indicate, respectively, the key node of key ``'key'`` and its value node.

        .. rubric:: Example

        .. testcode::

          from soleil.solconf.solconf import SolConf

          sc = SolConf({'node0': {'node1': 1}})

          # Refer to the value node.
          node = sc['node0']['node1']
          assert node==sc.node_tree['node0'].children['node1'].value
          assert node.qual_name == 'node0.node1'

          # Refer to the key node.
          node = sc['node0']['*node1']
          assert node==sc.node_tree['node0'].children['node1']
          assert node.qual_name == 'node0.*node1'

        """

        if child_node is self.value:
            # DictContainer objects can refer to the key or value node directly.
            # See :meth:`DictContainer.__getitem__`.
            if not self.parent:
                raise Exception('Attempted to retrieve the qualified name of an unbounded KeyNode.')
            return self.parent._derive_qual_name(self.key)
        else:
            raise exceptions.NotAChildOfError(child_node, self)


class DictContainer(Container):
    """
    Contains a dictionary node. Adding and removing entries to this container should be done entirely using :meth:`add` and :meth:`remove` to ensure correct handling of parent/child relationships.
    """

    _REF_COMPONENT_PATTERN = re.compile(r'\*?[a-zA-Z_]\w*')

    children: Dict[Node, Node] = None
    # Both key and value will be the same KeyNode, ensuring a single source for the
    # node key.
    #
    # This approach will also behave in a way similar to dictionaries when inserting nodes
    # with the same key. Node indexing can be done using a key that is the KeyNode or the
    # node key as a string,  a behavior enable by the KeyNodes.__eq__ implementation.
    #
    # Using a set seemed like a more natural solution, but I was unable to
    # retrieve an object from a set given a matching key (I tried `node_set.intersection(key)`,
    # and `{key}.intersection(node_set)` )
    #
    # WARNING: Changing the key of a key node without taking care that
    # that node is not a part of a dictionary where another KeyNode exists with the
    # same key will result in unexpected behavior.

    def __init__(self, **kwargs):
        self.children = {}
        super().__init__(**kwargs)

    def add(self, node: KeyNode):
        """
        Adds the node to the container or replaces the node with the same key if one exists.
        The node's parent is set to ``self``.
        """
        with self.lock, node.lock:
            if not isinstance(node, KeyNode):
                raise exceptions.KeyNodeRequired(node)
            if node.parent is not None:
                raise exceptions.NodeHasParent(node, self)
            # Remove node of same key, if it exists.
            self.remove(node, safe=True)
            # Add the new node.
            node.parent = self
            self.children[node] = node

    def remove(self, node: Union[KeyNode, str], safe=False) -> KeyNode:
        """
        Removes the child node with the same key as ``node`` from the container.

        The removed node's parent is set to ``None`` and the node is returned.

        :param node: The key or node whose key will serve as a key.
        :param safe: Whether to ignore non-existing keys.

        .. warning:: The removed node is only guaranteed to match the input node in key.
        """
        with self.lock, (nullcontext(None) if isinstance(node, str) else node.lock):
            if popped_node := self.children.pop(node, *((None,) if safe else tuple())):
                popped_node.parent = None
                return popped_node

    def replace(self, old_node: Union[str, KeyNode], new_node: KeyNode):
        """
        Removes the old node and adds the new node. Both nodes do not need to have the same hash key.
        """

        if not isinstance(new_node, KeyNode):
            raise exceptions.KeyNodeRequired(new_node)

        old_node = self[old_node]
        with self.lock, new_node.lock, old_node.lock:
            self.remove(old_node)
            if new_node.parent:
                new_node.parent.remove(new_node)
            self.add(new_node)

    def _unsafe_resolve(self):
        """
        Returns the resolved dictionary.
        """
        return dict(child.resolve() for child in self.children.values() if not child.hidden)

    def _getitem(self, key: str, modify=True):
        """
        Returns the resolved value for the specified key.

        By default, the returned node is the :class:`ValueNode` child of the referred :class:`KeyNode`.

        To instead the obtain the :class:`KeyNode`, prepended the input key string with a ``'*'`` character.
        """
        if not isinstance(key, str):
            raise Exception(f'Expected a string key but got `{key}`.')
        if modify:
            self.modify()
        if key[:1] == '*':
            return self.children[key[1:]]
        else:
            key_node = self.children[key]
            if modify:
                key_node.modify()
            return key_node.value

    def get_child_qual_name(self, node: KeyNode):
        """
        Prepends a ``'*'`` character to the input key node's key before building the qualified name. See :meth:`__getitem__`.
        """

        for child_node in self.children:
            if node is child_node:
                return self._derive_qual_name(f'*{node.key}')

        raise exceptions.NotAChildOfError(child_node, self)
