
|soleil| is *(1)* a **configuration manager** that is templated, hierarchical, and cross-referential; *(2)* a **CLI builder** ; and *(3)* **experiment launcher** inspired by Facebook's `Hydra <https://hydra.cc/docs/intro/>`_.

The main aim of |soleil| is to minimize the amount of glue code, effort, technical debt buildup and related cognitive load associated with managing machine learning model training experiments.

Motivation
==========

* [TODO] Leverages the :mod:`xerializer` package to support custom type type-checking and config file or CLI object representation.

* Near-no-code CLI experiment launching.

* Leverages Python's built-in `Abstract Syntax Tree <https://docs.python.org/3/library/ast.html>`_ support.

  * Simple, rich, Python-based syntax for configuration value resolution.
  * Restricted for safety, user-extensible.

* Flexible configuration node tree system

  * Supports hidden nodes that are visible to other nodes when rendering, but not included in the final rendered configuration.
  * Can represent any argument structure - the root does not need to be a dictionary.

* [TODO] Plays nicely with `argparse <https://docs.python.org/3/library/argparse.html>`_ -- can be used to define an argparse parameter, or to auto-build a CLI from a config file.

* Simple, well-documented code base.
* Common type-checking interface
* Consistent, flexible conventions, easy to remember.
* Non-intrusive 

  * Does not auto-configure logging or output file location. 
  * Does not require a rigid configuration file structure or output file name location.

* Meaningful error messages clearly indicating configuration nodes with problems.

  * Configuration values cyclical dependencies detected automatically and signaled to the user.
  * [TODO] Config source file causing the error included in error message.


Installation
============

.. code-block:: bash

  pip install soleil

Getting started
===============


Soleil configuration objects 
===============================

Basic configuration objects
----------------------------------

Soleil configuration objects (:class:`SolConf` objects) are built from compositions of *native serializable types* (i.e., those types that can be represented natively in **YAML** or **JSON** format):

   * ``int``, ``float``, ``str``, ``bool``, 
   * ``None``, 
   * ``list`` and
   * ``dict`` (with string keys that are valid variable names).

This makes it possible to represent these objects in human-readable **YAML** or **JSON** files stored in directory hierarchies.

A :class:`SolConf` object is built by passing raw content directly to the initializer:

.. testcode:: SolConf

   from soleil import SolConf

   sc = SolConf('abc')

Calling a :class:`SolConf` object returns its **resolved** value. For simple raw content (raw content without modifiers or |dstrings|), the resolved value is the same as the original input:

.. testcode:: SolConf

   # Base types
   for raw in [1, 2.0, 'abc', [1,2,'abc']]:
     sc = SolConf(raw)
     assert sc() == raw
     
   # Dictionaries - keys must be valid variable names.
   for raw in [{'var0':0, 'var1':1, 'var2':2}]:
      sc = SolConf(raw)
      assert sc() == raw


Compositions of these base types are also valid input:

.. testcode:: SolConf

  # Base type compositions are valid too.
  raw_content = {
    'var0': [0, 1, 2, 'abc', {'var1':[3,4,'xyz']}],
    'var2': 5
  }
  assert SolConf(raw_content)() == raw_content    
     
|dstrings|
-----------

The power of :class:`SolConf` objects comes from their ability to interpret |dstrings| -- special strings indicated by a ``'$:'`` prefix that are evaluated using |soleil|'s :ref:`Restricted Python Parser`:

.. testcode:: SolConf

  assert SolConf('$: 1+2')() == 3 # White space after ``'$:'`` is stripped.
  assert SolConf('$: {1:[0,1], 2:[2,3]}')() == {1:[0,1], 2:[2,3]}

|dstrings| are evaluated using a :class:`~soleil.solconf.parser.Parser` object that supports a subset of the standard Python syntax. Evaluation occurs within a user-extensible variable context (the |dstring| context) that includes several standard Python functions and types (e.g., ``range``, ``list``, ``dict``, ``int``, ``str``) as well as special node variables used in node :ref:`cross-referencing <xr>`.

