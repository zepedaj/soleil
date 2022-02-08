from typing import Optional
from .utils2 import _Unassigned


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
    def __init__(self, ref: str, ref_component: str = _Unassigned):

        if ref_component is not _Unassigned:
            super().__init__(f'Invalid component `{ref_component}` in reference string `{ref}`.')
        else:
            super().__init__(f'Invalid reference string `{ref}`.')


class InvalidRefStrComponent(Exception):
    def __init__(self, ref_component: str):
        self.ref_component = ref_component
        super().__init__(f'Invalid ref string component {ref_component}.')
