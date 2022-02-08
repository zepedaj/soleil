import re
from .exceptions import NotAChildOfError
import abc
from .nodes import Node
from typing import List, Union


class Container(Node):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    @abc.abstractmethod
    def children(self): return {}

    @abc.abstractmethod
    def add(self, node: Node):
        """
        Add the specified node to the container.
        """

    @abc.abstractmethod
    def remove(self, node: Node):
        """
        Remove the specified node from the container.
        """

    @abc.abstractmethod
    def replace(self, old_node: Node, new_node: Node):
        """
        Replaces an old node with a new node.
        """

    def __getitem__(self, *args) -> Node:
        """
        Returns the specified node or nodes.
        """
        return self.children.__getitem__(*args)

    @abc.abstractmethod
    def get_child_qual_name(self, child_node):
        """
        Returns the name of the specified child in the container as a string.
        """

    def _derive_qual_name(self, child_name: str):
        """
        Helper method to build a qualified name from a child of this node given that node's string (non-qualified) name.
        """
        return (
            f'{_qual_name}.' if (_qual_name := self.qual_name) else '') + child_name


class ListContainer(Container):

    children: List[Node] = None

    _REF_COMPONENT_PATTERN = re.compile(r'(0|[1-9]\d*)')

    def __init__(self, **kwargs):
        self.children = []
        super().__init__(**kwargs)

    def add(self, node: Node):
        with self.lock:
            node.parent = self
            self.children.append(node)

    def get_child_posn(self, child: Node):
        """
        Gets the position of the child in the container, raising an :exc:`NotAChildOfError` if the child is not found in the container.
        """
        success = False
        for k, node in enumerate(self.children):
            if node is child:
                success = True
        if not success:
            raise NotAChildOfError(child, self)
        return k

    def remove(self, index: Union[int, Node]):
        """
        Removes the node (if index is a Node) or the node at the specified position (if index is an int).
        """
        with self.lock:
            if isinstance(index, int):
                node = self.children.pop(index)
                node.parent = None
            elif isinstance(index, Node):
                with index.lock:
                    self.remove(self.get_child_posn(index))
            else:
                raise TypeError(f'Invalid type {type(index)} for arg `index`.')

    def replace(self, old_node: Node, new_node: Node):
        """
        Replaces the specified node with a new node at the same position.
        """
        with self.lock, old_node.lock, new_node.lock:
            posn = self.get_child_posn(old_node)
            old_node.parent = None
            if new_node.parent:
                new_node.parent.remove(new_node)
            new_node.parent = self
            self.children[posn] = new_node

    def _unsafe_resolve(self):
        with self.lock:
            return [n.resolve() for n in self.children if not n.hidden]

    def get_child_qual_name(self, child_node):

        #
        for k, contained_child in enumerate(self.children):
            if child_node is contained_child:
                return self._derive_qual_name(str(k))
        #
        raise NotAChildOfError(child_node, self)

    def _node_from_ref_component(self, ref_component: str):
        if re.fullmatch(self._REF_COMPONENT_PATTERN, ref_component):
            return self[int(ref_component)]
        else:
            return super()._node_from_ref_component(ref_component)
