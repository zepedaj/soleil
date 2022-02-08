from .ast_parser import register
from pathlib import Path


@register('cwd')
def cwd():
    """
    Returns the current working directory as a pathlib ``Path`` object.

    It can be concatenated to form a full directory using the division operator.

    .. rubric:: Example

      my_sub_dir = cwd() / 'my' / 'sub' / 'dir'

    """
    return Path.cwd().absolute()
