"""
|SRPP|-registered utility functions and types.

Types defined here can be used for type-checking and casting. Type alias ``dt64``, for example, is an alias to ``numpy.datetime64`` and can take an ISO-8601 string (e.g., ``'2014-03-07T17:52:05.245'`` or sub-part like ``'2014-03-01T17'``) and convert it ``numpy.datetime64``:

.. doctest::
  :options: +NORMALIZE_WHITESPACE

  >>> from soleil import SolConf
  >>> SolConf({
  ...   'a::cast(dt64)': '2014-03-07T17:52:05.245',
  ...   'b:dt64': "$: dt64('2014-03-01T17')"
  ... })()
  {'a': numpy.datetime64('2014-03-07T17:52:05.245'),
   'b': numpy.datetime64('2014-03-01T17','h')}
"""


from .parser import register
from pathlib import Path
from typing import Union
import numpy as np


@register("cwd")
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


@register("values")
def values(x: dict):
    """
    Returns the values of the input dictionary
    """
    return x.values()


@register("keys")
def keys(x: dict):
    """
    Returns the keys of the input dictionary
    """
    return x.values()


# TODO: Not reflected in documentation!
dt64 = np.datetime64
"""
(Sphinx Autodoc overwrites this doc string with an 'alias of ...' string -- the doc string is required however to have the 'alias of ...').
"""
register("dt64", np.datetime64)
