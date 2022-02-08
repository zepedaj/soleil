
ROOT_NODE_VAR_NAME = 'r_'
"""
Specifies the name of the root node in the parser context.
"""

CURRENT_NODE_VAR_NAME = 'n_'
"""
Specifies the name of the current node variable in the parser context.
"""

FILE_ROOT_NODE_VAR_NAME = 'f_'
"""
Specifies the name of the highest-level node in the current file.
"""

SPHINX_DEFS = f"""
.. |CURRENT_NODE_VAR_NAME| replace:: ``{CURRENT_NODE_VAR_NAME}``
.. |ROOT_NODE_VAR_NAME| replace:: ``{ROOT_NODE_VAR_NAME}``
.. |FILE_ROOT_NODE_VAR_NAME| replace:: ``{FILE_ROOT_NODE_VAR_NAME}``
"""

DEFAULT_EXTENSION = '.yaml'
"""
The default file extension.
"""
