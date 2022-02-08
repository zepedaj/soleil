from typing import Union
import numpy as np
from .utils import register, namespace

ns = namespace('numpy')


@register('dt64')  # For convenience
# @ns('datetime64')
def datetime64(val: Union[str, np.datetime64]):
    """
    Takes an ISO-8601 string (e.g., '2014-03-07T17:52:00.000' or parts thereof) (or numpy.datetime64) and converts it numpy.datetime64.
    """
    return np.datetime64(val)
