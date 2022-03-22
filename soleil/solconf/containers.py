import re
from .exceptions import NotAChildOfError, NodeHasParent
import abc
from .nodes import Node
from typing import List, Union


class Container(Node):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    @abc.abstractmethod
    def children(self):
        """
        Returns an iterable over the container's children
        """

    def __len__(self):
        return len(self.children)

    def is_child(self, node):
        return node in self.children

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

    def __init__(self, **kwargs):
        self.children = []
        super().__init__(**kwargs)

    def _getitem(self, key, modify=True) -> Node:
        """
        Returns the specified node or nodes.
        """
        if isinstance(key, str):
            key = int(key)
        if modify:
            self.modify()
        return self.children[key]

    def add(self, node: Node):
        with self.lock:
            if node.parent is not None:
                raise NodeHasParent(node, self)
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
                break
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
