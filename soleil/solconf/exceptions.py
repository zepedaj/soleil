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
    def __init__(self, node, err):
        super().__init__(
            f'Error while modifying node '
            f'`{node}` (full traceback above): `{err}`')


class RawKeyComponentError(Exception):
    def __init__(self, node, err, component):
        super().__init__(
            f'Error while parsing the raw key `{component}` string of node '
            f'`{node}` (full traceback above): `{err}`')


class ResolutionError(Exception):
    def __init__(self, node, err):
        super().__init__(
            f'Error while resolving node '
            f'`{node}` (full traceback above): `{err}`')


class InvalidOverridePattern(Exception):
    def __init__(self, pattern):
        super().__init__(
            f'Invalid override pattern `{pattern}` must have the form `a.8.b... = <raw content>`.')


class KeyNodeRequired(TypeError):
    def __init__(self, node):
        super().__init__(f'`KeyNode` required but got {node} of type `{type(node)}`.')
