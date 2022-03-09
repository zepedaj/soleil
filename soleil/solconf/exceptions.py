from .utils import _Unassigned


class NotAChildOfError(Exception):
    def __init__(self, orphan, parent):
        super().__init__(f'Node `{orphan}` is not a child of `{parent}`.')


class ResolutionCycleError(Exception):
    def __init__(self, cycle):
        self.cycle = cycle
        super().__init__(
            'Resolution dependency cycle detected when attempting to resolve a node: ' +
            ' -> '.join('<root>' if x.qual_name == '' else x.qual_name for x in cycle))


class InvalidRefStr(Exception):
    def __init__(self, ref: str):
        super().__init__(f'Invalid reference string `{ref}`.')


class InvalidRefStrComponent(Exception):
    def __init__(self, node, ref_component: str):
        self.ref_component = ref_component
        super().__init__(f'Node `{node}` cannot handle ref string component `{ref_component}`.')


class ModificationError(Exception):
    def __init__(self, node, modifier=None):
        super().__init__(
            'Error while ' +
            (f'applying modifier `{modifier}` to ' if modifier else 'modifying ') +
            f'node `{node}`.')


class RawKeyComponentError(Exception):
    def __init__(self, node, component, raw_value=None):
        super().__init__(
            f'Error while parsing the raw key `{component}` string ' +
            (f'`{raw_value}` ' if raw_value is not None else '') +
            f'of node `{node}`.')


class ResolutionError(Exception):
    def __init__(self, node):
        super().__init__(
            f'Error while resolving node `{node}`.')


class InvalidOverridePattern(Exception):
    def __init__(self, pattern):
        super().__init__(
            f'Invalid override pattern `{pattern}` must have the form `a.8.b... = <raw content>`.')


class KeyNodeRequired(TypeError):
    def __init__(self, node):
        super().__init__(f'`KeyNode` required but got {node} of type `{type(node)}`.')


class NodeHasParent(Exception):
    def __init__(node, self):
        super().__init__('Attempted to add `{node}` with parent `{node.parent}` to `{self}`.')
