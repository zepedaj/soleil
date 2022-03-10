
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
.. |Node| replace:: :attr:`~soleil.solconf.nodes.Node`
.. |Node.value_modifiers| replace:: :attr:`Node.value_modifiers <soleil.solconf.nodes.Node.value_modifiers>`
.. |KeyNode| replace:: :class:`~soleil.solconf.dict_container.KeyNode`
.. |KeyNode.value| replace:: :attr:`KeyNode.value <soleil.solconf.dict_container.KeyNode.value>`
.. |ParsedNode.raw_value| replace:: :attr:`ParsedNode.raw_value <soleil.solconf.nods.ParsedNode.raw_value>`
.. |DictContainer| replace:: :attr:`~soleil.solconf.dict_container.DictContainer`
.. |SolConf| replace:: :class:`~soleil.solconf.solconf.SolConf`
.. |SolConf.post_processor| replace:: :class:`~soleil.solconf.solconf.SolConf.post_processor`
.. |SolConfArg| replace:: :class:`~soleil.solconf.cli_tools.solconfarg.SolConfArg`
.. |DEFAULT_EXTENSION| replace:: ``.yaml``
.. |argparse| replace:: `argparse <https://docs.python.org/library/argparse.html#argparse.ArgumentParser.add_argument>`__
.. |load| replace:: :meth:`~soleil.solconf.modifiers.load`
.. |choices| replace:: :meth:`~soleil.solconf.modifiers.choices`
.. |extends| replace:: :meth:`~soleil.solconf.modifiers.extends`
.. |cast| replace:: :meth:`~soleil.solconf.modifiers.cast`
.. |SRPP| replace:: :ref:`SRPP <SRPP>`
"""

DEFAULT_EXTENSION = '.yaml'
"""
The default file extension.
"""