See :ref:`Restricted Python Parser` for more information on supported Python grammar components, the default variable context and ways to extend it.

.. rubric:: Escaping strings

All strings in raw content that begin with ``'$: '`` are evaluated as Python expressions when the node containing the content is resolved. This behavior can be overriden by instead prefixing the string with ``'\:'``:

.. testcode:: SolConf

   assert SolConf('\:  $: 1+2')() == '  $: 1+2' # White space after '\:' is not ignored
   assert SolConf('\\:  $: 1+2')() == '  $: 1+2' # Equivalent, with escaped backslash
   assert SolConf(r'\:  $: 1+2')() == '  $: 1+2' # Equivalent, with Python raw string

.. _xr:

Cross-references
-----------------

Raw content used to initialize :class:`SolConf` objects can contain cross-references. To facilitate this, soleil automatically injects three nodes as variables into the |dstring| evaluation context:

  * Variable |ROOT_NODE_VAR_NAME| refers to the *root node*.
  * Variable |CURRENT_NODE_VAR_NAME| refers to the *current node* -- the node where the |dstring| is defined.
  * Variable |FILE_ROOT_NODE_VAR_NAME| refers to the current file's root node -- the highest-level node of the configuration file where the current node is defined. This is possibly the same as ``n_``. It will not be defined if the current node was not defined in a file.

Any of these variables described above can be used to create cross-references using :ref:`chained indices <with indices>` or :ref:`reference strings <with reference strings>`:

.. testcode:: SolConf

   sc_xr = SolConf({
	      'var1': {
	        'subvar1': 2,
		'subvar2': 3
		},
	      # Chained index cross-ref
	      'var2': "$: r_['var1']['subvar1']()",
	      # Ref string cross-ref
	      'var3': "$: n_('..var1.subvar2')"
	      })

   assert sc_xr() ==  {
	      'var1': {
	        'subvar1': 2,
		'subvar2': 3
		},
	      'var2': 2,
	      'var3': 3
	      }

Node system
============

:class:`SolConf` objects construct  a node-tree from raw input content. Understanding the structure of this tree is useful for advanced use. 

Node types
-----------

:class:`SolConf`  node trees can have nodes of the following types:

DictContainer
     :class:`DictContainer` nodes represent Python dictionaries with keys that are valid variable names. Their children nodes must be of type :attr:`KeyNode`.
KeyNode
     :class:`KeyNode`  nodes contain a string key that is a valid variable name and a child node :attr:`KeyNode.value` that is of any of the three other node types. :class:`KeyNode` nodes always have a parent that is a :class:`DictContainer`. Key nodes play a special role discussed :ref:`here <Key nodes>`.
ListContainer
     :class:`ListContainer` nodes represent Python lists and can contain nodes of any type except for type :class:`KeyNode`.
ParsedNode
     :class:`ParsedNode` nodes represent tree leafs -- they must always be either the root node, or a child of a :class:`KeyNode` or :class:`ListContainer` node. When the :class:`ParsedNode`'s raw content is a string, |dstring| evaluation rules are applied to it. Otherwise, the raw value is passed on directly when resolving the node.

The types of nodes are designed to cover all :ref:`native serializable types <NST>`.


.. rubric:: Example

As an example, consider the following :class:`SolConf` object:

.. _example code:

.. testcode:: SolConf

   raw_content = {
    'var1': 1,
    'var2': [2,3,'$:1+3']}

   sc = SolConf(raw_content)

The object's node tree will have the following structure:

.. root [label="DictContainer@'' qual name: ''"]


.. _example graph:

