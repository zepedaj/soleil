"""
"""
from .autonamed_pattern import AutonamedPattern
from threading import RLock
from .exceptions import (
    InvalidRefStr, InvalidRefStrComponent, ResolutionError, ResolutionCycleError, ModificationError)
from dataclasses import dataclass, field, replace
import abc
from .parser import Parser
from typing import Any, Set, Optional, Tuple, Callable, List
from enum import Enum, auto
from . import varnames
import re
from .resolving_node import ResolvingNode
from pathlib import Path
from .utils import kw_only

# TODO: Remove this


class FLAGS(Enum):
    HIDDEN = auto()


def _propagate(node, prop_name, hidden_prop_name=None, default=None):
    """
    Returns the value of the hidden property, if it is not None, or the parent's property, if available, else the default value.

    If used as a property getter in a class, accessing the parent's property will access, recursively, the property of all 
    ancestors until one is foudn with a non-``None`` hidden property value.

    :param node: The starting node.
    :param prop_name: The name of the property.
    :param hidden_prop_name: The name of the hidden property. Defaults to the property name prefixed with a ``'_'``.
    """
    return (
        my_val if (my_val := getattr(node, hidden_prop_name or f'_{prop_name}')) is not None else
        (getattr(node.parent, prop_name) if node.parent else default))


