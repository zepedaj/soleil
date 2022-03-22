
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
.. |Node| replace:: :attr:`~soleil.solconf.nodes.Node`
.. |Node.value_modifiers| replace:: :attr:`Node.value_modifiers <soleil.solconf.nodes.Node.value_modifiers>`
.. |KeyNode| replace:: :class:`~soleil.solconf.dict_container.KeyNode`
.. |KeyNode.value| replace:: :attr:`KeyNode.value <soleil.solconf.dict_container.KeyNode.value>`
.. |ParsedNode.raw_value| replace:: :attr:`ParsedNode.raw_value <soleil.solconf.nods.ParsedNode.raw_value>`
.. |DictContainer| replace:: :attr:`~soleil.solconf.dict_container.DictContainer`
.. |Container| replace:: :attr:`~soleil.solconf.container.Container`
.. |SolConf| replace:: :class:`~soleil.solconf.solconf.SolConf`
.. |SolConf.post_processor| replace:: :class:`SolConf.post_processor < soleil.solconf.solconf.SolConf.post_processor>`
.. |SolConf.load| replace:: :class:`SolConf.load <soleil.solconf.solconf.SolConf.load>`
.. |SolConfArg| replace:: :class:`~soleil.solconf.cli_tools.solconfarg.SolConfArg`
.. |DEFAULT_EXTENSION| replace:: ``.yaml``
.. |argparse| replace:: `argparse <https://docs.python.org/library/argparse.html#argparse>`__
.. |ArgumentParser.add_argument| replace:: `ArgumentParser.add_argument <https://docs.python.org/library/argparse.html#argparse.ArgumentParser.add_argument>`__
.. |argparse.ArgumentParser| replace:: `argparse <https://docs.python.org/library/argparse.html#argparse.ArgumentParser>`__
.. |load| replace:: :meth:`~soleil.solconf.modifiers.load`
.. |derives| replace:: :meth:`~soleil.solconf.modifiers.derives`
.. |choices| replace:: :meth:`~soleil.solconf.modifiers.choices`
.. |fuse| replace:: :meth:`~soleil.solconf.modifiers.fuse`
.. |cast| replace:: :meth:`~soleil.solconf.modifiers.cast`
.. |promote| replace:: :meth:`~soleil.solconf.modifiers.promote`
.. |SRPP| replace:: :ref:`SRPP <SRPP>`
"""

DEFAULT_EXTENSION = '.yaml'
"""
The default file extension.
"""
