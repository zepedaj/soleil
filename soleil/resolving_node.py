from dataclasses import dataclass
from inspect import stack
from typing import Optional
from xerializer.cli_tools.exceptions import ResolutionCycleError


@dataclass
class ResolvingNode:
    """
    This class is a special marker class used as part of the node resolution cycle detection mechanism.  For this mechanism to work correctly, this class should only be used inside method :meth:`~xerializer.cli_tools.nodes.Node.resolve`. Classes overloading that method should take care to call the super method or instantiate this object in a similar manner.
    """
    node: Optional  # : Optional['Node']

    def __init__(self, node):
        """
        :param node: The node currently being resolved.
        """
        self.node = node
        self.resolving_dependent = self.get_resolving_dependent()
        self.check_no_cycle()

    def check_no_cycle(self):
        """
        Verifies that no resolution cycles will occur as part of ``self.node``'s resolution and raises a :class:`ResolutionCycleError` otherwise.
        """
        cycle = [self.node]
        for node in self.dependents():
            cycle.append(node)
            if self.node is node:
                raise ResolutionCycleError(cycle[::-1])

    @staticmethod
    def get_resolving_dependent() -> 'ResolvingNode':
        """
        Returns the resolving node whose :meth:`resolve` method called the current node's (``self.node``'s) :meth:`resolve` method.

        This is done by searching down the stack for the first variable of name `__resolving_node__` and type :class:`ResolvingNode`.
        """
        call_stack = stack()
        for call in call_stack:
            if resolving_dependent := call.frame.f_locals.get('__resolving_node__', None):
                return resolving_dependent

        return None

    def dependents(self):
        """
        Iterates over all the nodes whose resolution depends on this node's resolution.
        """
        resolving_dependent = self.resolving_dependent
        while resolving_dependent is not None:
            yield resolving_dependent.node
            resolving_dependent = resolving_dependent.resolving_dependent