@dataclass
class Node(abc.ABC):
    """
    Base node used to represent contants, containers, keys and values. All nodes need to either be the root node or part of a :class:`Container`.
    """
    flags: Set[FLAGS] = field(default_factory=set)

    parent: Optional['Node'] = field(default=None)
    """
    The parent :class:`Container` node. This field is handled by container nodes and should not be set explicitly.
    """

    lock: RLock = field(default_factory=RLock)
    """
    Locks the node, preventing modifications.

    .. todo:: Currently only used by containers. Thread-safety needs a review / testing.

    """

    types: Optional[Tuple[type]] = None
    """
    Contains the valid types for the resolved content.
    """

    modified: bool = False
    """
    Keeps track of whether the node's :meth:`modify` method has been called.
    """

    modifiers: Tuple[Callable[['Node'], Optional['Node']]] = tuple()
    """
    Contains the modifiers to apply to this node.
    """

    value_modifiers: List[Callable] = field(default_factory=list)
    """
    List of callables applied sequentially to the resolved node's value at the end of node resolution.
    """

    _source_file: Optional[Path] = None  # Set by :func:`load`
    source_file = property(lambda self: _propagate(self, 'source_file'))
    """
    Returns the source file of the nearest ancestor (including ``self``), or ``None`` if no ancestor was loaded from a file.
    """

    _sol_conf_obj: Optional = None  # Set by SolConf initializer.
    sol_conf_obj = property(lambda self: _propagate(self, 'sol_conf_obj'))
    """
    If the node is part of a tree in an :class:`SolConf` object, returns that object.
    """

    def __getitem__(self, key, modify=True):
        """
        By default, :class:`Node` objects are not subscriptable. However, some modifiers (e.g., |load|) will alter the node type. This catch-all :meth:`__getitem__` modifies the node and, if the modified node is different than ``self``, calls the :meth:`__getitem__`` method of that the new node.

        Otherwise, a ``TypeError`` is raised indicating that the node is not subscriptable.

        Parameter ``modify`` is provided for compatibility with other node types. Setting it to ``True`` will cause  the above described ``TypeError`` exception to be raised.
        """
        if not modify or (node := self.modify()) is self:
            raise TypeError(f"'{type(self).__name__}' object is not subscriptable")
        else:
            return node[key]

    @property
    def hidden(self):
        # """
        # Returns ``True`` if the node or any ancestor node is marked as hidden. With the exception of the root node (root nodes cannot be hidden), hidden nodes are not included in resolved content. Hiden nodes can, however, be referred to by ref strings or accessed using ``Node.__getitem__``, including as part of ``$``-strings.
        # """
        """
        Returns ``True`` if the node is marked as hidden.
        """
        return FLAGS.HIDDEN in self.flags

    @property
    def root(self):
        """
        Returns the root node.
        """
        return sol_conf_obj.root if (sol_conf_obj := self.sol_conf_obj) else None

    def modify(self):
        """
        Applies the modifiers associated to the current node. Does not modify children nodes, if any.
        """

        # Check if the modifiers have been applied.
        if self.modified:
            return self
        else:
            self.modified = True

        # Obtain the modifiers from the parent KeyNode's raw key, if any.
        from .dict_container import KeyNode
        if isinstance(self.parent, KeyNode):
            self.parent.modify()

        # Apply node modifiers.
        node = self
        if self.modifiers:
            for modifier in self.modifiers:
                try:
                    node = modifier(node) or node
                except ModificationError:
                    raise
                except Exception as err:
                    raise ModificationError(self,  modifier) from err

        return node

    def copy(self, **kwargs):
        """
        Returns a copy of the sub-tree with this node as the root.
        """
        out = replace(self, **kwargs)
        out.parent = None
        return out

    @property
    def file_root(self):
        """
        Returns the nearest ancestor (including self) that was loaded from a file or ``None`` if none was loaded form a file.
        """
        node = self
        while node and node._source_file is None:
            node = node.parent
        return node

    def __str__(self):
        return f"{type(self).__name__}@'{self.qual_name}'" + (
            f'<{self.source_file}>' if self._source_file else '')

    def __repr__(self):
        return str(self)

    def resolve(self):
        """
        Computes and returns the node's value, checking for cyclical references and generating meaningful error messages if these are detected.
        """

        if not self.modified and self.modifiers:
            raise Exception(
                f'Attempted resolution of unmodified node `{self}` with modifiers - call `node.modify()` before resolving.')

        try:
            # Set up marker variable that is used to track node dependencies
            # The follwing unused variable is used in stack inspection within initializer
            # to automatically detect cyclical referenes.
            __resolving_node__ = ResolvingNode(self)  # noqa

            # Resolve the node
            value = self._unsafe_resolve()

            # Apply value modifiers
            for _fxn in self.value_modifiers:
                value = _fxn(value)

            # Check type is correct
            if self.types:
                if self.types and not isinstance(value, self.types):
                    raise TypeError(f'Invalid type {type(value)}. Expected one of {self.types}.')

            return value

        except (ResolutionError, ResolutionCycleError):
            raise

        except Exception as error:
            raise ResolutionError(self) from error

    @abc.abstractmethod
    def _unsafe_resolve(self):
        """
        Children classes need to implement this method and not the public method :meth:`resolve`, which wraps this method. As a rule of thumb, this method should never be called directly.
        Any node resolutions done inside this method should instead call method :meth:`resolve`.
        """

    # Regular expressions for ref strings.
    _REF_STR_COMPONENT_PATTERN_RAW = r'(0|[1-9]\d*|\*?[_a-zA-Z]\w*)'
    _REF_STR_COMPONENT_PATTERN_OR_DOTS_RAW = f'(?P<component_or_dots>{_REF_STR_COMPONENT_PATTERN_RAW}|\\.+)'
    _FULL_REF_STR_PATTERN_RAW = AutonamedPattern(
        r'\.*(?P<start>{x})?(?(start)(\.+{x})*\.*)',
        {'x': AutonamedPattern(_REF_STR_COMPONENT_PATTERN_RAW)})

    # Compile the patterns.
    _REF_STR_COMPONENT_PATTERN = re.compile(str(_REF_STR_COMPONENT_PATTERN_RAW))
    _REF_STR_COMPONENT_PATTERN_OR_DOTS = re.compile(_REF_STR_COMPONENT_PATTERN_OR_DOTS_RAW)
    _FULL_REF_STR_PATTERN = re.compile(str(_FULL_REF_STR_PATTERN_RAW))

    def node_from_ref(self, ref: str = ''):
        """
        Returns the node indicated by the input :ref:`reference string <with reference strings>`.

        .. rubric:: Examples

        .. testcode::

          from soleil import SolConf

          #
          raw_data = {'my_key0':[0,1,2], 'my_key1':[4,5,6]}
          r_ = SolConf(raw_data).root

          # From the root node
          assert (r_.node_from_ref('') is 
                  r_)
          assert (r_.node_from_ref('my_key0.1') is 
                  r_['my_key0'][1])          

          # Ancestor access
          assert (r_.node_from_ref('my_key0..') is
                  r_)
          assert (r_.node_from_ref('my_key0.0...') is
                  r_)

          # From a child node
          node = r_.node_from_ref('my_key0..')
          assert (node.node_from_ref('my_key1.2') is
                  node['my_key1'][2])

        :param ref: A string of dot-separated keys, indices or empty strings (:ref:`syntax <with reference strings>`).

        """
        #
        _ref_components = self._get_ref_components(ref)
        node = self
        for _component in _ref_components:
            node = node._node_from_ref_component(_component)

        return node

    @classmethod
    def _get_ref_components(cls, ref: str):
        # Check ref string
        if not re.fullmatch(cls._FULL_REF_STR_PATTERN, ref):
            raise InvalidRefStr(ref)

        # Break up ref string into list of components.
        return [x['component_or_dots']
                for x in re.finditer(cls._REF_STR_COMPONENT_PATTERN_OR_DOTS, ref)]

    def _node_from_ref_component(self, ref_component: str):
        """
        Each node type should know how to handle specific string ref component patterns.
        If the ref component is not recognied by the type, it should punt handling to the parent
        type. The implementation in :meth:`Node._node_from_ref_component` is the last resort, and it can only handle
        dot-references to parents (e.g., "....") or self (e.g., ".").

        This method also provides a hacky way for ref strings to skip :class:`KeyNode`s when these are parents in ref strings.
        """
        from .dict_container import KeyNode
        if re.fullmatch(r'\.+', ref_component):
            # Matches a sequence of dots (e.g., "....")
            node = self
            for _ in range(len(ref_component)-1):
                node = node.parent
                if isinstance(node, KeyNode):
                    node = node.parent
            return node
        else:
            return self[ref_component]
            # raise InvalidRefStrComponent(self, ref_component)

    def __call__(self, ref: str = '.', calling_node=None):
        """
        Retrieves the node with the specified reference string relative to ``self`` and resolves it.
        """
        node = self.node_from_ref(ref)
        return node.resolve()

    @property
    def qual_name(self):
        """
        Returns the absolute node name.
        """
        return (f'{self.parent.get_child_qual_name(self)}' if self.parent else '')

    def rel_name(self, ancestor: 'Node'):
        """
        Returns the name of this node, relative to the specified ancestor node.

        .. doctest::

          >>> from soleil import SolConf
          >>> sc = SolConf({'greek': {'alpha': 'a', 'beta': 'b'}})
          >>> sc.root.rel_name(sc.root)
          ''
          >>> sc.root['greek']['alpha'].rel_name(sc.root['greek'])
          'alpha'

        """

        # Check that ancestor is an ancestor
        ancestors = [node := self]
        while node.parent:
            ancestors.append(node := node.parent)

        if ancestor not in ancestors:
            raise Exception(f'{ancestor} is not an ancestor of {self}.')

        # Get relative name
        ancestor_qual_name = ancestor.qual_name
        self_qual_name = self.qual_name
        if ancestor_qual_name != self_qual_name[:len(ancestor_qual_name)]:
            # Should never happen, since ancestry was verified above.
            raise Exception('Unexpected error!')

        #
        return self_qual_name[len(ancestor_qual_name):].lstrip('.')