.. graphviz::
   :caption: A node tree corresponding to the code snippet :ref:`above <example code>`. Node types are indicated to the left of the '@' character, and :ref:`qualified names <qualified name>` in the single-quoted string after the '@' character. For parsed nodes, the raw content is indicated in parentheses.

   digraph foo {

     node [shape=box,style=rounded]

     root [label="DictContainer@''"]
     var1_key [label="KeyNode@'*var1'"] 
     var2_key [label="KeyNode@'*var2'"]
     var1_val [label="ParsedNode@'var1' (1)"]
     var2_val [label="ListContainer@'var2'"]
     
     var2_val0 [label="ParsedNode@'var2.0' (2)"]
     var2_val1 [label="ParsedNode@'var2.1' (3)"]
     var2_val2 [label="ParsedNode@'var2.2' ('$:1+3')"]

     root -> var1_key;
     root -> var2_key;
     var1_key -> var1_val;
     var2_key -> var2_val;

     var2_val -> var2_val0;
     var2_val -> var2_val1;
     var2_val -> var2_val2;
   }

.. todo:: 

   Improvments to the above graph:

   1. Add and color-code node type, node qual_name, and value, raw content
   2. Use square, rounded-corner nodes with arrows that enter the node vertically.

.. _Key nodes:

Key nodes
----------

Modifiers
^^^^^^^^^^
Missing

Type checking
^^^^^^^^^^^^^^
Missing

.. todo:: Discuss xerializable types

Referencing nodes
-------------------

.. _with indices :

... with indices
^^^^^^^^^^^^^^^^^

Container nodes expose a :meth:`~Node.__getitem__` method that enables natural, chainable, dictionary- or list-like access:

.. testcode:: SolConf

   root = sc.root
   root['var2'][2]

:class:`SolConf` further exposes a :meth:`~SolConf.__getitem__` that is an alias to the root node's :meth:`~Node.__getitem__` method:

.. testcode:: SolConf

   assert (
     root['var2'][2] is 
     sc['var2'][2]
   )


Note that accessing children nodes in this manner will return another node. As usual, the returned node can be resolved with its :class:`~Node.__call__` method:

.. testcode:: SolConf

   assert root['var2'][2]() == 4

.. rubric:: Key vs. value node indexing syntax

Accessing a dictionary container's node using the key string produces not the :class:`KeyNode` that is a direct child of the container, but rather the :class:`KeyNode.value` attribute. The key node can be accessed instead by pre-pending the key string with ``'*'``:

.. testcode:: SolConf

   from soleil.solconf.dict_container import KeyNode

   assert type(sc['var2']) is not KeyNode
   assert type(sc['*var2']) is KeyNode

   assert sc['var2'].parent is sc['*var2']
   assert sc['*var2'].parent is sc.root

This indexing syntax is meant to make node access behave like standard dictionary indexing.

.. _with reference strings :

... with reference strings
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Reference strings offer another, more compact way to refer to nodes in the node tree. Reference strings consist of a sequence of container indices separated by one or more ``'.'`` characters. Using :math:`N>1` characters will refer to the node's :math:`(N-1)`-th ancestor.

.. testcode:: SolConf

   # From the root
   assert (
     root.node_from_ref('var2.2..0') is 
     root.node_from_ref('var2.0') )

A reference string can also be passed directly to a node's :meth:`~Node.__call__` method in order to resolve the referenced node:

.. testcode:: SolConf

   # From the root   
   assert root('var2.2..0') == 2
   assert root('var2.0') == 2

   # From node
   node = root.node_from_ref('var2')
   assert node('2..0') == 2
   assert node('0') == 2

Note that, similarly to index refernces, reference strings skip nodes of type :class:`KeyNode`:

.. todo:: Example
 
... with qualified names
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Nodes expose a :ref:`qualified name <qualified name>` in attribute :attr:`~Node.qual_name` that contains the node's reference string relative to the root node. Qualified names offer a compact way to refer to the node:

.. testcode:: SolConf

   node = root.node_from_ref('var2.2..0')
   assert node.qual_name == 'var2.0'
   assert root(node.qual_name) is node

Note that qualified names contain no consecutive ``'.'`` characters.
