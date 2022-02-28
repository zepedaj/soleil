
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

EXTENDED_NODE_VAR_NAME = 'x_'
"""
When an :meth:`~soleil.solconf.modifiers.extends` modifier is in effect, nodes being modified will have the source node injected into the eval context under this name.
"""

SPHINX_DEFS = f"""
.. |CURRENT_NODE_VAR_NAME| replace:: ``{CURRENT_NODE_VAR_NAME}``
.. |ROOT_NODE_VAR_NAME| replace:: ``{ROOT_NODE_VAR_NAME}``
.. |FILE_ROOT_NODE_VAR_NAME| replace:: ``{FILE_ROOT_NODE_VAR_NAME}``
.. |EXTENDED_NODE_VAR_NAME| replace:: ``{EXTENDED_NODE_VAR_NAME}``
.. |Node.value_modifiers| replace:: :attr:`Node.value_modifiers <soleil.solconf.nodes.Node.value_modifiers>`
.. |KeyNode| replace:: :class:`~soleil.solconf.dict_container.KeyNode`
.. |KeyNode.attr| replace:: :attr:`KeyNode.attr <soleil.solconf.dict_container.KeyNode.attr>`
.. |DictContainer| replace:: :attr:`~soleil.solconf.dict_container.DictContainer`
.. |SolConf| replace:: :attr:`~soleil.solconf.solconf.SolConf`
.. |DEFAULT_EXTENSION| replace:: ``.yaml``
"""

DEFAULT_EXTENSION = '.yaml'
"""
The default file extension.
"""
