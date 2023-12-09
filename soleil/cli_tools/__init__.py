"""
Soleil CLI utilities.

.. note:: Importing this module or members thereof will monkey-path Python's builtin module. See the :ref:`note <argparse patches note>` in the |SolConfArg| documentation.
"""

from .solconfarg import SolConfArg
from .solex_decorator import solex

__all__ = ["SolConfArg", "solex"]
