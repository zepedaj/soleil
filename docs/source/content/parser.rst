.. _Restricted Python Parser:

Restricted Python Parser
=========================

.. todo :: Finish specifying what is supported.

Supported Grammar Components
------------------------------

Constructs
 List and dictionaries, including comprehensions.

Operators
 +, -, /, 

Types
  ``float``, ``int``, ``bool``, ``bytes``, ``str``, ``list``, ``tuple``, ``dict``, ``set``


Variable Context
------------------

 * The root-node variable |ROOT_NODE_VAR_NAME| pointing to the root of the node tree.
 * The current-node variable |CURRENT_NODE_VAR_NAME| pointing to the node where the |dstring| exists as raw content.
 * The file root node variable |FILE_ROOT_NODE_VAR_NAME|, pointing to the nearest ancestor that is the highest-level node in a file -- this will be ``n_`` or an ancestor.