@dataclass
class EvaledNode(Node):
    """
    Adds a :attr:`parser` attribute and :meth:`safe_eval` method to the standard Node.
    """

    parser: Parser = field(default_factory=kw_only('parser'))
    """
    The Python parser used to resolve :ref:`dstrings` and :ref:`raw key <raw key syntax>` type and modifier strings.
    """

    eval_context: dict = field(default_factory=dict)
    """
    Extra context variables injected to the parser evaluation context.
    """

    def safe_eval(self, py_expr: str, context=None):
        """
        Evaluates the python expression ``py_expr``, injecting ``self`` as variable |CURRENT_NODE_VAR_NAME|, ``self.root`` as |ROOT_NODE_VAR_NAME| and ``self.file_root`` as |FILE_ROOT_NODE_VAR_NAME| in the parser evaluation context. If the node or one of its ancestors was loaded from a file, that node will also be injected to the parser evaluation context as variable |FILE_ROOT_NODE_VAR_NAME|.
        """
        context = {
            varnames.CURRENT_NODE_VAR_NAME: self,
            varnames.ROOT_NODE_VAR_NAME: self.root,
            **({varnames.FILE_ROOT_NODE_VAR_NAME: self.file_root}
               if self.file_root is not None else {}),
            **self.eval_context,
            **(context or {}), }

        return self.parser.safe_eval(py_expr, context)


@dataclass
class ParsedNode(EvaledNode):
    """
    Parsed nodes are leaf nodes that contain literal values or |dstrings|.

    Parsed nodes are resolved in one of four ways depending on the raw input value:

    1. Raw values that are not strings are passed on without modification.

    For string raw values, the node's resolved content will depend on the raw value's first character:

    2. The string starts with ``'$:'``: the remainder of the string will be evaluated as a safe python expression returning the resolved value. Any whitespace after the prefix will be stripped.
    3. The string starts with ``'\\:'``: that prefix will be stripped and the remainder used as the resolved value.
    4. For any other character, the string itself will be the resolved value.

    .. rubric:: Special context variables

    Parsed node objects expose an :meth:`safe_eval` method that automatically injects the special node-related variables |CURRENT_NODE_VAR_NAME|, |ROOT_NODE_VAR_NAME| and |FILE_ROOT_NODE_VAR_NAME| to the parser evaluation context:

    * Variable |CURRENT_NODE_VAR_NAME| points to ``self``.
    * Variable |FILE_ROOT_NODE_VAR_NAME| points to ``self``'s closest ancestor (including ``self``) that was loaded from a file. If no ancestor was loaded from a file, the variable is not present.

    .. todo:: Change the name of this node to DollarNode or LeafNode.
    """

    raw_value: Any = field(default_factory=kw_only('raw_value'))
    """
    The literal value or unparsed |dstring|.
    """

    def __init__(self, raw_value, **kwargs):
        self.raw_value = raw_value
        super().__init__(**kwargs)

    def _unsafe_resolve(self) -> Any:
        if isinstance(self.raw_value, str):
            if self.raw_value[:2] == '$:':
                return self.safe_eval(self.raw_value[2:].strip())
            elif self.raw_value[:2] == r'\:':
                return self.raw_value[2:]
            else:
                return self.raw_value
        else:
            return self.raw_value
