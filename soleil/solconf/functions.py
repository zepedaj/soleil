from .parser import register
from pathlib import Path
from typing import Union
import numpy as np


@register('cwd')
def cwd():
    """
    Returns the current working directory as a pathlib ``Path`` object.

    It can be concatenated to form a full directory using the division operator.

    .. rubric:: Example

    .. testcode::

      from soleil.solconf.parser import Parser

      parser = Parser()
      my_sub_dir = parser.safe_eval("cwd()/'my'/'sub'/'dir'")

    """
    return Path.cwd().absolute()


@register('values')
def values(x: dict):
    """
    Returns the values of the input dictionary
    """
    return x.values()


@register('keys')
def keys(x: dict):
    """
    Returns the keys of the input dictionary
    """
    return x.values()


register('dt64', np.datetime64)
"""
Takes an ISO-8601 string (e.g., '2014-03-07T17:52:00.000' or parts thereof) (or numpy.datetime64) and converts it numpy.datetime64.
"""


register('range', range)
