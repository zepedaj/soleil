import numpy as np
from .parser import register

# TODO: Not reflected in documentation!
dt64 = np.datetime64
"""
(Sphinx Autodoc overwrites this doc string with an 'alias of ...' string -- the doc string is required however to have the 'alias of ...').
"""
register("dt64", np.datetime64)
register("td64", np.timedelta64)

# Numpy extras
for _symbol in ["inf", "log", "exp"]:
    register(_symbol, getattr(np, _symbol))
